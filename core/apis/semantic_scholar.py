# core/apis/semantic_scholar.py
# Adapter cho Semantic Scholar API (https://api.semanticscholar.org)
# Không cần API key để dùng cơ bản, nhưng key giúp tăng rate limit.

import requests
import time
from typing import List, Optional
from core.models import Article, SearchResult
from config import Config


# Các trường metadata cần lấy từ Semantic Scholar
_FIELDS = ",".join([
    "title",
    "authors",
    "year",
    "abstract",
    "venue",
    "journal",
    "volume",
    "externalIds",
    "citationCount",
    "fieldsOfStudy",
    "url",
    "openAccessPdf",
    "isOpenAccess",
    "publicationTypes",
    "publicationDate",
])


def _build_headers() -> dict:
    """Xây dựng HTTP headers, thêm API key nếu có."""
    headers = {"Content-Type": "application/json"}
    if Config.SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = Config.SEMANTIC_SCHOLAR_API_KEY
    return headers


def _parse_article(raw: dict) -> Article:
    """
    Chuyển đổi dict JSON từ Semantic Scholar thành đối tượng Article.
    """
    # Lấy danh sách tác giả
    authors = [a.get("name", "") for a in raw.get("authors", [])]

    # Lấy tên tạp chí (ưu tiên journal.name, rồi đến venue)
    journal_info = raw.get("journal") or {}
    journal = journal_info.get("name", "") or raw.get("venue", "")
    volume = journal_info.get("volume", "")
    pages = journal_info.get("pages", "")

    # Lấy DOI từ externalIds
    ext_ids = raw.get("externalIds") or {}
    doi = ext_ids.get("DOI", "")
    arxiv_id = ext_ids.get("ArXiv", "")

    # Lấy năm
    year = raw.get("year")

    # Xác định loại tài liệu
    pub_types = raw.get("publicationTypes") or []
    doc_type = "article"
    if "Conference" in pub_types:
        doc_type = "conference"
    elif "Book" in pub_types:
        doc_type = "book"

    # Extract Open Access PDF if available
    open_access = raw.get("openAccessPdf") or {}
    pdf_url = open_access.get("url", "")
    is_open_access = raw.get("isOpenAccess", bool(pdf_url))

    return Article(
        title=raw.get("title", "Untitled"),
        authors=authors,
        year=int(year) if year else None,
        abstract=raw.get("abstract", ""),
        journal=journal,
        volume=str(volume) if volume else "",
        pages=str(pages) if pages else "",
        doi=doi,
        arxiv_id=arxiv_id,
        semantic_scholar_id=raw.get("paperId", ""),
        url=raw.get("url", ""),
        pdf_url=pdf_url,
        is_open_access=is_open_access,
        citation_count=raw.get("citationCount", 0),
        fields_of_study=raw.get("fieldsOfStudy") or [],
        source="Semantic Scholar",
        doc_type=doc_type,
    )


def search_by_keyword(
    query: str,
    limit: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fields_of_study: Optional[str] = None,
) -> SearchResult:
    """
    Tìm kiếm bài báo theo từ khóa.

    Args:
        query: Từ khóa tìm kiếm
        limit: Số kết quả tối đa (tối đa 100)
        year_from: Năm bắt đầu lọc
        year_to: Năm kết thúc lọc
        fields_of_study: Lĩnh vực (ví dụ: "Education,Linguistics")

    Returns:
        SearchResult chứa danh sách Article
    """
    url = f"{Config.SEMANTIC_SCHOLAR_BASE_URL}/paper/search"
    params = {
        "query": query,
        "limit": min(limit, 100),
        "fields": _FIELDS,
    }

    # Lọc theo năm
    if year_from and year_to:
        params["year"] = f"{year_from}-{year_to}"
    elif year_from:
        params["year"] = f"{year_from}-"
    elif year_to:
        params["year"] = f"-{year_to}"

    # Lọc theo lĩnh vực
    if fields_of_study:
        params["fieldsOfStudy"] = fields_of_study

    try:
        response = requests.get(
            url,
            params=params,
            headers=_build_headers(),
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        articles = [_parse_article(p) for p in data.get("data", [])]
        return SearchResult(
            articles=articles,
            total_count=data.get("total", len(articles)),
            query=query,
            source="Semantic Scholar",
        )

    except requests.exceptions.Timeout:
        return SearchResult(error="⏱️ Request timeout — Vui lòng thử lại.")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return SearchResult(
                error="🚦 Rate limit exceeded — Vui lòng đợi vài giây rồi thử lại."
            )
        return SearchResult(error=f"❌ HTTP Error: {e.response.status_code}")
    except Exception as e:
        return SearchResult(error=f"❌ Lỗi không xác định: {str(e)}")


def search_by_author(author_name: str, limit: int = 20) -> SearchResult:
    """
    Tìm kiếm bài báo theo tên tác giả.
    Sử dụng author search endpoint rồi lấy papers của author đó.
    """
    # Bước 1: Tìm author ID
    author_url = f"{Config.SEMANTIC_SCHOLAR_BASE_URL}/author/search"
    try:
        resp = requests.get(
            author_url,
            params={"query": author_name, "limit": 5},
            headers=_build_headers(),
            timeout=Config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        authors_data = resp.json().get("data", [])

        if not authors_data:
            return SearchResult(
                error=f"❌ Không tìm thấy tác giả: '{author_name}'",
                query=author_name,
                source="Semantic Scholar",
            )

        # Lấy author đầu tiên
        author_id = authors_data[0]["authorId"]
        author_real_name = authors_data[0].get("name", author_name)

        # Bước 2: Lấy danh sách papers của author
        papers_url = f"{Config.SEMANTIC_SCHOLAR_BASE_URL}/author/{author_id}/papers"
        time.sleep(0.5)  # Tránh rate limit

        resp2 = requests.get(
            papers_url,
            params={"limit": min(limit, 100), "fields": _FIELDS},
            headers=_build_headers(),
            timeout=Config.REQUEST_TIMEOUT,
        )
        resp2.raise_for_status()
        papers_data = resp2.json().get("data", [])

        articles = [_parse_article(p) for p in papers_data]
        return SearchResult(
            articles=articles,
            total_count=len(articles),
            query=f"Author: {author_real_name}",
            source="Semantic Scholar",
        )

    except requests.exceptions.Timeout:
        return SearchResult(error="⏱️ Request timeout — Vui lòng thử lại.")
    except Exception as e:
        return SearchResult(error=f"❌ Lỗi: {str(e)}")


def search_by_doi(doi: str) -> SearchResult:
    """
    Tra cứu bài báo theo mã DOI.
    """
    # Chuẩn hóa DOI (xóa prefix https://doi.org/ nếu có)
    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    elif doi.startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/"):]

    url = f"{Config.SEMANTIC_SCHOLAR_BASE_URL}/paper/DOI:{doi}"
    try:
        response = requests.get(
            url,
            params={"fields": _FIELDS},
            headers=_build_headers(),
            timeout=Config.REQUEST_TIMEOUT,
        )
        if response.status_code == 404:
            return SearchResult(
                error=f"❌ Không tìm thấy bài báo với DOI: {doi}",
                query=doi,
                source="Semantic Scholar",
            )
        response.raise_for_status()
        article = _parse_article(response.json())
        return SearchResult(
            articles=[article],
            total_count=1,
            query=f"DOI: {doi}",
            source="Semantic Scholar",
        )

    except requests.exceptions.Timeout:
        return SearchResult(error="⏱️ Request timeout — Vui lòng thử lại.")
    except Exception as e:
        return SearchResult(error=f"❌ Lỗi: {str(e)}")
