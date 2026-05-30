# Mô tả Pipeline Backend - Hệ thống RAG kiểm tra thể thức văn bản

Tài liệu này mô tả chi tiết luồng xử lý dữ liệu (pipeline) của backend, làm rõ từng giai đoạn, cấu trúc dữ liệu đầu vào và đầu ra.

## Luồng hoạt động tổng quan

Backend xử lý một file văn bản (`.docx` hoặc `.pdf`) qua nhiều giai đoạn tự động để kiểm tra và đánh giá thể thức theo Nghị định 30/2020/NĐ-CP. Pipeline được chia thành các tầng xử lý nối tiếp nhau.

![Sơ đồ luồng xử lý](https://i.imgur.com/your-diagram-image.png)
*(Lưu ý: Đây là placeholder, bạn có thể tạo sơ đồ và thay link vào)*

---

### **Tầng 1: Bóc tách dữ liệu (Extraction)**

Giai đoạn này chịu trách nhiệm chuyển đổi file văn bản gốc thành một cấu trúc dữ liệu JSON chi tiết, làm đầu vào cho các tầng tiếp theo.

-   **Scripts thực thi**: `src/extract_docx.py` hoặc `src/extract_pdf.py`.
-   **Đầu vào**: Một file văn bản (`.docx` hoặc `.pdf`) từ người dùng.
-   **Xử lý**:
    -   Phân tích sâu file văn bản để trích xuất không chỉ nội dung chữ mà còn cả các siêu dữ liệu (metadata) về định dạng.
    -   **Với DOCX**: Đọc các thuộc tính của paragraph (căn lề, thụt dòng, khoảng cách) và các thuộc tính của run (font, cỡ chữ, in đậm, in nghiêng).
    -   **Với PDF**: Tái cấu trúc các khối văn bản, gom nhóm các ký tự có cùng định dạng, tính toán lề trang, vị trí tương đối của các khối.
-   **Đầu ra**: Một file JSON (`*_optimized.json`) được lưu vào thư mục `output/`. File này chứa toàn bộ thông tin đã bóc tách.

**Cấu trúc file `*_optimized.json` (ví dụ):**
```json
{
  "filename": "cv123.pdf",
  "source": "pdf", // hoặc "docx"
  "pages": 5,
  "margins": {"left_cm": 3.0, "right_cm": 2.0, "top_cm": 2.0, "bottom_cm": 2.0},
  "doc_type": "cong_van",
  "paragraphs": [
    {
      "idx": 0,
      "text": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
      "block": {
        "align": "CENTER",
        "y_pt": 72.5
      },
      "spans": [ // "runs" đối với docx
        {"fmt": "Arial-13pt-Bold", "txt": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"}
      ],
      "zone": "RIGHT_COL",
      "page": 0
    },
    // ... các đoạn văn khác
  ]
}
```

---

### **Tầng 2: Kiểm tra sơ bộ & Gán nhãn (Pre-check)**

Giai đoạn này áp dụng các quy tắc logic dựa trên Nghị định 30 để kiểm tra các lỗi cơ bản và gán nhãn cho các thành phần trong văn bản.

-   **Script thực thi**: `src/pre_check.py`.
-   **Đầu vào**: File `*_optimized.json` từ Tầng 1.
-   **Xử lý**:
    1.  **Gán nhãn**: Duyệt qua từng đoạn văn, dựa vào từ khóa, định dạng và vị trí để gán nhãn thể thức (ví dụ: `quoc_hieu`, `tieu_ngu`, `ten_loai`, `dieu`, `noi_nhan`...).
    2.  **Kiểm tra lỗi cơ học**: So sánh các thuộc tính định dạng (lề trang, font chữ, cỡ chữ...) với các hằng số được định nghĩa trong `pre_check.py`. Các lỗi tìm thấy được ghi lại.
    3.  **Phân loại xử lý**: Xác định những đoạn văn bản nào cần được LLM phân tích sâu hơn (các lỗi cần ngữ cảnh, cấu trúc phức tạp).
-   **Đầu ra**: Một file JSON (`*_precheck.json`) được lưu vào thư mục `pre_check_output/`.

**Cấu trúc file `*_precheck.json`:**
```json
{
  "summary": {
    "total_paragraphs": 150,
    "mechanical_errors": 5, // Số lỗi cơ học phát hiện được
    "paragraphs_need_llm": 45, // Số đoạn cần LLM kiểm tra
    "chunks_for_llm": 3 // Số "chunk" được tạo cho LLM
  },
  "labels": {
    "0": "co_quan",
    "1": "quoc_hieu",
    "2": "tieu_ngu",
    "10": "ten_loai",
    "11": "trich_yeu"
    // ... nhãn cho tất cả các đoạn
  },
  "errors_mechanical": [
    {
      "code": "MARGIN_LEFT_INVALID",
      "message": "Lề trái là 2.5cm, không đạt yêu cầu (phải từ 3.0cm - 3.5cm).",
      "component": "page_margins"
    }
    // ... các lỗi cơ học khác
  ],
  "chunks_for_llm": [
    {
      "id": "header_0",
      "paragraph_indices": [0, 1, 2, 3, 4, 5, 6, 7, 8],
      "kb_rule": "QUY TẮC KIỂM TRA PHẦN ĐẦU VĂN BẢN..."
    }
    // ... các chunk khác
  ]
}
```

---

### **Tầng 3: Chuẩn bị dữ liệu cho RAGFlow**

Giai đoạn này chuẩn bị dữ liệu đầu vào cuối cùng cho RAGFlow dưới dạng các file text đơn giản.

-   **Script thực thi**: `src/jsonl_to_text.py`.
-   **Đầu vào**:
    1.  File `*_optimized.json` (Tầng 1).
    2.  File `*_precheck.json` (Tầng 2).
-   **Xử lý**:
    -   Dựa vào thông tin `chunks_for_llm` từ file precheck, script sẽ tạo ra các file text riêng biệt cho mỗi chunk.
    -   Mỗi file text chứa nội dung của các đoạn văn trong chunk đó, được làm giàu bằng các thông tin định dạng và nhãn đã được dịch sang tiếng Việt tường minh (ví dụ: "Căn lề: Căn giữa", "Thành phần: Quốc hiệu").
    -   Việc này giúp LLM dễ dàng hiểu được ngữ cảnh và thuộc tính của từng đoạn văn mà không cần đọc file JSON phức tạp.
-   **Đầu ra**: Nhiều file `.txt` được lưu trong thư mục `ragflow_chunks/` (hoặc tương tự). Tên file có dạng `[tên_gốc]_[id_chunk].txt`.

**Ví dụ nội dung file `06-vbhn-bxd_header_0.txt`:**
```text
📄 TÀI LIỆU: 06-vbhn-bxd.pdf
📎 NGUỒN: PDF | LOẠI VĂN BẢN: Văn bản hợp nhất
📐 KHỔ GIẤY: Rộng 21.0cm, Cao 29.7cm
📌 LỀ TRANG: Trên 2.0cm, Dưới 2.0cm, Trái 3.0cm, Phải 1.5cm

==================================================
NỘI DUNG VĂN BẢN
==================================================
[Đoạn 0 | Thành phần: Tên cơ quan | Vị trí: Cột trái | Căn lề: Căn giữa]
- [Arial-12pt]: "BỘ XÂY DỰNG"

[Đoạn 1 | Thành phần: Quốc hiệu | Vị trí: Cột phải | Căn lề: Căn giữa]
- [Times-13pt-Bold]: "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"

[Đoạn 2 | Thành phần: Tiêu ngữ | Vị trí: Cột phải | Căn lề: Căn giữa]
- [Times-14pt-Bold]: "Độc lập - Tự do - Hạnh phúc"

...
```

### **Tầng 4: Phân tích bằng RAGFlow (LLM)**

Đây là giai đoạn cuối cùng, nơi các file text được đưa vào RAGFlow để phân tích.

-   **Hệ thống thực thi**: RAGFlow Framework.
-   **Đầu vào**: Các file `.txt` được tạo ra ở Tầng 3.
-   **Xử lý**:
    -   Frontend/một tiến trình khác sẽ tải các file `.txt` này lên RAGFlow.
    -   RAGFlow sử dụng LLM để đọc nội dung và các quy tắc đính kèm trong mỗi file, từ đó phát hiện các lỗi về ngữ nghĩa, logic, và cấu trúc phức tạp mà các quy tắc ở Tầng 2 không thể phát hiện.
-   **Đầu ra**: Kết quả phân tích từ LLM (thường là dạng JSON), chứa các lỗi đã được phát hiện.

---
*Tài liệu này nên được cập nhật khi có sự thay đổi trong pipeline của backend.*
