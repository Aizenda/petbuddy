import jwt, os
from .redis_sever import *
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fastapi import Request
from fastapi.responses import JSONResponse

load_dotenv()

key = os.getenv("JWT_KEY")
ALGORITHM = "HS256"
EXPIRE_MINUTES = 60

class JWT:

	@staticmethod
	def create_jwt(userid: str, username: str, expire_minutes: int = EXPIRE_MINUTES):
		payload = {
			"userid": userid,
			"username": username,
			"exp":datetime.now() + timedelta(minutes=EXPIRE_MINUTES)
		}

		token = jwt.encode(payload, key, ALGORITHM)
		
		return token 

	@staticmethod
	def decode_jwt(token: str):
		try:
				payload = jwt.decode(token, key, algorithms=[ALGORITHM])
				return payload
		except jwt.ExpiredSignatureError:
				return None
		except jwt.InvalidTokenError:
				return None
		
	@staticmethod
	def get_current_user(request: Request):
			"""
			FastAPI 依賴注入用：自動從 Header 中解析 Bearer Token 並驗證
			"""
			token = request.headers.get("Authorization", "").replace("Bearer ", "")
			user_data = JWT.decode_jwt(token)

			if not user_data:
					raise JSONResponse(status_code=401, detail="未授權")

			return user_data
