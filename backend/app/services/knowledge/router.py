import uuid
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user, require_roles
from ...shared.models.user import User
from .service import KnowledgeService
from .schemas import (
    KnowledgeCategoryDto, KnowledgeCategoryCreate, KnowledgeCategoryUpdate,
    KnowledgeDocDto, KnowledgeDocUpdate, KnowledgeDocListResponse, KnowledgeStatsResponse
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

# ---------- Categories ----------

@router.get("/categories", response_model=List[KnowledgeCategoryDto])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await KnowledgeService.get_categories(db)

@router.post("/categories", response_model=KnowledgeCategoryDto, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: KnowledgeCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await KnowledgeService.create_category(db, data)

@router.put("/categories/{category_id}", response_model=KnowledgeCategoryDto)
async def update_category(
    category_id: int,
    data: KnowledgeCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await KnowledgeService.update_category(db, category_id, data)

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await KnowledgeService.delete_category(db, category_id)
    return

# ---------- Documents ----------

@router.get("/documents", response_model=KnowledgeDocListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    docs, total = await KnowledgeService.get_documents(db, page, limit, category_id, status, search)
    return KnowledgeDocListResponse(
        documents=[KnowledgeDocDto.model_validate(d) for d in docs],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit if limit > 0 else 0
    )

@router.post("/documents", response_model=KnowledgeDocDto, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form(...),
    category_id: Optional[int] = Form(None),
    doc_code: Optional[str] = Form(None),
    effective_date: Optional[date] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    # Convert date to datetime if needed, or handle in service
    eff_dt = None
    if effective_date:
        from datetime import datetime
        eff_dt = datetime.combine(effective_date, datetime.min.time())

    doc = await KnowledgeService.upload_document(
        db, file, title, doc_type, category_id, doc_code, eff_dt, current_user
    )
    return KnowledgeDocDto.model_validate(doc)

@router.put("/documents/{doc_id}", response_model=KnowledgeDocDto)
async def update_document(
    doc_id: uuid.UUID,
    data: KnowledgeDocUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    doc = await KnowledgeService.update_document(db, doc_id, data)
    return KnowledgeDocDto.model_validate(doc)

@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await KnowledgeService.delete_document(db, doc_id)
    return

@router.post("/documents/{doc_id}/reindex")
async def reindex_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await KnowledgeService.reindex_document(db, doc_id)
    return {"success": True}

@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await KnowledgeService.get_stats(db)
