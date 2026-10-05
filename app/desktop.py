import sys
import json
import time
import urllib.request
import os
from pathlib import Path
import subprocess

from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen
from PySide6.QtWebEngineWidgets import QWebEngineView

from app.backend_server import start_api_server, get_frontend_config, get_api_config


class SplashScreen(QWidget):
    """Native splash screen shown while backend/frontend are starting."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 300)
        self._dots = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(400)

    def _animate(self):
        self._dots = (self._dots + 1) % 4
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background card
        rect = self.rect().adjusted(10, 10, -10, -10)
        painter.setBrush(QColor(0, 10, 25, 240))
        painter.setPen(QPen(QColor(0, 245, 255, 180), 2))
        painter.drawRoundedRect(rect, 16, 16)

        # JARVIS logo
        font = QFont("Orbitron", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QColor(0, 245, 255))
        painter.drawText(rect.adjusted(0, 40, 0, 0), Qt.AlignmentFlag.AlignHCenter, "JARVIS")

        # Version
        font = QFont("Rajdhani", 10)
        painter.setFont(font)
        painter.setPen(QColor(0, 245, 255, 120))
        painter.drawText(rect.adjusted(0, 90, 0, 0), Qt.AlignmentFlag.AlignHCenter, "OS v3.7.2 — ALPHA")

        # Loading text with animated dots
        font = QFont("Share Tech Mono", 11)
        painter.setFont(font)
        painter.setPen(QColor(0, 245, 255, 200))
        dots = "." * self._dots
        painter.drawText(rect.adjusted(0, 140, 0, 0), Qt.AlignmentFlag.AlignHCenter, f"Initializing neural core{dots}")

        # Subtext
        font = QFont("Rajdhani", 9)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 80))
        painter.drawText(rect.adjusted(0, 180, 0, 0), Qt.AlignmentFlag.AlignHCenter, "Starting backend services...")
        painter.drawText(rect.adjusted(0, 210, 0, 0), Qt.AlignmentFlag.AlignHCenter, "Waiting for frontend...")


class JarvisWindow(QMainWindow):
    def __init__(self, frontend_url: str):
        super().__init__()

        self.setWindowTitle("JARVIS")
        self.resize(1400, 900)

        self.browser = QWebEngineView()
        self._frontend_url = QUrl(frontend_url)
        self.browser.loadFinished.connect(self._on_load_finished)
        self.setCentralWidget(self.browser)

    def _on_load_finished(self, loaded: bool) -> None:
        if not loaded:
            # Retry once after a short delay
            QTimer.singleShot(1000, lambda: self.browser.setUrl(self._frontend_url))


def load_config() -> dict:
    config_path = Path(__file__).resolve().parents[1] / "config" / "settings.json"
    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def wait_for_backend_ready(host: str, port: int, timeout: float = 30.0) -> bool:
    """Poll /api/health until it returns 200 OK or timeout."""
    url = f"http://{host}:{port}/api/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def wait_for_frontend_ready(host: str, port: int, timeout: float = 60.0) -> bool:
    """Poll frontend dev server until it returns 200 OK or timeout."""
    url = f"http://{host}:{port}"
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def _start_vite_dev_server(frontend_host: str, frontend_port: int, api_host: str, api_port: int) -> subprocess.Popen[bytes]:
    """Run the existing Vite app locally for desktop development."""
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    env = os.environ.copy()
    env["VITE_JARVIS_API_URL"] = f"http://{api_host}:{api_port}"
    return subprocess.Popen(
        ["npm.cmd", "run", "dev", "--", "--host", frontend_host, "--port", str(frontend_port)],
        cwd=frontend,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
        env=env,
    )


def run_desktop_app():
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    # Load configuration
    config = load_config()
    api_host, api_port = get_api_config()
    frontend_host, frontend_port = get_frontend_config()
    development_mode = os.environ.get("JARVIS_DEV") == "1"

    # Show splash screen immediately
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # Start API server
    api_server = start_api_server()

    # Wait for backend to be ready
    splash.update()
    app.processEvents()
    if not wait_for_backend_ready(api_host, api_port):
        print("WARNING: Backend health check timed out")

    vite_process = None
    frontend_url = f"http://{api_host}:{api_port}"
    if development_mode:
        vite_process = _start_vite_dev_server(frontend_host, frontend_port, api_host, api_port)
        splash.update()
        app.processEvents()
        if not wait_for_frontend_ready(frontend_host, frontend_port):
            print("WARNING: Frontend dev server timed out")
        frontend_url = f"http://{frontend_host}:{frontend_port}"

    # Create main window (hidden initially)
    window = JarvisWindow(frontend_url)

    # Cleanup on quit
    app.aboutToQuit.connect(api_server.stop)
    if vite_process is not None:
        app.aboutToQuit.connect(vite_process.terminate)

    # Close splash and show main window
    splash.close()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run_desktop_app()
