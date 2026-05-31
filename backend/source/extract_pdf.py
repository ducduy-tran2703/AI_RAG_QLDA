"""
extract_pdf_optimized.py
=========================
Module bóc tách TỐI ƯU cho LLM - Văn bản hành chính (.pdf text)
Dự án: AI_RAG_QLDA - Kiểm tra thể thức theo NĐ30/2020

🎯 ĐẶC ĐIỂM CHÍNH:
──────────────────
✅ Bước 1: Tái cấu trúc Block + Inline (Span-level)
   - Block: Thuộc tính đoạn văn (căn lề, khoảng cách, vị trí)
   - Spans: Gom các ký tự liền kề có CÙNG định dạng thành cụm

✅ Bước 2: Lọc rác (Drop Nulls & Defaults)
   - Loại bỏ hoàn toàn: None, False, [], 0, giá trị mặc định
   - Chỉ giữ thông tin CÓ GIÁ TRỊ cho suy luận logic
   - Lưu bbox chỉ khi cần thiết (phân biệt cột trái/phải)

📦 OUTPUT CÔ ĐẶC:
────────────────
{
  "filename": "cv123.pdf",
  "pages": 5,
  "margins": {"left_cm": 3.0, "right_cm": 2.0, ...},
  "paragraphs": [
    {
      "idx": 0,
      "text": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
      "block": {
        "align": "CENTER",
        "y_pt": 72.5,
        "space_before_pt": 12
      },
      "spans": [
        {"fmt": "Arial-13pt-Bold", "txt": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"}
      ],
      "zone": "RIGHT_COL",
      "page": 0
    },
    {
      "idx": 1,
      "text": "Điều 1. Phạm vi điều chỉnh",
      "block": {
        "indent_cm": 1.0,
        "space_before_pt": 6,
        "y_pt": 150.2
      },
      "spans": [
        {"fmt": "Times-14pt-Bold", "txt": "Điều 1."},
        {"fmt": "Times-14pt", "txt": " Phạm vi điều chỉnh"}
      ],
      "zone": "FULL_WIDTH",
      "page": 0
    }
  ]
}

Token giảm ~70-85% so với bản cũ! 🚀
"""

import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import fitz  # PyMuPDF


# ═════════════════════════════════════════════════════════════════════
# HẰNG SỐ QUY ĐỔI ĐƠN VỊ
# ═════════════════════════════════════════════════════════════════════
PT_PER_INCH = 72.0
CM_PER_INCH = 2.54
PT_PER_CM   = PT_PER_INCH / CM_PER_INCH   # ≈ 28.346 pt/cm


def pt_to_cm(pt: Optional[float]) -> Optional[float]:
    if pt is None or pt == 0:
        return None
    return round(pt / PT_PER_CM, 2)


# ═════════════════════════════════════════════════════════════════════
# HELPER: Phát hiện loại văn bản (doc_type)
# ═════════════════════════════════════════════════════════════════════
_DOC_TYPE_PATTERNS: List[tuple] = [
    # Ưu tiên từ khóa dài/cụ thể trước để tránh match nhầm
    ("văn bản hợp nhất", "vbhn"),
    ("thông tư liên tịch", "thong_tu_lien_tich"),
    ("nghị định",          "nghi_dinh"),
    ("thông tư",           "thong_tu"),
    ("quyết định",         "quyet_dinh"),
    ("chỉ thị",            "chi_thi"),
    ("nghị quyết",         "nghi_quyet"),
    ("công văn",           "cong_van"),
    ("tờ trình",           "to_trinh"),
    ("báo cáo",            "bao_cao"),
    ("kế hoạch",           "ke_hoach"),
    ("hướng dẫn",          "huong_dan"),
    ("thông báo",          "thong_bao"),
    ("biên bản",           "bien_ban"),
    ("hợp đồng",           "hop_dong"),
    ("giấy mời",           "giay_moi"),
    ("giấy phép",          "giay_phep"),
    ("đề án",              "de_an"),
]

# Detect từ tên file — ưu tiên cao nhất vì tên file do người dùng đặt có chủ đích
_FILENAME_PATTERNS: List[tuple] = [
    ("vbhn",   "vbhn"),
    ("-nd-",   "nghi_dinh"),
    ("/nd-",   "nghi_dinh"),
    ("-tt-",   "thong_tu"),
    ("/tt-",   "thong_tu"),
    ("-ttlt-", "thong_tu_lien_tich"),
    ("-qd-",   "quyet_dinh"),
    ("/qd-",   "quyet_dinh"),
    ("-ct-",   "chi_thi"),
    ("-nq-",   "nghi_quyet"),
    ("-cv-",   "cong_van"),
]


