import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...shared.models.collaboration import ApprovalRequest
from ...shared.models.document import Document
from ...shared.models.user import User
from fastapi import HTTPException

class ApprovalService:
    @staticmethod
    async def create_request(db: AsyncSession, data, current_user: User):
        # Kiểm tra document tồn tại và thuộc về user
        doc = await db.get(Document, data.document_id)
        if not doc or doc.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Văn bản không hợp lệ")
        # Kiểm tra approver tồn tại (có thể là LEADER hoặc bất kỳ)
        approver = await db.get(User, data.approver_id)
        if not approver or not approver.is_active:
            raise HTTPException(status_code=400, detail="Người phê duyệt không hợp lệ")
        
        req = ApprovalRequest(
            document_id=data.document_id,
            check_result_id=data.check_result_id,
            submitted_by=current_user.id,
            approver_id=data.approver_id,
            submitter_note=data.note,
            deadline_at=data.deadline_at,
            status="pending"
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def get_pending_requests(db: AsyncSession, user: User):
        from sqlalchemy.orm import joinedload
        result = await db.execute(
            select(ApprovalRequest)
            .options(joinedload(ApprovalRequest.document), joinedload(ApprovalRequest.submitter))
            .where(ApprovalRequest.approver_id == user.id, ApprovalRequest.status == "pending")
            .order_by(ApprovalRequest.submitted_at.desc())
        )
        requests = result.scalars().all()

        # Populate names for DTO
        for r in requests:
            r.document_name = r.document.display_name if r.document else "Unknown"
            r.submitter_name = r.submitter.full_name if r.submitter else "Unknown"

        return requests

    @staticmethod
    async def process_request(db: AsyncSession, request_id: uuid.UUID, user: User, action: str, note: str | None):
        req = await db.get(ApprovalRequest, request_id)
        if not req:
            raise HTTPException(status_code=404, detail="Yêu cầu không tồn tại")
        if req.approver_id != user.id:
            raise HTTPException(status_code=403, detail="Bạn không phải người được chỉ định phê duyệt")
        if req.status != "pending":
            raise HTTPException(status_code=400, detail="Yêu cầu đã được xử lý trước đó")
        
        req.status = "approved" if action == "approve" else "rejected"
        req.approver_note = note
        req.reviewed_at = datetime.now(timezone.utc)
        await db.commit()
        return req