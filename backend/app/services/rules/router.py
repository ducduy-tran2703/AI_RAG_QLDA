from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from ..auth.dependencies import get_current_active_user, require_roles
from ...shared.models.user import User
from .service import RuleService
from .schemas import (
    RuleSetDto, RuleSetUpdate,
    RuleDto, RuleCreate, RuleUpdate, RuleListResponse
)

router = APIRouter(prefix="/rules", tags=["Rules"])

# ---------- Rule Sets (Documents) ----------

@router.get("/sets", response_model=List[RuleSetDto])
async def get_rule_sets(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    rule_sets, total = await RuleService.get_rule_sets(page, limit, search or "")
    return rule_sets

@router.put("/sets/{id}", response_model=dict)
async def update_rule_set(
    id: str,
    data: RuleSetUpdate,
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await RuleService.update_rule_set(id, data.name)

@router.delete("/sets/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule_set(
    id: str,
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await RuleService.delete_rule_set(id)
    return

# ---------- Rules (Chunks) ----------

@router.get("/sets/{set_id}/rules", response_model=RuleListResponse)
async def list_rules(
    set_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    keywords: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    chunks, total = await RuleService.get_rules(set_id, page, limit, keywords or "")
    return {"chunks": chunks, "total": total}

@router.get("/sets/{set_id}/rules/{rule_id}", response_model=dict)
async def get_rule(
    set_id: str,
    rule_id: str,
    current_user: User = Depends(get_current_active_user)
):
    # This will return the normalized chunk from RAGFlow
    return await RuleService.get_rule(set_id, rule_id)

@router.post("/sets/{set_id}/rules", response_model=dict)
async def create_rule(
    set_id: str,
    data: RuleCreate,
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await RuleService.create_rule(set_id, data)

@router.patch("/sets/{set_id}/rules/{rule_id}", response_model=dict)
async def update_rule(
    set_id: str,
    rule_id: str,
    data: RuleUpdate,
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await RuleService.update_rule(set_id, rule_id, data)

@router.delete("/sets/{set_id}/rules", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rules(
    set_id: str,
    rule_ids: List[str],
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await RuleService.delete_rules(set_id, rule_ids)
    return