def _detect_doc_type_from_filename(filename: str) -> Optional[str]:
    """
    Phát hiện loại văn bản từ tên file.
    VD: '23-vbhn-vpqh.pdf' → 'vbhn', '45-2013-nd-cp.pdf' → 'nghi_dinh'
    """
    name_lower = filename.lower()
    for pattern, doc_type in _FILENAME_PATTERNS:
        if pattern in name_lower:
            return doc_type
    return None


def _detect_doc_type(paragraphs_text: List[str], filename: str = "") -> str:
    """
    Phát hiện loại văn bản.
    Ưu tiên: tên file → nội dung 20 đoạn đầu → 'unknown'.
    """
    # 1. Ưu tiên filename (chắc chắn nhất, không bị OCR lỗi ảnh hưởng)
    if filename:
        doc_type = _detect_doc_type_from_filename(filename)
        if doc_type:
            return doc_type

    # 2. Fallback: dò nội dung
    sample = " ".join(paragraphs_text[:20]).lower()
    for keyword, doc_type in _DOC_TYPE_PATTERNS:
        if keyword in sample:
            return doc_type
    return "unknown"


# ═════════════════════════════════════════════════════════════════════
# FONT NAME NORMALIZATION
# ═════════════════════════════════════════════════════════════════════
_FONT_NORMALIZE_MAP = [
    (re.compile(r'times.?new.?roman|TimesNewRoman|TIMES', re.IGNORECASE), 'Times'),
    (re.compile(r'arial', re.IGNORECASE), 'Arial'),
    (re.compile(r'calibri', re.IGNORECASE), 'Calibri'),
    (re.compile(r'cambria', re.IGNORECASE), 'Cambria'),
]

def normalize_font_name(raw: Optional[str]) -> Optional[str]:
    """
    Normalize tên font PDF về dạng ngắn gọn.
    VD: 'TimesNewRomanPSMT' → 'Times'
        'ABCDEF+TimesNewRoman' → 'Times'
    """
    if not raw:
        return None
    # Bỏ subset prefix (6 ký tự + dấu '+')
    if '+' in raw:
        raw = raw.split('+', 1)[1]
    # Normalize theo map
    for pattern, normalized in _FONT_NORMALIZE_MAP:
        if pattern.search(raw):
            return normalized
    # Bỏ suffix (PSMT, PS-BoldMT, ...)
    raw = re.sub(r'(PS|MT|-Bold|-Italic).*$', '', raw, flags=re.IGNORECASE)
    return raw[:20] if raw else None


def is_bold_from_name(font_name: Optional[str]) -> bool:
    if not font_name:
        return False
    name_lower = font_name.lower()
    return 'bold' in name_lower or '-bd' in name_lower or 'heavy' in name_lower


def is_italic_from_name(font_name: Optional[str]) -> bool:
    if not font_name:
        return False
    name_lower = font_name.lower()
    return 'italic' in name_lower or 'oblique' in name_lower or '-it' in name_lower


# ═════════════════════════════════════════════════════════════════════
# HELPER: Phát hiện OCR noise
# ═════════════════════════════════════════════════════════════════════

def _is_ocr_noise(text: str) -> bool:
    """
    Phát hiện đoạn văn bị OCR lỗi nặng.

    Tiêu chí kết hợp:
    1. Tỉ lệ ký tự Unicode ngoài khối Latin/tiếng Việt > 15%
    2. Ký tự { } xuất hiện trong văn bản hành chính (không bao giờ hợp lệ)
    3. Tổng ký tự < > { } | chiếm > 5% (OCR artifact điển hình)

    VD noise: 'XAc TH1/C VAN BAN H<}P NHAT', 'QU6C H<}I'
    """
    text = text.strip()
    if not text or len(text) < 5:
        return False

    n = len(text)

    # Tiêu chí 1: non-Vietnamese Unicode
    non_vi = sum(
        1 for ch in text
        if ord(ch) > 127 and not (
            0x00C0 <= ord(ch) <= 0x024F or
            0x1E00 <= ord(ch) <= 0x1EFF or
            0x0300 <= ord(ch) <= 0x036F
        )
    )
    if non_vi / n > 0.15:
        return True

    # Tiêu chí 2: dấu ngoặc nhọn { } — không bao giờ xuất hiện trong văn bản hành chính
    brace_count = text.count('{') + text.count('}')
    if brace_count > 0 and brace_count / n > 0.03:
        return True

    # Tiêu chí 3: tổ hợp ký tự OCR artifact chiếm > 5%
    bracket_count = sum(1 for ch in text if ch in '<>{|}')
    if bracket_count / n > 0.05:
        return True

    return False


