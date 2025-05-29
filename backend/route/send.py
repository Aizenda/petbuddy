from fastapi import APIRouter, File, UploadFile, Form, Depends, Request
from fastapi.responses import JSONResponse
from backend.model.upload_function import Uploader, UploadText
from backend.model.JWT import JWT
from pydantic import BaseModel

router = APIRouter()

@router.post("/api/send")
async def send_adoption(
    request: Request,
    pet_name: str = Form(...),
    pet_breed: str = Form(...),
    pet_kind: str = Form(...),
    pet_sex: str = Form(...),
    pet_bodytype: str = Form(...),
    pet_colour: str = Form(...),
    pet_age: str = Form(...),
    pet_place: str = Form(...),
    pet_describe: str = Form(...),
    pet_ligation_status: str = Form(...),
    images: list[UploadFile] = File(...),
):
    try:
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        print("收到的 token:", token)
        user_data = JWT.decode_jwt(token)
        print("收到的 token:", user_data)
        user_id = user_data.get("userid")

        if not user_id:
            return JSONResponse(status_code=401, content={"error": "未授權"})


        uploader = Uploader()
        image_urls = []

        for image in images[:4]:
            url = await uploader.upload_file(image, bucket="petbuddy-img")
            if url:
                image_urls.append(url)

        if not image_urls:
            return JSONResponse(status_code=400, content={"error": "圖片上傳失敗"})

        upload_text = UploadText()
        for url in image_urls:
            upload_text.insert_text(
                {
                    "user_id": user_id,
                    "pet_name": pet_name,
                    "pet_breed": pet_breed,
                    "pet_kind": pet_kind,
                    "pet_sex": pet_sex,
                    "pet_bodytype": pet_bodytype,
                    "pet_colour": pet_colour,
					"pet_age":pet_age,
                    "pet_place": pet_place,
                    "pet_describe": pet_describe,
                    "pet_ligation_status": pet_ligation_status,
                },
                file_url=url
            )
        upload_text.close()

        return {"ok": True, "message": "送養資訊已上傳"}

    except Exception as e:
        print("送養失敗:", e)
        return JSONResponse(status_code=500, content={"error": "伺服器錯誤"})