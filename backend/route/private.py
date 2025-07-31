from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import math
from ..model.db_connect import mysql_pool
from ..model.redis_sever import redis_cache  # 使用統一實例
import json

router = APIRouter()

class PrivateRequest(BaseModel):
    place: Optional[str] = None
    kind: Optional[str] = None
    sex: Optional[str] = None
    color: Optional[str] = None
    page: int = 0

@router.get(
    "/api/member/adoptions/private",
    tags=["Adoption"],
    summary="取得私人送養資料",
    description="根據條件查詢私人送養資料，支援地點、種類、性別、顏色與分頁，結果會快取 5 分鐘",
    response_description="成功查詢",
    responses={
        200: {
            "description": "成功",
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "data": [
                            {
                                "id": 1,
                                "user_id": 12,
                                "pet_name": "小花",
                                "pet_kind": "狗",
                                "pet_colour": "白",
                                "images": ["https://your-s3/img1.jpg"]
                            }
                        ],
                        "current_page": 0,
                        "total_pages": 3,
                        "total_count": 28
                    }
                }
            }
        },
        500: {"description": "伺服器錯誤"}
    }
)
async def get_private_adoptions(request: PrivateRequest = Depends()):
    conn = None
    cursor = None

    # ✅ 使用統一的快取鍵生成方法
    filters = request.model_dump(exclude_none=True)
    cache_key = redis_cache.get_cache_hash_key("private_adoptions", filters)
    
    cached = redis_cache.get_cache(cache_key)
    if cached:
        return JSONResponse({"ok": True, **cached}, status_code=200)

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        base_query = """
        FROM send AS s
        JOIN imgurl ON imgurl.send_id = s.id
        """
        where_list = []
        params_for_where = []

        if request.place is not None:
            where_list.append("s.pet_place = %s")
            params_for_where.append(request.place)
        if request.kind is not None:
            where_list.append("s.pet_kind = %s")
            params_for_where.append(request.kind)
        if request.sex is not None:
            where_list.append("s.pet_sex = %s")
            params_for_where.append(request.sex)
        if request.color is not None:
            where_list.append("s.pet_colour = %s")
            params_for_where.append(request.color)

        where_clause = ""
        if where_list:
            where_clause = " WHERE " + " AND ".join(where_list)

        count_sql = f"SELECT COUNT(DISTINCT s.id) AS total_count {base_query}{where_clause}"
        cursor.execute(count_sql, params_for_where)
        total_count = cursor.fetchone()["total_count"]

        per_page = 12
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

        offset_value = request.page * per_page
        params_for_data = params_for_where.copy()
        params_for_data.append(offset_value)

        select_sql = f"""
        SELECT s.id,
               s.user_id,
               s.pet_name,
               s.pet_breed,
               s.pet_kind,
               s.pet_sex,
               s.pet_colour,
               s.pet_place,
               JSON_ARRAYAGG(imgurl.img_url) AS images
        {base_query}
        {where_clause}
        GROUP BY
        s.id,
        s.user_id,
        s.pet_name,
        s.pet_breed,
        s.pet_kind,
        s.pet_sex,
        s.pet_colour,
        s.pet_place
        ORDER BY
        s.id DESC
        LIMIT 12 OFFSET %s;
        """
        cursor.execute(select_sql, params_for_data)
        data = cursor.fetchall()

        result = {
            "data": data,
            "current_page": request.page,
            "total_pages": total_pages,
            "total_count": total_count
        }

        # ✅ 設定快取 5 分鐘
        redis_cache.set_cache(cache_key, result, 300)

        return JSONResponse({"ok": True, **result}, status_code=200)
        
    except Exception as e:
        print(e)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()