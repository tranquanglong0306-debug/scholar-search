# citation/formatter.py
# Tạo chuỗi trích dẫn theo chuẩn APA 7th, MLA 9th và Chicago 17th.

import re
from typing import List
from core.models import Article


# ---------------------------------------------------------------
# Hàm tiện ích
# ---------------------------------------------------------------

def _format_authors_apa(authors: List[str]) -> str:
    """
    Định dạng tên tác giả theo APA 7th.
    
    Quy tắc:
    - 1 tác giả: Nguyen, V. A.
    - 2 tác giả: Nguyen, V. A., & Tran, T. B.
    - 3–20 tác giả: ... tác giả cuối dùng & ...
    - >20 tác giả: 19 tác giả đầu, ..., tác giả cuối
    """
    if not authors:
        return "Unknown Author"

    formatted = []
    for author in authors:
        author = author.strip()
        # Nếu đã có dạng "Lastname, Firstname" → giữ nguyên
        if "," in author:
            parts = [p.strip() for p in author.split(",", 1)]
            last = parts[0]
            first = parts[1] if len(parts) > 1 else ""
            # Rút gọn tên: "John Michael" → "J. M."
            initials = " ".join(
                f"{w[0].upper()}." for w in first.split() if w
            )
            formatted.append(f"{last}, {initials}" if initials else last)
        else:
            # Dạng "Firstname Lastname" → đảo thành "Lastname, F."
            parts = author.split()
            if len(parts) >= 2:
                last = parts[-1]
                initials = " ".join(f"{w[0].upper()}." for w in parts[:-1] if w)
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(author)

    n = len(formatted)
    if n == 1:
        return formatted[0]
    elif n == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    elif n <= 20:
        return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"
    else:
        # APA 7th: 19 tác giả + ... + tác giả cuối
        return ", ".join(formatted[:19]) + f", ... {formatted[-1]}"


def _format_authors_mla(authors: List[str]) -> str:
    """
    Định dạng tên tác giả theo MLA 9th.
    
    - 1 tác giả: Nguyen, Van A.
    - 2 tác giả: Nguyen, Van A., and Tran Thi B.
    - 3+ tác giả: Nguyen, Van A., et al.
    """
    if not authors:
        return "Unknown Author"

    def _format_single_mla(author: str) -> str:
        author = author.strip()
        if "," in author:
            return author  # Đã đúng dạng "Last, First"
        parts = author.split()
        if len(parts) >= 2:
            return f"{parts[-1]}, {' '.join(parts[:-1])}"
        return author

    if len(authors) == 1:
        return _format_single_mla(authors[0])
    elif len(authors) == 2:
        return f"{_format_single_mla(authors[0])}, and {authors[1]}"
    else:
        return f"{_format_single_mla(authors[0])}, et al."


def _format_authors_chicago(authors: List[str]) -> str:
    """
    Định dạng tên tác giả theo Chicago 17th Author-Date.
    - 1-3 tác giả: liệt kê đầy đủ
    - 4+ tác giả: et al.
    """
    if not authors:
        return "Unknown Author"

    def _format_single(author: str, first: bool = True) -> str:
        author = author.strip()
        if "," in author:
            parts = [p.strip() for p in author.split(",", 1)]
            if first:
                return f"{parts[0]}, {parts[1]}" if len(parts) > 1 else parts[0]
            else:
                return f"{parts[1]} {parts[0]}" if len(parts) > 1 else parts[0]
        parts = author.split()
        if first and len(parts) >= 2:
            return f"{parts[-1]}, {' '.join(parts[:-1])}"
        return author

    if len(authors) == 1:
        return _format_single(authors[0], first=True)
    elif len(authors) <= 3:
        first = _format_single(authors[0], first=True)
        rest = [_format_single(a, first=False) for a in authors[1:]]
        return first + ", and " + ", and ".join(rest)
    else:
        return f"{_format_single(authors[0], first=True)}, et al."


def _clean_title(title: str) -> str:
    """Xóa các ký tự HTML và chuẩn hóa khoảng trắng."""
    title = re.sub(r"<[^>]+>", "", title)
    return " ".join(title.split())


# ---------------------------------------------------------------
# APA 7th Edition
# ---------------------------------------------------------------

