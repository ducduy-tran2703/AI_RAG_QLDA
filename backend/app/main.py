from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .shared.config import settings
from .shared.database import engine, Base
from .shared.websocket_manager import manager
from .shared.storage import UPLOAD_DIR
from .services.auth.router import router as auth_router
from .services.document.router import router as document_router
from .services.check.router import router as check_router
from .services.analytics.router import router as analytics_router
from .services.admin.router import router as admin_router
from .services.approval.router import router as approval_router
from .services.knowledge.router import router as knowledge_router
from .services.rules.router import router as rules_router
from .services.notification.router import router as notification_router
from .services.collaboration.router import router as collaboration_router
from .services.template.router import router as template_router
import os

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# WebSocket endpoint cho realtime progress
@app.websocket("/ws/{connection_type}/{identifier}")
async def websocket_endpoint(websocket: WebSocket, connection_type: str, identifier: str):
    is_user = connection_type == "user"
    await manager.connect(websocket, identifier, is_user)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, identifier, is_user)

# Mount static files cho uploads
app.mount("/api/v1/files", StaticFiles(directory=UPLOAD_DIR), name="files")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(document_router, prefix="/api/v1")
app.include_router(check_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(approval_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(rules_router, prefix="/api/v1")
app.include_router(notification_router, prefix="/api/v1")
app.include_router(collaboration_router, prefix="/api/v1")
app.include_router(template_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    # Tự động tạo bảng (chỉ dùng cho dev, sau này dùng migration)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Đảm bảo thư mục upload tồn tại
    os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}