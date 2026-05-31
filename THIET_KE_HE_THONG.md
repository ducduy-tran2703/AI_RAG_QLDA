# THIẾT KẾ HỆ THỐNG - AI KIỂM TRA VĂN BẢN HÀNH CHÍNH

**Ngày:** 30/05/2026
**Phiên bản:** 1.0

---

## 1. TỔNG QUAN KIẾN TRÚC

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)                  │
│  http://localhost:5173                                       │
├─────────────────────────────────────────────────────────────┤
│                        API (REST + WS)                      │
├─────────────────────────────────────────────────────────────┤
│                    BACKEND (FastAPI + Python)                │
│  http://localhost:8000                                       │
├─────────────────────────────────────────────────────────────┤
│         PostgreSQL (Database)   │    RAGFlow (AI Service)    │
│         localhost:5432          │    http://192.168.123.159  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. BACKEND - FASTAPI

### 2.1 Cấu trúc thư mục

```
backend/
├── .env                      # Biến môi trường
├── requirements.txt          # Dependencies
├── app/
│   ├── main.py               # Entry point FastAPI app
│   ├── shared/
│   │   ├── config.py         # Settings (pydantic)
│   │   ├── database.py       # SQLAlchemy engine + session
│   │   ├── storage.py        # Upload file management
│   │   ├── auth.py           # JWT auth dependency
│   │   └── websocket_manager.py  # WebSocket progress manager
│   │   └── models/           # SQLAlchemy models (13 tables)
│   │       ├── __init__.py   # Export all models
│   │       ├── user.py       # User, Department
│   │       ├── document.py   # Document, DocumentFolder, DocumentVersion
│   │       ├── check.py      # CheckResult, CheckError
│   │       ├── rules.py      # RuleSet, Rule, RuleSetDepartment, RuleSetVersion
│   │       ├── knowledge.py  # KnowledgeCategory, KnowledgeBaseDocument
│   │       ├── template.py   # Template, TemplateComparison
│   │       ├── notification.py # Notification
│   │       ├── collaboration.py # ApprovalRequest, DocumentComment
│   │       └── system.py     # SystemSetting, AuditLog, SupportTicket, ApiKey, AiAgent, AgentTask, AiFeedback, PasswordResetToken, LoginSession
│   └── services/             # Business logic modules
│       ├── auth/             # Đăng nhập, JWT, refresh token
│       ├── document/         # CRUD documents, folders, versions
│       ├── check/            # Kiểm tra văn bản (pipeline RAGFlow)
│       │   ├── router.py     # POST /checks, GET /checks/{id}, ...
│       │   ├── service.py    # CheckService (tạo check, chạy pipeline)
│       │   ├── pipeline.py   # Pipeline 5 bước: Extract → Chunk → RAG → Parse → Save
│       │   ├── ragflow_client.py  # Async RAGFlow API client (dual assistant)
│       │   ├── mock_pipeline.py   # Mock pipeline (heuristic analysis)
│       │   └── schemas.py    # Pydantic schemas
│       ├── rules/            # Quản lý bộ quy tắc
│       ├── knowledge/        # Quản lý knowledge base
│       ├── template/         # Quản lý mẫu văn bản
│       ├── analytics/        # Thống kê, báo cáo
│       ├── admin/            # Quản trị hệ thống
│       ├── approval/         # Quy trình phê duyệt
│       ├── notification/     # Thông báo
│       ├── collaboration/    # Cộng tác, comment
│       └── ...               # Services khác
├── source/                   # Các module extraction độc lập
│   ├── extract_docx.py       # Bóc tách .docx → JSON cấu trúc
│   ├── extract_pdf.py        # Bóc tách .pdf → JSON cấu trúc
│   ├── jsonl_to_text.py      # JSON → plain text cho LLM
│   ├── chunnk_for_ragflow.py # Chunk text → chunks cho RAGFlow
│   └── send_to_ragflow.py    # CLI gửi chunks đến RAGFlow (dual assistant)
├── uploads/                  # Thư mục lưu file upload
└── scripts/
    └── seed_data.py          # Seed dữ liệu mẫu
```

### 2.2 Endpoints API

