"""
send_to_ragflow.py  (v3 — dual assistant)
==========================================
Đọc _chunks.json từ ragflow_chunks/,
gửi từng chunk vào đúng RAGFlow Assistant:
  - chunk_000 (type=meta)    → ASSISTANT_MANIFEST_ID  (kiểm tra cấu trúc)
  - chunk_001...N (content)  → ASSISTANT_FORMAT_ID    (kiểm tra định dạng)

Yêu cầu trước khi chạy:
  1. Tạo 2 Assistant trong RAGFlow (cùng gắn Knowledge Base NĐ30):
       - Assistant 1 "checker_manifest": dùng System Prompt cho chunk_000
       - Assistant 2 "checker_format":   dùng System Prompt cho chunk_001...N
  2. Cấu hình mỗi Assistant trong RAGFlow UI:
       - System prompt tương ứng (có {knowledge} placeholder)
       - Empty response: {"errors": [], "note": ""}
       - Temperature: 0.1
       - Similarity threshold: 0.3
       - Top N: 4
  3. Tạo file .env ở thư mục gốc project:
       RAGFLOW_BASE_URL=http://172.20.10.13
       RAGFLOW_API_KEY=ragflow-xxxxx
       RAGFLOW_ASSISTANT_MANIFEST_ID=xxx   ← Assistant kiểm tra cấu trúc
       RAGFLOW_ASSISTANT_FORMAT_ID=xxx     ← Assistant kiểm tra định dạng

Cách chạy:
  python src/send_to_ragflow.py
  python src/send_to_ragflow.py --file ragflow_chunks/ten_file_chunks.json
"""

import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

import requests

# ── Đọc config từ .env ───────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════════════
# CẤU HÌNH
# ══════════════════════════════════════════════════════════════════════

RAGFLOW_BASE_URL      = os.getenv("RAGFLOW_BASE_URL", "http://172.20.10.13")
RAGFLOW_API_KEY       = os.getenv("RAGFLOW_API_KEY", "")
ASSISTANT_MANIFEST_ID = os.getenv("RAGFLOW_ASSISTANT_MANIFEST_ID", "")  # chunk_000
ASSISTANT_FORMAT_ID   = os.getenv("RAGFLOW_ASSISTANT_FORMAT_ID", "")    # chunk_001...N

DELAY_BETWEEN_CHUNKS = 0.5   # giây
MAX_RETRIES          = 3
TIMEOUT_SECONDS      = 60


# ══════════════════════════════════════════════════════════════════════
# HÀM GỌI RAGFLOW API
# ══════════════════════════════════════════════════════════════════════

def pick_assistant(chunk: dict) -> tuple[str, str]:
    """
    Chọn assistant phù hợp dựa vào type của chunk.
    Trả về (assistant_id, label) để log.
    """
    chunk_type = chunk.get("meta", {}).get("type", "content")
    if chunk_type == "meta":
        return ASSISTANT_MANIFEST_ID, "manifest"
    return ASSISTANT_FORMAT_ID, "format"


def create_session(http_session: requests.Session, assistant_id: str) -> str | None:
    """Tạo session mới — mỗi chunk dùng 1 session riêng tránh context nhiễm."""
    url     = f"{RAGFLOW_BASE_URL}/api/v1/chats/{assistant_id}/sessions"
    payload = {"name": f"check_{uuid.uuid4().hex[:8]}"}

    try:
        resp = http_session.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") == 0:
            return data["data"]["id"]
        print(f"   ⚠️  Tạo session thất bại: {data.get('message')}")
        return None
    except Exception as e:
        print(f"   ❌ Lỗi tạo session: {e}")
        return None


