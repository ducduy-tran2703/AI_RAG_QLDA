from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ApprovalRequestCreate(BaseModel):
    document_id: UUID
    check_result_id: Optional[UUID] = None
    approver_id: UUID
    note: Optional[str] = None
    deadline_at: Optional[datetime] = None

class ApprovalAction(BaseModel):
    action: str  # "approve" hoặc "reject"
    note: Optional[str] = None

class ApprovalDto(BaseModel):
    id: UUID
    document_id: UUID
    check_result_id: Optional[UUID] = None
    submitted_by: UUID
    approver_id: UUID
    status: str
    submitter_note: Optional[str] = None
    approver_note: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True