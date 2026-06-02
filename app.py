# app.py
# ============================================================
# ScholarSearch — Ứng dụng Tìm kiếm & Quản lý Trích dẫn Học thuật
# Phiên bản: 1.0.0
# Tác giả: Dành riêng cho luận văn Thạc sĩ — Applied Linguistics & Education
# Công nghệ: Python + Streamlit
# ============================================================

import streamlit as st
import sys
import os
import qrcode

# Đảm bảo Python tìm thấy các module trong dự án
sys.path.insert(0, os.path.dirname(__file__))

from ui.styles import inject_css
from ui.search_tab import render_search_tab
from ui.library_tab import render_library_tab
from ui.export_tab import render_export_tab
from ui.ai_summary_tab import render_ai_summary_tab
from ui.feedback_tab import render_feedback_tab
from config import Config
from core import storage
from core import db

# ---------------------------------------------------------------
# Cấu hình trang Streamlit (PHẢI là lệnh đầu tiên)
# ---------------------------------------------------------------
st.set_page_config(
    page_title="ScholarSearch — Tìm kiếm Học thuật",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://api.semanticscholar.org/",
        "Report a bug": None,
        "About": (
            "**ScholarSearch v1.0** — Công cụ tìm kiếm bài báo khoa học\n\n"
            "Dữ liệu từ: Semantic Scholar · Crossref · OpenAlex\n\n"
            "Hỗ trợ trích dẫn: APA 7th · MLA 9th · Chicago 17th"
        ),
    },
)

# Khởi tạo Database
db.init_db()

# ---------------------------------------------------------------
# Inject CSS tùy chỉnh
# ---------------------------------------------------------------
st.markdown(inject_css(), unsafe_allow_html=True)


