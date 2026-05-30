from fastapi import APIRouter, Depends
from ...shared.database import get_db
from ..auth.dependencies import get_current_active_user
from .schemas import DashboardDto
from .service import AnalyticsService
from sqlalchemy.ext.asyncio import AsyncSession
from ...shared.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=DashboardDto)
async def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    stats = await AnalyticsService.get_dashboard_stats(db, current_user)
    return DashboardDto(**stats)
