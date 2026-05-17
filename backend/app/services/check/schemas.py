from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class CheckErrorDto(BaseModel):
    id: UUID
    error_type: str
    severity: str
    description: str
    current_value: Optional[str] = None
    expected_value: Optional[str] = None
    suggested_fix: Optional[str] = None
    rag_reference: Optional[str] = None
    location_info: Optional[dict] = {}
    confidence: Optional[float] = None

    class Config:
        from_attributes = True

class CheckResultDto(BaseModel):
    id: UUID
    document_id: UUID
    score: Optional[float] = None
    total_errors: int
    critical_count: int
    warning_count: int
    info_count: int
    ai_model: Optional[str] = None
    checked_at: datetime
    status: str
    processing_time_ms: Optional[int] = None
    errors: List[CheckErrorDto] = []

    class Config:
        from_attributes = True