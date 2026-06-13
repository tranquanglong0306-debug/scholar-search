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
            <p>Thư viện của bạn đang trống. Hãy tìm kiếm bài báo và lưu lại trước khi xuất dữ liệu.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ---------------------------------------------------------------
    # Cấu hình phong cách & Thống kê nhanh
    # ---------------------------------------------------------------
    col_opt1, col_opt2 = st.columns([4, 2])
    with col_opt1:
        export_style = st.selectbox(
            "📝 Định dạng trích dẫn xuất ra",
            options=get_available_styles(),
            key="export_style",
            help="Áp dụng định dạng trích dẫn này cho file Excel và Text (.txt)"
        )
    with col_opt2:
        st.metric("📚 Thư viện hiện tại", f"{len(library)} bài viết")

    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------
    # Bố cục 4 cột xuất dữ liệu song song (Rút gọn & Tiện lợi)
    # ---------------------------------------------------------------
    col_bib, col_xl, col_txt, col_csv = st.columns(4)

    # 1. BibTeX
    with col_bib:
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: var(--bg-card); 
                    border: 1px solid var(--border-color); border-radius: 8px; min-height: 110px;">
            <div style="font-size: 1.8rem; margin-bottom: 6px;">📄</div>
            <strong style="font-size: 0.9rem; color: var(--text-primary);">BibTeX (.bib)</strong>
            <p style="margin: 4px 0 0 0; font-size: 0.75rem; color: var(--text-secondary); line-height: 1.3;">Cho Zotero, Mendeley, LaTeX</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        
        bib_bytes = export_bibtex_bytes(library)
        filename_bib = f"references_{datetime.now().strftime('%Y%m%d')}.bib"
        st.download_button(
            label="⬇️ Tải file .bib",
            data=bib_bytes,
            file_name=filename_bib,
            mime="application/x-bibtex",
            key="dl_bibtex",
            use_container_width=True,
        )

    # 2. Excel
    with col_xl:
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: var(--bg-card); 
                    border: 1px solid var(--border-color); border-radius: 8px; min-height: 110px;">
            <div style="font-size: 1.8rem; margin-bottom: 6px;">📊</div>
            <strong style="font-size: 0.9rem; color: var(--text-primary);">Excel (.xlsx)</strong>
            <p style="margin: 4px 0 0 0; font-size: 0.75rem; color: var(--text-secondary); line-height: 1.3;">Bảng dữ liệu & trích dẫn</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        
        xl_bytes = export_excel_bytes(library, export_style)
        filename_xl = f"references_{datetime.now().strftime('%Y%m%d')}.xlsx"
        st.download_button(
            label="⬇️ Tải file .xlsx",
            data=xl_bytes,
            file_name=filename_xl,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_excel",
            use_container_width=True,
        )

    # 3. References TXT
    with col_txt:
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: var(--bg-card); 
                    border: 1px solid var(--border-color); border-radius: 8px; min-height: 110px;">
            <div style="font-size: 1.8rem; margin-bottom: 6px;">📝</div>
            <strong style="font-size: 0.9rem; color: var(--text-primary);">Text (.txt)</strong>
            <p style="margin: 4px 0 0 0; font-size: 0.75rem; color: var(--text-secondary); line-height: 1.3;">Sắp xếp A-Z sẵn sàng copy</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        
        txt_bytes = export_apa_txt_bytes(library, export_style)
        filename_txt = f"references_{export_style.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt"
        st.download_button(
            label="⬇️ Tải file .txt",
            data=txt_bytes,
            file_name=filename_txt,
            mime="text/plain",
            key="dl_txt",
            use_container_width=True,
        )

    # 4. CSV
    with col_csv:
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: var(--bg-card); 
                    border: 1px solid var(--border-color); border-radius: 8px; min-height: 110px;">
            <div style="font-size: 1.8rem; margin-bottom: 6px;">📋</div>
            <strong style="font-size: 0.9rem; color: var(--text-primary);">CSV (.csv)</strong>
            <p style="margin: 4px 0 0 0; font-size: 0.75rem; color: var(--text-secondary); line-height: 1.3;">Dữ liệu thô đa năng</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        
        csv_bytes = export_csv_bytes(library)
        filename_csv = f"references_{datetime.now().strftime('%Y%m%d')}.csv"
        st.download_button(
            label="⬇️ Tải file .csv",
            data=csv_bytes,
            file_name=filename_csv,
            mime="text/csv",
            key="dl_csv",
            use_container_width=True,
        )

    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------
    # Bộ xem trước kết quả thông minh
    # ---------------------------------------------------------------
    st.markdown("##### 👁️ Xem trước nội dung xuất")
    tab_prev_txt, tab_prev_bib = st.columns(2)
    
    with tab_prev_txt:
        with st.expander(f"Xem trước trích dẫn ({export_style})", expanded=True):
            txt_preview = export_apa_txt(library, export_style)
            st.text_area(
                label="",
                value=txt_preview,
                height=150,
                key="txt_preview",
                label_visibility="collapsed",
            )
            
    with tab_prev_bib:
        with st.expander("Xem trước BibTeX (.bib)", expanded=True):
            bibtex_preview = export_bibtex(library[:3])
            if len(library) > 3:
                bibtex_preview += f"\n\n% ... và {len(library) - 3} tài liệu khác"
            st.text_area(
                label="",
                value=bibtex_preview,
                height=150,
                key="bib_preview",
                label_visibility="collapsed",
            )

    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------
    # Hướng dẫn nhanh import
    # ---------------------------------------------------------------
    with st.expander("📘 Hướng dẫn nhập (Import) vào Zotero / Mendeley", expanded=False):
        col_z, col_m = st.columns(2)
        with col_z:
            st.markdown("""
            **🟠 Zotero**
            1. Mở Zotero Desktop.
            2. Chọn **File → Import...**
            3. Chọn file `.bib` đã tải về.
            4. Chọn "Place imported collections and items into new collection" → **Next** → **Done**.
            *Hoặc kéo thả trực tiếp file `.bib` vào thư viện.*
            """)
        with col_m:
            st.markdown("""
            **🔵 Mendeley Reference Manager**
            1. Mở Mendeley Reference Manager.
            2. Chọn **File → Import → BibTeX (.bib)**.
            3. Chọn file `.bib` đã tải về và click **Open**.
            """)
