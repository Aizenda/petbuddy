import redis
import os

class RedisService:
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT")),
            password=os.getenv("REDIS_PASSWORD"),
            ssl=True,
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

class RedisCache(RedisService):
    def get_cache(self, key: str) -> dict | list | None:
        cached = self.client.get(key)
        if cached:
            try:
                import json
                return json.loads(cached)
            except Exception as e:
                print(f"JSON decode failed: {e}")
                return None
        return None

    def set_cache(self, key: str, value: dict | list, ttl: int = 600):
        try:
            import json
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            print(f"JSON encode failed: {e}")

    def acquire_lock(self, key: str, expire: int = 10) -> bool:
        return self.client.set(key, "1", nx=True, ex=expire)

    def release_lock(self, key: str):
        self.client.delete(key)