# ═════════════════════════════════════════════════════════════════════
# HELPER: Kiểm tra PDF dạng text
# ═════════════════════════════════════════════════════════════════════
def _is_text_pdf(doc: fitz.Document, sample_pages: int = 3) -> bool:
    total = min(sample_pages, len(doc))
    for i in range(total):
        text = doc[i].get_text().strip()
        if len(text) > 50:
            return True
    return False


# ═════════════════════════════════════════════════════════════════════
# HELPER: Tính margins
# ═════════════════════════════════════════════════════════════════════
def _extract_margins(page: fitz.Page) -> Optional[Dict[str, float]]:
    media  = page.mediabox
    page_w = media.width
    page_h = media.height
    
    blocks = page.get_text("blocks")
    text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
    
    if not text_blocks:
        return None
    
    min_x = min(b[0] for b in text_blocks)
    min_y = min(b[1] for b in text_blocks)
    max_x = max(b[2] for b in text_blocks)
    max_y = max(b[3] for b in text_blocks)
    
    # Lọc rác: chỉ lưu nếu > 0
    result = {}
    left_cm = pt_to_cm(min_x)
    right_cm = pt_to_cm(page_w - max_x)
    top_cm = pt_to_cm(min_y)
    bottom_cm = pt_to_cm(page_h - max_y)
    width_cm = pt_to_cm(page_w)
    height_cm = pt_to_cm(page_h)
    
    if left_cm:
        result['left_cm'] = left_cm
    if right_cm:
        result['right_cm'] = right_cm
    if top_cm:
        result['top_cm'] = top_cm
    if bottom_cm:
        result['bottom_cm'] = bottom_cm
    if width_cm:
        result['width_cm'] = width_cm
    if height_cm:
        result['height_cm'] = height_cm
    
    return result if result else None


# ═════════════════════════════════════════════════════════════════════
# HELPER: Phát hiện số trang
# ═════════════════════════════════════════════════════════════════════
def _extract_page_number_info(doc: fitz.Document,
                               page_left_pt: float,
                               page_right_pt: float) -> Optional[Dict[str, Any]]:
    """
    Phát hiện số trang trong PDF.
    Chỉ trả về dict nếu tìm thấy, None nếu không có.
    """
    found         = False
    font_size_pt  = None
    alignment_str = None
    position_str  = None
    found_on_p1   = False
    found_on_p2   = False
    
    page_center = (page_left_pt + page_right_pt) / 2
    tolerance   = 10.0
    
    def _check_page(page: fitz.Page, page_idx: int):
        nonlocal found, font_size_pt, alignment_str, position_str, found_on_p1, found_on_p2
        
        page_h = page.mediabox.height
        header_zone = page_h * 0.12
        footer_zone = page_h * 0.88
        
        raw = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        for block in raw.get("blocks", []):
            if block.get("type") != 0:
                continue
            text = ''.join(
                span.get("text", "")
                for line in block.get("lines", [])
                for span in line.get("spans", [])
            ).strip()
            
            if not re.match(r'^\d{1,3}$', text):
                continue
            
            bbox = block["bbox"]
            y_center = (bbox[1] + bbox[3]) / 2
            x_center = (bbox[0] + bbox[2]) / 2
            
            in_header = y_center < header_zone
            in_footer = y_center > footer_zone
            if not (in_header or in_footer):
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    sz = span.get("size", 0)
                    if sz:
                        font_size_pt = round(sz, 1)
                    break
                break
            
            is_center = abs(x_center - page_center) < tolerance
            alignment_str = 'CENTER' if is_center else ('LEFT' if bbox[0] < page_center else 'RIGHT')
            position_str  = 'HEADER' if in_header else 'FOOTER'
            
            found = True
            if page_idx == 0:
                found_on_p1 = True
            elif page_idx == 1:
                found_on_p2 = True
    
    total = min(3, len(doc))
    for i in range(total):
        _check_page(doc[i], i)
    
    if not found:
        return None
    
    result = {}
    if font_size_pt:
        result['size_pt'] = font_size_pt
    if alignment_str:
        result['align'] = alignment_str
    if position_str:
        result['pos'] = position_str
    if (not found_on_p1) and found_on_p2:
        result['hidden_p1'] = True
    
    return result if result else None


