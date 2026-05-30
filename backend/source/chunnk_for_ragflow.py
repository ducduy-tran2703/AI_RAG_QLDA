"""
chunk_for_ragflow.py  (v2 — simplified)
=========================================
Đọc file .txt (output của jsonl_to_text.py),
chia thành các chunk theo số ký tự (MAX_CHARS),
xuất ra ragflow_chunks/*_chunks.json.

Chiến lược chunk:
  - Gom từng đoạn [PARA_ID=N] theo thứ tự
  - Khi tổng ký tự vượt MAX_CHARS → cắt chunk, bắt đầu chunk mới
  - Không phân biệt region, không cần precheck

Cách chạy:
  python src/chunk_for_ragflow.py

Tự động quét output/*.txt
Xuất ra ragflow_chunks/*_chunks.json
"""

import json
import re
import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════
# CẤU HÌNH
# ══════════════════════════════════════════════════════════════════════

MAX_CHARS = 3000  # ~750 token tiếng Việt, phù hợp Qwen2.5 7B


# ══════════════════════════════════════════════════════════════════════
# HÀM PHỤ TRỢ
# ══════════════════════════════════════════════════════════════════════

def extract_header_block(txt_content: str) -> str:
    """Lấy phần metadata header (trước dòng '===...')."""
    lines = txt_content.splitlines()
    header_lines = []
    for line in lines:
        if line.startswith("=" * 10):
            break
        header_lines.append(line)
    return "\n".join(header_lines).strip()


def parse_paragraphs(txt_content: str) -> list[dict]:
    """
    Parse file txt thành danh sách đoạn.
    Mỗi đoạn: {"idx": int, "text": str}
    """
    paragraphs = []
    lines = txt_content.splitlines()

    # Bỏ qua phần header metadata (trước "NỘI DUNG VĂN BẢN")
    content_start = 0
    for i, line in enumerate(lines):
        if "NỘI DUNG VĂN BẢN" in line:
            content_start = i + 2
            break

    current_idx  = None
    current_lines: list[str] = []

    for line in lines[content_start:]:
        m = re.match(r"^\[PARA_ID=(\d+)", line)
        if m:
            if current_idx is not None:
                paragraphs.append({
                    "idx":  current_idx,
                    "text": "\n".join(current_lines),
                })
            current_idx   = int(m.group(1))
            current_lines = [line]
        elif current_idx is not None:
            current_lines.append(line)

    if current_idx is not None:
        paragraphs.append({
            "idx":  current_idx,
            "text": "\n".join(current_lines),
        })

    return paragraphs


# ══════════════════════════════════════════════════════════════════════
# HÀM META-CHUNK (chunk_000 đặc biệt)
# ══════════════════════════════════════════════════════════════════════

# Pattern nhận dạng thành phần bắt buộc
# Dấu gạch ngang: hỗ trợ hyphen (-), en-dash (–), em-dash (—)
_DASH = r"[\-\u2013\u2014]"
_RE_QUOC_HUU   = re.compile(r"CỘNG\s*HÒA\s*XÃ\s*HỘI\s*CHỦ\s*NGHĨA", re.IGNORECASE)
_RE_TIEU_NGU   = re.compile(
    r"Độc\s*lập\s*" + _DASH + r"\s*Tự\s*do\s*" + _DASH + r"\s*Hạnh\s*phúc",
    re.IGNORECASE
)
_RE_SO_KY_HIEU = re.compile(r"Số\s*:", re.IGNORECASE)
_RE_DIA_DANH   = re.compile(r"ngày\s+\S*\s*tháng\s+\S*\s*năm", re.IGNORECASE)

# Loại VB không có tên cơ quan ở LEFT_COL đầu trang
_DOC_TYPE_NO_CO_QUAN = {"vbhn", "luat"}
# Loại VB không có "Số: XX/YYYY/..." dạng chuẩn
_DOC_TYPE_NO_SO = {"vbhn", "luat"}

