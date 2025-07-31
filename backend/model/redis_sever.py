# redis_sever.py - 修正版本
import redis
import os
import json
import hashlib
import fnmatch

class RedisService:
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._client = redis.Redis(
                host=os.getenv("REDIS_HOST"),
                port=int(os.getenv("REDIS_PORT")),
                decode_responses=True
            )
    
    @property
    def client(self):
        return self._client

class Redis_OTP(RedisService):
    def set_otp(self, phone: str, otp: str, ttl: int = 120):
        self.client.setex(f"otp:{phone}", ttl, otp)

    def get_otp(self, phone: str) -> str | None:
        return self.client.get(f"otp:{phone}")

    def delete_otp(self, phone: str):
        self.client.delete(f"otp:{phone}")

class Redis_JWT(RedisService):
    def set_JWT(self, JWT: str, user_id: int, ttl: int = 3600):
        self.client.setex(f"JWT:{user_id}", ttl, JWT)

    def get_JWT(self, user_id: int) -> str | None:
        return self.client.get(f"JWT:{user_id}")
    
    def delete_JWT(self, user_id: int):
        self.client.delete(f"JWT:{user_id}")

class RedisCache(RedisService):
    def get_cache(self, key: str) -> dict | list | None:
        try:
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Redis get_cache error for key {key}: {e}")
        return None

    def set_cache(self, key: str, value: dict | list, ttl: int = 600):
        try:
            serialized = json.dumps(value, ensure_ascii=False, default=str)
            self.client.setex(key, ttl, serialized)
            print(f"✅ 設定快取: {key} (TTL: {ttl}s)")
        except Exception as e:
            print(f"Redis set_cache error for key {key}: {e}")

    def delete_cache(self, key: str):
        try:
            result = self.client.delete(key)
            if result:
                print(f"🗑️ 刪除快取: {key}")
            return result
        except Exception as e:
            print(f"Redis delete_cache error for key {key}: {e}")
            return 0

    def delete_pattern(self, pattern: str):
        """刪除符合模式的所有快取鍵"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                deleted = self.client.delete(*keys)
                print(f"🗑️ 批量刪除快取: {pattern} ({deleted} 個)")
                return deleted
            return 0
        except Exception as e:
            print(f"Redis delete_pattern error for pattern {pattern}: {e}")
            return 0

    def acquire_lock(self, key: str, expire: int = 10) -> bool:
        return self.client.set(key, "1", nx=True, ex=expire)

    def release_lock(self, key: str):
        self.client.delete(key)

    def invalidate_adoption_caches(self, user_id: int = None, post_id: int = None, 
                                 place: str = None, kind: str = None, 
                                 sex: str = None, color: str = None):
        """統一的送養相關快取清除方法"""
        patterns_to_delete = []
        
        # 1. 清除用戶相關快取
        if user_id:
            patterns_to_delete.extend([
                f"user:{user_id}:*",
            ])
        
        # 2. 清除特定貼文快取
        if post_id:
            patterns_to_delete.extend([
                f"adoption_detail:{post_id}",
                f"form:{post_id}",
                f"submission:{post_id}:*",
                f"answers:{post_id}:*",
                f"like:*:{post_id}",
            ])
        
        # 3. 清除列表快取 (private/public)
        patterns_to_delete.extend([
            "private:*",
            "public:*",
            "private_adoptions:*",
        ])
        
        # 執行刪除
        total_deleted = 0
        for pattern in patterns_to_delete:
            total_deleted += self.delete_pattern(pattern)
        
        print(f"🧹 總共清除 {total_deleted} 個快取項目")
        return total_deleted

    def get_cache_hash_key(self, prefix: str, filters: dict) -> str:
        """生成一致的快取鍵"""
        clean_filters = {k: v for k, v in filters.items() if v is not None}
        key_base = json.dumps(clean_filters, sort_keys=True, ensure_ascii=False)
        hash_key = hashlib.md5(key_base.encode()).hexdigest()
        return f"{prefix}:{hash_key}"

# 單例實例
redis_cache = RedisCache()