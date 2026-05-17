import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user
from .service import DocumentService
from .schemas import (
    DocumentDto, DocumentListResponse, PaginationMeta,
    DocumentUpdateRequest, FolderDto, FolderCreateRequest, FolderUpdateRequest
)
from ...shared.models.document import DocumentFolder
from ...shared.models.user import User
from ..check.service import CheckService
import asyncio


router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=None, status_code=201)
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
    print(f"[UPLOAD] Tạo check_id: {check_id}, gọi mock check...")
    asyncio.create_task(CheckService.run_mock_check(check_id, doc.id))
    print(f"[UPLOAD] Đã gọi mock check (nền)")
    # Trả về thông tin document + check_id dạng JSON
    return {
        "document": DocumentDto.model_validate(doc).model_dump(),
        "check_id": check_id
    }

@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    folder_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    docs, total = await DocumentService.get_documents(
        db, current_user, page, limit, folder_id, search, file_type
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

# Folders
@router.get("/folders", response_model=list[FolderDto])
async def get_folders(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    folders = await DocumentService.get_folders(db, current_user)
    validated_folders = []
    for f in folders:
        try:
            validated_folders.append(FolderDto.model_validate(f))
        except Exception as e:
            print(f"[{datetime.now()}] [ERROR] Lỗi validate FolderDto cho folder {f.id}: {e}")
            raise HTTPException(status_code=422, detail=f"Lỗi định dạng dữ liệu thư mục: {e}")
    return validated_folders

@router.post("/folders", response_model=FolderDto, status_code=201)
async def create_folder(
    data: FolderCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    folder = await DocumentService.create_folder(db, current_user, data)
    return folder

@router.get("/{document_id}", response_model=DocumentDto)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await DocumentService.get_document(db, document_id, current_user)
    return doc

@router.put("/folders/{folder_id}", response_model=FolderDto)
async def update_folder(
    folder_id: UUID,
    data: FolderUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    folder = await db.get(DocumentFolder, folder_id)
    if not folder or folder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(folder, key, value)
    await db.commit()
    await db.refresh(folder)
    return folder

@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    folder = await db.get(DocumentFolder, folder_id)
    if not folder or folder.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy thư mục")
    await db.delete(folder)
    await db.commit()
    return