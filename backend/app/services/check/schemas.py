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
    version_id: Optional[UUID] = None
    rule_set_id: Optional[int] = None
    score: Optional[float] = None
    total_errors: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    ai_model: Optional[str] = None
    checked_at: datetime
    status: str
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    errors: List[CheckErrorDto] = []

    class Config:
        from_attributes = True


class CheckResultSummaryDto(BaseModel):
    id: UUID
    document_id: UUID
    score: Optional[float] = None
    total_errors: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    ai_model: Optional[str] = None
    checked_at: datetime
    status: str

    class Config:
        from_attributes = True


class CheckCreateRequest(BaseModel):
    document_id: UUID
    version_id: Optional[UUID] = None
    rule_set_id: Optional[int] = None


class CheckCreateResponse(BaseModel):
    check_id: str
    status: str = "queued"


class FeedbackCreateRequest(BaseModel):
    is_correct: bool
    user_note: Optional[str] = None


class FeedbackDto(BaseModel):
    id: int
    error_id: UUID
    user_id: UUID
    is_correct: bool
    user_note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NormalizeChangeDto(BaseModel):
    error_id: UUID
    change_type: str
    description: str
    current_value: Optional[str] = None
    new_value: Optional[str] = None


class NormalizePreviewResponse(BaseModel):
    changes: List[NormalizeChangeDto]


class NormalizeApplyResponse(BaseModel):
    document_url: str
    applied_changes: int