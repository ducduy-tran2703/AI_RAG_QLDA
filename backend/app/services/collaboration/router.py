from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user
from ...shared.models.user import User
from .service import CollaborationService
from .schemas import CommentDto, CommentCreateDto

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])

@router.get("/comments/{document_id}", response_model=List[CommentDto])
async def list_comments(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    comments = await CollaborationService.get_comments(db, document_id)
    return [CommentDto.model_validate(c) for c in comments]

@router.post("/comments", response_model=CommentDto, status_code=201)
async def add_comment(
    data: CommentCreateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    comment = await CollaborationService.add_comment(db, current_user.id, data)
    return CommentDto.model_validate(comment)

@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await CollaborationService.resolve_comment(db, comment_id)
    return {"success": True}
