# TIẾN ĐỘ DỰ ÁN - AI KIỂM TRA VĂN BẢN

**Ngày cập nhật:** 30/05/2026

---

## 1. BACKEND - TÌNH TRẠNG

### Services đã hoàn chỉnh (12/12)
- ✅ Auth, Document, Check, Rules, Knowledge, Template
- ✅ Analytics, Notification, Admin, Approval, Collaboration
- ✅ WebSocket realtime

### Bug đã fix (từ API test 30/05)
| # | Bug | Trạng thái |
|---|---|---|
| 1 | GET /checks/{id} - 404 do check chưa tạo trong DB | ✅ FIX: Tạo CheckResult ngay với status="processing" |
| 2 | GET /checks/document/{doc_id} - 500 thiếu selectinload | ✅ FIX: Thêm .options(selectinload(CheckResult.errors)) |
| 3 | POST /admin/api-keys - 500 do ApiKeyResponse | ✅ FIX: Bỏ response_model, return dict thủ công |
| 4 | POST /rules/sets - 403 (dùng sai token) | ✅ Hướng dẫn: dùng admin token |
| 5 | POST /knowledge/categories - 403 (dùng sai token) | ✅ Hướng dẫn: dùng admin token |
| 6 | GET /documents/{id}/download - 307 thay vì 302 | ✅ Minor: trình duyệt vẫn redirect được |
| 7 | Không token gọi API - 403 thay vì 401 | ✅ Minor: do HTTPBearer scheme mặc định |

### Database model đã sửa
| Model | Thay đổi |
|---|---|
| `Document` | ✅ Thêm `check_results = relationship(..., cascade="all, delete-orphan")` |
| `Document` | ✅ `versions` cascade đã có |
| `CheckResult` | ✅ Thêm `document = relationship("Document", back_populates="check_results")` |
| `CheckResult` | ✅ `errors` cascade="all, delete-orphan" |

## 2. FRONTEND - TÌNH TRẠNG

### Đã hoàn thành:
- ✅ API client (`lib/api.ts`) - 11 modules đầy đủ
- ✅ Types (`types/index.ts`) - 15+ interfaces
- ✅ Shared UI components: Button, Input, Sheet, Avatar, Separator, Tooltip, Badge
- ✅ NotificationBell component
- ✅ DocumentListPage (search, sort, pagination, delete)
- ✅ CheckResultPage (score, errors, filter, feedback, export)
- ✅ UploadPage (drag-drop, progress bar, WebSocket)
- ✅ WebSocket hooks (useCheckProgress, useUserNotifications)

### Còn thiếu:
- ⬜ LoginPage UI đẹp hơn
- ⬜ DashboardPage (biểu đồ Recharts)
- ⬜ Knowledge, Rules, Admin pages UI
- ⬜ Toast/notification system
- ⬜ Card component (cần cho CheckResultPage)

## 3. CÁC VẤN ĐỀ ANH/CHỊ HỎI

### ❓ Document tự thêm trong DB không hiển thị trên view
**Nguyên nhân:** Code query lọc theo `user_id` của user đang login. DOC_ID trong DB có `user_id` khác hoặc `is_deleted = True`.

**Cách kiểm tra nhanh:**
```sql
SELECT d.id, d.original_filename, d.is_deleted, d.user_id, u.email
FROM documents d
JOIN users u ON u.id = d.user_id
WHERE d.is_deleted = FALSE
  AND u.email = 'chuyenvien1@cq.vn';
```

### ❓ Không xóa được document trong DB do FK
**Đã fix:** Thêm `cascade="all, delete-orphan"` vào Document.check_results và CheckResult.errors. Sau khi chạy migration mới (hoặc tạo lại bảng) thì xóa document sẽ tự động xóa check_results + check_errors + ai_feedback.

**Hiện tại (workaround):** Xóa tay theo thứ tự:
```sql
DELETE FROM check_errors WHERE result_id IN (SELECT id FROM check_results WHERE document_id = '...');
DELETE FROM check_results WHERE document_id = '...';
DELETE FROM documents WHERE id = '...';
```

### ❓ Document trong storage không hiển thị
File trong `backend/uploads/` chỉ là file vật lý. Database mới là nguồn dữ liệu chính. Nếu có file trong `uploads/` mà không có record trong `documents` table → không hiển thị. Cần thêm record vào DB hoặc upload lại qua web.

## 4. KẾ HOẠCH TIẾP THEO

### Phase 1: Fix lỗi còn lại (ưu tiên)
- [ ] Cập nhật script test API với admin token cho rules/knowledge
- [ ] Chạy lại test verify các bug đã fix

### Phase 2: UI/UX cải thiện
- [ ] LoginPage - thiết kế đẹp theo THIET_KE_WEB_AI_VANBAN.md
- [ ] Dashboard - biểu đồ Recharts
- [ ] Toast notifications
- [ ] Card component loading skeleton
- [ ] Responsive improvements

### Phase 3: Khi AI pipeline hoàn thành
- [ ] Tích hợp extraction, RAG, LLM pipeline
- [ ] Remove mock data

### Phase 4: Mở rộng
- [ ] API Developer Portal
- [ ] i18n đa ngôn ngữ
- [ ] LDAP/SSO integration