# ═════════════════════════════════════════════════════════════════════
# HELPER: Phát hiện đường kẻ ngang
# ═════════════════════════════════════════════════════════════════════
def _extract_horizontal_rules(page: fitz.Page, page_num: int,
                               min_length_pt: float = 50.0) -> List[Dict[str, Any]]:
    """
    Phát hiện đường kẻ ngang từ vector drawings.
    Trả về list rút gọn (chỉ giữ thông tin cần thiết).
    """
    rules = []
    drawings = page.get_drawings()
    
    for d in drawings:
        rect = d.get("rect")
        if rect is None:
            continue
        x0, y0, x1, y1 = rect
        height = abs(y1 - y0)
        width  = abs(x1 - x0)
        
        if height > 3.0 or width < min_length_pt:
            continue
        
        # Tìm text gần nhất phía trên
        nearby_text = None
        search_rect = fitz.Rect(x0 - 10, y0 - 30, x1 + 10, y0)
        nearby_blocks = page.get_text("blocks", clip=search_rect)
        if nearby_blocks:
            nearest = max(nearby_blocks, key=lambda b: b[3])
            nearby_text = nearest[4].strip()[:40]
        
        rule = {
            'page': page_num,
            'y_pt': round((y0 + y1) / 2, 1),
        }
        if nearby_text:
            rule['near'] = nearby_text
        
        rules.append(rule)
    
    return rules


# ═════════════════════════════════════════════════════════════════════
# HELPER: Alignment & Spatial Position
# ═════════════════════════════════════════════════════════════════════
def _calc_alignment(x0: float, x1: float,
                    page_left: float, page_right: float,
                    tolerance: float = 8.0) -> Optional[str]:
    text_width    = x1 - x0
    content_width = page_right - page_left
    left_gap      = x0 - page_left
    right_gap     = page_right - x1
    
    if abs(left_gap - right_gap) < tolerance:
        return 'CENTER'
    if text_width >= content_width * 0.85:
        return 'JUSTIFY'
    if right_gap < tolerance:
        return 'RIGHT'
    # LEFT là mặc định, không cần trả về
    return None


def _calc_spatial_position(x0: float, x1: float,
                            page_left: float, page_right: float) -> Optional[str]:
    """
    Phân loại vị trí không gian.
    None = FULL_WIDTH (mặc định, không cần lưu)
    """
    page_center = (page_left + page_right) / 2
    block_center = (x0 + x1) / 2
    block_width  = x1 - x0
    content_width = page_right - page_left
    
    if block_width >= content_width * 0.7:
        return None  # FULL_WIDTH
    if block_center < page_center:
        return 'LEFT_COL'
    return 'RIGHT_COL'


# ═════════════════════════════════════════════════════════════════════
# HELPER: Font flags → bold/italic
# ═════════════════════════════════════════════════════════════════════
def _parse_font_flags(flags: int, font_name_raw: Optional[str]) -> tuple:
    italic = bool(flags & 2)  or is_italic_from_name(font_name_raw)
    bold   = bool(flags & 16) or is_bold_from_name(font_name_raw)
    return bold, italic


# ═════════════════════════════════════════════════════════════════════
# CORE: Gom cụm định dạng (Span-level Accumulation)
# ═════════════════════════════════════════════════════════════════════
@dataclass
class SpanInfo:
    """Cụm text có cùng định dạng (Font, Size, Bold, Italic)"""
    fmt: str
    txt: str


def _extract_spans_from_block(block: dict) -> List[SpanInfo]:
    """
    Gom các span có cùng định dạng thành cụm.
    
    QUAN TRỌNG: Thuật toán "Accumulation" - tránh tạo quá nhiều cụm nhỏ lẻ.
    """
    spans_data = []
    
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            text = span.get("text", "")
            if not text:
                continue
            
            # ── Font info ──────────────────────────────
            font_raw  = span.get("font", "")
            font_norm = normalize_font_name(font_raw)
            font_size = round(span.get("size", 0), 1) or None
            flags     = span.get("flags", 0)
            bold, italic = _parse_font_flags(flags, font_raw)
            
            # ── Tạo format string cô đặc ───────────────
            parts = []
            if font_norm:
                parts.append(font_norm)
            if font_size:
                parts.append(f"{int(font_size)}pt")
            if bold:
                parts.append("Bold")
            if italic:
                parts.append("Italic")
            
            fmt = "-".join(parts) if parts else "default"
            
            spans_data.append({'fmt': fmt, 'txt': text})
    
    # ── ACCUMULATION: Gom các span liền kề có cùng format ──
    if not spans_data:
        return []
    
    accumulated = []
    current = spans_data[0]
    
    for i in range(1, len(spans_data)):
        if spans_data[i]['fmt'] == current['fmt']:
            # Cùng format → gom vào cụm hiện tại
            current['txt'] += spans_data[i]['txt']
        else:
            # Khác format → lưu cụm cũ, bắt đầu cụm mới
            accumulated.append(SpanInfo(fmt=current['fmt'], txt=current['txt']))
            current = spans_data[i]
    
    # Lưu cụm cuối cùng
    accumulated.append(SpanInfo(fmt=current['fmt'], txt=current['txt']))
    
    return accumulated


