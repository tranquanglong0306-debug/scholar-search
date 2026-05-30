# core/search_engine.py
# Điều phối tìm kiếm từ nhiều nguồn API khác nhau.
# Người dùng chọn nguồn, engine gọi đúng adapter.

from typing import List, Optional
from core.models import Article, SearchResult
from core.apis import semantic_scholar, crossref, openalex


# Mapping tên nguồn → module adapter
_ADAPTERS = {
    "OpenAlex": openalex,
    "Semantic Scholar": semantic_scholar,
    "Crossref": crossref,
}

# Nguồn mặc định
DEFAULT_SOURCE = "OpenAlex"


def get_available_sources() -> List[str]:
    """Trả về danh sách tên nguồn dữ liệu khả dụng."""
    return list(_ADAPTERS.keys())


def search(
    query: str,
    search_type: str = "keyword",       # "keyword" | "author" | "doi"
    source: str = DEFAULT_SOURCE,
    limit: int = 20,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    fields_of_study: Optional[str] = None,
) -> SearchResult:
    """
    Hàm tìm kiếm chính — điều phối đến adapter phù hợp.

    Args:
        query: Từ khóa / tên tác giả / DOI
        search_type: Loại tìm kiếm
        source: Tên nguồn dữ liệu
        limit: Số kết quả tối đa
        year_from: Lọc từ năm
        year_to: Lọc đến năm
        fields_of_study: Lọc lĩnh vực (Semantic Scholar / OpenAlex)

    Returns:
        SearchResult với danh sách Article
    """
    if not query or not query.strip():
        return SearchResult(error="⚠️ Vui lòng nhập từ khóa tìm kiếm.")

    adapter = _ADAPTERS.get(source)
    if not adapter:
        return SearchResult(error=f"❌ Nguồn dữ liệu không hợp lệ: {source}")

    query = query.strip()

    if search_type == "doi":
        return adapter.search_by_doi(query)

    elif search_type == "author":
        return adapter.search_by_author(query, limit=limit)

    else:  # keyword (mặc định)
        # Các adapters khác nhau có tham số khác nhau
        if source == "Semantic Scholar":
            return adapter.search_by_keyword(
                query,
                limit=limit,
                year_from=year_from,
                year_to=year_to,
                fields_of_study=fields_of_study,
            )
        elif source == "OpenAlex":
            return adapter.search_by_keyword(
                query,
                limit=limit,
                year_from=year_from,
                year_to=year_to,
                fields_of_study=fields_of_study,
            )
        else:  # Crossref
            return adapter.search_by_keyword(
                query,
                limit=limit,
                year_from=year_from,
                year_to=year_to,
            )


def deduplicate(articles: List[Article]) -> List[Article]:
    """
    Loại bỏ bài báo trùng lặp dựa trên DOI hoặc tiêu đề.
    Dùng khi tổng hợp kết quả từ nhiều nguồn.
    """
    seen_dois = set()
    seen_titles = set()
    unique = []

    for article in articles:
        # Ưu tiên dedup theo DOI
        if article.doi:
            doi_key = article.doi.lower().strip()
            if doi_key in seen_dois:
                continue
            seen_dois.add(doi_key)
        else:
            # Dedup theo tiêu đề nếu không có DOI
            title_key = article.title.lower().strip()[:80]
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)

        unique.append(article)

    return unique
