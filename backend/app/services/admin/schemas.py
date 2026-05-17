from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class UserCreateDto(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)
    department_code: Optional[str] = None
    role: str = "OFFICER"

class UserUpdateDto(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserAdminDto(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    department_code: Optional[str] = None
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedUsersResponse(BaseModel):
    users: List[UserAdminDto]
    meta: dict