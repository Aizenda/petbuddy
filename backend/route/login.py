from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..model.OTP import OTPService
from ..model.db_connect import mysql_pool
from ..model.auth_service import (
    hash_password,
    verify_password,
    generate_and_store_jwt,
    verify_jwt_token
)

router = APIRouter()
otp_service = OTPService()


# ========== Pydantic Models ==========
class PhoneRequest(BaseModel):
    phone_number: str
    
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: str
    otp: str

class LoginRequest(BaseModel):
    email: str
    password: str


# ========== Routes ==========

@router.post(
    "/api/auth/otp",
    tags=["Auth"],
    summary="發送 OTP 驗證碼",
    description="傳送簡訊驗證碼到指定手機號碼"
)
async def send_otp(request: PhoneRequest):
    try:
        otp_service.send_otp(request.phone_number)
        return JSONResponse({"ok": True, "message": "驗證碼已發送"}, status_code=201)
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})


@router.post(
    "/api/auth/signup",
    tags=["Auth"],
    summary="註冊新帳號",
    description="使用手機驗證碼進行註冊"
)
async def signup(request: SignupRequest):
    conn = None
    cursor = None

    try:
        if not otp_service.verify_otp(request.phone, request.otp):
            return JSONResponse({"ok": False, "message": "驗證碼錯誤或過期"}, status_code=400)

        hashed_password = await hash_password(request.password)

        conn = mysql_pool.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = %s OR phone = %s", (request.email, request.phone))
        if cursor.fetchone():
            return JSONResponse({"ok": False, "message": "Email 或電話已註冊"}, status_code=400)

        cursor.execute("""
            INSERT INTO users (name, email, password, phone, is_phone_verified)
            VALUES (%s, %s, %s, %s, 1)
        """, (request.name, request.email, hashed_password, request.phone))
        conn.commit()

        return JSONResponse({"ok": True, "message": "註冊成功"}, status_code=201)

    except Exception as e:
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@router.post(
    "/api/auth/login",
    tags=["Auth"],
    summary="使用者登入",
    description="登入成功會回傳 JWT token"
)
async def login(request: LoginRequest):
    conn = None
    cursor = None
    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, name, email, password FROM users WHERE email = %s", (request.email,))
        user = cursor.fetchone()

        if not user or not verify_password(request.password, user["password"]):
            return JSONResponse({"ok": False, "message": "帳號或密碼錯誤"}, status_code=400)

        token = generate_and_store_jwt(user["id"], user["name"])

        return JSONResponse({"ok": True, "message": "登入成功", "token": token}, status_code=200)

    except Exception as e:
        return JSONResponse({"ok": False, "message": str(e)}, status_code=500)
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


@router.get(
    "/api/auth/check",
    tags=["Auth"],
    summary="檢查使用者登入狀態",
    description="根據 JWT 判斷是否登入並回傳使用者資訊"
)
async def check_login(request: Request):
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    payload = verify_jwt_token(token)
    if not payload:
        return JSONResponse({"ok": False, "message": "Token 無效或已過期"}, status_code=401)

    user_id = payload.get("userid")

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, name FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return JSONResponse({"ok": False, "message": "帳號不存在"}, status_code=403)

        return JSONResponse({
            "ok": True,
            "user_id": user["id"],
            "username": user["name"]
        }, status_code=200)

    finally:
        if cursor: cursor.close()
        if conn: conn.close()
