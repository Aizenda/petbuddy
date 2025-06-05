from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ..model.db_connect import mysql_pool
from backend.model.JWT import JWT

router = APIRouter()

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
	

@router.get("/api/want_to_adopt")
async def get_want_to_adopt_data(request:Request):
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
				s.*,
				u.name AS user_name, 
				u.email AS user_email,
				l.liked_at AS time
		FROM send AS s
		LEFT JOIN likes AS l 
				ON s.id = l.send_id
		LEFT JOIN users AS u 
				ON l.user_id = u.id

		WHERE s.user_id = %s
		ORDER BY s.created_at DESC, l.liked_at DESC;
		"""

		cursor.execute(select_want_to_adopt_quary,(user_id,))
		data = cursor.fetchall()

		return JSONResponse({"ok":True, "data":data}, status_code=200)
	
	except Exception as e:
		return JSONResponse({"ok":False,"message":str(e)},status_code=500)
	
	finally:
		if cursor:
				cursor.close()
		if conn:
				conn.close()
		