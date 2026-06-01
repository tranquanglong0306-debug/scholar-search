# ui/search_tab.py
# Tab Tìm kiếm — giao diện chính cho người dùng tìm bài báo

import streamlit as st
from typing import List
from core.models import Article
from core import search_engine
from citation.formatter import format_citation, get_available_styles
from core import storage


def _render_article_card(article: Article, index: int, citation_style: str) -> None:
    """
    Hiển thị một bài báo dưới dạng card đẹp với đầy đủ thông tin.
    """
    # Tạo unique key từ internal_id
    key = f"search_{article.internal_id}_{index}"

    with st.container():
        # Tiêu đề bài báo (Sử dụng thẻ <a> HTML thay vì Markdown vì nó nằm trong block HTML)
        title_link = f"<a href='{article.url}' target='_blank'>{article.title}</a>" if article.url else article.title
        # Xây dựng các thẻ HTML cẩn thận để tránh lỗi khoảng trắng của Streamlit Markdown
        scopus_badge = '<span class="meta-badge" style="background:#f97316; color:white;">🌟 Scopus</span>' if getattr(article, 'is_scopus', False) else ''
        wos_badge = '<span class="meta-badge" style="background:#8b5cf6; color:white;">🏆 WoS</span>' if getattr(article, 'is_wos', False) else ''
        journal_html = f'<div class="article-journal">📰 {article.journal}</div>' if article.journal else ''
        tags_html = ('<div class="tag-cloud">' + ''.join(f'<span class="tag">{f}</span>' for f in article.fields_of_study[:4]) + '</div>') if article.fields_of_study else ''

        html_content = f'''<div class="article-card">
            <div class="article-title">{title_link}</div>
            <div class="article-meta"><span class="meta-badge badge-year">📅 {article.display_year}</span><span class="meta-badge badge-source">🔍 {article.source}</span><span class="meta-badge badge-citations">📚 {article.citation_count:,} citations</span>{scopus_badge}{wos_badge}</div>
            <div class="article-authors">👤 {article.authors_str}</div>
            {journal_html}
            {tags_html}
        </div>'''
        
        st.markdown(html_content, unsafe_allow_html=True)

        # Expand abstract và actions
        col_abs, col_add = st.columns([5, 1])

        with col_abs:
            # Các nút truy cập bài báo
            actions_html = ""
            if getattr(article, "pdf_url", ""):
                actions_html += f"<a href='{article.pdf_url}' target='_blank' style='display:inline-block; margin-right: 10px; margin-bottom: 8px; padding: 4px 12px; background: #ef4444; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>📥 Đọc/Tải PDF</a>"
            if article.url:
                actions_html += f"<a href='{article.url}' target='_blank' style='display:inline-block; margin-bottom: 8px; padding: 4px 12px; background: #3b82f6; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>🔗 Xem tại NXB (Gốc)</a>"
            
            if actions_html:
                st.markdown(f"<div>{actions_html}</div>", unsafe_allow_html=True)

            if article.has_abstract:
                with st.expander("📖 Xem tóm tắt (Abstract)", expanded=False):
                    st.markdown(f"""
                    <div class="abstract-text">{article.abstract}</div>
                    """, unsafe_allow_html=True)

                    # Citation preview trong expander
                    citation_text = format_citation(article, citation_style)
                    st.markdown("**📝 Trích dẫn:**")
                    st.markdown(f"""
                    <div class="citation-box">{citation_text.replace("*", "<em>").replace("</em>", "</em>")}</div>
                    """, unsafe_allow_html=True)
                    st.code(citation_text.replace("*", ""), language=None)
            else:
                st.caption("_Không có abstract._")

        with col_add:
            # Kiểm tra bài đã được thêm vào thư viện chưa
            library = st.session_state.get("library", [])
            already_added = any(
                a.internal_id == article.internal_id or
                (a.doi and a.doi == article.doi and a.doi)
                for a in library
            )

            if already_added:
                st.markdown("✅ **Đã lưu**")
            else:
                if st.button("➕ Lưu", key=f"add_{key}", help="Thêm vào thư viện"):
                    st.session_state.library.append(article)
                    storage.save_library(st.session_state.user_id, st.session_state.library)
                    st.toast(f"✅ Đã thêm: «{article.title[:40]}...»", icon="📚")
                    st.rerun()


