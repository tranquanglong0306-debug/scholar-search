# config.py
# Quản lý cấu hình và API keys của ứng dụng

import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env (nếu có)
load_dotenv()


class Config:
    """Cấu hình toàn cục của ứng dụng."""

    # ---------------------------------------------------------------
    # API Keys (đặt trong file .env hoặc biến môi trường hệ thống)
    # ---------------------------------------------------------------

    # Google Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Semantic Scholar — Đăng ký miễn phí tại:
    # https://www.semanticscholar.org/product/api
    # Không cần key vẫn dùng được, nhưng giới hạn 100 req/5min
    SEMANTIC_SCHOLAR_API_KEY: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

    # Crossref — Không cần key, nhưng thêm email để ưu tiên rate limit
    # Theo chính sách "polite pool" của Crossref
    CROSSREF_MAILTO: str = os.getenv("CROSSREF_MAILTO", "your_email@example.com")

    # OpenAlex — Không cần key, nhưng thêm email để tăng giới hạn
    OPENALEX_MAILTO: str = os.getenv("OPENALEX_MAILTO", "your_email@example.com")

    # ---------------------------------------------------------------
    # Cấu hình tìm kiếm
    # ---------------------------------------------------------------

    # Số kết quả mặc định mỗi trang
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 50

    # Timeout cho HTTP requests (giây)
    REQUEST_TIMEOUT: int = 15

    # Số lần retry khi request thất bại
    MAX_RETRIES: int = 3

    # ---------------------------------------------------------------
    # Lĩnh vực mặc định (Applied Linguistics & Education)
    # ---------------------------------------------------------------
    DEFAULT_FIELDS = [
        "Applied Linguistics",
        "Language Education",
        "Second Language Acquisition",
        "English Language Teaching",
        "TESOL",
    ]

    # ---------------------------------------------------------------
    # Thông tin ứng dụng
    # ---------------------------------------------------------------
    APP_NAME: str = "ScholarSearch"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Công cụ tìm kiếm bài báo khoa học và quản lý trích dẫn "
        "cho Ngôn ngữ học ứng dụng & Giáo dục"
    )

    # ---------------------------------------------------------------
    # API Endpoints
    # ---------------------------------------------------------------
    SEMANTIC_SCHOLAR_BASE_URL: str = "https://api.semanticscholar.org/graph/v1"
    CROSSREF_BASE_URL: str = "https://api.crossref.org"
    OPENALEX_BASE_URL: str = "https://api.openalex.org"
