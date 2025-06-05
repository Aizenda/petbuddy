from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from ..model.db_connect import mysql_pool
from backend.model.JWT import JWT


router = APIRouter()


@router.get("/api/details/{id}")
async def dearails(request: Request,id: int):	
	conn = None
	cursor = None

	try:

		token = request.headers.get("Authorization", "").replace("Bearer ", "")
		user_data = JWT.decode_jwt(token)
		
		if not user_data:
				return JSONResponse({"ok":False,"message": "未登入"},status_code=401)
		
		conn = mysql_pool.get_connection()
		cursor = conn.cursor(dictionary = True)

		id = request.path_params.get("id")
		user_id = user_data.get("userid")

		select_query = """
		SELECT 
		s.*,
		COALESCE(JSON_ARRAYAGG(i.img_url), JSON_ARRAY()) AS images
		FROM send AS s
		LEFT JOIN imgurl AS i
		ON i.send_id = s.id
		WHERE s.id = %s
		"""

		cursor.execute(select_query,(id,))
		data = cursor.fetchone()

		json_compatible_data = jsonable_encoder(data)

		return JSONResponse({"ok":True,"data":json_compatible_data, "user_id":user_id},status_code=200)


	except Exception as e:
		return JSONResponse({"ok":False,"message":str(e)},status_code=500)
	
	finally:
		if cursor:
				cursor.close()
		if conn:
				conn.close()

@router.post("/api/want_to_adopt")
async def insert_like_table(request: Request):
	conn = None
	cursor =None

	try:

		token = request.headers.get("Authorization", "").replace("Bearer ", "")

		user_data = JWT.decode_jwt(token)
		if not user_data:
				return JSONResponse({"ok":False,"message": "未登入"},status_code=401)
		
		conn = mysql_pool.get_connection()
		cursor = conn.cursor(dictionary = True)

		want_to_adopt_user_id = user_data.get("userid")
		body = await request.json()
		post_id = body.get("post_id")

		select_ruery = """
		SELECT user_id, send_id FROM likes
		WHERE user_id = %s AND send_id =%s;
		"""

		cursor.execute(select_ruery,(want_to_adopt_user_id, post_id))
		check_for_adoption_duplication = cursor.fetchall()

		if len(check_for_adoption_duplication)>0:
			return JSONResponse({"ok":False , "message":"已通知送養人，請勿重複認養"},status_code= 409)


		insert_sql = """
		INSERT INTO likes (user_id, send_id)
		VALUES (%s, %s);
        """

		cursor.execute(insert_sql,(want_to_adopt_user_id, post_id))
		conn.commit()

		return JSONResponse({"ok":True},status_code=200)

	except Exception as e:
		print(str(e))
		return JSONResponse({"ok":False, "message":str(e)},status_code=500)

	finally:
		if cursor:
				cursor.close()
		if conn:
				conn.close()
		