# ═════════════════════════════════════════════════════════════════════
# HELPER: First-line indent
# ═════════════════════════════════════════════════════════════════════
def _calc_first_line_indent(lines: list, page_left_pt: float) -> Optional[float]:
    if len(lines) < 2:
        return None
    
    x0_first = lines[0]["bbox"][0]
    x0_rest  = [l["bbox"][0] for l in lines[1:]]
    if not x0_rest:
        return None
    
    avg_rest = sum(x0_rest) / len(x0_rest)
    diff     = x0_first - avg_rest
    
    if diff > 3.0:
        return pt_to_cm(diff)
    return None


# ═════════════════════════════════════════════════════════════════════
# HELPER: Line spacing ratio
# ═════════════════════════════════════════════════════════════════════
def _calc_line_spacing(lines: list, font_size: Optional[float]) -> Optional[float]:
    if len(lines) < 2 or not font_size or font_size == 0:
        return None
    
    y_gaps = []
    for i in range(1, len(lines)):
        y0_prev = lines[i-1]["bbox"][1]
        y0_curr = lines[i]["bbox"][1]
        gap = abs(y0_curr - y0_prev)
        if gap > 0:
            y_gaps.append(gap)
    
    if not y_gaps:
        return None
    
    avg_gap = sum(y_gaps) / len(y_gaps)
    ratio   = round(avg_gap / font_size, 2)
    
    # Chỉ trả về nếu khác 1.0 (single spacing là mặc định)
    return ratio if ratio != 1.0 else None


# ═════════════════════════════════════════════════════════════════════
# CORE: Bóc tách paragraphs từ 1 trang
# ═════════════════════════════════════════════════════════════════════
def _extract_paragraphs_from_page(page: fitz.Page,
                                   start_idx: int,
                                   page_left_pt: float,
                                   page_right_pt: float,
                                   page_num: int,
                                   prev_block_y1: float = 0.0) -> tuple:
    """
    Trả về (list[dict], last_block_y1)
    """
    paragraphs = []
    idx = start_idx
    last_y1 = prev_block_y1
    
    raw    = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    blocks = raw.get("blocks", [])
    
    for block_idx, block in enumerate(blocks):
        if block.get("type") != 0:
            continue
        
        lines = block.get("lines", [])
        if not lines:
            continue
        
        block_x0 = block["bbox"][0]
        block_y0 = block["bbox"][1]
        block_x1 = block["bbox"][2]
        block_y1 = block["bbox"][3]
        
        # ── Gom toàn bộ text ───────────────────────────────────────────
        full_text = ""
        for line in lines:
            for span in line.get("spans", []):
                full_text += span.get("text", "")
        
        if not full_text.strip():
            last_y1 = block_y1
            continue
        
        # ══════════════════════════════════════════════════════════════
        # BLOCK LEVEL: Thuộc tính của cả đoạn văn
        # ══════════════════════════════════════════════════════════════
        block_data = {}
        
        # ── Y position (pt) - quan trọng cho phân tích không gian ─────
        block_data['y_pt'] = round(block_y0, 1)
        
        # ── Space before (khoảng cách từ block trước) ──────────────────
        if last_y1 > 0:
            space_before_pt = round(block_y0 - last_y1, 1)
            if space_before_pt > 0:
                block_data['space_before_pt'] = space_before_pt
        
        # ── Font info từ span đầu tiên ────────────────────────────────
        font_size = None
        for line in lines:
            for span in line.get("spans", []):
                font_size = round(span.get("size", 0), 1) or None
                if font_size:
                    break
            if font_size:
                break
        
        # ── Line spacing ───────────────────────────────────────────────
        line_spacing = _calc_line_spacing(lines, font_size)
        if line_spacing:
            block_data['line_spacing'] = line_spacing
        
        # ── Alignment ──────────────────────────────────────────────────
        alignment = _calc_alignment(block_x0, block_x1, page_left_pt, page_right_pt)
        if alignment:
            block_data['align'] = alignment
        
        # ── First-line indent ──────────────────────────────────────────
        first_line_indent_cm = _calc_first_line_indent(lines, page_left_pt)
        if first_line_indent_cm:
            block_data['indent_cm'] = first_line_indent_cm
        
        # ══════════════════════════════════════════════════════════════
        # SPANS LEVEL: Các cụm text có cùng định dạng
        # ══════════════════════════════════════════════════════════════
        spans = _extract_spans_from_block(block)
        
        # Nếu chỉ có 1 span duy nhất và format = "default" → bỏ spans
        spans_output = None
        if len(spans) == 1 and spans[0].fmt == "default":
            spans_output = None
        elif len(spans) > 0:
            spans_output = [{'fmt': s.fmt, 'txt': s.txt} for s in spans]
        
        # ══════════════════════════════════════════════════════════════
        # SPATIAL ZONE: LEFT_COL / RIGHT_COL / None (FULL_WIDTH)
        # ══════════════════════════════════════════════════════════════
        zone = _calc_spatial_position(block_x0, block_x1, page_left_pt, page_right_pt)
        
        # ══════════════════════════════════════════════════════════════
        # FINAL OUTPUT: Lọc rác - chỉ giữ thông tin có giá trị
        # ══════════════════════════════════════════════════════════════
        result = {
            'idx': idx,
            'text': full_text.strip(),
        }

        # Đánh dấu OCR noise để Tầng 2 bỏ qua kiểm tra
        if _is_ocr_noise(full_text):
            result['ocr_noise'] = True
        
        if block_data:
            result['block'] = block_data
        if spans_output:
            result['spans'] = spans_output
        if zone:
            result['zone'] = zone
        if page_num > 0:  # Chỉ lưu page nếu không phải trang đầu
            result['page'] = page_num
        
        paragraphs.append(result)
        idx += 1
        last_y1 = block_y1
    
    return paragraphs, last_y1