def format_apa(article: Article) -> str:
    """
    Tạo trích dẫn theo chuẩn APA 7th Edition.
    
    Cấu trúc:
    Author(s). (Year). Title of article. Journal Name, Volume(Issue), Pages.
    https://doi.org/xxxxx
    """
    # Tác giả
    authors_str = _format_authors_apa(article.authors)

    # Năm
    year = f"({article.display_year})"

    # Tiêu đề (chữ thường, chỉ viết hoa chữ đầu và sau dấu : )
    title = _clean_title(article.title)
    # Chuyển sang sentence case
    title_sc = title[0].upper() + title[1:].lower() if title else "Untitled"
    # Giữ chữ hoa sau dấu hai chấm
    title_sc = re.sub(r"(:\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), title_sc)

    # Tên tạp chí (in nghiêng — dùng markdown *italic*)
    journal = article.journal
    citation_parts = [f"*{journal}*"] if journal else []

    # Volume và Issue
    if article.volume and article.issue:
        citation_parts.append(f"*{article.volume}*({article.issue})")
    elif article.volume:
        citation_parts.append(f"*{article.volume}*")

    # Pages
    if article.pages:
        citation_parts.append(article.pages)

    journal_info = ", ".join(citation_parts)

    # DOI
    doi_str = f"\n  https://doi.org/{article.doi}" if article.doi else (
        f"\n  {article.url}" if article.url else ""
    )

    # Ghép lại
    citation = f"{authors_str}. {year}. {title_sc}."
    if journal_info:
        citation += f" {journal_info}."
    citation += doi_str

    return citation.strip()


def format_apa_plain(article: Article) -> str:
    """
    Tạo trích dẫn APA không có markdown (*italic*).
    Dùng để xuất file .txt, .csv.
    """
    return format_apa(article).replace("*", "")


# ---------------------------------------------------------------
# MLA 9th Edition
# ---------------------------------------------------------------

def format_mla(article: Article) -> str:
    """
    Tạo trích dẫn theo chuẩn MLA 9th Edition.
    
    Cấu trúc:
    Author(s). "Title of Article." Journal Name, vol. X, no. X, Year, pp. X–X,
    https://doi.org/xxxxx.
    """
    authors_str = _format_authors_mla(article.authors)
    title = _clean_title(article.title)

    # Tên tạp chí in nghiêng
    journal = f"*{article.journal}*" if article.journal else ""

    # Vol/No
    vol_no = []
    if article.volume:
        vol_no.append(f"vol. {article.volume}")
    if article.issue:
        vol_no.append(f"no. {article.issue}")
    if article.year:
        vol_no.append(str(article.year))
    if article.pages:
        vol_no.append(f"pp. {article.pages}")

    citation = f'{authors_str}. "{title}."'
    if journal:
        citation += f" {journal},"
    if vol_no:
        citation += " " + ", ".join(vol_no) + ","
    if article.doi:
        citation += f" https://doi.org/{article.doi}."
    elif article.url:
        citation += f" {article.url}."

    return citation.strip()


# ---------------------------------------------------------------
# Chicago 17th Author-Date
# ---------------------------------------------------------------

def format_chicago(article: Article) -> str:
    """
    Tạo trích dẫn theo chuẩn Chicago 17th Author-Date.
    
    Cấu trúc:
    Author(s). Year. "Title." Journal Name Volume (Issue): Pages.
    https://doi.org/xxxxx.
    """
    authors_str = _format_authors_chicago(article.authors)
    year = article.display_year
    title = _clean_title(article.title)
    journal = f"*{article.journal}*" if article.journal else ""

    # Volume (Issue): Pages
    location = ""
    if article.volume:
        location += article.volume
    if article.issue:
        location += f" ({article.issue})"
    if article.pages:
        location += f": {article.pages}"

    citation = f'{authors_str}. {year}. "{title}."'
    if journal:
        citation += f" {journal}"
    if location:
        citation += f" {location}."
    if article.doi:
        citation += f" https://doi.org/{article.doi}."
    elif article.url:
        citation += f" {article.url}."

    return citation.strip()


# ---------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------

CITATION_STYLES = {
    "APA 7th": format_apa,
    "MLA 9th": format_mla,
    "Chicago 17th": format_chicago,
}


def format_citation(article: Article, style: str = "APA 7th") -> str:
    """
    Hàm chính để tạo trích dẫn.
    
    Args:
        article: Đối tượng Article
        style: "APA 7th" | "MLA 9th" | "Chicago 17th"
    
    Returns:
        Chuỗi trích dẫn theo định dạng yêu cầu
    """
    formatter = CITATION_STYLES.get(style, format_apa)
    return formatter(article)


def get_available_styles() -> List[str]:
    """Trả về danh sách định dạng trích dẫn khả dụng."""
    return list(CITATION_STYLES.keys())
