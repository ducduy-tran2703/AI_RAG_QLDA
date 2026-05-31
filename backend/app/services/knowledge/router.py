from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from ..auth.dependencies import get_current_active_user, require_roles
from ...shared.models.user import User
from .service import KnowledgeService
from .schemas import (
    KnowledgeDocDto, KnowledgeDocUpdate, KnowledgeDocListResponse, KnowledgeStatsResponse
)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

# ---------- Documents ----------

@router.get("/documents", response_model=KnowledgeDocListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    docs, total = await KnowledgeService.get_documents(page, limit, search or "")
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
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    doc = await KnowledgeService.upload_document(file)
    return KnowledgeDocDto.model_validate(doc)

@router.put("/documents/{doc_id}", response_model=KnowledgeDocDto)
async def update_document(
    doc_id: str,
    data: KnowledgeDocUpdate,
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    doc = await KnowledgeService.update_document(doc_id, data)
    return KnowledgeDocDto.model_validate(doc)

@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await KnowledgeService.delete_document(doc_id)
    return

@router.post("/documents/{doc_id}/reindex")
async def reindex_document(
    doc_id: str,
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await KnowledgeService.reindex_document(doc_id)
    return {"success": True}

@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_active_user)
):
    return await KnowledgeService.get_stats()