def build_user_message(chunk: dict, total_chunks: int) -> str:
    """
    Xây dựng user message gửi vào RAGFlow.
    chunk_000: gửi thẳng nội dung manifest.
    chunk_001...N: bổ sung thêm thông tin định vị.
    """
    meta       = chunk.get("meta", {})
    filename   = meta.get("filename", "")
    chunk_id   = meta.get("chunk_id", "")
    chunk_type = meta.get("type", "content")

    if chunk_type == "meta":
        # chunk_000 — nội dung đã đầy đủ, chỉ thêm tiêu đề nhiệm vụ
        return (
            f"Kiểm tra cấu trúc tổng thể văn bản:\n"
            f"\n"
            f"{chunk.get('content', '')}"
        )
    else:
        # chunk_001...N — thêm thông tin định vị để LLM hiểu ngữ cảnh
        order      = meta.get("order", "?")
        para_idxs  = meta.get("para_idxs", [])
        para_range = f"{para_idxs[0]}–{para_idxs[-1]}" if para_idxs else "?"

        return (
            f"Kiểm tra định dạng đoạn văn bản:\n"
            f"Tài liệu : {filename}\n"
            f"Chunk    : {chunk_id} ({order}/{total_chunks})\n"
            f"PARA_ID  : {para_range}\n"
            f"\n"
            f"--- NỘI DUNG ---\n"
            f"{chunk.get('content', '')}"
        )


