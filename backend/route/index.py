from fastapi import *
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ..model.db_connect import mysql_pool

router = APIRouter()

@router.get("/api/count")
async def count(request:Request):
	conn=None
	cursor=None

	try:
		conn = mysql_pool.get_connection()
		cursor = conn.cursor(dictionary=True)

		query="""
		SELECT animal_kind, COUNT(*) AS count FROM public GROUP BY animal_kind
		"""
		cursor.execute(query)
		data = cursor.fetchall()
		kind_counts = {row["animal_kind"]: row["count"] for row in data}

		dog_count = kind_counts.get("狗")
		cat_count = kind_counts.get("貓")
		other_count = kind_counts.get("其他")

		return JSONResponse({"ok":True,"dog":dog_count, "cat": cat_count, "other": other_count},status_code=200)

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
