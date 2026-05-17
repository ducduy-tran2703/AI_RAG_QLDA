from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from ...shared.database import get_db
from .service import AuthService
from .schemas import (
    LoginRequest, SSOLoginRequest, TokenRefreshRequest,
    LogoutRequest, ForgotPasswordRequest, ResetPasswordRequest,
    ChangePasswordRequest, RegisterRequest, UserUpdateRequest,
    TokenResponse, RefreshTokenResponse, MessageResponse, UserDto, SessionDto
)
from .dependencies import get_current_active_user
from ...shared.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await AuthService.authenticate(db, data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không đúng")
    return AuthService.create_tokens(user)

@router.post("/login/sso", response_model=TokenResponse)
async def sso_login(data: SSOLoginRequest, db: AsyncSession = Depends(get_db)):
    # TODO: Tích hợp LDAP thật sau
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="SSO chưa được triển khai")

@router.post("/register", response_model=UserDto, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await AuthService.register(db, data)
        return UserDto.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(data: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token không hợp lệ")
    
    user_id = payload.get("sub")
    user = await AuthService.get_user_by_id(db, UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Người dùng không tồn tại")
    
    # Tạo access token mới
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    new_access = create_access_token(token_data)
    return RefreshTokenResponse(access_token=new_access)

@router.post("/logout", response_model=MessageResponse)
async def logout(data: LogoutRequest, current_user: User = Depends(get_current_active_user)):
    # Có thể thêm logic vô hiệu hóa token ở đây (dùng Redis trong tương lai)
    return MessageResponse(success=True, message="Đăng xuất thành công")

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    # TODO: Gửi email reset password
    return MessageResponse(success=True, message="Nếu email tồn tại, bạn sẽ nhận được hướng dẫn đặt lại mật khẩu")

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    # TODO: Xác thực token và đặt lại mật khẩu
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Chưa triển khai")

@router.get("/me", response_model=UserDto)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    return UserDto.model_validate(current_user)

@router.put("/me", response_model=UserDto)
async def update_profile(data: UserUpdateRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    user = await AuthService.update_user(db, current_user, data)
    return UserDto.model_validate(user)

@router.put("/me/password", response_model=MessageResponse)
async def change_password(data: ChangePasswordRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    success = await AuthService.change_password(db, current_user, data.current_password, data.new_password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mật khẩu hiện tại không đúng")
    return MessageResponse(success=True, message="Đổi mật khẩu thành công")

@router.get("/me/sessions", response_model=list[SessionDto])
async def get_sessions(current_user: User = Depends(get_current_active_user)):
    # TODO: Lấy danh sách phiên đăng nhập từ database
    return []