| Nhóm | Endpoint | Method | Chức năng |
|------|----------|--------|-----------|
| **Auth** | `/api/v1/auth/login` | POST | Đăng nhập |
| | `/api/v1/auth/register` | POST | Đăng ký |
| | `/api/v1/auth/refresh` | POST | Refresh token |
| | `/api/v1/auth/me` | GET | Thông tin user |
| **Documents** | `/api/v1/documents` | GET | Danh sách văn bản |
| | `/api/v1/documents` | POST | Upload văn bản mới |
| | `/api/v1/documents/{id}` | GET | Chi tiết văn bản |
| | `/api/v1/documents/{id}` | DELETE | Xóa văn bản |
| | `/api/v1/documents/{id}/download` | GET | Tải văn bản |
| | `/api/v1/documents/folders` | GET | Danh sách thư mục |
| | `/api/v1/documents/folders` | POST | Tạo thư mục |
| **Checks** | `/api/v1/checks` | POST | Tạo kiểm tra mới |
| | `/api/v1/checks/{id}` | GET | Kết quả kiểm tra |
| | `/api/v1/checks/document/{doc_id}` | GET | DS kết quả của văn bản |
| | `/api/v1/checks/{id}/recheck` | POST | Kiểm tra lại |
| | `/api/v1/checks/{id}/export/json` | GET | Xuất JSON |
| | `/api/v1/checks/{id}/export/pdf` | GET | Xuất PDF |
| | `/api/v1/checks/{id}/errors/{eid}/feedback` | POST | Phản hồi lỗi |
| **WebSocket** | `/ws/check/{check_id}` | WS | Progress kiểm tra realtime |
| | `/ws/user/{user_id}` | WS | Notification realtime |
| **Admin** | `/api/v1/admin/users` | GET | DS người dùng |
| | `/api/v1/admin/settings` | GET | Cài đặt hệ thống |
| | `/api/v1/admin/audit-logs` | GET | Audit logs |
| | `/api/v1/admin/api-keys` | GET | Quản lý API key |
| **Rules** | `/api/v1/rules/sets` | GET | DS bộ quy tắc |
| | `/api/v1/rules/sets` | POST | Tạo bộ quy tắc |
| | `/api/v1/rules/sets/{id}` | GET | Chi tiết bộ quy tắc |
| **Knowledge** | `/api/v1/knowledge/categories` | GET | DS danh mục |
| **Approval** | `/api/v1/approval/submit` | POST | Gửi phê duyệt |
| | `/api/v1/approval/pending` | GET | DS chờ duyệt |

### 2.3 Pipeline Kiểm Tra (RAGFlow Pipeline)

```
POST /api/v1/checks  →  tạo CheckResult (status="processing")
                         ↓
                    asyncio.create_task(pipeline.run_check_pipeline())
                         ↓
                    ┌──────────────────────────────────────┐
                    │  Bước 1: EXTRACT FILE                │
                    │  extract_docx_to_dict /              │
                    │  extract_pdf_to_dict                 │
                    │  → extraction_data (JSON)            │
                    │  Progress: 10%                       │
                    ├──────────────────────────────────────┤
                    │  Bước 2: CONVERT TO TEXT             │
                    │  build_llm_text(extraction_data)     │
                    │  → plain_text                        │
                    │  Progress: 25%                       │
                    ├──────────────────────────────────────┤
                    │  Bước 3: CHUNK                       │
                    │  build_chunks(plain_text, filename)  │
                    │  → [chunk_000 (meta), chunk_001, ..] │
                    │  Progress: 40%                       │
                    ├──────────────────────────────────────┤
                    │  Bước 4: RAGFLOW                     │
                    │  chunk_000 → ASSISTANT_MANIFEST_ID   │
                    │  chunk_N   → ASSISTANT_FORMAT_ID     │
                    │  Progress: 55-75%                    │
                    ├──────────────────────────────────────┤
                    │  Bước 5: LƯU DB                      │
                    │  parse_ragflow_results → CheckError  │
                    │  calculate_score → CheckResult       │
                    │  Progress: 90-100%                   │
                    └──────────────────────────────────────┘
```

