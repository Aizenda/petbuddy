import jwt, os
from .redis_sever import *
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
