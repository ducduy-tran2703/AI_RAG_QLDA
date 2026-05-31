"""
Mock Pipeline — Dùng khi chưa có RAGFlow API hoặc cần test flow
=================================================================
Trả về lỗi giả dựa trên dữ liệu extraction thật.
"""

import asyncio
import random
from typing import Optional


def _check_font_in_paragraph(para: dict) -> list[dict]:
    """Kiểm tra font trong paragraph, trả về danh sách lỗi phát hiện."""
    errors = []
    text = para.get("text", "")
    idx = para.get("idx", 0)
    page = para.get("page", 1)

    # Kiểm tra từ runs (docx) hoặc spans (pdf)
    fragments = para.get("runs", []) or para.get("spans", [])

    for frag in fragments:
        fmt = frag.get("fmt", "")
        txt = frag.get("txt", "")

        # Font Arial → critical (NĐ30 yêu cầu Times New Roman)
        if "Arial" in fmt and txt.strip():
            errors.append({
                "type": "FONT",
                "severity": "critical",
                "description": f"Font Arial phát hiện trong đoạn văn",
                "current": fmt,
                "expected": "Times New Roman 13pt",
                "fix": "Chuyển font về Times New Roman 13pt",
                "reference": "Điều 6, Khoản 2, NĐ30/2020/NĐ-CP",
                "confidence": round(random.uniform(0.85, 0.98), 2),
                "page": page,
                "paragraph": idx,
            })

        # Font < 12pt → warning
        if any(kw in fmt for kw in ["8pt", "9pt", "10pt", "11pt"]) and txt.strip():
            errors.append({
                "type": "FONT_SIZE",
                "severity": "warning",
                "description": f"Cỡ chữ nhỏ hơn quy định trong đoạn văn",
                "current": fmt,
                "expected": "13pt",
                "fix": "Tăng cỡ chữ lên 13pt",
                "reference": "Điều 6, Khoản 2, NĐ30/2020/NĐ-CP",
                "confidence": round(random.uniform(0.80, 0.95), 2),
                "page": page,
                "paragraph": idx,
            })

    return errors


def _check_margins(extraction_data: dict) -> list[dict]:
    """Kiểm tra lề trang."""
    errors = []
    margins = extraction_data.get("margins", {})

    if margins.get("left_cm", 3.0) < 2.8:
        errors.append({
            "type": "MARGIN",
            "severity": "warning",
            "description": "Lề trái nhỏ hơn quy định",
            "current": f"{margins['left_cm']}cm",
            "expected": "3.0cm (±0.2cm)",
            "fix": "Điều chỉnh lề trái về 3.0cm",
            "reference": "Điều 6, Khoản 1, NĐ30/2020/NĐ-CP",
            "confidence": 0.90,
            "page": 1,
            "paragraph": None,
        })

    if margins.get("right_cm", 2.0) < 1.8:
        errors.append({
            "type": "MARGIN",
            "severity": "info",
            "description": "Lề phải nhỏ hơn quy định",
            "current": f"{margins['right_cm']}cm",
            "expected": "2.0cm (±0.2cm)",
            "fix": "Điều chỉnh lề phải về 2.0cm",
            "reference": "Điều 6, Khoản 1, NĐ30/2020/NĐ-CP",
            "confidence": 0.85,
            "page": 1,
            "paragraph": None,
        })

    if margins.get("top_cm", 2.0) < 1.8:
        errors.append({
            "type": "MARGIN",
            "severity": "info",
            "description": "Lề trên nhỏ hơn quy định",
            "current": f"{margins['top_cm']}cm",
            "expected": "2.0cm (±0.2cm)",
            "fix": "Điều chỉnh lề trên về 2.0cm",
            "reference": "Điều 6, Khoản 1, NĐ30/2020/NĐ-CP",
            "confidence": 0.85,
            "page": 1,
            "paragraph": None,
        })

    return errors


def _check_page_number(extraction_data: dict) -> list[dict]:
    """Kiểm tra số trang."""
    errors = []
    page_number = extraction_data.get("page_number", {})

    if not page_number:
        errors.append({
            "type": "PAGE_NUMBER",
            "severity": "warning",
            "description": "Không phát hiện số trang trong văn bản",
            "current": "Không có số trang",
            "expected": "Có số trang (thường đặt ở giữa hoặc bên phải footer)",
            "fix": "Thêm số trang vào vị trí phù hợp",
            "reference": "Điều 6, Khoản 5, NĐ30/2020/NĐ-CP",
            "confidence": 0.75,
            "page": 1,
            "paragraph": None,
        })
    else:
        # Kiểm tra font size số trang
        if page_number.get("size_pt", 14) < 12:
            errors.append({
                "type": "PAGE_NUMBER_FONT",
                "severity": "info",
                "description": "Cỡ chữ số trang nhỏ hơn quy định",
                "current": f"{page_number['size_pt']}pt",
                "expected": "13-14pt",
                "fix": "Tăng cỡ chữ số trang lên 13-14pt",
                "reference": "Điều 6, Khoản 5, NĐ30/2020/NĐ-CP",
                "confidence": 0.80,
                "page": 1,
                "paragraph": None,
            })

    return errors


def _check_line_spacing(paragraphs: list[dict]) -> list[dict]:
    """Kiểm tra giãn dòng."""
    errors = []
    for para in paragraphs:
        block = para.get("block", {})
        line_spacing = block.get("line_spacing")
        if line_spacing and line_spacing < 1.3:
            errors.append({
                "type": "LINE_SPACING",
                "severity": "warning",
                "description": f"Giãn dòng quá nhỏ (đoạn {para['idx']})",
                "current": str(line_spacing),
                "expected": "1.5",
                "fix": "Điều chỉnh giãn dòng về 1.5 lines",
                "reference": "Điều 6, Khoản 4, NĐ30/2020/NĐ-CP",
                "confidence": 0.85,
                "page": para.get("page", 1),
                "paragraph": para["idx"],
            })

    return errors


async def run_mock_pipeline(extraction_data: dict) -> list[dict]:
    """
    Mock pipeline — kiểm tra heuristic dựa trên extraction data.
    
    Trả về list[dict] mỗi dict là 1 error theo format:
    {
        "type": str,
        "severity": str,
        "description": str,
        "current": str,
        "expected": str,
        "fix": str,
        "reference": str,
        "confidence": float,
        "page": int|None,
        "paragraph": int|None,
    }
    """
    # Mô phỏng thời gian xử lý
    await asyncio.sleep(1)

    errors = []
    paragraphs = extraction_data.get("paragraphs", [])

    # 1. Kiểm tra font trong từng paragraph
    for para in paragraphs:
        errors.extend(_check_font_in_paragraph(para))

    # 2. Kiểm tra lề
    errors.extend(_check_margins(extraction_data))

    # 3. Kiểm tra số trang
    errors.extend(_check_page_number(extraction_data))

    # 4. Kiểm tra giãn dòng
    errors.extend(_check_line_spacing(paragraphs))

    return errors