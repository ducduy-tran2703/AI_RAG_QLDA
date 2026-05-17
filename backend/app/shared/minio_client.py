from minio import Minio
from minio.error import S3Error
from .config import settings
import io

client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

async def ensure_bucket():
    if not client.bucket_exists(settings.MINIO_BUCKET):
        client.make_bucket(settings.MINIO_BUCKET)

async def upload_file(object_name: str, data: bytes, content_type: str) -> str:
    await ensure_bucket()
    client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type
    )
    return object_name

async def get_file_url(object_name: str) -> str:
    # Pre-signed URL valid 1 hour
    return client.presigned_get_object(settings.MINIO_BUCKET, object_name)

async def delete_file(object_name: str):
    client.remove_object(settings.MINIO_BUCKET, object_name)