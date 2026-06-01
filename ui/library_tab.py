# ui/library_tab.py
# Tab Thư viện — quản lý danh sách bài báo đã lưu

import streamlit as st
from citation.formatter import format_citation, get_available_styles
from core.models import Article
from core import storage

def _render_library_card(article: Article, index: int, citation_style: str) -> bool:
    """
    Hiển thị một bài báo trong thư viện.
    Trả về True nếu người dùng bấm nút Xóa.
    """
    should_remove = False

    # Tính toán delay tối ưu cho số lượng bài báo lớn (12ms mỗi card, tối đa 150ms)
    delay = min(index * 0.012, 0.15)

    with st.container():
        # Header card
        st.markdown(f"""
        <div class="article-card animate-card" style="animation-delay: {delay}s;">
            <div class="article-title">
                <span style="color:#6c63ff;font-size:0.85rem;font-weight:600;">#{index + 1}</span>
                {f'&nbsp;<a href="{article.pdf_url if getattr(article, "pdf_url", "") else article.url}" target="_blank">{article.title}</a>' if (getattr(article, "pdf_url", "") or article.url) else f'&nbsp;{article.title}'}
            </div>
            <div class="article-meta">
                <span class="meta-badge badge-year">📅 {article.display_year}</span>
                <span class="meta-badge badge-source">🔍 {article.source}</span>
                <span class="meta-badge badge-citations">📚 {article.citation_count:,} citations</span>
            </div>
            <div class="article-authors">👤 {article.authors_str}</div>
            {'<div class="article-journal">📰 ' + article.journal + '</div>' if article.journal else ''}
        </div>
        """, unsafe_allow_html=True)

        # Citation và nút xóa
        col_cite, col_del = st.columns([5, 1])

        with col_cite:
            # Các nút truy cập bài báo
            actions_html = ""
            if getattr(article, "pdf_url", ""):
                # PDF mở (màu xanh lá cây sang trọng)
                actions_html += f"<a href='{article.pdf_url}' target='_blank' style='display:inline-block; margin-right: 10px; margin-bottom: 8px; padding: 4px 12px; background: #10b981; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>📥 Tải PDF (Miễn phí)</a>"
            
            # Luôn hiển thị link NXB gốc (qua DOI hoặc URL)
            original_url = f"https://doi.org/{article.doi}" if getattr(article, 'doi', '') else article.url
            if original_url:
                actions_html += f"<a href='{original_url}' target='_blank' style='display:inline-block; margin-right: 10px; margin-bottom: 8px; padding: 4px 12px; background: #3b82f6; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>🌐 Xem tại NXB (Gốc)</a>"
            
            # Logic mở khóa qua Sci-Hub / Cảnh báo bài viết trả phí mới
            scihub_info = ""
            is_paywalled = not getattr(article, "pdf_url", "")
            if is_paywalled:
                if getattr(article, "doi", ""):
                    year_val = article.year
                    if year_val and year_val >= 2022:
                        import urllib.parse
                        encoded_title = urllib.parse.quote(article.title)
                        gs_url = f"https://scholar.google.com/scholar?q={encoded_title}"
                        rg_url = f"https://www.researchgate.net/search.Search.html?query={encoded_title}&type=publication"
                        scihub_info = (
                            f"<div style='margin-top: 8px; padding: 10px; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 6px; font-size: 0.85rem; color: #f87171; line-height:1.5;'>"
                            f"⚠️ <strong>Bài viết có phí ({article.display_year}):</strong> Do Sci-Hub đã ngừng cập nhật từ năm 2022, tài liệu này chưa có sẵn trên Sci-Hub.<br>"
                            f"💡 Bạn có thể tìm bản miễn phí (nháp/preprint) qua: "
                            f"<a href='{gs_url}' target='_blank' style='color:#a78bfa; text-decoration:underline; font-weight:500;'>Google Scholar</a> hoặc "
                            f"<a href='{rg_url}' target='_blank' style='color:#a78bfa; text-decoration:underline; font-weight:500;'>ResearchGate</a>"
                            f"</div>"
                        )
                    else:
                        scihub_url = f"https://sci-hub.ru/{article.doi}"
                        actions_html += f"<a href='{scihub_url}' target='_blank' style='display:inline-block; margin-bottom: 8px; padding: 4px 12px; background: #8b5cf6; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>🔑 Mở khóa qua Sci-Hub</a>"
                        scihub_info = f"<div style='font-size:0.78rem; color:var(--text-muted); margin-top:4px;'>*(Sci-Hub chỉ hỗ trợ tài liệu xuất bản trước năm 2022)*</div>"
                else:
                    import urllib.parse
                    encoded_title = urllib.parse.quote(article.title)
                    gs_url = f"https://scholar.google.com/scholar?q={encoded_title}"
                    rg_url = f"https://www.researchgate.net/search.Search.html?query={encoded_title}&type=publication"
                    scihub_info = (
                        f"<div style='margin-top: 8px; padding: 10px; background: rgba(251, 146, 60, 0.10); border: 1px solid rgba(251, 146, 60, 0.25); border-radius: 6px; font-size: 0.85rem; color: #fb923c; line-height:1.5;'>"
                        f"⚠️ Bài báo trả phí này không có mã DOI để mở khóa tự động qua Sci-Hub.<br>"
                        f"💡 Thử tìm kiếm bản copy miễn phí tại: "
                        f"<a href='{gs_url}' target='_blank' style='color:#a78bfa; text-decoration:underline; font-weight:500;'>Google Scholar</a> | "
                        f"<a href='{rg_url}' target='_blank' style='color:#a78bfa; text-decoration:underline; font-weight:500;'>ResearchGate</a>"
                        f"</div>"
                    )
            
            if actions_html:
                st.markdown(f"<div>{actions_html}</div>", unsafe_allow_html=True)
            if scihub_info:
                st.markdown(scihub_info, unsafe_allow_html=True)
                
            citation = format_citation(article, citation_style)
            st.markdown(f"""
            <div class="citation-box">{citation.replace('*', '<em>').replace('</em>', '</em>')}</div>
            """, unsafe_allow_html=True)
            # Copy-friendly text
            st.code(citation.replace("*", ""), language=None)

            # DOI link
            if article.doi:
                st.caption(f"🔗 DOI: [{article.doi}](https://doi.org/{article.doi})")

        with col_del:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Xóa", key=f"del_{article.internal_id}_{index}",
                          help="Xóa khỏi thư viện"):
                should_remove = True

        st.divider()

    return should_remove