# ═════════════════════════════════════════════════════════════════════
# HELPER: Gắn đường kẻ vào paragraph
# ═════════════════════════════════════════════════════════════════════
def _match_borders_to_paragraphs(paragraphs: list, rules: list, tolerance_pt: float = 15.0):
    """
    Tìm paragraph nằm ngay phía trên đường kẻ và gắn border vào block.
    """
    for rule in rules:
        best = None
        best_dist = float('inf')
        
        for para in paragraphs:
            # Kiểm tra cùng trang
            para_page = para.get('page', 0)
            if para_page != rule['page']:
                continue
            
            # Lấy y1 của block
            block_data = para.get('block', {})
            if 'y_pt' not in block_data:
                continue
            
            # Ước tính y1 (dùng y_pt, giả sử chiều cao ~20pt)
            para_y0 = block_data['y_pt']
            para_y1 = para_y0 + 20  # Ước tính
            
            dist = rule['y_pt'] - para_y1
            if 0 <= dist <= tolerance_pt and dist < best_dist:
                best_dist = dist
                best = para
        
        if best is not None:
            if 'block' not in best:
                best['block'] = {}
            best['block']['border'] = True


# ═════════════════════════════════════════════════════════════════════
# HELPER: Cắt vùng chữ ký / dấu mộc cuối văn bản
# ═════════════════════════════════════════════════════════════════════

# Pattern nhận dạng ranh giới vùng ký — xuất hiện trong văn bản hành chính VN
_SIGNATURE_PATTERNS = re.compile(
    r"TM\.\s*ỦY\s*BAN|TM\.\s*BỘ\s*TRƯỞNG|TM\.\s*CHÍNH\s*PHỦ"
    r"|KT\.\s*CHỦ\s*TỊCH|KT\.\s*BỘ\s*TRƯỞNG|KT\.\s*THỦ\s*TƯỚNG"
    r"|THỪA\s*ỦY\s*QUYỀN|THỪA\s*LỆNH"
    r"|TM\.\s*BAN\s*CHẤP\s*HÀNH|TM\.\s*HỘI\s*ĐỒNG"
    r"|CHỦ\s*TỊCH\s*UBND|CHỦ\s*TỊCH\s*HỘI\s*ĐỒNG",
    re.IGNORECASE | re.UNICODE,
)

_TINY_FONT_MAX_PT = 8.0   # font < 8pt → mã nội bộ, không phải nội dung


