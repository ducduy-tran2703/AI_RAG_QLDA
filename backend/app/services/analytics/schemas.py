from pydantic import BaseModel
from typing import List, Optional

class TrendItem(BaseModel):
    date: str
    score: float

class DashboardDto(BaseModel):
    total_documents: int
    documents_today: int
    pass_rate: float
    average_score: float
    recent_checks: List[dict] = []
    trend_data: List[TrendItem] = []