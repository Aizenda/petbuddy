from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Literal
from ..model.db_connect import mysql_pool
from ..model.JWT import *
from ..model.upload_function import Uploader
import json
import traceback
from typing import List, Optional

router = APIRouter()

# 1. 定義 Pydantic schema
class OptionIn(BaseModel):
    id: int                   # 前端臨時 id，用不到可忽略
    text: str
    value: str

class QuestionIn(BaseModel):
    id: int                   # 前端給的臨時 id
    title: str
    type: Literal["text","choice","image"]
    required: bool
    options: List[OptionIn] = []

class FormPayload(BaseModel):
    formTitle: str
    postId: int
    questions: List[QuestionIn]

class FormCheckItem(BaseModel):
    postId: int
    adopterId: Optional[int]  # 有些 adopterId 是 null

@router.post("/api/form")
async def create_form(payload: FormPayload,request:Request):
    conn = mysql_pool.get_connection()
    cursor = conn.cursor()
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"error": "未授權"})
        
        cursor.execute(
            "SELECT id FROM forms WHERE post_id = %s",
			 (payload.postId,)
		)
		
        if cursor.fetchone():
            return JSONResponse({"ok": False, "message":"表單已存在"},status_code=409)
        
        cursor.execute(
            "SELECT 1 FROM send WHERE id = %s", (payload.postId,)
		)
        
        if not cursor.fetchone():
             return JSONResponse({"ok": False, "message":"找不到對應的送養文章"},status_code=404)
        
        # 2. 先 insert into forms 拿到 new_form_id
        cursor.execute(
          "INSERT INTO forms (post_id, title) VALUES (%s, %s)",
          (payload.postId, payload.formTitle)
        )
        form_id = cursor.lastrowid

        # 3. 逐題插入 form_questions
        for order, q in enumerate(payload.questions, start=1):
            question_key = f"q{q.id}"
            cursor.execute(
              """
              INSERT INTO form_questions
                (form_id, question_key, question_order, type, title, is_required)
              VALUES (%s, %s, %s, %s, %s, %s)
              """,
              (
                form_id,
                question_key,
                order,         # 題目順序
                q.type,
                q.title,
                int(q.required)
              )
            )
            question_id = cursor.lastrowid

            # 4. 如果是 choice，才 insert options
            if q.type == "choice":
                for opt_order, opt in enumerate(q.options, start=1):
                    cursor.execute(
                      """
                      INSERT INTO question_options
                        (question_id, option_order, label, value)
                      VALUES (%s, %s, %s, %s)
                      """,
                      (
                        question_id,
                        opt_order,
                        opt.text,
                        opt.value
                      )
                    )

        conn.commit()
        return JSONResponse({"ok": True, "message": "表單儲存成功"},status_code=200)

    except Exception as e:
        print(e)
        conn.rollback()
        return JSONResponse({"ok":False, "message":f"儲存表單及題目失敗：{e}"}, status_code=500)

    finally:
        cursor.close()
        conn.close()
        

@router.get("/api/form/{post_id}")
async def get_form(post_id: int, request:Request):
    conn = mysql_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"error": "未授權"})

        print(user_data)
        cursor.execute("""
          SELECT 
            id   AS formId,
            post_id AS postId,
            title    AS formTitle,
            created_at AS createdAt
          FROM forms
          WHERE post_id = %s
        """, (post_id,))

        form = cursor.fetchone()
        if not form:
            return JSONResponse({"ok":False, "message": "找不到這張表單"},status_code=404)

        form_id = form.get("formId")

        # 2. 撈所有題目
        cursor.execute("""
          SELECT 
            id              AS questionId,
            question_key    AS question_key,
            question_order  AS questionOrder,
            type,
            title,
            is_required     AS required
          FROM form_questions
          WHERE form_id = %s
          ORDER BY question_order
        """, (form_id,))
        questions = cursor.fetchall()

        # 3. 撈所有選項（如果有的話）
        question_ids = [q["questionId"] for q in questions]
        options = []
        if question_ids:
            fmt = ",".join(["%s"] * len(question_ids))
            cursor.execute(f"""
              SELECT
                question_id      AS questionId,
                id                AS optionId,
                option_order      AS optionOrder,
                label,
                value
              FROM question_options
              WHERE question_id IN ({fmt})
              ORDER BY question_id, option_order
            """, question_ids)
            options = cursor.fetchall()

        # 4. 把選項塞回對應的題目裡
        for q in questions:
            q["options"] = [o for o in options if o["questionId"] == q["questionId"]]

        form["createdAt"] = form["createdAt"].isoformat()
        # 5. 組回傳物件
        form["questions"] = questions
        return JSONResponse({"ok": True, "form": form},status_code=200)
    
    except Exception as e:
        print(str(e))
        conn.rollback()
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        cursor.close()
        conn.close()