def _drop_signature_zone(paragraphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Loại bỏ vùng chữ ký / dấu mộc / mã nội bộ cuối văn bản.

    Chiến lược kết hợp:
    1. Font < 8pt → drop ngay (mã nội bộ kiểu TC_VP7_TCBM_xxx)
    2. Khi gặp paragraph RIGHT_COL khớp _SIGNATURE_PATTERNS
       → đánh dấu cut_page + cut_y, drop tất cả paragraph cùng trang
       có y_pt >= cut_y VÀ zone == RIGHT_COL (tên người ký, chức danh)
    3. Paragraph LEFT_COL thuộc vùng "Nơi nhận" không bị drop
       (vẫn cần kiểm tra thể thức)
    """
    # Bước 1: lọc font nhỏ (mã nội bộ)
    result = []
    for p in paragraphs:
        spans = p.get('spans', [])
        if spans:
            # Lấy size pt từ fmt string, VD "Times-5pt" → 5
            sizes = []
            for sp in spans:
                m = re.search(r'-(\d+(?:\.\d+)?)pt', sp.get('fmt', ''))
                if m:
                    sizes.append(float(m.group(1)))
            if sizes and max(sizes) < _TINY_FONT_MAX_PT:
                continue   # drop: font quá nhỏ
        result.append(p)

    # Bước 2: tìm ranh giới vùng ký theo trang
    # cut_map: {page_num: cut_y_pt}
    cut_map: Dict[int, float] = {}
    for p in result:
        text     = p.get('text', '')
        zone     = p.get('zone', 'FULL_WIDTH')
        page_num = p.get('page', 0)
        y_pt     = p.get('block', {}).get('y_pt', 0)

        if zone == 'RIGHT_COL' and _SIGNATURE_PATTERNS.search(text):
            # Chỉ cập nhật nếu chưa có hoặc y nhỏ hơn (lấy ranh giới cao nhất)
            if page_num not in cut_map or y_pt < cut_map[page_num]:
                cut_map[page_num] = y_pt

    if not cut_map:
        return result   # Không tìm thấy vùng ký → giữ nguyên

    # Bước 3: drop các paragraph RIGHT_COL nằm trong vùng ký
    filtered = []
    for p in result:
        page_num = p.get('page', 0)
        zone     = p.get('zone', 'FULL_WIDTH')
        y_pt     = p.get('block', {}).get('y_pt', 0)

        if page_num in cut_map and zone == 'RIGHT_COL' and y_pt >= cut_map[page_num]:
            continue   # drop: nằm trong vùng ký bên phải
        filtered.append(p)

    return filtered


# ═════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════
def extract_pdf_optimized(pdf_path: str, max_pages: int = None) -> Dict[str, Any]:
    """
    Bóc tách cấu trúc vật lý tối ưu cho LLM.
    
    Parameters
    ----------
    pdf_path  : str  — đường dẫn tới file .pdf
    max_pages : int  — giới hạn số trang xử lý (None = toàn bộ)
    
    Returns
    -------
    dict — Cấu trúc cô đặc (Block + Spans), đã lọc rác
    
    Raises
    ------
    ValueError — Nếu file là PDF scan
    """
    path = Path(pdf_path)
    doc  = fitz.open(str(path))
    
    # ── Từ chối PDF scan ───────────────────────────────────────────────
    if not _is_text_pdf(doc):
        doc.close()
        raise ValueError(
            f"❌ '{path.name}' là PDF scan (không có text layer). "
            "Hệ thống chỉ xử lý PDF dạng text."
        )
    
    # ── Margins + Page size ────────────────────────────────────────────
    first_page = doc[0]
    media      = first_page.mediabox
    margins_raw = _extract_margins(first_page)

    # Tách page_size ra field riêng, KHÔNG lẫn vào margins
    page_size: Dict[str, float] = {}
    margins:   Dict[str, float] = {}
    if margins_raw:
        for k in ('left_cm', 'right_cm', 'top_cm', 'bottom_cm'):
            if k in margins_raw:
                margins[k] = margins_raw[k]
        if 'width_cm'  in margins_raw: page_size['width_cm']  = margins_raw['width_cm']
        if 'height_cm' in margins_raw: page_size['height_cm'] = margins_raw['height_cm']

    # Fallback: tính từ mediabox khi _extract_margins không trả về
    if 'width_cm' not in page_size:
        page_size['width_cm']  = round(media.width  / PT_PER_CM, 2)
    if 'height_cm' not in page_size:
        page_size['height_cm'] = round(media.height / PT_PER_CM, 2)

    page_left_pt  = margins.get('left_cm',  0) * PT_PER_CM
    page_right_pt = media.width - margins.get('right_cm', 0) * PT_PER_CM

    # ── Số trang ───────────────────────────────────────────────────────
    page_number = _extract_page_number_info(doc, page_left_pt, page_right_pt)

    # ── Paragraphs + horizontal rules ──────────────────────────────────
    total_pages    = len(doc) if max_pages is None else min(max_pages, len(doc))
    all_paragraphs: List[Dict[str, Any]] = []
    all_rules:      List[Dict[str, Any]] = []
    last_y1        = 0.0

    for page_num in range(total_pages):
        page = doc[page_num]

        rules = _extract_horizontal_rules(page, page_num)
        all_rules.extend(rules)

        paras, last_y1 = _extract_paragraphs_from_page(
            page,
            start_idx=len(all_paragraphs),
            page_left_pt=page_left_pt,
            page_right_pt=page_right_pt,
            page_num=page_num,
            prev_block_y1=last_y1 if page_num == 0 else 0.0,
        )
        all_paragraphs.extend(paras)

    doc.close()

    # ── Gắn đường kẻ vào paragraph ─────────────────────────────────────
    if all_rules:
        _match_borders_to_paragraphs(all_paragraphs, all_rules)

    # ── GIỮ TOÀN BỘ: không cắt vùng chữ ký / nơi nhận ─────────────────
    # Tất cả thành phần đều cần kiểm tra thể thức theo NĐ30

    # ── Phát hiện loại văn bản ─────────────────────────────────────────
    para_texts = [p.get('text', '') for p in all_paragraphs]
    doc_type   = _detect_doc_type(para_texts, filename=path.name)

    # ── Final output ───────────────────────────────────────────────────
    result: Dict[str, Any] = {
        'filename': path.name,
        'source':   'pdf',      # Tầng 2 biết nguồn gốc file
        'doc_type': doc_type,   # VD: "nghi_dinh", "cong_van", "unknown"
    }

    if total_pages > 1:
        result['pages'] = total_pages
    if page_size:
        result['page_size'] = page_size   # {'width_cm': 21.0, 'height_cm': 29.7}
    if margins:
        result['margins']   = margins     # Chỉ còn lề (cm)
    if page_number:
        result['page_number'] = page_number
    if all_paragraphs:
        result['paragraphs']  = all_paragraphs
    if all_rules:
        result['rules'] = all_rules

    return result


def save_report(report: dict, output_path: str):
    """Lưu report ra file JSON (compact format)"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã lưu: {output_path}")


