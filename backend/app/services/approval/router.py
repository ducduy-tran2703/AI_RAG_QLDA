from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user
from ...shared.models.user import User
from .service import ApprovalService
from .schemas import ApprovalRequestCreate, ApprovalAction, ApprovalDto

router = APIRouter(prefix="/approval", tags=["Approval"])

@router.post("/requests", response_model=ApprovalDto, status_code=201)
async def create_approval_request(
    data: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    req = await ApprovalService.create_request(db, data, current_user)
    return req

@router.get("/requests/pending", response_model=list[ApprovalDto])
async def list_pending_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await ApprovalService.get_pending_requests(db, current_user)

@router.put("/requests/{request_id}", response_model=ApprovalDto)
async def process_approval_request(
    request_id: UUID,
    action_data: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if action_data.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Hành động không hợp lệ")
    req = await ApprovalService.process_request(db, request_id, current_user, action_data.action, action_data.note)
    return req