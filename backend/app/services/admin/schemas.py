import uuid
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, EmailStr

# ---------- User Schemas ----------
class UserCreateDto(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: str
    department_code: Optional[str] = None

class UserUpdateDto(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    position: Optional[str] = None
    phone: Optional[str] = None

class UserDto(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    users: List[UserDto]
    meta: dict

# ---------- System Settings ----------
class SettingDto(BaseModel):
    key: str
    value: Optional[str] = None
    value_type: str
    category: str
    label: str
    description: Optional[str] = None
    is_editable: bool = True

    class Config:
        from_attributes = True

class SettingUpdateDto(BaseModel):
    value: str

# ---------- Audit Logs ----------
class AuditLogDto(BaseModel):
    id: int
    user_id: Optional[uuid.UUID] = None
    actor_type: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    result: str
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    logs: List[AuditLogDto]
    meta: dict

# ---------- API Keys ----------
class ApiKeyCreateDto(BaseModel):
    name: str
    expires_in_days: Optional[int] = 365

class ApiKeyDto(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    scopes: List[str]
    last_used_at: Optional[datetime] = None
    usage_count: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ApiKeyResponse(ApiKeyDto):
    key: str # Only returned once on creation
