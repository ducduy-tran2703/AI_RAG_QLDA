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
# HÀM CHÍNH — BUILD CHUNKS
# ══════════════════════════════════════════════════════════════════════

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

            chunks = build_chunks(txt_content, filename)

            out = {
                "filename":     filename,
                "total_chunks": len(chunks),
                "max_chars":    MAX_CHARS,
                "chunks":       chunks,
            }

            out_path = ragflow_dir / f"{txt_path.stem}_chunks.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)

            print(f"   ✅ {len(chunks)} chunks → {out_path.name}")
            for c in chunks:
                m2 = c["meta"]
                print(f"      [{m2['chunk_id']}] {len(c['content'])} ký tự | "
                      f"đoạn {m2['para_idxs'][0]}–{m2['para_idxs'][-1]}")
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