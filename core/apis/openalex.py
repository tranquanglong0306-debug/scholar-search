# core/apis/openalex.py
# Adapter cho OpenAlex API (https://api.openalex.org)
# Miễn phí, không cần API key, giới hạn 100,000 req/ngày.
# OpenAlex là thay thế mã nguồn mở cho Microsoft Academic Graph.

import requests
import re
from typing import List, Optional
from core.models import Article, SearchResult
from config import Config


def _build_headers() -> dict:
    """User-Agent header giúp OpenAlex nhận dạng ứng dụng."""
    return {
        "User-Agent": f"ScholarSearch/1.0 (mailto:{Config.OPENALEX_MAILTO})",
    }


def _build_mailto_param() -> dict:
    """Thêm email vào params để tăng rate limit."""
    params = {}
    if Config.OPENALEX_MAILTO and Config.OPENALEX_MAILTO != "your_email@example.com":
        params["mailto"] = Config.OPENALEX_MAILTO
    return params


def _clean_abstract(inverted_index: Optional[dict]) -> str:
    """
    OpenAlex lưu abstract dưới dạng 'inverted index'.
    Hàm này tái tạo lại văn bản từ cấu trúc đó.

    Ví dụ:
    {"The": [0], "study": [1], "of": [2], ...}
    → "The study of ..."
    """
    if not inverted_index:
        return ""
    try:
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(word for _, word in word_positions)
    except Exception:
        return ""


