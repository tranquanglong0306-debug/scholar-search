import streamlit as st
from core import db

def render_feedback_tab():
    st.markdown("### 💡 Góp ý & Đề xuất phát triển ScholarSearch")
    st.markdown("Chúng tôi luôn lắng nghe ý kiến của bạn để cải thiện phần mềm tốt hơn mỗi ngày. Mọi đóng góp đều được lưu nhận và xem xét kỹ lưỡng.")
    
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

    # Thông tin liên hệ trực tiếp
    st.divider()
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(59,130,246,0.12), rgba(99,102,241,0.06));
                border: 1px solid rgba(59,130,246,0.25); border-radius: 12px;
                padding: 1.25rem 1.5rem; margin-top: 0.5rem;">
        <h4 style="margin:0 0 0.6rem 0; font-size:1.05rem; color:var(--text-primary);">
            📬 Liên hệ trực tiếp với tác giả
        </h4>
        <p style="margin:0 0 0.5rem 0; color:var(--text-secondary); font-size:0.9rem;">
            Ngoài hệ thống góp ý ở trên, bạn có thể gửi email trực tiếp cho chúng tôi để được hỗ trợ nhanh hơn:
        </p>
        <a href="mailto:tranquanglong0306@gmail.com?subject=Góp ý ScholarSearch&body=Xin chào, tôi muốn góp ý về ScholarSearch:%0A%0A"
           style="display:inline-flex; align-items:center; gap:8px;
                  padding: 8px 18px; background: linear-gradient(135deg,#3b82f6,#6366f1);
                  color:white; border-radius:8px; text-decoration:none; font-weight:600;
                  font-size:0.9rem; transition:opacity 0.2s;"
           onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'">
            ✉️ tranquanglong0306@gmail.com
        </a>
        <p style="margin:0.75rem 0 0 0; color:var(--text-muted); font-size:0.8rem; font-style:italic;">
            💡 Bấm vào nút trên để mở ứng dụng email và gửi trực tiếp cho tác giả.
        </p>
    </div>
    """, unsafe_allow_html=True)
