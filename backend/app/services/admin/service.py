import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from ...shared.models.user import User, Department
from ...shared.auth import get_password_hash
from fastapi import HTTPException, status

class AdminService:
    @staticmethod
    async def get_users(
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        role: str | None = None,
        department_id: str | None = None,
        is_active: bool | None = None,
        search: str | None = None
    ):
        query = select(User)
        if role:
            query = query.where(User.role == role)
        if department_id:
            query = query.where(User.department_id == department_id)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if search:
            query = query.where(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
        
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar()
        
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
        result = await db.execute(query)
        users = result.scalars().all()
        return users, total

    @staticmethod
    async def create_user(db: AsyncSession, data):
        # Kiểm tra email tồn tại
        existing = await db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email đã tồn tại")
        
        user = User(
            email=data.email,
            full_name=data.full_name,
            password_hash=get_password_hash(data.password),
            role=data.role,
            auth_method="local",
            is_email_verified=True
        )
        if data.department_code:
            result = await db.execute(select(Department).where(Department.code == data.department_code))
            dept = result.scalar_one_or_none()
            if dept:
                user.department_id = dept.id
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_user(db: AsyncSession, user_id: uuid.UUID, data):
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        await db.commit()
        return user

    @staticmethod
    async def lock_user(db: AsyncSession, user_id: uuid.UUID):
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
        user.is_active = False
        await db.commit()
        return user

    @staticmethod
    async def unlock_user(db: AsyncSession, user_id: uuid.UUID):
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
        user.is_active = True
        await db.commit()
        return user

    @staticmethod
    async def reset_password(db: AsyncSession, user_id: uuid.UUID):
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
        new_pw = "Admin@123"
        user.password_hash = get_password_hash(new_pw)
        user.must_change_pw = True
        await db.commit()
        # Trong thực tế sẽ gửi email, hiện tại trả về mật khẩu tạm
        return new_pw