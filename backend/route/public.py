from fastapi import *
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..model.db_connect import mysql_pool
from ..model.redis_sever import *
from typing import Optional
import hashlib, json, math, time
from ..model.redis_sever import RedisService

router = APIRouter()
r = RedisService().client

class PublicRequest(BaseModel):
	place: Optional[str] = None
	kind: Optional[str] = None
	sex: Optional[str] = None
	color: Optional[str] = None
	page: Optional[int] = 0

@router.get("/api/public")
async def get_public(request: PublicRequest = Depends()):
	filters = request.model_dump(exclude_none=True)

	# 產生快取 key
	cache_key = "public:" + hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
	lock_key = cache_key + ":lock"

	try:
		# 查快取
		cached = r.get(cache_key)
		if cached:
			return {"ok": True, **json.loads(cached)}

		# 嘗試取得鎖
		if r.set(lock_key, "1", nx=True, ex=10):
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
			data_values = where_values + [12, offset]
			cursor.execute(query, data_values)
			result = cursor.fetchall()

			cursor.close()
			conn.close()

			res_obj = {
				"data": result,
				"pages": pages,
				"current_page": page
			}

			# 寫入快取（10分鐘）
			r.set(cache_key, json.dumps(res_obj, default=str), ex=600)
			return {"ok": True, **res_obj}

		else:
			# 搶不到鎖就等快取出現
			for _ in range(20):
				time.sleep(0.1)
				cached = r.get(cache_key)
				if cached:
					return {"ok": True, **json.loads(cached)}
			return JSONResponse({"ok": False, "error": "系統忙碌，請稍後再試"}, status_code=503)

	except Exception as e:
		return JSONResponse({"ok": False, "error": str(e)}, status_code=500)