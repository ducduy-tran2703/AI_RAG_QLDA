import logging
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

# Setup logging
logger = logging.getLogger(__name__)

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
    try:
        users, total = await AdminService.get_users(db, page, limit, role, department_id, is_active, search)
        return UserListResponse(
            users=[UserDto.model_validate(u) for u in users],
            meta={"page": page, "limit": limit, "total": total}
        )
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi lấy danh sách người dùng"
        )

@router.post("/users", response_model=UserDto, status_code=201)
async def create_user(
    data: UserCreateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    try:
        user = await AdminService.create_user(db, data)
        return UserDto.model_validate(user)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi tạo người dùng"
        )

@router.put("/users/{user_id}", response_model=UserDto)
async def update_user(
    user_id: UUID,
    data: UserUpdateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    try:
        user = await AdminService.update_user(db, user_id, data)
        return UserDto.model_validate(user)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi cập nhật người dùng"
        )

@router.post("/users/{user_id}/lock")
async def lock_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    try:
        await AdminService.lock_user(db, user_id)
        return {"message": "Đã khóa người dùng"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error locking user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi khóa người dùng"
        )

@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    try:
        await AdminService.unlock_user(db, user_id)
        return {"message": "Đã mở khóa người dùng"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error unlocking user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi mở khóa người dùng"
        )

@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    try:
        new_pw = await AdminService.reset_password(db, user_id)
        return {"message": f"Mật khẩu tạm: {new_pw}"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error resetting password for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi đặt lại mật khẩu"
        )

# ---------- Settings ----------

@router.get("/settings", response_model=List[SettingDto])
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    try:
        return await AdminService.get_settings(db)
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi lấy cấu hình hệ thống"
        )

@router.put("/settings/{key}", response_model=SettingDto)
async def update_setting(
    key: str,
    data: SettingUpdateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    try:
        return await AdminService.update_setting(db, key, data.value, current_user.id)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error updating setting {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi cập nhật cấu hình"
        )

# ---------- Audit Logs ----------

@router.get("/audit-logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    try:
        logs, total = await AdminService.get_audit_logs(db, page, limit, action)
        return AuditLogListResponse(
            logs=[AuditLogDto.model_validate(l) for l in logs],
            meta={"page": page, "limit": limit, "total": total}
        )
    except Exception as e:
        logger.error(f"Error listing audit logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi lấy nhật ký hệ thống"
        )

# ---------- Health ----------

@router.get("/health")
async def system_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    """Kiểm tra sức khỏe hệ thống"""
    from sqlalchemy import text
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Health check DB error: {str(e)}")
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
    try:
        return await AdminService.get_api_keys(db, current_user.id)
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi lấy danh sách khóa API"
        )

@router.post("/api-keys", status_code=201)
async def create_api_key(
    data: ApiKeyCreateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        key_obj, raw_key = await AdminService.create_api_key(db, current_user.id, data.name)
        return {
            "id": str(key_obj.id),
            "name": key_obj.name,
            "key_prefix": key_obj.key_prefix,
            "scopes": key_obj.scopes,
            "is_active": key_obj.is_active,
            "last_used_at": key_obj.last_used_at.isoformat() if key_obj.last_used_at else None,
            "usage_count": key_obj.usage_count,
            "created_at": key_obj.created_at.isoformat(),
            "key": raw_key
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo khóa API: {str(e)}"
        )

@router.delete("/api-keys/{id}")
async def revoke_api_key(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    try:
        await AdminService.revoke_api_key(db, id, current_user.id)
        return {"message": "Đã thu hồi khóa"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error revoking API key {id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi khi thu hồi khóa API"
        )
