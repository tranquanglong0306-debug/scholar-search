import streamlit as st
import time

FREE_LIMIT = 3

def mock_ai_summary(text: str) -> str:
    """Hàm giả lập gọi AI tóm tắt"""
    time.sleep(1.5)  # Giả lập delay API
    return f"**Đây là bản tóm tắt tự động bằng AI** cho đoạn văn bản dài {len(text)} ký tự của bạn.\n\n_\"Bài báo tập trung thảo luận về các vấn đề cốt lõi trong lĩnh vực nghiên cứu, đề xuất một phương pháp tiếp cận mới nhằm tối ưu hóa kết quả và đưa ra những số liệu thực nghiệm chứng minh tính hiệu quả của mô hình.\"_"

def render_ai_summary_tab():
    st.markdown("### 🤖 Trợ lý AI Tóm tắt Bài báo")
    st.markdown("Dán nội dung bài báo khoa học của bạn vào đây để AI đọc, phân tích và trích xuất những ý chính quan trọng nhất chỉ trong vài giây.")
    
    # Hiển thị số lượt còn lại
    remaining = max(0, FREE_LIMIT - st.session_state.summary_usage_count)
    st.info(f"💡 Bạn đang sử dụng gói Miễn phí. Lượt dùng AI còn lại: **{remaining}/{FREE_LIMIT}**")

    # Vùng nhập liệu
    article_text = st.text_area(
        "Nội dung bài báo:", 
        height=250, 
        placeholder="Copy và dán toàn văn (full-text) hoặc phần Abstract của bài báo vào đây..."
    )

    # Logic kiểm tra giới hạn (nếu hết lượt thì khóa nút)
    if st.session_state.summary_usage_count >= FREE_LIMIT:
        st.error("🔒 Bạn đã hết lượt sử dụng tính năng AI miễn phí.")
        st.markdown(
            "👉 **[🚀 Nhấn vào đây để Nâng cấp lên tài khoản Premium (Không giới hạn AI)](#)**", 
            unsafe_allow_html=True
        )
        st.button("✨ Tóm tắt bằng AI", disabled=True, key="btn_ai_disabled")
    else:
        # Nút hoạt động bình thường nếu còn lượt
        if st.button("✨ Tóm tắt bằng AI", type="primary", key="btn_ai_active"):
            if not article_text.strip():
                st.warning("⚠️ Vui lòng dán nội dung bài báo trước khi nhấn tóm tắt.")
            else:
                # Tăng biến đếm
                st.session_state.summary_usage_count += 1
                
                with st.spinner("🤖 AI đang đọc và tổng hợp thông tin..."):
                    summary_result = mock_ai_summary(article_text)
                
                st.success("✅ Tóm tắt thành công!")
                st.markdown("#### 📑 Kết quả Tóm tắt:")
                st.info(summary_result)
                
                # Cập nhật lại UI ngay lập tức để trừ đi 1 lượt hiển thị
                st.rerun()
