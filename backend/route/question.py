from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Literal
from ..model.db_connect import mysql_pool
from ..model.JWT import *
from ..model.upload_function import *

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
    uploader = Uploader()
    conn = mysql_pool.get_connection()
    cursor = conn.cursor()

    try:
        # ─── 1. 建立 submission 主檔 ─────────────────────────
        if "application/json" in ct:
            payload = await request.json()
            form_id      = int(payload["formId"])
            submitted_at = payload["submittedAt"]
            answers_src  = payload["answers"]
        elif "multipart/form-data" in ct:
            form         = await request.form()
            form_id      = int(form.get("formId"))
            submitted_at = form.get("submittedAt")
            answers_src  = None
        else:
            raise HTTPException(status_code=415, detail="Unsupported Content-Type")

        cursor.execute(
            """
            INSERT INTO form_submissions (form_id, submitter_user_id, submitted_at)
            VALUES (%s, %s, %s)
            """,
            (form_id, current_user_id, submitted_at)
        )
        submission_id = cursor.lastrowid

        # ─── 2. 處理文字 & 選擇題 ─────────────────────────────
        if answers_src is not None:
            # JSON path
            for qkey, ans in answers_src.items():
                qid = extract_question_id(qkey)
                if ans["type"] == "text":
                    cursor.execute(
                        "INSERT INTO response_answers (submission_id, question_id, answer_text) VALUES (%s, %s, %s)",
                        (submission_id, qid, ans["value"])
                    )
                elif ans["type"] == "choice":
                    sel = ans["selectedValues"]
                    opt = sel if isinstance(sel, str) else sel[0]
                    cursor.execute(
                        "SELECT id FROM question_options WHERE form_id=%s AND title=%s",
                        (form_id, opt)
                    )
                    row = cursor.fetchone()
                    if row:
                        cursor.execute(
                            "INSERT INTO response_answers (submission_id, question_id, answer_option_id) VALUES (%s, %s, %s)",
                            (submission_id, qid, row[0])
                        )
        else:
            # FormData path: 先文字+選擇
            for key, raw in form.multi_items():
                if not key.startswith("answer_"): continue
                qkey = key.replace("answer_", "")
                ans  = json.loads(raw)
                qid  = extract_question_id(qkey)
                if ans["type"] == "text":
                    cursor.execute(
                        "INSERT INTO response_answers (submission_id, question_id, answer_text) VALUES (%s, %s, %s)",
                        (submission_id, qid, ans["value"])
                    )
                elif ans["type"] == "choice":
                    sel = ans["selectedValues"]
                    opt = sel if isinstance(sel, str) else sel[0]
                    cursor.execute(
                        "SELECT id FROM question_options WHERE form_id=%s AND title=%s",
                        (form_id, opt)
                    )
                    row = cursor.fetchone()
                    if row:
                        cursor.execute(
                            "INSERT INTO response_answers (submission_id, question_id, answer_option_id) VALUES (%s, %s, %s)",
                            (submission_id, qid, row[0])
                        )

        # ─── 3. 處理圖片題 ─────────────────────────────────────
        if "multipart/form-data" in ct:
            for key, val in form.multi_items():
                if not key.startswith("image_"): continue
                qkey       = key.replace("image_", "")
                qid        = extract_question_id(qkey)
                uploadFile: UploadFile = val
                # 上傳 S3
                file_url = await uploader.upload_file(uploadFile, bucket="你的-bucket-name")
                cursor.execute(
                    "INSERT INTO response_answers (submission_id, question_id, image_url) VALUES (%s, %s, %s)",
                    (submission_id, qid, file_url)
                )

        conn.commit()
        return {"ok": True, "submission_id": submission_id}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
