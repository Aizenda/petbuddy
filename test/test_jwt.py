# tests/test_jwt.py
import pytest
from datetime import datetime, timedelta
from backend.model.JWT import JWT

def test_create_and_decode_jwt():
    userid = "123"
    username = "testuser"
    token = JWT.create_jwt(userid, username)

    decoded = JWT.decode_jwt(token)
    assert decoded is not None
    assert decoded["userid"] == userid
    assert decoded["username"] == username
    assert datetime.fromtimestamp(decoded["exp"]) > datetime.now()

def test_expired_jwt(monkeypatch):
    userid = "456"
    username = "expireduser"

    # 產生過期的 token
    token = JWT.create_jwt(userid, username, expire_minutes=-1)
    decoded = JWT.decode_jwt(token)

    assert decoded is None

def test_invalid_token():
    fake_token = "this.is.not.a.valid.token"
    decoded = JWT.decode_jwt(fake_token)

    assert decoded is None
