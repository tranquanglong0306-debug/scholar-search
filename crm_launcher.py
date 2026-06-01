"""
ScholarSearch Admin CRM - Desktop Launcher
Mở ứng dụng CRM trong cửa sổ Desktop mà không cần trình duyệt
"""
import subprocess
import threading
import time
import sys
import os
import signal

# Đặt cổng riêng cho CRM Desktop
PORT = 8502
APP_DIR = os.path.dirname(os.path.abspath(__file__))


def find_streamlit():
    """Tìm đường dẫn của streamlit."""
    import shutil
    path = shutil.which("streamlit")
    if path:
        return path
    # Thử tìm trong Scripts của Python
    python_dir = os.path.dirname(sys.executable)
    candidates = [
        os.path.join(python_dir, "streamlit.exe"),
        os.path.join(python_dir, "Scripts", "streamlit.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "streamlit"


def start_streamlit():
    """Khởi động Streamlit server trong nền."""
    streamlit_path = find_streamlit()
    proc = subprocess.Popen(
        [streamlit_path, "run", "admin_app.py",
         "--server.port", str(PORT),
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=APP_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    return proc


def wait_for_server(timeout=30):
    """Chờ server Streamlit sẵn sàng."""
    import urllib.request
    url = f"http://localhost:{PORT}"
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    import webview

    print("Dang khoi dong ScholarSearch Admin CRM...")

    # Khởi động Streamlit server trong thread nền
    proc = start_streamlit()

    # Hiện cửa sổ loading trong khi chờ
    print("Dang cho server khoi dong...")
    server_ready = wait_for_server(timeout=30)

    if not server_ready:
        print("Loi: Khong the khoi dong server. Thu lai sau.")
        proc.terminate()
        sys.exit(1)

    # Tạo cửa sổ Desktop
    window = webview.create_window(
        title="ScholarSearch Admin CRM",
        url=f"http://localhost:{PORT}",
        width=1200,
        height=750,
        min_size=(900, 600),
        resizable=True,
    )

    def on_closed():
        """Dọn dẹp khi đóng cửa sổ."""
        proc.terminate()

    window.events.closed += on_closed

    # Chạy giao diện Desktop
    webview.start()

    # Đảm bảo Streamlit bị tắt khi thoát
    try:
        proc.terminate()
    except Exception:
        pass


if __name__ == "__main__":
    main()
