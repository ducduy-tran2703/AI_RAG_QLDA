"""
Pipeline Service — Xử lý kiểm tra văn bản thật
=================================================
Quy trình:
  1. Extract file (docx/pdf) → extraction_data
  2. Convert JSON to text → plain_text
  3. Chunk → chunks
  4. Send to RAGFlow → kết quả LLM
  5. Parse kết quả → CheckError objects
  6. Tính score
  7. Lưu DB
  8. WebSocket progress

Mỗi bước đều gửi progress qua WebSocket.
"""

import os
import sys
import uuid
import json
import time
import asyncio
from typing import Optional

from ...shared.config import settings
from ...shared.websocket_manager import manager
from ...shared.models.check import CheckResult, CheckError

# Đảm bảo thư mục backend/ nằm trong sys.path để import source package
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Import extract functions từ source/ (chạy synchronous, cần thread pool)
from source.extract_docx import extract_docx_to_dict
from source.extract_pdf import extract_pdf_to_dict

# Import text converter + chunker
from source.jsonl_to_text import build_llm_text
from source.chunnk_for_ragflow import build_chunks

# Import RAGFlow client
from .ragflow_client import ragflow_client, RAGFlowError

# Import mock pipeline
from .mock_pipeline import run_mock_pipeline

# Flag: dùng mock hay thật (có thể set bằng env)
USE_MOCK_PIPELINE = os.getenv("USE_MOCK_PIPELINE", "false").lower() == "true"


# ══════════════════════════════════════════════════════════════════════
# HÀM TÍNH SCORE
# ══════════════════════════════════════════════════════════════════════

def calculate_score(errors: list[dict]) -> float:
    """
    Tính điểm tuân thủ 0-100 dựa trên danh sách lỗi.

    Công thức:
    - Critical: 15 điểm/phát hiện
    - Warning: 5 điểm/phát hiện
    - Info: 1 điểm/phát hiện
    - Điểm = max(0, 100 - (penalty / max_penalty * 40))
    """
    if not errors:
        return 100.0

    weights = {"critical": 15, "warning": 5, "info": 1}
    penalty = sum(weights.get(e.get("severity", "info"), 1) for e in errors)
    max_penalty = len(errors) * 15

    if max_penalty == 0:
        return 100.0

    score = max(0, 100 - (penalty / max_penalty * 40))
    return round(score, 1)


def count_by_severity(errors: list[dict]) -> dict:
    """Đếm số lỗi theo severity."""
    return {
        "critical": sum(1 for e in errors if e.get("severity") == "critical"),
        "warning": sum(1 for e in errors if e.get("severity") == "warning"),
        "info": sum(1 for e in errors if e.get("severity") == "info"),
    }


# ══════════════════════════════════════════════════════════════════════
# HÀM EXTRACT FILE
# ══════════════════════════════════════════════════════════════════════

