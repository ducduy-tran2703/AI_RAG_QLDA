# KẾ HOẠCH TÍCH HỢP PIPELINE UPLOAD → EXTRACT → RAG → HIỂN THỊ KẾT QUẢ

**Ngày:** 30/05/2026

---

## 1. TỔNG QUAN

### Mục tiêu
Hoàn thiện luồng xử lý:
```
User Upload → Extract (docx/pdf) → Gửi Prompt đến RAG → Nhận kết quả lỗi → Lưu DB → Hiển thị UI
```

### Flow hiện tại (mock)
```
Upload → POST /documents/upload → tạo CheckResult (status="processing") 
→ run_mock_check() [hardcoded 3 lỗi] → WebSocket progress → Display
```

### Flow cần đạt được
```
Upload → POST /documents/upload → tạo CheckResult (status="processing")
→ Extract file (python-docx / PyMuPDF) → _optimized.json
→ Chunks → Gửi prompt đến RAGFlow API → Nhận kết quả
→ Parse kết quả → Lưu CheckResult + CheckErrors
→ WebSocket progress → Display trên UI
```

---

## 2. CÁC BƯỚC CẦN THỰC HIỆN

### BƯỚC 1: Tạo file `.env` config RAGFlow

**File:** `backend/.env`

Thêm các biến:
```
# RAGFlow Configuration
RAGFLOW_BASE_URL=http://172.20.10.13
RAGFLOW_API_KEY=ragflow-xxxxx
RAGFLOW_ASSISTANT_ID=5a59365a...
```

Cập nhật `backend/app/shared/config.py` để đọc các biến này.

---

### BƯỚC 2: Tạo RAGFlow Client Service

**File mới:** `backend/app/services/check/ragflow_client.py`

Chức năng:
- `RAGFlowClient` class
- `create_session()` - Tạo session mới
- `send_prompt(question: str) -> dict` - Gửi prompt, nhận kết quả LLM
- Parse JSON response (xử lý markdown code block)
- Error handling + retry

Tham khảo code có sẵn trong `backend/source/send_to_ragflow.py`:
- Hàm `create_session()` → copy và async
- Hàm `send_chunk()` → copy và async
- Hàm `parse_llm_answer()` → copy nguyên

---

### BƯỚC 3: Tạo Pipeline Service

**File mới:** `backend/app/services/check/pipeline.py`

Chức năng:
- `run_check_pipeline(check_id, document_id)` - Pipeline chính
- Bước 1: Extract - Gọi `extract_docx.py` / `extract_pdf.py`
- Bước 2: Convert - Gọi `jsonl_to_text.py` → .txt
- Bước 3: Chunk - Gọi `chunnk_for_ragflow.py` → chunks
- Bước 4: Send to RAG - Gọi RAGFlow API
- Bước 5: Parse kết quả → Tạo CheckError objects
- Bước 6: Lưu DB
- Mỗi bước gửi WebSocket progress

**Lưu ý quan trọng:**
- Code extract hiện tại trong `backend/source/` là standalone scripts
- Cần refactor thành **importable functions** để dùng trong pipeline
- Không dùng `if __name__ == "__main__"` mà export functions

---

### BƯỚC 4: Refactor Extract Functions

**Files cần refactor:**

#### `backend/source/extract_docx.py`
- Tách phần logic chính ra hàm `extract_docx(file_path: str) -> dict`
- Bỏ phần `if __name__ == "__main__"` (giữ nguyên để test)
- Export: `extract_docx`, `load_docx`, `build_block_info`, etc.

#### `backend/source/extract_pdf.py`
- Tương tự: `extract_pdf(file_path: str) -> dict`
- Export main functions

#### `backend/source/jsonl_to_text.py`
- Tách: `convert_json_to_text(json_data: dict) -> str`

#### `backend/source/chunnk_for_ragflow.py`
- Tách: `create_chunks_from_text(text: str, meta: dict) -> dict`

---

### BƯỚC 5: Cập nhật Check Service

**File:** `backend/app/services/check/service.py`

Thay `run_mock_check()` bằng `run_real_check()`:

