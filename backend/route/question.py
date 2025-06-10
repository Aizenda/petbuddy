from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Literal, Optional
from ..model.db_connect import mysql_pool

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
        raise HTTPException(500, f"儲存表單及題目失敗：{e}")

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

    finally:
        cursor.close()
        conn.close()