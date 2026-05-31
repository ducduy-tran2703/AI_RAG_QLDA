"""Drop và tạo lại toàn bộ bảng database từ models, sau đó seed dữ liệu mẫu."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.shared.database import engine, Base
from app.shared.models import (
    User, Department, Document, DocumentFolder, DocumentVersion,
    CheckResult, CheckError, ApprovalRequest, DocumentComment,
    RuleSet, Rule, RuleSetDepartment, RuleSetVersion,
    KnowledgeCategory, KnowledgeBaseDocument,
    Template, TemplateComparison,
    Notification, SystemSetting, AuditLog, SupportTicket, ApiKey,
    AiAgent, AgentTask, AiFeedback, PasswordResetToken, LoginSession,
)


async def reset_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("DROP: Xoa tat ca bang thanh cong")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("CREATE: Tao tat ca bang thanh cong")

    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda inspector: inspector.get_table_names())
        print(f"\nTong so bang: {len(tables)}")
        for t in sorted(tables):
            print(f"  - {t}")


if __name__ == "__main__":
    asyncio.run(reset_database())