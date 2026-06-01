# core/indexing_check.py
import os
import csv
from typing import Tuple

import streamlit as st

# Đường dẫn tới file CSV (dành cho Phương án 1)
SCOPUS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'scopus_list.csv')
WOS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'wos_list.csv')

@st.cache_data(ttl=3600)
def _load_scopus_dict() -> dict:
    scopus_dict = {}
    if os.path.exists(SCOPUS_CSV_PATH):
        try:
            with open(SCOPUS_CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        journal = row[0].strip().lower()
                        q = row[1].strip().upper() if len(row) > 1 else ""
                        scopus_dict[journal] = q
        except Exception as e:
            print(f"Lỗi đọc file Scopus: {e}")
    return scopus_dict

@st.cache_data(ttl=3600)
def _load_wos_dict() -> dict:
    wos_dict = {}
    if os.path.exists(WOS_CSV_PATH):
        try:
            with open(WOS_CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        journal = row[0].strip().lower()
                        q = row[1].strip().upper() if len(row) > 1 else ""
                        wos_dict[journal] = q
        except Exception as e:
            print(f"Lỗi đọc file WoS: {e}")
    return wos_dict

def check_indexing(journal_name: str, issn: str = None) -> Tuple[bool, str, bool, str]:
    """
    Kiểm tra xem bài báo có thuộc Scopus hoặc WoS hay không.
    Trả về: (is_scopus, scopus_q, is_wos, wos_q)
    """
    if not journal_name:
        return False, "", False, ""

    journal_lower = journal_name.strip().lower()
    
    scopus_journals = _load_scopus_dict()
    wos_journals = _load_wos_dict()
    
    scopus_q = scopus_journals.get(journal_lower)
    wos_q = wos_journals.get(journal_lower)
    
    is_scopus = scopus_q is not None
    is_wos = wos_q is not None
    
    # Nếu tìm thấy trong CSV thì trả về ngay
    if is_scopus or is_wos:
        return is_scopus, scopus_q or "", is_wos, wos_q or ""
        
    # 2. Phương án 2: Kiểm tra qua API (Chưa có API Key)
    # Tạm thời trả về False, nơi này sẽ gắn API tích hợp Elsevier / Clarivate sau.
    # is_scopus_api = call_elsevier_api(journal_name)
    # is_wos_api = call_clarivate_api(journal_name)
    
    return False, "", False, ""
