# ScholarSearch 🎓

> **Công cụ tìm kiếm bài báo khoa học & quản lý trích dẫn cho Luận văn Thạc sĩ**  
> Lĩnh vực: Ngôn ngữ học ứng dụng · Giáo dục · Second Language Acquisition

---

## 📋 Mục lục

1. [Tổng quan](#tổng-quan)
2. [Tính năng](#tính-năng)
3. [Cấu trúc dự án](#cấu-trúc-dự-án)
4. [Cài đặt](#cài-đặt)
5. [Cấu hình API Key](#cấu-hình-api-key)
6. [Chạy ứng dụng](#chạy-ứng-dụng)
7. [Hướng dẫn sử dụng](#hướng-dẫn-sử-dụng)
8. [Xuất file & Import vào Zotero/Mendeley](#xuất-file--import-vào-zoteromendeley)
9. [Xử lý sự cố](#xử-lý-sự-cố)

---

## Tổng quan

**ScholarSearch** là ứng dụng Python/Streamlit cho phép bạn:
- Tìm kiếm bài báo khoa học từ **3 nguồn dữ liệu uy tín** (Semantic Scholar, Crossref, OpenAlex)
- Xem tóm tắt (Abstract) ngay trong ứng dụng
- Tự động tạo trích dẫn chuẩn **APA 7th**, **MLA 9th**, **Chicago 17th**
- Xuất ra file **.bib**, **.xlsx**, **.csv**, **.txt** tương thích Zotero & Mendeley

**Không cần API key** để bắt đầu sử dụng — tất cả 3 nguồn đều miễn phí!

---

## Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| 🔍 Tìm kiếm đa nguồn | Semantic Scholar, Crossref, OpenAlex |
| 📝 3 loại tìm kiếm | Từ khóa · Tên tác giả · Mã DOI |
| ⚙️ Bộ lọc nâng cao | Lọc theo năm, số kết quả, lĩnh vực |
| 📖 Preview Abstract | Xem tóm tắt ngay trong ứng dụng |
| 📚 Quản lý thư viện | Lưu, sắp xếp, xóa bài báo |
| 📝 Trích dẫn tự động | APA 7th · MLA 9th · Chicago 17th |
| 📤 Xuất đa định dạng | .bib · .xlsx · .csv · .txt |
| 🔗 Tích hợp DOI | Link trực tiếp đến bài báo |

---

## Cấu trúc dự án

```
scholar_search/
├── app.py                          # ← Chạy file này
├── config.py                       # Cấu hình & API keys
├── requirements.txt                # Thư viện cần cài
├── .env.example                    # Mẫu file cấu hình
│
├── core/
│   ├── models.py                   # Dataclass Article, SearchResult
│   ├── search_engine.py            # Điều phối tìm kiếm
│   └── apis/
│       ├── semantic_scholar.py     # Semantic Scholar API
│       ├── crossref.py             # Crossref API
│       └── openalex.py             # OpenAlex API
│
├── citation/
│   ├── formatter.py                # APA 7th, MLA 9th, Chicago 17th
│   └── exporter.py                 # Xuất BibTeX, CSV, Excel, TXT
│
└── ui/
    ├── styles.py                   # CSS Dark Academia theme
    ├── search_tab.py               # Tab Tìm kiếm
    ├── library_tab.py              # Tab Thư viện
    └── export_tab.py               # Tab Xuất dữ liệu
```

---

## Cài đặt

### Yêu cầu hệ thống
- **Python 3.9** trở lên
- Windows 10/11, macOS, hoặc Linux
- Kết nối Internet

### Bước 1 — Kiểm tra Python

Mở Command Prompt (Windows) hoặc Terminal, chạy:

```bash
python --version
```

Nếu chưa có Python, tải tại: https://www.python.org/downloads/

### Bước 2 — Tạo môi trường ảo (Khuyến nghị)

```bash
# Di chuyển vào thư mục dự án
cd đường/dẫn/đến/scholar_search

# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Bước 3 — Cài đặt thư viện

```bash
pip install -r requirements.txt
```

Quá trình cài đặt sẽ tải về:
- `streamlit` — Giao diện web
- `requests` — Gọi API
- `pandas` — Xử lý dữ liệu
- `openpyxl` — Xuất Excel
- `python-dotenv` — Quản lý API key

---

## Cấu hình API Key

> ✅ **Ứng dụng chạy được ngay mà không cần API key nào!**

Tuy nhiên, để tăng giới hạn rate limit, bạn có thể cấu hình như sau:

### Tạo file `.env`

```bash
# Sao chép file mẫu
copy .env.example .env    # Windows
cp .env.example .env      # macOS/Linux
```

Mở file `.env` và điền thông tin:

```env
# Semantic Scholar API Key (tùy chọn)
# Đăng ký miễn phí tại: https://www.semanticscholar.org/product/api
SEMANTIC_SCHOLAR_API_KEY=your_key_here

# Email của bạn (tùy chọn nhưng khuyến nghị)
# Giúp Crossref & OpenAlex ưu tiên rate limit cho bạn
CROSSREF_MAILTO=your_email@example.com
OPENALEX_MAILTO=your_email@example.com
```

### So sánh Rate Limit

| Nguồn | Không có key | Có key/email |
|-------|-------------|-------------|
| Semantic Scholar | 100 req/5min | 1 req/giây |
| Crossref | Bình thường | Ưu tiên (polite pool) |
| OpenAlex | 10 req/giây | 100,000 req/ngày |

---

## Chạy ứng dụng

### Khởi động

```bash
# Đảm bảo đang ở thư mục scholar_search/
# Đảm bảo môi trường ảo đã được kích hoạt (nếu dùng)

streamlit run app.py
```

Ứng dụng sẽ tự động mở trình duyệt tại địa chỉ:
```
http://localhost:8501
```

### Dừng ứng dụng

Nhấn `Ctrl + C` trong terminal.

---

## Hướng dẫn sử dụng

### Tab 1 — Tìm kiếm 🔍

1. **Nhập từ khóa** vào ô tìm kiếm  
   Ví dụ: `task-based language teaching`, `Nation vocabulary`, `10.1016/j.system.2019`

2. **Chọn loại tìm kiếm**:
   - **Từ khóa** — Tìm theo nội dung, chủ đề
   - **Tác giả** — Tìm theo tên tác giả (ví dụ: `Paul Nation`)
   - **DOI** — Tra cứu chính xác theo mã DOI

3. **Chọn nguồn dữ liệu**:
   - **Semantic Scholar** — Tốt nhất cho CS/NLP, có abstract đầy đủ
   - **Crossref** — Tốt nhất cho tra cứu DOI chính xác
   - **OpenAlex** — Phủ rộng nhất, thay thế Google Scholar

4. **Bộ lọc nâng cao** (click mở):
   - Lọc theo khoảng năm xuất bản
   - Điều chỉnh số kết quả (5–50)
   - Chọn định dạng trích dẫn xem trước

5. **Click "Tìm kiếm"** → Kết quả hiển thị dưới dạng cards

6. **Xem Abstract**: Click "📖 Xem tóm tắt" để mở rộng

7. **Thêm vào thư viện**: Click "➕ Lưu" trên card

### Tab 2 — Thư viện 📚

- Xem tất cả bài báo đã lưu
- Chọn định dạng trích dẫn (APA/MLA/Chicago)
- Sắp xếp theo năm, tác giả, số trích dẫn
- Xóa bài không cần thiết
- Xem thống kê nhanh (tổng bài, năm span, có DOI)

### Tab 3 — Xuất dữ liệu 📤

- **BibTeX** → Import vào Zotero/Mendeley/LaTeX
- **Excel** → Bảng dữ liệu + danh sách trích dẫn
- **CSV** → Dữ liệu thô cho mọi phần mềm
- **TXT** → Danh sách tài liệu tham khảo đã định dạng

---

## Xuất file & Import vào Zotero/Mendeley

### Zotero (Khuyến nghị)

```
1. Vào Tab "Xuất dữ liệu" → Tải file .bib
2. Mở Zotero Desktop
3. File → Import → Chọn file .bib
4. Chọn "Place into new collection" → Next → Done
```

### Mendeley Reference Manager

```
1. Vào Tab "Xuất dữ liệu" → Tải file .bib
2. Mở Mendeley
3. File → Import → BibTeX (.bib)
4. Chọn file → Open
```

### JabRef (LaTeX users)

```
1. Tải file .bib
2. Kéo thả vào JabRef
3. Hoặc File → Open Library
```

---

## Xử lý sự cố

### ❌ Lỗi "ModuleNotFoundError"

```bash
# Cài lại thư viện
pip install -r requirements.txt --upgrade
```

### ❌ Lỗi "Rate limit exceeded"

- Đợi 30 giây rồi thử lại
- Đổi sang nguồn dữ liệu khác (Crossref hoặc OpenAlex)
- Thêm email vào file `.env` để được ưu tiên

### ❌ Không tìm thấy kết quả

- Thử viết từ khóa bằng **tiếng Anh** (các API chủ yếu lưu tài liệu tiếng Anh)
- Kiểm tra lỗi chính tả
- Thử nguồn dữ liệu khác
- Đối với DOI, đảm bảo nhập đúng định dạng: `10.xxxx/xxxxx`

### ❌ Ứng dụng không mở được

```bash
# Kiểm tra port đã bị chiếm chưa
streamlit run app.py --server.port 8502
```

### ❌ File Excel bị lỗi font tiếng Việt

- File CSV sử dụng **UTF-8-BOM** — hỗ trợ tiếng Việt
- Khi mở Excel: **Data → From Text/CSV → File Origin: 65001 UTF-8**

---

## Liên hệ & Tài nguyên

- 📖 [APA 7th Style Guide](https://apastyle.apa.org/)
- 🔬 [Semantic Scholar](https://www.semanticscholar.org/)
- 📚 [OpenAlex](https://openalex.org/)
- 🔗 [Crossref](https://www.crossref.org/)
- 📦 [Zotero](https://www.zotero.org/)
- 📦 [Mendeley](https://www.mendeley.com/)

---

*ScholarSearch v1.0.0 — Được xây dựng bằng Python & Streamlit*
