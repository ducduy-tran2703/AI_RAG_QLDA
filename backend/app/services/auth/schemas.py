from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

# ---------- Request Schemas ----------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)

class SSOLoginRequest(BaseModel):
    ldap_username: str
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    logout_all: bool = False

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=8)
    department_code: Optional[str] = None

class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

# ---------- Response Schemas ----------
class DepartmentDto(BaseModel):
    id: UUID
    name: str
    code: str
    parent_id: Optional[UUID] = None

    class Config:
        from_attributes = True

class UserDto(BaseModel):
    id: UUID
    email: str
    username: Optional[str] = None
    full_name: str
    phone: Optional[str] = None
    position: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    department: Optional[DepartmentDto] = None
    is_active: bool
    is_email_verified: bool
    last_login_at: Optional[datetime] = None
    must_change_pw: bool
    timezone: str
    language: str
    preferences: dict = {}
    document_quota: int
    storage_quota_mb: int
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserDto

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MessageResponse(BaseModel):
    success: bool
    message: str

class SessionDto(BaseModel):
    id: UUID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[dict] = None
    is_active: bool
    expires_at: datetime
    created_at: datetime