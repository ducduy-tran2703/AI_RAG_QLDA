from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...shared.database import get_db
from ...shared.models.check import CheckResult, CheckError
from ...shared.models.document import Document
from ...shared.models.system import AiFeedback
from ..auth.dependencies import get_current_active_user
from .schemas import (
    CheckResultDto, CheckErrorDto, CheckCreateRequest, CheckCreateResponse,
    FeedbackCreateRequest, FeedbackDto, NormalizePreviewResponse, NormalizeChangeDto
)
from .service import CheckService
from uuid import UUID
from typing import Optional, List

router = APIRouter(prefix="/checks", tags=["Check Results"])


@router.post("", response_model=CheckCreateResponse, status_code=201)
async def create_check(
    data: CheckCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Tạo một phiên kiểm tra mới cho văn bản"""
    # Kiểm tra document thuộc về user
    doc = await db.get(Document, data.document_id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản")
    if doc.is_deleted:
        raise HTTPException(status_code=400, detail="Văn bản đã bị xóa")
    
    check_id = await CheckService.create_check(db, data, current_user)
    return CheckCreateResponse(check_id=str(check_id))


@router.get("/{check_id}", response_model=CheckResultDto)
async def get_check_result(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Lấy kết quả kiểm tra chi tiết"""
    result = await CheckService.get_check(db, check_id, current_user)
    return CheckResultDto.model_validate(result)


@router.get("/document/{document_id}", response_model=list[CheckResultDto])
async def list_checks_for_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Lấy danh sách kết quả kiểm tra của một văn bản"""
    doc = await db.get(Document, document_id)
    if not doc or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy văn bản")
    
    result = await db.execute(
        select(CheckResult)
        .where(CheckResult.document_id == document_id)
        .order_by(CheckResult.checked_at.desc())
        .options(selectinload(CheckResult.errors))
    )
    checks = result.scalars().all()
    return [CheckResultDto.model_validate(c) for c in checks]


# ===================== FEEDBACK =====================

@router.post("/{check_id}/errors/{error_id}/feedback", response_model=FeedbackDto)
async def create_feedback(
    check_id: UUID,
    error_id: UUID,
    data: FeedbackCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Gửi phản hồi về một lỗi (đúng/sai)"""
    # Kiểm tra error tồn tại và thuộc check
    error = await db.get(CheckError, error_id)
    if not error or error.result_id != check_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy lỗi")
    
    feedback = AiFeedback(
        error_id=error_id,
        user_id=current_user.id,
        is_correct=data.is_correct,
        user_note=data.user_note,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return FeedbackDto.model_validate(feedback)


# ===================== EXPORT =====================

@router.get("/{check_id}/export/json", response_model=dict)
async def export_check_json(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Xuất kết quả kiểm tra dạng JSON"""
    result = await CheckService.get_check(db, check_id, current_user)
    return {
        "id": str(result.id),
        "document_id": str(result.document_id),
        "score": result.score,
        "total_errors": result.total_errors,
        "critical_count": result.critical_count,
        "warning_count": result.warning_count,
        "info_count": result.info_count,
        "ai_model": result.ai_model,
        "status": result.status,
        "processing_time_ms": result.processing_time_ms,
        "errors": [
            {
                "id": str(e.id),
                "error_type": e.error_type,
                "severity": e.severity,
                "description": e.description,
                "current_value": e.current_value,
                "expected_value": e.expected_value,
                "suggested_fix": e.suggested_fix,
                "rag_reference": e.rag_reference,
                "location_info": e.location_info,
                "confidence": e.confidence,
            }
            for e in result.errors
        ]
    }


# ===================== RECHECK =====================

@router.post("/{check_id}/recheck", response_model=CheckCreateResponse)
async def recheck_document(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Kiểm tra lại văn bản"""
    result = await CheckService.get_check(db, check_id, current_user)
    new_check_id = await CheckService.create_check(
        db,
        type("data", (), {"document_id": result.document_id, "version_id": None, "rule_set_id": None})(),
        current_user
    )
    return CheckCreateResponse(check_id=str(new_check_id))


# ===================== NORMALIZE =====================

@router.get("/{check_id}/normalize/preview", response_model=NormalizePreviewResponse)
async def preview_normalize(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Xem trước các thay đổi chuẩn hóa"""
    result = await CheckService.get_check(db, check_id, current_user)
    changes = []
    for error in result.errors:
        if error.suggested_fix:
            changes.append(NormalizeChangeDto(
                error_id=error.id,
                change_type=error.error_type,
                description=error.description[:200],
                current_value=error.current_value,
                new_value=error.expected_value,
            ))
    return NormalizePreviewResponse(changes=changes)


@router.post("/{check_id}/normalize/apply")
async def apply_normalize(
    check_id: UUID,
    change_ids: List[UUID],
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Áp dụng các thay đổi chuẩn hóa và tạo văn bản mới"""
    # Logic này sẽ được AI Team tích hợp sau.
    # Hiện tại trả về URL mock.
    return {
        "success": True,
        "message": "Đã áp dụng các thay đổi. Văn bản đang được xử lý.",
        "download_url": f"/api/v1/documents/normalized_mock.docx"
    }


@router.get("/{check_id}/export/pdf")
async def export_check_pdf(
    check_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Xuất báo cáo kết quả kiểm tra dạng PDF"""
    result = await CheckService.get_check(db, check_id, current_user)

    # 1. Chuẩn bị dữ liệu cho template
    data = {
        "score": result.score,
        "checked_at": result.checked_at.strftime("%d/%m/%Y %H:%M"),
        "ai_model": result.ai_model,
        "total_errors": result.total_errors,
        "critical_count": result.critical_count,
        "warning_count": result.warning_count,
        "info_count": result.info_count,
        "errors": result.errors
    }

    # 2. Tạo nội dung HTML (Đơn giản)
    html_content = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'DejaVu Sans', sans-serif; padding: 20px; }}
                h1 {{ color: #1d4ed8; text-align: center; }}
                .summary {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 10px; border-radius: 8px; }}
                .error-item {{ margin-bottom: 15px; padding: 10px; border-left: 5px solid #ef4444; background: #fef2f2; }}
                .severity-warning {{ border-left-color: #f59e0b; background: #fffbeb; }}
                .severity-info {{ border-left-color: #3b82f6; background: #eff6ff; }}
            </style>
        </head>
        <body>
            <h1>BÁO CÁO KẾT QUẢ KIỂM TRA VĂN BẢN</h1>
            <div class="summary">
                <p><strong>Điểm tuân thủ:</strong> {data['score']}/100</p>
                <p><strong>Thời gian kiểm tra:</strong> {data['checked_at']}</p>
                <p><strong>Mô hình AI:</strong> {data['ai_model']}</p>
                <p><strong>Tổng số lỗi:</strong> {data['total_errors']} (Nghiêm trọng: {data['critical_count']}, Cảnh báo: {data['warning_count']})</p>
            </div>
            <h3>Chi tiết lỗi:</h3>
            {''.join([f'''
                <div class="error-item severity-{e.severity}">
                    <p><strong>[{e.severity.upper()}] {e.description}</strong></p>
                    <p>Hiện tại: {e.current_value} | Yêu cầu: {e.expected_value}</p>
                    <p><em>Gợi ý: {e.suggested_fix}</em></p>
                </div>
            ''' for e in data['errors']])}
        </body>
    </html>
    """

    # 3. Chuyển đổi HTML sang PDF bằng WeasyPrint
    from weasyprint import HTML
    import io

    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)

    # 4. Trả về file PDF cho trình duyệt
    return Response(
        content=pdf_file.read(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=BaoCao_KiemTra_{check_id}.pdf"
        }
    )