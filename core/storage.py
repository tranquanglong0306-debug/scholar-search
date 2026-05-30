import json
from typing import List, Dict, Any
from datetime import datetime
from core.models import Article
from core.db import get_connection, execute_query
import dataclasses

# ---------------------------------------------------------------
# Quản lý Thư viện
# ---------------------------------------------------------------

def load_library(user_id: int) -> List[Article]:
    conn = get_connection()
    cursor = execute_query(conn, "SELECT article_data FROM library WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    articles = []
    for row in rows:
        try:
            data = json.loads(row[0])
            valid_keys = Article.__dataclass_fields__.keys()
            filtered_item = {k: v for k, v in data.items() if k in valid_keys}
            articles.append(Article(**filtered_item))
        except Exception as e:
            print(f"Lỗi phân tích bài báo từ CSDL: {e}")
            
    return articles

def save_library(user_id: int, library: List[Article]):
    conn = get_connection()
    
    try:
        execute_query(conn, "DELETE FROM library WHERE user_id = ?", (user_id,))
        
        for a in library:
            data_str = json.dumps(dataclasses.asdict(a), ensure_ascii=False)
            execute_query(conn, "INSERT INTO library (user_id, article_data) VALUES (?, ?)", (user_id, data_str))
            
        conn.commit()
    except Exception as e:
        print(f"Lỗi lưu thư viện vào CSDL: {e}")
    finally:
        conn.close()

# ---------------------------------------------------------------
# Quản lý Lịch sử tìm kiếm
# ---------------------------------------------------------------

def load_history(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    
    cursor = execute_query(conn, """
        SELECT query, search_type, source, total_count, timestamp 
        FROM search_history 
        WHERE user_id = ? 
        ORDER BY id DESC
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "query": row[0],
            "search_type": row[1],
            "source": row[2],
            "total_count": row[3],
            "timestamp": row[4]
        })
    return history

def add_to_history(user_id: int, query: str, search_type: str, source: str, total_count: int):
    if not query or not query.strip():
        return
        
    conn = get_connection()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        execute_query(conn, "DELETE FROM search_history WHERE user_id = ? AND query = ? AND source = ?", (user_id, query.strip(), source))
        
        execute_query(conn, """
            INSERT INTO search_history (user_id, query, search_type, source, total_count, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, query.strip(), search_type, source, total_count, timestamp))
        
        execute_query(conn, """
            DELETE FROM search_history 
            WHERE id NOT IN (
                SELECT id FROM search_history 
                WHERE user_id = ? 
                ORDER BY id DESC LIMIT 50
            ) AND user_id = ?
        """, (user_id, user_id))
        
        conn.commit()
    except Exception as e:
        print(f"Lỗi cập nhật lịch sử: {e}")
    finally:
        conn.close()

def clear_history(user_id: int):
    conn = get_connection()
    execute_query(conn, "DELETE FROM search_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