```python
@staticmethod
async def run_real_check(check_id: uuid.UUID, document_id: uuid.UUID):
    """Pipeline kiểm tra thật"""
    start_time = time.time()
    
    try:
        # 1. Lấy file path
        doc = await get_document_by_id(document_id)
        file_path = os.path.join(UPLOAD_DIR, doc.minio_object_key)
        
        # 2. Extract (gửi progress 30%)
        await manager.send_progress(check_id, {"stage": "extracting", "percent": 30})
        extraction = await extract_file(file_path, doc.file_type)
        
        # 3. Chunk (gửi progress 50%)
        await manager.send_progress(check_id, {"stage": "chunking", "percent": 50})
        chunks = await create_chunks(extraction)
        
        # 4. Send to RAG (gửi progress 70%)
        await manager.send_progress(check_id, {"stage": "rag", "percent": 70})
        rag_results = await send_to_ragflow(chunks)
        
        # 5. Parse kết quả (gửi progress 85%)
        await manager.send_progress(check_id, {"stage": "parsing", "percent": 85})
        errors = parse_rag_results(rag_results)
        
        # 6. Lưu DB (gửi progress 95%)
        await save_results(check_id, errors, extraction)
        
        # 7. Hoàn thành
        processing_time = int((time.time() - start_time) * 1000)
        await manager.send_progress(check_id, {"stage": "done", "percent": 100})
        
    except Exception as e:
        # Xử lý lỗi
        await update_check_error(check_id, str(e))
```

---

### BƯỚC 6: Cập nhật Extract → Pipeline Integration

**Luồng chi tiết:**

```
Step 1: EXTRACT
  extract_docx(file_path) → extraction_data (dict JSON)
  
  Output: {
    "filename": "...",
    "margins": {...},
    "paragraphs": [...]
  }

Step 2: CONVERT TO TEXT  
  jsonl_to_text(extraction_data) → plain_text (str)
  
  Output: "📄 TÀI LIỆU: ...\n[Đoạn 0 | Thành phần: ...]\n..."

Step 3: CHUNK
  create_chunks(plain_text, meta) → chunks_data (dict)
  
  Output: {
    "filename": "...",
    "chunks": [
      {"content": "...", "meta": {...}},
      ...
    ]
  }

Step 4: SEND TO RAG
  ragflow_client.send_chunks(chunks_data) → results (list)
  
  Output: [
    {"chunk_id": "...", "errors": [...], "note": "..."},
    ...
  ]

Step 5: PARSE TO CHECKERRORS
  parse_results(results) → list[CheckError]
  
  Map RAGFlow output → CheckError model:
  - errors[].type → error_type
  - errors[].severity → severity  
  - errors[].description → description
  - errors[].current → current_value
  - errors[].expected → expected_value
  - errors[].fix → suggested_fix
  - errors[].reference → rag_reference
```

---

### BƯỚC 7: Upload Flow Integration

**Hiện tại:**
```
POST /documents/upload → DocumentService.upload() → saves to backend/uploads/
```

**Cần thêm:**
- Sau khi upload thành công, nếu user chọn "Kiểm tra ngay" → trigger `check_api.create_check()`
- Frontend gọi `POST /checks` với `document_id` ngay sau upload

**Hoặc tích hợp luôn trong upload endpoint:**
```
POST /documents/upload → save file → auto-create check → run pipeline
```

---

### BƯỚC 8: WebSocket Progress Events

**Events hiện tại (từ check service):**
```json
{"type": "progress", "check_id": "...", "stage": "extracting", "percent": 30}
{"type": "progress", "check_id": "...", "stage": "rag", "percent": 65}
{"type": "progress", "check_id": "...", "stage": "llm", "percent": 90}
{"type": "complete", "check_id": "...", "result_id": "..."}
```

**Cần cập nhật stages:**
```json
{"stage": "extracting", "percent": 15, "message": "Đang bóc tách file..."}
{"stage": "chunking", "percent": 35, "message": "Đang chia nội dung..."}
{"stage": "sending", "percent": 50, "message": "Đang gửi đến AI..."}
{"stage": "analyzing", "percent": 70, "message": "AI đang phân tích..."}
{"stage": "parsing", "percent": 85, "message": "Đang xử lý kết quả..."}
{"stage": "saving", "percent": 95, "message": "Đang lưu kết quả..."}
{"stage": "done", "percent": 100, "message": "Hoàn tất!"}
```

---

### BƯỚC 9: Error Response Format

