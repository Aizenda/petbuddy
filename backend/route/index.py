from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ..model.db_connect import mysql_pool

router = APIRouter()


def get_animal_kind_count(cursor):
    cursor.execute("""
        SELECT animal_kind, COUNT(*) AS count 
        FROM public 
        GROUP BY animal_kind
    """)
    data = cursor.fetchall()
    return {row["animal_kind"]: row["count"] for row in data}


@router.get(
    "/api/statistics/animal-count",
    tags=["Statistics"],
    summary="取得送養動物種類統計",
    description="回傳目前送養資料中狗、貓、其他動物的統計數量"
)
async def get_animal_statistics(request: Request):
    conn = None
    cursor = None

    try:
        conn = mysql_pool.get_connection()
        cursor = conn.cursor(dictionary=True)

        kind_counts = get_animal_kind_count(cursor)

        return JSONResponse({
            "ok": True,
            "dog": kind_counts.get("狗", 0),
            "cat": kind_counts.get("貓", 0),
            "other": kind_counts.get("其他", 0)
        }, status_code=200)

    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": str(e)
        }, status_code=500)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
