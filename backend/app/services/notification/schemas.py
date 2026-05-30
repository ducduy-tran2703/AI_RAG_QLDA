import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class NotificationDto(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    type: str
    channel: str
    title: str
    body: str
    action_url: Optional[str] = None
    priority: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    notifications: List[NotificationDto]
    unread_count: int

class MarkReadRequest(BaseModel):
    notification_ids: List[uuid.UUID]
