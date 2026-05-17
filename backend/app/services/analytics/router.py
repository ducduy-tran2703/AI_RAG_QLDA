from fastapi import APIRouter, Depends
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user
from .schemas import DashboardDto
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardDto)
async def get_dashboard(
    current_user = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Tạm thời trả về dữ liệu mẫu, sau này thay bằng query thực tế
    return DashboardDto(
        total_documents=28,
        documents_today=5,
        pass_rate=78.0,
        average_score=82.0,
        recent_checks=[],  # Sẽ bổ sung sau
        trend_data=[
            {"date": "2026-04-01", "score": 75},
            {"date": "2026-04-08", "score": 78},
            {"date": "2026-04-15", "score": 80},
            {"date": "2026-04-22", "score": 82},
            {"date": "2026-04-29", "score": 85},
        ]
    )