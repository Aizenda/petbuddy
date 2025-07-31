from fastapi import *
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..model.db_connect import mysql_pool
from ..model.redis_sever import redis_cache  # 使用統一實例
from typing import Optional
import math, time

router = APIRouter()

class PublicRequest(BaseModel):
	place: Optional[str] = None
	kind: Optional[str] = None
	sex: Optional[str] = None
	color: Optional[str] = None
	page: Optional[int] = 0

@router.get(
    "/api/adoptions/public",
    tags=["Adoption"],
    summary="取得公開送養資料",
    description="查詢公開的送養資料，支援條件過濾（地點、種類、性別、顏色）與分頁，結果會快取 10 分鐘。",
    responses={
        200: {
            "description": "成功取得資料",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "data": [
                            {
                                "id": 1,
                                "animal_kind": "狗",
                                "animal_colour": "黑白",
                                "animal_place": "台北市"
                            }
                        ],
                        "pages": 3,
                        "current_page": 0
                    }
                }
            }
        },
        503: {"description": "系統忙碌"},
        500: {"description": "伺服器錯誤"},
    }
)
async def get_public_adoptions(request: PublicRequest = Depends()):
    filters = request.model_dump(exclude_none=True)
    
    # ✅ 使用統一的快取鍵生成方法
    cache_key = redis_cache.get_cache_hash_key("public", filters)
    lock_key = cache_key + ":lock"

    try:
        cached = redis_cache.get_cache(cache_key)
        if cached:
            return {"ok": True, **cached}

        if redis_cache.acquire_lock(lock_key, 10):
            conn = mysql_pool.get_connection()
            cursor = conn.cursor(dictionary=True)

            base_query = "SELECT * FROM public"
            count_query = "SELECT COUNT(*) as total FROM public"
            conditions = []
            where_values = []

            if "place" in filters:
                conditions.append("animal_place = %s")
                where_values.append(filters["place"])
            if "kind" in filters:
                conditions.append("animal_kind = %s")
                where_values.append(filters["kind"])
            if "sex" in filters:
                conditions.append("animal_sex = %s")
                where_values.append(filters["sex"])
            if "color" in filters:
                conditions.append("animal_colour = %s")
                where_values.append(filters["color"])

            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

            cursor.execute(count_query + where_clause, where_values)
            count = cursor.fetchone()["total"]
            pages = math.ceil(count / 12)
            page = filters.get("page", 0)
            offset = page * 12

            query = base_query + where_clause + " LIMIT %s OFFSET %s"
            cursor.execute(query, where_values + [12, offset])
            result = cursor.fetchall()

            cursor.close()
            conn.close()

            res_obj = {
                "data": result,
                "pages": pages,
                "current_page": page
            }

            # ✅ 設定快取 10 分鐘
            redis_cache.set_cache(cache_key, res_obj, ttl=600)
            redis_cache.release_lock(lock_key)
            
            return {"ok": True, **res_obj}

        else:
            # 等待其他請求完成
            for _ in range(20):
                time.sleep(0.1)
                cached = redis_cache.get_cache(cache_key)
                if cached:
                    return {"ok": True, **cached}

            return JSONResponse({"ok": False, "error": "系統忙碌，請稍後再試"}, status_code=503)

    except Exception as e:
        redis_cache.release_lock(lock_key)
        print(str(e))
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)