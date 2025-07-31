from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Literal, Optional, Dict, Any
from fastapi.security import HTTPBearer
from ..model.db_connect import mysql_pool
from ..model.JWT import *
from ..model.upload_function import *
from ..model.redis_sever import redis_cache  # 使用統一實例
import traceback
import json


router = APIRouter()
security = HTTPBearer()

# ---------- Pydantic Models ----------
class OptionIn(BaseModel):
    id: int
    text: str
    value: str

class QuestionIn(BaseModel):
    id: int
    title: str
    type: Literal["text", "choice", "image"]
    required: bool
    options: List[OptionIn] = []

class FormCreateRequest(BaseModel):
    formTitle: str
    postId: int
    questions: List[QuestionIn]

class FormSubmissionRequest(BaseModel):
    postId: int
    adopterId: Optional[int] = None

class FormAnswerData(BaseModel):
    answers: Dict[str, Any]

# ---------- 回應模型 ----------
class BaseResponse(BaseModel):
    ok: bool
    message: str

class FormCreateResponse(BaseResponse):
    formId: Optional[int] = None

class FormDetailResponse(BaseResponse):
    form: Optional[Dict[str, Any]] = None

class FormSubmissionResponse(BaseResponse):
    submissionId: Optional[int] = None

class FormAnswersResponse(BaseResponse):
    data: Optional[Dict[str, Any]] = None

class FormCheckResponse(BaseResponse):
    data: Optional[List[Dict[str, Any]]] = None

# ---------- 資料庫輔助函數 ----------
async def get_db_connection():
    """取得資料庫連線"""
    return mysql_pool.get_connection()

def close_db_resources(cursor, conn):
    """關閉資料庫資源"""
    if cursor:
        cursor.close()
    if conn:
        conn.close()

# ---------- 快取輔助函數 ----------
def get_form_cache_key(post_id: int) -> str:
    """取得表單快取鍵"""
    return f"form:{post_id}"

def get_submission_cache_key(post_id: int, user_id: int) -> str:
    """取得表單填寫紀錄快取鍵"""
    return f"submission:{post_id}:{user_id}"

def get_answers_cache_key(post_id: int, user_id: int) -> str:
    """取得表單答案快取鍵"""
    return f"answers:{post_id}:{user_id}"

def invalidate_form_caches(post_id: int = None, user_id: int = None):
    """清除表單相關快取 - 使用統一的快取清除方法"""
    return redis_cache.invalidate_adoption_caches(user_id=user_id, post_id=post_id)

# ---------- 驗證輔助函數 ----------
async def validate_post_exists(cursor, post_id: int) -> bool:
    """驗證送養文章是否存在"""
    cursor.execute("SELECT 1 FROM send WHERE id = %s", (post_id,))
    return cursor.fetchone() is not None

async def validate_form_exists(cursor, post_id: int) -> Optional[int]:
    """驗證表單是否存在，回傳表單 ID"""
    cursor.execute("SELECT id FROM forms WHERE post_id = %s", (post_id,))
    result = cursor.fetchone()
    return result[0] if result else None

async def validate_user_is_post_owner(cursor, post_id: int, user_id: int) -> bool:
    """驗證使用者是否為送養文章擁有者"""
    cursor.execute("SELECT user_id FROM send WHERE id = %s", (post_id,))
    result = cursor.fetchone()
    print(result)
    return result and result["user_id"] == user_id

async def validate_submission_exists(cursor, form_id: int, user_id: int) -> Optional[int]:
    """驗證表單填寫紀錄是否存在，回傳 submission ID"""
    cursor.execute(
        "SELECT id FROM form_submissions WHERE form_id = %s AND submitter_user_id = %s",
        (form_id, user_id)
    )
    result = cursor.fetchone()
    return result["id"] if result else None

# ---------- 表單查詢函數 ----------
async def fetch_form_basic_info(cursor, post_id: int) -> Optional[Dict[str, Any]]:
    """查詢表單基本資訊"""
    cursor.execute("""
        SELECT 
            id AS formId,
            post_id AS postId,
            title AS formTitle,
            created_at AS createdAt
        FROM forms
        WHERE post_id = %s
    """, (post_id,))
    return cursor.fetchone()

