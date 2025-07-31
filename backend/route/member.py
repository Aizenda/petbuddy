from fastapi import APIRouter,Request,Query,File,UploadFile,Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ..model.db_connect import mysql_pool
from backend.model.redis_sever import redis_cache  # 使用統一實例
from backend.model.JWT import JWT
from backend.model.upload_function import Uploader
from pydantic import BaseModel
import bcrypt
from datetime import datetime
import json

router = APIRouter()

class UpdateUser(BaseModel):
    name: str
    phone: str
    email: str
    address: str = ""
    profession: str
    live: str = ""
    pet_experience: str = ""

class PasswordChange(BaseModel):
    old_password: str
    new_password: str
    
	



@router.get("/api/user")
async def get_user(request:Request):
	conn = None
	cursor = None

	try:
		
		conn = mysql_pool.get_connection()
		cursor = conn.cursor(dictionary = True)

		token = request.headers.get("Authorization", "").replace("Bearer ", "")
		user_data = JWT.decode_jwt(token)

		if not user_data:
			return JSONResponse({"ok":False,"message": "未登入"},status_code=401)

		user_id = user_data.get("userid")

		select_user = """
		SELECT * FROM users
		WHERE id = %s
		"""

		cursor.execute(select_user,(user_id,))
		data = cursor.fetchone()
		data = jsonable_encoder(data)
		return JSONResponse({"ok":True,"data":data},status_code=200) 

	except Exception as e:
		return JSONResponse({"ok":False,"message":str(e)},status_code=500)
	
	finally:
		if cursor:
				cursor.close()
		if conn:
				conn.close()
	

