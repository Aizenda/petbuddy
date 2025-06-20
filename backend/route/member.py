from fastapi import APIRouter,Request,Query,File,UploadFile,Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ..model.db_connect import mysql_pool
from backend.model.JWT import JWT
from backend.model.upload_function import Uploader
from pydantic import BaseModel
import bcrypt
from datetime import datetime


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
	

@router.get("/api/advertise_for_adoption")
async def get_advertise_for_adoption(request:Request):
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
		select_want_to_adopt_quary = """
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

		cursor.execute(select_want_to_adopt_quary,(user_id,))
		data = cursor.fetchall()
		return JSONResponse({"ok":True, "data":data}, status_code=200)
	
	except Exception as e:
		print(e)
		return JSONResponse({"ok":False,"message":str(e)}, status_code=500)
	
	finally:
		if cursor:
				cursor.close()
		if conn:
				conn.close()
		
@router.get("/api/want_to_adopt")
async def get_want_to_adopt(request:Request):
	conn = None
	cursor = None

	try:
		conn  = mysql_pool.get_connection()
		cursor = conn.cursor(dictionary = True)

		token = request.headers.get("Authorization", "").replace("Bearer ", "")
		user_data = JWT.decode_jwt(token)

		if not user_data:
			return JSONResponse({"ok":False,"message": "未登入"}, status_code=401)

		user_id = user_data.get("userid")
		select_query = """
		SELECT
			s.id AS send_id,
			s.pet_name,
			s.pet_kind,
			s.pet_breed,
			GROUP_CONCAT(i.img_url) AS images,
			su.name             AS sender_name,
			l.user_id          AS adopter_id
		FROM likes AS l
			JOIN send AS s
			ON l.send_id = s.id
			JOIN users AS su
			ON s.user_id = su.id         
			LEFT JOIN imgurl AS i
			ON i.send_id = s.id
		WHERE
			l.user_id = %s  
		GROUP BY
			s.id,
			su.id,
			l.liked_at
		ORDER BY
			l.liked_at DESC;
		"""

		cursor.execute(select_query,(user_id,))
		data = cursor.fetchall()
		
		return JSONResponse({"ok":True, "data":data}, status_code=200)
	
	except Exception as e:
		print(e)
		return JSONResponse({"ok":False,"message":str(e)}, status_code=500)

	finally:
		if cursor:
			cursor.close()
		if conn:
			conn.close()

@router.delete("/api/cancel_adoption")
async def cancel_adoption(request: Request,post_id: int = Query(...),adopter_id: int = Query(...)):
    conn = None
    cursor = None
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor()

        # 找 form_id
        cursor.execute("SELECT id FROM forms WHERE post_id = %s", (post_id,))
        form_row = cursor.fetchone()
        if form_row:
            form_id = form_row[0]
            # 刪除答案
            cursor.execute(
                "DELETE FROM form_submissions WHERE form_id = %s AND submitter_user_id = %s",
                (form_id, adopter_id)
            )

        # 刪除 like
        cursor.execute(
            "DELETE FROM likes WHERE user_id = %s AND send_id = %s",
            (adopter_id, post_id)
        )

        conn.commit()
        return JSONResponse({"ok": True})
    except Exception as e:
        print("刪除失敗:", e)
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@router.get("/api/get_all_data")
async def get_all_data(request:Request):
	conn = None
	cursor = None

	try:

		conn = mysql_pool.get_connection()
		cursor = conn.cursor(dictionary = True)
		token = request.headers.get("Authorization", "").replace("Bearer ", "")
		user_data = JWT.decode_jwt(token)

		if not user_data:
			return JSONResponse({"ok":False,"message": "未登入"}, status_code=401)

		user_id = user_data.get("userid")
		select_all_send = """
		SELECT s.id AS send_id , s.pet_name,JSON_ARRAYAGG(img.img_url) AS images
		FROM send AS s 
		LEFT JOIN imgurl AS img ON img.send_id = s.id
		WHERE s.user_id = %s
		GROUP BY s.id
		ORDER BY s.id ASC;
		"""

		cursor.execute(select_all_send,(user_id,))
		data = cursor.fetchall()

		return JSONResponse({"ok":True, "data":data},status_code=200)
	except Exception as e:
		print(e)
		return JSONResponse({"ok": False, "message": str(e)}, status_code=500)
	
	finally:
		if cursor:
			cursor.close()
		if conn:
			conn.close()


@router.get("/api/get_histor")
async def get_all_data(request:Request):
	conn = None
	cursor = None

	try:

		conn = mysql_pool.get_connection()
		cursor = conn.cursor(dictionary = True)
		token = request.headers.get("Authorization", "").replace("Bearer ", "")
		user_data = JWT.decode_jwt(token)

		if not user_data:
			return JSONResponse({"ok":False,"message": "未登入"}, status_code=401)

		user_id = user_data.get("userid")
		select_all_send = """
		SELECT s.original_send_id AS send_id , s.pet_name,JSON_ARRAYAGG(img.img_url) AS images,s.adopted_at
		FROM send_history AS s 
		LEFT JOIN imgurl_history AS img ON img.send_id = s.id
		WHERE s.user_id = %s
		GROUP BY s.id
		ORDER BY s.id ASC;
		"""

		cursor.execute(select_all_send,(user_id,))
		data = cursor.fetchall()
		for row in data:
			if isinstance(row.get("adopted_at"), datetime):
				row["adopted_at"] = row["adopted_at"].strftime("%Y-%m-%d")

		return JSONResponse({"ok":True, "data":data},status_code=200)
	except Exception as e:
		print(e)
		return JSONResponse({"ok": False, "message": str(e)}, status_code=500)
	
	finally:
		if cursor:
			cursor.close()
		if conn:
			conn.close()

@router.get("/api/member/get_user_date")
async def get_user_data(request: Request):
	conn = mysql_pool.get_connection()
	cursor = conn.cursor(dictionary=True)
	try:
		token = request.headers.get("Authorization", "").replace("Bearer ", "")
		user_data = JWT.decode_jwt(token)
		if not user_data:
			return JSONResponse(status_code=401, content={"error": "未授權"})
		
		user_id = user_data["userid"]
		cursor.execute("SELECT name, phone, email, address, occupation, pet_experience, avatar_url FROM users WHERE id = %s", (user_id,))
		user = cursor.fetchone()
		if not user:
			return JSONResponse(status_code=404, content={"ok": False, "message": "找不到使用者"})
		return {"ok": True, "data": user}
	finally:
		cursor.close()
		conn.close()


@router.get("/api/member/get_user_avatar")
async def get_avatar(request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse(status_code=401, content={"error": "未授權"})

    user_id = int(user_data["userid"])
    conn = mysql_pool.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT avatar_url FROM users WHERE id = %s", (user_id,))
        avatar = cursor.fetchone()
        if not avatar:
            return JSONResponse(status_code=404, content={"ok": False, "message": "找不到頭像"})
        return {"ok": True, "avatar_url": avatar[0]}
    finally:
        cursor.close()
        conn.close()
				

@router.put("/api/member/updata_avatar")
async def update_avatar(request: Request, file: UploadFile = File(...)):
		
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse(status_code=401, content={"error": "未授權"})

    user_id = int(user_data["userid"])

    uploader = Uploader()
    bucket_name = "petbuddy-img"  

    # 上傳到 S3 並取得圖片網址
    image_url = await uploader.upload_file(file, bucket_name)
    if not image_url:
        return JSONResponse(status_code=500, content={"ok": False, "message": "圖片上傳失敗"})

    # 將圖片網址存入資料庫
    conn = mysql_pool.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (image_url, user_id))
        conn.commit()
        return {"ok": True, "avatar_url": image_url}
    finally:
        cursor.close()
        conn.close()
				
				
@router.put("/api/member/update_user")
async def update_user(request: Request, user: UpdateUser):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse(status_code=401, content={"error": "未授權"})

    user_id = int(user_data["userid"])
    conn = mysql_pool.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE users SET name=%s, phone=%s, email=%s, address=%s, 
            occupation=%s, residence_status=%s, pet_experience=%s 
            WHERE id=%s
        """, (
            user.name, user.phone, user.email, user.address,
            user.profession, user.live, user.pet_experience, user_id
        ))
        conn.commit()
        return {"ok": True}
    finally:
        cursor.close()
        conn.close()


@router.put("/api/member/update_password")
async def update_password(request: Request, data: PasswordChange):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user_data = JWT.decode_jwt(token)
    if not user_data:
        return JSONResponse(status_code=401, content={"error": "未授權"})

    user_id = int(user_data["userid"])
    conn = mysql_pool.get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return JSONResponse(status_code=404, content={"ok": False, "message": "找不到使用者"})

        if not bcrypt.checkpw(data.old_password.encode(), user["password"].encode()):
            return JSONResponse(status_code=400, content={"ok": False, "message": "舊密碼錯誤"})

        new_hashed = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()

        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (new_hashed, user_id))
        conn.commit()
        return {"ok": True}
    finally:
        cursor.close()
        conn.close()

