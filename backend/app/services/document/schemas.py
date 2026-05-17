from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# ---------- Request ----------
class UploadMultipleRequest(BaseModel):
    rule_set_id: Optional[int] = None
    folder_id: Optional[UUID] = None

class DocumentUpdateRequest(BaseModel):
    display_name: Optional[str] = None
    folder_id: Optional[UUID] = None
    doc_type: Optional[str] = None
    tags: Optional[List[str]] = None

class FolderCreateRequest(BaseModel):
    name: str
    parent_id: Optional[UUID] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class FolderUpdateRequest(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    position: Optional[int] = None

# ---------- Response ----------
class DocumentDto(BaseModel):
    id: UUID
    original_filename: str
    display_name: str
    file_type: str
    file_size_bytes: int
    minio_object_key: str
    checksum_sha256: str
    mime_type: str
    is_deleted: bool
    doc_type: Optional[str] = None
    tags: List[str] = []
    folder_id: Optional[UUID] = None
    user_id: UUID
    department_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DocumentVersionDto(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    version_label: Optional[str]
    minio_object_key: str
    file_size_bytes: int
    checksum_sha256: str
    change_notes: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True

class FolderDto(BaseModel):
    id: UUID
    user_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int

class DocumentListResponse(BaseModel):
    documents: List[DocumentDto]
    meta: PaginationMeta