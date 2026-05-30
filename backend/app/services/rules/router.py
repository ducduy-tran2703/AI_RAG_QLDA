import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user, require_roles
from ...shared.models.user import User
from .service import RuleService
from .schemas import (
    RuleSetDto, RuleSetCreate, RuleSetUpdate, RuleSetCloneRequest,
    RuleDto, RuleCreate, RuleUpdate
)

router = APIRouter(prefix="/rules", tags=["Rules"])

# ---------- Rule Sets ----------

@router.get("/sets", response_model=List[RuleSetDto])
async def get_rule_sets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await RuleService.get_rule_sets(db)

@router.post("/sets", response_model=RuleSetDto, status_code=status.HTTP_201_CREATED)
async def create_rule_set(
    data: RuleSetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await RuleService.create_rule_set(db, data, current_user)

@router.get("/sets/{id}", response_model=RuleSetDto)
async def get_rule_set(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await RuleService.get_rule_set(db, id)

@router.put("/sets/{id}", response_model=RuleSetDto)
async def update_rule_set(
    id: int,
    data: RuleSetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await RuleService.update_rule_set(db, id, data)

@router.post("/sets/{id}/clone", response_model=RuleSetDto)
async def clone_rule_set(
    id: int,
    data: RuleSetCloneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await RuleService.clone_rule_set(db, id, data.new_name, data.new_code, current_user)

@router.post("/sets/{id}/set-default")
async def set_default_rule_set(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await RuleService.set_default(db, id)
    return {"success": True}

# ---------- Rules ----------

@router.post("/sets/{set_id}/rules", response_model=RuleDto, status_code=status.HTTP_201_CREATED)
async def create_rule(
    set_id: int,
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await RuleService.create_rule(db, set_id, data)

@router.put("/{id}", response_model=RuleDto)
async def update_rule(
    id: uuid.UUID,
    data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    return await RuleService.update_rule(db, id, data)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("BIZ_ADMIN", "IT_ADMIN"))
):
    await RuleService.delete_rule(db, id)
    return
