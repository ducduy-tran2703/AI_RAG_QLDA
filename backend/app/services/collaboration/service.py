import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from ...shared.models.collaboration import DocumentComment
from ...shared.models.user import User

class CollaborationService:
    @staticmethod
    async def add_comment(db: AsyncSession, user_id: uuid.UUID, data):
        comment = DocumentComment(
            document_id=data.document_id,
            error_id=data.error_id,
            user_id=user_id,
            content=data.content
        )
        db.add(comment)
        await db.commit()
        await db.refresh(comment)
        return comment

    @staticmethod
    async def get_comments(db: AsyncSession, document_id: uuid.UUID):
        result = await db.execute(
            select(DocumentComment)
            .options(selectinload(DocumentComment.user))
            .where(DocumentComment.document_id == document_id)
            .order_by(DocumentComment.created_at.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def resolve_comment(db: AsyncSession, comment_id: uuid.UUID):
        comment = await db.get(DocumentComment, comment_id)
        if comment:
            comment.is_resolved = True
            await db.commit()
        return comment
