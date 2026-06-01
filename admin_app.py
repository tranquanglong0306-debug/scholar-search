import os
from dotenv import load_dotenv

# QUAN TRỌNG: load_dotenv() phải chạy TRƯỚC khi import core.db
# vì db.py đọc DATABASE_URL ngay khi được import
load_dotenv()

import streamlit as st
import pandas as pd
from core.db import get_dashboard_stats, get_all_users, get_all_feedbacks, init_db
from config import Config

st.set_page_config(
    page_title="ScholarSearch CRM",
    page_icon="🛡️",
    layout="wide"
)

# Khởi tạo database nếu chưa có bảng
init_db()

# Lấy mật khẩu admin từ biến môi trường, mặc định là admin123 nếu chưa set
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def login_screen():
    st.markdown("<h2 style='text-align: center; color: #f97316;'>🛡️ Đăng nhập Hệ thống Quản trị</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Vui lòng nhập mật khẩu quản trị viên để tiếp tục.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("Mật khẩu Admin:", type="password", key="admin_pwd")
        if st.button("Đăng nhập", use_container_width=True, type="primary"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Sai mật khẩu!")

def dashboard_screen():
    st.sidebar.title("🛡️ ScholarSearch CRM")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("Điều hướng", ["Trang chủ (Dashboard)", "Quản lý Người dùng", "Quản lý Góp ý"])
    
    if st.sidebar.button("Đăng xuất"):
        st.session_state.admin_logged_in = False
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 ScholarSearch Admin Panel")

    if menu == "Trang chủ (Dashboard)":
        st.title("📊 Tổng quan Hệ thống")
        stats = get_dashboard_stats()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👥 Tổng số Users", stats['users'])
        with col2:
            st.metric("💡 Tổng số Góp ý", stats['feedbacks'])
        with col3:
            st.metric("🔍 Lượt Tìm kiếm", stats['searches'])
            
        st.markdown("---")
        st.info("💡 CRM đang chạy hoàn toàn độc lập với website chính. Bạn có thể theo dõi biến động số lượng người dùng theo thời gian thực tại đây.")

    elif menu == "Quản lý Người dùng":
        st.title("👥 Quản lý Người dùng")
        users = get_all_users()
        if users:
            df_users = pd.DataFrame(users, columns=["ID", "Tên đăng nhập", "Email", "Ngày đăng ký"])
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            st.caption(f"Đang hiển thị {len(users)} người dùng.")
        else:
            st.warning("Chưa có người dùng nào đăng ký.")

    elif menu == "Quản lý Góp ý":
        st.title("💡 Quản lý Góp ý (Feedback)")
        feedbacks = get_all_feedbacks()
        if feedbacks:
            df_feedbacks = pd.DataFrame(feedbacks, columns=["ID", "Người gửi", "Nội dung", "Thời gian"])
            st.dataframe(df_feedbacks, use_container_width=True, hide_index=True)
            st.caption(f"Đang hiển thị {len(feedbacks)} góp ý.")
        else:
            st.info("Chưa có góp ý nào từ người dùng.")

if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    login_screen()
else:
    dashboard_screen()
