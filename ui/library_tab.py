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

    with st.container():
        # Header card
        st.markdown(f"""
        <div class="article-card">
            <div class="article-title">
                <span style="color:#6c63ff;font-size:0.85rem;font-weight:600;">#{index + 1}</span>
                {'&nbsp;<a href="' + article.url + '" target="_blank">' + article.title + '</a>' if article.url else '&nbsp;' + article.title}
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
                actions_html += f"<a href='{article.pdf_url}' target='_blank' style='display:inline-block; margin-right: 10px; margin-bottom: 8px; padding: 4px 12px; background: #ef4444; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>📥 Đọc/Tải PDF</a>"
            if article.url:
                actions_html += f"<a href='{article.url}' target='_blank' style='display:inline-block; margin-bottom: 8px; padding: 4px 12px; background: #3b82f6; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>🔗 Xem tại NXB (Gốc)</a>"
            
            if actions_html:
                st.markdown(f"<div>{actions_html}</div>", unsafe_allow_html=True)
                
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
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("📄 Tổng bài", len(library))
    with col_m2:
        years = [a.year for a in library if a.year]
        st.metric("📅 Span", f"{min(years)}–{max(years)}" if years else "N/A")
    with col_m3:
        with_doi = sum(1 for a in library if a.doi)
        st.metric("🔗 Có DOI", with_doi)
    with col_m4:
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