async def fetch_form_questions(cursor, form_id: int) -> List[Dict[str, Any]]:
    """查詢表單問題清單"""
    cursor.execute("""
        SELECT 
            id AS questionId,
            question_key,
            question_order AS questionOrder,
            type,
            title,
            is_required AS required
        FROM form_questions
        WHERE form_id = %s
        ORDER BY question_order
    """, (form_id,))
    return cursor.fetchall()

async def fetch_question_options(cursor, question_ids: List[int]) -> List[Dict[str, Any]]:
    """查詢問題選項"""
    if not question_ids:
        return []
    
    fmt = ",".join(["%s"] * len(question_ids))
    cursor.execute(f"""
        SELECT
            question_id AS questionId,
            id AS optionId,
            option_order AS optionOrder,
            label,
            value
        FROM question_options
        WHERE question_id IN ({fmt})
        ORDER BY question_id, option_order
    """, question_ids)
    return cursor.fetchall()

async def build_complete_form_data(cursor, post_id: int) -> Optional[Dict[str, Any]]:
    """組建完整的表單資料"""
    # 查詢表單基本資料
    form = await fetch_form_basic_info(cursor, post_id)
    if not form:
        return None

    form_id = form["formId"]
    
    # 查詢問題清單
    questions = await fetch_form_questions(cursor, form_id)
    
    # 查詢選項
    question_ids = [q["questionId"] for q in questions]
    options = await fetch_question_options(cursor, question_ids)
    
    # 將選項配對回問題
    for q in questions:
        q["options"] = [opt for opt in options if opt["questionId"] == q["questionId"]]
    
    form["questions"] = questions
    form["createdAt"] = form["createdAt"].isoformat()
    
    return form

# ---------- 表單操作函數 ----------
async def create_form_record(cursor, conn, payload: FormCreateRequest) -> int:
    """建立表單主體記錄"""
    cursor.execute(
        "INSERT INTO forms (post_id, title) VALUES (%s, %s)",
        (payload.postId, payload.formTitle)
    )
    conn.commit()
    return cursor.lastrowid

