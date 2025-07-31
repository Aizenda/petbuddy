from fastapi import APIRouter, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.model.upload_function import Uploader, UploadText
from backend.model.JWT import JWT
from ..model.redis_sever import redis_cache

router = APIRouter(
    prefix="/api",
    tags=["Pet Adoption"],
    responses={
        401: {"description": "未授權"},
        500: {"description": "伺服器錯誤"}
    }
)

# Response Models
class SuccessResponse(BaseModel):
    ok: bool = Field(True, description="操作是否成功")
    message: str = Field(..., description="回應訊息")
    post_id: int = Field(..., description="新建立的送養貼文ID")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="錯誤訊息")

@router.post(
    "/send",
    summary="刊登寵物送養資訊",
    description="建立新的寵物送養貼文，包含寵物資訊和照片上傳",
    response_model=SuccessResponse,
    responses={
        200: {
            "description": "成功刊登送養資訊",
            "model": SuccessResponse,
            "content": {
                "application/json": {
                    "example": {
                        "ok": True,
                        "message": "送養資訊已成功刊登！",
                        "post_id": 123
                    }
                }
            }
        },
        400: {
            "description": "請求參數錯誤或圖片上傳失敗",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "image_upload_failed": {
                            "summary": "圖片上傳失敗",
                            "value": {"error": "圖片上傳失敗"}
                        }
                    }
                }
            }
        },
        401: {
            "description": "未授權存取",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "未授權"}
                }
            }
        },
        500: {
            "description": "伺服器內部錯誤",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "data_creation_failed": {
                            "summary": "資料建立失敗",
                            "value": {"error": "送養資料建立失敗"}
                        },
                        "server_error": {
                            "summary": "一般伺服器錯誤",
                            "value": {"error": "伺服器錯誤"}
                        }
                    }
                }
            }
        }
    },
    operation_id="create_pet_adoption_post"
)
async def send_adoption(
    request: Request,
    pet_name: str = Form(
        ...,
        description="寵物名稱",
        example="小白",
        min_length=1,
        max_length=50
    ),
    pet_breed: str = Form(
        ...,
        description="寵物品種",
        example="黃金獵犬",
        min_length=1,
        max_length=100
    ),
    pet_kind: str = Form(
        ...,
        description="寵物種類",
        example="狗",
        enum=["狗", "貓", "兔子", "鳥類", "其他"]
    ),
    pet_sex: str = Form(
        ...,
        description="寵物性別",
        example="公",
        enum=["公", "母", "未知"]
    ),
    pet_bodytype: str = Form(
        ...,
        description="寵物體型",
        example="中型",
        enum=["小型", "中型", "大型"]
    ),
    pet_colour: str = Form(
        ...,
        description="寵物顏色",
        example="金黃色",
        min_length=1,
        max_length=50
    ),
    pet_place: str = Form(
        ...,
        description="所在地區",
        example="台北市",
        min_length=1,
        max_length=100
    ),
    pet_describe: str = Form(
        ...,
        description="寵物描述",
        example="個性溫和親人，已完成基本訓練",
        min_length=1,
        max_length=1000
    ),
    pet_ligation_status: str = Form(
        ...,
        description="結紮狀態",
        example="已結紮",
        enum=["已結紮", "未結紮", "未知"]
    ),
    pet_age: str = Form(
        ...,
        description="寵物年齡",
        example="2歲",
        min_length=1,
        max_length=20
    ),
    images: List[UploadFile] = File(
        ...,
        description="寵物照片（最多4張）",
        media_type="image/*"
    )
):
    """
    刊登寵物送養資訊
    
    此API用於建立新的寵物送養貼文，包含以下功能：
    
    1. **身份驗證**：透過JWT token驗證使用者身份
    2. **圖片上傳**：上傳寵物照片到雲端儲存（最多4張）
    3. **資料儲存**：將送養資訊儲存到資料庫
    4. **快取更新**：更新相關的Redis快取
    
    **注意事項：**
    - 需要在請求標頭中包含有效的JWT token
    - 圖片格式需為常見的圖片格式（JPEG, PNG等）
    - 單張圖片大小建議不超過10MB
    - 所有必填欄位都需要填寫
    
    **處理流程：**
    1. 驗證JWT token
    2. 上傳圖片到雲端存儲
    3. 將送養資料插入資料庫
    4. 將圖片URL關聯到送養貼文
    5. 清除相關快取
    6. 回傳成功結果
    """
    try:
        # 1. JWT驗證
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            raise HTTPException(status_code=401, detail="缺少授權token")
            
        user_data = JWT.decode_jwt(token)
        if not user_data:
            raise HTTPException(status_code=401, detail="未授權")

        user_id = user_data.get("userid")
        if not user_id:
            raise HTTPException(status_code=401, detail="無效的使用者資訊")

        # 2. 圖片上傳（最多4張）
        uploader = Uploader()
        image_urls = []
        
        # 檢查圖片數量
        if len(images) > 4:
            images = images[:4]
            
        for image in images:
            if image and image.filename and image.size > 0:
                # 檢查檔案類型
                if not image.content_type or not image.content_type.startswith('image/'):
                    continue
                    
                url = await uploader.upload_file(image, bucket="petbuddy-img")
                if url:
                    image_urls.append(url)

        if not image_urls:
            raise HTTPException(status_code=400, detail="圖片上傳失敗")

        # 3. 送養資料入庫
        upload_text = UploadText()
        try:
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
                raise HTTPException(status_code=500, detail="送養資料建立失敗")

            # 4. 圖片入庫
            for url in image_urls:
                upload_text.insert_img(send_id, url)

            # 5. 統一清除快取
            redis_cache.invalidate_adoption_caches(
                user_id=user_id,
                post_id=send_id,
                place=pet_place,
                kind=pet_kind,
                sex=pet_sex,
                color=pet_colour
            )

            return SuccessResponse(
                ok=True,
                message="送養資訊已成功刊登！",
                post_id=send_id
            )

        finally:
            upload_text.close()

    except HTTPException:
        raise
    except Exception as e:
        print("送養失敗:", e)
        raise HTTPException(status_code=500, detail="伺服器錯誤")