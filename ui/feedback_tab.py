import streamlit as st
from core import db

def render_feedback_tab():
    st.markdown("### 💡 Góp ý & Đề xuất phát triển ScholarSearch")
    st.markdown("Chúng tôi luôn lắng nghe ý kiến của bạn để cải thiện phần mềm tốt hơn mỗi ngày. Mọi đóng góp đều được lưu nhận và xem xét kỹ lưỡng.")
    
    if st.session_state.get("logged_in"):
        st.info(f"Xin chào **{st.session_state.username}**, cảm ơn bạn đã đồng hành cùng ScholarSearch!")
        with st.form("feedback_form_main", clear_on_submit=True):
            feedback_text = st.text_area(
                "Nội dung góp ý / Báo lỗi:", 
                height=200, 
                placeholder="Ví dụ: Tính năng tải PDF đôi khi bị lỗi, tôi đề xuất thêm tính năng..."
            )
            submit_btn = st.form_submit_button("🚀 Gửi góp ý", type="primary")
            
            if submit_btn:
                if feedback_text.strip():
                    if db.save_feedback(st.session_state.user_id, st.session_state.username, feedback_text):
                        st.success("✅ Tuyệt vời! Cảm ơn bạn. Góp ý của bạn đã được gửi thành công vào hệ thống.")
                    else:
                        st.error("❌ Có lỗi xảy ra với hệ thống cơ sở dữ liệu, không thể gửi góp ý.")
                else:
                    st.warning("⚠️ Vui lòng nhập nội dung góp ý trước khi gửi.")
    else:
        st.warning("🔒 Vui lòng đăng nhập để có thể gửi góp ý vào hệ thống.")
