from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ..model.db_connect import mysql_pool
from ..model.redis_sever import redis_cache  # 使用統一實例
from backend.model.JWT import JWT
import time

router = APIRouter()


def get_current_user(request: Request):
    """驗證用戶身份並返回用戶資料"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse({"ok": False, "message": "未登入"}, status_code=401)
    return user_data


@router.get("/api/adoptions/{id}", tags=["Adoptions"])
async def get_adoption_detail(
    id: int,
    request: Request,
    user_data: dict = Depends(get_current_user)
):
    """
    取得單筆送養貼文的詳細資訊（含圖片）

    - **id**: 貼文的 ID
    - **Authorization**: Bearer Token
    """
    user_id = user_data.get("userid")
    cache_key = f"adoption_detail:{id}"

    # 嘗試從快取取得
    start = time.time()
    cached_data = redis_cache.get_cache(cache_key)
    end = time.time()
    print(f"Redis round trip time: {(end - start) * 1000:.2f} ms")

    if cached_data:
        return JSONResponse({
            "ok": True,
            "data": cached_data,
            "user_id": user_id,
            "cached": True
        }, status_code=200)

    conn = None
    cursor = None

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        select_query = """
        SELECT 
        s.*,
        COALESCE(JSON_ARRAYAGG(i.img_url), JSON_ARRAY()) AS images
        FROM send AS s
        LEFT JOIN imgurl AS i
        ON i.send_id = s.id
        WHERE s.id = %s
        """

        cursor.execute(select_query, (id,))
        data = cursor.fetchone()

        if not data:
            return JSONResponse({"ok": False, "message": "找不到資料"}, status_code=404)

        json_data = jsonable_encoder(data)

        # 寫入快取，TTL 可自訂（這裡預設 10 分鐘）
        redis_cache.set_cache(cache_key, json_data, ttl=600)

        return JSONResponse({
            "ok": True,
            "data": json_data,
            "user_id": user_id,
            "cached": False
        }, status_code=200)

    except Exception as e:
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            

@router.post("/api/adoptions/{id}/likes", tags=["Adoptions"])
async def like_adoption_post(
    id: int,
    request: Request,
    user_data: dict = Depends(get_current_user)
):
    """
    使用者對某筆送養貼文表達認養意願（加入 likes）

    - **id**: 貼文 ID
    - **Authorization**: Bearer Token
    """
    conn = None
    cursor = None
    user_id = user_data.get("userid")

    like_key = f"like:{user_id}:{id}"

    # 如果 Redis 中存在重複紀錄，直接擋掉
    if redis_cache.get_cache(like_key):
        return JSONResponse({
            "ok": False,
            "message": "請勿重複認養"
        }, status_code=409)

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        # 查資料庫是否真的已經存在（避免 Redis 假陽性）
        select_query = """
        SELECT 1 FROM likes
        WHERE user_id = %s AND send_id = %s
        """
        cursor.execute(select_query, (user_id, id))
        exists = cursor.fetchone()

        if exists:
            redis_cache.set_cache(like_key, True, ttl=3600)  # 快取一小時
            return JSONResponse({
                "ok": False,
                "message": "已通知送養人，請勿重複認養"
            }, status_code=409)

        # 新增到 likes 表
        insert_sql = """
        INSERT INTO likes (user_id, send_id)
        VALUES (%s, %s);
        """
        cursor.execute(insert_sql, (user_id, id))
        conn.commit()

        # 寫入快取避免短時間內重複點擊
        redis_cache.set_cache(like_key, True, ttl=3600)

        # ✅ 清除相關快取
        # 1. 清除用戶收藏列表快取
        redis_cache.delete_pattern(f"user:{user_id}:adoptions:favorites")
        
        # 2. 查詢並清除送養人的發佈列表快取
        cursor.execute("SELECT user_id FROM send WHERE id = %s", (id,))
        post_owner = cursor.fetchone()
        if post_owner:
            owner_id = post_owner["user_id"]
            redis_cache.delete_pattern(f"user:{owner_id}:adoptions:published")

        return JSONResponse({"ok": True}, status_code=200)

    except Exception as e:
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()