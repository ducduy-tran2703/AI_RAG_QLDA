# BẢN THIẾT KẾ CHI TIẾT HỆ THỐNG WEB
## Mô hình AI Kiểm tra Thể thức và Chuẩn hóa Văn bản Hành chính (RAG)

**Phiên bản:** 1.0 | **PM:** [Tên PM] | **Ngày:** 2026

---

> **⚠️ CÁC ĐIỀU CHỈNH SO VỚI BÁO CÁO KTKT GỐC**
>
> Trong quá trình thiết kế, PM đã phát hiện và đề xuất điều chỉnh 4 điểm sau:
>
> 1. **[Sửa - Bảng `check_results`]** Trường `ai_model` trong báo cáo gốc liệt kê ví dụ là "GPT-4o, Claude 3.5, Gemini 1.5" - đây là các dịch vụ Cloud KHÔNG ĐƯỢC PHÉP theo yêu cầu On-premise. **Sửa thành:** các giá trị ví dụ là "llama3:8b", "qwen2.5:7b", "mistral:7b" (Local LLM).
> 2. **[Sửa - Bảo mật]** Báo cáo gốc ghi "Sử dụng giao thức HTTP khi truyền dữ liệu trên mạng nội bộ." → **Sửa thành HTTPS** (dùng self-signed certificate nội bộ). Dù On-premise vẫn nên mã hóa transport để đạt Cấp độ 3 an toàn thông tin.
> 3. **[Bổ sung]** Thiết kế bổ sung **WebSocket endpoint** để realtime progress bar (báo cáo gốc đề cập nhưng chưa thiết kế chi tiết).
> 4. **[Bổ sung]** Thêm bảng **`document_folders`** vào database để hỗ trợ EP02 (tổ chức văn bản vào thư mục - PB-036, PB-037) mà báo cáo gốc chưa có.

---

# MỤC LỤC