# ---------------------------------------------------------------
# Khởi tạo Session State
# ---------------------------------------------------------------
def _init_session_state() -> None:
    """Khởi tạo các biến session state nếu chưa có."""
    if "user_id" not in st.session_state:
        # Đọc phiên đăng nhập đã lưu cục bộ nếu có
        saved_uid, saved_uname = storage.load_active_session()
        st.session_state["user_id"] = saved_uid
        st.session_state["username"] = saved_uname

    defaults = {
        "search_results": [],       # Kết quả tìm kiếm hiện tại
        "last_query": "",           # Truy vấn cuối
        "search_error": None,       # Thông báo lỗi tìm kiếm
        "search_total": 0,          # Tổng kết quả từ API
        "active_tab": 0,            # Tab đang hiển thị
        "history_loaded": False,    # Cờ theo dõi lịch sử
        "summary_usage_count": 0,   # Biến đếm số lần dùng AI tóm tắt
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

_init_session_state()

# ---------------------------------------------------------------
# Màn hình Đăng nhập / Đăng ký
# ---------------------------------------------------------------
if st.session_state.user_id is None:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🎓 ScholarSearch</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8892b0;'>Hệ thống tìm kiếm bài báo khoa học & quản lý trích dẫn đa người dùng.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        tab_login, tab_register, tab_forgot = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký", "❓ Quên mật khẩu"])
        
        with tab_login:
            with st.form("login_form"):
                log_username = st.text_input("Tên đăng nhập")
                log_password = st.text_input("Mật khẩu", type="password")
                submitted = st.form_submit_button("Đăng nhập", use_container_width=True)
                
                if submitted:
                    user_id, msg = db.verify_user(log_username, log_password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = msg
                        # Lưu phiên đăng nhập cục bộ
                        storage.save_active_session(user_id, msg)
                        # Tải thư viện của user này
                        st.session_state.library = storage.load_library(user_id)
                        st.rerun()
                    else:
                        st.error(msg)
                        
        with tab_register:
            with st.form("register_form"):
                reg_username = st.text_input("Tên đăng nhập mới")
                reg_email = st.text_input("Email (bắt buộc để khôi phục mật khẩu)")
                reg_password = st.text_input("Mật khẩu mới", type="password")
                reg_password_confirm = st.text_input("Nhập lại mật khẩu", type="password")
                reg_submitted = st.form_submit_button("Đăng ký tài khoản", use_container_width=True)
                
                if reg_submitted:
                    if reg_password != reg_password_confirm:
                        st.error("Mật khẩu không khớp!")
                    else:
                        success, msg = db.create_user(reg_username, reg_password, reg_email)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                            
        with tab_forgot:
            # Khởi tạo state cho quy trình quên mật khẩu
            if "forgot_step" not in st.session_state:
                st.session_state.forgot_step = 1
            if "forgot_email" not in st.session_state:
                st.session_state.forgot_email = ""
                
            if st.session_state.forgot_step == 1:
                st.markdown("Nhập Email đã đăng ký để nhận mã OTP khôi phục.")
                with st.form("forgot_step1"):
                    f_email = st.text_input("Email")
                    btn_send = st.form_submit_button("Gửi mã OTP", use_container_width=True)
                    
                    if btn_send:
                        success, msg_or_otp = db.generate_reset_code(f_email)
                        if success:
                            from core import mailer
                            st.session_state.forgot_email = f_email
                            email_success, email_msg = mailer.send_otp_email(f_email, msg_or_otp)
                            if email_success:
                                st.session_state.forgot_step = 2
                                st.session_state.dev_otp_msg = email_msg
                                st.rerun()
                            else:
                                st.error(email_msg)
                        else:
                            st.error(msg_or_otp)
            
            elif st.session_state.forgot_step == 2:
                st.markdown(f"Đang khôi phục mật khẩu cho email: **{st.session_state.forgot_email}**")
                
                if "dev_otp_msg" in st.session_state and st.session_state.dev_otp_msg:
                    st.info(st.session_state.dev_otp_msg)
                    
                with st.form("forgot_step2"):
                    f_otp = st.text_input("Nhập mã OTP (6 số)")
                    f_new_password = st.text_input("Mật khẩu mới", type="password")
                    btn_reset = st.form_submit_button("Xác nhận đổi mật khẩu", use_container_width=True)
                    
                    if btn_reset:
                        success, msg = db.reset_password_with_otp(st.session_state.forgot_email, f_otp, f_new_password)
                        if success:
                            st.success(msg)
                            st.session_state.forgot_step = 1
                            st.session_state.forgot_email = ""
                        else:
                            st.error(msg)
                
                if st.button("⬅️ Quay lại"):
                    st.session_state.forgot_step = 1
                    st.rerun()
    
    st.stop() # Dừng chạy phần app chính nếu chưa đăng nhập

# Tải thư viện một lần nếu chưa có (sau khi đăng nhập)
if "library" not in st.session_state:
    st.session_state["library"] = storage.load_library(st.session_state.user_id)


# ---------------------------------------------------------------
# Header chính
# ---------------------------------------------------------------
st.markdown("""
<div class="scholar-header">
    <h1>🎓 ScholarSearch</h1>
    <p>Công cụ Tìm kiếm Học thuật & Quản lý Trích dẫn Đa Ngành</p>
    <p style="margin-top:0.4rem; font-size:0.8rem; opacity:0.5;">
        Ngôn ngữ học · Giáo dục · CNTT · Kinh tế · Y học · Khoa học xã hội · Môi trường
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# Mục Ủng hộ (Donate)
# ---------------------------------------------------------------
with st.expander("💖 Ủng hộ ScholarSearch", expanded=False):
    st.markdown("""
    **Website này được duy trì hoàn toàn miễn phí cho cộng đồng.** Tuy nhiên, các tính năng tích hợp AI (như tóm tắt bài viết) đòi hỏi chi phí vận hành và duy trì server mỗi tháng.
    
    Nếu bạn yêu thích công cụ này và muốn ủng hộ tác giả duy trì nó "chậm mà chắc", bạn có thể donate tùy hỷ qua mã QR bên dưới. Cảm ơn bạn đã tiếp sức cho ScholarSearch!
    """)
    qr_path = os.path.join(os.path.dirname(__file__), "assets", "qr_donate.jpg")
    qr_path_png = os.path.join(os.path.dirname(__file__), "assets", "qr_donate.png")
    
    if os.path.exists(qr_path):
        st.image(qr_path, width=300)
    elif os.path.exists(qr_path_png):
        st.image(qr_path_png, width=300)
    else:
        st.info("💡 Hướng dẫn cho Admin: Hãy copy file ảnh mã QR của bạn vào thư mục `assets/` và đổi tên thành `qr_donate.jpg` hoặc `qr_donate.png` để hiển thị ảnh QR tại đây.")

# ---------------------------------------------------------------
# Tabs chính
# ---------------------------------------------------------------

with st.sidebar:
    st.markdown(f"### 👋 Xin chào, **{st.session_state.username}**")
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.library = []
        # Xóa phiên đăng nhập cục bộ
        storage.clear_active_session()
        st.rerun()
        
    st.markdown("---")
    
    st.markdown("### ⚙️ Cấu hình")

    # Trạng thái thư viện
    lib_count = len(st.session_state.library)
    if lib_count > 0:
        st.success(f"📚 {lib_count} bài trong thư viện")
    else:
        st.info("📂 Thư viện trống")

    st.divider()

    # Khung lựa chọn ngành nghề/lĩnh vực (Đa ngành)
    st.markdown("### 🎓 Lĩnh vực nghiên cứu")
    from core import disciplines
    
    # Lưu lĩnh vực được chọn vào session_state để đồng bộ
    if "selected_discipline" not in st.session_state:
        st.session_state["selected_discipline"] = disciplines.get_disciplines_list()[0]
        
    selected_disp = st.selectbox(
        "Chọn Ngành học / Lĩnh vực:",
        options=disciplines.get_disciplines_list(),
        key="discipline_selector",
        label_visibility="collapsed"
    )
    
    # Khi đổi ngành học, lưu lại
    st.session_state["selected_discipline"] = selected_disp
    
    custom_field = ""
    if selected_disp == "Ngành học / Lĩnh vực khác":
        custom_field = st.text_input("Nhập tên ngành (tiếng Anh):", 
                                     placeholder="Ví dụ: Chemistry, Physics, Art...", 
                                     key="custom_discipline_input")
        # Đồng bộ từ tùy chọn nhập tay nếu user chưa click nút gợi ý
        if "fields_filter" not in st.session_state or st.session_state.fields_filter == "" or st.session_state.fields_filter in ["Linguistics,Education", "Education", "Computer Science", "Economics,Business", "Medicine,Biology", "Sociology,Psychology,History", "Environmental Science,Ecology"]:
            st.session_state.fields_filter = custom_field
            
    # Ánh xạ tên ngành tiếng Việt sang tiếng Anh cho API nâng cao
    english_fields_map = {
        "Ngôn ngữ học ứng dụng & Ngoại ngữ": "Linguistics,Education",
        "Giáo dục & Sư phạm": "Education",
        "Khoa học máy tính & CNTT": "Computer Science",
        "Kinh tế & Quản trị kinh doanh": "Economics,Business",
        "Y học & Khoa học sức khỏe": "Medicine,Biology",
        "Khoa học xã hội & Nhân văn": "Sociology,Psychology,History",
        "Môi trường & Sinh thái": "Environmental Science,Ecology"
    }
    
    # Khi đổi ngành chính (không phải ngành khác), tự động đồng bộ sang bộ lọc nâng cao
    if selected_disp != "Ngành học / Lĩnh vực khác":
        st.session_state.fields_filter = english_fields_map.get(selected_disp, "")
    
    # Gợi ý từ khóa tương ứng với ngành học được chọn
    st.markdown("### 💡 Từ khóa Gợi ý")
    suggested_kws = disciplines.get_keywords_by_discipline(selected_disp)
    for kw in suggested_kws:
        if st.button(f"🔸 {kw}", key=f"kw_{selected_disp}_{kw}", use_container_width=True):
            st.session_state.search_query = kw
            st.session_state.fields_filter = custom_field if selected_disp == "Ngành học / Lĩnh vực khác" else english_fields_map.get(selected_disp, "")
            st.session_state.active_tab = 0
            st.rerun()

    st.divider()

    # Lịch sử tìm kiếm
    st.markdown("### 🕒 Lịch sử Tìm kiếm")
    history = storage.load_history(st.session_state.user_id)
    if history:
        if st.button("🗑️ Xóa lịch sử", key="clear_history", use_container_width=True):
            storage.clear_history(st.session_state.user_id)
            st.rerun()
        
        # Hiển thị tối đa 10 tìm kiếm gần nhất để không làm quá dài sidebar
        for h in history[:10]:
            if st.button(f"🔍 {h['query']} ({h['source']})", key=f"hist_{h['timestamp']}_{h['query']}", use_container_width=True):
                st.session_state.search_query = h['query']
                st.session_state.active_tab = 0
                st.rerun()
    else:
        st.info("Chưa có lịch sử tìm kiếm.")

    st.divider()

    # Thông tin nguồn dữ liệu
    st.markdown("### 🌐 Nguồn Dữ liệu")
    st.markdown("""
    | Nguồn | Giới hạn |
    |-------|---------|
    | 🔬 Semantic Scholar | 100 req/5min |
    | 📖 Crossref | Không giới hạn |
    | 🌍 OpenAlex | 100k/ngày |
    """)

    st.divider()

    # Link tài nguyên
    st.markdown("### 📎 Tài nguyên")
    st.markdown("""
    - [Semantic Scholar API](https://api.semanticscholar.org/)
    - [Crossref API](https://api.crossref.org/)
    - [OpenAlex API](https://openalex.org/)
    - [APA 7th Guide](https://apastyle.apa.org/)
    - [Zotero](https://www.zotero.org/)
    - [Mendeley](https://www.mendeley.com/)
    """)


    st.caption(f"ScholarSearch v{Config.APP_VERSION}")
    st.caption("Made with ❤️ by Python + Streamlit")


# ---------------------------------------------------------------
# Navigation Tabs chính
# ---------------------------------------------------------------
tab_search, tab_library, tab_export, tab_ai, tab_feedback = st.tabs([
    f"🔍 Tìm kiếm",
    f"📚 Thư viện  ({lib_count})",
    f"📤 Xuất dữ liệu",
    f"🤖 AI Tóm tắt",
    f"💡 Góp ý",
])

with tab_search:
    render_search_tab()

with tab_library:
    render_library_tab()

with tab_export:
    render_export_tab()

with tab_ai:
    render_ai_summary_tab()

with tab_feedback:
    render_feedback_tab()
