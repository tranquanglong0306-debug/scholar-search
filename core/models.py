# core/models.py
# Định nghĩa cấu trúc dữ liệu cho bài báo và kết quả tìm kiếm

from dataclasses import dataclass, field
from typing import List, Optional
import uuid


@dataclass
class Article:
    """
    Đại diện cho một bài báo khoa học với đầy đủ metadata.
    Mỗi Article có một ID nội bộ duy nhất để quản lý thư viện.
    """
    # Định danh nội bộ (tự động tạo)
    internal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Chuẩn đánh giá (Scopus / Web of Science)
    is_scopus: bool = False
    is_wos: bool = False

    # Thông tin cơ bản
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    abstract: str = ""

    # Thông tin xuất bản
    journal: str = ""           # Tên tạp chí / hội nghị
    volume: str = ""
    issue: str = ""
    pages: str = ""
    publisher: str = ""

    # Định danh học thuật
    doi: str = ""
    url: str = ""
    pdf_url: str = ""  # Link PDF trực tiếp nếu là Open Access
    arxiv_id: str = ""
    semantic_scholar_id: str = ""
    openalex_id: str = ""

    # Chỉ số & phân loại
    citation_count: int = 0
    fields_of_study: List[str] = field(default_factory=list)
    source: str = ""            # "semantic_scholar" | "crossref" | "openalex"

    # Loại tài liệu
    doc_type: str = "article"   # article | book | chapter | conference

    # ---------------------------------------------------------------
    # Các helper property
    # ---------------------------------------------------------------

    @property
    def authors_str(self) -> str:
        """Trả về chuỗi tác giả ngăn cách bởi dấu phẩy."""
        return ", ".join(self.authors) if self.authors else "Unknown Author"

    @property
    def first_author_last(self) -> str:
        """
        Trả về HỌ của tác giả đầu tiên để dùng trong APA.
        Ví dụ: "Nguyen Van A" → "Nguyen"
        """
        if not self.authors:
            return "Unknown"
        parts = self.authors[0].split()
        return parts[0] if parts else "Unknown"

    @property
    def has_abstract(self) -> bool:
        return bool(self.abstract and len(self.abstract.strip()) > 10)

    @property
    def display_year(self) -> str:
        return str(self.year) if self.year else "n.d."

    def to_dict(self) -> dict:
        """Chuyển đổi thành dict để lưu vào DataFrame / CSV."""
        return {
            "ID": self.internal_id,
            "Title": self.title,
            "Authors": self.authors_str,
            "Year": self.display_year,
            "Journal": self.journal,
            "Volume": self.volume,
            "Issue": self.issue,
            "Pages": self.pages,
            "Publisher": self.publisher,
            "DOI": self.doi,
            "URL": self.url,
            "Abstract": self.abstract,
            "Citation Count": self.citation_count,
            "Fields": ", ".join(self.fields_of_study),
            "Source": self.source,
        }


@dataclass
class SearchResult:
    """Kết quả trả về từ một lần tìm kiếm."""
    articles: List[Article] = field(default_factory=list)
    total_count: int = 0
    query: str = ""
    source: str = ""
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None
