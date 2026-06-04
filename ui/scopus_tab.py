# ui/scopus_tab.py
# Tab Scopus — Tìm kiếm bài báo trong tạp chí chuẩn Scopus

import streamlit as st
from core import search_engine, storage
from core.models import Article
from citation.formatter import format_citation, get_available_styles
from ui.search_tab import _render_article_card


def _add_to_library(articles_to_add: list, label: str = ""):
    """Helper: Thêm danh sách bài báo vào thư viện, tránh trùng lặp."""
    library = st.session_state.get("library", [])
    existing_ids = {a.internal_id for a in library}
    existing_dois = {a.doi for a in library if a.doi}
    added = 0
    for art in articles_to_add:
        if art.internal_id not in existing_ids and \
           (not art.doi or art.doi not in existing_dois):
            library.append(art)
            existing_ids.add(art.internal_id)
            if art.doi:
                existing_dois.add(art.doi)
            added += 1
    st.session_state.library = library
    storage.save_library(st.session_state.user_id, library)
    msg = f"✅ Đã thêm {added} bài {label}vào thư viện!" if added > 0 else "ℹ️ Không có bài mới để thêm (tất cả đã được lưu)."
    st.toast(msg, icon="📚")
    st.rerun()


def render_scopus_tab() -> None:
    """Hiển thị Tab Scopus — tìm kiếm chuyên biệt bài báo trong tạp chí chuẩn Scopus."""

    # Header nổi bật
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(249,115,22,0.15), rgba(234,88,12,0.05));
                border: 1px solid rgba(249,115,22,0.3); border-radius: 12px;
                padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;">
        <h2 style="margin:0; font-size:1.6rem; background: linear-gradient(135deg,#f97316,#ea580c);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            🌟 Tìm kiếm bài báo chuẩn Scopus
        </h2>
        <p style="margin:0.4rem 0 0 0; color:var(--text-secondary); font-size:0.9rem;">
            Chỉ hiển thị các bài báo được đăng trên tạp chí được <strong>Elsevier Scopus</strong> xếp hạng.
            Bao gồm Q1, Q2, Q3, Q4.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Khởi tạo session state cho tab này
    if "scopus_results" not in st.session_state:
        st.session_state.scopus_results = []
    if "scopus_query" not in st.session_state:
        st.session_state.scopus_query = ""
    if "scopus_error" not in st.session_state:
        st.session_state.scopus_error = None

    # ---------------------------------------------------------------
    # Thanh tìm kiếm
    # ---------------------------------------------------------------
    col_q, col_src = st.columns([4.5, 1.5])
    with col_q:
        query = st.text_input(
            "Từ khóa tìm kiếm Scopus",
            placeholder="Nhập từ khóa, tác giả, hoặc mã DOI... (kết quả sẽ chỉ hiển thị bài Scopus)",
            key="scopus_query_input",
            label_visibility="collapsed",
        )
    with col_src:
        source = st.selectbox(
            "Nguồn",
            options=search_engine.get_available_sources(),
            key="scopus_source",
            label_visibility="collapsed",
        )

    # ---------------------------------------------------------------
    # Bộ lọc nâng cao
    # ---------------------------------------------------------------
    with st.expander("⚙️ Bộ lọc nâng cao", expanded=False):
        c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1.2, 1.2])
        with c1:
            year_from = st.number_input("Từ năm", min_value=1900, max_value=2026,
                                        value=2015, step=1, key="scopus_year_from")
        with c2:
            year_to = st.number_input("Đến năm", min_value=1900, max_value=2026,
                                      value=2026, step=1, key="scopus_year_to")
        with c3:
            limit = st.slider("Số kết quả", min_value=10, max_value=100,
                              value=100, step=10, key="scopus_limit")
        with c4:
            citation_style = st.selectbox(
                "Định dạng trích dẫn",
                options=get_available_styles(),
                key="scopus_citation_style",
            )
        with c5:
            q_filter = st.selectbox(
                "Lọc theo Q-Rank",
                options=["Tất cả (Q1-Q4)", "Q1 only", "Q2 only", "Q1 + Q2"],
                key="scopus_q_filter",
            )
        fields_input = st.text_input(
            "Lĩnh vực (tùy chọn)",
            placeholder="Ví dụ: Education, Linguistics",
            key="scopus_fields",
            help="Lọc theo lĩnh vực (áp dụng với OpenAlex & Semantic Scholar)",
        )

    # ---------------------------------------------------------------
    # Nút Tìm kiếm
    # ---------------------------------------------------------------
    if st.button("🌟 Tìm kiếm bài báo Scopus", key="btn_scopus_search",
                 use_container_width=True, type="primary"):
        if query.strip():
            with st.spinner("⏳ Đang tìm kiếm bài báo Scopus..."):
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
                    indexing_filter="Scopus",
                )
                if result.success:
                    st.session_state.scopus_results = result.articles
                    st.session_state.scopus_query = query
                    st.session_state.scopus_error = None
                    storage.add_to_history(
                        st.session_state.user_id, query, detected_type, source, result.total_count
                    )
                    st.rerun()
                else:
                    st.session_state.scopus_error = result.error
                    st.session_state.scopus_results = []
        else:
            st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm.")

    # ---------------------------------------------------------------
    # Hiển thị lỗi
    # ---------------------------------------------------------------
    if st.session_state.scopus_error:
        st.error(st.session_state.scopus_error)

    # ---------------------------------------------------------------
    # Hiển thị kết quả
    # ---------------------------------------------------------------
    articles = st.session_state.scopus_results

    if articles:
        # Lọc theo Q-rank nếu cần
        filtered = articles
        if q_filter == "Q1 only":
            filtered = [a for a in articles if getattr(a, "scopus_q", "").upper() == "Q1"]
        elif q_filter == "Q2 only":
            filtered = [a for a in articles if getattr(a, "scopus_q", "").upper() == "Q2"]
        elif q_filter == "Q1 + Q2":
            filtered = [a for a in articles if getattr(a, "scopus_q", "").upper() in ("Q1", "Q2")]

        # Đếm theo Q
        q1 = sum(1 for a in articles if getattr(a, "scopus_q", "").upper() == "Q1")
        q2 = sum(1 for a in articles if getattr(a, "scopus_q", "").upper() == "Q2")
        q3 = sum(1 for a in articles if getattr(a, "scopus_q", "").upper() == "Q3")
        q4 = sum(1 for a in articles if getattr(a, "scopus_q", "").upper() == "Q4")
        oa = sum(1 for a in articles if getattr(a, "is_open_access", False))

        # Thanh thống kê
        st.markdown(f"""
        <div class="stats-bar">
            <span class="stat-item">🔎 Truy vấn: <strong class="stat-number">«{st.session_state.scopus_query}»</strong></span>
            <span class="stat-item">🌟 Scopus: <strong class="stat-number">{len(articles)}</strong> bài</span>
            <span class="stat-item" style="color:#f97316;">Q1: <strong class="stat-number">{q1}</strong></span>
            <span class="stat-item" style="color:#fb923c;">Q2: <strong class="stat-number">{q2}</strong></span>
            <span class="stat-item" style="color:#fbbf24;">Q3: <strong class="stat-number">{q3}</strong></span>
            <span class="stat-item" style="color:#a3a3a3;">Q4: <strong class="stat-number">{q4}</strong></span>
            <span class="stat-item">🟢 Open Access: <strong class="stat-number">{oa}</strong></span>
        </div>
        """, unsafe_allow_html=True)

        if not filtered:
            st.info(f"ℹ️ Không có bài báo nào thỏa điều kiện lọc **{q_filter}**. Thử chọn lại bộ lọc.")
        else:
            # Nút thêm tất cả
            if st.button(f"➕ Thêm tất cả {len(filtered)} bài Scopus vào thư viện",
                         key="scopus_add_all"):
                _add_to_library(filtered, "Scopus ")

            st.divider()
            current_style = st.session_state.get("scopus_citation_style", "APA 7th")
            for i, article in enumerate(filtered):
                _render_article_card(article, i, current_style, tab_prefix="scopus_tab")

    elif not st.session_state.scopus_error and st.session_state.scopus_query:
        st.markdown("""
        <div class="empty-state">
            <span class="icon">🌟</span>
            <p>Không tìm thấy bài báo Scopus nào. Hãy thử từ khóa khác hoặc đổi nguồn dữ liệu.</p>
        </div>
        """, unsafe_allow_html=True)

    elif not st.session_state.scopus_query:
        st.markdown("""
        <div class="empty-state">
            <span class="icon">🌟</span>
            <p>Nhập từ khóa ở trên và nhấn <strong>Tìm kiếm bài báo Scopus</strong> để bắt đầu.<br>
            <small>Chỉ hiển thị bài báo được đăng trên tạp chí chuẩn Scopus (Q1 → Q4)</small></p>
        </div>
        """, unsafe_allow_html=True)