**Format lỗi từ RAGFlow (dựa trên send_to_ragflow.py):**
```json
{
  "errors": [
    {
      "type": "FONT",
      "severity": "critical",
      "description": "Font chữ không đúng quy định",
      "current": "Arial 12pt",
      "expected": "Times New Roman 13pt",
      "fix": "Chuyển font về TNR 13pt",
      "reference": "Điều 6 NĐ30",
      "confidence": 0.95,
      "page": 1,
      "paragraph": 3
    }
  ],
  "note": ""
}
```

**Map vào CheckError model:**
| RAGFlow Field | CheckError Field |
|---|---|
| type | error_type |
| severity | severity |
| description | description |
| current | current_value |
| expected | expected_value |
| fix | suggested_fix |
| reference | rag_reference |
| confidence | confidence |
| page + paragraph | location_info |

---

### BƯỚC 10: Score Calculation

**Hiện tại:** Mock score = 85

**Tính điểm thật:**
```python
def calculate_score(errors: list[dict]) -> float:
    """Tính điểm tuân thủ 0-100"""
    if not errors:
        return 100.0
    
    # Trọng số theo severity
    weights = {"critical": 15, "warning": 5, "info": 1}
    
    penalty = sum(weights.get(e.get("severity", "info"), 1) for e in errors)
    max_penalty = len(errors) * 15  # penalty tối đa nếu tất cả critical
    
    score = max(0, 100 - (penalty / max_penalty * 40)) if max_penalty > 0 else 100
    return round(score, 1)
```

---

## 3. CHIẾN LƯỢC MOCK (KHI CHƯA CÓ RAGFLOW API)

Tạo file `backend/app/services/check/mock_pipeline.py`:

```python
async def run_mock_pipeline(extraction_data: dict) -> list[dict]:
    """Mock pipeline - trả về lỗi giả để test"""
    await asyncio.sleep(2)  # Mô phỏng thời gian xử lý
    
    paragraphs = extraction_data.get("paragraphs", [])
    errors = []
    
    # Kiểm tra font
    for p in paragraphs:
        for run in p.get("runs", []):
            fmt = run.get("fmt", "")
            if "Arial" in fmt:
                errors.append({
                    "type": "FONT",
                    "severity": "critical",
                    "description": f"Font Arial phát hiện ở đoạn {p['idx']}",
                    "current": fmt,
                    "expected": "Times New Roman 13pt",
                    "fix": "Thay font về Times New Roman 13pt",
                    "reference": "Điều 6, Khoản 2, NĐ30/2020",
                    "confidence": 0.95,
                    "page": p.get("page", 1),
                    "paragraph": p["idx"]
                })
    
    # Kiểm tra lề
    margins = extraction_data.get("margins", {})
    if margins.get("left_cm", 0) < 3.0:
        errors.append({
            "type": "MARGIN",
            "severity": "warning",
            "description": "Lề trái nhỏ hơn quy định",
            "current": f"{margins['left_cm']}cm",
            "expected": "3.0cm (±0.1cm)",
            "fix": "Điều chỉnh lề trái về 3.0cm",
            "reference": "Điều 6, Khoản 1, NĐ30/2020",
            "confidence": 0.90
        })
    
    return errors
```

---

## 4. THỨ TỰ THỰC HIỆN

| # | Task | Files | Mức độ ưu tiên |
|---|---|---|---|
| 1 | Thêm RAGFlow config vào .env | `.env`, `config.py` | ✅ |
| 2 | Refactor extract functions | `source/*.py` | ✅ |
| 3 | Tạo pipeline service | `check/pipeline.py` | ✅ |
| 4 | Tạo mock pipeline | `check/mock_pipeline.py` | ✅ |
| 5 | Cập nhật CheckService | `check/service.py` | ✅ |
| 6 | Tạo RAGFlow client | `check/ragflow_client.py` | ✅ |
| 7 | Test pipeline end-to-end | Manual test | ✅ |
| 8 | Cập nhật frontend | Display errors | ✅ |

---

## 5. KIỂM TRA TRƯỚC KHI BẮT ĐẦU

- [ ] Đã cài `python-docx`, `pymupdf` chưa?
- [ ] File extract_docx.py có import được không?
- [ ] File upload lưu ở đâu? (`backend/uploads/` có tồn tại?)
- [ ] RAGFlow server có đang chạy không? (http://172.20.10.13)

---

*Nếu RAGFlow chưa sẵn sàng, dùng mock pipeline để test toàn bộ flow trước.*