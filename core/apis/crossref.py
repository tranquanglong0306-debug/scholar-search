# core/apis/crossref.py
# Adapter cho Crossref API (https://api.crossref.org)
# Hoàn toàn miễn phí, không cần API key.
# Thêm email vào CROSSREF_MAILTO để được ưu tiên rate limit.

import requests
from typing import List, Optional
from core.models import Article, SearchResult
from config import Config


def _build_params(base: dict) -> dict:
    """Thêm mailto vào params để dùng 'polite pool' của Crossref."""
    if Config.CROSSREF_MAILTO and Config.CROSSREF_MAILTO != "your_email@example.com":
        base["mailto"] = Config.CROSSREF_MAILTO
    return base


def _parse_author_name(author: dict) -> str:
    """
    Tạo tên tác giả từ dict Crossref.
    Ưu tiên: 'family, given' hoặc 'name' (tổ chức).
    """
    family = author.get("family", "")
    given = author.get("given", "")
    name = author.get("name", "")

    if family and given:
        return f"{family}, {given}"
    elif family:
        return family
    elif name:
        return name
    return "Unknown"


def _extract_year(item: dict) -> Optional[int]:
    """Trích xuất năm xuất bản từ nhiều trường khác nhau."""
    # Ưu tiên published-print, rồi published-online, rồi issued
    for field in ["published-print", "published-online", "issued", "created"]:
        date_parts = item.get(field, {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            try:
                return int(date_parts[0][0])
            except (ValueError, IndexError):
                pass
    return None


def _parse_article(item: dict) -> Article:
    """
    Chuyển đổi dict JSON từ Crossref thành đối tượng Article.
    """
    # Tiêu đề (có thể là list)
    titles = item.get("title", ["Untitled"])
    title = titles[0] if titles else "Untitled"

    # Tác giả
    authors = [_parse_author_name(a) for a in item.get("author", [])]

    # Tạp chí
    journal_list = item.get("container-title", [])
    journal = journal_list[0] if journal_list else ""

    # Nhà xuất bản
    publisher = item.get("publisher", "")

    # Volume, Issue, Pages
    volume = item.get("volume", "")
    issue = item.get("issue", "")
    page = item.get("page", "")

    # DOI & URL
    doi = item.get("DOI", "")
    url = item.get("URL", "")
    if not url and doi:
        url = f"https://doi.org/{doi}"

    # Abstract (Crossref thường không có, nhưng một số có)
    abstract = item.get("abstract", "")
    # Xóa tags XML thường có trong abstract Crossref
    if abstract:
        import re
        abstract = re.sub(r"<[^>]+>", " ", abstract).strip()

    # Số lần trích dẫn
    citation_count = item.get("is-referenced-by-count", 0)

    # Lĩnh vực
    subjects = item.get("subject", [])

    # Loại tài liệu
    doc_type_raw = item.get("type", "journal-article")
    doc_type_map = {
        "journal-article": "article",
        "book": "book",
        "book-chapter": "chapter",
        "proceedings-article": "conference",
        "dissertation": "thesis",
        "report": "report",
    }
    doc_type = doc_type_map.get(doc_type_raw, "article")

    return Article(
        title=title,
        authors=authors,
        year=_extract_year(item),
        abstract=abstract,
        journal=journal,
        volume=str(volume) if volume else "",
        issue=str(issue) if issue else "",
        pages=str(page) if page else "",
        publisher=publisher,
        doi=doi,
        url=url,
        citation_count=citation_count,
        fields_of_study=subjects,
        source="Crossref",
        doc_type=doc_type,
    )


def search_by_keyword(
    query: str,
    limit: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> SearchResult:
    """
    Tìm kiếm bài báo theo từ khóa qua Crossref Works API.
    """
    url = f"{Config.CROSSREF_BASE_URL}/works"
    params = _build_params({
        "query": query,
        "rows": min(limit, 50),
        "sort": "relevance",
        "select": "DOI,title,author,published-print,published-online,issued,"
                  "container-title,volume,issue,page,publisher,abstract,"
                  "is-referenced-by-count,subject,type,URL,created",
    })

    # Lọc theo năm (dùng filter của Crossref)
    filters = []
    if year_from:
        filters.append(f"from-pub-date:{year_from}")
    if year_to:
        filters.append(f"until-pub-date:{year_to}")
    if filters:
        params["filter"] = ",".join(filters)

    try:
        response = requests.get(
            url,
            params=params,
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        items = data.get("message", {}).get("items", [])
        total = data.get("message", {}).get("total-results", len(items))

        articles = [_parse_article(item) for item in items]
        return SearchResult(
            articles=articles,
            total_count=total,
            query=query,
            source="Crossref",
        )

    except requests.exceptions.Timeout:
        return SearchResult(error="⏱️ Crossref timeout — Vui lòng thử lại.")
    except Exception as e:
        return SearchResult(error=f"❌ Crossref lỗi: {str(e)}")


def search_by_doi(doi: str) -> SearchResult:
    """
    Tra cứu bài báo theo DOI — rất chính xác vì DOI là định danh duy nhất.
    """
    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi[len("https://doi.org/"):]
    elif doi.startswith("http://doi.org/"):
        doi = doi[len("http://doi.org/"):]

    url = f"{Config.CROSSREF_BASE_URL}/works/{doi}"
    try:
        response = requests.get(
            _build_params({}),
            # requests không hỗ trợ params trong GET với path variable → build URL trực tiếp
        )
    except Exception:
        pass

    try:
        params = {}
        if Config.CROSSREF_MAILTO and Config.CROSSREF_MAILTO != "your_email@example.com":
            params["mailto"] = Config.CROSSREF_MAILTO

        response = requests.get(
            url,
            params=params,
            timeout=Config.REQUEST_TIMEOUT,
        )

        if response.status_code == 404:
            return SearchResult(
                error=f"❌ Không tìm thấy DOI: {doi}",
                query=doi,
                source="Crossref",
            )
        response.raise_for_status()
        item = response.json().get("message", {})
        article = _parse_article(item)
        return SearchResult(
            articles=[article],
            total_count=1,
            query=f"DOI: {doi}",
            source="Crossref",
        )

    except requests.exceptions.Timeout:
        return SearchResult(error="⏱️ Timeout — Vui lòng thử lại.")
    except Exception as e:
        return SearchResult(error=f"❌ Crossref DOI lỗi: {str(e)}")


def search_by_author(author_name: str, limit: int = 20) -> SearchResult:
    """
    Tìm kiếm bài báo theo tên tác giả qua Crossref.
    """
    url = f"{Config.CROSSREF_BASE_URL}/works"
    params = _build_params({
        "query.author": author_name,
        "rows": min(limit, 50),
        "sort": "relevance",
        "select": "DOI,title,author,published-print,published-online,issued,"
                  "container-title,volume,issue,page,publisher,abstract,"
                  "is-referenced-by-count,subject,type,URL,created",
    })

    try:
        response = requests.get(url, params=params, timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        items = data.get("message", {}).get("items", [])
        articles = [_parse_article(item) for item in items]
        return SearchResult(
            articles=articles,
            total_count=len(articles),
            query=f"Author: {author_name}",
            source="Crossref",
        )

    except Exception as e:
        return SearchResult(error=f"❌ Crossref Author lỗi: {str(e)}")
