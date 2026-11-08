import sys
import json
import time
import urllib.request
import os
from pathlib import Path
import subprocess

import ctypes
import ctypes.wintypes

from PySide6.QtCore import QTimer, QUrl, Qt, QThread, Signal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QSystemTrayIcon, QMenu
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QIcon
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from app.backend_server import start_api_server, get_frontend_config, get_api_config, _get_config_path


def create_tray_icon() -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # Draw outer glow circle
    painter.setPen(QPen(QColor(0, 245, 255, 220), 2))
    painter.setBrush(QColor(0, 20, 40, 230))
    painter.drawEllipse(2, 2, 28, 28)
    # Inner circle
    painter.setPen(QPen(QColor(0, 245, 255, 180), 1))
    painter.drawEllipse(7, 7, 18, 18)
    # Center letter J
    font = QFont("Orbitron", 11, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor(0, 245, 255))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "J")
    painter.end()
    return QIcon(pixmap)


class GlobalHotkeyListener(QThread):
    hotkey_triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

    def run(self):
        user32 = ctypes.windll.user32
        # Register Ctrl+Shift+J (101) and Ctrl+Alt+J (102)
        MOD_ALT = 0x0001
        MOD_CONTROL = 0x0002
        MOD_SHIFT = 0x0004
        VK_J = ord("J")

        user32.RegisterHotKey(None, 101, MOD_CONTROL | MOD_SHIFT, VK_J)
        user32.RegisterHotKey(None, 102, MOD_CONTROL | MOD_ALT, VK_J)

        msg = ctypes.wintypes.MSG()
        while self._running:
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE = 1
                if msg.message == 0x0312:  # WM_HOTKEY
                    self.hotkey_triggered.emit()
            time.sleep(0.05)

        user32.UnregisterHotKey(None, 101)
        user32.UnregisterHotKey(None, 102)

    def stop(self):
        self._running = False
        self.wait(1000)


class SplashScreen(QWidget):
    """Native splash screen shown while backend/frontend are starting."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 300)

        # Center on primary screen
        primary_screen = QApplication.primaryScreen()
        if primary_screen:
            geo = primary_screen.geometry()
            self.move((geo.width() - 400) // 2, (geo.height() - 300) // 2)

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
    def __init__(self, frontend_url: str, on_ready=None):
        super().__init__()

        self.setWindowTitle("JARVIS")
        self.resize(1400, 900)
        self.setWindowIcon(create_tray_icon())
        self._on_ready = on_ready

        # Dark window container to prevent any flicker during paint
        self.setStyleSheet("background-color: #0A0F19;")

        self.browser = QWebEngineView()
        self._frontend_url = QUrl(frontend_url)
        # Avoid white flash: initialize canvas with dark space background
        self.browser.page().setBackgroundColor(QColor(10, 15, 25))
        self.browser.page().featurePermissionRequested.connect(self._handle_feature_permission)
        self.browser.loadFinished.connect(self._on_load_finished)
        self.browser.load(self._frontend_url)
        self.setCentralWidget(self.browser)

        # System tray icon
        self.tray = QSystemTrayIcon(create_tray_icon(), self)
        self.tray.setToolTip("JARVIS — Active & Monitoring\nHotkey: Ctrl+Shift+J")

        tray_menu = QMenu()
        restore_action = tray_menu.addAction("Show JARVIS (Ctrl+Shift+J)")
        restore_action.triggered.connect(self.bring_to_front)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Exit JARVIS")
        quit_action.triggered.connect(self._force_quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        # Global hotkey listener
        self.hotkey_listener = GlobalHotkeyListener(self)
        self.hotkey_listener.hotkey_triggered.connect(self.bring_to_front)
        self.hotkey_listener.start()

    def _force_quit(self):
        if hasattr(self, "hotkey_listener"):
            self.hotkey_listener.stop()
        QApplication.instance().quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self.bring_to_front()

    def closeEvent(self, event):
        # Minimize to tray instead of quitting
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "JARVIS Running in Background",
            "Say 'Daddy\'s home' or press Ctrl+Shift+J to summon.",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def bring_to_front(self) -> None:
        """Restore and bring JARVIS window to the front and focus when wake word or hotkey is triggered."""
        if self.isHidden() or self.isMinimized():
            self.showNormal()
            self.show()
            self.raise_()
            self.activateWindow()
            try:
                hwnd = int(self.winId())
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
        else:
            self.raise_()
            self.activateWindow()

    def _handle_feature_permission(self, security_origin, feature):
        self.browser.page().setFeaturePermission(
            security_origin,
            feature,
            QWebEnginePage.PermissionPolicy.PermissionGrantedByUser,
        )

    def _on_load_finished(self, loaded: bool) -> None:
        if self._on_ready:
            callback = self._on_ready
            self._on_ready = None
            callback()
        if not loaded:
            # Retry once after a short delay
            QTimer.singleShot(1000, lambda: self.browser.load(self._frontend_url))


def load_config() -> dict:
    import sys
    config_path = _get_config_path()
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
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        kwargs["startupinfo"] = startupinfo
    env = os.environ.copy()
    env["VITE_JARVIS_API_URL"] = f"http://{api_host}:{api_port}"
    return subprocess.Popen(
        ["npm.cmd", "run", "dev", "--", "--host", frontend_host, "--port", str(frontend_port)],
        cwd=frontend,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
        **kwargs,
    )


def run_desktop_app():
    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    # Ensure app stays alive in system tray when windows are hidden or during splash transition
    app.setQuitOnLastWindowClosed(False)

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

    # Reveal main window smoothly only once page has rendered, avoiding any white flash or flicker
    shown = False
    def reveal_main_window():
        nonlocal shown
        if shown:
            return
        shown = True
        window.show()
        window.raise_()
        window.activateWindow()
        QTimer.singleShot(150, splash.close)

    # Create main window (hidden while page loads in background)
    window = JarvisWindow(frontend_url, on_ready=reveal_main_window)

    # Fallback to ensure window shows even if loadFinished takes longer
    QTimer.singleShot(2500, reveal_main_window)

    # Wire wake detection to bring window to front!
    api_server.set_wake_callback(lambda: QTimer.singleShot(0, window.bring_to_front))

    # Cleanup on quit
    app.aboutToQuit.connect(api_server.stop)
    if vite_process is not None:
        app.aboutToQuit.connect(vite_process.terminate)

    sys.exit(app.exec())


if __name__ == "__main__":
    run_desktop_app()

