from fastapi import *
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..model.db_connect import mysql_pool
from ..model.redis_sever import *
from typing import Optional
import math

router = APIRouter()

class PublicRequest(BaseModel):
	place: Optional[str] = None
	kind: Optional[str] = None
	sex: Optional[str] = None
	color: Optional[str] = None
	page: Optional[int] = 0

@router.get("/api/public")
async def get_public(request: PublicRequest = Depends()):
	filters = request.model_dump(exclude_none=True)
	conn = None
	cursor = None
	try:
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

		where_clause = ""
		if conditions:
			where_clause = " WHERE " + " AND ".join(conditions)

		# 取得總筆數
		cursor.execute(count_query + where_clause, where_values)
		count = cursor.fetchone()["total"]
		pages = math.ceil(count / 12)

		# 計算 offset
		page = filters.get("page", 1)
		offset = page * 12
		# 查分頁資料
		query = base_query + where_clause + " LIMIT %s OFFSET %s"
		data_values = where_values + [12, offset]
		cursor.execute(query, data_values)
		result = cursor.fetchall()

		return JSONResponse({
			"ok": True,
			"data": result,
			"pages": pages,
			"current_page": page
		},status_code= 200)

	except Exception as e:
		return JSONResponse({
			"ok": False,
			"error": str(e)
		},status_code=500)

	finally:
		if cursor:
			cursor.close()
		if conn:
			conn.close()

