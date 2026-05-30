import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from ...shared.models.notification import Notification
from ...shared.websocket_manager import manager
from .schemas import NotificationDto

class NotificationService:
    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: uuid.UUID,
        type: str,
        title: str,
        body: str,
        channel: str = "in_app",
        action_url: Optional[str] = None,
        priority: str = "normal"
    ):
        notification = Notification(
            user_id=user_id,
            type=type,
            channel=channel,
            title=title,
            body=body,
            action_url=action_url,
            priority=priority
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # Push via WebSocket if in_app
        if channel == "in_app":
            # Assuming user_id can be used as a room ID or we have a mapping
            # For now, let's assume we can broadcast to a check_id or user_id room
            # Let's use a generic room or specific user room in the manager
            await manager.broadcast_to_user(str(user_id), {
                "type": "notification",
                "notification": NotificationDto.model_validate(notification).model_dump()
            })

        return notification

    @staticmethod
    async def get_notifications(db: AsyncSession, user_id: uuid.UUID, limit: int = 20):
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        notifications = result.scalars().all()

        unread_count_res = await db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id, Notification.is_read == False)
        )
        unread_count = unread_count_res.scalar() or 0

        return notifications, unread_count

    @staticmethod
    async def mark_as_read(db: AsyncSession, user_id: uuid.UUID, notification_ids: List[uuid.UUID]):
        await db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.id.in_(notification_ids))
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await db.commit()
        return True
