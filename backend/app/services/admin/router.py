from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user, require_roles
from ...shared.models.user import User
from .service import AdminService
from .schemas import UserAdminDto, PaginatedUsersResponse, UserCreateDto, UserUpdateDto

router = APIRouter(prefix="/admin/users", tags=["Admin - Users"])

@router.get("/", response_model=PaginatedUsersResponse)
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
    return PaginatedUsersResponse(
        users=[UserAdminDto.model_validate(u) for u in users],
        meta={"page": page, "limit": limit, "total": total}
    )

@router.post("/", response_model=UserAdminDto, status_code=201)
async def create_user(
    data: UserCreateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    user = await AdminService.create_user(db, data)
    return user

@router.put("/{user_id}", response_model=UserAdminDto)
async def update_user(
    user_id: UUID,
    data: UserUpdateDto,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    user = await AdminService.update_user(db, user_id, data)
    return user

@router.post("/{user_id}/lock")
async def lock_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    await AdminService.lock_user(db, user_id)
    return {"message": "Đã khóa người dùng"}

@router.post("/{user_id}/unlock")
async def unlock_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    await AdminService.unlock_user(db, user_id)
    return {"message": "Đã mở khóa người dùng"}

@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("IT_ADMIN"))
):
    new_pw = await AdminService.reset_password(db, user_id)
    return {"message": f"Mật khẩu tạm: {new_pw}"}