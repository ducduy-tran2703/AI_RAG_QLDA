import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import Response, RedirectResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from uuid import UUID
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user
from .service import DocumentService
from .schemas import (
    DocumentDto, DocumentVersionDto, DocumentListResponse, PaginationMeta,
    DocumentUpdateRequest, DocumentUploadResponse,
    FolderDto, FolderCreateRequest, FolderUpdateRequest
)
from ...shared.models.document import Document, DocumentFolder, DocumentVersion
from ...shared.models.user import User
from ..check.service import CheckService
from ...shared.storage import get_file_url, delete_file
import asyncio

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# ===================== UPLOAD =====================

@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        folder_uuid = None
        if folder_id and folder_id.strip():
            try:
                folder_uuid = UUID(folder_id)
            except ValueError:
                raise HTTPException(status_code=422, detail="folder_id không hợp lệ")
        doc = await DocumentService.upload(db, file, current_user, folder_uuid)
        check_id = str(uuid.uuid4())
        asyncio.create_task(CheckService.run_check_pipeline(check_id, doc.id))
        return DocumentUploadResponse(
            document=DocumentDto.model_validate(doc),
            check_id=check_id
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tải lên văn bản: {str(e)}"
        )


# ===================== LIST =====================

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    folder_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    sort: str = Query("created_at"),
    order: str = Query("desc"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        docs, total = await DocumentService.get_documents(
            db, current_user, page, limit, folder_id, search, file_type, sort, order
        )
        return DocumentListResponse(
            documents=[DocumentDto.model_validate(d) for d in docs],
            meta=PaginationMeta(
                page=page,
                limit=limit,
                total=total,
                total_pages=(total + limit - 1) // limit if limit > 0 else 0
            )
        )
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi lấy danh sách văn bản"
        )

# ===================== FOLDERS =====================

@router.get("/folders", response_model=list[FolderDto])
async def get_folders(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        folders = await DocumentService.get_folders(db, current_user)
        return [FolderDto.model_validate(f) for f in folders]
    except Exception as e:
        logger.error(f"Error getting folders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi lấy danh sách thư mục"
        )


@router.post("/folders", response_model=FolderDto, status_code=201)
async def create_folder(
    data: FolderCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        folder = await DocumentService.create_folder(db, current_user, data)
        return FolderDto.model_validate(folder)
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi tạo thư mục"
        )


@router.put("/folders/{folder_id}", response_model=FolderDto)
async def update_folder(
    folder_id: UUID,
    data: FolderUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        folder = await DocumentService.update_folder(db, folder_id, current_user, data)
        return FolderDto.model_validate(folder)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating folder {folder_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi cập nhật thư mục"
        )


@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        await DocumentService.delete_folder(db, folder_id, current_user)
        return
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting folder {folder_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi xóa thư mục"
        )


# ===================== CRUD =====================

@router.get("/{document_id}", response_model=DocumentDto)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        doc = await DocumentService.get_document(db, document_id, current_user)
        return DocumentDto.model_validate(doc)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi lấy thông tin văn bản"
        )


@router.put("/{document_id}", response_model=DocumentDto)
async def update_document(
    document_id: UUID,
    data: DocumentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        doc = await DocumentService.update_document(db, document_id, current_user, data)
        return DocumentDto.model_validate(doc)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi cập nhật văn bản"
        )


@router.delete("/{document_id}", status_code=200)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        await DocumentService.delete_document(db, document_id, current_user)
        return {"success": True, "message": "Đã xóa văn bản"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi xóa văn bản"
        )


# ===================== DOWNLOAD & PREVIEW =====================

@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Verify document access
        doc = await DocumentService.get_document(db, document_id, current_user)

        from ...shared.storage import UPLOAD_DIR
        import os
        # Đảm bảo đường dẫn sử dụng phân tách của hệ điều hành
        normalized_key = doc.storage_key.replace('/', os.sep).replace('\\', os.sep)
        file_path = os.path.abspath(os.path.join(UPLOAD_DIR, normalized_key))

        logger.info(f"Checking file existence: {file_path}")

        if not os.path.exists(file_path):
             logger.error(f"File not found: {file_path}")
             raise HTTPException(status_code=404, detail="Tệp tin không tồn tại trên máy chủ")

        return FileResponse(
            path=file_path,
            filename=doc.original_filename,
            media_type=doc.mime_type
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error downloading document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi tải xuống văn bản"
        )


@router.get("/{document_id}/preview")
async def preview_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        doc = await DocumentService.get_document(db, document_id, current_user)
        url = await get_file_url(doc.storage_key)
        return {"preview_url": url, "file_type": doc.file_type}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error previewing document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi xem trước văn bản"
        )


# ===================== VERSIONS =====================

@router.get("/{document_id}/versions", response_model=list[DocumentVersionDto])
async def list_versions(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        doc = await DocumentService.get_document(db, document_id, current_user)
        result = await db.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == doc.id)
            .order_by(DocumentVersion.version_number.desc())
        )
        versions = result.scalars().all()
        return [DocumentVersionDto.model_validate(v) for v in versions]
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error listing versions for document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi lấy danh sách phiên bản"
        )


@router.post("/{document_id}/versions", response_model=DocumentVersionDto, status_code=201)
async def create_version(
    document_id: UUID,
    file: UploadFile = File(...),
    change_notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        doc = await DocumentService.get_document(db, document_id, current_user)
        version = await DocumentService.create_version(db, doc, file, current_user, change_notes)
        return DocumentVersionDto.model_validate(version)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating version for document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi tạo phiên bản mới"
        )