@router.get(
    "/api/member/adoptions/published",
    tags=["Adoption"],
    summary="取得我發布的送養貼文",
    description="查詢目前登入使用者所發佈的送養資料，包含收藏者資訊與圖片",
    responses={
        200: {
            "description": "成功取得送養資料",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "data": [
                            {
                                "send_id": 1,
                                "pet_name": "小白",
                                "liker_id": 7,
                                "liker_name": "王大明",
                                "phone": "0912345678",
                                "images": [
                                    "https://s3.amazonaws.com/your-bucket/img1.jpg",
                                    "https://s3.amazonaws.com/your-bucket/img2.jpg"
                                ]
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "未授權"},
        500: {"description": "伺服器錯誤"},
    }
)
async def get_my_adoptions(request: Request):
    conn = None
    cursor = None

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse({"ok": False, "message": "未登入"}, status_code=401)

    user_id = user_data.get("userid")
    cache_key = f"user:{user_id}:adoptions:published"

    # 嘗試從 Redis 讀取快取
    cached = redis_cache.get_cache(cache_key)
    if cached:
        return JSONResponse({"ok": True, "data": cached})

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            s.id AS send_id,
            s.pet_name,
            u.id AS liker_id,
            u.name AS liker_name,
            u.phone,
            JSON_ARRAYAGG(img.img_url) AS images
        FROM send AS s
        LEFT JOIN likes AS l ON l.send_id = s.id
        LEFT JOIN users AS u ON u.id = l.user_id
        LEFT JOIN imgurl AS img ON img.send_id = s.id
        WHERE s.user_id = %s
        GROUP BY s.id, u.id
        ORDER BY s.id DESC;
        """
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()

        # 快取 5 分鐘
        redis_cache.set_cache(cache_key, data, 300)

        return JSONResponse({"ok": True, "data": data}, status_code=200)

    except Exception as e:
        print("查詢錯誤:", e)
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
		
@router.get(
    "/api/member/adoptions/favorites",
    tags=["Adoption"],
    summary="取得我收藏的送養貼文",
    description="查詢目前登入使用者收藏的送養清單，包含送養人資訊與圖片",
    responses={
        200: {"description": "成功"},
        401: {"description": "未登入"},
        500: {"description": "伺服器錯誤"},
    }
)
async def get_favorite_adoptions(request: Request):
    conn = None
    cursor = None

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse({"ok": False, "message": "未登入"}, status_code=401)

    user_id = user_data.get("userid")
    cache_key = f"user:{user_id}:adoptions:favorites"

    cached = redis_cache.get_cache(cache_key)
    if cached:
        return JSONResponse({"ok": True, "data": cached})

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT
            s.id AS send_id,
            s.pet_name,
            s.pet_kind,
            s.pet_breed,
            GROUP_CONCAT(i.img_url) AS images,
            su.name AS sender_name,
            l.user_id AS adopter_id
        FROM likes AS l
        JOIN send AS s ON l.send_id = s.id
        JOIN users AS su ON s.user_id = su.id         
        LEFT JOIN imgurl AS i ON i.send_id = s.id
        WHERE l.user_id = %s
        GROUP BY s.id, su.id, l.liked_at
        ORDER BY l.liked_at DESC;
        """
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()

        redis_cache.set_cache(cache_key, data, 300)

        return JSONResponse({"ok": True, "data": data}, status_code=200)

    except Exception as e:
        print(e)
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.delete(
    "/api/member/adoptions/cancel",
    tags=["Adoption"],
    summary="取消送養申請",
    description="送養人可取消某位申請者的送養申請，會一併刪除填表與按讚紀錄，並清除快取。",
    responses={
        200: {"description": "取消成功"},
        401: {"description": "未登入"},
        500: {"description": "取消失敗"},
    }
)
async def cancel_adoption(
    request: Request,
    post_id: int = Query(..., description="送養貼文 ID"),
    adopter_id: int = Query(..., description="欲取消的領養者 ID")
):
    conn = None
    cursor = None

    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            return JSONResponse({"ok": False, "message": "未登入"}, status_code=401)

        conn = mysql_pool.get_connection()
        cursor = conn.cursor()

        # 查 form_id 並刪除對應填單紀錄
        cursor.execute("SELECT id FROM forms WHERE post_id = %s", (post_id,))
        form_row = cursor.fetchone()
        if form_row:
            form_id = form_row[0]
            cursor.execute(
                "DELETE FROM form_submissions WHERE form_id = %s AND submitter_user_id = %s",
                (form_id, adopter_id)
            )

        # 刪除 likes 記錄
        cursor.execute(
            "DELETE FROM likes WHERE user_id = %s AND send_id = %s",
            (adopter_id, post_id)
        )

        conn.commit()

        # 同步清除 Redis 快取
        redis_cache.delete(f"user:{adopter_id}:adoptions:favorites")

        return JSONResponse({"ok": True}, status_code=200)

    except Exception as e:
        print("取消失敗:", e)
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get(
    "/api/member/adoptions/all",
    tags=["Adoption"],
    summary="取得所有我發佈的送養貼文",
    description="取得目前登入使用者發佈的所有送養貼文與圖片（不含收藏者）",
    responses={
        200: {"description": "成功"},
        401: {"description": "未登入"},
        500: {"description": "伺服器錯誤"},
    }
)
async def get_all_my_adoptions(request: Request):
    conn = None
    cursor = None

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse({"ok": False, "message": "未登入"}, status_code=401)

    user_id = user_data.get("userid")
    cache_key = f"user:{user_id}:adoptions:all"

    cached = redis_cache.get_cache(cache_key)
    if cached:
        return JSONResponse({"ok": True, "data": cached})

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT s.id AS send_id, s.pet_name, JSON_ARRAYAGG(img.img_url) AS images
        FROM send AS s 
        LEFT JOIN imgurl AS img ON img.send_id = s.id
        WHERE s.user_id = %s
        GROUP BY s.id
        ORDER BY s.id ASC;
        """
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()

        redis_cache.set_cache(cache_key, data, )

        return JSONResponse({"ok": True, "data": data}, status_code=200)

    except Exception as e:
        print(e)
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get(
    "/api/member/adoptions/history",
    tags=["Adoption"],
    summary="取得歷史送養紀錄",
    description="查詢使用者過往已完成領養的送養貼文資料，包含圖片與完成時間",
    responses={
        200: {"description": "成功"},
        401: {"description": "未登入"},
        500: {"description": "伺服器錯誤"},
    }
)
async def get_adoption_history(request: Request):
    conn = None
    cursor = None

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse({"ok": False, "message": "未登入"}, status_code=401)

    user_id = user_data.get("userid")
    cache_key = f"user:{user_id}:adoptions:history"

    cached = redis_cache.get_cache(cache_key)
    if cached:
        return JSONResponse({"ok": True, "data": cached})

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT 
            s.original_send_id AS send_id,
            s.pet_name,
            JSON_ARRAYAGG(img.img_url) AS images,
            s.adopted_at
        FROM send_history AS s 
        LEFT JOIN imgurl_history AS img ON img.send_id = s.id
        WHERE s.user_id = %s
        GROUP BY s.id
        ORDER BY s.id ASC;
        """
        cursor.execute(query, (user_id,))
        data = cursor.fetchall()

        for row in data:
            if isinstance(row.get("adopted_at"), datetime):
                row["adopted_at"] = row["adopted_at"].strftime("%Y-%m-%d")

        redis_cache.set_cache(cache_key, data, 300)

        return JSONResponse({"ok": True, "data": data}, status_code=200)

    except Exception as e:
        print(e)
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get(
    "/api/member/profile",
    tags=["Member"],
    summary="取得使用者個人資料",
    description="查詢目前登入使用者的個人基本資料",
    responses={
        200: {
            "description": "成功",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "data": {
                            "name": "許正傑",
                            "phone": "0912345678",
                            "email": "aizenda@example.com",
                            "address": "台北市中山區",
                            "occupation": "工程師",
                            "pet_experience": "有飼養狗狗經驗",
                            "avatar_url": "https://your-bucket/avatar.jpg"
                        }
                    }
                }
            }
        },
        401: {"description": "未登入"},
        404: {"description": "找不到使用者"},
    }
)
async def get_user_profile(request: Request):
    conn = None
    cursor = None
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        if not user_data:
            return JSONResponse(status_code=401, content={"ok": False, "message": "未授權"})

        user_id = user_data["userid"]

        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT name, phone, email, address, occupation, pet_experience, avatar_url
            FROM users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()

        if not user:
            return JSONResponse(status_code=404, content={"ok": False, "message": "找不到使用者"})

        return JSONResponse(status_code=200, content={"ok": True, "data": user})

    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get(
    "/api/member/avatar",
    tags=["Member"],
    summary="取得使用者頭像",
    description="取得目前登入使用者的頭像圖片 URL",
    responses={
        200: {
            "description": "成功",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "avatar_url": "https://s3.amazonaws.com/petbuddy/avatar.jpg"
                    }
                }
            }
        },
        401: {"description": "未登入"},
        404: {"description": "找不到頭像"},
    }
)
async def get_user_avatar(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse(status_code=401, content={"ok": False, "message": "未授權"})

    user_id = user_data["userid"]

    conn = None
    cursor = None
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT avatar_url FROM users WHERE id = %s", (user_id,))
        avatar = cursor.fetchone()

        if not avatar:
            return JSONResponse(status_code=404, content={"ok": False, "message": "找不到頭像"})

        return JSONResponse({"ok": True, "avatar_url": avatar[0]})

    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
				

@router.put(
    "/api/member/avatar",
    tags=["Member"],
    summary="更新使用者頭像",
    description="上傳圖片到 S3，並更新資料庫中的頭像網址。",
    responses={
        200: {
            "description": "成功",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "avatar_url": "https://s3.amazonaws.com/petbuddy/avatar.jpg"
                    }
                }
            }
        },
        401: {"description": "未授權"},
        500: {"description": "圖片上傳失敗或伺服器錯誤"},
    }
)
async def update_user_avatar(request: Request, file: UploadFile = File(...)):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse(status_code=401, content={"ok": False, "message": "未授權"})

    user_id = user_data["userid"]

    # 上傳到 S3
    uploader = Uploader()
    bucket_name = "petbuddy-img"
    image_url = await uploader.upload_file(file, bucket_name)

    if not image_url:
        return JSONResponse(status_code=500, content={"ok": False, "message": "圖片上傳失敗"})

    conn = None
    cursor = None
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (image_url, user_id))
        conn.commit()

        return JSONResponse(status_code=200, content={"ok": True, "avatar_url": image_url})

    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
				
				