async def create_form_questions(cursor, conn, form_id: int, questions: List[QuestionIn]):
    """建立表單問題"""
    for order, q in enumerate(questions, start=1):
        question_key = f"q{q.id}"
        cursor.execute(
            """
            INSERT INTO form_questions (form_id, question_key, question_order, type, title, is_required)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (form_id, question_key, order, q.type, q.title, int(q.required))
        )
        question_id = cursor.lastrowid

        # 若為選擇題，寫入選項
        if q.type == "choice":
            await create_question_options(cursor, question_id, q.options)
    
    conn.commit()

async def create_question_options(cursor, question_id: int, options: List[OptionIn]):
    """建立問題選項"""
    for opt_order, opt in enumerate(options, start=1):
        cursor.execute(
            """
            INSERT INTO question_options (question_id, option_order, label, value)
            VALUES (%s, %s, %s, %s)
            """,
            (question_id, opt_order, opt.text, opt.value)
        )

async def create_submission_record(cursor, conn, form_id: int, user_id: int) -> int:
    """建立表單填寫記錄"""
    cursor.execute(
        "INSERT INTO form_submissions (form_id, submitter_user_id) VALUES (%s, %s)",
        (form_id, user_id)
    )
    conn.commit()
    return cursor.lastrowid

async def process_form_answers(result_dict: Dict[str, Any], submission_id: int, cursor, conn):
    """處理表單答案"""
    total_questions = int(result_dict["totalQuestions"])
    
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

        values.append((submission_id, qid, ans_text, ans_option, ans_image))

    # 寫入資料庫
    if values:
        cursor.executemany(insert_query, values)
        conn.commit()

async def fetch_submission_answers(cursor, submission_id: int) -> Dict[str, Any]:
    """查詢表單答案資料"""
    cursor.execute("""
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
        ORDER BY q.question_order
    """, (submission_id,))
    
    rows = cursor.fetchall()
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
    
    return result

# ---------- RESTful API 端點 ----------

@router.post(
    "/api/posts/{post_id}/forms",
    tags=["Forms"],
    summary="建立表單",
    description="為指定的送養文章建立表單",
    response_model=FormCreateResponse,
    responses={
        201: {"description": "表單建立成功"},
        400: {"description": "請求格式錯誤"},
        401: {"description": "未授權"},
        404: {"description": "找不到送養文章"},
        409: {"description": "表單已存在"},
        500: {"description": "伺服器錯誤"},
    }
)
async def create_form(
    post_id: int,
    payload: FormCreateRequest,
    user_data: dict = Depends(JWT.get_current_user)
):
    """
    為指定的送養文章建立表單

    - **post_id**: 送養文章 ID (路徑參數)
    - **formTitle**: 表單標題
    - **postId**: 對應的送養文章 ID (必須與路徑參數一致)
    - **questions**: 問題清單，每題可包含選項
    """
    if post_id != payload.postId:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="路徑參數與請求體中的 postId 不一致"
        )

    conn = None
    cursor = None
    try:
        conn = await get_db_connection()
        cursor = conn.cursor()

        # 檢查送養文章是否存在
        if not await validate_post_exists(cursor, post_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到對應的送養文章"
            )

        # 檢查是否已存在表單
        if await validate_form_exists(cursor, post_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="表單已存在"
            )

        # 建立表單
        form_id = await create_form_record(cursor, conn, payload)
        await create_form_questions(cursor, conn, form_id, payload.questions)

        # ✅ 清除相關快取
        redis_cache.invalidate_adoption_caches(post_id=post_id)

        return JSONResponse(
            {"ok": True, "message": "表單建立成功", "formId": form_id},
            status_code=201
        )

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立表單失敗：{str(e)}"
        )
    finally:
        close_db_resources(cursor, conn)


@router.get(
    "/api/posts/{post_id}/forms",
    tags=["Forms"],
    summary="取得表單",
    description="取得指定送養文章的表單資料",
    response_model=FormDetailResponse,
    responses={
        200: {"description": "成功取得表單資料"},
        401: {"description": "未授權"},
        404: {"description": "找不到表單"},
        500: {"description": "伺服器錯誤"},
    }
)
async def get_form(
    post_id: int,
    user_data: dict = Depends(JWT.get_current_user)
):
    """取得指定送養文章的表單資料（包含所有問題與選項）"""
    
    # 先檢查快取
    cache_key = get_form_cache_key(post_id)
    cached_form = redis_cache.get_cache(cache_key)
    if cached_form:
        return JSONResponse({"ok": True, "form": cached_form}, status_code=200)

    conn = None
    cursor = None
    try:
        conn = await get_db_connection()
        cursor = conn.cursor(dictionary=True)

        form = await build_complete_form_data(cursor, post_id)
        
        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到這張表單"
            )

        # 設定快取
        redis_cache.set_cache(cache_key, form, ttl=600)

        return JSONResponse({"ok": True, "form": form}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        close_db_resources(cursor, conn)


@router.post(
    "/api/posts/{post_id}/forms/submissions",
    tags=["Forms"],
    summary="提交表單",
    description="提交指定送養文章的表單答案",
    response_model=FormSubmissionResponse,
    responses={
        201: {"description": "表單提交成功"},
        401: {"description": "未授權"},
        404: {"description": "找不到表單"},
        409: {"description": "重複提交或送養人不能填表"},
        500: {"description": "伺服器錯誤"},
    }
)
async def submit_form(post_id: int, request: Request):
    """提交表單答案"""
    conn = None
    cursor = None

    try:
        conn = await get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 驗證用戶身份
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未授權"
            )
        
        user_id = user_data["userid"]

        # 解析表單資料
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

        form_id = result_dict["formId"]

        # 檢查是否為送養人（送養人不能填表）
        if await validate_user_is_post_owner(cursor, post_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="送養人無法填表"
            )
        
        # 檢查是否重複填表
        if await validate_submission_exists(cursor, form_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="請勿重複填表"
            )

        # 建立填寫記錄
        submission_id = await create_submission_record(cursor, conn, form_id, user_id)
        
        # 處理答案
        await process_form_answers(result_dict, submission_id, cursor, conn)

        # ✅ 清除相關快取
        redis_cache.invalidate_adoption_caches(
            user_id=user_id,
            post_id=post_id
        )

        return JSONResponse(
            {"ok": True, "message": "表單提交成功", "submissionId": submission_id},
            status_code=201
        )
    
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print(str(e))
        if conn:
            conn.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        close_db_resources(cursor, conn)


@router.put(
    "/api/posts/{post_id}/forms/submissions",
    tags=["Forms"],
    summary="修改表單答案",
    description="修改已提交的表單答案",
    response_model=BaseResponse,
    responses={
        200: {"description": "修改成功"},
        401: {"description": "未授權"},
        404: {"description": "找不到填寫記錄"},
        500: {"description": "伺服器錯誤"},
    }
)
async def update_form_submission(post_id: int, request: Request):
    """修改表單答案"""
    conn = None
    cursor = None

    try:
        conn = await get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 驗證用戶身份
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未授權"
            )

        user_id = user_data["userid"]

        # 解析表單資料
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

        form_id = result_dict["formId"]

        # 找出原本的 submission_id
        submission_id = await validate_submission_exists(cursor, form_id, user_id)
        if not submission_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="查無填寫紀錄"
            )

        # 先刪除原有答案
        cursor.execute("DELETE FROM form_answers WHERE submission_id = %s", (submission_id,))

        # 重建新答案
        await process_form_answers(result_dict, submission_id, cursor, conn)

        # ✅ 清除相關快取
        redis_cache.invalidate_adoption_caches(
            user_id=user_id,
            post_id=post_id
        )

        return JSONResponse({"ok": True, "message": "表單修改成功"}, status_code=200)

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        close_db_resources(cursor, conn)


@router.get(
    "/api/posts/{post_id}/forms/submissions/{user_id}",
    tags=["Forms"],
    summary="查看表單答案",
    description="送養人查看指定領養人的表單答案",
    response_model=FormAnswersResponse,
    responses={
        200: {"description": "成功取得答案資料"},
        401: {"description": "未授權"},
        403: {"description": "無權查看"},
        404: {"description": "找不到填寫記錄"},
        500: {"description": "伺服器錯誤"},
    }
)
async def get_form_answers(
    post_id: int,
    user_id: int,
    user_data: dict = Depends(JWT.get_current_user)
):
    """送養人查看指定領養人的表單答案"""
    
    # 先檢查快取
    cache_key = get_answers_cache_key(post_id, user_id)
    cached_answers = redis_cache.get_cache(cache_key)
    if cached_answers:
        return JSONResponse({"ok": True, "data": cached_answers}, status_code=200)

    conn = None
    cursor = None

    try:
        conn = await get_db_connection()
        cursor = conn.cursor(dictionary=True)

        current_user_id = int(user_data["userid"])

        # 驗證是否為送養人
        if not await validate_user_is_post_owner(cursor, post_id, current_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="你無權查看這篇貼文的表單"
            )

        # 查該領養人是否填過這篇貼文的表單
        cursor.execute("""
            SELECT s.id
            FROM form_submissions AS s
            LEFT JOIN forms AS f ON f.id = s.form_id
            WHERE f.post_id = %s AND s.submitter_user_id = %s
        """, (post_id, user_id))
        
        submission = cursor.fetchone()
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="該領養人尚未填寫表單"
            )

        submission_id = submission["id"]
        result = await fetch_submission_answers(cursor, submission_id)

        # 設定快取
        redis_cache.set_cache(cache_key, result, ttl=300)
        
        return JSONResponse({"ok": True, "data": result}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        close_db_resources(cursor, conn)


@router.post(
    "/api/forms/check",
    tags=["Forms"],
    summary="批量檢查表單狀態",
    description="批量檢查多個送養文章的表單存在狀態和填寫狀態",
    response_model=FormCheckResponse,
    responses={
        200: {"description": "檢查完成"},
        401: {"description": "未授權"},
        500: {"description": "伺服器錯誤"},
    }
)
async def check_forms_status(
    data: List[FormSubmissionRequest],
    user_data: dict = Depends(JWT.get_current_user)
):
    """批量檢查表單狀態"""
    conn = None
    cursor = None
    results = []
    
    try:
        conn = await get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
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
            filled = None
            if adopter_id is not None:
                cursor.execute("""
                    SELECT 1 FROM form_submissions fs 
                    JOIN forms f ON fs.form_id = f.id 
                    WHERE f.post_id = %s AND fs.submitter_user_id = %s
                    LIMIT 1
                """, (post_id, adopter_id))
                filled = cursor.fetchone() is not None
            
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
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        close_db_resources(cursor, conn)


@router.post(
    "/api/posts/{post_id}/complete",
    tags=["Posts"],
    summary="完成送養",
    description="將送養文章標記為完成並搬移至歷史記錄",
    response_model=BaseResponse,
    responses={
        200: {"description": "送養完成"},
        401: {"description": "未授權"},
        404: {"description": "找不到送養文章"},
        500: {"description": "伺服器錯誤"},
    }
)
async def complete_adoption(post_id: int, user_data: dict = Depends(JWT.get_current_user)):
    """完成送養"""
    conn = None
    cursor = None
    try:
        conn = await get_db_connection()
        cursor = conn.cursor(dictionary=True)

        user_id = user_data["userid"]

        # 取得送養貼文
        cursor.execute("SELECT * FROM send WHERE id = %s", (post_id,))
        send_data = cursor.fetchone()

        if not send_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="送養貼文不存在"
            )

        # 插入到 send_history
        insert_history_query = """
        INSERT INTO send_history (
            original_send_id, user_id, pet_name, pet_breed, pet_kind, pet_sex,
            pet_bodytype, pet_colour, pet_place, pet_describe,
            pet_ligation_status, pet_age, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_history_query, (
            send_data['id'],
            send_data['user_id'],
            send_data['pet_name'],
            send_data['pet_breed'],
            send_data['pet_kind'],
            send_data['pet_sex'],
            send_data['pet_bodytype'],
            send_data['pet_colour'],
            send_data['pet_place'],
            send_data['pet_describe'],
            send_data['pet_ligation_status'],
            send_data['pet_age'],
            send_data['created_at']
        ))

        # 取得剛插入的歷史 send_history.id
        history_send_id = cursor.lastrowid

        # 取得所有圖片
        cursor.execute("SELECT img_url FROM imgurl WHERE send_id = %s", (post_id,))
        img_list = cursor.fetchall()

        # 複製到 imgurl_history
        for img in img_list:
            cursor.execute("INSERT INTO imgurl_history (send_id, img_url) VALUES (%s, %s)", 
                         (history_send_id, img['img_url']))

        # 刪除原始資料
        cursor.execute("DELETE FROM imgurl WHERE send_id = %s", (post_id,))
        cursor.execute("DELETE FROM likes WHERE send_id = %s", (post_id,))
        cursor.execute("DELETE FROM send WHERE id = %s", (post_id,))

        conn.commit()
        
        # ✅ 清除相關快取
        redis_cache.invalidate_adoption_caches(
            user_id=user_id,
            post_id=post_id
        )
        
        return JSONResponse({"ok": True, "message": "送養已完成並搬移至歷史紀錄"}, status_code=200)

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        close_db_resources(cursor, conn)


@router.delete(
    "/api/posts/{post_id}",
    tags=["Posts"],
    summary="取消送養",
    description="取消送養文章並刪除相關資料",
    response_model=BaseResponse,
    responses={
        200: {"description": "取消成功"},
        401: {"description": "未授權"},
        403: {"description": "無權刪除"},
        404: {"description": "找不到送養文章"},
        500: {"description": "伺服器錯誤"},
    }
)
async def cancel_adoption(post_id: int, user_data: dict = Depends(JWT.get_current_user)):
    """取消送養"""
    conn = None
    cursor = None
    try:
        conn = await get_db_connection()
        cursor = conn.cursor(dictionary=True)

        user_id = user_data["userid"]

        # 確認這篇貼文是此使用者發的
        if not await validate_user_is_post_owner(cursor, post_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="你無權刪除此貼文"
            )

        # 檢查貼文是否存在
        if not await validate_post_exists(cursor, post_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到送養文章"
            )

        # 依序刪除資料
        cursor.execute("DELETE FROM imgurl WHERE send_id = %s", (post_id,))
        cursor.execute("DELETE FROM likes WHERE send_id = %s", (post_id,))
        cursor.execute("DELETE FROM send WHERE id = %s", (post_id,))

        conn.commit()
        
        # ✅ 清除相關快取
        redis_cache.invalidate_adoption_caches(
            user_id=user_id,
            post_id=post_id
        )
        
        return JSONResponse({"ok": True, "message": "已成功取消刊登"}, status_code=200)

    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    finally:
        close_db_resources(cursor, conn)