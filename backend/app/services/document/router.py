import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import Response, RedirectResponse
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


router = APIRouter(prefix="/documents", tags=["Documents"])


# ===================== UPLOAD =====================

@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    folder_uuid = None
    if folder_id and folder_id.strip():
        try:
            folder_uuid = UUID(folder_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="folder_id không hợp lệ")
    doc = await DocumentService.upload(db, file, current_user, folder_uuid)
    check_id = str(uuid.uuid4())
    asyncio.create_task(CheckService.run_mock_check(check_id, doc.id))
    return DocumentUploadResponse(
        document=DocumentDto.model_validate(doc),
        check_id=check_id
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
    docs, total = await DocumentService.get_documents(
        db, current_user, page, limit, folder_id, search, file_type, sort, order
    )
    return DocumentListResponse(
        documents=[DocumentDto.model_validate(d) for d in docs],
        meta=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=(total + limit - 1) // limit
        )
    )

# ===================== FOLDERS =====================

@router.get("/folders", response_model=list[FolderDto])
async def get_folders(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    folders = await DocumentService.get_folders(db, current_user)
    return [FolderDto.model_validate(f) for f in folders]


@router.post("/folders", response_model=FolderDto, status_code=201)
async def create_folder(
    data: FolderCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    folder = await DocumentService.create_folder(db, current_user, data)
    return FolderDto.model_validate(folder)


@router.put("/folders/{folder_id}", response_model=FolderDto)
async def update_folder(
    folder_id: UUID,
    data: FolderUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    folder = await DocumentService.update_folder(db, folder_id, current_user, data)
    return FolderDto.model_validate(folder)


@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    await DocumentService.delete_folder(db, folder_id, current_user)
    return


# ===================== CRUD =====================

@router.get("/{document_id}", response_model=DocumentDto)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await DocumentService.get_document(db, document_id, current_user)
    return DocumentDto.model_validate(doc)


@router.put("/{document_id}", response_model=DocumentDto)
async def update_document(
    document_id: UUID,
    data: DocumentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await DocumentService.update_document(db, document_id, current_user, data)
    return DocumentDto.model_validate(doc)


@router.delete("/{document_id}", status_code=200)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    success = await DocumentService.delete_document(db, document_id, current_user)
    return {"success": True, "message": "Đã xóa văn bản"}


# ===================== DOWNLOAD & PREVIEW =====================

@router.get("/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await DocumentService.get_document(db, document_id, current_user)
    url = await get_file_url(doc.minio_object_key)
    return RedirectResponse(url=url)


@router.get("/{document_id}/preview")
async def preview_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await DocumentService.get_document(db, document_id, current_user)
    url = await get_file_url(doc.minio_object_key)
    return {"preview_url": url, "file_type": doc.file_type}


# ===================== VERSIONS =====================

@router.get("/{document_id}/versions", response_model=list[DocumentVersionDto])
async def list_versions(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await DocumentService.get_document(db, document_id, current_user)
    result = await db.execute(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == doc.id)
        .order_by(DocumentVersion.version_number.desc())
    )
    versions = result.scalars().all()
    return [DocumentVersionDto.model_validate(v) for v in versions]


@router.post("/{document_id}/versions", response_model=DocumentVersionDto, status_code=201)
async def create_version(
    document_id: UUID,
    file: UploadFile = File(...),
    change_notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await DocumentService.get_document(db, document_id, current_user)
    version = await DocumentService.create_version(db, doc, file, current_user, change_notes)
    return DocumentVersionDto.model_validate(version)
