# core/pdf_resolver.py
# Bộ giải quyết tự động tìm link PDF miễn phí (Open Access) cho các tài liệu trả phí

import requests
import urllib.parse
import re
from typing import Optional
from config import Config

def clean_title_for_matching(title: str) -> str:
    """Chuẩn hóa tiêu đề để so khớp chính xác."""
    if not title:
        return ""
    # Chuyển chữ thường, xóa khoảng trắng thừa và ký tự đặc biệt
    clean = title.lower().strip()
    clean = re.sub(r'[^a-z0-9\s]', '', clean)
    return re.sub(r'\s+', ' ', clean).strip()

def matches_title(title_a: str, title_b: str) -> bool:
    """So khớp tiêu đề thô để kiểm tra độ tin cậy."""
    clean_a = clean_title_for_matching(title_a)
    clean_b = clean_title_for_matching(title_b)
    if not clean_a or not clean_b:
        return False
    # Cho phép so khớp chính xác hoặc một tiêu đề là con của tiêu đề kia (khi có subtitle)
    return clean_a in clean_b or clean_b in clean_a or len(set(clean_a.split()) & set(clean_b.split())) / max(len(clean_a.split()), len(clean_b.split())) > 0.85

def resolve_pdf_via_unpaywall(doi: str) -> Optional[str]:
    """Tìm PDF Open Access qua Unpaywall API."""
    if not doi:
        return None
    email = getattr(Config, "CROSSREF_MAILTO", "your_email@example.com")
    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
    try:
        r = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if data.get("is_oa"):
                best_loc = data.get("best_oa_location") or {}
                # Ưu tiên url_for_pdf
                pdf_url = best_loc.get("url_for_pdf") or best_loc.get("url")
                if pdf_url:
                    return pdf_url
    except Exception as e:
        print(f"[Unpaywall Resolver Error] {e}")
    return None

def resolve_pdf_via_openalex(doi: Optional[str], title: str) -> Optional[str]:
    """Tìm PDF qua OpenAlex bằng DOI hoặc Tiêu đề."""
    # 1. Tìm bằng DOI
    if doi:
        # Chuẩn hóa DOI
        doi_clean = doi.strip()
        if doi_clean.startswith("https://doi.org/"):
            doi_url = doi_clean
        else:
            doi_url = f"https://doi.org/{doi_clean}"
        
        url = f"https://api.openalex.org/works/{doi_url}"
        headers = {"User-Agent": f"ScholarSearch/1.0 (mailto:{Config.OPENALEX_MAILTO})"}
        try:
            r = requests.get(url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            if r.status_code == 200:
                work = r.json()
                oa = work.get("open_access", {})
                if oa.get("is_oa"):
                    pdf_url = oa.get("oa_url")
                    if pdf_url:
                        return pdf_url
                # Thử tìm trong locations
                for loc in work.get("locations", []):
                    if loc.get("pdf_url"):
                        return loc.get("pdf_url")
                    if loc.get("landing_page_url") and loc.get("is_oa"):
                        return loc.get("landing_page_url")
        except Exception as e:
            print(f"[OpenAlex DOI Resolver Error] {e}")

    # 2. Tìm bằng tiêu đề
    if title:
        encoded_title = urllib.parse.quote_plus(title)
        url = f"https://api.openalex.org/works?search={encoded_title}&per-page=3"
        headers = {"User-Agent": f"ScholarSearch/1.0 (mailto:{Config.OPENALEX_MAILTO})"}
        try:
            r = requests.get(url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                for work in data.get("results", []):
                    work_title = work.get("title", "")
                    if matches_title(title, work_title):
                        oa = work.get("open_access", {})
                        if oa.get("is_oa"):
                            pdf_url = oa.get("oa_url")
                            if pdf_url:
                                return pdf_url
                        # Duyệt locations
                        for loc in work.get("locations", []):
                            if loc.get("pdf_url"):
                                return loc.get("pdf_url")
                            if loc.get("landing_page_url") and loc.get("is_oa"):
                                return loc.get("landing_page_url")
        except Exception as e:
            print(f"[OpenAlex Title Resolver Error] {e}")
            
    return None

def resolve_pdf_via_semanticscholar(doi: Optional[str], title: str) -> Optional[str]:
    """Tìm PDF qua Semantic Scholar bằng DOI hoặc Tiêu đề."""
    # 1. Tìm bằng DOI
    if doi:
        doi_clean = doi.strip()
        if doi_clean.startswith("https://doi.org/"):
            doi_clean = doi_clean[len("https://doi.org/"):]
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi_clean}?fields=openAccessPdf,isOpenAccess"
        headers = {}
        if getattr(Config, "SEMANTIC_SCHOLAR_API_KEY", None):
            headers["x-api-key"] = Config.SEMANTIC_SCHOLAR_API_KEY
        try:
            r = requests.get(url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                oa = data.get("openAccessPdf") or {}
                if oa.get("url"):
                    return oa.get("url")
        except Exception as e:
            print(f"[SemanticScholar DOI Resolver Error] {e}")

    # 2. Tìm bằng tiêu đề
    if title:
        encoded_title = urllib.parse.quote_plus(title)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_title}&limit=3&fields=openAccessPdf,isOpenAccess,title"
        headers = {}
        if getattr(Config, "SEMANTIC_SCHOLAR_API_KEY", None):
            headers["x-api-key"] = Config.SEMANTIC_SCHOLAR_API_KEY
        try:
            r = requests.get(url, headers=headers, timeout=Config.REQUEST_TIMEOUT)
            if r.status_code == 200:
                data = r.json()
                for paper in data.get("data", []):
                    paper_title = paper.get("title", "")
                    if matches_title(title, paper_title):
                        oa = paper.get("openAccessPdf") or {}
                        if oa.get("url"):
                            return oa.get("url")
        except Exception as e:
            print(f"[SemanticScholar Title Resolver Error] {e}")
            
    return None

def auto_resolve_pdf(doi: Optional[str], title: str) -> Optional[str]:
    """
    Hàm tổng hợp để tìm PDF Open Access qua nhiều nguồn:
    1. Unpaywall (bằng DOI)
    2. OpenAlex (bằng DOI, rồi Tiêu đề)
    3. Semantic Scholar (bằng DOI, rồi Tiêu đề)
    """
    if not doi and not title:
        return None
        
    # Chuẩn hóa DOI
    doi_clean = doi.strip() if doi else None
    if doi_clean == "":
        doi_clean = None

    # Thử Unpaywall bằng DOI đầu tiên vì nó cực kỳ chính xác cho Open Access
    if doi_clean:
        pdf_url = resolve_pdf_via_unpaywall(doi_clean)
        if pdf_url:
            return pdf_url

    # Thử OpenAlex (DOI -> Tiêu đề)
    pdf_url = resolve_pdf_via_openalex(doi_clean, title)
    if pdf_url:
        return pdf_url

    # Thử Semantic Scholar (DOI -> Tiêu đề)
    pdf_url = resolve_pdf_via_semanticscholar(doi_clean, title)
    if pdf_url:
        return pdf_url

    return None
