from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user
from ...shared.models.user import User
from .service import NotificationService
from .schemas import NotificationDto, NotificationListResponse, MarkReadRequest

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notifications, unread_count = await NotificationService.get_notifications(db, current_user.id, limit)
    return NotificationListResponse(
        notifications=[NotificationDto.model_validate(n) for n in notifications],
        unread_count=unread_count
    )

@router.post("/mark-read")
async def mark_read(
    data: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await NotificationService.mark_as_read(db, current_user.id, data.notification_ids)
    return {"success": True}
