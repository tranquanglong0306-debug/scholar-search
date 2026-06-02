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
        # Tiêu đề bài báo (Nếu là bản free, ưu tiên link PDF trực tiếp khi click vào tiêu đề)
        target_url = article.direct_pdf_url if getattr(article, "pdf_url", "") else article.url
        title_link = f"<a href='{target_url}' target='_blank'>{article.title}</a>" if target_url else article.title
        # Xây dựng các thẻ HTML cẩn thận để tránh lỗi khoảng trắng của Streamlit Markdown
        scopus_text = f"🌟 Scopus ({getattr(article, 'scopus_q')})" if getattr(article, 'scopus_q', '').strip() else "🌟 Scopus"
        wos_text = f"🏆 WoS ({getattr(article, 'wos_q')})" if getattr(article, 'wos_q', '').strip() else "🏆 WoS"
        
        scopus_badge = f'<span class="meta-badge" style="background:#f97316; color:white;">{scopus_text}</span>' if getattr(article, 'is_scopus', False) else ''
        wos_badge = f'<span class="meta-badge" style="background:#8b5cf6; color:white;">{wos_text}</span>' if getattr(article, 'is_wos', False) else ''
        oa_badge = '<span class="meta-badge" style="background:#10b981; color:white; font-weight:bold;">🟢 MIỄN PHÍ</span>' if getattr(article, 'is_open_access', False) else '<span class="meta-badge" style="background:#ef4444; color:white; font-weight:bold;">🔒 TRẢ PHÍ (PAYWALL)</span>'
        journal_html = f'<div class="article-journal">📰 {article.journal}</div>' if article.journal else ''
        tags_html = ('<div class="tag-cloud">' + ''.join(f'<span class="tag">{f}</span>' for f in article.fields_of_study[:4]) + '</div>') if article.fields_of_study else ''

        # Tính toán delay cho hiệu ứng xuất hiện so le tối ưu (chỉ chạy cho 10 card đầu tiên để tối ưu hiệu năng)
        if index < 10:
            delay = index * 0.015
            card_class = "article-card animate-card"
            style_attr = f' style="animation-delay: {delay}s;"'
        else:
            card_class = "article-card"
            style_attr = ""

        html_content = (
            f'<div class="{card_class}"{style_attr}>'
            f'<div class="article-title">{title_link}</div>'
            f'<div class="article-meta"><span class="meta-badge badge-year">📅 {article.display_year}</span><span class="meta-badge badge-source">🔍 {article.source}</span><span class="meta-badge badge-citations">📚 {article.citation_count:,} citations</span>{scopus_badge}{wos_badge}{oa_badge}</div>'
            f'<div class="article-authors">👤 {article.authors_str}</div>'
            f'{journal_html}'
            f'{tags_html}'
            f'</div>'
        )
        
        st.markdown(html_content, unsafe_allow_html=True)

        # Expand abstract và actions
        col_abs, col_add = st.columns([5, 1])

        with col_abs:
            # Các nút truy cập bài báo
            actions_html = ""
            pdf_link = article.direct_pdf_url
            if pdf_link:
                # Kiểm tra xem link có phải direct PDF hay không
                lower_url = pdf_link.lower()
                is_direct_pdf = (".pdf" in lower_url or "/pdf/" in lower_url or "/pdf" in lower_url or "download" in lower_url or "bitstream" in lower_url)
                btn_label = "📥 Tải PDF (Trực tiếp)" if is_direct_pdf else "🔓 Xem bản Free (Kho lưu trữ)"
                btn_bg = "#10b981" if is_direct_pdf else "#fb923c"
                actions_html += f"<a href='{pdf_link}' target='_blank' style='display:inline-block; margin-right: 10px; margin-bottom: 8px; padding: 4px 12px; background: {btn_bg}; color: white; border-radius: 4px; text-decoration: none; font-size: 0.85rem; font-weight: 500;'>{btn_label}</a>"
            
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

            # Nút tự động tìm bản Free qua các APIs
            if is_paywalled:
                if st.button("🔍 Quét bản PDF Free tự động", key=f"scan_{key}", help="Tìm bản PDF công khai miễn phí qua OpenAlex, Semantic Scholar & Unpaywall"):
                    with st.spinner("⏳ Đang quét tìm bản PDF công khai..."):
                        from core import pdf_resolver
                        found_pdf = pdf_resolver.auto_resolve_pdf(article.doi, article.title)
                        if found_pdf:
                            article.pdf_url = found_pdf
                            # Cập nhật trong session state kết quả tìm kiếm
                            for r_art in st.session_state.get("search_results", []):
                                if r_art.internal_id == article.internal_id:
                                    r_art.pdf_url = found_pdf
                            st.toast("🎉 Đã tìm thấy bản PDF miễn phí trực tiếp!", icon="🔓")
                            st.rerun()
                        else:
                            st.error("❌ Không tìm thấy bản PDF Open Access công khai của tài liệu này.")

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
            limit = st.slider("Số kết quả", min_value=10, max_value=100,
                               value=100, step=10, key="result_limit")
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
        scopus_count = sum(1 for a in articles if getattr(a, "is_scopus", False))
        wos_count = sum(1 for a in articles if getattr(a, "is_wos", False))
        oa_count = sum(1 for a in articles if getattr(a, "is_open_access", False))
        st.markdown(f"""
        <div class="stats-bar">
            <span class="stat-item">🔎 Truy vấn: <strong class="stat-number">«{st.session_state.last_query}»</strong></span>
            <span class="stat-item">📄 Hiển thị: <strong class="stat-number">{len(articles)}</strong> / {total:,} kết quả</span>
            <span class="stat-item">🌟 Scopus: <strong class="stat-number">{scopus_count}</strong></span>
            <span class="stat-item">🏆 WoS: <strong class="stat-number">{wos_count}</strong></span>
            <span class="stat-item">🟢 Open Access: <strong class="stat-number">{oa_count}</strong></span>
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
        selected_disp = st.session_state.get("selected_discipline", "Ngôn ngữ học ứng dụng & Ngoại ngữ")
        from core import disciplines
        kws = disciplines.get_keywords_by_discipline(selected_disp)[:4]
        kws_html = ", ".join(f"<em>{kw}</em>" for kw in kws)
        st.markdown(f"""
        <div class="empty-state">
            <span class="icon">📚</span>
            <p>Nhập từ khóa để bắt đầu tìm kiếm.<br>
            <small>Gợi ý ngành <strong>{selected_disp}</strong>: {kws_html}</small></p>
        </div>
        """, unsafe_allow_html=True)
