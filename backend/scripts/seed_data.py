"""
Script seed dữ liệu mẫu cho hệ thống AI_VANBAN.
Chạy: python -m scripts.seed_data
"""
import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Change working directory to backend so .env file can be found
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import async_session_maker, engine, Base
from app.shared.models.user import User, Department
from app.shared.models.document import Document, DocumentFolder, DocumentVersion
from app.shared.models.check import CheckResult, CheckError
from app.shared.models.rules import RuleSet, Rule, RuleSetDepartment
from app.shared.models.knowledge import KnowledgeCategory, KnowledgeBaseDocument
from app.shared.models.template import Template
from app.shared.models.system import SystemSetting, AiAgent

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_tables():
    """Tạo tất cả bảng nếu chưa có"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Đã tạo các bảng database")


async def seed_departments(db: AsyncSession):
    departments_data = [
        {"name": "Phòng Kế hoạch", "code": "PHONG_KH", "description": "Phòng Kế hoạch và Đầu tư"},
        {"name": "Phòng Tổ chức - Hành chính", "code": "PHONG_TC_HC", "description": "Phòng Tổ chức - Hành chính"},
        {"name": "Phòng Tài chính - Kế toán", "code": "PHONG_TC_KT", "description": "Phòng Tài chính - Kế toán"},
        {"name": "Phòng Công nghệ thông tin", "code": "PHONG_CNTT", "description": "Phòng Công nghệ thông tin (IT)"},
        {"name": "Ban Giám đốc", "code": "BAN_GD", "description": "Ban Giám đốc"},
    ]
    depts = {}
    for d in departments_data:
        # Kiểm tra đã tồn tại chưa
        result = await db.execute(select(Department).where(Department.code == d["code"]))
        existing = result.scalar_one_or_none()
        if existing:
            depts[d["code"]] = existing
            print(f"  ⏭️  Phòng ban {d['code']} đã tồn tại")
            continue
        dept = Department(**d)
        db.add(dept)
        await db.flush()
        depts[d["code"]] = dept
        print(f"  ✅ Đã tạo phòng ban: {d['name']}")
    await db.commit()
    return depts


async def seed_users(db: AsyncSession, departments: dict):
    users_data = [
        {"email": "admin@cq.vn", "username": "admin", "full_name": "Admin Hệ thống", "role": "IT_ADMIN", "department_code": "PHONG_CNTT", "password": "Admin@123"},
        {"email": "truongphong@cq.vn", "username": "truongphong", "full_name": "Trần Văn Trưởng", "role": "LEADER", "department_code": "PHONG_KH", "password": "Leader@123"},
        {"email": "chuyenvien1@cq.vn", "username": "chuyenvien1", "full_name": "Nguyễn Văn A", "role": "OFFICER", "department_code": "PHONG_KH", "password": "Officer@123"},
        {"email": "chuyenvien2@cq.vn", "username": "chuyenvien2", "full_name": "Lê Thị B", "role": "OFFICER", "department_code": "PHONG_TC_HC", "password": "Officer@123"},
        {"email": "bizadmin@cq.vn", "username": "bizadmin", "full_name": "Phạm Văn C", "role": "BIZ_ADMIN", "department_code": "PHONG_TC_HC", "password": "Biz@123"},
    ]
    created_users = []
    for u in users_data:
        result = await db.execute(select(User).where(User.email == u["email"]))
        existing = result.scalar_one_or_none()
        if existing:
            created_users.append(existing)
            print(f"  ⏭️  User {u['email']} đã tồn tại")
            continue
        dept = departments.get(u["department_code"])
        user = User(
            department_id=dept.id if dept else None,
            email=u["email"],
            username=u["username"],
            password_hash=pwd_context.hash(u["password"]),
            full_name=u["full_name"],
            role=u["role"],
            is_active=True,
            is_email_verified=True,
            auth_method="local",
        )
        db.add(user)
        await db.flush()
        created_users.append(user)
        print(f"  ✅ Đã tạo user: {u['email']} ({u['role']})")
    await db.commit()
    return created_users


async def seed_rule_sets(db: AsyncSession, users: list[User]):
    """Tạo bộ quy tắc mẫu Nghị định 30/2020/NĐ-CP"""
    admin = next(u for u in users if u.role == "BIZ_ADMIN")
    
    # Kiểm tra đã tồn tại
    result = await db.execute(select(RuleSet).where(RuleSet.code == "ND30_2020_STANDARD"))
    existing = result.scalar_one_or_none()
    if existing:
        print(f"  ⏭️  Bộ quy tắc ND30_2020_STANDARD đã tồn tại")
        return existing
    
    rule_set = RuleSet(
        name="Nghị định 30/2020/NĐ-CP - Chuẩn",
        code="ND30_2020_STANDARD",
        description="Bộ quy tắc kiểm tra thể thức văn bản hành chính theo Nghị định 30/2020/NĐ-CP",
        doc_types=["cong_van", "quyet_dinh", "bao_cao", "to_trinh", "thong_bao"],
        is_default=True,
        is_active=True,
        version="2.1",
        created_by=admin.id,
    )
    db.add(rule_set)
    await db.flush()
    
    # Tạo các rules chi tiết
    rules_data = [
        # Font chữ
        {"rule_code": "FONT_BODY_TIMES_13", "category": "font", "name": "Font thân văn bản",
         "expected_value": {"font_name": "Times New Roman", "size": 13},
         "severity": "critical", "error_message": "Font chữ thân văn bản không đúng quy định (phải là Times New Roman 13pt)",
         "fix_suggestion": "Chọn toàn bộ nội dung (Ctrl+A) → Thay đổi font về Times New Roman, cỡ 13pt",
         "sort_order": 1},
        {"rule_code": "FONT_HEADING_14_BOLD", "category": "font", "name": "Font tiêu đề Heading 1",
         "expected_value": {"font_name": "Times New Roman", "size": 14, "bold": True},
         "severity": "warning", "error_message": "Font tiêu đề không đúng quy định",
         "fix_suggestion": "Định dạng tiêu đề với font Times New Roman 14pt, in đậm",
         "sort_order": 2},
        # Lề trang
        {"rule_code": "MARGIN_LEFT_3", "category": "margin", "name": "Lề trái",
         "expected_value": {"cm": 3.0}, "tolerance": {"cm": 0.1},
         "severity": "critical", "error_message": "Lề trái không đúng quy định (yêu cầu: 3.0cm ± 0.1cm)",
         "fix_suggestion": "Vào Page Setup → Margins → Left: 3.0cm",
         "sort_order": 10},
        {"rule_code": "MARGIN_RIGHT_2", "category": "margin", "name": "Lề phải",
         "expected_value": {"cm": 2.0}, "tolerance": {"cm": 0.1},
         "severity": "warning", "error_message": "Lề phải không đúng quy định (yêu cầu: 2.0cm ± 0.1cm)",
         "fix_suggestion": "Vào Page Setup → Margins → Right: 2.0cm",
         "sort_order": 11},
        {"rule_code": "MARGIN_TOP_2", "category": "margin", "name": "Lề trên",
         "expected_value": {"cm": 2.0}, "tolerance": {"cm": 0.2},
         "severity": "warning", "error_message": "Lề trên không đúng quy định (yêu cầu: 2.0cm ± 0.2cm)",
         "fix_suggestion": "Vào Page Setup → Margins → Top: 2.0cm",
         "sort_order": 12},
        {"rule_code": "MARGIN_BOTTOM_2", "category": "margin", "name": "Lề dưới",
         "expected_value": {"cm": 2.0}, "tolerance": {"cm": 0.2},
         "severity": "warning", "error_message": "Lề dưới không đúng quy định (yêu cầu: 2.0cm ± 0.2cm)",
         "fix_suggestion": "Vào Page Setup → Margins → Bottom: 2.0cm",
         "sort_order": 13},
        # Quốc hiệu
        {"rule_code": "VN_QUOC_HIEU", "category": "quoc_hieu", "name": "Quốc hiệu",
         "expected_value": {"text": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"},
         "severity": "critical", "error_message": "Quốc hiệu không đúng quy định",
         "fix_suggestion": "Thêm dòng 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM' ở đầu văn bản",
         "sort_order": 20},
        {"rule_code": "VN_TIEU_NGU", "category": "quoc_hieu", "name": "Tiêu ngữ",
         "expected_value": {"text": "Độc lập - Tự do - Hạnh phúc"},
         "severity": "critical", "error_message": "Tiêu ngữ không đúng quy định",
         "fix_suggestion": "Thêm dòng 'Độc lập - Tự do - Hạnh phúc' bên dưới Quốc hiệu",
         "sort_order": 21},
        # Khoảng cách dòng
        {"rule_code": "LINE_SPACING_1_5", "category": "spacing", "name": "Khoảng cách dòng",
         "expected_value": {"spacing": 1.5},
         "severity": "warning", "error_message": "Khoảng cách dòng không đúng quy định (yêu cầu: 1.5 lines)",
         "fix_suggestion": "Chọn toàn bộ văn bản → Paragraph → Line spacing: 1.5",
         "sort_order": 30},
        # Số ký hiệu
        {"rule_code": "SO_KY_HIEU", "category": "so_ky_hieu", "name": "Số ký hiệu văn bản",
         "expected_value": {"pattern": "Số: .../..."},
         "severity": "info", "error_message": "Số ký hiệu văn bản cần theo mẫu 'Số: xx/xxx'",
         "fix_suggestion": "Thêm số ký hiệu theo mẫu quy định",
         "sort_order": 40},
        # Ngày tháng
        {"rule_code": "NGAY_THANG", "category": "ngay_thang", "name": "Ngày tháng văn bản",
         "expected_value": {"pattern": "Ngày ... tháng ... năm ..."},
         "severity": "info", "error_message": "Ngày tháng cần theo mẫu 'Ngày ... tháng ... năm ...'",
         "fix_suggestion": "Viết ngày tháng đúng theo mẫu quy định",
         "sort_order": 50},
    ]
    
    for r in rules_data:
        rule = Rule(
            rule_set_id=rule_set.id,
            rule_code=r["rule_code"],
            category=r["category"],
            name=r["name"],
            expected_value=r["expected_value"],
            tolerance=r.get("tolerance"),
            severity=r["severity"],
            error_message=r["error_message"],
            fix_suggestion=r.get("fix_suggestion"),
            sort_order=r["sort_order"],
        )
        db.add(rule)
    
    await db.commit()
    print(f"  ✅ Đã tạo bộ quy tắc: {rule_set.name} với {len(rules_data)} rules")
    return rule_set


async def seed_knowledge_categories(db: AsyncSession):
    cats = [
        {"name": "Thể thức văn bản", "code": "THE_THUC", "description": "Quy định về thể thức văn bản hành chính", "sort_order": 1},
        {"name": "Chính tả", "code": "CHINH_TA", "description": "Quy tắc chính tả tiếng Việt", "sort_order": 2},
        {"name": "Định dạng số", "code": "DINH_DANG_SO", "description": "Quy tắc viết số trong văn bản", "sort_order": 3},
        {"name": "Viết tắt", "code": "VIET_TAT", "description": "Danh mục từ viết tắt được phép", "sort_order": 4},
    ]
    created = []
    for c in cats:
        result = await db.execute(select(KnowledgeCategory).where(KnowledgeCategory.code == c["code"]))
        existing = result.scalar_one_or_none()
        if existing:
            created.append(existing)
            continue
        cat = KnowledgeCategory(**c)
        db.add(cat)
        await db.flush()
        created.append(cat)
    await db.commit()
    print(f"  ✅ Đã tạo {len(cats)} danh mục knowledge")
    return created


async def seed_system_settings(db: AsyncSession):
    settings_data = [
        {"key": "llm_model", "value": "llama3:8b", "value_type": "string", "category": "ai_model",
         "label": "Model LLM", "description": "Model ngôn ngữ đang sử dụng"},
        {"key": "llm_timeout", "value": "30", "value_type": "integer", "category": "ai_model",
         "label": "Timeout LLM (giây)", "description": "Thời gian chờ tối đa khi gọi LLM"},
        {"key": "concurrent_processing", "value": "3", "value_type": "integer", "category": "ai_model",
         "label": "Xử lý đồng thời", "description": "Số văn bản xử lý đồng thời"},
        {"key": "password_min_length", "value": "8", "value_type": "integer", "category": "security",
         "label": "Độ dài mật khẩu tối thiểu"},
        {"key": "max_login_attempts", "value": "5", "value_type": "integer", "category": "security",
         "label": "Số lần đăng nhập sai tối đa"},
        {"key": "auto_logout_minutes", "value": "30", "value_type": "integer", "category": "security",
         "label": "Tự động đăng xuất sau (phút)"},
        {"key": "max_file_size_mb", "value": "50", "value_type": "integer", "category": "storage",
         "label": "Kích thước file tối đa (MB)"},
        {"key": "retention_days", "value": "365", "value_type": "integer", "category": "storage",
         "label": "Giữ lịch sử tối đa (ngày)"},
    ]
    for s in settings_data:
        result = await db.execute(select(SystemSetting).where(SystemSetting.key == s["key"]))
        existing = result.scalar_one_or_none()
        if existing:
            continue
        setting = SystemSetting(**s, is_editable=True, default_value=s["value"])
        db.add(setting)
    await db.commit()
    print(f"  ✅ Đã tạo {len(settings_data)} cài đặt hệ thống")


async def seed_ai_agents(db: AsyncSession):
    agents_data = [
        {"agent_code": "AG01", "agent_name": "Kiểm tra Lề", "description": "Kiểm tra lề trái, phải, trên, dưới",
         "sla_threshold_ms": 2000},
        {"agent_code": "AG02", "agent_name": "Kiểm tra Font", "description": "Kiểm tra font chữ, cỡ chữ",
         "sla_threshold_ms": 1500},
        {"agent_code": "AG03", "agent_name": "Kiểm tra Quốc hiệu", "description": "Kiểm tra quốc hiệu và tiêu ngữ",
         "sla_threshold_ms": 3000},
        {"agent_code": "AG04", "agent_name": "Kiểm tra Khoảng cách", "description": "Kiểm tra khoảng cách dòng, đoạn",
         "sla_threshold_ms": 2000},
        {"agent_code": "AG05", "agent_name": "Kiểm tra Định dạng số", "description": "Kiểm tra cách viết số trong văn bản",
         "sla_threshold_ms": 3000},
    ]
    for a in agents_data:
        result = await db.execute(select(AiAgent).where(AiAgent.agent_code == a["agent_code"]))
        existing = result.scalar_one_or_none()
        if existing:
            continue
        agent = AiAgent(**a, status="ACTIVE", version="1.0")
        db.add(agent)
    await db.commit()
    print(f"  ✅ Đã tạo {len(agents_data)} AI Agents")


async def seed_demo_document(db: AsyncSession, user: User, folder: DocumentFolder):
    """Tạo một document demo với check result mẫu"""
    from app.shared.storage import upload_file
    
    result = await db.execute(
        select(Document).where(Document.original_filename == "BaoCao_Q1_2026.docx", Document.user_id == user.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        print(f"  ⏭️  Document demo đã tồn tại")
        return
    
    doc = Document(
        user_id=user.id,
        department_id=user.department_id,
        folder_id=folder.id,
        original_filename="BaoCao_Q1_2026.docx",
        display_name="Báo cáo Quý 1 năm 2026",
        file_type="docx",
        file_size_bytes=24576,
        minio_object_key=f"{user.id}/demo/baocao_q1_2026.docx",
        checksum_sha256="a" * 64,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        doc_type="bao_cao",
        tags=["quy_1", "2026", "bao_cao"],
    )
    db.add(doc)
    await db.flush()
    
    # Tạo check result mẫu
    check = CheckResult(
        id=uuid.uuid4(),
        document_id=doc.id,
        score=72.5,
        total_errors=10,
        critical_count=3,
        warning_count=5,
        info_count=2,
        ai_model="llama3:8b",
        status="completed",
        processing_time_ms=18300,
        extraction_data={"pages": 5, "paragraphs": 48, "sections": ["header", "body", "footer"]},
        rag_context={"sources": ["ND30/2020/NĐ-CP", "TT01/2011/TT-BNV"]},
    )
    db.add(check)
    await db.flush()
    
    # Tạo errors mẫu
    errors_data = [
        {"error_type": "FONT", "severity": "critical", "description": "Font chữ thân văn bản không đúng quy định. Hiện tại: Arial 12pt, Yêu cầu: Times New Roman 13pt",
         "current_value": "Arial, 12pt", "expected_value": "Times New Roman, 13pt",
         "suggested_fix": "Chọn toàn bộ nội dung (Ctrl+A) → Thay đổi font về Times New Roman, cỡ 13pt",
         "rag_reference": "Điều 6, Khoản 2, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 1, "paragraph": 3, "section": "body"}, "confidence": 0.98},
        {"error_type": "MARGIN", "severity": "critical", "description": "Lề trái không đúng quy định. Hiện tại: 2.5cm, Yêu cầu: 3.0cm ± 0.1cm",
         "current_value": "2.5cm", "expected_value": "3.0cm",
         "suggested_fix": "Vào Page Setup → Margins → Left: 3.0cm",
         "rag_reference": "Điều 7, Khoản 1, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 0, "section": "all"}, "confidence": 0.95},
        {"error_type": "MARGIN", "severity": "warning", "description": "Lề phải không đúng quy định. Hiện tại: 1.5cm, Yêu cầu: 2.0cm ± 0.1cm",
         "current_value": "1.5cm", "expected_value": "2.0cm",
         "suggested_fix": "Vào Page Setup → Margins → Right: 2.0cm",
         "rag_reference": "Điều 7, Khoản 2, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 0, "section": "all"}, "confidence": 0.92},
        {"error_type": "SPACING", "severity": "warning", "description": "Khoảng cách dòng không đúng quy định. Hiện tại: 1.0, Yêu cầu: 1.5 lines",
         "current_value": "1.0", "expected_value": "1.5",
         "suggested_fix": "Chọn toàn bộ văn bản → Paragraph → Line spacing: 1.5",
         "rag_reference": "Điều 8, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 1, "section": "body"}, "confidence": 0.88},
        {"error_type": "SPACING", "severity": "info", "description": "Khoảng cách sau đoạn chưa phù hợp",
         "current_value": "0pt", "expected_value": "6pt",
         "suggested_fix": "Paragraph → Spacing After: 6pt",
         "rag_reference": "Điều 8, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 2, "paragraph": 5}, "confidence": 0.75},
        {"error_type": "HEADER", "severity": "warning", "description": "Header văn bản thiếu thông tin cơ quan chủ quản",
         "current_value": "Không có", "expected_value": "Tên cơ quan chủ quản",
         "suggested_fix": "Thêm tên cơ quan chủ quản vào phần header",
         "rag_reference": "Điều 5, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 1, "section": "header"}, "confidence": 0.82},
        {"error_type": "HEADER", "severity": "critical", "description": "Thiếu tên cơ quan ban hành trong header",
         "current_value": "Không có", "expected_value": "Tên cơ quan ban hành",
         "suggested_fix": "Bổ sung tên cơ quan ban hành ngay dưới cơ quan chủ quản",
         "rag_reference": "Điều 5, Khoản 2, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 1, "section": "header"}, "confidence": 0.90},
        {"error_type": "ALIGNMENT", "severity": "warning", "description": "Căn lề văn bản chưa đúng. Văn bản hành chính cần căn đều hai bên (Justify)",
         "current_value": "Left", "expected_value": "Justify",
         "suggested_fix": "Chọn toàn bộ văn bản → Căn đều hai bên (Ctrl+J)",
         "rag_reference": "Điều 9, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 1, "section": "body"}, "confidence": 0.85},
        {"error_type": "FONT", "severity": "info", "description": "Tiêu đề chưa được in đậm theo quy định",
         "current_value": "Regular", "expected_value": "Bold",
         "suggested_fix": "Bôi đen tiêu đề → Ctrl+B",
         "rag_reference": "Điều 6, Khoản 3, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 1, "paragraph": 1}, "confidence": 0.78},
        {"error_type": "QUOC_HIEU", "severity": "warning", "description": "Quốc hiệu chưa được căn giữa",
         "current_value": "Left", "expected_value": "Center",
         "suggested_fix": "Căn giữa dòng Quốc hiệu và Tiêu ngữ",
         "rag_reference": "Điều 10, Nghị định 30/2020/NĐ-CP",
         "location_info": {"page": 1, "paragraph": 1}, "confidence": 0.91},
    ]
    
    for e in errors_data:
        error = CheckError(
            result_id=check.id,
            error_type=e["error_type"],
            severity=e["severity"],
            description=e["description"],
            current_value=e.get("current_value"),
            expected_value=e.get("expected_value"),
            suggested_fix=e.get("suggested_fix"),
            rag_reference=e.get("rag_reference"),
            location_info=e.get("location_info", {}),
            confidence=e.get("confidence"),
        )
        db.add(error)
    
    await db.commit()
    print(f"  ✅ Đã tạo document demo + check result (72.5/100, 10 errors)")


async def main():
    print("🚀 Bắt đầu seed dữ liệu...\n")
    
    # 1. Tạo bảng
    print("📦 Tạo bảng database...")
    await create_tables()
    
    async with async_session_maker() as db:
        # 2. Departments
        print("\n🏢 Seed phòng ban...")
        depts = await seed_departments(db)
        
        # 3. Users
        print("\n👤 Seed người dùng...")
        users = await seed_users(db, depts)
        
        # 4. Rule Sets
        print("\n📋 Seed bộ quy tắc...")
        await seed_rule_sets(db, users)
        
        # 5. Knowledge Categories
        print("\n📚 Seed danh mục knowledge...")
        await seed_knowledge_categories(db)
        
        # 6. System Settings
        print("\n⚙️ Seed cài đặt hệ thống...")
        await seed_system_settings(db)
        
        # 7. AI Agents
        print("\n🤖 Seed AI Agents...")
        await seed_ai_agents(db)
        
        # 8. Demo Documents
        print("\n📄 Seed document demo...")
        officer = next(u for u in users if u.role == "OFFICER")
        # Tạo folder mẫu cho user
        folder_result = await db.execute(
            select(DocumentFolder).where(DocumentFolder.name == "Báo cáo", DocumentFolder.user_id == officer.id)
        )
        folder = folder_result.scalar_one_or_none()
        if not folder:
            folder = DocumentFolder(user_id=officer.id, name="Báo cáo", color="#3B82F6", icon="file-text", position=0)
            db.add(folder)
            await db.flush()
            print(f"  ✅ Đã tạo folder mẫu: Báo cáo")
        
        await seed_demo_document(db, officer, folder)
        
        # Tạo thêm folder mẫu
        other_folders = [
            {"name": "Công văn đi", "color": "#22C55E", "icon": "send"},
            {"name": "Quyết định", "color": "#F59E0B", "icon": "file-plus"},
        ]
        for f in other_folders:
            result = await db.execute(
                select(DocumentFolder).where(DocumentFolder.name == f["name"], DocumentFolder.user_id == officer.id)
            )
            if not result.scalar_one_or_none():
                folder = DocumentFolder(user_id=officer.id, **f, position=0)
                db.add(folder)
        await db.commit()
        print(f"  ✅ Đã tạo folders mẫu")
    
    print("\n🎉 Seed dữ liệu hoàn tất!")
    print("\n📝 Tài khoản đăng nhập:")
    print("   Admin:      admin@cq.vn / Admin@123 (IT_ADMIN)")
    print("   Trưởng phòng: truongphong@cq.vn / Leader@123 (LEADER)")
    print("   Chuyên viên: chuyenvien1@cq.vn / Officer@123 (OFFICER)")
    print("   Biz Admin:  bizadmin@cq.vn / Biz@123 (BIZ_ADMIN)")


if __name__ == "__main__":
    asyncio.run(main())