@router.put(
    "/api/member/profile",
    tags=["Member"],
    summary="更新使用者基本資料",
    description="更新使用者的姓名、手機、Email、地址、職業、居住狀況與飼養經驗。",
    responses={
        200: {"description": "成功"},
        401: {"description": "未登入"},
        500: {"description": "伺服器錯誤"},
    }
)
async def update_user_profile(request: Request, user: UpdateUser):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse(status_code=401, content={"ok": False, "message": "未授權"})

    user_id = user_data["userid"]
    conn = None
    cursor = None

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users SET
                name=%s,
                phone=%s,
                email=%s,
                address=%s,
                occupation=%s,
                residence_status=%s,
                pet_experience=%s
            WHERE id = %s
        """, (
            user.name,
            user.phone,
            user.email,
            user.address,
            user.profession,
            user.live,
            user.pet_experience,
            user_id
        ))

        conn.commit()
        return JSONResponse(status_code=200, content={"ok": True})

    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.put(
    "/api/member/password",
    tags=["Member"],
    summary="更新使用者密碼",
    description="使用舊密碼進行驗證後，更新為新密碼。",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "舊密碼錯誤"},
        401: {"description": "未登入"},
        404: {"description": "找不到使用者"},
        500: {"description": "伺服器錯誤"},
    }
)
async def update_password(request: Request, data: PasswordChange):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse(status_code=401, content={"ok": False, "message": "未授權"})

    user_id = user_data["userid"]
    conn = None
    cursor = None

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return JSONResponse(status_code=404, content={"ok": False, "message": "找不到使用者"})

        if not bcrypt.checkpw(data.old_password.encode(), user["password"].encode()):
            return JSONResponse(status_code=400, content={"ok": False, "message": "舊密碼錯誤"})

        new_hashed = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()

        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_hashed, user_id))
        conn.commit()

        return JSONResponse(status_code=200, content={"ok": True})

    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

