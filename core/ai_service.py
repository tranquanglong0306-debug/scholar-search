# core/ai_service.py
import google.generativeai as genai
from config import Config

def summarize_article(text: str) -> str:
    """Gọi Google Gemini API để tóm tắt bài báo."""
    if not Config.GEMINI_API_KEY:
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY. Vui lòng lấy API key từ Google AI Studio và thêm vào cấu hình môi trường."
    
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Sử dụng mô hình gemini-1.5-flash cho tốc độ nhanh và chính xác
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Bạn là một chuyên gia nghiên cứu học thuật. Hãy đọc và tóm tắt bài báo khoa học (hoặc Abstract) sau đây một cách súc tích, chuyên nghiệp bằng tiếng Việt.

Yêu cầu:
- Tóm tắt mục tiêu nghiên cứu (Objective).
- Trình bày phương pháp nghiên cứu (Methodology).
- Nêu bật các kết quả chính (Key Findings).
- Trình bày dạng các gạch đầu dòng rõ ràng, mạch lạc.
- Giữ văn phong học thuật, khách quan.

Nội dung bài báo:
{text}
"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Lỗi khi gọi Gemini API: {str(e)}"