# Loại văn bản → tên tiêu đề cần tìm
_DOC_TYPE_VI = {
    "nghi_dinh":          "Nghị định",
    "thong_tu":           "Thông tư",
    "thong_tu_lien_tich": "Thông tư liên tịch",
    "quyet_dinh":         "Quyết định",
    "cong_van":           "Công văn",
    "luat":               "Luật",
    "vbhn":               "Văn bản hợp nhất",
    "nghi_quyet":         "Nghị quyết",
    "chi_thi":            "Chỉ thị",
    "to_trinh":           "Tờ trình",
    "bao_cao":            "Báo cáo",
    "ke_hoach":           "Kế hoạch",
    "thong_bao":          "Thông báo",
    "unknown":            "Chưa xác định",
}

# Loại văn bản → tên tiêu đề cần tìm trong nội dung
_DOC_TYPE_TITLE = {
    "thong_tu":           "THÔNG TƯ",
    "thong_tu_lien_tich": "THÔNG TƯ LIÊN TỊCH",
    "nghi_dinh":          "NGHỊ ĐỊNH",
    "quyet_dinh":         "QUYẾT ĐỊNH",
    "chi_thi":            "CHỈ THỊ",
    "nghi_quyet":         "NGHỊ QUYẾT",
    "cong_van":           "CÔNG VĂN",
    "luat":               "LUẬT",
    "vbhn":               "VĂN BẢN HỢP NHẤT",
}

# Pattern nhận dạng Chương / Mục / Điều / Khoản để dựng cây cấu trúc
_RE_CHUONG = re.compile(r"^Chương\s+([IVXLCDM]+|\d+)\b", re.IGNORECASE)
_RE_MUC    = re.compile(r"^Mục\s+(\d+)\b",                re.IGNORECASE)
_RE_DIEU   = re.compile(r"^Điều\s+(\d+)\b",               re.IGNORECASE)


def _roman_to_int(s: str) -> int:
    """Chuyển số La Mã đơn giản sang int (dùng cho Chương)."""
    val = {'I':1,'V':5,'X':10,'L':50,'C':100,'D':500,'M':1000}
    s = s.upper()
    result = 0
    for i, ch in enumerate(s):
        if ch not in val:
            return 0
        cur = val[ch]
        nxt = val[s[i+1]] if i+1 < len(s) else 0
        result += cur if cur >= nxt else -cur
    return result


def _to_int(s: str) -> int:
    """Chuyển số La Mã hoặc Ả Rập sang int."""
    try:
        return int(s)
    except ValueError:
        return _roman_to_int(s)


