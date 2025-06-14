from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Literal
from ..model.db_connect import mysql_pool
from ..model.JWT import *
from ..model.upload_function import Uploader
import json

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

@router.post("/api/form")
async def create_form(payload: FormPayload):
    conn = mysql_pool.get_connection()
    cursor = conn.cursor()
    try:
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
async def get_form(post_id: int):
    conn = mysql_pool.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. 先撈 forms 表頭
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
        return JSONResponse({"ok": False, "message": str(e)}, status_code=200)

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
        
        user_id = user_data.get("userid")
        result_dict = {}

        if "multipart/form-data" in ct:

            data = await request.form()
            for key, value in data.items():
                if hasattr(value, 'filename'):  # 處理檔案上傳
                    result_dict[key] = {
                        'filename': value.filename,
                        'size': value.size,
                        'content_type': value.content_type,
                        'file_object': value  # 保留檔案對象供後續處理
                    }
                else:
                    # 嘗試解析 JSON 字串
                    try:
                        result_dict[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result_dict[key] = value
            

            form_id = data.get("formId")

            insert_sub = """
            INSERT INTO form_submissions
            (id, form_id, submitter_user_id, submitted_at)
            VALUES
            (DEFAULT, %s, %s, DEFAULT);
            """
            cursor.execute(insert_sub,(form_id, user_id,))
            conn.commit() 

            sub_id = cursor.lastrowid
            total_questions = int(result_dict.get("totalQuestions"))

            for i in range(total_questions):
                question_id_query = """
                SELECT id FROM form_questions
                WHERE form_id = %s AND question_order = %s
                """
                cursor.execute(question_id_query, (form_id, i + 1))
                question_result = cursor.fetchone()
                
                if not question_result:
                    continue
                    
                question_id = question_result['id']
                
                answer_key = f"answer_q{i + 1}"
                image_key = f"image_q{i + 1}"
                
                # 初始化所有欄位為 NULL
                answer_text = None
                answer_option_id = None
                image_url = None
                
                if answer_key in result_dict:
                    answer_data = result_dict[answer_key]
                    
                    if answer_data['type'] == 'text':
                        # 文字題：只填 answer_text
                        answer_text = answer_data['value']
                        
                    elif answer_data['type'] == 'choice':
                        # 選擇題：只填 answer_option_id
                        selected_value = answer_data.get('selectedValues')
                        
                        if selected_value:
                            # 查找對應的選項 ID
                            option_query = """
                            SELECT id FROM question_options
                            WHERE question_id = %s AND (label = %s OR value = %s)
                            """
                            cursor.execute(option_query, (question_id, selected_value, selected_value))
                            option_result = cursor.fetchone()
                            if option_result:
                                answer_option_id = option_result['id']
                                
                    elif answer_data['type'] == 'image':
                        # 圖片題：只填 image_url
                        if image_key in result_dict:
                            file_info = result_dict[image_key]
                            file_object = file_info['file_object']
                            
                            # 上傳到 S3
                            uploader = Uploader()
                            saved_url = await uploader.upload_file(file_object, "petbuddy-img")
                            
                            if saved_url:
                                image_url = saved_url
                            else:
                                raise Exception(f"圖片上傳失敗 - 問題 {i + 1}")
                
                # 插入答案（每個欄位只存放對應的內容，其他為 NULL）
                insert_ans = """
                INSERT INTO form_answers 
                (submission_id, question_id, answer_text, answer_option_id, image_url)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_ans, (
                    sub_id, 
                    question_id, 
                    answer_text,        # 只有文字題才有值
                    answer_option_id,   # 只有選擇題才有值
                    image_url           # 只有圖片題才有值
                ))
            
            conn.commit()
            
            return JSONResponse(content={
                "success": True, 
                "message": "表單提交成功",
                "submission_id": sub_id
            })
        
        else:

            result_dict = await request.json()
            
            form_id = result_dict.get("formId")
            
            # 插入提交記錄
            insert_sub = """
            INSERT INTO form_submissions (form_id, submitter_user_id)
            VALUES (%s, %s)
            """
            cursor.execute(insert_sub, (form_id, user_id))
            conn.commit() 
            sub_id = cursor.lastrowid
            
            # 從 answers 物件中處理答案
            answers = result_dict.get("answers", {})
            
            for question_key, answer_data in answers.items():
                # 從 question_key (如 "q1") 提取問題序號
                question_order = int(question_key.replace("q", ""))
                
                # 查詢問題 ID
                question_id_query = """
                SELECT id FROM form_questions
                WHERE form_id = %s AND question_order = %s
                """
                cursor.execute(question_id_query, (form_id, question_order))
                question_result = cursor.fetchone()
                
                if not question_result:
                    continue
                    
                question_id = question_result['id']
                
                # 初始化所有欄位為 NULL
                answer_text = None
                answer_option_id = None
                
                if answer_data['type'] == 'text':
                    # 文字題：只填 answer_text
                    answer_text = answer_data['value']
                    
                elif answer_data['type'] == 'choice':
                    # 選擇題：只填 answer_option_id
                    selected_value = answer_data.get('selectedValues')
                    
                    if selected_value:
                        option_query = """
                        SELECT id FROM question_options
                        WHERE question_id = %s AND (label = %s OR value = %s)
                        """
                        cursor.execute(option_query, (question_id, selected_value, selected_value))
                        option_result = cursor.fetchone()
                        if option_result:
                            answer_option_id = option_result['id']
                
                # 插入答案（移除 image_url 欄位）
                insert_ans = """
                INSERT INTO form_answers 
                (submission_id, question_id, answer_text, answer_option_id)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(insert_ans, (
                    sub_id, 
                    question_id, 
                    answer_text,
                    answer_option_id
                ))
            
            conn.commit()
            
            return JSONResponse(content={
                "success": True, 
                "message": "表單提交成功",
                "submission_id": sub_id
            })
            
    except Exception as e:
        print(e)
        if conn:
            conn.rollback()
        return JSONResponse(
            status_code=500, 
            content={"error": f"提交失敗: {str(e)}"}
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()