import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field

# ---------- Category Schemas ----------
class KnowledgeCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    sort_order: int = 0

class KnowledgeCategoryCreate(KnowledgeCategoryBase):
    pass

class KnowledgeCategoryUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None

class KnowledgeCategoryDto(KnowledgeCategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- Document Schemas ----------
class KnowledgeDocBase(BaseModel):
    category_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=500)
    doc_code: Optional[str] = None
    doc_type: str  # nghi_dinh, thong_tu, quyet_dinh, huong_dan, khac
    effective_date: Optional[date] = None
    notes: Optional[str] = None

class KnowledgeDocCreate(KnowledgeDocBase):
    pass

class KnowledgeDocUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = None
    doc_code: Optional[str] = None
    doc_type: Optional[str] = None
    is_active: Optional[bool] = None
    effective_date: Optional[date] = None
    notes: Optional[str] = None

class KnowledgeDocDto(KnowledgeDocBase):
    id: uuid.UUID
    minio_object_key: str
    ragflow_doc_id: Optional[str] = None
    chunk_count: int
    vector_size_mb: float
    index_status: str
    is_active: bool
    replaced_by_id: Optional[uuid.UUID] = None
    uploaded_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    category: Optional[KnowledgeCategoryDto] = None

    class Config:
        from_attributes = True

class KnowledgeDocListResponse(BaseModel):
    documents: List[KnowledgeDocDto]
    total: int
    page: int
    limit: int
    total_pages: int

class KnowledgeStatsResponse(BaseModel):
    total_docs: int
    total_chunks: int
    ready_docs: int
    error_docs: int
    size_mb: float
