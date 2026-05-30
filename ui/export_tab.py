# ui/export_tab.py
# Tab Xuất dữ liệu — xuất thư viện ra các định dạng file

import streamlit as st
from datetime import datetime
from citation.exporter import (
    export_bibtex_bytes,
    export_csv_bytes,
    export_excel_bytes,
    export_apa_txt_bytes,
    export_bibtex,
    export_apa_txt,
)
from citation.formatter import get_available_styles, format_citation


def render_export_tab() -> None:
    """
    Hiển thị toàn bộ nội dung Tab Xuất dữ liệu.
    """
    library = st.session_state.get("library", [])

    st.markdown("### 📤 Xuất Dữ liệu Thư viện")

    if not library:
        st.markdown("""
        <div class="empty-state">
            <span class="icon">📭</span>
            <p>Thư viện trống. Hãy thêm bài báo trước khi xuất.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ---------------------------------------------------------------
    # Chọn style trích dẫn
    # ---------------------------------------------------------------
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        export_style = st.selectbox(
            "📝 Định dạng trích dẫn xuất ra",
            options=get_available_styles(),
            key="export_style",
        )
    with col_opt2:
        st.metric("📚 Số bài sẵn sàng xuất", len(library))

    st.divider()

    # ---------------------------------------------------------------
    # Section 1: BibTeX
    # ---------------------------------------------------------------
    st.markdown("#### 📄 BibTeX (.bib) — Dùng cho Zotero, Mendeley, LaTeX")
    st.markdown(
        "_BibTeX là định dạng tiêu chuẩn được hỗ trợ bởi **Zotero**, **Mendeley**, "
        "**JabRef** và **LaTeX**. Đây là lựa chọn tốt nhất để quản lý tài liệu._"
    )

    col_bib_dl, col_bib_prev = st.columns([1, 2])
    with col_bib_dl:
        bib_bytes = export_bibtex_bytes(library)
        filename_bib = f"references_{datetime.now().strftime('%Y%m%d')}.bib"
        st.download_button(
            label="⬇️ Tải BibTeX (.bib)",
            data=bib_bytes,
            file_name=filename_bib,
            mime="application/x-bibtex",
            key="dl_bibtex",
            use_container_width=True,
        )

        st.markdown(f"""
        <div style="margin-top:0.5rem; padding:0.5rem 0.75rem;
             background:rgba(52,211,153,0.08); border-radius:8px;
             border:1px solid rgba(52,211,153,0.2); font-size:0.8rem;">
            📁 <strong>{filename_bib}</strong><br>
            📊 {len(library)} entries · {len(bib_bytes):,} bytes
        </div>
        """, unsafe_allow_html=True)

    with col_bib_prev:
        with st.expander("👁️ Xem trước BibTeX", expanded=False):
            bibtex_preview = export_bibtex(library[:3])  # Preview 3 entries đầu
            if len(library) > 3:
                bibtex_preview += f"\n\n% ... và {len(library) - 3} entries khác"
            st.code(bibtex_preview, language="bibtex")

    st.divider()

    # ---------------------------------------------------------------
    # Section 2: Excel
    # ---------------------------------------------------------------
    st.markdown("#### 📊 Excel (.xlsx) — Bảng dữ liệu đầy đủ")
    st.markdown(
        "_File Excel bao gồm **2 sheet**: (1) Metadata đầy đủ, "
        f"(2) Danh sách trích dẫn **{export_style}** sẵn sàng copy._"
    )

    col_xl_dl, col_xl_info = st.columns([1, 2])
    with col_xl_dl:
        xl_bytes = export_excel_bytes(library, export_style)
        filename_xl = f"references_{datetime.now().strftime('%Y%m%d')}.xlsx"
        st.download_button(
            label="⬇️ Tải Excel (.xlsx)",
            data=xl_bytes,
            file_name=filename_xl,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_excel",
            use_container_width=True,
        )

    with col_xl_info:
        st.markdown(f"""
        <div style="padding:0.75rem 1rem; background:var(--bg-card);
             border:1px solid var(--border-color); border-radius:8px; font-size:0.85rem;">
            <strong>📋 Nội dung file Excel:</strong><br>
            • Sheet "Metadata": Tiêu đề, Tác giả, Năm, Tạp chí, DOI, Abstract, ...<br>
            • Sheet "{export_style} Citations": Danh sách trích dẫn đã định dạng<br>
            • Hỗ trợ tiếng Việt (UTF-8)
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ---------------------------------------------------------------
    # Section 3: CSV
    # ---------------------------------------------------------------
    st.markdown("#### 📋 CSV (.csv) — Dữ liệu thô, tương thích mọi phần mềm")

    col_csv_dl, col_csv_info = st.columns([1, 2])
    with col_csv_dl:
        csv_bytes = export_csv_bytes(library)
        filename_csv = f"references_{datetime.now().strftime('%Y%m%d')}.csv"
        st.download_button(
            label="⬇️ Tải CSV (.csv)",
            data=csv_bytes,
            file_name=filename_csv,
            mime="text/csv",
            key="dl_csv",
            use_container_width=True,
        )

    with col_csv_info:
        st.markdown("""
        <div style="padding:0.75rem 1rem; background:var(--bg-card);
             border:1px solid var(--border-color); border-radius:8px; font-size:0.85rem;">
            <strong>📋 Mẹo sử dụng CSV:</strong><br>
            • Mở bằng Excel: <em>Data → From Text/CSV</em><br>
            • Import vào Zotero: <em>File → Import → CSV</em><br>
            • Mã hóa UTF-8-BOM (hỗ trợ tiếng Việt trong Excel)
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ---------------------------------------------------------------
    # Section 4: APA List (TXT)
    # ---------------------------------------------------------------
    st.markdown(f"#### 📝 Danh sách Tài liệu Tham khảo (.txt) — {export_style}")
    st.markdown(
        "_File text thuần chứa danh sách tài liệu tham khảo sắp xếp theo alphabet, "
        "sẵn sàng copy vào Word/Google Docs._"
    )

    col_txt_dl, col_txt_prev = st.columns([1, 2])
    with col_txt_dl:
        txt_bytes = export_apa_txt_bytes(library, export_style)
        filename_txt = f"references_{export_style.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt"
        st.download_button(
            label=f"⬇️ Tải References (.txt)",
            data=txt_bytes,
            file_name=filename_txt,
            mime="text/plain",
            key="dl_txt",
            use_container_width=True,
        )

    with col_txt_prev:
        with st.expander(f"👁️ Xem trước danh sách {export_style}", expanded=True):
            txt_preview = export_apa_txt(library, export_style)
            st.text_area(
                label="",
                value=txt_preview,
                height=250,
                key="txt_preview",
                label_visibility="collapsed",
            )

    st.divider()

    # ---------------------------------------------------------------
    # Hướng dẫn import vào Zotero / Mendeley
    # ---------------------------------------------------------------
    with st.expander("📘 Hướng dẫn import vào Zotero & Mendeley", expanded=False):
        col_z, col_m = st.columns(2)
        with col_z:
            st.markdown("""
            **🟠 Zotero**
            1. Mở Zotero Desktop
            2. Vào **File → Import...**
            3. Chọn file `.bib` đã tải
            4. Chọn "Place imported collections and items into new collection"
            5. Click **Next** → **Done**

            _Hoặc: Kéo thả file `.bib` trực tiếp vào Zotero_
            """)
        with col_m:
            st.markdown("""
            **🔵 Mendeley Reference Manager**
            1. Mở Mendeley
            2. Vào **File → Import → BibTeX (.bib)**
            3. Chọn file `.bib` đã tải
            4. Click **Open**
            5. Bài báo sẽ xuất hiện trong "All Documents"

            _Lưu ý: Mendeley cũng hỗ trợ import CSV_
            """)