def build_meta_chunk(txt_content: str, json_data: dict, filename: str,
                     total_content_chunks: int) -> dict:
    """
    Tạo chunk_000 — chunk đặc biệt chứa:
      1. Thành phần bắt buộc (quốc hiệu, tiêu ngữ, tên loại VB, số ký hiệu...)
      2. Cây thứ tự cấu trúc (Chương → Điều với PARA_ID)
      3. Thông số trang (lề, khổ giấy, số trang)

    LLM dùng chunk này để kiểm tra toàn cục mà không cần đọc lại từng chunk.
    """
    paragraphs = json_data.get("paragraphs", [])
    doc_type   = json_data.get("doc_type", "unknown")

    # ── 1. Phát hiện thành phần bắt buộc ─────────────────────────────
    found: dict[str, str | None] = {
        "ten_co_quan":   None,
        "quoc_hieu":     None,
        "tieu_ngu":      None,
        "so_ky_hieu":    None,
        "dia_danh_ngay": None,
        "ten_loai_vb":   None,
        "trich_yeu":     None,
        "chu_ky":        "DA_CAT",  # đã cắt vùng ký → luôn tích ✅
    }

    title_keyword = _DOC_TYPE_TITLE.get(doc_type, "").upper()

    for p in paragraphs:
        idx  = p.get("idx", 0)
        text = p.get("text", "").strip()
        zone = p.get("zone", "FULL_WIDTH")

        if not text:
            continue

        ref = f"PARA_ID={idx}"

        # ten_co_quan: LEFT_COL đầu trang — không áp dụng cho VBHN/Luật
        if found["ten_co_quan"] is None:
            if doc_type in _DOC_TYPE_NO_CO_QUAN:
                found["ten_co_quan"] = "N/A"   # lấp liếm — loại VB này không có
            elif zone == "LEFT_COL" and idx < 5:
                found["ten_co_quan"] = ref

        if found["quoc_hieu"] is None and _RE_QUOC_HUU.search(text):
            found["quoc_hieu"] = ref

        if found["tieu_ngu"] is None and _RE_TIEU_NGU.search(text):
            found["tieu_ngu"] = ref

        # so_ky_hieu: VBHN/Luật không có "Số: XX/..." dạng chuẩn
        if found["so_ky_hieu"] is None:
            if doc_type in _DOC_TYPE_NO_SO:
                found["so_ky_hieu"] = "N/A"
            elif _RE_SO_KY_HIEU.search(text):
                found["so_ky_hieu"] = ref

        if found["dia_danh_ngay"] is None and _RE_DIA_DANH.search(text):
            found["dia_danh_ngay"] = ref

        if found["ten_loai_vb"] is None:
            if doc_type == "vbhn":
                # VBHN: có thể là "XÁC THỰC VĂN BẢN HỢP NHẤT" hoặc tên Luật/NĐ/TT
                # nằm đầu trang (idx < 10), không cần kiểm tra zone
                if idx < 10 and re.search(
                    r"(LUẬT|NGHỊ ĐỊNH|THÔNG TƯ|PHÁP LỆNH|XÁC THỰC|VĂN BẢN HỢP NHẤT)",
                    text.upper()
                ):
                    found["ten_loai_vb"] = ref
                    if found["trich_yeu"] is None:
                        nxt = [q for q in paragraphs if q.get("idx", 0) == idx + 1]
                        if nxt:
                            found["trich_yeu"] = f"PARA_ID={idx+1}"
            elif title_keyword and title_keyword in text.upper():
                found["ten_loai_vb"] = ref
                rest = text[text.upper().find(title_keyword) + len(title_keyword):].strip()
                if rest:
                    found["trich_yeu"] = ref
                elif found["trich_yeu"] is None:
                    next_paras = [q for q in paragraphs if q.get("idx", 0) == idx + 1]
                    if next_paras:
                        found["trich_yeu"] = f"PARA_ID={idx+1}"


    # ── 2. Dựng cây thứ tự cấu trúc ─────────────────────────────────
    struct_lines  = []
    warnings      = []

    prev_chuong = 0
    prev_dieu   = 0
    prev_muc    = 0
    has_chuong  = False

    for p in paragraphs:
        idx  = p.get("idx", 0)
        text = p.get("text", "").strip()

        mc = _RE_CHUONG.match(text)
        mm = _RE_MUC.match(text)
        md = _RE_DIEU.match(text)

        if mc:
            num = _to_int(mc.group(1))
            has_chuong = True
            label = f"Chương {mc.group(1)}"
            if num != prev_chuong + 1 and prev_chuong > 0:
                warnings.append(
                    f"⚠️  {label} (PARA_ID={idx}): nhảy từ Chương {prev_chuong} → {num}"
                )
            struct_lines.append(f"  {label:<12} → PARA_ID={idx}")
            prev_chuong = num
            prev_dieu   = 0
            prev_muc    = 0

        elif mm:
            num   = _to_int(mm.group(1))
            label = f"Mục {mm.group(1)}"
            if num != prev_muc + 1 and prev_muc > 0:
                warnings.append(
                    f"⚠️  {label} (PARA_ID={idx}): nhảy từ Mục {prev_muc} → {num}"
                )
            struct_lines.append(f"    {label:<10} → PARA_ID={idx}")
            prev_muc  = num
            prev_dieu = 0

        elif md:
            num   = _to_int(md.group(1))
            label = f"Điều {md.group(1)}"
            if num != prev_dieu + 1:
                if prev_dieu > 0:
                    warnings.append(
                        f"⚠️  {label} (PARA_ID={idx}): nhảy từ Điều {prev_dieu} → {num}"
                    )
                elif has_chuong:
                    # Điều đầu tiên của chương mới — bình thường nếu tiếp nối
                    pass
            struct_lines.append(f"    {label:<10} → PARA_ID={idx}")
            prev_dieu = num

    # ── 3. Thông số trang ─────────────────────────────────────────────
    ps  = json_data.get("page_size", {})
    mg  = json_data.get("margins",   {})
    pn  = json_data.get("page_number", {})

    page_lines = []
    if ps:
        page_lines.append(f"Khổ giấy : {ps.get('width_cm')}cm x {ps.get('height_cm')}cm")
    if mg:
        parts = []
        if "top_cm"    in mg: parts.append(f"Trên {mg['top_cm']}cm")
        if "bottom_cm" in mg: parts.append(f"Dưới {mg['bottom_cm']}cm")
        if "left_cm"   in mg: parts.append(f"Trái {mg['left_cm']}cm")
        if "right_cm"  in mg: parts.append(f"Phải {mg['right_cm']}cm")
        page_lines.append(f"Lề       : {' | '.join(parts)}")
    if pn:
        pn_parts = []
        if "size_pt" in pn: pn_parts.append(f"{pn['size_pt']}pt")
        if "align"   in pn: pn_parts.append(f"Căn {pn['align']}")
        if "pos"     in pn: pn_parts.append(f"Vị trí {pn['pos']}")
        if pn.get("hidden_p1"): pn_parts.append("Ẩn trang đầu")
        page_lines.append(f"Số trang : {' | '.join(pn_parts)}")
    page_lines.append(f"Tổng chunk nội dung: {total_content_chunks}")

    # ── Ghép nội dung meta-chunk ──────────────────────────────────────
    sep  = "━" * 34
    lines = [
        f"📄 TÀI LIỆU: {filename}",
        f"📎 NGUỒN: {json_data.get('source','').upper()} | LOẠI VĂN BẢN: {_DOC_TYPE_VI.get(doc_type, doc_type)}",
        "",
        sep,
        "PHẦN 1 — THÀNH PHẦN BẮT BUỘC",
        sep,
    ]

    component_labels = {
        "ten_co_quan":   "ten_co_quan  ",
        "quoc_hieu":     "quoc_hieu    ",
        "tieu_ngu":      "tieu_ngu     ",
        "so_ky_hieu":    "so_ky_hieu   ",
        "dia_danh_ngay": "dia_danh_ngay",
        "ten_loai_vb":   "ten_loai_vb  ",
        "trich_yeu":     "trich_yeu    ",
        "chu_ky":        "chu_ky       ",
    }
    for key, label in component_labels.items():
        val = found[key]
        if val is None:
            mark, ref = "❌", "→ THIẾU"
        elif val in ("N/A", "DA_CAT"):
            mark, ref = "✅", ""
        else:
            mark, ref = "✅", f"→ {val}"
        lines.append(f"{mark} {label} {ref}".rstrip())

    lines += ["", sep, "PHẦN 2 — THỨ TỰ CẤU TRÚC", sep]
    if struct_lines:
        lines.extend(struct_lines)
    else:
        lines.append("  (Không phát hiện Chương/Điều — văn bản không có cấu trúc phân cấp)")
    if warnings:
        lines.append("")
        lines.extend(warnings)

    lines += ["", sep, "PHẦN 3 — THÔNG SỐ TRANG", sep]
    lines.extend(page_lines)

    content = "\n".join(lines)

    return {
        "meta": {
            "chunk_id":  "chunk_000",
            "filename":  filename,
            "para_idxs": [],
            "order":     0,
            "type":      "meta",
        },
        "content": content,
    }



