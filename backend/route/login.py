from fastapi import *
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..model.OTP import OTPService
from ..model.db_connect import mysql_pool
from ..model.JWT import JWT
from ..model.redis_sever import *
import bcrypt, asyncio

router = APIRouter()
otp_service = OTPService()
jwt_redis = Redis_JWT() 

class PhoneRequest(BaseModel):
    phone_number: str

class VerifyRequest(BaseModel):
    phone_number: str
    otp_code: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    otp: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/otp")
async def send_otp(request: PhoneRequest):
    try:
        response = otp_service.send_otp(request.phone_number)
        return JSONResponse({"ok":True, "message": "驗證碼已發送"}, status_code=201)
    except Exception as e:
        
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})
    
@router.post("/signup")
async def signup(request: SignupRequest):
    conn = None
    cursor = None
    try:
        if not otp_service.verify_otp(request.phone, request.otp):
            return JSONResponse({"ok": False, "message":"驗證碼錯誤或過期"}, status_code=400)

        loop = asyncio.get_running_loop()
        hashed_bytes = await loop.run_in_executor(
            None,
            bcrypt.hashpw,
            request.password.encode("utf-8"),
            bcrypt.gensalt()
        )
        hashed_password = hashed_bytes.decode("utf-8")

        conn = mysql_pool.get_connection()
        cursor = conn.cursor()

        check_query = "SELECT id FROM users WHERE email = %s OR phone = %s"
        cursor.execute(check_query, (request.email, request.phone))
        existing_user = cursor.fetchone()
        if existing_user:
            return JSONResponse({"ok":False, "message": "Email 或電話已被註冊"}, status_code=400)
        
        insert_query = """
            INSERT INTO users (name, email, password, phone, is_phone_verified)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            request.name,
            request.email,
            hashed_password,
            request.phone,
            1
        ))
        conn.commit()

        return JSONResponse({"ok":True, "message": "註冊成功"},status_code=201)

    except Exception as e:
        return JSONResponse({"ok":False,"message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.post("/login")
async def login(request: LoginRequest):
    conn = None
    cursor = None
    
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT id, name, email, password FROM users WHERE email = %s"
        cursor.execute(query, (request.email,))
        user = cursor.fetchone()

        if not user:
            return JSONResponse({"ok":False,"message": "帳號不存在"},status_code=404)

        if not bcrypt.checkpw(request.password.encode("utf-8"), user["password"].encode("utf-8")):
            return JSONResponse({"ok":False,"message": "密碼錯誤"},status_code=400,)
        
        userid = user["id"] 
        username = user["name"]
        
        jwt_encode = JWT.create_jwt(userid, username ) 
        jwt_redis.set_JWT(jwt_encode, userid)

        return JSONResponse({"ok":True, "message":"登入成功", "token" : jwt_encode}, status_code=200)

    except Exception as e:
        return JSONResponse({"ok":False,"message": str(e)}, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@router.get("/api/jwt")
async def user_check(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse({"ok": False, "message": "請登入"}, status_code=403)

    token = auth_header.split(" ")[1]
    
    if not token or token == "null":
        return JSONResponse({"ok": False, "message": "請登入"}, status_code=403)

    payload = JWT.decode_jwt(token)
    if not payload:
        return JSONResponse({"ok": False, "message": "Token 無效或已過期"}, status_code=401)

    user_id = payload.get("userid")

    stored_token = jwt_redis.get_JWT(user_id)
    if stored_token != token:
        return JSONResponse({"ok": False, "message": "Token 已失效或已登出"}, status_code=401)
    
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT id, name FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        if not user:
            return JSONResponse({"ok": False, "message": "帳號無效或被封鎖"}, status_code=403)

    finally:
        cursor.close()
        conn.close()

    return JSONResponse({"ok": True, "user_id": user_id, "username": payload.get("username")},status_code=200)