# ═════════════════════════════════════════════════════════════════════
# CLI RUNNER
# ═════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import sys
    
    input_dir  = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('data/groundtruth')
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('output')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = sorted(input_dir.glob('*.pdf'))
    if not pdf_files:
        print(f"⚠️  Không tìm thấy file .pdf trong: {input_dir}")
        sys.exit(1)
    
    print(f"🔍 Tìm thấy {len(pdf_files)} file .pdf\n")
    print(f"🎯 Chế độ: OPTIMIZED (Block + Spans, Drop Nulls)\n")
    
    all_reports = []
    
    for pdf_path in pdf_files:
        print(f"📄 Đang xử lý: {pdf_path.name}")
        try:
            report = extract_pdf_optimized(str(pdf_path))
            
            m  = report.get('margins', {})
            pn = report.get('page_number', {})
            print(f"   Trang: {report.get('pages', 1)}")
            print(f"   Lề: trái={m.get('left_cm')}cm | phải={m.get('right_cm')}cm")
            print(f"   Số trang: {pn if pn else 'không phát hiện'}")
            print(f"   Số đoạn văn: {len(report.get('paragraphs', []))}")
            print(f"   Đường kẻ: {len(report.get('rules', []))} rules")
            
            # In 3 đoạn đầu
            for p in report.get('paragraphs', [])[:3]:
                text_preview = p['text'][:40]
                block_info = p.get('block', {})
                spans_count = len(p.get('spans', []))
                zone_info = p.get('zone', 'FULL_WIDTH')
                print(f"   ↳ [{p['idx']}] '{text_preview}' | block={block_info} | spans={spans_count} | zone={zone_info}")
            
            out_file = output_dir / f"{pdf_path.stem}_optimized.json"
            save_report(report, str(out_file))
            all_reports.append(report)
            print()
            
        except ValueError as e:
            print(f"   {e}\n")
        except Exception as e:
            import traceback
            print(f"   ❌ Lỗi không mong đợi: {e}")
            traceback.print_exc()
            print()
    
    if all_reports:
        all_path = output_dir / '_all_optimized.json'
        with open(all_path, 'w', encoding='utf-8') as f:
            json.dump(all_reports, f, ensure_ascii=False, indent=2)
        print(f"\n📦 Tổng hợp toàn bộ: {all_path}")
        print(f"\n🚀 Token giảm ước tính: 70-85% so với bản cũ!")