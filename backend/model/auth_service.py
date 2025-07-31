import bcrypt
import asyncio
from ..model.JWT import JWT
from ..model.redis_sever import Redis_JWT

jwt_redis = Redis_JWT()

async def hash_password(password: str) -> str:
    loop = asyncio.get_running_loop()
    hashed_bytes = await loop.run_in_executor(
        None,
        bcrypt.hashpw,
        password.encode("utf-8"),
        bcrypt.gensalt()
    )
    return hashed_bytes.decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def generate_and_store_jwt(user_id: int, username: str) -> str:
    token = JWT.create_jwt(user_id, username)
    jwt_redis.set_JWT(token, user_id)
    return token

def verify_jwt_token(token: str):
    if not token or token == "null":
        return None
    payload = JWT.decode_jwt(token)
    if not payload:
        return None
    user_id = payload.get("userid")
    if jwt_redis.get_JWT(user_id) != token:
        return None
    return payload
