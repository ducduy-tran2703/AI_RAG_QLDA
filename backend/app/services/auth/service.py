import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from ...shared.auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token
)
from ...shared.models.user import User, Department
from .schemas import (
    LoginRequest, RegisterRequest, UserUpdateRequest,
    TokenResponse, UserDto, MessageResponse
)
from ...shared.database import async_session_maker

class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
        result = await db.execute(
            select(User)
            .options(selectinload(User.department))
            .where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user or not user.password_hash:
            return None
        if not user.is_active:
            return None
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            return None
        if not verify_password(password, user.password_hash):
            # Tăng số lần đăng nhập sai
            user.login_fail_count += 1
            if user.login_fail_count >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
            await db.commit()
            return None
        # Reset fail count nếu thành công
        user.login_fail_count = 0
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user

    @staticmethod
    async def register(db: AsyncSession, data: RegisterRequest) -> User:
        # Kiểm tra email đã tồn tại
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            raise ValueError("Email đã được sử dụng")
        
        # Tìm department nếu có mã
        department = None
        if data.department_code:
            result = await db.execute(select(Department).where(Department.code == data.department_code))
            department = result.scalar_one_or_none()
        
        user = User(
            email=data.email,
            full_name=data.full_name,
            password_hash=get_password_hash(data.password),
            department_id=department.id if department else None,
            role="OFFICER",
            auth_method="local",
            is_email_verified=False,
            must_change_pw=False
        )
        db.add(user)
        await db.commit()
        return await AuthService.get_user_by_id(db, user.id)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
        result = await db.execute(
            select(User)
            .options(selectinload(User.department))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_user(db: AsyncSession, user: User, data: UserUpdateRequest) -> User:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return await AuthService.get_user_by_id(db, user.id)

    @staticmethod
    async def change_password(db: AsyncSession, user: User, current_password: str, new_password: str) -> bool:
        if not verify_password(current_password, user.password_hash):
            return False
        user.password_hash = get_password_hash(new_password)
        user.must_change_pw = False
        user.updated_at = datetime.now(timezone.utc)
        await db.commit()
        return True

    @staticmethod
    def create_tokens(user: User) -> TokenResponse:
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "department_id": str(user.department_id) if user.department_id else None
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserDto.model_validate(user)
        )