def _parse_article(work: dict) -> Article:
    """
    Chuyển đổi dict JSON từ OpenAlex thành đối tượng Article.
    """
    # Tiêu đề
    title = work.get("title") or "Untitled"

    # Tác giả
    authors = []
    for authorship in work.get("authorships", []):
        author = authorship.get("author", {})
        name = author.get("display_name", "")
        if name:
            authors.append(name)

    # Năm
    year = work.get("publication_year")

    # Abstract từ inverted index
    abstract = _clean_abstract(work.get("abstract_inverted_index"))

    # Tạp chí / Venue
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    journal = source.get("display_name", "")

    # Thông tin tạp chí chi tiết
    biblio = work.get("biblio") or {}
    volume = biblio.get("volume", "")
    issue = biblio.get("issue", "")
    first_page = biblio.get("first_page", "")
    last_page = biblio.get("last_page", "")
    pages = f"{first_page}-{last_page}" if first_page and last_page else first_page

    # DOI
    doi = work.get("doi", "") or ""
    if doi.startswith("https://doi.org/"):
        doi_clean = doi[len("https://doi.org/"):]
    else:
        doi_clean = doi
    url = doi if doi else work.get("id", "")

    # Publisher
    publisher = source.get("host_organization_name", "")

    # Citation count
    citation_count = work.get("cited_by_count", 0)

    # Lĩnh vực
    concepts = work.get("concepts", [])
    fields = [c.get("display_name", "") for c in concepts[:5] if c.get("score", 0) > 0.3]

    # Loại tài liệu
    type_map = {
        "journal-article": "article",
        "book": "book",
        "book-chapter": "chapter",
        "proceedings-article": "conference",
        "dissertation": "thesis",
        "dataset": "dataset",
        "review": "article",
        "editorial": "article",
    }
    doc_type_raw = work.get("type", "journal-article")
    doc_type = type_map.get(doc_type_raw, "article")

    # Open Access PDF
    open_access = work.get("open_access", {})
    pdf_url = open_access.get("oa_url") or ""
    is_open_access = open_access.get("is_oa", bool(pdf_url))

    return Article(
        title=title,
        authors=authors,
        year=int(year) if year else None,
        abstract=abstract,
        journal=journal,
        volume=str(volume) if volume else "",
        issue=str(issue) if issue else "",
        pages=pages,
        publisher=publisher,
        doi=doi_clean,
        url=url,
        pdf_url=pdf_url,
        is_open_access=is_open_access,
        openalex_id=work.get("id", ""),
        citation_count=citation_count,
        fields_of_study=fields,
        source="OpenAlex",
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
    Tìm kiếm bài báo theo từ khóa qua OpenAlex Works API.
    Hỗ trợ lọc theo năm và lĩnh vực.
    """
    # Ghép lĩnh vực nghiên cứu vào từ khóa tìm kiếm chính để OpenAlex trả về đúng chuyên ngành (tránh dùng concepts filter cũ bị lỗi 400)
    if fields_of_study:
        fields_clean = fields_of_study.replace(",", " ").strip()
        if fields_clean:
            query = f"{query} {fields_clean}"

    url = f"{Config.OPENALEX_BASE_URL}/works"
    params = _build_mailto_param()
    params.update({
        "search": query,
        "per-page": min(limit, 100),
        "select": "id,title,authorships,publication_year,abstract_inverted_index,"
                  "primary_location,biblio,doi,cited_by_count,concepts,type,open_access",
        "sort": "relevance_score:desc",
    })

    # Lọc theo năm
    filters = []
    if year_from:
        filters.append(f"publication_year:>{year_from - 1}")
    if year_to:
        filters.append(f"publication_year:<{year_to + 1}")

    if filters:
        params["filter"] = ",".join(filters)

    try:
        response = requests.get(
            url,
            params=params,
            headers=_build_headers(),
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        works = data.get("results", [])
        total = data.get("meta", {}).get("count", len(works))

        articles = [_parse_article(w) for w in works]
        return SearchResult(
            articles=articles,
            total_count=total,
            query=query,
            source="OpenAlex",
        )

    except requests.exceptions.Timeout:
        return SearchResult(error="⏱️ OpenAlex timeout — Vui lòng thử lại.")
    except Exception as e:
        return SearchResult(error=f"❌ OpenAlex lỗi: {str(e)}")


def search_by_author(author_name: str, limit: int = 20) -> SearchResult:
    """
    Tìm kiếm bài báo theo tên tác giả qua OpenAlex.
    """
    url = f"{Config.OPENALEX_BASE_URL}/works"
    params = _build_mailto_param()
    params.update({
        "filter": f"authorships.author.display_name.search:{author_name}",
        "per-page": min(limit, 100),
        "select": "id,title,authorships,publication_year,abstract_inverted_index,"
                  "primary_location,biblio,doi,cited_by_count,concepts,type,open_access",
        "sort": "cited_by_count:desc",
    })

    try:
        response = requests.get(
            url,
            params=params,
            headers=_build_headers(),
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        works = data.get("results", [])
        articles = [_parse_article(w) for w in works]
        return SearchResult(
            articles=articles,
            total_count=len(articles),
            query=f"Author: {author_name}",
            source="OpenAlex",
        )

    except Exception as e:
        return SearchResult(error=f"❌ OpenAlex Author lỗi: {str(e)}")


def search_by_doi(doi: str) -> SearchResult:
    """
    Tra cứu bài báo theo DOI qua OpenAlex.
    """
    doi = doi.strip()
    if not doi.startswith("https://doi.org/"):
        doi_url = f"https://doi.org/{doi}"
    else:
        doi_url = doi
        doi = doi[len("https://doi.org/"):]

    url = f"{Config.OPENALEX_BASE_URL}/works"
    params = _build_mailto_param()
    params["filter"] = f"doi:{doi_url}"
    params["select"] = ("id,title,authorships,publication_year,abstract_inverted_index,"
                        "primary_location,biblio,doi,cited_by_count,concepts,type,open_access")

    try:
        response = requests.get(
            url,
            params=params,
            headers=_build_headers(),
            timeout=Config.REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        works = data.get("results", [])

        if not works:
            return SearchResult(
                error=f"❌ Không tìm thấy DOI: {doi}",
                query=doi,
                source="OpenAlex",
            )

        article = _parse_article(works[0])
        return SearchResult(
            articles=[article],
            total_count=1,
            query=f"DOI: {doi}",
            source="OpenAlex",
        )

    except Exception as e:
        return SearchResult(error=f"❌ OpenAlex DOI lỗi: {str(e)}")
