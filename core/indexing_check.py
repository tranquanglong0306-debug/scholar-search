# core/indexing_check.py
import os
import csv
from typing import Tuple

# Đường dẫn tới file CSV (dành cho Phương án 1)
SCOPUS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'scopus_list.csv')
WOS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wos_list.csv')

# Cache danh sách tạp chí (để không phải đọc file nhiều lần)
_scopus_journals = set()
_wos_journals = set()
_lists_loaded = False

def _load_csv_lists():
    """Tải dữ liệu tạp chí từ thư mục data/ nếu có."""
    global _scopus_journals, _wos_journals, _lists_loaded
    if _lists_loaded:
        return

    # Tải danh sách Scopus nếu có file
    if os.path.exists(SCOPUS_CSV_PATH):
        try:
            with open(SCOPUS_CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        _scopus_journals.add(row[0].strip().lower())
        except Exception as e:
            print(f"Lỗi đọc file Scopus: {e}")

    # Tải danh sách WoS nếu có file
    if os.path.exists(WOS_CSV_PATH):
        try:
            with open(WOS_CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        _wos_journals.add(row[0].strip().lower())
        except Exception as e:
            print(f"Lỗi đọc file WoS: {e}")

    _lists_loaded = True

def check_indexing(journal_name: str, issn: str = None) -> Tuple[bool, bool]:
    """
    Kiểm tra xem bài báo có thuộc Scopus hoặc WoS hay không.
    Trả về: (is_scopus, is_wos)
    """
    if not journal_name:
        return False, False

    journal_lower = journal_name.strip().lower()
    
    # 1. Phương án 1: Kiểm tra qua danh sách tĩnh (CSV)
    _load_csv_lists()
    
    is_scopus = journal_lower in _scopus_journals
    is_wos = journal_lower in _wos_journals
    
    # Nếu tìm thấy trong CSV thì trả về ngay
    if is_scopus or is_wos:
        return is_scopus, is_wos
        
    # 2. Phương án 2: Kiểm tra qua API (Chưa có API Key)
    # Tạm thời trả về False, nơi này sẽ gắn API tích hợp Elsevier / Clarivate sau.
    # is_scopus_api = call_elsevier_api(journal_name)
    # is_wos_api = call_clarivate_api(journal_name)
    
    return False, False
