import uuid
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from ...shared.models.user import User, Department
from ...shared.models.system import SystemSetting, AuditLog, ApiKey
from ...shared.auth import get_password_hash
import secrets
import hashlib
from fastapi import HTTPException, status

# Setup logging
logger = logging.getLogger(__name__)

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
        try:
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
            total_res = await db.execute(count_query)
            total = total_res.scalar() or 0

            offset = (page - 1) * limit
            query = query.offset(offset).limit(limit).order_by(User.created_at.desc())
            result = await db.execute(query)
            users = result.scalars().all()
            return users, total
        except Exception as e:
            logger.error(f"AdminService.get_users error: {str(e)}")
            raise e

    @staticmethod
    async def create_user(db: AsyncSession, data):
        try:
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
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"AdminService.create_user error: {str(e)}")
            await db.rollback()
            raise e

    @staticmethod
    async def update_user(db: AsyncSession, user_id: uuid.UUID, data):
        try:
            user = await db.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
            update_data = data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(user, key, value)
            await db.commit()
            await db.refresh(user)
            return user
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"AdminService.update_user error: {str(e)}")
            await db.rollback()
            raise e

    @staticmethod
    async def lock_user(db: AsyncSession, user_id: uuid.UUID):
        try:
            user = await db.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
            user.is_active = False
            await db.commit()
            return user
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"AdminService.lock_user error: {str(e)}")
            await db.rollback()
            raise e

    @staticmethod
    async def unlock_user(db: AsyncSession, user_id: uuid.UUID):
        try:
            user = await db.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
            user.is_active = True
            await db.commit()
            return user
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"AdminService.unlock_user error: {str(e)}")
            await db.rollback()
            raise e

    @staticmethod
    async def reset_password(db: AsyncSession, user_id: uuid.UUID):
        try:
            user = await db.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
            new_pw = "Admin@123"
            user.password_hash = get_password_hash(new_pw)
            user.must_change_pw = True
            await db.commit()
            return new_pw
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"AdminService.reset_password error: {str(e)}")
            await db.rollback()
            raise e

    # ---------- System Settings ----------
    @staticmethod
    async def get_settings(db: AsyncSession):
        try:
            result = await db.execute(select(SystemSetting).order_by(SystemSetting.category, SystemSetting.label))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"AdminService.get_settings error: {str(e)}")
            raise e

    @staticmethod
    async def update_setting(db: AsyncSession, key: str, value: str, user_id: uuid.UUID):
        try:
            setting = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
            obj = setting.scalar_one_or_none()
            if not obj:
                raise HTTPException(status_code=404, detail="Không tìm thấy cấu hình")
            if not obj.is_editable:
                raise HTTPException(status_code=403, detail="Cấu hình này không thể chỉnh sửa")

            obj.value = value
            obj.updated_by = user_id
            obj.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(obj)
            return obj
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"AdminService.update_setting error: {str(e)}")
            await db.rollback()
            raise e

    # ---------- Audit Logs ----------
    @staticmethod
    async def get_audit_logs(db: AsyncSession, page: int = 1, limit: int = 50, action: str = None):
        try:
            query = select(AuditLog)
            if action:
                query = query.where(AuditLog.action == action)

            count_res = await db.execute(select(func.count()).select_from(query.subquery()))
            total = count_res.scalar() or 0

            query = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit)
            result = await db.execute(query)
            return result.scalars().all(), total
        except Exception as e:
            logger.error(f"AdminService.get_audit_logs error: {str(e)}")
            raise e

    # ---------- API Keys ----------
    @staticmethod
    async def create_api_key(db: AsyncSession, user_id: uuid.UUID, name: str):
        try:
            raw_key = f"rag_{secrets.token_urlsafe(32)}"
            key_prefix = raw_key[:8]
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

            new_key = ApiKey(
                user_id=user_id,
                name=name,
                key_prefix=key_prefix,
                key_hash=key_hash,
                scopes=["read", "write"]
            )
            db.add(new_key)
            await db.commit()
            await db.refresh(new_key)

            return new_key, raw_key
        except Exception as e:
            logger.error(f"AdminService.create_api_key error: {str(e)}")
            await db.rollback()
            raise e

    @staticmethod
    async def get_api_keys(db: AsyncSession, user_id: uuid.UUID):
        try:
            result = await db.execute(select(ApiKey).where(ApiKey.user_id == user_id))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"AdminService.get_api_keys error: {str(e)}")
            raise e

    @staticmethod
    async def revoke_api_key(db: AsyncSession, key_id: uuid.UUID, user_id: uuid.UUID):
        try:
            key = await db.get(ApiKey, key_id)
            if not key or key.user_id != user_id:
                raise HTTPException(status_code=404, detail="Không tìm thấy khóa")
            key.is_active = False
            key.revoked_at = datetime.utcnow()
            await db.commit()
            return True
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"AdminService.revoke_api_key error: {str(e)}")
            await db.rollback()
            raise e
