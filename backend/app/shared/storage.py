import os
import uuid
from fastapi import HTTPException
from .config import settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/
UPLOAD_DIR = os.path.join(BASE_DIR, settings.UPLOAD_DIR)  # backend/uploads

async def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

async def upload_file(object_name: str, data: bytes, content_type: str) -> str:
    await ensure_upload_dir()
    file_path = os.path.join(UPLOAD_DIR, object_name)
    # Đảm bảo thư mục con tồn tại
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(data)
    return object_name

async def get_file_url(object_name: str) -> str:
    # Trả về đường dẫn tương đối để frontend gọi API /files/
    return f"/api/v1/files/{object_name}"

async def delete_file(object_name: str):
    file_path = os.path.join(UPLOAD_DIR, object_name)
    if os.path.exists(file_path):
        os.remove(file_path)