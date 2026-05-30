import os
import bcrypt
import random
import sqlite3
from datetime import datetime, timedelta

try:
    import psycopg2
except ImportError:
    psycopg2 = None

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "scholar.db")
DATABASE_URL = os.environ.get("DATABASE_URL")

def _ensure_db_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_connection():
    if DATABASE_URL and psycopg2:
        return psycopg2.connect(DATABASE_URL)
    else:
        _ensure_db_dir()
        return sqlite3.connect(DB_PATH, check_same_thread=False)

def execute_query(conn, query: str, params: tuple = ()):
    """Helper hỗ trợ cả SQLite và PostgreSQL (xử lý placeholder và syntax khác biệt)"""
    is_pg = hasattr(conn, 'get_dsn_parameters')
    if is_pg:
        # Thay thế placeholder cho Postgres
        query = query.replace("?", "%s")
        # Thay thế AUTOINCREMENT
        query = query.replace("AUTOINCREMENT", "SERIAL")
        
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor

def init_db():
    """Tạo các bảng cơ sở dữ liệu nếu chưa tồn tại."""
    conn = get_connection()
    
    # Bảng người dùng
    execute_query(conn, '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Cập nhật bảng cũ nếu chưa có cột email (chỉ cho SQLite)
    is_pg = hasattr(conn, 'get_dsn_parameters')
    if not is_pg:
        try:
            execute_query(conn, "ALTER TABLE users ADD COLUMN email TEXT;")
        except sqlite3.OperationalError:
            pass
    
    # Bảng thư viện bài báo
    execute_query(conn, '''
    CREATE TABLE IF NOT EXISTS library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        article_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Bảng lịch sử tìm kiếm
    execute_query(conn, '''
    CREATE TABLE IF NOT EXISTS search_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        query TEXT NOT NULL,
        search_type TEXT,
        source TEXT,
        total_count INTEGER,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Bảng lưu mã OTP quên mật khẩu
    execute_query(conn, '''
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        reset_code TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# ---------------------------------------------------------------
# Quản lý người dùng (Authentication)
# ---------------------------------------------------------------

def create_user(username: str, password: str, email: str) -> tuple[bool, str]:
    if not username or not password or not email:
        return False, "Tài khoản, mật khẩu và email không được để trống."
    if len(password) < 6:
        return False, "Mật khẩu phải dài ít nhất 6 ký tự."
    if "@" not in email:
        return False, "Email không hợp lệ."
        
    conn = get_connection()
    
    cursor = execute_query(conn, "SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Tên tài khoản đã tồn tại!"
        
    email = email.lower().strip()
    cursor = execute_query(conn, "SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "Email này đã được sử dụng!"
        
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        execute_query(conn, 
            "INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)", 
            (username, hashed.decode('utf-8'), email)
        )
        conn.commit()
        return True, "Đăng ký thành công! Hãy đăng nhập."
    except Exception as e:
        return False, f"Lỗi hệ thống: {e}"
    finally:
        conn.close()

def verify_user(username: str, password: str) -> tuple[int, str]:
    conn = get_connection()
    cursor = execute_query(conn, "SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None, "Tài khoản không tồn tại."
        
    user_id, db_username, db_hash = row
    
    if bcrypt.checkpw(password.encode('utf-8'), db_hash.encode('utf-8')):
        return user_id, db_username
    else:
        return None, "Sai mật khẩu."

# ---------------------------------------------------------------
# Tính năng Quên mật khẩu
# ---------------------------------------------------------------

def generate_reset_code(email: str) -> tuple[bool, str]:
    conn = get_connection()
    email = email.lower().strip()
    
    cursor = execute_query(conn, "SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return False, "Không tìm thấy tài khoản nào liên kết với Email này."
        
    user_id = row[0]
    otp = str(random.randint(100000, 999999))
    expires_at = (datetime.now() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        execute_query(conn, "DELETE FROM password_resets WHERE user_id = ?", (user_id,))
        execute_query(conn, "INSERT INTO password_resets (user_id, reset_code, expires_at) VALUES (?, ?, ?)", (user_id, otp, expires_at))
        conn.commit()
        return True, otp
    except Exception as e:
        return False, f"Lỗi tạo mã: {e}"
    finally:
        conn.close()

def reset_password_with_otp(email: str, otp: str, new_password: str) -> tuple[bool, str]:
    if len(new_password) < 6:
        return False, "Mật khẩu mới phải dài ít nhất 6 ký tự."
        
    conn = get_connection()
    email = email.lower().strip()
    
    cursor = execute_query(conn, "SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    user_row = cursor.fetchone()
    
    if not user_row:
        conn.close()
        return False, "Email không hợp lệ."
    
    user_id = user_row[0]
    
    cursor = execute_query(conn, "SELECT reset_code, expires_at FROM password_resets WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    otp_row = cursor.fetchone()
    
    if not otp_row:
        conn.close()
        return False, "Bạn chưa yêu cầu cấp lại mật khẩu."
        
    db_otp, expires_at = otp_row
    
    if otp != db_otp:
        conn.close()
        return False, "Mã OTP không chính xác."
        
    if datetime.now() > datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S"):
        conn.close()
        return False, "Mã OTP đã hết hạn."
        
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        execute_query(conn, "UPDATE users SET password_hash = ? WHERE id = ?", (hashed.decode('utf-8'), user_id))
        execute_query(conn, "DELETE FROM password_resets WHERE user_id = ?", (user_id,))
        conn.commit()
        return True, "Mật khẩu đã được đặt lại thành công! Bạn có thể đăng nhập."
    except Exception as e:
        return False, f"Lỗi đổi mật khẩu: {e}"
    finally:
        conn.close()
