# ui/search_tab.py
# Tab Tìm kiếm — giao diện chính cho người dùng tìm bài báo

import streamlit as st
from typing import List
from core.models import Article
from core import search_engine
from citation.formatter import format_citation, get_available_styles
from core import storage


def _render_article_card(article: Article, index: int, citation_style: str, tab_prefix: str = "search") -> None:
    """
    Hiển thị một bài báo dưới dạng card đẹp với đầy đủ thông tin.
    """
    # Tạo unique key từ internal_id và tab_prefix để tránh trùng lặp giữa các tab
    key = f"{tab_prefix}_{article.internal_id}_{index}"

    with st.container():
        # Tiêu đề bài báo (Nếu là bản free, ưu tiên link PDF trực tiếp khi click vào tiêu đề)
        target_url = article.direct_pdf_url or getattr(article, "pdf_url", "") or article.url
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
        col_abs, col_copy, col_add = st.columns([4.5, 1.2, 1])

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

        with col_copy:
            # Sprint 1: Quick Copy APA Citation button
            citation_quick = format_citation(article, citation_style)
            st.markdown('<br>', unsafe_allow_html=True)
            if st.button('📋 APA', key=f'copy_apa_{key}', help='Sao chép trích dẫn APA vào clipboard'):
                st.session_state[f'copied_{key}'] = citation_quick.replace('*', '')
                st.toast('✅ Đã copy trích dẫn APA!', icon='📋')
            if st.session_state.get(f'copied_{key}'):
                st.code(st.session_state[f'copied_{key}'], language=None)
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


