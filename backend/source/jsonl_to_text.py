"""
jsonl_to_text.py  (v3 — simplified)
=====================================
Chuyển đổi JSON vật lý sang Plain Text cho LLM.
Bỏ hoàn toàn precheck và nhãn thành phần.

Cách chạy (từ thư mục gốc project):
  python src/jsonl_to_text.py

Tự động quét output/*.json
Xuất ra output/*.txt (ghi đè file txt cũ)
"""

import json
import sys
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════
# BẢNG DỊCH
# ══════════════════════════════════════════════════════════════════════

ZONE_VI = {
    "LEFT_COL":   "Cột trái",
    "RIGHT_COL":  "Cột phải",
    "FULL_WIDTH": "Toàn trang",
}

ALIGN_VI = {
    "LEFT":    "Căn trái",
    "RIGHT":   "Căn phải",
    "CENTER":  "Căn giữa",
    "JUSTIFY": "Căn đều 2 lề",
}

DOC_TYPE_VI = {
    "nghi_dinh":          "Nghị định",
    "thong_tu":           "Thông tư",
    "thong_tu_lien_tich": "Thông tư liên tịch",
    "quyet_dinh":         "Quyết định",
    "cong_van":           "Công văn",
    "luat":               "Luật",
    "vbhn":               "Văn bản hợp nhất",
    "nghi_quyet":         "Nghị quyết",
    "chi_thi":            "Chỉ thị",
    "unknown":            "Chưa xác định",
}


# ══════════════════════════════════════════════════════════════════════
# HÀM CHÍNH
# ══════════════════════════════════════════════════════════════════════

def build_llm_text(json_data: dict) -> str:
    """
    Chuyển JSON vật lý sang plain text có định dạng rõ ràng cho LLM.
    Không dùng precheck, không gắn nhãn thành phần.
    """
    lines = []

    filename    = json_data.get("filename", "Không rõ")
    source      = json_data.get("source",   "unknown").upper()
    doc_type    = json_data.get("doc_type", "unknown")
    doc_type_vi = DOC_TYPE_VI.get(doc_type, doc_type)

    # ── Thông tin tài liệu ───────────────────────────────────────────
    lines.append(f"📄 TÀI LIỆU: {filename}")
    lines.append(f"📎 NGUỒN: {source} | LOẠI VĂN BẢN: {doc_type_vi}")

    ps = json_data.get("page_size", {})
    if ps:
        parts = []
        if "width_cm"  in ps: parts.append(f"Rộng {ps['width_cm']}cm")
        if "height_cm" in ps: parts.append(f"Cao {ps['height_cm']}cm")
        lines.append(f"📐 KHỔ GIẤY: {', '.join(parts)}")

    m = json_data.get("margins", {})
    if m:
        parts = []
        if "top_cm"    in m: parts.append(f"Trên {m['top_cm']}cm")
        if "bottom_cm" in m: parts.append(f"Dưới {m['bottom_cm']}cm")
        if "left_cm"   in m: parts.append(f"Trái {m['left_cm']}cm")
        if "right_cm"  in m: parts.append(f"Phải {m['right_cm']}cm")
        lines.append(f"📌 LỀ TRANG: {', '.join(parts)}")

    pn = json_data.get("page_number", {})
    if pn:
        parts = []
        if "size_pt" in pn: parts.append(f"Cỡ {pn['size_pt']}pt")
        if "align"   in pn: parts.append(f"Canh {pn['align']}")
        if "pos"     in pn: parts.append(f"Vị trí {pn['pos']}")
        if pn.get("hidden_p1"): parts.append("Ẩn số trang đầu")
        lines.append(f"📌 SỐ TRANG: {' | '.join(parts)}")

    lines.append("\n" + "=" * 50)
    lines.append("NỘI DUNG VĂN BẢN")
    lines.append("=" * 50)

    # ── Từng đoạn ────────────────────────────────────────────────────
    paragraphs = json_data.get("paragraphs", [])
    for p in paragraphs:
        idx       = p.get("idx", 0)
        zone      = p.get("zone", "FULL_WIDTH")
        block     = p.get("block", {})
        fragments = p.get("runs", []) or p.get("spans", [])

        # Header đoạn
        header_parts = [f"PARA_ID={idx}"]

        zone_vi = ZONE_VI.get(zone, "")
        if zone_vi and zone != "FULL_WIDTH":
            header_parts.append(f"Vị trí: {zone_vi}")

        align_vi = ALIGN_VI.get(block.get("align", ""), "")
        if align_vi:
            header_parts.append(f"Căn lề: {align_vi}")

        if "indent_cm" in block:
            header_parts.append(f"Lùi đầu dòng: {block['indent_cm']}cm")

        if "line_spacing" in block:
            header_parts.append(f"Cách dòng: {block['line_spacing']}")

        if "space_before_pt" in block:
            header_parts.append(f"Cách đoạn trước: {block['space_before_pt']}pt")

        if block.get("border"):
            header_parts.append("Có đường kẻ ngang")

        lines.append(f"[{' | '.join(header_parts)}]")

        # Nội dung các cụm chữ
        if fragments:
            for frag in fragments:
                fmt = frag.get("fmt", "Default")
                txt = frag.get("txt", "").replace("\n", " ")
                if txt.strip():
                    lines.append(f'- [{fmt}]: "{txt}"')
        else:
            txt = p.get("text", "").replace("\n", " ")
            lines.append(f'- [Default]: "{txt}"')

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    output_dir = Path("output")

    if not output_dir.exists():
        print(f"⚠️  Không tìm thấy thư mục '{output_dir}'")
        sys.exit(1)

    json_files = sorted(
        f for f in output_dir.glob("*.json")
        if not f.name.endswith("_precheck.json")
    )

    if not json_files:
        print(f"⚠️  Không tìm thấy file .json trong '{output_dir}'")
        sys.exit(1)

    print(f"🔍 Tìm thấy {len(json_files)} file JSON\n")

    for json_path in json_files:
        print(f"🔄 Đang xử lý: {json_path.name}")
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            text     = build_llm_text(data)
            out_file = json_path.with_suffix(".txt")

            with open(out_file, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"   ✅ Đã xuất: {out_file.name}\n")

        except Exception as e:
            print(f"   ❌ Lỗi: {e}\n")

    print("🎉 HOÀN TẤT!")