# core/indexing_check.py
import os
import csv
import json
import requests
from typing import Tuple

import streamlit as st
from config import Config

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

@st.cache_data(ttl=2592000)  # Lưu cache trong 30 ngày
def check_indexing_via_claude(journal_name: str, api_key: str) -> Tuple[bool, str, bool, str] or None:
    """
    Gọi Claude API làm dự phòng thông minh khi không tra cứu được trong file CSV tĩnh.
    Trả về None nếu có lỗi xảy ra để có thể chuyển sang phương án dự phòng tiếp theo.
    """
    if not api_key or not journal_name:
        return None
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    prompt = f"""Hãy kiểm tra xem tạp chí khoa học sau đây có nằm trong danh mục Scopus hoặc Web of Science (WoS) hay không.
Tên tạp chí: "{journal_name}"

Yêu cầu chỉ trả về duy nhất một chuỗi JSON có cấu trúc sau (không giải thích, không bọc trong markdown):
{{
  "is_scopus": true/false,
  "scopus_q": "Q1" hoặc "Q2" hoặc "Q3" hoặc "Q4" hoặc "",
  "is_wos": true/false,
  "wos_q": "SSCI" hoặc "SCIE" hoặc "AHCI" hoặc "ESCI" hoặc ""
}}
"""
    
    payload = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 150,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=6)
        if response.status_code == 200:
            res_data = response.json()
            raw_text = res_data["content"][0]["text"].strip()
            
            # Làm sạch markdown if needed
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            data = json.loads(raw_text)
            return (
                bool(data.get("is_scopus", False)),
                str(data.get("scopus_q", "")).strip().upper(),
                bool(data.get("is_wos", False)),
                str(data.get("wos_q", "")).strip().upper()
            )
        else:
            print(f"[Anthropic Claude API Error] Status {response.status_code} - Response: {response.text}")
            return None
    except Exception as e:
        print(f"Lỗi kiểm tra Scopus/WoS qua Claude: {e}")
        return None

@st.cache_data(ttl=2592000)  # Lưu cache trong 30 ngày
def check_indexing_via_gemini(journal_name: str, api_key: str) -> Tuple[bool, str, bool, str] or None:
    """
    Gọi Google Gemini API để kiểm tra danh mục Scopus/WoS của tạp chí khi Claude không khả dụng.
    Trả về None nếu có lỗi xảy ra.
    """
    if not api_key or not journal_name:
        return None
        
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        # Sử dụng gemini-2.5-flash để truy vấn nhanh và kinh tế
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""Hãy kiểm tra xem tạp chí khoa học sau đây có nằm trong danh mục Scopus hoặc Web of Science (WoS) hay không.
Tên tạp chí: "{journal_name}"

Yêu cầu chỉ trả về duy nhất một chuỗi JSON có cấu trúc sau (không giải thích, không bọc trong markdown):
{{
  "is_scopus": true/false,
  "scopus_q": "Q1" hoặc "Q2" hoặc "Q3" hoặc "Q4" hoặc "",
  "is_wos": true/false,
  "wos_q": "SSCI" hoặc "SCIE" hoặc "AHCI" hoặc "ESCI" hoặc ""
}}
"""
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Làm sạch markdown if needed
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(raw_text)
        return (
            bool(data.get("is_scopus", False)),
            str(data.get("scopus_q", "")).strip().upper(),
            bool(data.get("is_wos", False)),
            str(data.get("wos_q", "")).strip().upper()
        )
    except Exception as e:
        print(f"Lỗi kiểm tra Scopus/WoS qua Gemini: {e}")
        return None

def check_indexing(journal_name: str, issn: str = None) -> Tuple[bool, str, bool, str]:
    """
    Kiểm tra xem bài báo có thuộc Scopus hoặc WoS hay không.
    Ưu tiên: ISSN match -> Tên chính xác -> Tên rút gọn -> API fallback
    Trả về: (is_scopus, scopus_q, is_wos, wos_q)
    """
    if not journal_name and not issn:
        return False, "", False, ""

    scopus_journals = _load_scopus_dict()
    wos_journals = _load_wos_dict()

    scopus_q = None
    wos_q = None

    # --- 1. ISSN match (chính xác nhất) ---
    if issn:
        issn_clean = issn.strip().replace("-", "")
        issn_key1 = f"issn:{issn.strip()}"
        issn_key2 = f"issn:{issn_clean[:4]}-{issn_clean[4:]}" if len(issn_clean) >= 8 else ""
        for key in [issn_key1, issn_key2]:
            if key and scopus_q is None:
                scopus_q = scopus_journals.get(key)
            if key and wos_q is None:
                wos_q = wos_journals.get(key)

    # --- 2. Tên tạp chí chính xác + normalize ---
    def _normalize(name: str) -> list:
        """Trả về các biến thể tên cần thử."""
        n = name.strip().lower()
        variants = [n]
        # & <-> and
        if " & " in n:
            variants.append(n.replace(" & ", " and "))
        if " and " in n:
            variants.append(n.replace(" and ", " & "))
        # Bỏ "the " ở đầu
        if n.startswith("the "):
            stripped = n[4:].strip()
            variants.append(stripped)
            if " & " in stripped:
                variants.append(stripped.replace(" & ", " and "))
            if " and " in stripped:
                variants.append(stripped.replace(" and ", " & "))
        return variants

    if journal_name and (scopus_q is None or wos_q is None):
        for variant in _normalize(journal_name):
            if scopus_q is None:
                scopus_q = scopus_journals.get(variant)
            if wos_q is None:
                wos_q = wos_journals.get(variant)
            if scopus_q is not None and wos_q is not None:
                break

    is_scopus = scopus_q is not None
    is_wos = wos_q is not None

    # Chuẩn hóa WoS label
    if is_wos and wos_q in ("", "WOS", "WoS", None):
        wos_q = "WoS Core"

    # Nếu đã tìm thấy ở bước tĩnh -> trả về ngay
    if is_scopus or is_wos:
        return is_scopus, scopus_q or "", is_wos, wos_q or ""

    # --- 4. Claude API fallback ---
    if Config.ANTHROPIC_API_KEY:
        res = check_indexing_via_claude(journal_name or "", Config.ANTHROPIC_API_KEY)
        if res is not None:
            return res

    # --- 5. Gemini API fallback ---
    if Config.GEMINI_API_KEY:
        res = check_indexing_via_gemini(journal_name or "", Config.GEMINI_API_KEY)
        if res is not None:
            return res

    return False, "", False, ""
