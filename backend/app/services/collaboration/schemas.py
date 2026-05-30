import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class CommentCreateDto(BaseModel):
    document_id: uuid.UUID
    error_id: Optional[uuid.UUID] = None
    content: str

class CommentDto(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    error_id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    user_name: Optional[str] = None
    content: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True
