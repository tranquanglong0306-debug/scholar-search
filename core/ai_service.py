# core/ai_service.py
import google.generativeai as genai
from config import Config

def summarize_article(text: str) -> str:
    """Gọi Google Gemini API để tóm tắt bài báo."""
    if not Config.GEMINI_API_KEY:
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY. Vui lòng lấy API key từ Google AI Studio và thêm vào cấu hình môi trường."
    
    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Sử dụng mô hình gemini-2.5-flash cho tốc độ nhanh và chính xác
        model = genai.GenerativeModel('gemini-2.5-flash')
        
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

def translate_and_expand_query(query: str) -> str:
    """
    Nếu truy vấn chứa tiếng Việt, sử dụng Gemini để dịch và tối ưu hóa
    thành cụm từ khóa tiếng Anh học thuật (Academic keywords) tốt nhất.
    """
    import re
    # Kiểm tra xem truy vấn có chứa ký tự tiếng Việt có dấu không
    vietnamese_chars = re.compile(r'[àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]', re.IGNORECASE)
    if not vietnamese_chars.search(query):
        # Nếu là tiếng Anh hoàn toàn, không cần dịch
        return query
        
    if not Config.GEMINI_API_KEY:
        return query

    try:
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
Bạn là trợ lý tìm kiếm học thuật. Hãy chuyển đổi truy vấn tiếng Việt sau đây thành một cụm từ khóa tìm kiếm bằng tiếng Anh (Academic search keywords) tối ưu nhất để tìm trên các cơ sở dữ liệu bài báo quốc tế (như Semantic Scholar, OpenAlex).

Yêu cầu:
- Trả về CHỈ duy nhất cụm từ khóa tiếng Anh học thuật kết quả (không thêm lời giải thích, không đặt trong dấu ngoặc hay dấu nháy).
- Cụm từ khóa nên ngắn gọn (1-4 từ), phản ánh đúng nghĩa của truy vấn gốc.
- Ví dụ: "trí tuệ nhân tạo trong y học" -> "artificial intelligence in medicine"
- Ví dụ: "dạy từ vựng tiếng anh" -> "teaching english vocabulary"

Truy vấn gốc: {query}
"""
        response = model.generate_content(prompt)
        translated = response.text.strip().strip('"').strip("'").strip()
        return translated
    except Exception as e:
        print(f"[AI Query Translator Error] {e}")
        return query
