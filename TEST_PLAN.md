# KẾ HOẠCH KIỂM THỬ (TEST PLAN) HỆ THỐNG AI KIỂM TRA VĂN BẢN

**Phiên bản:** 1.0 | **Ngày:** 29/05/2026

---

## MỤC LỤC
1. [Môi trường kiểm thử](#1-môi-trường-kiểm-thử)
2. [Backend API Tests (Agent tự động)](#2-backend-api-tests-agent-tự-động)
3. [Frontend Visual Tests (Người dùng test)](#3-frontend-visual-tests-người-dùng-test)
4. [Integration Tests (Luồng nghiệp vụ)](#4-integration-tests)
5. [Mẫu báo cáo lỗi](#5-mẫu-báo-cáo-lỗi)

---

## 1. MÔI TRƯỜNG KIỂM THỬ

### Yêu cầu
| Thành phần | Yêu cầu |
|---|---|
| **Backend** | Python 3.11+, PostgreSQL 16, Redis |
| **Frontend** | Node 18+, npm |
| **Trình duyệt** | Chrome 120+ hoặc Firefox 120+ |

### Cách chạy

**1. Khởi động Backend:**
```bash
cd backend
# Cài dependencies (lần đầu)
pip install -r requirements.txt
pip install weasyprint  # Cho export PDF

# Chạy server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**2. Khởi động Frontend:**
```bash
cd frontend
npm install   # lần đầu
npm run dev   # http://localhost:5173
```

**3. Kiểm tra health:**
```
Backend:  http://localhost:8000/api/v1/health
Swagger:  http://localhost:8000/api/docs
Frontend: http://localhost:5173
```

### Tài khoản test (seed data)
| Role | Email | Password |
|---|---|---|
| OFFICER | user@test.com | 123456 |
| LEADER | leader@test.com | 123456 |
| IT_ADMIN | admin@test.com | 123456 |

---

## 2. BACKEND API TESTS (Agent tự động)

Script test: `backend/scripts/test_api.py`

Chạy script:
```bash
cd backend
python scripts/test_api.py
```

Script sẽ tự động test các API và in ra kết quả PASS/FAIL.

### 2.1 Auth APIs (7 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 1 | POST /auth/login | user@test.com / 123456 | 200 + token |
| 2 | POST /auth/login | Sai mật khẩu | 401 |
| 3 | POST /auth/register | Email mới | 201 |
| 4 | POST /auth/register | Email trùng | 400 |
| 5 | GET /auth/me | Có token | 200 + user info |
| 6 | PUT /auth/me | Update full_name | 200 |
| 7 | POST /auth/refresh | Refresh token | 200 + new token |

### 2.2 Document APIs (12 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 8 | POST /documents/upload | Upload .docx file | 201 + check_id |
| 9 | POST /documents/upload | Upload file sai định dạng (.exe) | 400 |
| 10 | GET /documents/ | List documents | 200 + array |
| 11 | GET /documents/{id} | Get document by ID | 200 |
| 12 | GET /documents/{id} | ID không tồn tại | 404 |
| 13 | PUT /documents/{id} | Update display_name | 200 |
| 14 | DELETE /documents/{id} | Soft delete | 200 |
| 15 | POST /documents/folders | Tạo folder | 201 |
| 16 | GET /documents/folders | List folders | 200 |
| 17 | DELETE /documents/folders/{id} | Xóa folder rỗng | 204 |
| 18 | GET /documents/{id}/versions | List versions | 200 |
| 19 | GET /documents/{id}/download | Download file | 302 redirect |

### 2.3 Check APIs (8 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 20 | POST /checks | Create check cho document | 201 + check_id |
| 21 | GET /checks/{id} | Lấy kết quả (đang processing) | 200 |
| 22 | GET /checks/document/{doc_id} | List checks của document | 200 |
| 23 | POST /checks/{id}/errors/{eid}/feedback | Feedback "Đúng" | 200 |
| 24 | POST /checks/{id}/errors/{eid}/feedback | Feedback "Sai" | 200 |
| 25 | GET /checks/{id}/export/json | Export JSON | 200 |
| 26 | GET /checks/{id}/normalize/preview | Preview normalize | 200 |
| 27 | POST /checks/{id}/recheck | Recheck | 201 |

### 2.4 Rules APIs (8 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 28 | GET /rules/sets | List rule sets | 200 |
| 29 | GET /rules/sets/{id} | Get rule set chi tiết + rules | 200 |
| 30 | POST /rules/sets | Tạo rule set mới | 201 |
| 31 | PUT /rules/sets/{id} | Update rule set | 200 |
| 32 | POST /rules/sets/{id}/set-default | Set default | 200 |
| 33 | POST /rules/sets/{id}/clone | Clone rule set | 201 |
| 34 | POST /rules/sets/{sid}/rules | Tạo rule mới | 201 |
| 35 | PUT /rules/{id} | Update rule | 200 |

### 2.5 Knowledge APIs (6 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 36 | GET /knowledge/categories | List categories | 200 |
| 37 | POST /knowledge/categories | Tạo category | 201 |
| 38 | GET /knowledge/documents | List documents | 200 |
| 39 | GET /knowledge/stats | Get stats | 200 |
| 40 | POST /knowledge/documents | Upload KB document | 201 |
| 41 | PUT /knowledge/documents/{id} | Update document | 200 |

### 2.6 Template APIs (4 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 42 | GET /templates | List templates | 200 |
| 43 | GET /templates/{id} | Get template detail | 200 |
| 44 | POST /templates | Tạo template (cần BIZ_ADMIN) | 201/403 |
| 45 | GET /templates/{id}/download | Download template | 302 |

### 2.7 Approval APIs (4 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 46 | POST /approval/requests | Tạo approval request | 201 |
| 47 | GET /approval/requests/pending | List pending | 200 |
| 48 | PUT /approval/requests/{id} | Approve | 200 |
| 49 | PUT /approval/requests/{id} | Reject | 200 |

### 2.8 Notification APIs (2 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 50 | GET /notifications/ | List notifications | 200 |
| 51 | POST /notifications/mark-read | Mark as read | 200 |

### 2.9 Admin APIs (10 tests)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 52 | GET /admin/users | List users | 200 |
| 53 | POST /admin/users | Tạo user mới | 201 |
| 54 | PUT /admin/users/{id} | Update user | 200 |
| 55 | POST /admin/users/{id}/lock | Lock user | 200 |
| 56 | POST /admin/users/{id}/unlock | Unlock user | 200 |
| 57 | POST /admin/users/{id}/reset-password | Reset password | 200 |
| 58 | GET /admin/settings | List settings | 200 |
| 59 | GET /admin/audit-logs | List audit logs | 200 |
| 60 | GET /admin/health | System health | 200 |
| 61 | POST /admin/api-keys | Tạo API key | 201 |

### 2.10 Analytics API (1 test)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 62 | GET /analytics/dashboard | Dashboard stats | 200 |

### 2.11 WebSocket Test (1 test)

| # | Endpoint | Test case | Expected |
|---|---|---|---|
| 63 | WS /ws/check/{check_id} | Connect + receive progress | Kết nối OK |

---

## 3. FRONTEND VISUAL TESTS (Người dùng test)

### 3.1 Auth Pages

| # | Màn hình | Test case | Expected | Kết quả |
|---|---|---|---|---|
| F1 | Login | Mở /login | Hiển thị form login đẹp, có logo | ⬜ |
| F2 | Login | Nhập user@test.com / 123456 | Chuyển đến /documents | ⬜ |
| F3 | Login | Nhập sai mật khẩu | Toast/alert lỗi "Email hoặc mật khẩu không đúng" | ⬜ |
| F4 | Login | Nhập email không tồn tại | Toast lỗi | ⬜ |
| F5 | Login | Click "Quên mật khẩu?" | Chuyển đến forgot password | ⬜ |
| F6 | App | Load trang với token hết hạn | Tự động refresh token | ⬜ |

### 3.2 Document List (Trang chính)

| # | Màn hình | Test case | Expected | Kết quả |
|---|---|---|---|---|
| F7 | /documents | Load danh sách | Hiển thị table/list documents | ⬜ |
| F8 | /documents | Có search box | Gõ tên file → filter đúng | ⬜ |
| F9 | /documents | Click sort cột | Sort theo tên/ngày | ⬜ |
| F10 | /documents | Click phân trang | Chuyển trang | ⬜ |
| F11 | /documents | Click icon Xóa | Confirm + xóa thành công | ⬜ |
| F12 | /documents | Click icon Download | Tải file về | ⬜ |
| F13 | /documents | Click "Kiểm tra mới" | Chuyển đến /upload | ⬜ |
| F14 | /documents | Empty state (không có document) | Hiển thị icon + text "Chưa có văn bản nào" | ⬜ |

### 3.3 Upload Page

| # | Màn hình | Test case | Expected | Kết quả |
|---|---|---|---|---|
| F15 | /upload | Kéo thả file .docx | Hiển thị tên file | ⬜ |
| F16 | /upload | Kéo thả file .pdf | Hiển thị tên file | ⬜ |
| F17 | /upload | Kéo thả file sai (.exe, .txt) | Báo lỗi định dạng | ⬜ |
| F18 | /upload | Click "Upload & Kiểm tra" | Hiện progress bar | ⬜ |
| F19 | /upload | Progress bar chạy | Các stage: extracting → rag → llm → done | ⬜ |
| F20 | /upload | Hoàn thành | Hiện nút "Xem kết quả chi tiết" | ⬜ |
| F21 | /upload | Click "Xem kết quả" | Chuyển đến trang kết quả | ⬜ |

### 3.4 Check Result Page

| # | Màn hình | Test case | Expected | Kết quả |
|---|---|---|---|---|
| F22 | /checks/{id} | Load kết quả | Hiển thị score + error list | ⬜ |
| F23 | /checks/{id} | Score badge | Màu đúng: >=90 xanh, 75-89 lime, 60-74 vàng, <60 đỏ | ⬜ |
| F24 | /checks/{id} | Card tổng hợp | Đúng số lỗi: critical/warning/info | ⬜ |
| F25 | /checks/{id} | Filter lỗi | Click "Nghiêm trọng" → chỉ hiện critical errors | ⬜ |
| F26 | /checks/{id} | Error card | Hiển thị: severity badge, description, vị trí, current/expected, fix | ⬜ |
| F27 | /checks/{id} | Feedback buttons | Click 👍 Đúng → button active | ⬜ |
| F28 | /checks/{id} | Feedback buttons | Click 👎 Sai → button active | ⬜ |
| F29 | /checks/{id} | Export JSON | Tải file JSON về | ⬜ |
| F30 | /checks/{id} | Export PDF | Tải file PDF về (có layout báo cáo) | ⬜ |
| F31 | /checks/{id} | Click "Kiểm tra lại" | Tạo check mới | ⬜ |
| F32 | /checks/{id} | 0 errors | Hiển thị "Không có lỗi nào!" | ⬜ |

### 3.5 Dashboard

| # | Màn hình | Test case | Expected | Kết quả |
|---|---|---|---|---|
| F33 | /dashboard | 4 KPI cards | Tổng văn bản, hôm nay, tỷ lệ đạt, điểm TB | ⬜ |
| F34 | /dashboard | Trend chart | Biểu đồ 7 ngày | ⬜ |

### 3.6 Navigation & Layout

| # | Màn hình | Test case | Expected | Kết quả |
|---|---|---|---|---|
| F35 | Layout | Sidebar | Hiển thị menu cho đúng role | ⬜ |
| F36 | Layout | User dropdown | Click avatar → Hồ sơ, Cài đặt, Đăng xuất | ⬜ |
| F37 | Layout | Notification bell | Click → dropdown notifications | ⬜ |
| F38 | Layout | Responsive | Resize → sidebar ẩn, hamburger menu | ⬜ |
| F39 | /profile | Load trang | Hiển thị thông tin user | ⬜ |

### 3.7 Admin Pages

| # | Màn hình | Test case | Expected | Kết quả |
|---|---|---|---|---|
| F40 | /admin/users | List users | Table users | ⬜ |
| F41 | /admin/users | Search/filter users | Lọc đúng | ⬜ |
| F42 | /admin/users | Lock/Unlock user | Click lock → user bị khóa | ⬜ |
| F43 | /admin/audit-logs | List logs | Hiển thị audit log | ⬜ |

### 3.8 Knowledge & Rules Pages

| # | Màn hình | Test case | Expected | Kết quả |
|---|---|---|---|---|
| F44 | /knowledge | Load trang | Hiển thị KB documents | ⬜ |
| F45 | /knowledge | Stats | Hiển thị tổng quan KB | ⬜ |
| F46 | /rules | Load trang | List rule sets | ⬜ |
| F47 | /rules/{id} | Rule detail | Rules grouped by category | ⬜ |

---

## 4. INTEGRATION TESTS

Test luồng nghiệp vụ hoàn chỉnh:

### Test 1: Luồng Chuyên viên (OFFICER)
```
Login → Upload .docx → Chờ AI check → Xem kết quả → Feedback → Export PDF
```
| Bước | Mô tả | Expected |
|---|---|---|
| 1 | Login OFFICER user@test.com | Success |
| 2 | Upload file BaoCao.docx | 201 + check_id |
| 3 | Chờ progress → done | WS progress đúng stages |
| 4 | Click "Xem kết quả" | Trang kết quả đầy đủ |
| 5 | Feedback 1 lỗi 👍 | Ghi nhận |
| 6 | Export PDF | File PDF tải về |

### Test 2: Luồng Phê duyệt (OFFICER → LEADER)
```
OFFICER: Gửi phê duyệt → LEADER login → Xem → Duyệt/Từ chối
```

### Test 3: Luồng Admin
```
Admin login → CRUD users → Lock user → Xem audit logs → Health check
```

### Test 4: Permission Test
| Test case | Expected |
|---|---|
| OFFICER truy cập /admin/users | 403 Forbidden |
| OFFICER xem document không phải của mình | 404 (không leak data) |
| Không token gọi API | 401 |

---

## 5. MẪU BÁO CÁO LỖI

Khi phát hiện lỗi, ghi lại theo mẫu:

```markdown
## [BUG-001] Tiêu đề lỗi
- **Mức độ:** [Critical/Major/Minor]
- **Module:** [Auth/Document/Check/Frontend/...]
- **Mô tả:** Mô tả ngắn gọn
- **Steps:**
  1. Bước 1
  2. Bước 2
- **Actual:** Kết quả hiện tại
- **Expected:** Kết quả mong đợi
- **Screenshot:** [link ảnh nếu có]
```

### Gợi ý check UI (vì giao diện còn thô):
- [ ] Các button có hover effect không?
- [ ] Loading spinner khi fetch data?
- [ ] Toast thông báo khi success/error?
- [ ] Màu sắc đồng bộ giữa các trang?
- [ ] Font chữ tiếng Việt hiển thị đẹp?
- [ ] Responsive trên mobile?
- [ ] Empty state khi không có data?
- [ ] Error state khi API fail?

---

## Sau khi test xong

Kế hoạch tiếp theo:
1. Fix tất cả bugs phát hiện
2. Cải thiện UI/UX (theo thiết kế trong THIET_KE_WEB_AI_VANBAN.md Section 6)
3. Tích hợp AI/RAG pipeline (khi bạn của anh/chị hoàn thành)
4. Mở rộng tính năng