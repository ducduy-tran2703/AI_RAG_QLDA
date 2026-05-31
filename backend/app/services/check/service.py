import asyncio
import uuid
import os
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ...shared.websocket_manager import manager
from ...shared.models.document import Document
from ...shared.models.check import CheckResult, CheckError
from ...shared.models.user import User
from ...shared.database import async_session_maker
from ...shared.config import settings
from .schemas import CheckCreateRequest
from .pipeline import run_check_pipeline, calculate_score, count_by_severity, extract_file, convert_to_text
from .mock_pipeline import run_mock_pipeline
from fastapi import HTTPException, status


class CheckService:
    @staticmethod
    async def create_check(db: AsyncSession, data: CheckCreateRequest, user: User) -> CheckResult:
        """Tạo một phiên kiểm tra mới và chạy pipeline (thật hoặc mock)"""
        result_id = uuid.uuid4()
        # Tạo CheckResult ngay với status processing để có thể GET ngay
        check_result = CheckResult(
            id=result_id,
            document_id=data.document_id,
            status="processing",
        )
        db.add(check_result)
        await db.commit()
        await db.refresh(check_result)

        # Lấy thông tin document để lấy file path
        doc = await db.get(Document, data.document_id)
        if not doc:
            # Nếu không tìm thấy document, vẫn chạy pipeline nhưng sẽ báo lỗi
            pass

        # Chạy pipeline trong nền
        asyncio.create_task(CheckService._run_pipeline(result_id, data.document_id))
        return check_result

    @staticmethod
    async def run_check_pipeline(check_id: uuid.UUID, document_id: uuid.UUID):
        """
        Lấy file path và chạy pipeline.
        Tách riêng để có thể lấy DB session mới.
        """
        # Lấy document để có file path
        async with async_session_maker() as db:
            doc = await db.get(Document, document_id)
            if not doc or doc.is_deleted:
                # Cập nhật trạng thái lỗi
                check = await db.get(CheckResult, check_id)
                if check:
                    check.status = "error"
                    check.error_message = f"Document {document_id} không tồn tại hoặc đã xóa"
                    await db.commit()
                await manager.send_progress(str(check_id), {
                    "type": "error",
                    "check_id": str(check_id),
                    "message": "Văn bản không tồn tại hoặc đã xóa",
                })
                return

            file_path = os.path.join(settings.UPLOAD_DIR, doc.storage_key)
            file_type = doc.file_type

        # Kiểm tra file tồn tại
        if not os.path.exists(file_path):
            async with async_session_maker() as db:
                check = await db.get(CheckResult, check_id)
                if check:
                    check.status = "error"
                    check.error_message = f"File không tồn tại: {file_path}"
                    await db.commit()
            await manager.send_progress(str(check_id), {
                "type": "error",
                "check_id": str(check_id),
                "message": "File vật lý không tồn tại trên server",
            })
            return

        # Chạy pipeline chính
        await run_check_pipeline(
            check_id=check_id,
            document_id=document_id,
            file_path=file_path,
            file_type=file_type,
            db_session_maker=async_session_maker,
        )

    @staticmethod
    async def get_check(db: AsyncSession, check_id: uuid.UUID, user: User) -> CheckResult:
        """Lấy check result + errors, kiểm tra quyền"""
        result = await db.execute(
            select(CheckResult)
            .options(selectinload(CheckResult.errors))
            .where(CheckResult.id == check_id)
        )
        check = result.scalar_one_or_none()
        if not check:
            raise HTTPException(status_code=404, detail="Không tìm thấy kết quả kiểm tra")
        
        # Kiểm tra quyền
        doc = await db.get(Document, check.document_id)
        if not doc or doc.user_id != user.id:
            raise HTTPException(status_code=403, detail="Không có quyền xem kết quả này")
        
        return check
