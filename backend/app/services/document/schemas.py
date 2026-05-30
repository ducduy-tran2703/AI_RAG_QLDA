import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentDto(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    folder_id: Optional[uuid.UUID] = None
    original_filename: str
    display_name: str
    file_type: str
    file_size_bytes: int
    minio_object_key: str
    checksum_sha256: str
    mime_type: str
    is_deleted: bool = False
    doc_type: Optional[str] = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentVersionDto(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    version_label: Optional[str] = None
    minio_object_key: str
    file_size_bytes: int
    checksum_sha256: str
    change_notes: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentDto]
    meta: PaginationMeta


class DocumentUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    folder_id: Optional[uuid.UUID] = None
    doc_type: Optional[str] = None
    tags: Optional[list[str]] = None


class FolderDto(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    position: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FolderCreateRequest(BaseModel):
    name: str
    parent_id: Optional[uuid.UUID] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class FolderUpdateRequest(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    position: Optional[int] = None


class DocumentUploadResponse(BaseModel):
    document: DocumentDto
    check_id: str