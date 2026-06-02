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
    
    # 1. Tra cứu nhanh trong file CSV tĩnh
    if is_scopus or is_wos:
        return is_scopus, scopus_q or "", is_wos, wos_q or ""
        
    # 2. Sử dụng Claude API làm dự phòng thông minh (nếu được cấu hình)
    if Config.ANTHROPIC_API_KEY:
        res = check_indexing_via_claude(journal_name, Config.ANTHROPIC_API_KEY)
        if res is not None:
            return res
            
    # 3. Sử dụng Gemini API làm dự phòng thứ hai (nếu Claude thất bại hoặc không cấu hình)
    if Config.GEMINI_API_KEY:
        res = check_indexing_via_gemini(journal_name, Config.GEMINI_API_KEY)
        if res is not None:
            return res
    
    return False, "", False, ""
