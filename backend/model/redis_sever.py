import redis
import os

class RedisService:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True
        )

class Redis_OTP(RedisService):
    def set_otp(self, phone: str, otp: str, ttl: int = 120):
        self.client.setex(f"otp:{phone}", ttl, otp)

    def get_otp(self, phone: str) -> str | None:
        return self.client.get(f"otp:{phone}")

    def delete_otp(self, phone: str):
        self.client.delete(f"otp:{phone}")

class Redis_JWT(RedisService):
    def set_JWT(self, JWT: str, user_id:int, ttl: int = 3600,):
        self.client.setex(f"JWT:{user_id}", ttl, JWT)

    def get_JWT(self, user_id: int) -> str | None:
        return self.client.get(f"JWT:{user_id}")
    
    def delete_JWT(self, user_id: int):
        self.client.delete(f"JWT:{user_id}")