def send_chunk(
    http_session: requests.Session,
    assistant_id: str,
    session_id: str,
    chunk: dict,
    total_chunks: int,
) -> dict:
    """Gửi 1 chunk vào RAGFlow, trả về dict kết quả."""
    url     = f"{RAGFLOW_BASE_URL}/api/v1/chats/{assistant_id}/completions"
    meta    = chunk.get("meta", {})
    payload = {
        "question":   build_user_message(chunk, total_chunks),
        "stream":     False,
        "session_id": session_id,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = http_session.post(url, json=payload, timeout=TIMEOUT_SECONDS)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") == 0:
                answer = data["data"]["answer"]
                parsed = parse_llm_answer(answer)
                return {
                    "chunk_id":   meta.get("chunk_id"),
                    "chunk_type": meta.get("type", "content"),
                    "order":      meta.get("order"),
                    "para_idxs":  meta.get("para_idxs", []),
                    "raw_answer": answer,
                    "errors":     parsed.get("errors", []),
                    "note":       parsed.get("note", ""),
                    "status":     "ok",
                }
            print(f"      ⚠️  API trả lỗi: {data.get('message')} (lần {attempt})")

        except requests.exceptions.Timeout:
            print(f"      ⚠️  Timeout (lần {attempt}/{MAX_RETRIES})")
        except requests.exceptions.RequestException as e:
            print(f"      ⚠️  Lỗi request: {e} (lần {attempt}/{MAX_RETRIES})")
        except Exception as e:
            print(f"      ⚠️  Lỗi không xác định: {e} (lần {attempt}/{MAX_RETRIES})")

        if attempt < MAX_RETRIES:
            time.sleep(2 ** attempt)

    return {
        "chunk_id":   meta.get("chunk_id"),
        "chunk_type": meta.get("type", "content"),
        "order":      meta.get("order"),
        "para_idxs":  meta.get("para_idxs", []),
        "raw_answer": None,
        "errors":     [],
        "note":       "Gửi thất bại sau nhiều lần thử",
        "status":     "failed",
    }


def parse_llm_answer(answer: str) -> dict:
    """Parse JSON từ câu trả lời của Qwen (xử lý cả markdown code block)."""
    text = answer.strip()

    if text.startswith("```"):
        lines = [l for l in text.splitlines() if not l.startswith("```")]
        text  = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass

    return {
        "errors": [],
        "note":   f"Không parse được JSON. Raw: {text[:300]}"
    }


# ══════════════════════════════════════════════════════════════════════
# XỬ LÝ 1 FILE CHUNKS
# ══════════════════════════════════════════════════════════════════════

def process_chunks_file(chunks_path: Path, results_dir: Path) -> None:
    """Đọc _chunks.json → gửi từng chunk đúng assistant → lưu kết quả."""
    print(f"🔄 Đang xử lý: {chunks_path.name}")

    with open(chunks_path, encoding="utf-8") as f:
        chunks_data = json.load(f)

    filename = chunks_data.get("filename", chunks_path.stem)
    chunks   = chunks_data.get("chunks", [])
    total    = len(chunks)

    # Đếm riêng meta vs content để log
    n_meta    = sum(1 for c in chunks if c.get("meta", {}).get("type") == "meta")
    n_content = total - n_meta
    print(f"   📄 File: {filename} | {total} chunks ({n_meta} manifest + {n_content} nội dung)\n")

    http_session = requests.Session()
    http_session.headers.update({
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type":  "application/json",
    })

    all_results           = []
    total_errors          = 0
    total_struct_errors   = 0   # lỗi từ chunk_000
    total_format_errors   = 0   # lỗi từ chunk_001...N
    failed                = 0

    for i, chunk in enumerate(chunks, 1):
        meta       = chunk.get("meta", {})
        cid        = meta.get("chunk_id", f"chunk_{i:03d}")
        chars      = len(chunk.get("content", ""))
        assistant_id, a_label = pick_assistant(chunk)

        print(f"   [{i:02d}/{total}] {cid} [{a_label}] ({chars} ký tự) ...", end=" ", flush=True)

        sess_id = create_session(http_session, assistant_id)
        if not sess_id:
            print("❌ Không tạo được session")
            failed += 1
            all_results.append({
                "chunk_id":   cid,
                "chunk_type": meta.get("type", "content"),
                "order":      meta.get("order"),
                "errors":     [],
                "status":     "failed",
                "note":       "Không tạo được session",
            })
            continue

        result = send_chunk(http_session, assistant_id, sess_id, chunk, total)
        n_err  = len(result.get("errors", []))
        total_errors += n_err

        if meta.get("type") == "meta":
            total_struct_errors += n_err
        else:
            total_format_errors += n_err

        if result["status"] == "ok":
            print(f"✅ {n_err} lỗi")
        else:
            print(f"❌ thất bại")
            failed += 1

        all_results.append(result)
        time.sleep(DELAY_BETWEEN_CHUNKS)

    # ── Lưu kết quả ──
    out = {
        "filename":            filename,
        "total_chunks":        total,
        "total_errors":        total_errors,
        "struct_errors":       total_struct_errors,   # lỗi cấu trúc/thiếu thành phần
        "format_errors":       total_format_errors,   # lỗi định dạng font/lề/...
        "failed_chunks":       failed,
        "results":             all_results,
    }

    stem     = chunks_path.stem.replace("_chunks", "")
    out_path = results_dir / f"{stem}_llm_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n   ✅ Xong!")
    print(f"      Lỗi cấu trúc : {total_struct_errors}")
    print(f"      Lỗi định dạng: {total_format_errors}")
    print(f"      Chunk thất bại: {failed}")
    print(f"   💾 Lưu: {out_path}\n")


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Kiểm tra config
    if not RAGFLOW_API_KEY:
        print("❌ Thiếu RAGFLOW_API_KEY. Thêm vào file .env:")
        print("   RAGFLOW_API_KEY=ragflow-xxxxx")
        sys.exit(1)
    if not ASSISTANT_MANIFEST_ID:
        print("❌ Thiếu RAGFLOW_ASSISTANT_MANIFEST_ID. Thêm vào file .env:")
        print("   RAGFLOW_ASSISTANT_MANIFEST_ID=xxx")
        sys.exit(1)
    if not ASSISTANT_FORMAT_ID:
        print("❌ Thiếu RAGFLOW_ASSISTANT_FORMAT_ID. Thêm vào file .env:")
        print("   RAGFLOW_ASSISTANT_FORMAT_ID=xxx")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Gửi chunks vào RAGFlow để kiểm tra thể thức văn bản"
    )
    parser.add_argument(
        "--file", "-f",
        help="Chỉ xử lý 1 file _chunks.json (mặc định: quét toàn bộ ragflow_chunks/)"
    )
    args = parser.parse_args()

    chunks_dir  = Path("ragflow_chunks")
    results_dir = Path("ragflow_results")
    results_dir.mkdir(exist_ok=True)

    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"❌ Không tìm thấy file: {p}")
            sys.exit(1)
        process_chunks_file(p, results_dir)
    else:
        if not chunks_dir.exists():
            print(f"❌ Không tìm thấy thư mục '{chunks_dir}'")
            sys.exit(1)

        files = sorted(chunks_dir.glob("*_chunks.json"))
        if not files:
            print(f"❌ Không tìm thấy file *_chunks.json trong '{chunks_dir}'")
            sys.exit(1)

        print(f"🔍 Tìm thấy {len(files)} file chunks\n")
        for f in files:
            process_chunks_file(f, results_dir)

    print("🎉 HOÀN TẤT!")