def render_search_tab() -> None:
    """
    Hiển thị toàn bộ nội dung Tab Tìm kiếm.
    """
    # ---------------------------------------------------------------
    # Khởi tạo session state
    # ---------------------------------------------------------------
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""
    if "search_error" not in st.session_state:
        st.session_state.search_error = None

    # ---------------------------------------------------------------
    # Thanh tìm kiếm
    # ---------------------------------------------------------------
    st.markdown("### 🔎 Tìm kiếm Bài báo Khoa học")

    col_q, col_type, col_src = st.columns([3, 1.5, 1.5])

    with col_q:
        query = st.text_input(
            "Từ khóa / Tên tác giả / DOI",
            placeholder="Ví dụ: task-based language teaching, Nation 2001, 10.1017/...",
            key="search_query",
            label_visibility="collapsed",
        )

    with col_type:
        search_type = st.selectbox(
            "Loại tìm kiếm",
            options=["Từ khóa", "Tác giả", "DOI"],
            key="search_type",
            label_visibility="collapsed",
        )
        search_type_map = {"Từ khóa": "keyword", "Tác giả": "author", "DOI": "doi"}

    with col_src:
        source = st.selectbox(
            "Nguồn",
            options=search_engine.get_available_sources(),
            key="search_source",
            label_visibility="collapsed",
        )

    # ---------------------------------------------------------------
    # Bộ lọc nâng cao (collapsible)
    # ---------------------------------------------------------------
    with st.expander("⚙️ Bộ lọc nâng cao", expanded=False):
        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([1, 1, 1, 1.2, 1.2])
        with f_col1:
            year_from = st.number_input("Từ năm", min_value=1900, max_value=2026,
                                         value=2000, step=1, key="year_from")
        with f_col2:
            year_to = st.number_input("Đến năm", min_value=1900, max_value=2026,
                                       value=2026, step=1, key="year_to")
        with f_col3:
            limit = st.slider("Số kết quả", min_value=5, max_value=50,
                               value=20, step=5, key="result_limit")
        with f_col4:
            citation_style = st.selectbox(
                "Định dạng trích dẫn",
                options=get_available_styles(),
                key="citation_style_search",
            )
        with f_col5:
            indexing_filter = st.selectbox(
                "Chuẩn quốc tế",
                options=["Tất cả", "Scopus", "Web of Science"],
                key="indexing_filter",
            )

        # Lĩnh vực mặc định cho Applied Linguistics
        fields_input = st.text_input(
            "Lĩnh vực (tùy chọn)",
            value="",
            placeholder="Ví dụ: Education, Linguistics",
            key="fields_filter",
            help="Nhập lĩnh vực để lọc (áp dụng với Semantic Scholar & OpenAlex)",
        )

    # ---------------------------------------------------------------
    # Nút Tìm kiếm
    # ---------------------------------------------------------------
    search_clicked = st.button(
        "🔍 Tìm kiếm",
        key="btn_search",
        use_container_width=True,
        type="primary",
    )

    if search_clicked and query.strip():
        with st.spinner("⏳ Đang tìm kiếm..."):
            result = search_engine.search(
                query=query,
                search_type=search_type_map[search_type],
                source=source,
                limit=limit,
                year_from=int(year_from) if year_from else None,
                year_to=int(year_to) if year_to else None,
                fields_of_study=fields_input.strip() or None,
                indexing_filter=indexing_filter,
            )

            if result.success:
                st.session_state.search_results = result.articles
                st.session_state.last_query = query
                st.session_state.search_error = None
                st.session_state.search_total = result.total_count
                # Lưu vào lịch sử
                storage.add_to_history(st.session_state.user_id, query, search_type_map[search_type], source, result.total_count)
                st.rerun()
            else:
                st.session_state.search_error = result.error
                st.session_state.search_results = []

    # ---------------------------------------------------------------
    # Hiển thị lỗi
    # ---------------------------------------------------------------
    if st.session_state.search_error:
        st.error(st.session_state.search_error)

    # ---------------------------------------------------------------
    # Hiển thị kết quả
    # ---------------------------------------------------------------
    articles = st.session_state.search_results

    if articles:
        total = st.session_state.get("search_total", len(articles))
        st.markdown(f"""
        <div class="stats-bar">
            <span class="stat-item">🔎 Truy vấn: <strong class="stat-number">«{st.session_state.last_query}»</strong></span>
            <span class="stat-item">📄 Hiển thị: <strong class="stat-number">{len(articles)}</strong> / {total:,} kết quả</span>
            <span class="stat-item">📚 Đã lưu: <strong class="stat-number">{len(st.session_state.get('library', []))}</strong></span>
        </div>
        """, unsafe_allow_html=True)

        # Nút thêm tất cả
        col_all, col_sort = st.columns([2, 2])
        with col_all:
            if st.button("➕ Thêm tất cả vào thư viện", key="add_all"):
                library = st.session_state.get("library", [])
                existing_ids = {a.internal_id for a in library}
                existing_dois = {a.doi for a in library if a.doi}
                added = 0
                for art in articles:
                    if art.internal_id not in existing_ids and \
                       (not art.doi or art.doi not in existing_dois):
                        library.append(art)
                        existing_ids.add(art.internal_id)
                        if art.doi:
                            existing_dois.add(art.doi)
                        added += 1
                st.session_state.library = library
                storage.save_library(st.session_state.user_id, library)
                st.toast(f"✅ Đã thêm {added} bài vào thư viện!", icon="📚")
                st.rerun()

        st.divider()

        # Render từng card
        current_style = st.session_state.get("citation_style_search", "APA 7th")
        for i, article in enumerate(articles):
            _render_article_card(article, i, current_style)

    elif not st.session_state.search_error and st.session_state.last_query:
        st.markdown("""
        <div class="empty-state">
            <span class="icon">🔍</span>
            <p>Không tìm thấy kết quả nào. Hãy thử từ khóa khác hoặc đổi nguồn dữ liệu.</p>
        </div>
        """, unsafe_allow_html=True)

    elif not st.session_state.last_query:
        st.markdown("""
        <div class="empty-state">
            <span class="icon">📚</span>
            <p>Nhập từ khóa để bắt đầu tìm kiếm.<br>
            <small>Gợi ý: <em>task-based language teaching</em>, <em>second language acquisition</em>, <em>EFL vocabulary learning</em></small></p>
        </div>
        """, unsafe_allow_html=True)
