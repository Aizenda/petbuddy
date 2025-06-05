from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import math
from ..model.db_connect import mysql_pool

router = APIRouter()

class PrivateRequest(BaseModel):
    place: Optional[str] = None
    kind: Optional[str] = None
    sex: Optional[str] = None
    color: Optional[str] = None
    page: int = 0

@router.get("/api/private")
async def private_data(request: PrivateRequest = Depends()):
    conn = None
    cursor = None
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

        return JSONResponse({
            "data": data,
            "current_page": request.page,
            "total_pages": total_pages,
            "total_count": total_count
        },status_code=200)
    except Exception as e:
        print(e)
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