def build_chunks(txt_content: str, filename: str) -> list[dict]:
    """
    Chia txt thành các chunk theo MAX_CHARS.

    Mỗi chunk:
    {
        "meta": {
            "chunk_id":  str,   # "chunk_001", "chunk_002", ...
            "filename":  str,
            "para_idxs": [int], # các PARA_ID nằm trong chunk này
            "order":     int,   # thứ tự chunk (bắt đầu từ 1)
        },
        "content": str
    }
    """
    header_block = extract_header_block(txt_content)
    paragraphs   = parse_paragraphs(txt_content)

    chunks     = []
    chunk_idx  = 1
    buf_paras: list[dict] = []
    buf_chars  = 0

    def flush(buf: list[dict], idx: int, include_header: bool) -> dict:
        content = "\n".join(p["text"] for p in buf)
        if include_header:
            content = header_block + "\n\n" + content
        return {
            "meta": {
                "chunk_id":  f"chunk_{idx:03d}",
                "filename":  filename,
                "para_idxs": [p["idx"] for p in buf],
                "order":     idx,
            },
            "content": content,
        }

    for para in paragraphs:
        para_len = len(para["text"])

        # Nếu thêm đoạn này sẽ vượt MAX_CHARS → flush chunk hiện tại trước
        if buf_paras and buf_chars + para_len > MAX_CHARS:
            chunks.append(flush(buf_paras, chunk_idx, include_header=(chunk_idx == 1)))
            chunk_idx += 1
            buf_paras  = []
            buf_chars  = 0

        buf_paras.append(para)
        buf_chars += para_len

    # Flush phần còn lại
    if buf_paras:
        chunks.append(flush(buf_paras, chunk_idx, include_header=(chunk_idx == 1)))

    return chunks


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    output_dir   = Path("output")
    ragflow_dir  = Path("ragflow_chunks")
    ragflow_dir.mkdir(exist_ok=True)

    if not output_dir.exists():
        print(f"⚠️  Không tìm thấy thư mục '{output_dir}'")
        sys.exit(1)

    txt_files = sorted(output_dir.glob("*.txt"))
    if not txt_files:
        print(f"⚠️  Không tìm thấy file .txt trong '{output_dir}'")
        sys.exit(1)

    print(f"🔍 Tìm thấy {len(txt_files)} file TXT\n")

    for txt_path in txt_files:
        print(f"🔄 Đang xử lý: {txt_path.name}")
        try:
            with open(txt_path, encoding="utf-8") as f:
                txt_content = f.read()

            # Lấy filename gốc từ dòng đầu txt nếu có, fallback về tên file
            filename = txt_path.stem
            first_line = txt_content.splitlines()[0] if txt_content else ""
            m = re.search(r"TÀI LIỆU:\s*(.+)", first_line)
            if m:
                filename = m.group(1).strip()

            # ── Chunks nội dung ──────────────────────────────────────
            content_chunks = build_chunks(txt_content, filename)

            # ── Meta-chunk (chunk_000) ───────────────────────────────
            # Tìm file JSON gốc tương ứng để lấy structured data
            json_path = output_dir / f"{txt_path.stem}.json"
            meta_chunk = None
            if json_path.exists():
                with open(json_path, encoding="utf-8") as jf:
                    json_data = json.load(jf)
                meta_chunk = build_meta_chunk(
                    txt_content, json_data, filename,
                    total_content_chunks=len(content_chunks),
                )
            else:
                print(f"   ⚠️  Không tìm thấy JSON gốc ({json_path.name}), bỏ qua meta-chunk")

            # ── Ghép: meta_chunk đứng đầu, content_chunks theo sau ──
            all_chunks = ([meta_chunk] if meta_chunk else []) + content_chunks

            out = {
                "filename":     filename,
                "total_chunks": len(all_chunks),
                "max_chars":    MAX_CHARS,
                "chunks":       all_chunks,
            }

            out_path = ragflow_dir / f"{txt_path.stem}_chunks.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

            print(f"   ✅ {len(all_chunks)} chunks (1 meta + {len(content_chunks)} nội dung) → {out_path.name}")
            for c in all_chunks:
                m2 = c["meta"]
                ctype = m2.get("type", "content")
                if ctype == "meta":
                    print(f"      [{m2['chunk_id']}] META | {len(c['content'])} ký tự")
                else:
                    idxs = m2.get("para_idxs", [])
                    rng  = f"đoạn {idxs[0]}–{idxs[-1]}" if idxs else "?"
                    print(f"      [{m2['chunk_id']}] {len(c['content'])} ký tự | {rng}")
            print()

        except Exception as e:
            import traceback
            print(f"   ❌ Lỗi: {e}")
            traceback.print_exc()
            print()

    print("🎉 HOÀN TẤT! Chunks đã lưu trong thư mục 'ragflow_chunks/'")
    print()
    print("📌 Bước tiếp theo:")
    print("   python src/send_to_ragflow.py")