---

## 3. DATABASE - POSTGRESQL (13 Tables)

### 3.1 Sơ đồ thực thể

```
Department (1) ──< (N) User (1) ──< (N) Document ──< (N) CheckResult ──< (N) CheckError
                      │                                        │
                      │                                        ├──< AiFeedback
                      │                                        └──< AgentTask ──> AiAgent
                      │
                      ├──< DocumentFolder
                      ├──< DocumentVersion
                      ├──< ApprovalRequest
                      ├──< DocumentComment
                      ├──< Notification
                      ├──< LoginSession
                      ├──< PasswordResetToken
                      └──< ApiKey

RuleSet (1) ──< (N) Rule
RuleSet (1) ──< (N) RuleSetDepartment ──> Department
RuleSet (1) ──< (N) RuleSetVersion

KnowledgeCategory (1) ──< (N) KnowledgeBaseDocument

Template (1) ──< (N) TemplateComparison

SupportTicket ──> User (submitter)
SupportTicket ──> User (assignee)

AuditLog (độc lập, ghi log mọi hành động)
SystemSetting (độc lập, lưu cấu hình)
```

### 3.2 Danh sách bảng

| # | Bảng | Mô tả | Số cột |
|---|------|-------|--------|
| 1 | `departments` | Phòng ban | 7 |
| 2 | `users` | Người dùng | 20 |
| 3 | `documents` | Văn bản | 14 |
| 4 | `document_folders` | Thư mục | 8 |
| 5 | `document_versions` | Phiên bản văn bản | 9 |
| 6 | `check_results` | Kết quả kiểm tra | 14 |
| 7 | `check_errors` | Chi tiết lỗi | 10 |
| 8 | `approval_requests` | Yêu cầu phê duyệt | 11 |
| 9 | `document_comments` | Bình luận | 7 |
| 10 | `rule_sets` | Bộ quy tắc | 12 |
| 11 | `rules` | Quy tắc chi tiết | 11 |
| 12 | `rule_set_departments` | Áp dụng bộ quy tắc | 3 |
| 13 | `rule_set_versions` | Phiên bản bộ quy tắc | 6 |
| 14 | `knowledge_categories` | Danh mục kiến thức | 5 |
| 15 | `knowledge_base_documents` | Tài liệu knowledge | 7 |
| 16 | `templates` | Mẫu văn bản | 10 |
| 17 | `template_comparisons` | So sánh mẫu | 8 |
| 18 | `notifications` | Thông báo | 8 |
| 19 | `system_settings` | Cài đặt hệ thống | 12 |
| 20 | `audit_logs` | Nhật ký hoạt động | 16 |
| 21 | `support_tickets` | Yêu cầu hỗ trợ | 16 |
| 22 | `api_keys` | API keys | 14 |
| 23 | `ai_agents` | AI Agents | 9 |
| 24 | `agent_tasks` | Tác vụ AI | 9 |
| 25 | `ai_feedback` | Phản hồi AI | 5 |
| 26 | `password_reset_tokens` | Token reset mật khẩu | 5 |
| 27 | `login_sessions` | Phiên đăng nhập | 9 |

---

## 4. FRONTEND - REACT + VITE

### 4.1 Cấu trúc thư mục

