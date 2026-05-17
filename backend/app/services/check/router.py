from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...shared.database import get_db
from ...shared.models.check import CheckResult
from ...shared.models.document import Document
from ..auth.dependencies import get_current_active_user
from .schemas import CheckResultDto, CheckErrorDto
from uuid import UUID

router = APIRouter(prefix="/checks", tags=["Check Results"])

@router.get("/{check_id}", response_model=CheckResultDto)
async def get_check_result(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    result = await db.get(CheckResult, check_id)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả")
    # Load document để kiểm tra quyền (chỉ chủ sở hữu mới xem)
    doc = await db.get(Document, result.document_id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền xem kết quả này")
    return result

@router.get("/document/{document_id}", response_model=list[CheckResultDto])
async def list_checks_for_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Không có quyền")
    # Trả về tất cả kết quả kiểm tra của document
    # Có thể lấy từ database, nhưng hiện tại chưa có quan hệ ngược, ta query thủ công
    from sqlalchemy import select
    result = await db.execute(
        select(CheckResult)
        .where(CheckResult.document_id == document_id)
        .order_by(CheckResult.checked_at.desc())
    )
    return result.scalars().all()