1. [Tổng quan & Công nghệ](#1-tổng-quan--công-nghệ)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Tổ chức Module cho Agents](#3-tổ-chức-module-cho-agents)
4. [Thiết kế Database hoàn chỉnh](#4-thiết-kế-database-hoàn-chỉnh)
5. [Thiết kế API](#5-thiết-kế-api)
6. [Design System (UI/UX)](#6-design-system-uiux)
7. [Thiết kế màn hình từng Module](#7-thiết-kế-màn-hình-từng-module)
8. [Luồng xử lý chính](#8-luồng-xử-lý-chính)
9. [Cấu trúc thư mục dự án](#9-cấu-trúc-thư-mục-dự-án)

---

# 1. TỔNG QUAN & CÔNG NGHỆ

## 1.1 Mô tả hệ thống
Hệ thống web nội bộ (On-premise) cho phép cán bộ/chuyên viên văn thư tải lên văn bản hành chính (.docx, .pdf dạng text) để AI tự động kiểm tra thể thức theo Nghị định 30/2020/NĐ-CP và xuất báo cáo lỗi chi tiết.

**Nguyên tắc cốt lõi:** Human-in-the-loop — AI phân tích, con người quyết định.

## 1.2 Stack công nghệ

### Frontend
| Hạng mục | Công nghệ | Lý do chọn |
|---|---|---|
| Framework | **React 18** + TypeScript | Ecosystem lớn, typing tốt cho dự án nghiêm túc |
| Build tool | **Vite** | Nhanh, HMR tốt |
| Routing | **React Router v6** | Standard, file-based routing |
| State Management | **Zustand** (global) + **TanStack Query** (server state) | Nhẹ, dễ debug, không boilerplate |
| UI Components | **Shadcn/ui** + **Radix UI** (headless) | Accessible, customizable, không vendor lock-in |
| Styling | **Tailwind CSS** + CSS Variables | Utility-first, dễ maintain |
| Charts | **Recharts** | Lightweight, declarative |
| File Upload | **React Dropzone** | Drag & drop, robust |
| WebSocket | **Socket.io-client** | Realtime progress |
| HTTP Client | **Axios** + interceptors | JWT refresh tự động |
| Form | **React Hook Form** + **Zod** | Performance, validation |
| i18n | **react-i18next** | Chuẩn bị đa ngôn ngữ (VI mặc định) |
| PDF Viewer | **react-pdf** | Xem trước văn bản |
| Date | **Day.js** | Nhỏ gọn thay Moment |
| Icons | **Lucide React** | Consistent, tree-shakeable |

### Backend
| Hạng mục | Công nghệ | Lý do chọn |
|---|---|---|
| API Framework | **FastAPI** (Python 3.11) | Async native, OpenAPI tự động, type hints |
| Auth | **python-jose** (JWT) + **passlib** (bcrypt) | Standard |
| LDAP | **python-ldap3** | AD/LDAP integration |
| ORM | **SQLAlchemy 2.0** + **Alembic** | Type-safe, migrations |
| Task Queue | **Celery** + **Redis** | Async document processing |
| WebSocket | **FastAPI WebSocket** | Built-in |
| File Security | **python-magic** (MIME check) + **ClamAV** (antivirus) | On-premise safe |
| Email | **python-smtp** | Gửi qua SMTP nội bộ |
| Object Storage | **MinIO Python SDK** | On-premise S3-compatible |
| AI - Doc Extract | **python-docx** + **PyMuPDF** | Bóc tách metadata |
| AI - RAG | **RAGFlow** SDK | Knowledge Base engine |
| AI - LLM | **Ollama** Python client | Local LLM management |
| PDF Export | **WeasyPrint** | HTML → PDF |
| Excel Export | **openpyxl** | Báo cáo Excel |

### Infrastructure
| Hạng mục | Công nghệ |
|---|---|
| Database | **PostgreSQL 16** |
| Vector DB | **Qdrant** |
| Cache/Queue | **Redis 7** |
| Object Storage | **MinIO** |
| Reverse Proxy | **Nginx** |
| Container | **Docker + Docker Compose** |
| LLM Runtime | **Ollama** (Llama3:8b / Qwen2.5:7b) |

---

# 2. KIẾN TRÚC HỆ THỐNG

## 2.1 Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│                    MẠNG NỘI BỘ (LAN/Intranet)                   │
│                                                                  │
│  PC/Laptop User                                                  │
│  ┌─────────────┐                                                 │
│  │  Trình duyệt│──HTTPS──► Nginx (Port 443)                      │
│  │ Chrome/FF   │           │                                     │
│  └─────────────┘           ├──► React SPA (static files)        │
│                            │                                     │
│                            └──► API Gateway (FastAPI :8000)     │
│                                       │                          │
│                    ┌──────────────────┼──────────────────────┐   │
│                    │                  │                       │   │
│             Auth Service       Document Service        Admin  │   │
│             (:8001)            (:8002)                Service │   │
│                                   │                   (:8005) │   │
│                                   ▼                           │   │
│                           Redis Queue                         │   │
│                                   │                           │   │
│                    ┌──────────────┘                           │   │
│                    ▼                                          │   │
│         Check Orchestration Service (:8003)                   │   │
│                    │                                          │   │
│         ┌──────────┼──────────┐                              │   │
│         ▼          ▼          ▼                               │   │
│     Data         RAG        LLM                               │   │
│   Extraction   Engine     Inference                           │   │
│   (python-    (RAGFlow)  (Ollama)                             │   │
│   docx/MuPDF)    │           │                               │   │
│                  ▼           │                                │   │
│               Qdrant ◄───────┘                               │   │
│                                                               │   │
│  ┌──────────┬─────────────┬──────────┬──────────────────┐   │   │
│  │PostgreSQL│   MinIO     │  Redis   │   RAGFlow Engine  │   │   │
│  │  :5432   │   :9000     │  :6379   │     :9380         │   │   │
│  └──────────┴─────────────┴──────────┴──────────────────┘   │   │
└─────────────────────────────────────────────────────────────────┘
```

## 2.2 Microservices & Ports

| Service | Port | Trách nhiệm |
|---|---|---|
| **nginx** | 443 (HTTPS) | Reverse proxy, static files, SSL termination |
| **api-gateway** | 8000 | Routing, rate limiting, WebSocket |
| **auth-service** | 8001 | JWT, LDAP/AD, RBAC |
| **document-service** | 8002 | Upload, CRUD, MinIO |
| **check-orchestration** | 8003 | Điều phối AI pipeline |
| **notification-service** | 8004 | Email, in-app push |
| **admin-service** | 8005 | User management, audit logs |
| **report-service** | 8006 | Xuất PDF/Excel |
| **knowledge-service** | 8007 | RAGFlow management |
| **postgresql** | 5432 | Relational DB |
| **redis** | 6379 | Cache, Queue, Session |
| **minio** | 9000 | Object storage |
| **qdrant** | 6333 | Vector DB |
| **ollama** | 11434 | Local LLM |
| **ragflow** | 9380 | RAG engine |

## 2.3 Vai trò người dùng (RBAC)

| Role | Mã | Quyền chính |
|---|---|---|
| **Chuyên viên / Văn thư** | `OFFICER` | Upload, xem kết quả kiểm tra của mình |
| **Lãnh đạo / Người phê duyệt** | `LEADER` | Xem tất cả của phòng ban, phê duyệt |
| **IT Admin** | `IT_ADMIN` | Toàn bộ user management, system |
| **Admin nghiệp vụ / Quản lý RAG** | `BIZ_ADMIN` | Quản lý knowledge base, rule sets, templates |

---

# 3. TỔ CHỨC MODULE CHO AGENTS

> **QUY ƯỚC CHO AGENTS:** Mỗi Agent code một Module độc lập. Interface giữa modules thông qua REST API (documented tại Section 5). Agents KHÔNG được thay đổi code của module khác trừ khi PM cho phép.

## 3.1 Danh sách Modules

### FRONTEND MODULES

| Module ID | Tên | Epics liên quan | Sprint |
|---|---|---|---|
| **FE-M01** | Auth & Profile | EP01 | Sprint 1 |
| **FE-M02** | Document Upload & Management | EP02, EP21 | Sprint 1-2 |
| **FE-M03** | Check Results & Error Report | EP03, EP04, EP05, EP17 | Sprint 1-2 |
| **FE-M04** | Knowledge Base & Templates | EP06, EP09 | Sprint 2 |
| **FE-M05** | History, Dashboard & Analytics | EP07, EP18, EP24 | Sprint 2-3 |
| **FE-M06** | Approval Workflow | EP08 | Sprint 3 |
| **FE-M07** | Admin - User Management | EP01(admin), EP19 | Sprint 1-2 |
| **FE-M08** | Admin - System Settings | EP13, EP12 | Sprint 2 |
| **FE-M09** | Admin - AI Monitoring | EP20 | Sprint 3 |
| **FE-M10** | Notifications & Support | EP11, EP14, EP22 | Sprint 2-3 |
| **FE-M11** | API Developer Portal | EP15 | Sprint 2 |
| **FE-M12** | Shared Components | (all) | Sprint 1 |

### BACKEND MODULES

| Module ID | Tên | Epics liên quan | Sprint |
|---|---|---|---|
| **BE-M01** | Auth Service | EP01, EP12 | Sprint 1 |
| **BE-M02** | Document Service | EP02, EP21 | Sprint 1 |
| **BE-M03** | Check Orchestration Service | EP03, EP04 | Sprint 1 |
| **BE-M04** | AI Processing Pipeline | EP03, EP05, EP17 | Sprint 1-2 |
| **BE-M05** | Knowledge & Rule Service | EP06, EP09, EP16 | Sprint 2 |
| **BE-M06** | Report & Export Service | EP07, EP24 | Sprint 2 |
| **BE-M07** | Notification Service | EP11 | Sprint 2 |
| **BE-M08** | Admin & Audit Service | EP13, EP12, EP19 | Sprint 1-2 |
| **BE-M09** | API Gateway & Rate Limiting | EP15 | Sprint 2 |
| **BE-M10** | Workflow & Approval | EP08, EP18 | Sprint 3 |

## 3.2 Phụ thuộc giữa Modules

```
FE-M12 (Shared) ← TẤT CẢ FE Modules
BE-M01 (Auth)   ← TẤT CẢ BE Modules (JWT validation)
BE-M02 (Doc)    ← BE-M03 (Check), FE-M02, FE-M03
BE-M03 (Orch)   ← BE-M04 (AI), BE-M05 (Rules)
BE-M04 (AI)     ← BE-M05 (Knowledge)
BE-M05 (KB)     ← FE-M04
BE-M06 (Report) ← FE-M05, FE-M03
BE-M07 (Notif)  ← BE-M03, BE-M10
```

## 3.3 Shared Interfaces (Contract)

### 3.3.1 JWT Token Payload
```typescript
interface JWTPayload {
  sub: string;          // user UUID
  email: string;
  role: 'OFFICER' | 'LEADER' | 'IT_ADMIN' | 'BIZ_ADMIN';
  department_id: string;
  permissions: string[];
  exp: number;
  iat: number;
}
```

### 3.3.2 Standard API Response
```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error?: {
    code: string;         // VD: "VALIDATION_ERROR", "NOT_FOUND"
    message: string;      // Tiếng Việt
    details?: Record<string, string[]>;
  };
  meta?: {
    page?: number;
    limit?: number;
    total?: number;
    total_pages?: number;
  };
}
```

### 3.3.3 WebSocket Events
```typescript
// Client → Server
type WsClientEvent =
  | { type: 'subscribe'; check_id: string }
  | { type: 'unsubscribe'; check_id: string };

// Server → Client  
type WsServerEvent =
  | { type: 'progress'; check_id: string; stage: 'extracting'|'rag'|'llm'|'done'; percent: number }
  | { type: 'complete'; check_id: string; result_id: string }
  | { type: 'error'; check_id: string; message: string }
  | { type: 'notification'; notification: NotificationDto };
```

### 3.3.4 Document DTO
```typescript
interface DocumentDto {
  id: string;
  name: string;
  original_filename: string;
  file_type: 'docx' | 'pdf';
  file_size_bytes: number;
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  latest_check_result?: CheckResultSummaryDto;
  folder_id?: string;
  created_at: string;
  updated_at: string;
}
```

### 3.3.5 CheckResult DTO
```typescript
interface CheckResultDto {
  id: string;
  document_id: string;
  score: number;         // 0-100
  total_errors: number;
  error_counts: {
    critical: number;
    warning: number;
    info: number;
  };
  ai_model: string;      // VD: "llama3:8b"
  checked_at: string;
  status: 'processing' | 'completed' | 'error' | 'timeout';
  processing_time_ms: number;
  errors: CheckErrorDto[];
}

interface CheckErrorDto {
  id: string;
  error_type: string;    // "FONT", "MARGIN", "SPACING", "HEADER", "FOOTER", etc.
  severity: 'critical' | 'warning' | 'info';
  description: string;   // Mô tả tiếng Việt
  location_info: {
    page: number;
    paragraph?: number;
    section?: string;
  };
  current_value: string;
  expected_value: string;
  suggested_fix: string;
  rag_reference: string;  // Trích dẫn điều khoản NĐ30
  confidence: number;     // 0-1
}
```

---

# 4. THIẾT KẾ DATABASE HOÀN CHỈNH

## 4.1 Sơ đồ quan hệ (ERD - text)

```
users ──────────────────────────────────────────────┐
  ├── departments (N:1)                              │
  ├── user_roles (1:N)                               │
  ├── documents (1:N) ──────────────────────────┐    │
  │     ├── document_versions (1:N)              │    │
  │     ├── document_folders (N:1) [NEW]         │    │
  │     └── check_results (1:N)                  │    │
  │           ├── check_errors (1:N)             │    │
  │           │     └── ai_feedback (1:N)        │    │
  │           └── agent_tasks (1:N)              │    │
  ├── approval_requests (1:N)                    │    │
  ├── notifications (1:N)                        │    │
  ├── support_tickets (1:N)                      │    │
  ├── api_keys (1:N)                             │    │
  └── audit_logs (1:N)                           │    │
                                                 │    │
rule_sets ─── rules (1:N)                        │    │
rule_sets ─── check_results (1:N) ───────────────┘    │
                                                       │
templates ─── rule_sets (N:1)                         │
templates ─── documents (N:N via template_comparisons)│
                                                       │
knowledge_base_documents ─── knowledge_categories (N:1)
                                                       │
ai_agents ─── agent_tasks (1:N) ──────────────────────┘
system_settings (standalone)
```

## 4.2 DDL - Tất cả bảng

### Nhóm 1: Người dùng & Phân quyền

```sql
-- DEPARTMENTS: Phòng ban/Đơn vị
CREATE TABLE departments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id   UUID REFERENCES departments(id),
    name        VARCHAR(200) NOT NULL,
    code        VARCHAR(50) UNIQUE NOT NULL,     -- VD: "PHONG_KH"
    description TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- USERS: Tài khoản người dùng
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id   UUID REFERENCES departments(id),
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE,            -- LDAP username
    password_hash   VARCHAR(255),                   -- NULL nếu chỉ dùng SSO
    full_name       VARCHAR(200) NOT NULL,
    phone           VARCHAR(20),
    position        VARCHAR(200),                   -- Chức vụ
    avatar_url      VARCHAR(500),
    role            VARCHAR(20) NOT NULL
                    CHECK (role IN ('OFFICER','LEADER','IT_ADMIN','BIZ_ADMIN')),
    auth_method     VARCHAR(20) NOT NULL DEFAULT 'local'
                    CHECK (auth_method IN ('local','ldap','sso')),
    ldap_dn         VARCHAR(500),                   -- Distinguished Name từ AD
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at   TIMESTAMPTZ,
    login_fail_count SMALLINT NOT NULL DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    must_change_pw  BOOLEAN NOT NULL DEFAULT FALSE,
    timezone        VARCHAR(50) DEFAULT 'Asia/Ho_Chi_Minh',
    language        VARCHAR(10) DEFAULT 'vi',
    preferences     JSONB DEFAULT '{}',             -- UI preferences
    document_quota  INTEGER DEFAULT 1000,           -- Giới hạn số văn bản/tháng
    storage_quota_mb INTEGER DEFAULT 2048,          -- Giới hạn dung lượng MB
    invitation_token VARCHAR(255),
    invitation_expires_at TIMESTAMPTZ,
    privacy_accepted_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- PASSWORD_RESET_TOKENS
CREATE TABLE password_reset_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    used_at     TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- LOGIN_SESSIONS: Theo dõi phiên đăng nhập
CREATE TABLE login_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jwt_jti     VARCHAR(100) UNIQUE NOT NULL,       -- JWT ID để revoke
    ip_address  INET,
    user_agent  TEXT,
    device_info JSONB,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at  TIMESTAMPTZ
);
```

### Nhóm 2: Văn bản & Phiên bản

```sql
-- DOCUMENT_FOLDERS: Thư mục tổ chức văn bản [BỔ SUNG MỚI]
CREATE TABLE document_folders (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id   UUID REFERENCES document_folders(id),
    name        VARCHAR(200) NOT NULL,
    color       VARCHAR(7),                         -- Hex color VD: "#3B82F6"
    icon        VARCHAR(50),                        -- Icon name
    position    INTEGER DEFAULT 0,                  -- Thứ tự hiển thị
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- DOCUMENTS: Văn bản chính
CREATE TABLE documents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id),
    department_id       UUID REFERENCES departments(id),
    folder_id           UUID REFERENCES document_folders(id),
    original_filename   VARCHAR(500) NOT NULL,
    display_name        VARCHAR(500) NOT NULL,       -- Có thể đổi tên
    file_type           VARCHAR(10) NOT NULL CHECK (file_type IN ('docx','pdf')),
    file_size_bytes     BIGINT NOT NULL,
    minio_object_key    VARCHAR(1000) NOT NULL,      -- Đường dẫn trong MinIO
    checksum_sha256     VARCHAR(64) NOT NULL,
    mime_type           VARCHAR(100) NOT NULL,
    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMPTZ,
    doc_type            VARCHAR(100),                -- Loại văn bản: quyết định, công văn...
    tags                TEXT[] DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- DOCUMENT_VERSIONS: Phiên bản văn bản
CREATE TABLE document_versions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number      INTEGER NOT NULL,
    version_label       VARCHAR(50),                 -- VD: "v1.0", "Bản nháp"
    minio_object_key    VARCHAR(1000) NOT NULL,
    file_size_bytes     BIGINT NOT NULL,
    checksum_sha256     VARCHAR(64) NOT NULL,
    change_notes        TEXT,
    created_by          UUID REFERENCES users(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, version_number)
);
```

### Nhóm 3: Quy tắc & Cơ sở tri thức

```sql
-- KNOWLEDGE_CATEGORIES: Danh mục knowledge base
CREATE TABLE knowledge_categories (
    id          INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name        VARCHAR(200) NOT NULL,
    code        VARCHAR(50) UNIQUE NOT NULL,         -- VD: "THE_THUC", "CHINH_TA"
    description TEXT,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- KNOWLEDGE_BASE_DOCUMENTS: Tài liệu pháp lý trong RAGFlow
CREATE TABLE knowledge_base_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id     INTEGER REFERENCES knowledge_categories(id),
    title           VARCHAR(500) NOT NULL,
    doc_code        VARCHAR(100),                    -- VD: "ND30/2020/ND-CP"
    doc_type        VARCHAR(50) NOT NULL
                    CHECK (doc_type IN ('nghi_dinh','thong_tu','quyet_dinh','huong_dan','khac')),
    minio_object_key VARCHAR(1000) NOT NULL,
    ragflow_doc_id  VARCHAR(100),                    -- ID trong RAGFlow
    chunk_count     INTEGER DEFAULT 0,
    vector_size_mb  FLOAT DEFAULT 0,
    index_status    VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (index_status IN ('pending','indexing','ready','error')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    effective_date  DATE,
    replaced_by_id  UUID REFERENCES knowledge_base_documents(id),
    uploaded_by     UUID REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RULE_SETS: Bộ quy tắc kiểm tra
CREATE TABLE rule_sets (
    id              INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name            VARCHAR(200) NOT NULL,
    code            VARCHAR(100) UNIQUE NOT NULL,    -- VD: "ND30_2020_STANDARD"
    description     TEXT,
    doc_types       TEXT[] NOT NULL DEFAULT '{}',    -- Loại VB áp dụng
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version         VARCHAR(20) NOT NULL DEFAULT '1.0',
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RULES: Quy tắc chi tiết
CREATE TABLE rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_set_id     INTEGER NOT NULL REFERENCES rule_sets(id),
    rule_code       VARCHAR(100) NOT NULL,            -- VD: "FONT_BODY_TIMES_13"
    category        VARCHAR(50) NOT NULL
                    CHECK (category IN ('font','margin','spacing','heading',
                                       'page_number','alignment','list',
                                       'header','footer','table','caption',
                                       'quoc_hieu','co_quan','so_ky_hieu',
                                       'ngay_thang','noi_nhan','chu_ky',
                                       'chinh_ta','viet_tat','so_tien')),
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    check_property  VARCHAR(200),                    -- Thuộc tính cụ thể
    expected_value  JSONB NOT NULL,                  -- Giá trị chuẩn
    tolerance       JSONB,                           -- Ngưỡng chấp nhận
    severity        VARCHAR(10) NOT NULL DEFAULT 'warning'
                    CHECK (severity IN ('critical','warning','info')),
    error_message   TEXT NOT NULL,                   -- Mô tả lỗi tiếng Việt
    fix_suggestion  TEXT,                            -- Gợi ý sửa
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (rule_set_id, rule_code)
);

-- RULE_SET_DEPARTMENTS: Gán bộ quy tắc cho phòng ban
CREATE TABLE rule_set_departments (
    rule_set_id     INTEGER NOT NULL REFERENCES rule_sets(id),
    department_id   UUID NOT NULL REFERENCES departments(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (rule_set_id, department_id)
);

-- RULE_SET_VERSIONS: Lịch sử thay đổi bộ quy tắc
CREATE TABLE rule_set_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_set_id     INTEGER NOT NULL REFERENCES rule_sets(id),
    version         VARCHAR(20) NOT NULL,
    snapshot        JSONB NOT NULL,                  -- Toàn bộ rules tại thời điểm đó
    change_notes    TEXT,
    changed_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Nhóm 4: Kiểm tra & Kết quả AI

```sql
-- CHECK_RESULTS: Phiên kiểm tra tổng quan
CREATE TABLE check_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         UUID NOT NULL REFERENCES documents(id),
    version_id          UUID REFERENCES document_versions(id),
    rule_set_id         INTEGER NOT NULL REFERENCES rule_sets(id),
    score               DECIMAL(5,2),                -- 0.00-100.00
    total_errors        INTEGER NOT NULL DEFAULT 0,
    critical_count      INTEGER NOT NULL DEFAULT 0,
    warning_count       INTEGER NOT NULL DEFAULT 0,
    info_count          INTEGER NOT NULL DEFAULT 0,
    ai_model            VARCHAR(100),                -- VD: "llama3:8b" [SỬA từ báo cáo gốc]
    checked_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status              VARCHAR(20) NOT NULL DEFAULT 'processing'
                        CHECK (status IN ('processing','completed','error','timeout')),
    processing_time_ms  INTEGER,
    error_message       TEXT,
    extraction_data     JSONB,                       -- Dữ liệu bóc tách từ file
    rag_context         JSONB,                       -- Quy chuẩn RAG truy xuất được
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CHECK_ERRORS: Chi tiết từng lỗi
CREATE TABLE check_errors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    result_id       UUID NOT NULL REFERENCES check_results(id) ON DELETE CASCADE,
    rule_id         UUID REFERENCES rules(id),
    error_type      VARCHAR(50) NOT NULL,
    severity        VARCHAR(10) NOT NULL CHECK (severity IN ('critical','warning','info')),
    description     TEXT NOT NULL,                   -- Tiếng Việt
    current_value   TEXT,
    expected_value  TEXT,
    suggested_fix   TEXT,
    rag_reference   TEXT,                            -- Trích dẫn điều khoản
    location_info   JSONB,                           -- {"page":1,"paragraph":5,"section":"header"}
    confidence      FLOAT CHECK (confidence BETWEEN 0 AND 1),
    is_acknowledged BOOLEAN NOT NULL DEFAULT FALSE,  -- Người dùng đã xem
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AI_FEEDBACK: Phản hồi người dùng về kết quả AI
CREATE TABLE ai_feedback (
    id              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    error_id        UUID NOT NULL REFERENCES check_errors(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id),
    is_correct      BOOLEAN NOT NULL,
    user_note       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AI_AGENTS: Danh mục AI Agents
CREATE TABLE ai_agents (
    id                  INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    agent_code          VARCHAR(50) UNIQUE NOT NULL,
    agent_name          VARCHAR(100) NOT NULL,
    description         TEXT,
    technical_params    JSONB NOT NULL DEFAULT '{}',
    sla_threshold_ms    INTEGER NOT NULL DEFAULT 5000,
    status              VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
                        CHECK (status IN ('ACTIVE','INACTIVE','MAINTENANCE')),
    version             VARCHAR(10) NOT NULL DEFAULT '1.0',
    last_health_check   TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AGENT_TASKS: Nhiệm vụ của Agent
CREATE TABLE agent_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        INTEGER NOT NULL REFERENCES ai_agents(id),
    check_result_id UUID NOT NULL REFERENCES check_results(id),
    task_priority   INTEGER NOT NULL DEFAULT 1,
    status          VARCHAR(20) NOT NULL DEFAULT 'TODO'
                    CHECK (status IN ('TODO','IN_PROGRESS','DONE','FAILED')),
    input_payload   JSONB,
    output_log      TEXT,
    execution_time  INTEGER,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Nhóm 5: Templates

```sql
-- TEMPLATES: Mẫu văn bản chuẩn
CREATE TABLE templates (
    id              INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    template_name   VARCHAR(255) NOT NULL,
    template_code   VARCHAR(50) UNIQUE NOT NULL,
    description     TEXT,
    minio_object_key VARCHAR(1000) NOT NULL,
    rule_set_id     INTEGER NOT NULL REFERENCES rule_sets(id),
    thumbnail_url   VARCHAR(500),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    version         VARCHAR(10) NOT NULL DEFAULT '1.0',
    doc_types       TEXT[] NOT NULL DEFAULT '{}',
    download_count  INTEGER NOT NULL DEFAULT 0,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TEMPLATE_COMPARISONS: Kết quả so sánh văn bản với template
CREATE TABLE template_comparisons (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_result_id UUID NOT NULL REFERENCES check_results(id),
    template_id     INTEGER NOT NULL REFERENCES templates(id),
    missing_sections JSONB,                          -- Các phần còn thiếu
    extra_sections  JSONB,                           -- Các phần thừa
    structural_score DECIMAL(5,2),                   -- Điểm cấu trúc
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Nhóm 6: Phê duyệt & Cộng tác

```sql
-- APPROVAL_REQUESTS: Yêu cầu phê duyệt
CREATE TABLE approval_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id),
    check_result_id UUID REFERENCES check_results(id),
    submitted_by    UUID NOT NULL REFERENCES users(id),
    approver_id     UUID NOT NULL REFERENCES users(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','rejected','cancelled')),
    submitter_note  TEXT,
    approver_note   TEXT,
    submitted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at     TIMESTAMPTZ,
    deadline_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- DOCUMENT_COMMENTS: Nhận xét cộng tác
CREATE TABLE document_comments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(id),
    error_id        UUID REFERENCES check_errors(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    content         TEXT NOT NULL,
    is_resolved     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Nhóm 7: Hệ thống & Vận hành

```sql
-- API_KEYS: Khóa API tích hợp
CREATE TABLE api_keys (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                VARCHAR(100) NOT NULL,
    key_prefix          VARCHAR(10) NOT NULL,
    key_hash            VARCHAR(255) NOT NULL UNIQUE,
    scopes              TEXT[] NOT NULL DEFAULT '{read}',
    rate_limit_per_min  INTEGER NOT NULL DEFAULT 60 CHECK (rate_limit_per_min >= 0),
    rate_limit_per_day  INTEGER NOT NULL DEFAULT 1000 CHECK (rate_limit_per_day >= 0),
    allowed_ips         INET[],
    last_used_at        TIMESTAMPTZ,
    usage_count         BIGINT NOT NULL DEFAULT 0,
    expires_at          TIMESTAMPTZ,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    revoked_at          TIMESTAMPTZ,
    revoke_reason       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- NOTIFICATIONS
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(50) NOT NULL,
    channel         VARCHAR(20) NOT NULL CHECK (channel IN ('in_app','email','push','webhook')),
    title           VARCHAR(255) NOT NULL,
    body            TEXT NOT NULL,
    action_url      VARCHAR(500),
    icon            VARCHAR(100),
    priority        VARCHAR(10) NOT NULL DEFAULT 'normal'
                    CHECK (priority IN ('low','normal','high','urgent')),
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    is_sent         BOOLEAN NOT NULL DEFAULT FALSE,
    sent_at         TIMESTAMPTZ,
    reference_type  VARCHAR(50),
    reference_id    UUID,
    metadata        JSONB,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- SUPPORT_TICKETS
CREATE TABLE support_tickets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number       VARCHAR(20) NOT NULL UNIQUE,
    user_id             UUID NOT NULL REFERENCES users(id),
    assigned_to         UUID REFERENCES users(id),
    category            VARCHAR(50) NOT NULL,
    priority            VARCHAR(10) NOT NULL DEFAULT 'normal'
                        CHECK (priority IN ('low','normal','high','urgent')),
    status              VARCHAR(20) NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open','in_progress','waiting_user','resolved','closed')),
    subject             VARCHAR(255) NOT NULL,
    description         TEXT NOT NULL,
    attachments         JSONB,
    tags                TEXT[],
    source              VARCHAR(20) NOT NULL DEFAULT 'web',
    sla_due_at          TIMESTAMPTZ,
    first_response_at   TIMESTAMPTZ,
    resolved_at         TIMESTAMPTZ,
    closed_at           TIMESTAMPTZ,
    satisfaction_score  SMALLINT CHECK (satisfaction_score BETWEEN 1 AND 5),
    internal_notes      TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AUDIT_LOGS
CREATE TABLE audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID REFERENCES users(id),
    actor_type      VARCHAR(20) NOT NULL CHECK (actor_type IN ('user','system','api_key','admin')),
    actor_id        VARCHAR(100),
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(50),
    resource_id     VARCHAR(100),
    ip_address      INET,
    user_agent      TEXT,
    request_method  VARCHAR(10),
    request_path    VARCHAR(500),
    request_body    JSONB,
    response_status SMALLINT,
    old_values      JSONB,
    new_values      JSONB,
    result          VARCHAR(10) NOT NULL CHECK (result IN ('success','failure','denied')),
    failure_reason  TEXT,
    duration_ms     INTEGER CHECK (duration_ms >= 0),
    session_id      VARCHAR(255),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);  -- Partition theo tháng để hiệu suất

-- SYSTEM_SETTINGS
CREATE TABLE system_settings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key             VARCHAR(200) NOT NULL UNIQUE,
    value           TEXT,
    value_type      VARCHAR(20) NOT NULL CHECK (value_type IN ('string','integer','float','boolean','json','encrypted')),
    category        VARCHAR(50) NOT NULL,
    label           VARCHAR(200) NOT NULL,
    description     TEXT,
    is_encrypted    BOOLEAN NOT NULL DEFAULT FALSE,
    is_public       BOOLEAN NOT NULL DEFAULT FALSE,
    is_editable     BOOLEAN NOT NULL DEFAULT TRUE,
    default_value   TEXT,
    validation_rules JSONB,
    updated_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## 4.3 Indexes quan trọng

```sql
-- Performance indexes
CREATE INDEX idx_documents_user_id ON documents(user_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_documents_folder_id ON documents(folder_id);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_check_results_document_id ON check_results(document_id);
CREATE INDEX idx_check_results_status ON check_results(status);
CREATE INDEX idx_check_results_checked_at ON check_results(checked_at DESC);
CREATE INDEX idx_check_errors_result_id ON check_errors(result_id);
CREATE INDEX idx_check_errors_severity ON check_errors(severity);
CREATE INDEX idx_check_errors_error_type ON check_errors(error_type);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id) WHERE is_active = TRUE;
```

---

# 5. THIẾT KẾ API

## 5.1 Base URL & Conventions

```
Base URL: https://{server-ip}/api/v1

Headers bắt buộc:
  Authorization: Bearer {jwt-token}
  Content-Type: application/json
  Accept-Language: vi

Phân trang:
  GET /resource?page=1&limit=20&sort=created_at&order=desc
```

## 5.2 Authentication APIs (BE-M01)

```yaml
POST /auth/login
  Body: { email, password }
  Response: { access_token, refresh_token, user: UserDto }

POST /auth/login/sso
  Body: { ldap_username, password }
  Response: { access_token, refresh_token, user: UserDto }

POST /auth/refresh
  Body: { refresh_token }
  Response: { access_token }

POST /auth/logout
  Body: { logout_all?: boolean }
  Response: { success: true }

POST /auth/forgot-password
  Body: { email }
  Response: { success: true }

POST /auth/reset-password
  Body: { token, new_password }
  Response: { success: true }

GET  /auth/me
  Response: { user: UserDto }

PUT  /auth/me
  Body: UserUpdateDto
  Response: { user: UserDto }

PUT  /auth/me/password
  Body: { current_password, new_password }
  Response: { success: true }

GET  /auth/me/sessions
  Response: { sessions: SessionDto[] }

DELETE /auth/sessions/{session_id}
  Response: { success: true }
```

## 5.3 Document APIs (BE-M02)

```yaml
# Upload
POST /documents/upload
  Content-Type: multipart/form-data
  Body: { file, rule_set_id?, folder_id? }
  Response: { document: DocumentDto, check_id: string }

POST /documents/batch-upload
  Content-Type: multipart/form-data
  Body: { files[], rule_set_id?, folder_id? }
  Response: { batch_id: string, documents: DocumentDto[] }

# CRUD
GET  /documents
  Query: { page, limit, sort, folder_id?, search?, file_type?, status?, date_from?, date_to? }
  Response: { documents: DocumentDto[], meta: PaginationMeta }

GET  /documents/{id}
  Response: { document: DocumentDto }

PUT  /documents/{id}
  Body: { display_name?, folder_id?, doc_type?, tags? }
  Response: { document: DocumentDto }

DELETE /documents/{id}
  Response: { success: true }

GET  /documents/{id}/download
  Response: 302 Redirect to MinIO pre-signed URL

GET  /documents/{id}/preview
  Response: { preview_url: string }  # Pre-signed URL MinIO

# Versions
GET  /documents/{id}/versions
  Response: { versions: DocumentVersionDto[] }

POST /documents/{id}/versions
  Content-Type: multipart/form-data
  Body: { file, change_notes? }
  Response: { version: DocumentVersionDto }

# Folders
GET  /folders
  Response: { folders: FolderDto[] }  # Tree structure

POST /folders
  Body: { name, parent_id?, color?, icon? }
  Response: { folder: FolderDto }

PUT  /folders/{id}
  Body: { name?, color?, icon?, position? }
  Response: { folder: FolderDto }

DELETE /folders/{id}
  Response: { success: true }
```

## 5.4 Check APIs (BE-M03)

```yaml
# Kiểm tra
POST /checks
  Body: { document_id, version_id?, rule_set_id? }
  Response: { check_id: string, status: 'queued' }

GET  /checks/{id}
  Response: { result: CheckResultDto }

GET  /documents/{doc_id}/checks
  Response: { results: CheckResultSummaryDto[], meta: PaginationMeta }

# Feedback
POST /checks/{id}/errors/{error_id}/feedback
  Body: { is_correct: boolean, user_note?: string }
  Response: { success: true }

# Export
GET  /checks/{id}/export/pdf
  Response: application/pdf

GET  /checks/{id}/export/excel
  Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

GET  /checks/{id}/export/json
  Response: application/json

# Re-check
POST /checks/{id}/recheck
  Body: { rule_set_id? }
  Response: { check_id: string }

# Template comparison
POST /checks/{id}/compare-template
  Body: { template_id }
  Response: { comparison: TemplateComparisonDto }

# Auto-normalize (EP05)
GET  /checks/{id}/normalize/preview
  Response: { changes: NormalizeChangeDto[] }

POST /checks/{id}/normalize/apply
  Body: { change_ids: string[] }  # Chọn thay đổi nào áp dụng
  Response: { document_url: string }  # URL file đã chuẩn hóa
```

## 5.5 Knowledge Base APIs (BE-M05)

```yaml
# Documents
GET  /knowledge/documents
  Query: { page, limit, category_id?, status?, search? }
  Response: { documents: KnowledgeDocDto[], meta }

POST /knowledge/documents
  Content-Type: multipart/form-data
  Body: { file, title, doc_code?, doc_type, category_id, effective_date? }
  Response: { document: KnowledgeDocDto }

PUT  /knowledge/documents/{id}
  Body: { title?, is_active?, notes? }
  Response: { document: KnowledgeDocDto }

DELETE /knowledge/documents/{id}
  Response: { success: true }

POST /knowledge/documents/{id}/reindex
  Response: { success: true }

# Categories
GET  /knowledge/categories
  Response: { categories: KnowledgeCategoryDto[] }

# Stats
GET  /knowledge/stats
  Response: { total_docs, total_chunks, ready_docs, error_docs, size_mb }

# Rule Sets
GET  /rules/sets
  Response: { rule_sets: RuleSetDto[] }

POST /rules/sets
  Body: { name, code, description, doc_types, is_default? }
  Response: { rule_set: RuleSetDto }

GET  /rules/sets/{id}
  Response: { rule_set: RuleSetDto, rules: RuleDto[] }

PUT  /rules/sets/{id}
  Body: RuleSetUpdateDto
  Response: { rule_set: RuleSetDto }

POST /rules/sets/{id}/clone
  Body: { new_name, new_code }
  Response: { rule_set: RuleSetDto }

POST /rules/sets/{id}/set-default
  Response: { success: true }

# Rules
POST /rules/sets/{set_id}/rules
  Body: RuleCreateDto
  Response: { rule: RuleDto }

PUT  /rules/{id}
  Body: RuleUpdateDto
  Response: { rule: RuleDto }

DELETE /rules/{id}
  Response: { success: true }
```

## 5.6 Templates APIs

```yaml
GET  /templates
  Query: { page, limit, doc_type?, is_active? }
  Response: { templates: TemplateDto[], meta }

GET  /templates/{id}
  Response: { template: TemplateDto }

GET  /templates/{id}/download
  Response: Redirect to MinIO pre-signed URL

POST /templates (BIZ_ADMIN only)
  Content-Type: multipart/form-data
  Body: { file, template_name, template_code, rule_set_id, doc_types[], description? }
  Response: { template: TemplateDto }

PUT  /templates/{id} (BIZ_ADMIN only)
  Body: { template_name?, description?, is_active?, doc_types? }
  Response: { template: TemplateDto }
```

## 5.7 Analytics APIs (BE-M06)

```yaml
# Dashboard
GET  /analytics/dashboard
  Query: { from_date, to_date, department_id? }
  Response: DashboardDto

# Reports
GET  /analytics/reports/checks
  Query: { from_date, to_date, user_id?, department_id?, doc_type? }
  Response: { data: CheckStatsDto[], summary: StatsSummaryDto }

GET  /analytics/reports/errors
  Query: { from_date, to_date, department_id? }
  Response: { top_errors: ErrorFrequencyDto[], by_type: ErrorByTypeDto[] }

GET  /analytics/reports/trends
  Query: { period: 'day'|'week'|'month', from_date, to_date }
  Response: { trend: TrendDataDto[] }

# Export reports
GET  /analytics/export/excel
  Query: { type, from_date, to_date, ... }
  Response: Excel file

GET  /analytics/export/pdf
  Query: { type, from_date, to_date, ... }
  Response: PDF file
```

## 5.8 Admin APIs (BE-M08)

```yaml
# Users (IT_ADMIN)
GET  /admin/users
  Query: { page, limit, role?, department_id?, is_active?, search? }
  Response: { users: UserDto[], meta }

POST /admin/users
  Body: UserCreateDto
  Response: { user: UserDto }

PUT  /admin/users/{id}
  Body: UserUpdateDto
  Response: { user: UserDto }

POST /admin/users/{id}/lock
  Response: { success: true }

POST /admin/users/{id}/unlock
  Response: { success: true }

POST /admin/users/{id}/reset-password
  Response: { success: true }  # Gửi email reset

POST /admin/users/sync-ldap
  Response: { synced: number, created: number, updated: number }

POST /admin/users/bulk-import
  Content-Type: multipart/form-data
  Body: { file }  # Excel/CSV
  Response: { imported: number, errors: ImportErrorDto[] }

# Audit logs
GET  /admin/audit-logs
  Query: { page, limit, from_date, to_date, action?, user_id?, result? }
  Response: { logs: AuditLogDto[], meta }

# System health
GET  /admin/health
  Response: SystemHealthDto

# Settings
GET  /admin/settings
  Response: { settings: SettingDto[] }

PUT  /admin/settings/{key}
  Body: { value: string }
  Response: { setting: SettingDto }

# API Keys
GET  /admin/api-keys
  Response: { keys: ApiKeyDto[] }

PUT  /admin/api-keys/{id}/revoke
  Body: { reason? }
  Response: { success: true }
```

## 5.9 WebSocket Endpoint

```
WS: wss://{server}/ws?token={jwt-token}

Events từ Server:
  check_progress: { check_id, stage, percent, message }
  check_complete: { check_id, result_id, score, total_errors }
  check_error: { check_id, message }
  notification: { id, type, title, body, action_url }
  system_message: { message, level }
```

---

# 6. DESIGN SYSTEM (UI/UX)

## 6.1 Màu sắc (CSS Variables)

```css
:root {
  /* Brand - Tông xanh chính phủ Việt Nam, hiện đại */
  --color-primary-50:  #EFF6FF;
  --color-primary-100: #DBEAFE;
  --color-primary-500: #1D4ED8;   /* Main brand */
  --color-primary-600: #1E40AF;
  --color-primary-700: #1E3A8A;

  /* Neutral */
  --color-gray-50:  #F9FAFB;
  --color-gray-100: #F3F4F6;
  --color-gray-200: #E5E7EB;
  --color-gray-300: #D1D5DB;
  --color-gray-400: #9CA3AF;
  --color-gray-500: #6B7280;
  --color-gray-600: #4B5563;
  --color-gray-700: #374151;
  --color-gray-800: #1F2937;
  --color-gray-900: #111827;

  /* Semantic - Lỗi, cảnh báo, thành công */
  --color-error-50:   #FEF2F2;
  --color-error-500:  #EF4444;   /* Lỗi nghiêm trọng */
  --color-error-700:  #B91C1C;

  --color-warning-50:  #FFFBEB;
  --color-warning-500: #F59E0B;  /* Cảnh báo */
  --color-warning-700: #B45309;

  --color-success-50:  #F0FDF4;
  --color-success-500: #22C55E;  /* Đạt chuẩn */
  --color-success-700: #15803D;

  --color-info-50:  #EFF6FF;
  --color-info-500: #3B82F6;    /* Thông tin */

  /* Score colors - Điểm tuân thủ */
  --score-excellent: #16A34A;   /* 90-100 */
  --score-good:      #65A30D;   /* 75-89 */
  --score-fair:      #D97706;   /* 60-74 */
  --score-poor:      #DC2626;   /* <60 */

  /* Layout */
  --sidebar-width: 256px;
  --topbar-height: 64px;
  --content-max-width: 1280px;
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  --border-radius-xl: 16px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1);
}
```

## 6.2 Typography

```css
/* Font system - Dùng font hệ thống Việt Nam tốt */
--font-primary: 'Be Vietnam Pro', system-ui, sans-serif;  /* Tiêu đề */
--font-body:    'Inter', 'Be Vietnam Pro', sans-serif;     /* Nội dung */
--font-mono:    'JetBrains Mono', 'Fira Code', monospace;  /* Code/số */

/* Scale */
--text-xs:   0.75rem;   /* 12px */
--text-sm:   0.875rem;  /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg:   1.125rem;  /* 18px */
--text-xl:   1.25rem;   /* 20px */
--text-2xl:  1.5rem;    /* 24px */
--text-3xl:  1.875rem;  /* 30px */
```

## 6.3 Layout chính

```
┌──────────────────────────────────────────────────────────────┐
│ TOPBAR (64px)                                                │
│ [Logo] [Breadcrumb]          [Search] [Bell] [Avatar] [Menu]│
├─────────────┬────────────────────────────────────────────────┤
│             │                                                │
│  SIDEBAR    │  MAIN CONTENT AREA                            │
│  (256px)    │                                               │
│             │  Padding: 24px                                │
│  [Nav items]│                                               │
│             │                                               │
│             │                                               │
│             │                                               │
│  ─────────  │                                               │
│  [User info]│                                               │
└─────────────┴────────────────────────────────────────────────┘
```

## 6.4 Score Badge Component

```tsx
// Hiển thị điểm tuân thủ 0-100
<ScoreBadge score={85} size="lg" />

// Colors:
// 90-100: green (Đạt chuẩn xuất sắc)
// 75-89:  lime  (Đạt chuẩn)
// 60-74:  amber (Cần cải thiện)
// <60:    red   (Chưa đạt)
```

## 6.5 Error Severity Badge

```tsx
<SeverityBadge level="critical" />  // Đỏ - Nghiêm trọng
<SeverityBadge level="warning" />   // Vàng - Cảnh báo
<SeverityBadge level="info" />      // Xanh - Thông tin
```

## 6.6 Shared Components (FE-M12)

Danh sách components Agent FE-M12 phải xây dựng TRƯỚC:

```
components/
  ui/
    Button.tsx        (primary, secondary, danger, ghost variants)
    Input.tsx         (với validation, error states)
    Select.tsx        (single, multi)
    Modal.tsx         (với portal, animation)
    Toast.tsx         (success, error, warning, info)
    Table.tsx         (sortable, pagination, selection)
    Skeleton.tsx      (loading states)
    Badge.tsx
    Tabs.tsx
    Accordion.tsx
    Tooltip.tsx
    Dropdown.tsx
    DatePicker.tsx
    FileUploadZone.tsx  (drag & drop)
    ProgressBar.tsx
    Avatar.tsx
    EmptyState.tsx
    ErrorBoundary.tsx
  layout/
    Topbar.tsx
    Sidebar.tsx
    PageWrapper.tsx
    Breadcrumb.tsx
  charts/
    LineChart.tsx
    BarChart.tsx
    PieChart.tsx
    AreaChart.tsx
  feedback/
    ScoreBadge.tsx
    SeverityBadge.tsx
    StatusBadge.tsx
    CheckProgressBar.tsx   (realtime WebSocket)
```

---

# 7. THIẾT KẾ MÀN HÌNH TỪNG MODULE

## FE-M01: Auth & Profile

### 7.1.1 Màn hình Đăng nhập (`/login`)

```
┌────────────────────────────────────────────────────────────┐
│  [Logo Cơ quan]                                            │
│                                                            │
│  HỆ THỐNG AI KIỂM TRA VĂN BẢN                            │
│  Hành chính theo Nghị định 30/2020/NĐ-CP                  │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Đăng nhập bằng tài khoản cơ quan                   │   │
│  │                                                     │   │
│  │  [  Đăng nhập qua SSO (LDAP/Active Directory)  ]   │   │
│  │                                                     │   │
│  │  ─────────────────── hoặc ───────────────────────  │   │
│  │                                                     │   │
│  │  Email công vụ: [_________________________]         │   │
│  │  Mật khẩu:      [_________________________] [👁]   │   │
│  │                                                     │   │
│  │  [ ] Ghi nhớ đăng nhập         [Quên mật khẩu?]   │   │
│  │                                                     │   │
│  │  [         ĐĂNG NHẬP         ]                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ℹ️ Hệ thống nội bộ - Chỉ dành cho cán bộ được phép       │
└────────────────────────────────────────────────────────────┘

States:
- Loading: Nút disabled, spinner
- Error: Red border + message tiếng Việt
- Locked: "Tài khoản bị khóa sau 5 lần sai. Liên hệ IT Admin."
```

### 7.1.2 Trang Hồ sơ (`/profile`)

```
Sections:
1. Thông tin cá nhân (full_name, email, phone, position, department)
2. Đổi mật khẩu (current_pw, new_pw, confirm_pw)
3. Cài đặt thông báo (toggle email/in-app per event type)
4. Bộ quy tắc mặc định (dropdown chọn rule_set mặc định)
5. Múi giờ & Ngôn ngữ
6. Lịch sử đăng nhập (table: thời gian, IP, thiết bị)
7. Phiên đang hoạt động (list + nút thu hồi)
```

---

## FE-M02: Document Upload & Management

### 7.2.1 Màn hình Kiểm tra mới (`/documents/upload`)

```
┌─────────────────────────────────────────────────────────────────┐
│  KIỂM TRA VĂN BẢN MỚI                                [? Help]  │
│                                                                  │
│  Bước 1/3: Tải lên văn bản                                       │
│  ●───────○───────○                                               │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │    📄  Kéo thả file vào đây hoặc nhấn để chọn           │   │
│  │                                                          │   │
│  │    Hỗ trợ: .docx, .pdf (dạng text, không phải scan)     │   │
│  │    Kích thước tối đa: 50MB/file                          │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Tải lên nhiều file cùng lúc: [Chọn nhiều file...]              │
│                                                                  │
│  Bước 2/3: Chọn bộ quy tắc                                       │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ ● Bộ quy tắc Nghị định 30/2020/NĐ-CP (Mặc định)       │     │
│  │ ○ Luận văn tốt nghiệp - Tiêu chuẩn trường ĐH          │     │
│  │ ○ Văn bản quy phạm pháp luật                           │     │
│  │ ○ [Chọn bộ quy tắc khác...]                            │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                  │
│  Bước 3/3: Chọn thư mục (tùy chọn)                              │
│  [ 📁 Không có thư mục ▼ ]                                      │
│                                                                  │
│  [  Hủy  ]                     [  BẮT ĐẦU KIỂM TRA  →  ]      │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2.2 Màn hình Processing (realtime WebSocket)

```
┌────────────────────────────────────────────────────────────┐
│  ĐANG XỬ LÝ VĂN BẢN                                       │
│                                                            │
│  📄 BaoCao_Q1_2026.docx                                   │
│                                                            │
│  ████████████████░░░░░░░░░░░░  65%                        │
│                                                            │
│  ✅ Bóc tách metadata (python-docx)...    Hoàn thành       │
│  ✅ Truy xuất quy chuẩn (RAG Engine)...  Hoàn thành       │
│  🔄 AI phân tích & suy luận (LLM)...    Đang xử lý       │
│  ○  Tổng hợp báo cáo...                 Chờ               │
│                                                            │
│  ⏱️ Thời gian ước tính: ~15 giây                          │
│                                                            │
│  [ Hủy ]              [ Tiếp tục dùng hệ thống ]          │
└────────────────────────────────────────────────────────────┘
```

### 7.2.3 Danh sách văn bản (`/documents`)

```
Toolbar:
  [🔍 Tìm kiếm tên file...] [📁 Thư mục ▼] [📂 Loại ▼] [📅 Ngày ▼] [Kết quả ▼] [+ Kiểm tra mới]

Layout 2 chế độ: [⊞ Lưới] [☰ Danh sách]

Chế độ danh sách:
  Cột: [✓] Tên file | Loại | Ngày | Điểm | Lỗi | Trạng thái | [...]
  
  Row example:
  [✓] 📄 QuyetDinh_TuyenDung_2026.docx | DOCX | 05/05/2026 14:30 | 🟡 72% | ⚠️ 8 lỗi | ✅ Hoàn tất | [Xem] [...]

  Menu [...]:
    - Xem kết quả
    - Kiểm tra lại
    - Tải xuống file gốc
    - Đổi tên
    - Di chuyển vào thư mục
    - Xóa

Pagination: [← Trước] [1] [2] [3] [...] [50] [Sau →] | Hiển thị 20/1000 văn bản
```

---

## FE-M03: Check Results & Error Report

### 7.3.1 Trang kết quả kiểm tra (`/checks/{id}`)

```
┌─────────────────────────────────────────────────────────────────┐
│ ← Quay lại    BaoCao_Q1_2026.docx    [↓ Tải báo cáo ▼] [🔄]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────┐  ┌─────────────────────────────────────────┐    │
│  │           │  │ Tổng hợp kết quả kiểm tra               │    │
│  │    72     │  │                                          │    │
│  │    /100   │  │ 🔴 Nghiêm trọng: 3 lỗi                  │    │
│  │  ──────   │  │ 🟡 Cảnh báo:    5 lỗi                  │    │
│  │ Cần cải   │  │ 🔵 Thông tin:   2 lỗi                  │    │
│  │ thiện     │  │                                          │    │
│  └───────────┘  │ Thời gian xử lý: 18.3 giây              │    │
│                 │ Model AI: llama3:8b                      │    │
│                 │ Bộ quy tắc: NĐ30/2020 (v2.1)           │    │
│                 └─────────────────────────────────────────┘    │
│                                                                  │
│  Filter: [Tất cả(10)] [🔴 Nghiêm trọng(3)] [🟡 Cảnh báo(5)]   │
│          [🔵 Thông tin(2)] | Nhóm: [Font(2)] [Lề(3)] [Tiêu đề(2)] [Khác(3)] │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🔴 [LỖI NGHIÊM TRỌNG] Font chữ không đúng quy định    │   │
│  │─────────────────────────────────────────────────────────│   │
│  │ 📍 Vị trí: Trang 1, Đoạn 3 (Nội dung chính)           │   │
│  │ ❌ Hiện tại: Arial, 12pt                                │   │
│  │ ✅ Yêu cầu:  Times New Roman, 13pt                     │   │
│  │ 💡 Gợi ý sửa: Chọn toàn bộ nội dung (Ctrl+A) →        │   │
│  │    Thay đổi font về Times New Roman, cỡ 13pt           │   │
│  │ 📖 Cơ sở pháp lý: Điều 6, Khoản 2, NĐ30/2020/NĐ-CP   │   │
│  │ 🎯 Độ tin cậy AI: 98%                                  │   │
│  │ [👍 Đúng] [👎 Sai] [💬 Bình luận]                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 🟡 [CẢNH BÁO] Lề trái không đúng quy định             │   │
│  │─────────────────────────────────────────────────────────│   │
│  │ 📍 Vị trí: Toàn bộ văn bản                             │   │
│  │ ❌ Hiện tại: 2.5cm                                     │   │
│  │ ✅ Yêu cầu:  3.0cm (±0.1cm)                            │   │
│  │ [Xem thêm ▼]                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [So sánh với template] [Kiểm tra lại] [Gửi phê duyệt]        │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3.2 So sánh bản gốc vs chuẩn hóa (Diff View)

```
┌──────────────────────────────────────────────────────────────┐
│  SO SÁNH BẢN GỐC VÀ BẢN CHUẨN HÓA                         │
├─────────────────────────┬────────────────────────────────────┤
│  BẢN GỐC                │  BẢN CHUẨN HÓA                    │
├─────────────────────────┼────────────────────────────────────┤
│  Font: Arial 12pt       │  Font: Times New Roman 13pt ✅     │
│  Lề trái: 2.5cm         │  Lề trái: 3.0cm ✅                 │
│  Line spacing: 1.0      │  Line spacing: 1.5 ✅              │
│ [Đoạn có highlight đỏ]  │  [Đoạn đã sửa highlight xanh]     │
└─────────────────────────┴────────────────────────────────────┘

3 thay đổi được đề xuất:  ☑ Font chữ  ☑ Lề trang  ☐ Khoảng cách

[  Hủy  ]  [Áp dụng thay đổi được chọn → Tải xuống .docx]
```

---

## FE-M04: Knowledge Base & Templates

### 7.4.1 Quản lý Knowledge Base (`/admin/knowledge`)

```
QUẢN LÝ CƠ SỞ TRI THỨC (RAG)
[+ Tải lên tài liệu mới]  [🔄 Reindex tất cả]

Thống kê: 📚 12 tài liệu | 🔢 4,832 chunks | 💾 128MB | ✅ 10 sẵn sàng | ⚠️ 1 lỗi | 🔄 1 đang xử lý

Tabs: [Tất cả(12)] [Thể thức(8)] [Nội dung(3)] [Chuyên ngành(1)]

Table:
Tên tài liệu | Mã | Loại | Ngày hiệu lực | Chunks | Trạng thái | [Hành động]

Nghị định 30/2020/NĐ-CP | ND30 | Nghị định | 05/03/2020 | 234 | ✅ Sẵn sàng | [Xem] [⊙ Bật/Tắt] [🗑]
Thông tư 01/2011/TT-BNV  | TT01 | Thông tư  | 15/02/2011 | 156 | ✅ Sẵn sàng | [Xem] [⊙ Bật/Tắt] [🗑]
```

### 7.4.2 Quản lý Bộ quy tắc (`/admin/rules`)

```
BỘ QUY TẮC KIỂM TRA
[+ Tạo bộ quy tắc mới]

Card list:
┌─────────────────────────────────────────────────┐
│ ⭐ NĐ30/2020 - Chuẩn (Mặc định)               │
│ Áp dụng cho: Công văn, Quyết định, Báo cáo      │
│ Phiên bản: v2.1 | 45 quy tắc | 🟢 Hoạt động   │
│ [Xem quy tắc] [Sửa] [Sao chép] [Đặt mặc định]  │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Luận văn tốt nghiệp - ĐHBK                      │
│ Áp dụng cho: Luận văn                           │
│ Phiên bản: v1.0 | 32 quy tắc | 🟢 Hoạt động   │
│ [Xem quy tắc] [Sửa] [Sao chép] [...]           │
└─────────────────────────────────────────────────┘
```

### 7.4.3 Chi tiết bộ quy tắc

```
Accordion groups:
▶ Font chữ (8 quy tắc)
  - [FONT_BODY] Font thân văn bản: Times New Roman 13pt | 🔴 Nghiêm trọng
  - [FONT_HEADING] Font tiêu đề Heading 1: Times New Roman 14pt Bold | 🟡 Cảnh báo
  ...

▶ Lề trang (5 quy tắc)
  - [MARGIN_LEFT] Lề trái: 3.0cm (±0.1cm) | 🔴 Nghiêm trọng
  - [MARGIN_RIGHT] Lề phải: 2.0cm (±0.1cm) | 🟡 Cảnh báo
  ...

▶ Định dạng hành chính VN (12 quy tắc)
  - [VN_QUOC_HIEU] Quốc hiệu: "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" | 🔴 Nghiêm trọng
  ...
```

---

## FE-M05: History, Dashboard & Analytics

### 7.5.1 Dashboard Chuyên viên (`/`)

```
Chào buổi sáng, Nguyễn Văn A! 👋

┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Văn bản     │ │ Kiểm tra    │ │ Tỷ lệ đạt  │ │ Điểm TB    │
│ tháng này   │ │ hôm nay     │ │ chuẩn       │ │ tuân thủ   │
│    28       │ │     5       │ │   78%       │ │   82/100   │
│ ↑12% so T3  │ │             │ │ ↑5% so T3   │ │ ↑3 điểm    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘

[Biểu đồ xu hướng điểm tuân thủ 30 ngày gần đây]

KIỂM TRA GẦN ĐÂY:
[Table: Tên file | Ngày | Điểm | Lỗi | Hành động]

NHANH CHÓNG: [+ Kiểm tra văn bản mới]
```

### 7.5.2 Dashboard Lãnh đạo/Admin

```
TỔNG QUAN PHÒNG BAN - THÁNG 05/2026

Bộ lọc: [Tất cả phòng ban ▼] [Tháng 05/2026 ▼]

4 KPI cards: Tổng văn bản | Tỷ lệ đạt | Điểm TB | Top lỗi phổ biến

┌──────────────────────────────────────────────────────┐
│  [Biểu đồ đường] Xu hướng chất lượng theo tuần      │
└──────────────────────────────────────────────────────┘

┌──────────────────┬───────────────────────────────────┐
│  Top 10 lỗi      │  So sánh phòng ban               │
│  phổ biến nhất   │  [Bar chart ngang]               │
│  [Bar chart]     │                                   │
└──────────────────┴───────────────────────────────────┘

[Xuất báo cáo PDF] [Xuất Excel] [Xuất PowerPoint]
```

---

## FE-M06: Approval Workflow

### 7.6.1 Gửi phê duyệt (Chuyên viên)

```
GỬI VĂN BẢN ĐỂ PHÊ DUYỆT

Văn bản: QuyetDinh_BổNhiệm_2026.docx
Kết quả kiểm tra: 89/100 (Đạt chuẩn)

Người phê duyệt: [Chọn lãnh đạo... ▼]
Ghi chú: [________________________]
Hạn phê duyệt: [Chọn ngày...]

[Hủy]  [Gửi phê duyệt →]
```

### 7.6.2 Danh sách chờ phê duyệt (Lãnh đạo)

```
VĂN BẢN CHỜ PHÊ DUYỆT (5)

Filter: [Chờ xử lý(5)] [Đã duyệt(12)] [Đã từ chối(2)]

Table: Tên file | Người gửi | Gửi lúc | Điểm KT | Hạn | [Hành động]

  QuyetDinh... | Nguyễn V.A | 05/05 10:30 | 89/100 | 06/05 | [Xem] [Duyệt] [Từ chối]
```

---

## FE-M07: Admin - User Management

```
QUẢN LÝ NGƯỜI DÙNG
[+ Tạo tài khoản] [📥 Import Excel] [🔄 Đồng bộ LDAP]

Search: [🔍 Tìm email, tên...]  Filter: [Vai trò ▼] [Phòng ban ▼] [Trạng thái ▼]

Table:
  Họ tên | Email | Vai trò | Phòng ban | Đăng nhập cuối | Trạng thái | [...]

  Nguyễn Văn A | nva@cq.vn | Chuyên viên | Phòng Kế hoạch | 05/05 | 🟢 Hoạt động | [Sửa] [🔒] [...]

Menu [...]: Đặt lại mật khẩu | Xem audit log | Vô hiệu hóa

Drawer "Sửa người dùng":
  - Thông tin cơ bản
  - Vai trò & Phòng ban
  - Hạn mức (văn bản/tháng, dung lượng)
  - Lịch sử đăng nhập
```

---

## FE-M08: Admin - System Settings

```
CÀI ĐẶT HỆ THỐNG

Tabs:
  [Chung] [Email/SMTP] [Bảo mật] [Lưu trữ] [AI Model] [Tích hợp]

Tab "AI Model":
  Model LLM hiện tại: [ llama3:8b ▼ ]
  Trạng thái Ollama: 🟢 Hoạt động | Xem models
  Ngưỡng timeout: [ 30 ] giây
  Concurrent processing: [ 3 ] văn bản

Tab "Bảo mật":
  Chính sách mật khẩu: độ dài tối thiểu, ký tự đặc biệt, thời hạn
  Auto logout: [ 30 ] phút
  Số lần đăng nhập sai: [ 5 ] lần → khóa
  Whitelist IP: [textbox multi-line]

Tab "Lưu trữ":
  MinIO endpoint: [___]
  Giữ lịch sử tối đa: [ 365 ] ngày
  Cảnh báo dung lượng: [ 80 ] %
  Số phiên bản tối đa/tài liệu: [ 10 ]
```

---

## FE-M09: Admin - AI Monitoring

```
GIÁM SÁT & CHẤT LƯỢNG AI

KPI: Precision | Recall | F1-Score | Avg processing time | Cost estimate

┌──────────────────────────────────────────────────────────┐
│  Biểu đồ: Precision/Recall theo tuần                    │
└──────────────────────────────────────────────────────────┘

PHẢN HỒI NGƯỜI DÙNG:
Bị đánh dấu sai (False Positive): 23 trường hợp / tuần
Top loại lỗi AI hay sai nhất: [Bar chart]

AGENTS HEALTH:
Agent | SLA | Avg time | Success rate | Trạng thái
AG01 - Kiểm tra Lề | 2000ms | 450ms | 99.2% | 🟢
AG02 - Kiểm tra Font | 1500ms | 380ms | 98.7% | 🟢
...
```

---

## FE-M10: Notifications & Support

### Notification Center

```
THÔNG BÁO [Đánh dấu tất cả đã đọc]

Filter: [Tất cả] [Chưa đọc(3)] [Hoàn thành] [Cảnh báo]

┌─────────────────────────────────────────────────────────┐
│ 🔔 Kiểm tra hoàn tất                       vừa xong   │
│ QuyetDinh_2026.docx | Điểm: 89/100 | 3 lỗi cần xem   │
│ [Xem kết quả →]                                        │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│ ⚠️ Văn bản có lỗi nghiêm trọng              2 giờ trước│
│ BaoCao_Q1.docx | Font chữ không đúng quy định         │
│ [Xem kết quả →]                                        │
└─────────────────────────────────────────────────────────┘
```

### Hỗ trợ & Phản hồi

```
HỖ TRỢ KỸ THUẬT

[Tài liệu hướng dẫn] [Video hướng dẫn] [FAQ] [Gửi phiếu hỗ trợ]

PHIẾU HỖ TRỢ CỦA TÔI:
TKT-2026-001234 | Lỗi upload PDF | Đang xử lý | 03/05
TKT-2026-001100 | Câu hỏi về báo cáo | Đã giải quyết | 01/05
```

---

## FE-M11: API Developer Portal (`/developer`)

```
CỔNG TÍCH HỢP API

[Tài liệu API (OpenAPI)] [Postman Collection] [Changelog]

API KEYS CỦA TÔI:
┌────────────────────────────────────────────────────────┐
│ Tích hợp QLVB      | rag_k1a2****  | Active | Tạo API Key mới │
│ Quyền: check, upload | Rate: 60/min, 1000/day          │
│ Sử dụng: 234 lần | Lần cuối: 05/05 14:30             │
│ [Thu hồi]                                             │
└────────────────────────────────────────────────────────┘

[+ Tạo API Key mới]

SWAGGER UI: (nhúng Swagger UI cho /openapi.json)
```

---

# 8. LUỒNG XỬ LÝ CHÍNH

## 8.1 Luồng Upload & Check (Happy Path)

```
User                    Frontend              API Gateway         Services
 │                         │                      │                  │
 │ Kéo thả file            │                      │                  │
 ├────────────────────────►│                      │                  │
 │                         │ POST /documents/upload                  │
 │                         ├─────────────────────►│                  │
 │                         │                      │ → Document Svc   │
 │                         │                      │   1. Validate    │
 │                         │                      │   2. Virus scan  │
 │                         │                      │   3. MinIO store │
 │                         │                      │   4. Redis queue │
 │                         │  {doc_id, check_id}  │                  │
 │                         │◄─────────────────────│                  │
 │                         │                      │ → Check Orch Svc │
 │                         │                      │   (async)        │
 │                         │                      │         │        │
 │ WS subscribe(check_id)  │                      │         │ Stage 1: Extract
 │                         │                      │         │ python-docx/MuPDF
 │                         │ WS: progress 30%     │         │        │
 │◄────────────────────────│◄──────────────────── │◄────────│        │
 │                         │                      │         │ Stage 2: RAG
 │                         │ WS: progress 65%     │         │ Qdrant search
 │◄────────────────────────│◄──────────────────── │◄────────│        │
 │                         │                      │         │ Stage 3: LLM
 │                         │ WS: progress 90%     │         │ Ollama infer
 │◄────────────────────────│◄──────────────────── │◄────────│        │
 │                         │                      │         │ Save results
 │                         │ WS: complete         │         │ PostgreSQL
 │◄────────────────────────│◄──────────────────── │◄────────│        │
 │ Navigate to result page │                      │         │        │
 ├────────────────────────►│                      │         │        │
 │                         │ GET /checks/{id}     │         │        │
 │                         ├─────────────────────►│         │        │
 │                         │  CheckResultDto      │         │        │
 │◄────────────────────────│◄─────────────────────│         │        │
 │ Xem báo cáo lỗi        │                      │         │        │
```

## 8.2 Luồng Export Báo cáo

```
User → [Tải báo cáo PDF] → POST /checks/{id}/export/pdf
→ Report Service:
  1. Query check_results + check_errors
  2. Render HTML template (tiếng Việt)
  3. WeasyPrint → PDF
  4. Return binary
→ Browser tải về
```

---

# 9. CẤU TRÚC THƯ MỤC DỰ ÁN

## 9.1 Frontend (React)

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/           # Hình ảnh, fonts
│   ├── components/       # Shared components (FE-M12)
│   │   ├── ui/           # Base UI components
│   │   ├── layout/       # Layout components
│   │   ├── charts/       # Chart components
│   │   └── feedback/     # Domain-specific components
│   ├── modules/          # Feature modules
│   │   ├── auth/         # FE-M01
│   │   ├── documents/    # FE-M02
│   │   ├── checks/       # FE-M03
│   │   ├── knowledge/    # FE-M04
│   │   ├── analytics/    # FE-M05
│   │   ├── approval/     # FE-M06
│   │   ├── admin-users/  # FE-M07
│   │   ├── admin-system/ # FE-M08
│   │   ├── admin-ai/     # FE-M09
│   │   ├── support/      # FE-M10
│   │   └── developer/    # FE-M11
│   ├── hooks/            # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useWebSocket.ts
│   │   ├── useDocuments.ts
│   │   └── ...
│   ├── stores/           # Zustand stores
│   │   ├── authStore.ts
│   │   ├── notificationStore.ts
│   │   └── uiStore.ts
│   ├── lib/              # Utilities
│   │   ├── api.ts        # Axios instance + interceptors
│   │   ├── websocket.ts  # Socket.io client
│   │   ├── queryClient.ts# TanStack Query
│   │   └── utils.ts
│   ├── types/            # TypeScript types (DTOs)
│   │   ├── auth.types.ts
│   │   ├── document.types.ts
│   │   ├── check.types.ts
│   │   └── ...
│   ├── i18n/
│   │   └── vi.json       # Tiếng Việt translations
│   ├── router/
│   │   └── index.tsx     # React Router config
│   ├── App.tsx
│   └── main.tsx
├── .env.example
├── vite.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

## 9.2 Backend (FastAPI)

```
backend/
├── services/
│   ├── auth_service/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── utils/ldap.py
│   ├── document_service/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── models/
│   │   └── utils/minio.py
│   ├── check_orchestration/
│   │   ├── main.py
│   │   ├── celery_app.py
│   │   └── tasks/
│   │       ├── extract.py   # python-docx, PyMuPDF
│   │       ├── rag.py       # RAGFlow query
│   │       └── llm.py       # Ollama inference
│   ├── notification_service/
│   ├── report_service/
│   ├── knowledge_service/
│   └── admin_service/
├── shared/               # Code dùng chung
│   ├── database.py       # SQLAlchemy engine
│   ├── models/           # SQLAlchemy models (SINGLE SOURCE OF TRUTH)
│   ├── schemas/          # Pydantic schemas (DTOs)
│   ├── auth.py           # JWT helpers
│   ├── exceptions.py
│   └── config.py
├── migrations/           # Alembic migrations
├── scripts/
│   ├── seed_data.py      # Dữ liệu mẫu
│   └── init_agents.py    # Khởi tạo AI agents
├── tests/
├── docker-compose.yml
├── docker-compose.prod.yml
└── nginx/
    └── nginx.conf
```

## 9.3 Docker Compose Services

```yaml
# docker-compose.yml (tham khảo)
services:
  nginx:          { build: ./nginx, ports: ["443:443"] }
  frontend:       { build: ./frontend }
  api-gateway:    { build: ./backend/services/api_gateway, port: 8000 }
  auth-service:   { build: ./backend/services/auth_service, port: 8001 }
  document-svc:   { build: ./backend/services/document_service, port: 8002 }
  check-orch:     { build: ./backend/services/check_orchestration, port: 8003 }
  notif-svc:      { build: ./backend/services/notification_service, port: 8004 }
  admin-svc:      { build: ./backend/services/admin_service, port: 8005 }
  report-svc:     { build: ./backend/services/report_service, port: 8006 }
  knowledge-svc:  { build: ./backend/services/knowledge_service, port: 8007 }
  celery-worker:  { build: ./backend, command: "celery -A shared.celery worker" }
  postgresql:     { image: postgres:16, volume: ./data/postgres }
  redis:          { image: redis:7-alpine }
  minio:          { image: minio/minio, volume: ./data/minio }
  qdrant:         { image: qdrant/qdrant, volume: ./data/qdrant }
  ollama:         { image: ollama/ollama, volume: ./data/ollama, runtime: nvidia }
  ragflow:        { image: ragflowproject/ragflow, volume: ./data/ragflow }
```

---

# APPENDIX A: Danh sách Epics → Modules

| Epic | Module FE | Module BE |
|---|---|---|
| EP01 – Xác thực & Đăng nhập | FE-M01, FE-M07 | BE-M01, BE-M08 |
| EP02 – Tải lên & Quản lý văn bản | FE-M02 | BE-M02 |
| EP03 – Kiểm tra thể thức | FE-M03 | BE-M03, BE-M04 |
| EP04 – Kiểm tra đặc thù hành chính VN | FE-M03 | BE-M04 |
| EP05 – Chuẩn hóa tự động | FE-M03 | BE-M04 |
| EP06 – Knowledge Base RAG | FE-M04 | BE-M05 |
| EP07 – Lịch sử & Báo cáo | FE-M05 | BE-M06 |
| EP08 – Phân quyền & Workflow | FE-M06 | BE-M10 |
| EP09 – Template | FE-M04 | BE-M05 |
| EP10 – UX/UI | FE-M12 | - |
| EP11 – Thông báo | FE-M10 | BE-M07 |
| EP12 – Bảo mật & Tuân thủ | FE-M08 | BE-M01, BE-M08 |
| EP13 – Cài đặt hệ thống | FE-M08 | BE-M08 |
| EP14 – Hỗ trợ & Phản hồi | FE-M10 | BE-M08 |
| EP15 – Tích hợp API | FE-M11 | BE-M09 |
| EP16 – Chuyên ngành | FE-M03 | BE-M04, BE-M05 |
| EP17 – Kiểm tra chéo | FE-M03 | BE-M04 |
| EP18 – Cộng tác | FE-M05 | BE-M10 |
| EP19 – Quản lý người dùng nâng cao | FE-M07 | BE-M08 |
| EP20 – Giám sát AI | FE-M09 | BE-M04 |
| EP21 – Quản lý phiên bản | FE-M02 | BE-M02 |
| EP22 – Onboarding | FE-M10 | - |
| EP23 – Accessibility | FE-M12 | - |
| EP24 – Xuất dữ liệu | FE-M05 | BE-M06 |

---

# APPENDIX B: Sprint Plan (Must Have ưu tiên)

## Sprint 1 (Foundation)
**BE:** BE-M01 (Auth full), BE-M02 (Upload/basic CRUD), BE-M03 (Check pipeline), BE-M04 (AI pipeline), BE-M08 (User management)
**FE:** FE-M12 (Shared components), FE-M01 (Auth), FE-M02 (Upload + list), FE-M03 (Basic results), FE-M07 (Admin users)

## Sprint 2 (Core Features)
**BE:** BE-M05 (Knowledge + Rules), BE-M06 (Reports), BE-M07 (Notifications), BE-M09 (API Gateway)
**FE:** FE-M03 (Full error report + export), FE-M04 (Knowledge + Templates), FE-M05 (Dashboard + History), FE-M08 (Settings), FE-M10 (Notifications), FE-M11 (API Portal)

## Sprint 3 (Advanced)
**BE:** BE-M10 (Workflow + Collaboration)
**FE:** FE-M06 (Approval), FE-M09 (AI Monitoring)

## Sprint 4-5 (Could Have)
- EP16 (Chuyên ngành), EP18 (Cộng tác nâng cao), EP23 (Accessibility), EP24 (Kafka/BI integration)

---

*Tài liệu này là nguồn tham chiếu duy nhất (Single Source of Truth) cho tất cả Agents. Mọi thay đổi thiết kế phải được PM phê duyệt trước khi cập nhật.*

**Version:** 1.0 | **Ngày tạo:** 05/05/2026 | **PM:** [Tên PM]
