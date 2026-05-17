from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .shared.config import settings
from .shared.database import engine, Base
from .services.auth.router import router as auth_router
from .services.document.router import router as document_router
from fastapi.staticfiles import StaticFiles
from .shared.storage import UPLOAD_DIR
from fastapi import WebSocket, WebSocketDisconnect
from .shared.websocket_manager import manager
from .services.check.router import router as check_router
from .services.analytics.router import router as analytics_router
from .services.admin.router import router as admin_router
from .services.approval.router import router as approval_router
import os

from fastapi import WebSocket, WebSocketDisconnect
from .shared.websocket_manager import manager
# Tạo tất cả bảng (trong production dùng Alembic migrations)
# Chạy một lần khi khởi động
import asyncio
from .shared.models.user import User, Department  # Import để đăng ký models

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

@app.websocket("/ws/{check_id}")
async def websocket_endpoint(websocket: WebSocket, check_id: str):
    await manager.connect(websocket, check_id)
    try:
        while True:
            # Giữ kết nối mở, nhận message từ client (có thể dùng để subscribe/unsubscribe)
            data = await websocket.receive_text()
            # Có thể xử lý message từ client ở đây
    except WebSocketDisconnect:
        manager.disconnect(websocket, check_id)

app.mount("/api/v1/files", StaticFiles(directory=UPLOAD_DIR), name="files")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(check_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(approval_router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    # Tự động tạo bảng (chỉ dùng cho dev, sau này dùng migration)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}