```
frontend/src/
├── main.tsx                    # Entry point
├── App.tsx                     # (đang là mẫu Vite mặc định)
├── index.css                   # Tailwind base styles
├── router/
│   └── index.tsx               # React Router config (14 routes)
├── stores/
│   └── authStore.ts            # Zustand auth store
├── hooks/                      # Custom hooks
│   ├── useCheckResult.ts       # Fetch check results
│   ├── useDocuments.ts         # Fetch documents
│   ├── useWebSocket.ts         # WebSocket connection
│   ├── useFolders.ts           # Fetch folders
│   ├── useDashboard.ts         # Dashboard data
│   ├── useApproval.ts          # Approval requests
│   ├── useNotifications.ts     # Notifications
│   ├── useRules.ts             # Rules CRUD
│   ├── useKnowledge.ts         # Knowledge categories
│   ├── useAdminSettings.ts     # System settings
│   ├── useApiKeys.ts           # API keys
│   └── userAdminUsers.ts       # User management
├── lib/
│   ├── api.ts                  # Axios API client (11 modules)
│   ├── queryClient.ts          # React Query client
│   └── utils.ts                # Utility functions
├── types/
│   ├── index.ts                # Shared types
│   ├── check.ts                # CheckResult, CheckError types
│   └── document.ts             # Document types
├── components/
│   ├── layout/                 # ModernLayout (sidebar + header)
│   ├── ui/                     # Shared UI (Button, Input, Sheet, ...)
│   ├── ProtectedRoute.tsx      # Auth guard
│   └── folders/                # Folder component
└── modules/                    # Page modules
    ├── auth/LoginPage.tsx      # Đăng nhập
    ├── documents/
    │   ├── DocumentListPage.tsx # Danh sách văn bản
    │   └── UploadPage.tsx      # Upload văn bản
    ├── checks/CheckResultPage.tsx  # Kết quả kiểm tra
    ├── analytics/DashboardPage.tsx # Dashboard (biểu đồ)
    ├── admin/
    │   ├── AdminUsersPage.tsx  # Quản lý người dùng
    │   └── AuditLogPage.tsx    # Audit logs
    ├── approval/
    │   ├── SubmitApprovalPage.tsx # Gửi phê duyệt
    │   └── PendingApprovalsPage.tsx # Phê duyệt chờ
    ├── knowledge/KnowledgePage.tsx # Knowledge base
    ├── rules/
    │   ├── RuleSetPage.tsx     # Bộ quy tắc
    │   └── RuleDetailPage.tsx  # Chi tiết quy tắc
    ├── profile/
    │   ├── ProfilePage.tsx     # Hồ sơ cá nhân
    │   └── SettingsPage.tsx    # Cài đặt
    └── developer/DeveloperPortal.tsx # Cổng API
```

### 4.2 Routes

| Path | Page | Auth | Mô tả |
|------|------|------|-------|
| `/login` | LoginPage | ❌ | Đăng nhập |
| `/` | → redirect `/documents` | ✅ | |
| `/documents` | DocumentListPage | ✅ | Danh sách văn bản |
| `/upload` | UploadPage | ✅ | Upload văn bản |
| `/checks/:id` | CheckResultPage | ✅ | Kết quả kiểm tra |
| `/dashboard` | DashboardPage | ✅ | Thống kê |
| `/admin/users` | AdminUsersPage | ✅ | Quản lý user |
| `/admin/audit-logs` | AuditLogPage | ✅ | Audit logs |
| `/submit-approval` | SubmitApprovalPage | ✅ | Gửi phê duyệt |
| `/pending-approvals` | PendingApprovalsPage | ✅ | DS phê duyệt |
| `/profile` | ProfilePage | ✅ | Hồ sơ cá nhân |
| `/settings` | SettingsPage | ✅ | Cài đặt |
| `/knowledge` | KnowledgePage | ✅ | Knowledge base |
| `/rules` | RuleSetPage | ✅ | Bộ quy tắc |
| `/rules/:id` | RuleDetailPage | ✅ | Chi tiết quy tắc |
| `/developer` | DeveloperPortal | ✅ | API Portal |

---

## 5. LUỒNG NGHIỆP VỤ CHÍNH

### 5.1 Upload + Kiểm tra

```
User upload file (.docx/.pdf)
    ↓
Frontend: /upload → POST /api/v1/documents
    ↓
Backend: Lưu file vào uploads/
    ↓
Frontend: POST /api/v1/checks {document_id: ...}
    ↓
Backend: Tạo CheckResult (status="processing")
    ↓         (trả về ngay check_id)
    ↓
Frontend: Kết nối WebSocket /ws/check/{check_id}
    ↓
Backend: Chạy pipeline bất đồng bộ:
    ↓ 10% → Extracting...
    ↓ 25% → Converting...
    ↓ 40% → Chunking...
    ↓ 55% → Sending to AI...
    ↓ 75% → Analyzing...
    ↓ 90% → Saving...
    ↓100% → Complete!
    ↓
Frontend: Nhận complete event → redirect /checks/{id}
```