@router.post("/api/submit-form")
async def submit(request: Request):
    ct = request.headers.get("content-type", "")
    conn = None
    cursor = None

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"error": "未授權"})
        
        result_dict = {}
        form_data = await request.form()
        for key, value in form_data.items():
            if hasattr(value, 'filename'): 
                result_dict[key] = {
                    'filename': value.filename,
                    'size': value.size,
                    'content_type': value.content_type,
                    'file_object': value
                }
            else:
                try:
                    result_dict[key] = json.loads(value)
                except:
                    result_dict[key] = value 

        user_id = user_data["userid"]
        totalQuestions = int(result_dict["totalQuestions"])
        form_id = result_dict["formId"]

        select_user= """
        SELECT s.user_id, f.*
        FROM send AS s
        LEFT JOIN forms AS f ON f.post_id = s.id
        WHERE s.user_id = %s AND f.id = %s;
        """

        cursor.execute(select_user,(user_id, form_id))
        check_data = cursor.fetchone()
        if check_data is not None:
            return JSONResponse({"ok":False, "message":"送養人無法填表"},status_code=409)
        
        print(user_id,form_id)
        check_submissions_select = """
        SELECT submitter_user_id FROM form_submissions
        WHERE submitter_user_id = %s AND form_id = %s;
        """
        cursor.execute(check_submissions_select,(user_id, form_id))
        check_submissions = cursor.fetchone()

        if check_submissions is not None:
            return JSONResponse({"ok":False, "message":"請勿重複填表"},status_code=409)

        insert_submissions = """
        INSERT INTO form_submissions (form_id, submitter_user_id)
        VALUES (%s, %s);
        """
        cursor.execute(insert_submissions,(form_id, user_id, ))
        conn.commit()
        sub_id = cursor.lastrowid

        insert_query = """
        INSERT INTO form_answers (submission_id, question_id, answer_text, answer_option_id, image_url)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        values = []
        for i in range(totalQuestions):
            i += 1
            answer_key = f"answer_q{i}"
            image_key = f"image_q{i}"

            question = result_dict.get(answer_key)
            if not question:
                continue

            q_type = question.get("type")
            qid = question.get("questionId")

            # 初始化欄位
            ans_text = None
            ans_option = None
            ans_image = None

            if q_type == "text":
                ans_text = question.get("value", "").strip()

            elif q_type == "choice":
                ans_option = question.get("selectedOptionIds")

            elif q_type == "image":
                image_data = result_dict.get(image_key)
                if image_data:
                    uploader = Uploader()
                    s3_url = await uploader.upload_file(
                        image_data["file_object"],
                        bucket="petbuddy-img"
                    )
                    ans_image = s3_url

            values.append((sub_id, qid, ans_text, ans_option, ans_image))

        # 寫入資料庫
        if values:
            cursor.executemany(insert_query, values)
            conn.commit()
                    

        return JSONResponse({"ok":True},status_code=200)
    
    except Exception as e:
        if conn:
            conn.rollback()
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.put("/api/revise-form")
async def revise_form(request: Request):
    ct = request.headers.get("content-type", "")
    conn = None
    cursor = None

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. 解析 token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"error": "未授權"})

        user_id = user_data["userid"]

        # 2. 解析表單內容
        result_dict = {}
        form_data = await request.form()
        for key, value in form_data.items():
            if hasattr(value, 'filename'):
                result_dict[key] = {
                    'filename': value.filename,
                    'size': value.size,
                    'content_type': value.content_type,
                    'file_object': value
                }
            else:
                try:
                    result_dict[key] = json.loads(value)
                except:
                    result_dict[key] = value

        total_questions = int(result_dict["totalQuestions"])
        form_id = result_dict["formId"]

        # 3. 找出原本的 submission_id
        cursor.execute("""
            SELECT id FROM form_submissions
            WHERE submitter_user_id = %s AND form_id = %s
        """, (user_id, form_id))
        submission = cursor.fetchone()

        if not submission:
            return JSONResponse(status_code=404, content={"ok": False, "message": "查無填寫紀錄"})

        sub_id = submission["id"]

        # 4. 先刪除原有答案
        cursor.execute("DELETE FROM form_answers WHERE submission_id = %s", (sub_id,))

        # 5. 重建新答案
        insert_query = """
        INSERT INTO form_answers (submission_id, question_id, answer_text, answer_option_id, image_url)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = []

        for i in range(total_questions):
            i += 1
            answer_key = f"answer_q{i}"
            image_key = f"image_q{i}"

            question = result_dict.get(answer_key)
            if not question:
                continue

            q_type = question.get("type")
            qid = question.get("questionId")
            ans_text = None
            ans_option = None
            ans_image = None

            if q_type == "text":
                ans_text = question.get("value", "").strip()

            elif q_type == "choice":
                ans_option = question.get("selectedOptionIds")

            elif q_type == "image":
                image_data = result_dict.get(image_key)
                if image_data:
                    uploader = Uploader()
                    s3_url = await uploader.upload_file(
                        image_data["file_object"],
                        bucket="petbuddy-img"
                    )
                    ans_image = s3_url

            values.append((sub_id, qid, ans_text, ans_option, ans_image))

        if values:
            cursor.executemany(insert_query, values)
            conn.commit()

        return JSONResponse({"ok": True}, status_code=200)

    except Exception as e:
        if conn:
            conn.rollback()
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.post("/api/check/form")
async def check_form(data: List[FormCheckItem], request: Request):
    conn = None
    cursor = None
    results = []
    
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"error": "未授權"})
        
        for item in data:
            post_id = item.postId
            adopter_id = item.adopterId
            
            # 檢查該 post 是否有任何表單
            cursor.execute("SELECT COUNT(*) as form_count FROM forms WHERE post_id = %s", (post_id,))
            form_count_row = cursor.fetchone()
            
            if form_count_row["form_count"] == 0:
                results.append({
                    "postId": post_id,
                    "formExists": False,
                    "adopterFilled": None,
                    "adopterId": adopter_id
                })
                continue
            
            # 檢查 adopter 是否填寫過該 post 的任何表單
            if adopter_id is not None:
                cursor.execute("""
                    SELECT 1 FROM form_submissions fs 
                    JOIN forms f ON fs.form_id = f.id 
                    WHERE f.post_id = %s AND fs.submitter_user_id = %s
                    LIMIT 1
                """, (post_id, adopter_id))
                filled = cursor.fetchone() is not None
            else:
                filled = None
            
            results.append({
                "postId": post_id,
                "formExists": True,
                "adopterFilled": filled,
                "adopterId": adopter_id
            })
        
        return JSONResponse({
            "ok": True,
            "data": results
        }, status_code=200)
        
    except Exception as e:
        print(str(e))
        return JSONResponse({
            "ok": False,
            "message": str(e)
        }, status_code=500)
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/api/ans")
async def ans_data(post_id: int, user_id: int, request: Request):
    conn = None
    cursor = None

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. 解碼 JWT 拿出送養人身份
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"error": "未授權"})

        current_user_id = int(user_data["userid"])

        # 2. 查該篇 post 是哪個送養人發的
        cursor.execute("SELECT user_id FROM send WHERE id = %s", (post_id,))
        post = cursor.fetchone()

        if not post:
            return JSONResponse({"ok": False, "message": "送養文章不存在"}, status_code=404)

        if post["user_id"] != current_user_id:
            return JSONResponse({"ok": False, "message": "你無權查看這篇貼文的表單"}, status_code=403)

        # 3. 查該領養人是否填過這篇貼文的表單
        select_submission = """
        SELECT s.id
        FROM form_submissions AS s
        LEFT JOIN forms AS f ON f.id = s.form_id
        WHERE f.post_id = %s AND s.submitter_user_id = %s
        """
        cursor.execute(select_submission, (post_id, user_id))
        submission = cursor.fetchone()

        if not submission:
            return JSONResponse({"ok": False, "message": "該領養人尚未填寫表單"}, status_code=404)

        submission_id = submission["id"]

        # 4. 查答案資料
        select_ans_data = """
        SELECT
            a.question_id,
            q.type,
            a.answer_text,
            a.answer_option_id,
            a.image_url,
            o.label AS selected_label,
            o.value AS selected_value
        FROM form_answers AS a
        JOIN form_questions AS q ON a.question_id = q.id
        LEFT JOIN question_options AS o ON a.answer_option_id = o.id
        WHERE a.submission_id = %s
        ORDER BY q.question_order;
        """
        cursor.execute(select_ans_data, (submission_id,))
        rows = cursor.fetchall()

        # 5. 組裝回傳資料
        result = {}
        for row in rows:
            qid = row["question_id"]
            qtype = row["type"]

            if qtype == "text":
                result[qid] = {"type": "text", "answer": row["answer_text"]}
            elif qtype == "choice":
                result[qid] = {
                    "type": "choice",
                    "selected_option_id": row["answer_option_id"],
                    "selected_label": row["selected_label"],
                    "selected_value": row["selected_value"]
                }
            elif qtype == "image":
                result[qid] = {"type": "image", "image_url": row["image_url"]}
        
        print(result)
        return JSONResponse({"ok": True, "data": result}, status_code=200)

    except Exception as e:
        print(str(e))
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()