def render_library_tab() -> None:
    """
    Hiển thị toàn bộ nội dung Tab Thư viện.
    """
    library: list = st.session_state.get("library", [])

    st.markdown("### 📚 Thư viện Trích dẫn")

    if not library:
        st.markdown("""
        <div class="empty-state">
            <span class="icon">📂</span>
            <p>Thư viện trống. Hãy tìm kiếm và thêm bài báo từ tab <strong>Tìm kiếm</strong>.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ---------------------------------------------------------------
    # Toolbar
    # ---------------------------------------------------------------
    col_style, col_sort, col_clear = st.columns([2, 2, 1])

    with col_style:
        citation_style = st.selectbox(
            "Định dạng trích dẫn",
            options=get_available_styles(),
            key="citation_style_library",
        )

    with col_sort:
        sort_by = st.selectbox(
            "Sắp xếp theo",
            options=["Năm (Mới nhất)", "Năm (Cũ nhất)", "Tác giả (A-Z)", "Số trích dẫn"],
            key="library_sort",
        )

    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Xóa tất cả", key="clear_library"):
            st.session_state.library = []
            storage.save_library(st.session_state.user_id, [])
            st.rerun()

    # Sắp xếp thư viện
    if sort_by == "Năm (Mới nhất)":
        library = sorted(library, key=lambda a: a.year or 0, reverse=True)
    elif sort_by == "Năm (Cũ nhất)":
        library = sorted(library, key=lambda a: a.year or 0)
    elif sort_by == "Tác giả (A-Z)":
        library = sorted(library, key=lambda a: a.first_author_last.lower())
    elif sort_by == "Số trích dẫn":
        library = sorted(library, key=lambda a: a.citation_count, reverse=True)

    # ---------------------------------------------------------------
    # Thống kê nhanh
    # ---------------------------------------------------------------
    scopus_count = sum(1 for a in library if getattr(a, "is_scopus", False))
    wos_count = sum(1 for a in library if getattr(a, "is_wos", False))
    
    col_m1, col_m2, col_m3, col_m4, col_m5, col_m6 = st.columns(6)
    with col_m1:
        st.metric("📄 Tổng bài", len(library))
    with col_m2:
        st.metric("🌟 Scopus", scopus_count)
    with col_m3:
        st.metric("🏆 WoS", wos_count)
    with col_m4:
        years = [a.year for a in library if a.year]
        st.metric("📅 Khoảng năm", f"{min(years)}–{max(years)}" if years else "N/A")
    with col_m5:
        with_doi = sum(1 for a in library if a.doi)
        st.metric("🔗 Có DOI", with_doi)
    with col_m6:
        sources = len(set(a.source for a in library))
        st.metric("🌐 Nguồn", sources)

    st.divider()

    # ---------------------------------------------------------------
    # Danh sách bài báo
    # ---------------------------------------------------------------
    to_remove_index = None
    current_library = st.session_state.library

    for i, article in enumerate(library):
        should_remove = _render_library_card(article, i, citation_style)
        if should_remove:
            # Tìm và xóa từ session_state.library gốc (chưa sort)
            for j, orig_art in enumerate(current_library):
                if orig_art.internal_id == article.internal_id:
                    to_remove_index = j
                    break

    if to_remove_index is not None:
        st.session_state.library.pop(to_remove_index)
        storage.save_library(st.session_state.user_id, st.session_state.library)
        st.toast("🗑️ Đã xóa bài báo khỏi thư viện.", icon="✅")
        st.rerun()