### 5.2 Xem kết quả

```
Frontend: GET /api/v1/checks/{id}
    ↓
Response: CheckResult + CheckError list
    ↓
Hiển thị:
  - Score (0-100) + Overall assessment
  - Errors grouped by severity (critical, warning, info)
  - Mỗi error: type, description, location, confidence, fix suggestion
  - Filter by severity / error type
  - Feedback: correct / incorrect
  - Export JSON / PDF
```

---

## 6. CÁCH CHẠY HỆ THỐNG

### Backend
```bash
cd backend
.venv\Scripts\activate
python -m scripts.seed_data    # Seed database
python -m uvicorn app.main:app --reload
# Server: http://localhost:8000
# Docs: http://localhost:8000/api/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Server: http://localhost:5173
```

---

## 7. KIẾN TRÚC PIPELINE KIỂM TRA THỂ THỨC

### 7.1 Quy trình xử lý file

```
File .docx / .pdf
    │
    ▼
[Bước 1] EXTRACT
extract_docx_optimized() hoặc extract_pdf_optimized()
    │
    ├── margins: {left_cm, right_cm, top_cm, bottom_cm}
    ├── page_size: {width_cm, height_cm}
    ├── page_number: {size_pt, align, pos}
    ├── paragraphs: [{idx, text, block, runs/spans, zone, page}]
    └── doc_type: "nghi_dinh" | "thong_tu" | "cong_van" | ...
    │
    ▼
[Bước 2] CONVERT
build_llm_text(extraction_data) → plain_text
    │
    TÀI LIỆU: cv123.docx
    NGUỒN: DOCX | LOẠI VĂN BẢN: Công văn
    KHỔ GIẤY: Rộng 21.0cm, Cao 29.7cm
    LỀ TRANG: Trên 2.0cm, Dưới 2.0cm, Trái 3.0cm, Phải 2.0cm
    ==================================================
    NỘI DUNG VĂN BẢN
    ==================================================
    [PARA_ID=0 | Vị trí: Cột phải | Căn lề: Căn giữa]
    - [Times-13pt-Bold]: "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"
    ...
    │
    ▼
[Bước 3] CHUNK
build_chunks(plain_text, filename) → [chunks]
    │
    chunk_000: meta (thành phần bắt buộc + cấu trúc)
    chunk_001: đoạn 0-5
    chunk_002: đoạn 6-12
    ...
    │
    ▼
[Bước 4] RAGFLOW (Dual Assistant)
    │
    ├── chunk_000 → ASSISTANT_MANIFEST_ID (kiểm tra cấu trúc tổng thể)
    │     - Quốc hiệu, Tiêu ngữ
    │     - Tên loại văn bản
    │     - Số ký hiệu
    │     - Thứ tự Chương/Điều
    │
    └── chunk_N → ASSISTANT_FORMAT_ID (kiểm tra định dạng)
          - Font chữ
          - Cỡ chữ
          - Căn lề
          - Giãn dòng
    │
    ▼
[Bước 5] PARSE + LƯU
    │
    Kết quả RAGFlow:
    {
      "errors": [
        {"type": "FONT", "severity": "critical", ...},
        {"type": "MARGIN", "severity": "warning", ...}
      ]
    }
    │
    ▼
    CheckError objects → DB
    calculate_score() → CheckResult.score
```

### 7.2 Score Calculation

```python
weights = {"critical": 15, "warning": 5, "info": 1}
penalty = sum(weights[s] for each error)
max_penalty = total_errors * 15
score = max(0, 100 - (penalty / max_penalty * 40))
→ Kết quả 0-100
```

---

## 8. TÀI KHOẢN MẪU

| Vai trò | Email | Password |
|---------|-------|----------|
| IT Admin | admin@cq.vn | Admin@123 |
| Trưởng phòng | truongphong@cq.vn | Leader@123 |
| Chuyên viên 1 | chuyenvien1@cq.vn | Officer@123 |
| Chuyên viên 2 | chuyenvien2@cq.vn | Officer@123 |
| Biz Admin | bizadmin@cq.vn | Biz@123 |