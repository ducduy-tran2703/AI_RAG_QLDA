import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ...shared.websocket_manager import manager
from ...shared.models.document import Document
from ...shared.models.check import CheckResult, CheckError
from ...shared.database import async_session_maker

class CheckService:
    @staticmethod
    async def run_mock_check(check_id: str, document_id: uuid.UUID):
        print(f"[CHECK] Mock check BẮT ĐẦU cho check_id={check_id}, doc_id={document_id}")
        stages = [
            ("extracting", 30),
            ("rag", 65),
            ("llm", 90),
            ("done", 100)
        ]
        for stage, percent in stages:
            await asyncio.sleep(3)  # Giữ 3 giây để test WebSocket
            print(f"[CHECK] Gửi progress: {stage} - {percent}%")
            await manager.send_progress(check_id, {
                "type": "progress",
                "check_id": check_id,
                "stage": stage,
                "percent": percent,
                "message": f"Đang xử lý {stage}..."
            })
        
        # Sau khi hoàn tất, lưu kết quả vào DB
        async with async_session_maker() as db:
            result_id = uuid.uuid4()
            check_result = CheckResult(
                id=result_id,
                document_id=document_id,
                score=85.0,
                total_errors=3,
                critical_count=1,
                warning_count=1,
                info_count=1,
                ai_model="qwen2.5:7b",
                status="completed",
                processing_time_ms=12345,
                extraction_data={"pages": 5},
                rag_context={"ref": "NĐ30/2020"},
            )
            db.add(check_result)
            
            # Thêm các lỗi mẫu
            errors = [
                CheckError(
                    result_id=result_id,
                    error_type="FONT",
                    severity="critical",
                    description="Font chữ không đúng quy định",
                    current_value="Arial 12pt",
                    expected_value="Times New Roman 13pt",
                    suggested_fix="Chọn toàn bộ văn bản, chuyển font về Times New Roman, cỡ 13pt",
                    rag_reference="Điều 6, Khoản 2, NĐ30/2020/NĐ-CP",
                    location_info={"page": 1, "paragraph": 3},
                    confidence=0.98
                ),
                CheckError(
                    result_id=result_id,
                    error_type="MARGIN",
                    severity="warning",
                    description="Lề trái không đúng quy định",
                    current_value="2.5cm",
                    expected_value="3.0cm",
                    suggested_fix="Điều chỉnh lề trái về 3.0cm",
                    location_info={"page": 1},
                    confidence=0.95
                ),
                CheckError(
                    result_id=result_id,
                    error_type="SPACING",
                    severity="info",
                    description="Khoảng cách dòng không đồng nhất",
                    current_value="1.2",
                    expected_value="1.5",
                    suggested_fix="Cài đặt giãn dòng 1.5",
                    location_info={"page": 2},
                    confidence=0.90
                ),
            ]
            for e in errors:
                db.add(e)
            await db.commit()
        
        await manager.send_progress(check_id, {
            "type": "complete",
            "check_id": check_id,
            "result_id": str(result_id),
            "score": 85,
            "total_errors": 3
        })
        print(f"[CHECK] Mock check KẾT THÚC")
        return check_id