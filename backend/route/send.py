from fastapi import APIRouter, File, UploadFile, Form, Depends, Request
from fastapi.responses import JSONResponse
from backend.model.upload_function import Uploader, UploadText
from backend.model.JWT import JWT
from pydantic import BaseModel
from ..model.redis_sever import RedisService
import hashlib , json, time

router = APIRouter()
r = RedisService().client

@router.post("/api/send")
async def send_adoption(
    request: Request,
    pet_name: str = Form(...),
    pet_breed: str = Form(...),
    pet_kind: str = Form(...),
    pet_sex: str = Form(...),
    pet_bodytype: str = Form(...),
    pet_colour: str = Form(...),
    pet_place: str = Form(...),
    pet_describe: str = Form(...),
    pet_ligation_status: str = Form(...),
    pet_age: str = Form(...),
    images: list[UploadFile] = File(...)
):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_data = JWT.decode_jwt(token)
        user_id = user_data.get("userid")
        if not user_data:
            return JSONResponse(status_code=401, content={"error": "未授權"})

        uploader = Uploader()
        image_urls = []
        for image in images[:4]:
            if image and image.filename and image.size > 0:
                url = await uploader.upload_file(image, bucket="petbuddy-img")
                if url:
                    image_urls.append(url)

        if not image_urls:
            return JSONResponse(status_code=400, content={"error": "圖片上傳失敗"})

        upload_text = UploadText()
        send_id = upload_text.insert_send({
            "user_id": user_id,
            "pet_name": pet_name,
            "pet_breed": pet_breed,
            "pet_kind": pet_kind,
            "pet_sex": pet_sex,
            "pet_bodytype": pet_bodytype,
            "pet_colour": pet_colour,
            "pet_place": pet_place,
            "pet_describe": pet_describe,
            "pet_ligation_status": pet_ligation_status,
            "pet_age": pet_age
        })

        if not send_id:
            return JSONResponse(status_code=500, content={"error": "送養資料建立失敗"})

        # 4. 寫入圖片資料
        for url in image_urls:
            upload_text.insert_img(send_id, url)

        # ✅ 刪除相關 Redis 快取
        filters_to_invalidate = [
            {},  # 全部快取
            {"place": pet_place},
            {"place": pet_place, "kind": pet_kind},
            {"place": pet_place, "kind": pet_kind, "sex": pet_sex},
            {"place": pet_place, "kind": pet_kind, "sex": pet_sex, "color": pet_colour},
        ]

        for filters in filters_to_invalidate:
            key = "private:" + hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
            r.delete(key)

        upload_text.close()
        return {"ok": True, "message": "送養資訊已成功刊登！","post_id":send_id}

    except Exception as e:
        print("送養失敗:", e)
        return JSONResponse(status_code=500, content={"error": "伺服器錯誤"})