@st.dialog("🚀 THÔNG BÁO CẬP NHẬT: TÌM KIẾM SCOPUS & WEB OF SCIENCE", width="large")
def show_onboarding_modal() -> None:
    st.markdown("""
    ### 👋 Xin chào, Chúc mừng bạn đã quay lại với ScholarSearch!
    
    Chúng tôi xin giới thiệu bản cập nhật nâng cấp quan trọng với tính năng **Độc quyền & Duy nhất** giúp bạn tra cứu bài báo khoa học chuẩn quốc tế một cách dễ dàng và hiệu quả:
    
    ---
    
    #### 🌟 1. Tính năng Tìm kiếm & Phân loại Scopus / Web of Science (Unique Feature)
    *   **Đối khớp chính xác bằng ISSN & Tên**: Hệ thống tự động đối khớp mã số ISSN tiêu chuẩn và tên tạp chí với danh mục hơn **170.000 tạp chí** uy tín toàn cầu.
    *   **Phân hạng Q1-Q4 & WoS Core**: Tự động nhận diện phân hạng Scopus (Q1, Q2, Q3, Q4) và Web of Science Core Collection (SCIE, SSCI, AHCI, ESCI).
    *   **Phân chia Tab kết quả trực quan**: Lọc nhanh các bài báo Scopus và Web of Science trong tích tắc bằng các tab kết quả chuyên biệt.
    
    ---
    
    #### 💡 2. Các nâng cấp trải nghiệm người dùng (UX/UI) mới:
    *   **Recent Search Chips**: Click vào các từ khóa tìm kiếm gần đây ngay dưới thanh search để tìm kiếm nhanh.
    *   **Clickable Stats Badges**: Click trực tiếp vào các chỉ số thống kê (Scopus, WoS) để chuyển nhanh đến tab kết quả tương ứng.
    *   **Step-by-step Progress Indicator**: Trạng thái tìm kiếm chi tiết theo từng bước trực quan từ phân tích từ khóa đến đối khớp dữ liệu.
    *   **📋 Copy APA Citation**: Sao chép nhanh trích dẫn APA 7th trực tiếp trên từng bài báo.
    
    ---
    *Chúc bạn có những trải nghiệm nghiên cứu tuyệt vời cùng ScholarSearch!*
    """)
    if st.button("Bắt đầu khám phá ngay! 🚀", use_container_width=True, type="primary"):
        st.session_state["show_onboarding"] = False
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

    trigger_search = False
    if st.session_state.get("trigger_search_from_chip", False):
        trigger_search = True
        st.session_state["trigger_search_from_chip"] = False

    # Hiển thị onboarding modal nếu cần
    if st.session_state.get("show_onboarding", False):
        show_onboarding_modal()

    # ---------------------------------------------------------------
    # Thanh tìm kiếm (Smart Search / Ask Anything)
    # ---------------------------------------------------------------
    st.markdown("### 🔎 Tìm kiếm Học thuật Thông minh (Ask Anything)")

    col_q, col_src = st.columns([4.5, 1.5])

    with col_q:
        query = st.text_input(
            "Nhập từ khóa, chủ đề, tác giả hoặc mã DOI bất kỳ...",
            placeholder="Tìm gì cũng được (Ví dụ: trí tuệ nhân tạo, covid-19, author:Nation, 10.1186/...)",
            key="search_query",
            label_visibility="collapsed",
        )

    with col_src:
        source = st.selectbox(
            "Nguồn dữ liệu",
            options=search_engine.get_available_sources(),
            key="search_source",
            label_visibility="collapsed",
        )

    # ---------------------------------------------------------------
    # Recent search chips (Sprint 2 upgrade)
    # ---------------------------------------------------------------
    history = storage.load_history(st.session_state.user_id)
    if history:
        seen = set()
        unique_hist = []
        for h in history:
            q_clean = h['query'].strip()
            if q_clean and q_clean not in seen:
                seen.add(q_clean)
                unique_hist.append(h)
                if len(unique_hist) >= 5:
                    break
        
        if unique_hist:
            cols_chips = st.columns([1] + [1.5] * len(unique_hist) + [4])
            with cols_chips[0]:
                st.markdown("<span style='font-size:0.75rem; color:var(--text-muted); display:inline-block; padding-top:6px;'>🕒 Gần đây:</span>", unsafe_allow_html=True)
            for idx, h in enumerate(unique_hist):
                label = h['query']
                if len(label) > 15:
                    label = label[:13] + "..."
                with cols_chips[idx + 1]:
                    if st.button(f"🔍 {label}", key=f"chip_{idx}_{h['query']}", help=f"Tìm lại: {h['query']}", use_container_width=True):
                        st.session_state.search_query = h['query']
                        st.session_state.search_source = h['source']
                        st.session_state.trigger_search_from_chip = True
                        st.rerun()

    # ---------------------------------------------------------------
    # Bộ lọc nâng cao (collapsible)
    # ---------------------------------------------------------------
    with st.expander("⚙️ Bộ lọc nâng cao", expanded=False):
        f_col1, f_col2, f_col3, f_col4 = st.columns([1, 1, 1, 1.5])
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

    if (search_clicked or trigger_search) and query.strip():
        status_box = st.empty()
        progress_bar = st.progress(0)

        def ui_status_callback(step: int, msg: str):
            import time
            progress_bar.progress(step / 4.0)
            status_box.markdown(f"""
            <div style="background: rgba(108, 99, 255, 0.08); border: 1px solid rgba(108, 99, 255, 0.3); 
                        border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 1rem;
                        display: flex; align-items: center; gap: 0.75rem;">
                <div style="font-size: 1.25rem;">⏳</div>
                <div>
                    <span style="font-size: 0.72rem; color: var(--accent-secondary); font-weight: bold; text-transform: uppercase;">Bước {step} của 4</span>
                    <div style="color: var(--text-primary); font-size: 0.9rem; font-weight: 500; margin-top: 2px;">{msg}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.4)

        import re
        detected_type = "keyword"
        if re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', query, re.IGNORECASE):
            detected_type = "doi"
        elif query.lower().startswith("author:") or query.lower().startswith("tác giả:"):
            detected_type = "author"

        result = search_engine.search(
            query=query,
            search_type=detected_type,
            source=source,
            limit=limit,
            year_from=int(year_from) if year_from else None,
            year_to=int(year_to) if year_to else None,
            fields_of_study=fields_input.strip() or None,
            indexing_filter="Tất cả",
            status_callback=ui_status_callback,
        )

        status_box.empty()
        progress_bar.empty()

        if result.success:
            st.session_state.search_results = result.articles
            st.session_state.last_query = query
            st.session_state.search_error = None
            st.session_state.search_total = result.total_count
            # Reset active tab to default dynamic label
            st.session_state["active_results_tab"] = f"📚 Tất cả ({len(result.articles)})"
            # Lưu vào lịch sử
            storage.add_to_history(st.session_state.user_id, query, detected_type, source, result.total_count)
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
        scopus_articles = [a for a in articles if getattr(a, "is_scopus", False)]
        wos_articles = [a for a in articles if getattr(a, "is_wos", False)]
        oa_count = sum(1 for a in articles if getattr(a, "is_open_access", False))
        
        # Define tab labels and synchronize tab state
        tab_labels = [
            f"📚 Tất cả ({len(sorted_articles)})",
            f"🌟 Scopus ({len(scopus_articles)})",
            f"🏆 Web of Science ({len(wos_articles)})"
        ]
        
        current_tab = st.session_state.get("active_results_tab")
        if current_tab:
            if current_tab.startswith("📚 Tất cả"):
                st.session_state["active_results_tab"] = tab_labels[0]
            elif current_tab.startswith("🌟 Scopus"):
                st.session_state["active_results_tab"] = tab_labels[1]
            elif current_tab.startswith("🏆 Web of Science"):
                st.session_state["active_results_tab"] = tab_labels[2]
            else:
                st.session_state["active_results_tab"] = tab_labels[0]
        else:
            st.session_state["active_results_tab"] = tab_labels[0]

        st.markdown(f"""
        <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 1rem; margin-bottom: 0.75rem; font-size: 0.85rem;">
            🔎 Truy vấn hiện tại: <strong style="color: var(--accent-secondary);">«{st.session_state.last_query}»</strong>
        </div>
        """, unsafe_allow_html=True)

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1:
            if st.button(f"📚 Tất cả ({len(sorted_articles)})", key="click_stat_all", use_container_width=True, help="Bấm để chuyển sang tab Tất cả"):
                st.session_state["active_results_tab"] = tab_labels[0]
                st.rerun()
        with stat_col2:
            if st.button(f"🌟 Scopus ({len(scopus_articles)})", key="click_stat_scopus", use_container_width=True, help="Bấm để chuyển sang tab Scopus"):
                st.session_state["active_results_tab"] = tab_labels[1]
                st.rerun()
        with stat_col3:
            if st.button(f"🏆 WoS ({len(wos_articles)})", key="click_stat_wos", use_container_width=True, help="Bấm để chuyển sang tab Web of Science"):
                st.session_state["active_results_tab"] = tab_labels[2]
                st.rerun()
        with stat_col4:
            st.button(f"🟢 Open Access ({oa_count})", key="click_stat_oa", use_container_width=True, disabled=True)

        # Định dạng trích dẫn

        # --- SORT & FILTER controls (Sprint 1 upgrade) ---
        sort_col, filter_col = st.columns([3, 1])
        with sort_col:
            sort_option = st.selectbox(
                "Sắp xếp",
                options=["Mặc định", "📅 Mới nhất", "📊 Nhiều trích dẫn nhất", "🌟 Scopus/Q1 trước", "🔓 Open Access trước"],
                key="search_sort_option",
                label_visibility="collapsed",
            )
        with filter_col:
            show_oa_only = st.checkbox("Chỉ Open Access", key="filter_oa_only")

        # Apply sort
        sorted_articles = list(articles)
        if sort_option == "📅 Mới nhất":
            sorted_articles.sort(key=lambda a: a.year or 0, reverse=True)
        elif sort_option == "📊 Nhiều trích dẫn nhất":
            sorted_articles.sort(key=lambda a: a.citation_count, reverse=True)
        elif sort_option == "🌟 Scopus/Q1 trước":
            sorted_articles.sort(key=lambda a: (
                0 if getattr(a, 'scopus_q', '').strip() in ['Q1', 'Q2'] else
                1 if getattr(a, 'is_scopus', False) or getattr(a, 'is_wos', False) else 2
            ))
        elif sort_option == "🔓 Open Access trước":
            sorted_articles.sort(key=lambda a: 0 if getattr(a, 'is_open_access', False) else 1)

        # Apply OA filter
        if show_oa_only:
            sorted_articles = [a for a in sorted_articles if getattr(a, 'is_open_access', False)]
            scopus_articles = [a for a in sorted_articles if getattr(a, 'is_scopus', False)]
            wos_articles = [a for a in sorted_articles if getattr(a, 'is_wos', False)]

        current_style = st.session_state.get("citation_style_search", "APA 7th")

        # Tạo 3 tab riêng biệt hiển thị kết quả
        display_articles = sorted_articles
        tab_all_res, tab_scopus_res, tab_wos_res = st.tabs(tab_labels, key="active_results_tab")

        with tab_all_res:
            if articles:
                # Nút thêm tất cả vào thư viện cho tab Tất cả
                if st.button("➕ Thêm tất cả vào thư viện", key="add_all_all"):
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
                for i, article in enumerate(display_articles):
                    _render_article_card(article, i, current_style, tab_prefix="all")
            else:
                st.markdown("<p style='text-align:center; color:var(--text-muted);'>Không có kết quả nào.</p>", unsafe_allow_html=True)

        with tab_scopus_res:
            if scopus_articles:
                # Nút thêm tất cả bài Scopus vào thư viện
                if st.button("➕ Thêm tất cả bài Scopus vào thư viện", key="add_all_scopus"):
                    library = st.session_state.get("library", [])
                    existing_ids = {a.internal_id for a in library}
                    existing_dois = {a.doi for a in library if a.doi}
                    added = 0
                    for art in scopus_articles:
                        if art.internal_id not in existing_ids and \
                           (not art.doi or art.doi not in existing_dois):
                            library.append(art)
                            existing_ids.add(art.internal_id)
                            if art.doi:
                                existing_dois.add(art.doi)
                            added += 1
                    st.session_state.library = library
                    storage.save_library(st.session_state.user_id, library)
                    st.toast(f"✅ Đã thêm {added} bài thuộc chuẩn Scopus vào thư viện!", icon="📚")
                    st.rerun()
                st.divider()
                for i, article in enumerate(scopus_articles):
                    _render_article_card(article, i, current_style, tab_prefix="scopus")
            else:
                st.markdown("""
                <div class="empty-state">
                    <span class="icon">🌟</span>
                    <p>Không tìm thấy bài báo nào thuộc danh mục Scopus trong kết quả này.</p>
                </div>
                """, unsafe_allow_html=True)

        with tab_wos_res:
            if wos_articles:
                # Nút thêm tất cả bài WoS vào thư viện
                if st.button("➕ Thêm tất cả bài WoS vào thư viện", key="add_all_wos"):
                    library = st.session_state.get("library", [])
                    existing_ids = {a.internal_id for a in library}
                    existing_dois = {a.doi for a in library if a.doi}
                    added = 0
                    for art in wos_articles:
                        if art.internal_id not in existing_ids and \
                           (not art.doi or art.doi not in existing_dois):
                            library.append(art)
                            existing_ids.add(art.internal_id)
                            if art.doi:
                                existing_dois.add(art.doi)
                            added += 1
                    st.session_state.library = library
                    storage.save_library(st.session_state.user_id, library)
                    st.toast(f"✅ Đã thêm {added} bài thuộc chuẩn Web of Science vào thư viện!", icon="📚")
                    st.rerun()
                st.divider()
                for i, article in enumerate(wos_articles):
                    _render_article_card(article, i, current_style, tab_prefix="wos")
            else:
                st.markdown("""
                <div class="empty-state">
                    <span class="icon">🏆</span>
                    <p>Không tìm thấy bài báo nào thuộc danh mục Web of Science trong kết quả này.</p>
                </div>
                """, unsafe_allow_html=True)

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
        kws = disciplines.get_keywords_by_discipline(selected_disp)
        
        st.markdown(f"""
        <div class="empty-state" style="padding: 2.5rem 1.5rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius); margin-top: 1.5rem; box-shadow: var(--shadow-card);">
            <div class="icon" style="font-size: 2.5rem; margin-bottom: 0.75rem;">📚</div>
            <h4 style="margin-top: 0; color: var(--text-primary);">Bắt đầu Tra cứu Học thuật</h4>
            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem;">Hãy nhập từ khóa, chủ đề, tên tác giả hoặc mã DOI ở thanh tìm kiếm phía trên.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"##### 💡 Gợi ý từ khóa cho ngành **{selected_disp}**:")
        kws_to_show = kws[:4]
        cols_kws = st.columns(len(kws_to_show))
        for idx, kw in enumerate(kws_to_show):
            with cols_kws[idx]:
                if st.button(f"🔸 {kw}", key=f"empty_suggest_{idx}_{kw}", use_container_width=True):
                    st.session_state.search_query = kw
                    st.session_state.search_source = "OpenAlex"
                    st.session_state.search_query_trigger = True
                    st.rerun()