async def extract_file(file_path: str, file_type: str) -> dict:
    """
    Extract văn bản từ file docx/pdf.
    Chạy trong thread pool để không block event loop.
    """
    loop = asyncio.get_running_loop()

    if file_type == "docx":
        extraction = await loop.run_in_executor(None, extract_docx_to_dict, file_path)
    elif file_type == "pdf":
        extraction = await loop.run_in_executor(None, extract_pdf_to_dict, file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    return extraction


# ══════════════════════════════════════════════════════════════════════
# HÀM CONVERT → TEXT
# ══════════════════════════════════════════════════════════════════════

async def convert_to_text(extraction_data: dict) -> str:
    """Chuyển JSON extraction thành plain text cho LLM."""
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(None, build_llm_text, extraction_data)
    return text


# ══════════════════════════════════════════════════════════════════════
# HÀM CHUNK
# ══════════════════════════════════════════════════════════════════════

async def create_chunks(plain_text: str, filename: str) -> list[dict]:
    """
    Chia text thành các chunk.
    Trả về list chunk (chunk_000 meta + chunk_001, ...)
    """
    loop = asyncio.get_running_loop()
    chunks = await loop.run_in_executor(None, build_chunks, plain_text, filename)
    return chunks


# ══════════════════════════════════════════════════════════════════════
# HÀM PARSE KẾT QUẢ TỪ RAGFLOW
# ══════════════════════════════════════════════════════════════════════

def parse_ragflow_results(rag_results: list[dict]) -> list[dict]:
    """
    Parse kết quả từ RAGFlow thành list error dict.
    Map RAGFlow fields → pipeline error format.
    """
    errors = []
    for result in rag_results:
        if result.get("status") != "ok":
            continue
        for err in result.get("errors", []):
            errors.append({
                "type": err.get("type", "UNKNOWN"),
                "severity": err.get("severity", "info"),
                "description": err.get("description", ""),
                "current": err.get("current", ""),
                "expected": err.get("expected", ""),
                "fix": err.get("fix", ""),
                "reference": err.get("reference", ""),
                "confidence": err.get("confidence", 0.5),
                "page": err.get("page"),
                "paragraph": err.get("paragraph"),
            })
    return errors


# ══════════════════════════════════════════════════════════════════════
# HÀM LƯU KẾT QUẢ VÀO DB
# ══════════════════════════════════════════════════════════════════════

async def save_results(
    db_session,
    check_id: uuid.UUID,
    errors: list[dict],
    extraction_data: dict,
    rag_context: dict,
    processing_time_ms: int,
):
    """
    Lưu kết quả kiểm tra vào DB.

    Args:
        db_session: AsyncSession
        check_id: UUID của CheckResult
        errors: list error dict từ pipeline
        extraction_data: dict từ bước extract
        rag_context: dict metadata về RAG
        processing_time_ms: thời gian xử lý
    """
    check_result = await db_session.get(CheckResult, check_id)
    if not check_result:
        raise ValueError(f"CheckResult {check_id} không tồn tại")

    # Tính điểm
    score = calculate_score(errors)
    severity_counts = count_by_severity(errors)

    # Cập nhật CheckResult
    check_result.score = score
    check_result.total_errors = len(errors)
    check_result.critical_count = severity_counts["critical"]
    check_result.warning_count = severity_counts["warning"]
    check_result.info_count = severity_counts["info"]
    check_result.ai_model = rag_context.get("model", "qwen2.5:7b")
    check_result.status = "completed"
    check_result.processing_time_ms = processing_time_ms
    check_result.extraction_data = {
        "filename": extraction_data.get("filename", ""),
        "source": extraction_data.get("source", ""),
        "doc_type": extraction_data.get("doc_type", ""),
        "pages": extraction_data.get("pages", 1),
    }
    check_result.rag_context = rag_context

    # Xóa errors cũ (nếu có)
    for old_error in check_result.errors:
        db_session.delete(old_error)

    # Tạo CheckError objects
    for err in errors:
        check_error = CheckError(
            result_id=check_id,
            error_type=err.get("type", "UNKNOWN"),
            severity=err.get("severity", "info"),
            description=err.get("description", ""),
            current_value=err.get("current", ""),
            expected_value=err.get("expected", ""),
            suggested_fix=err.get("fix", ""),
            rag_reference=err.get("reference", ""),
            location_info={
                "page": err.get("page"),
                "paragraph": err.get("paragraph"),
            },
            confidence=err.get("confidence"),
        )
        db_session.add(check_error)

    await db_session.commit()


async def save_error_status(db_session, check_id: uuid.UUID, error_message: str):
    """Lưu trạng thái lỗi khi pipeline thất bại."""
    check_result = await db_session.get(CheckResult, check_id)
    if check_result:
        check_result.status = "error"
        check_result.error_message = error_message
        await db_session.commit()


# ══════════════════════════════════════════════════════════════════════
# PIPELINE CHÍNH
# ══════════════════════════════════════════════════════════════════════

async def run_check_pipeline(
    check_id: uuid.UUID,
    document_id: uuid.UUID,
    file_path: str,
    file_type: str,
    db_session_maker,
):
    """
    Pipeline kiểm tra văn bản chính.

    Args:
        check_id: ID của CheckResult
        document_id: ID của Document
        file_path: Đường dẫn file vật lý
        file_type: 'docx' hoặc 'pdf'
        db_session_maker: async_session_maker để tạo session
    """
    start_time = time.time()
    rag_context = {}

    try:
        # ══════════════════════════════════════════════════════════════
        # BƯỚC 1: EXTRACT
        # ══════════════════════════════════════════════════════════════
        await manager.send_progress(str(check_id), {
            "type": "progress",
            "check_id": str(check_id),
            "stage": "extracting",
            "percent": 10,
            "message": "Đang bóc tách nội dung file...",
        })

        print(f"[PIPELINE] Bắt đầu extract: {file_path} ({file_type})")
        extraction_data = await extract_file(file_path, file_type)
        print(f"[PIPELINE] Extract xong: {len(extraction_data.get('paragraphs', []))} paragraphs")

        # ══════════════════════════════════════════════════════════════
        # BƯỚC 2: CONVERT TO TEXT
        # ══════════════════════════════════════════════════════════════
        await manager.send_progress(str(check_id), {
            "type": "progress",
            "check_id": str(check_id),
            "stage": "converting",
            "percent": 25,
            "message": "Đang chuyển đổi nội dung...",
        })

        plain_text = await convert_to_text(extraction_data)
        filename = extraction_data.get("filename", f"doc_{document_id}")
        print(f"[PIPELINE] Text length: {len(plain_text)} ký tự")

        # ══════════════════════════════════════════════════════════════
        # BƯỚC 3: CHUNK
        # ══════════════════════════════════════════════════════════════
        await manager.send_progress(str(check_id), {
            "type": "progress",
            "check_id": str(check_id),
            "stage": "chunking",
            "percent": 40,
            "message": "Đang chia nội dung thành các phần...",
        })

        chunks = await create_chunks(plain_text, filename)
        content_chunks = [c for c in chunks if c.get("meta", {}).get("type") != "meta"]
        print(f"[PIPELINE] {len(content_chunks)} content chunks + 1 meta chunk")

        # ══════════════════════════════════════════════════════════════
        # BƯỚC 4: GỬI ĐẾN RAGFLOW (HOẶC MOCK)
        # ══════════════════════════════════════════════════════════════
        await manager.send_progress(str(check_id), {
            "type": "progress",
            "check_id": str(check_id),
            "stage": "sending",
            "percent": 55,
            "message": "Đang gửi đến AI phân tích...",
        })

        doc_type = extraction_data.get("doc_type", "văn bản hành chính")

        if USE_MOCK_PIPELINE:
            print(f"[PIPELINE] Dùng MOCK pipeline")
            rag_errors = await run_mock_pipeline(extraction_data)
            rag_context = {"source": "mock", "model": "heuristic"}
        else:
            print(f"[PIPELINE] Gửi {len(content_chunks)} chunks đến RAGFlow")
            rag_results = await ragflow_client.send_chunks(content_chunks, doc_type)
            print(f"[PIPELINE] RAGFlow trả về {len(rag_results)} kết quả")

            # Parse results
            await manager.send_progress(str(check_id), {
                "type": "progress",
                "check_id": str(check_id),
                "stage": "analyzing",
                "percent": 75,
                "message": "AI đang phân tích kết quả...",
            })

            rag_errors = parse_ragflow_results(rag_results)
            rag_context = {
                "source": "ragflow",
                "model": rag_results[0].get("model", "qwen2.5:7b") if rag_results else "qwen2.5:7b",
                "total_chunks": len(content_chunks),
                "failed_chunks": sum(1 for r in rag_results if r.get("status") != "ok"),
            }

        print(f"[PIPELINE] Tổng số lỗi phát hiện: {len(rag_errors)}")

        # ══════════════════════════════════════════════════════════════
        # BƯỚC 5: LƯU KẾT QUẢ
        # ══════════════════════════════════════════════════════════════
        await manager.send_progress(str(check_id), {
            "type": "progress",
            "check_id": str(check_id),
            "stage": "saving",
            "percent": 90,
            "message": "Đang lưu kết quả...",
        })

        processing_time_ms = int((time.time() - start_time) * 1000)

        async with db_session_maker() as db:
            await save_results(
                db_session=db,
                check_id=check_id,
                errors=rag_errors,
                extraction_data=extraction_data,
                rag_context=rag_context,
                processing_time_ms=processing_time_ms,
            )

        # ══════════════════════════════════════════════════════════════
        # HOÀN THÀNH
        # ══════════════════════════════════════════════════════════════
        score = calculate_score(rag_errors)
        print(f"[PIPELINE] Hoàn thành! Score={score}, {len(rag_errors)} lỗi, {processing_time_ms}ms")

        await manager.send_progress(str(check_id), {
            "type": "complete",
            "check_id": str(check_id),
            "result_id": str(check_id),
            "score": score,
            "total_errors": len(rag_errors),
            "processing_time_ms": processing_time_ms,
        })

    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"[PIPELINE] LỖI: {error_msg}")
        traceback.print_exc()

        # Lưu trạng thái lỗi
        async with db_session_maker() as db:
            await save_error_status(db, check_id, error_msg)

        # Gửi progress lỗi
        await manager.send_progress(str(check_id), {
            "type": "error",
            "check_id": str(check_id),
            "message": f"Xử lý thất bại: {error_msg[:200]}",
        })