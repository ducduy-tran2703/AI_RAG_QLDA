from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user, require_roles
from ...shared.models.user import User
from .service import AdminService
from .schemas import (
    UserDto, UserListResponse, UserCreateDto, UserUpdateDto,
    SettingDto, SettingUpdateDto, AuditLogDto, AuditLogListResponse,
    ApiKeyDto, ApiKeyCreateDto, ApiKeyResponse
)

router = APIRouter(prefix="/admin", tags=["Admin"])

# ---------- Users ----------

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    role: str | None = None,
    department_id: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    users, total = await AdminService.get_users(db, page, limit, role, department_id, is_active, search)
    return UserListResponse(
        users=[UserDto.model_validate(u) for u in users],
        meta={"page": page, "limit": limit, "total": total}
    )

@router.post("/users", response_model=UserDto, status_code=201)
async def create_user(
    data: UserCreateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    user = await AdminService.create_user(db, data)
    return UserDto.model_validate(user)

@router.put("/users/{user_id}", response_model=UserDto)
async def update_user(
    user_id: UUID,
    data: UserUpdateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    user = await AdminService.update_user(db, user_id, data)
    return UserDto.model_validate(user)

@router.post("/users/{user_id}/lock")
async def lock_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    await AdminService.lock_user(db, user_id)
    return {"message": "Đã khóa người dùng"}

@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    await AdminService.unlock_user(db, user_id)
    return {"message": "Đã mở khóa người dùng"}

@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    new_pw = await AdminService.reset_password(db, user_id)
    return {"message": f"Mật khẩu tạm: {new_pw}"}

# ---------- Settings ----------

@router.get("/settings", response_model=List[SettingDto])
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    return await AdminService.get_settings(db)

@router.put("/settings/{key}", response_model=SettingDto)
async def update_setting(
    key: str,
    data: SettingUpdateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    return await AdminService.update_setting(db, key, data.value, current_user.id)

# ---------- Audit Logs ----------

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    logs, total = await AdminService.get_audit_logs(db, page, limit, action)
    return AuditLogListResponse(
        logs=[AuditLogDto.model_validate(l) for l in logs],
        meta={"page": page, "limit": limit, "total": total}
    )

# ---------- API Keys ----------

# ---------- Health ----------

@router.get("/health")
async def system_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    """Kiểm tra sức khỏe hệ thống"""
    from ...shared.models.system import SystemSetting
    from sqlalchemy import text
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version": "1.0.0"
    }


# ---------- API Keys ----------

@router.get("/api-keys", response_model=List[ApiKeyDto])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return await AdminService.get_api_keys(db, current_user.id)

@router.post("/api-keys", response_model=ApiKeyResponse, status_code=201)
async def create_api_key(
    data: ApiKeyCreateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    key_obj, raw_key = await AdminService.create_api_key(db, current_user.id, data.name)
    res = ApiKeyResponse.model_validate(key_obj)
    res.key = raw_key
    return res

@router.delete("/api-keys/{id}")
async def revoke_api_key(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    await AdminService.revoke_api_key(db, id, current_user.id)
    return {"message": "Đã thu hồi khóa"}
