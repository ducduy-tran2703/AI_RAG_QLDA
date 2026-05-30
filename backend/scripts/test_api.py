"""
Script test tự động cho backend APIs.
Chạy: python scripts/test_api.py

Yêu cầu: backend đang chạy ở http://localhost:8000
"""

import requests
import json
import sys
import os
import time
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
PASS = "\u2705 PASS"
FAIL = "\u274c FAIL"
SKIP = "\u23ed\ufe0f SKIP"

pass_count = 0
fail_count = 0

def log_test(num, name, status, detail=""):
    global pass_count, fail_count
    if status == PASS:
        pass_count += 1
    elif status == FAIL:
        fail_count += 1
    print(f"  [{num:2d}] {status} {name}")
    if detail:
        print(f"       {detail}")

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def req(method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    try:
        r = requests.request(method, url, timeout=15, **kwargs)
        return r.status_code, r
    except requests.exceptions.ConnectionError:
        return 0, None
    except Exception as e:
        return -1, str(e)

# ==================== MAIN ====================
print(f"\n{'#'*60}")
print(f"  BACKEND API TEST SCRIPT")
print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print(f"{'#'*60}")
print(f"\n  Base URL: {BASE_URL}")

# Check connection
st, r = req("GET", "/health")
if st != 200:
    print(f"\n  {FAIL} Khong the ket noi den backend!")
    print(f"  Chay: uvicorn app.main:app --reload --port 8000")
    sys.exit(1)
print(f"  {PASS} Backend dang hoat dong")

# Login
TEST_EMAIL = "chuyenvien1@cq.vn"
TEST_PASSWORD = "Officer@123"

st, r = req("POST", "/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
if st == 200:
    data = r.json()
    TOKEN = data["access_token"]
    REFRESH_TOKEN = data["refresh_token"]
    USER_ID = data["user"]["id"]
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}
    print(f"  {PASS} Login: {TEST_EMAIL}")
else:
    print(f"  {FAIL} Khong login duoc. Ket thuc.")
    sys.exit(1)

# Admin login
st, r = req("POST", "/auth/login", json={"email": "admin@cq.vn", "password": "Admin@123"})
ADMIN_TOKEN = r.json()["access_token"] if st == 200 else TOKEN
ADMIN_H = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

DOC_ID = None
FOLDER_ID = None
CHECK_ID = None
RULE_SET_ID = None
RULE_ID = None
CAT_ID = None
APPROVAL_ID = None

# ===== 2.1 AUTH =====
print_header("2.1 AUTH APIs")
log_test(1, "POST /auth/login - Thanh cong", PASS)

st, r = req("POST", "/auth/login", json={"email": TEST_EMAIL, "password": "wrong"})
log_test(2, "POST /auth/login - Sai mat khau (expected 401)", 
         PASS if st == 401 else FAIL, f"Got {st}")

new_email = f"t{datetime.now().strftime('%H%M%S')}@test.com"
st, r = req("POST", "/auth/register", json={"email": new_email, "full_name": "Test", "password": "12345678"})
log_test(3, "POST /auth/register - Tao moi (expected 201)", 
         PASS if st == 201 else FAIL, f"Got {st}")

st, r = req("POST", "/auth/register", json={"email": TEST_EMAIL, "full_name": "Test", "password": "12345678"})
log_test(4, "POST /auth/register - Email trung (expected 400)", 
         PASS if st == 400 else FAIL, f"Got {st}")

st, r = req("GET", "/auth/me", headers=HEADERS)
log_test(5, "GET /auth/me (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

st, r = req("PUT", "/auth/me", headers=HEADERS, json={"full_name": "Updated"})
log_test(6, "PUT /auth/me (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

st, r = req("POST", "/auth/refresh", json={"refresh_token": REFRESH_TOKEN})
log_test(7, "POST /auth/refresh (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

# ===== 2.2 DOCUMENTS =====
print_header("2.2 DOCUMENT APIs")

tmp = os.path.join(os.environ.get('TEMP', '.'), 'test_doc.docx')
with open(tmp, 'w') as f: f.write("test")
with open(tmp, 'rb') as f:
    st, r = req("POST", "/documents/upload",
        headers={**HEADERS, "Content-Type": None},
        files={"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
if st == 201:
    DOC_ID = r.json()["document"]["id"]
    log_test(8, "POST /documents/upload - .docx (expected 201)", PASS)
else:
    log_test(8, "POST /documents/upload", FAIL, f"Got {st}: {r.text[:150] if st > 0 else 'Failed'}")
try: os.remove(tmp)
except: pass

with open(tmp + ".exe", 'w') as f: f.write("fake")
with open(tmp + ".exe", 'rb') as f:
    st, r = req("POST", "/documents/upload",
        headers={**HEADERS, "Content-Type": None},
        files={"file": ("test.exe", f, "application/x-msdownload")})
log_test(9, "POST /documents/upload - File sai (expected 400)", 
         PASS if st == 400 else FAIL, f"Got {st}")
try: os.remove(tmp + ".exe")
except: pass

st, r = req("GET", "/documents/", headers=HEADERS)
log_test(10, "GET /documents/ (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

if DOC_ID:
    st, r = req("GET", f"/documents/{DOC_ID}", headers=HEADERS)
    log_test(11, "GET /documents/{id} (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("PUT", f"/documents/{DOC_ID}", headers=HEADERS, json={"display_name": "Updated Doc"})
    log_test(12, "PUT /documents/{id} (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
else:
    log_test(11, "GET /documents/{id}", SKIP)
    log_test(12, "PUT /documents/{id}", SKIP)

st, r = req("GET", "/documents/00000000-0000-0000-0000-000000000000", headers=HEADERS)
log_test(13, "GET /documents/{id} - ID khong ton tai (expected 404)", 
         PASS if st == 404 else FAIL, f"Got {st}")

# Folders
st, r = req("POST", "/documents/folders", headers=HEADERS, json={"name": "Test Folder"})
FOLDER_ID = r.json().get("id") if st == 201 else None
log_test(14, "POST /documents/folders (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")

st, r = req("GET", "/documents/folders", headers=HEADERS)
log_test(15, "GET /documents/folders (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

if FOLDER_ID:
    st, r = req("DELETE", f"/documents/folders/{FOLDER_ID}", headers=HEADERS)
    log_test(16, "DELETE /documents/folders/{id} (expected 204)", PASS if st == 204 else FAIL, f"Got {st}")
else:
    log_test(16, "DELETE /documents/folders/{id}", SKIP)

# Versions
if DOC_ID:
    st, r = req("GET", f"/documents/{DOC_ID}/versions", headers=HEADERS)
    log_test(17, "GET /documents/{id}/versions (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("GET", f"/documents/{DOC_ID}/download", headers=HEADERS, allow_redirects=False)
    log_test(18, "GET /documents/{id}/download (expected 302)", PASS if st in (200, 302) else FAIL, f"Got {st}")
else:
    log_test(17, "GET /documents/{id}/versions", SKIP)
    log_test(18, "GET /documents/{id}/download", SKIP)

# Delete doc
if DOC_ID:
    with open(tmp, 'w') as f: f.write("delete")
    with open(tmp, 'rb') as f:
        st2, r2 = req("POST", "/documents/upload",
            headers={**HEADERS, "Content-Type": None},
            files={"file": ("del.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    if st2 == 201:
        did = r2.json()["document"]["id"]
        st, r = req("DELETE", f"/documents/{did}", headers=HEADERS)
        log_test(19, "DELETE /documents/{id} - Xoa mem (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    else:
        log_test(19, "DELETE /documents/{id}", SKIP)
    try: os.remove(tmp)
    except: pass
else:
    log_test(19, "DELETE /documents/{id}", SKIP)

# ===== 2.3 CHECKS =====
print_header("2.3 CHECK APIs")

if DOC_ID:
    st, r = req("POST", "/checks", headers=HEADERS, json={"document_id": DOC_ID})
    CHECK_ID = r.json().get("check_id") if st == 201 else None
    log_test(20, "POST /checks (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")
else:
    log_test(20, "POST /checks", SKIP)

if CHECK_ID:
    time.sleep(10)  # wait for mock check
    st, r = req("GET", f"/checks/{CHECK_ID}", headers=HEADERS)
    d = r.json() if st == 200 else {}
    log_test(21, "GET /checks/{id} (expected 200)", PASS if st == 200 else FAIL, 
             f"Got {st}, score={d.get('score','N/A')}, errors={len(d.get('errors',[]))}")
else:
    log_test(21, "GET /checks/{id}", SKIP)

if DOC_ID:
    st, r = req("GET", f"/checks/document/{DOC_ID}", headers=HEADERS)
    log_test(22, "GET /checks/document/{doc_id} (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
else:
    log_test(22, "GET /checks/document/{doc_id}", SKIP)

# Feedback
if CHECK_ID:
    st, r = req("GET", f"/checks/{CHECK_ID}", headers=HEADERS)
    if st == 200:
        errs = r.json().get("errors", [])
        if errs:
            eid = errs[0]["id"]
            st, r = req("POST", f"/checks/{CHECK_ID}/errors/{eid}/feedback",
                headers=HEADERS, json={"is_correct": True})
            log_test(23, "POST /checks/{id}/errors/{eid}/feedback - Đung (expected 200)", 
                     PASS if st == 200 else FAIL, f"Got {st}")
            st, r = req("POST", f"/checks/{CHECK_ID}/errors/{eid}/feedback",
                headers=HEADERS, json={"is_correct": False})
            log_test(24, "POST /checks/{id}/errors/{eid}/feedback - Sai (expected 200)", 
                     PASS if st == 200 else FAIL, f"Got {st}")
        else:
            log_test(23, "POST feedback", SKIP, "Khong co errors")
            log_test(24, "POST feedback", SKIP)
    else:
        log_test(23, "POST feedback", SKIP)
        log_test(24, "POST feedback", SKIP)
else:
    log_test(23, "POST feedback", SKIP)
    log_test(24, "POST feedback", SKIP)

if CHECK_ID:
    st, r = req("GET", f"/checks/{CHECK_ID}/export/json", headers=HEADERS)
    log_test(25, "GET /checks/{id}/export/json (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("POST", f"/checks/{CHECK_ID}/recheck", headers=HEADERS)
    log_test(26, "POST /checks/{id}/recheck (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")
else:
    log_test(25, "GET /checks/{id}/export/json", SKIP)
    log_test(26, "POST /checks/{id}/recheck", SKIP)

# ===== 2.4 RULES =====
print_header("2.4 RULES APIs")

st, r = req("GET", "/rules/sets", headers=HEADERS)
log_test(27, "GET /rules/sets (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

code = f"TEST_{datetime.now().strftime('%H%M%S')}"
st, r = req("POST", "/rules/sets", headers=HEADERS, json={
    "name": "Test Set", "code": code, "doc_types": ["cong_van"]})
RULE_SET_ID = r.json().get("id") if st == 201 else None
log_test(28, "POST /rules/sets (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")

if RULE_SET_ID:
    st, r = req("GET", f"/rules/sets/{RULE_SET_ID}", headers=HEADERS)
    log_test(29, "GET /rules/sets/{id} (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("PUT", f"/rules/sets/{RULE_SET_ID}", headers=HEADERS, json={"name": "Updated Set"})
    log_test(30, "PUT /rules/sets/{id} (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("POST", f"/rules/sets/{RULE_SET_ID}/set-default", headers=HEADERS)
    log_test(31, "POST /rules/sets/{id}/set-default (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("POST", f"/rules/sets/{RULE_SET_ID}/rules", headers=HEADERS, json={
        "rule_code": "FONT_TEST", "category": "font", "name": "Font Test",
        "expected_value": {"font": "TNR", "size": 13}, "severity": "critical",
        "error_message": "Loi font"})
    RULE_ID = r.json().get("id") if st == 201 else None
    log_test(32, "POST /rules/sets/{sid}/rules (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")
    
    if RULE_ID:
        st, r = req("PUT", f"/rules/{RULE_ID}", headers=HEADERS, json={"name": "Updated Rule"})
        log_test(33, "PUT /rules/{id} (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    else:
        log_test(33, "PUT /rules/{id}", SKIP)
else:
    for i in range(29, 34):
        log_test(i, f"Rules test {i}", SKIP)

# ===== 2.5 KNOWLEDGE =====
print_header("2.5 KNOWLEDGE APIs")

st, r = req("GET", "/knowledge/categories", headers=HEADERS)
log_test(34, "GET /knowledge/categories (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

st, r = req("POST", "/knowledge/categories", headers=HEADERS, json={
    "name": "The Thuc", "code": f"TT_{datetime.now().strftime('%H%M%S')}"})
CAT_ID = r.json().get("id") if st == 201 else None
log_test(35, "POST /knowledge/categories (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")

st, r = req("GET", "/knowledge/stats", headers=HEADERS)
log_test(36, "GET /knowledge/stats (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

st, r = req("GET", "/knowledge/documents", headers=HEADERS)
log_test(37, "GET /knowledge/documents (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

# ===== 2.6 TEMPLATES =====
print_header("2.6 TEMPLATE APIs")

st, r = req("GET", "/templates", headers=HEADERS)
log_test(38, "GET /templates (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

# ===== 2.7 APPROVAL =====
print_header("2.7 APPROVAL APIs")

if DOC_ID:
    st, r = req("POST", "/approval/requests", headers=HEADERS, json={
        "document_id": DOC_ID,
        "approver_id": USER_ID})
    APPROVAL_ID = r.json().get("id") if st == 201 else None
    log_test(39, "POST /approval/requests (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")
else:
    log_test(39, "POST /approval/requests", SKIP)

st, r = req("GET", "/approval/requests/pending", headers=HEADERS)
log_test(40, "GET /approval/requests/pending (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

if APPROVAL_ID:
    st, r = req("PUT", f"/approval/requests/{APPROVAL_ID}", headers=HEADERS, json={"action": "approve", "note": "OK"})
    log_test(41, "PUT /approval/requests/{id} - Approve (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
else:
    log_test(41, "PUT /approval/requests/{id}", SKIP)

# ===== 2.8 NOTIFICATIONS =====
print_header("2.8 NOTIFICATION APIs")

st, r = req("GET", "/notifications/", headers=HEADERS)
log_test(42, "GET /notifications/ (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

d = r.json() if st == 200 else {}
notifs = d.get("notifications", [])
log_test(43, f"GET /notifications/ - unread={d.get('unread_count', 0)}", PASS)

if notifs:
    ids = [n["id"] for n in notifs if not n["is_read"]]
    if ids:
        st, r = req("POST", "/notifications/mark-read", headers=HEADERS, json={"notification_ids": ids[:5]})
        log_test(44, "POST /notifications/mark-read (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    else:
        log_test(44, "POST /notifications/mark-read", SKIP, "Da doc het")
else:
    log_test(44, "POST /notifications/mark-read", SKIP)

# ===== 2.9 ADMIN =====
print_header("2.9 ADMIN APIs")

st, r = req("GET", "/admin/health", headers=ADMIN_H)
log_test(45, "GET /admin/health (expected 200)", PASS if st == 200 else FAIL, f"Got {st}: {r.text[:100] if st > 0 else ''}")

st, r = req("GET", "/admin/users", headers=ADMIN_H)
log_test(46, "GET /admin/users (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

st, r = req("POST", "/admin/users", headers=ADMIN_H, json={
    "email": f"new_{datetime.now().strftime('%H%M%S')}@test.com",
    "full_name": "New User", "password": "Pass@123", "role": "OFFICER"})
NEW_USER_ID = r.json().get("id") if st == 201 else None
log_test(47, "POST /admin/users (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")

if NEW_USER_ID:
    st, r = req("PUT", f"/admin/users/{NEW_USER_ID}", headers=ADMIN_H, json={"full_name": "Updated"})
    log_test(48, "PUT /admin/users/{id} (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("POST", f"/admin/users/{NEW_USER_ID}/lock", headers=ADMIN_H)
    log_test(49, "POST /admin/users/{id}/lock (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("POST", f"/admin/users/{NEW_USER_ID}/unlock", headers=ADMIN_H)
    log_test(50, "POST /admin/users/{id}/unlock (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
    
    st, r = req("POST", f"/admin/users/{NEW_USER_ID}/reset-password", headers=ADMIN_H)
    log_test(51, "POST /admin/users/{id}/reset-password (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")
else:
    log_test(48, "PUT /admin/users/{id}", SKIP)
    log_test(49, "POST /admin/users/{id}/lock", SKIP)
    log_test(50, "POST /admin/users/{id}/unlock", SKIP)
    log_test(51, "POST /admin/users/{id}/reset-password", SKIP)

st, r = req("GET", "/admin/settings", headers=ADMIN_H)
log_test(52, "GET /admin/settings (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

st, r = req("GET", "/admin/audit-logs", headers=ADMIN_H)
log_test(53, "GET /admin/audit-logs (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

st, r = req("POST", "/admin/api-keys", headers=ADMIN_H, json={"name": "Test Key"})
log_test(54, "POST /admin/api-keys (expected 201)", PASS if st == 201 else FAIL, f"Got {st}")

# ===== 2.10 ANALYTICS =====
print_header("2.10 ANALYTICS API")

st, r = req("GET", "/analytics/dashboard", headers=HEADERS)
log_test(55, "GET /analytics/dashboard (expected 200)", PASS if st == 200 else FAIL, f"Got {st}")

# ===== 2.11 PERMISSION TESTS =====
print_header("2.11 PERMISSION TESTS")

st, r = req("GET", "/admin/users", headers=HEADERS)
log_test(56, "OFFICER goi /admin/users (expected 403)", PASS if st in (401, 403) else FAIL, f"Got {st}")

st, r = req("GET", "/admin/health", headers=HEADERS)
log_test(57, "OFFICER goi /admin/health (expected 403)", PASS if st in (401, 403) else FAIL, f"Got {st}")

st, r = req("GET", "/auth/me")
log_test(58, "Khong token goi API (expected 401)", PASS if st == 401 else FAIL, f"Got {st}")

# ===== SUMMARY =====
print(f"\n{'='*60}")
print(f"  KET QUA TEST")
print(f"{'='*60}")
print(f"  Tong: {pass_count + fail_count} tests")
print(f"  {PASS}: {pass_count}")
print(f"  {FAIL}: {fail_count}")
print(f"  Ty le thanh cong: {pass_count / (pass_count + fail_count) * 100:.1f}%")
print()
if fail_count == 0:
    print(f"  \u2705 TAT CA DEU PASS!")
else:
    print(f"  \u26a0 Co {fail_count} test FAIL - Can kiem tra lai!")
print()