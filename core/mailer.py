import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_otp_email(to_email: str, otp: str) -> tuple[bool, str]:
    """Gửi email chứa mã OTP khôi phục mật khẩu. Trả về (Thành công, Lỗi nếu có)"""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    sender_email = os.environ.get("SMTP_EMAIL")
    sender_password = os.environ.get("SMTP_PASSWORD")
    
    if not sender_email or not sender_password:
        # Nếu hệ thống chưa được cấu hình, chỉ in ra console để Test cục bộ
        print(f"\n[DEV MODE] YOUR OTP CODE IS: {otp}\n")
        return True, f"Hệ thống Email chưa cấu hình. Mã OTP của bạn là: {otp} (Đã bỏ qua bước gửi mail)"
        
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "ScholarSearch - Mã khôi phục mật khẩu"
        
        body = f"""
Xin chào,

Bạn đã yêu cầu khôi phục mật khẩu trên hệ thống ScholarSearch.
Mã OTP của bạn là: {otp}

Mã này có hiệu lực trong 15 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.

Nếu bạn không yêu cầu đổi mật khẩu, vui lòng bỏ qua email này.

Trân trọng,
Đội ngũ ScholarSearch.
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return True, "Email đã được gửi thành công!"
    except Exception as e:
        return False, f"Lỗi gửi email: {e}"
