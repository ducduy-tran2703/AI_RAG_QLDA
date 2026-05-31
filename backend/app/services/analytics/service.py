import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ...shared.models.document import Document
from ...shared.models.check import CheckResult
from ...shared.models.user import User

class AnalyticsService:
    @staticmethod
    async def get_dashboard_stats(db: AsyncSession, user: User):
        # 1. Total documents (not deleted)
        total_docs_query = select(func.count(Document.id)).where(
            Document.user_id == user.id,
            Document.is_deleted == False
        )
        total_docs_res = await db.execute(total_docs_query)
        total_docs = total_docs_res.scalar() or 0

        # 2. Checks performed today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_checks_query = select(func.count(CheckResult.id)).join(Document).where(
            Document.user_id == user.id,
            CheckResult.checked_at >= today_start
        )
        today_checks_res = await db.execute(today_checks_query)
        today_checks = today_checks_res.scalar() or 0

        # 3. Average Score & Pass Rate
        avg_score_query = select(
            func.avg(CheckResult.score),
            func.count(CheckResult.id).filter(CheckResult.score >= 75)
        ).join(Document).where(
            Document.user_id == user.id
        )
        avg_score_res = await db.execute(avg_score_query)
        avg_score, pass_count = avg_score_res.fetchone()

        # Calculate pass rate
        total_checks_query = select(func.count(CheckResult.id)).join(Document).where(
            Document.user_id == user.id
        )
        total_checks = (await db.execute(total_checks_query)).scalar() or 0
        pass_rate = (pass_count / total_checks * 100) if total_checks > 0 else 0.0

        # 4. Trend data (last 7 days)
        trend_data = []
        for i in range(6, -1, -1):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).date()
            day_start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
            day_end = datetime.combine(day, datetime.max.time()).replace(tzinfo=timezone.utc)

            day_score_query = select(func.avg(CheckResult.score)).join(Document).where(
                Document.user_id == user.id,
                CheckResult.checked_at.between(day_start, day_end)
            )
            day_score_res = await db.execute(day_score_query)
            score = day_score_res.scalar() or 0.0

            trend_data.append({
                "date": day.strftime("%d/%m"),
                "score": round(float(score), 1)
            })

        return {
            "total_documents": total_docs,
            "documents_today": today_checks,
            "pass_rate": round(pass_rate, 1),
            "average_score": round(float(avg_score or 0.0), 1),
            "trend_data": trend_data,
            "recent_checks": []
        }
