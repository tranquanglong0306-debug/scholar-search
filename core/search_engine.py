# core/search_engine.py
# Điều phối tìm kiếm từ nhiều nguồn API khác nhau.
# Người dùng chọn nguồn, engine gọi đúng adapter.

from typing import List, Optional
from core.models import Article, SearchResult
from core.apis import semantic_scholar, crossref, openalex
from core import indexing_check


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
    indexing_filter: str = "Tất cả",    # "Tất cả" | "Scopus" | "Web of Science"
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
        indexing_filter: Bộ lọc chuẩn trích dẫn

    Returns:
        SearchResult với danh sách Article đã được lọc
    """
    if not query or not query.strip():
        return SearchResult(error="⚠️ Vui lòng nhập từ khóa tìm kiếm.")

    adapter = _ADAPTERS.get(source)
    if not adapter:
        return SearchResult(error=f"❌ Nguồn dữ liệu không hợp lệ: {source}")

    query = query.strip()

    # --- Tự động phát hiện loại tìm kiếm (Smart Search / Ask Anything) ---
    import re
    # 1. Tự động phát hiện DOI
    doi_match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', query, re.IGNORECASE)
    if doi_match:
        search_type = "doi"
        query = doi_match.group(1)
    # 2. Tự động phát hiện Tác giả (tiền tố author: hoặc tác giả:)
    elif query.lower().startswith("author:") or query.lower().startswith("tác giả:"):
        search_type = "author"
        if query.lower().startswith("author:"):
            query = query[7:].strip()
        else:
            query = query[8:].strip()
    # 3. Mặc định hoặc khi là keyword: Gọi AI dịch tiếng Việt -> tiếng Anh học thuật
    elif search_type == "keyword" or search_type not in ["doi", "author"]:
        search_type = "keyword"
        from core import ai_service
        query = ai_service.translate_and_expand_query(query)

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
            result = adapter.search_by_keyword(
                query,
                limit=limit,
                year_from=year_from,
                year_to=year_to,
            )

    # Nếu tìm kiếm thất bại, trả về ngay
    if not result.success:
        return result

    # --- Bước Lọc & Gắn nhãn Scopus/WoS ---
    filtered_articles = []
    for article in result.articles:
        # Gắn nhãn chuẩn
        is_scopus, scopus_q, is_wos, wos_q = indexing_check.check_indexing(article.journal, article.issn if hasattr(article, 'issn') else None)
        article.is_scopus = is_scopus
        article.scopus_q = scopus_q
        article.is_wos = is_wos
        article.wos_q = wos_q
        
        # Lọc theo yêu cầu
        if indexing_filter == "Scopus" and not is_scopus:
            continue
        if indexing_filter == "Web of Science" and not is_wos:
            continue
            
        filtered_articles.append(article)
        
    result.articles = filtered_articles
    result.total_count = len(filtered_articles)
    return result


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
