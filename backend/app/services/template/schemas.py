import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class TemplateDto(BaseModel):
    id: int
    template_name: str
    template_code: str
    description: Optional[str] = None
    minio_object_key: str
    rule_set_id: int
    thumbnail_url: Optional[str] = None
    is_active: bool = True
    version: str = "1.0"
    doc_types: List[str] = []
    download_count: int = 0
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateCreateRequest(BaseModel):
    template_name: str
    template_code: str
    description: Optional[str] = None
    rule_set_id: int
    doc_types: List[str] = []


class TemplateUpdateRequest(BaseModel):
    template_name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    doc_types: Optional[List[str]] = None


class TemplateComparisonDto(BaseModel):
    id: uuid.UUID
    check_result_id: uuid.UUID
    template_id: int
    missing_sections: Optional[dict] = None
    extra_sections: Optional[dict] = None
    structural_score: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True