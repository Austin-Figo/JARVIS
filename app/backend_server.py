"""Local HTTP API shared by the desktop shell and the React UI.

It uses only Python's standard library so a fresh virtual environment can run
the project without an additional backend dependency installation.
"""

from __future__ import annotations

import ctypes
import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from core.jarvis_core import JarvisCore
from memory.store import MemoryStore
from ai.provider import AIProvider, chat as ai_chat, set_ai_provider
from voice.windows_recognizer import WindowsSpeechRecognizer
from voice.windows_synthesizer import WindowsSpeechSynthesizer
from wake.wake_detector import WakeDetector
from security.activity_log import ActivityLog


_DEFAULT_SETTINGS: dict[str, Any] = {
    "assistant_name": "JARVIS",
    "wake_phrase": "Daddy's home",
    "language": "en-US",
    "tts_enabled": True,
    "wake_detection_enabled": True,
    "require_confirmation_for_sensitive_actions": True,
    "api": {"host": "127.0.0.1", "port": 8765},
    "frontend": {"dev_host": "127.0.0.1", "dev_port": 5173},
}
_SETTINGS_FIELDS = {
    "username": str, "fullName": str, "assistantName": str, "model": str,
    "temperature": (int, float), "streaming": bool, "voiceEnabled": bool,
    "tts_enabled": bool, "wake_detection_enabled": bool,
    "geminiKey": str, "secretKey": str, "gitUrl": str, "weatherKey": str,
    "searchId": str, "encEnabled": bool, "biometrics": bool, "twoFactor": bool,
    "auditLog": bool,
}
_SECRET_FIELDS = {"geminiKey", "secretKey", "weatherKey", "searchId"}


def _hidden_subprocess_kwargs() -> dict[str, Any]:
    """Return creationflags and STARTUPINFO to guarantee zero console window popup on Windows."""
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0  # SW_HIDE
        kwargs["startupinfo"] = startupinfo
    return kwargs


def _get_config_path() -> Path:
    """Find settings.json in development, PyInstaller onedir, or onefile."""
    import sys
    candidates = [
        Path(__file__).resolve().parents[1] / "config" / "settings.json",
    ]
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.insert(0, Path(sys._MEIPASS) / "config" / "settings.json")
        exe_dir = Path(sys.executable).parent
        candidates.insert(0, exe_dir / "_internal" / "config" / "settings.json")
        candidates.insert(0, exe_dir / "config" / "settings.json")

    for cand in candidates:
        if cand.is_file():
            return cand
    return candidates[0]


def _get_frontend_dist_dir() -> Path:
    """Find frontend/dist directory in development, PyInstaller onedir, or onefile."""
    import sys
    candidates = [
        Path(__file__).resolve().parents[1] / "frontend" / "dist",
    ]
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.insert(0, Path(sys._MEIPASS) / "frontend" / "dist")
        exe_dir = Path(sys.executable).parent
        candidates.insert(0, exe_dir / "_internal" / "frontend" / "dist")
        candidates.insert(0, exe_dir / "frontend" / "dist")

    for cand in candidates:
        if cand.is_dir() and (cand / "index.html").is_file():
            return cand
    return candidates[0]


def load_config() -> dict[str, Any]:
    """Load configuration from settings.json."""
    config_path = _get_config_path()
    try:
        with config_path.open("r", encoding="utf-8") as f:
            saved = json.load(f)
            return {**_DEFAULT_SETTINGS, **saved}
    except Exception:
        return dict(_DEFAULT_SETTINGS)


def save_config(config: dict[str, Any]) -> bool:
    """Atomically persist configuration so an interrupted write cannot erase it."""
    config_path = _get_config_path()
    try:
        temporary_path = config_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        os.replace(temporary_path, config_path)
        return True
    except Exception:
        return False


def public_settings() -> dict[str, Any]:
    """Return settings without exposing API secrets to the browser."""
    settings = load_config()
    for field in _SECRET_FIELDS:
        if settings.get(field):
            settings[field] = "•" * 12
    return settings


def save_settings_patch(payload: dict[str, Any]) -> bool:
    """Merge only validated UI settings; never allow a request to replace config."""
    current = load_config()
    changed = False
    for field, value in payload.items():
        expected = _SETTINGS_FIELDS.get(field)
        if expected is None or not isinstance(value, expected):
            continue
        if isinstance(value, str):
            if len(value) > 512:
                continue
            # A masked secret shown by the UI means "leave the stored value alone".
            if field in _SECRET_FIELDS and "•" in value:
                continue
        if field == "temperature" and not 0 <= float(value) <= 1:
            continue
        current[field] = value
        changed = True
    return save_config(current) if changed else False


def get_api_config() -> tuple[str, int]:
    """Get API host and port from config."""
    config = load_config()
    api_cfg = config.get("api", {})
    return api_cfg.get("host", "127.0.0.1"), api_cfg.get("port", 8765)


def get_frontend_config() -> tuple[str, int]:
    """Get frontend dev host and port from config."""
    config = load_config()
    fe_cfg = config.get("frontend", {})
    return fe_cfg.get("dev_host", "127.0.0.1"), fe_cfg.get("dev_port", 5173)


def get_cors_origin() -> str:
    """Get the CORS origin for the frontend."""
    host, port = get_frontend_config()
    return f"http://{host}:{port}"


class _FileTime(ctypes.Structure):
    _fields_ = (("dwLowDateTime", ctypes.c_ulong), ("dwHighDateTime", ctypes.c_ulong))


class _MemoryStatus(ctypes.Structure):
    _fields_ = (
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    )


def _filetime_value(value: _FileTime) -> int:
    return (value.dwHighDateTime << 32) + value.dwLowDateTime


class SystemMetrics:
    """Reads the Windows metrics available without third-party packages."""

    def __init__(self) -> None:
        self._previous_cpu: tuple[int, int] | None = None
        self._previous_network: tuple[int, int, float] | None = None
        self._last_gpu_percent: float | None = None
        self._last_gpu_temperature: float | None = None
        self._last_gpu_sample_at = 0.0
        self._latest: dict[str, Any] | None = None
        self._lock = threading.Lock()

    @staticmethod
    def _network_bytes() -> tuple[int, int] | None:
        """Read aggregate interface counters without requiring administrator access."""
        try:
            result = subprocess.run(
                ["netstat", "-e"],
                capture_output=True,
                text=True,
                timeout=3,
                **_hidden_subprocess_kwargs(),
            )
            match = re.search(r"^Bytes\s+(\d[\d,]*)\s+(\d[\d,]*)", result.stdout, re.MULTILINE)
            if match:
                return tuple(int(value.replace(",", "")) for value in match.groups())
        except (OSError, subprocess.TimeoutExpired):
            pass
        return None

    def _gpu_telemetry(self) -> tuple[float | None, float | None]:
        """Read dedicated NVIDIA GPU temperature/utilization, with a Windows fallback."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                **_hidden_subprocess_kwargs(),
            )
            values = result.stdout.strip().splitlines()
            if values:
                temperature, utilization = (float(value.strip()) for value in values[0].split(",")[:2])
                self._last_gpu_temperature = temperature
                self._last_gpu_percent = max(0.0, min(100.0, utilization))
                return self._last_gpu_percent, self._last_gpu_temperature
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass

        # Fall back to Windows' GPU Engine counter if dedicated NVIDIA
        # telemetry is unavailable. Windows has no generic GPU temperature API.
        command = (
            "(Get-Counter '\\GPU Engine(*)\\Utilization Percentage').CounterSamples "
            "| Measure-Object -Property CookedValue -Maximum | Select-Object -ExpandProperty Maximum"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", command],
                capture_output=True,
                text=True,
                timeout=5,
                **_hidden_subprocess_kwargs(),
            )
            match = re.search(r"[-+]?\d+(?:\.\d+)?", result.stdout)
            if match:
                self._last_gpu_percent = round(max(0.0, min(100.0, float(match.group()))), 1)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
        return self._last_gpu_percent, self._last_gpu_temperature

    def snapshot(self) -> dict[str, Any]:
        # The HTTP server is threaded; preserve deltas between consecutive samples.
        with self._lock:
            self._latest = self._snapshot()
            return dict(self._latest)

    def latest(self) -> dict[str, Any]:
        """Return the most recent background sample without starting a new probe."""
        with self._lock:
            if self._latest:
                return dict(self._latest)
        return self.snapshot()

    def _snapshot(self) -> dict[str, Any]:
        memory = _MemoryStatus()
        memory.dwLength = ctypes.sizeof(_MemoryStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))

        idle, kernel, user = _FileTime(), _FileTime(), _FileTime()
        ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)
        )
        idle_value = _filetime_value(idle)
        total_value = _filetime_value(kernel) + _filetime_value(user)
        cpu_percent = 0.0
        if self._previous_cpu:
            previous_idle, previous_total = self._previous_cpu
            total_delta = total_value - previous_total
            if total_delta:
                cpu_percent = round(100 * (1 - (idle_value - previous_idle) / total_delta), 1)
        self._previous_cpu = (idle_value, total_value)

        now = time.monotonic()
        received_mbps = sent_mbps = network_mbps = None
        counters = self._network_bytes()
        if counters and self._previous_network:
            previous_received, previous_sent, previous_time = self._previous_network
            elapsed = now - previous_time
            if elapsed > 0:
                received_mbps = round(max(0, counters[0] - previous_received) * 8 / elapsed / 1_000_000, 3)
                sent_mbps = round(max(0, counters[1] - previous_sent) * 8 / elapsed / 1_000_000, 3)
                network_mbps = round(received_mbps + sent_mbps, 3)
        if counters:
            self._previous_network = (counters[0], counters[1], now)

        # Get-Counter is relatively expensive. Cache the GPU sample for five seconds
        # while CPU, memory, and network continue to update every second.
        if now - self._last_gpu_sample_at >= 5:
            gpu_percent, gpu_temperature = self._gpu_telemetry()
            self._last_gpu_sample_at = now
        else:
            gpu_percent = self._last_gpu_percent
            gpu_temperature = self._last_gpu_temperature

        return {
            "cpu_percent": max(0.0, min(100.0, cpu_percent)),
            "memory_percent": float(memory.dwMemoryLoad),
            "memory_used_bytes": memory.ullTotalPhys - memory.ullAvailPhys,
            "memory_total_bytes": memory.ullTotalPhys,
            "uptime_seconds": int(ctypes.windll.kernel32.GetTickCount64() / 1000),
            "network_percent": None,
            "network_mbps": network_mbps,
            "network_receive_mbps": received_mbps,
            "network_send_mbps": sent_mbps,
            "gpu_percent": gpu_percent,
            "temperature_celsius": gpu_temperature,
            "processes": [{"name": "jarvis-api", "cpu": None, "memory": None}],
            "collected_at": int(time.time()),
        }


class MetricsSampler:
    """Collects machine metrics once per second for HTTP and live-stream clients."""

    def __init__(self, metrics: SystemMetrics, interval_seconds: float = 1.0) -> None:
        self._metrics = metrics
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="jarvis-metrics", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            started = time.monotonic()
            self._metrics.snapshot()
            self._stop_event.wait(max(0.0, self._interval_seconds - (time.monotonic() - started)))


class JarvisApiServer:
    def __init__(self, host: str | None = None, port: int | None = None) -> None:
        if host is None or port is None:
            host, port = get_api_config()
        self.core = JarvisCore()
        self.metrics = SystemMetrics()
        self.metrics_sampler = MetricsSampler(self.metrics)
        self.memory = MemoryStore()
        self.voice = WindowsSpeechRecognizer()
        self.tts = WindowsSpeechSynthesizer()
        wake_phrase = load_config().get("wake_phrase", "Daddy's home")
        self.wake_detector = WakeDetector(wake_phrase=wake_phrase, on_wake=self._on_wake_detected)
        self.activity_log = ActivityLog()
        self._server = ThreadingHTTPServer((host, port), self._handler())
        self._thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._host = host
        self._port = port
        self._wake_window_callback = None

    def set_wake_callback(self, callback: Any) -> None:
        """Register UI callback when wake event is detected."""
        self._wake_window_callback = callback

    def _on_wake_detected(self, event: dict[str, Any]) -> None:
        """Handler invoked when wake phrase or clap is triggered."""
        self.voice._events.put(event)
        if not self.voice.is_listening:
            self.voice.start()
        self.tts.speak("Yes, sir?")
        if self._wake_window_callback:
            try:
                self._wake_window_callback()
            except Exception:
                pass

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        core, metrics, memory, voice, tts, wake_detector, activity_log, api_server = (
            self.core, self.metrics, self.memory, self.voice, self.tts, self.wake_detector, self.activity_log, self
        )

        class Handler(BaseHTTPRequestHandler):
            def _send(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", get_cors_origin())
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()
                self.wfile.write(body)

            def _serve_frontend(self) -> None:
                root = _get_frontend_dist_dir()
                request_path = unquote(urlparse(self.path).path).lstrip("/")
                candidate = (root / (request_path or "index.html")).resolve()
                if root not in candidate.parents and candidate != root:
                    self._send(HTTPStatus.FORBIDDEN, {"ok": False, "message": "Invalid frontend path."})
                    return
                # Client-side routes are served by React's index page.
                if not candidate.is_file():
                    # If this is a static asset request with an extension, return 404 so script parsers are not corrupted
                    if "." in Path(request_path).name:
                        self._send(HTTPStatus.NOT_FOUND, {"ok": False, "message": f"Asset '{request_path}' not found."})
                        return
                    candidate = root / "index.html"
                if not candidate.is_file():
                    self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"ok": False, "message": "Frontend build not found. Run npm run build in frontend."})
                    return
                body = candidate.read_bytes()
                # Ensure correct MIME type across all Windows configurations
                if candidate.name.endswith(".js"):
                    content_type = "text/javascript"
                elif candidate.name.endswith(".css"):
                    content_type = "text/css"
                elif candidate.name.endswith(".html"):
                    content_type = "text/html"
                elif candidate.name.endswith(".svg"):
                    content_type = "image/svg+xml"
                elif candidate.name.endswith(".json"):
                    content_type = "application/json"
                elif candidate.name.endswith(".png"):
                    content_type = "image/png"
                elif candidate.name.endswith((".woff", ".woff2")):
                    content_type = "font/woff2" if candidate.name.endswith(".woff2") else "font/woff"
                else:
                    content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)

            def _stream_metrics(self) -> None:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", get_cors_origin())
                self.end_headers()
                try:
                    while not api_server._stopping.is_set():
                        payload = json.dumps(metrics.latest())
                        self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        api_server._stopping.wait(1.0)
                except (BrokenPipeError, ConnectionResetError):
                    return

            def _stream_voice(self) -> None:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("Access-Control-Allow-Origin", get_cors_origin())
                self.end_headers()
                try:
                    while not api_server._stopping.is_set():
                        event = voice.next_event(timeout=1.0)
                        if event and event.get("type") == "transcript":
                            text_lower = str(event.get("text", "")).lower().strip()
                            last_spoken = getattr(tts, "last_spoken", "").lower().strip()
                            # Acoustic echo suppression: only drop if it echoes what JARVIS is currently speaking
                            if tts.is_speaking and last_spoken and (text_lower in last_spoken or last_spoken in text_lower):
                                continue
                        payload = event or {"type": "heartbeat", "listening": voice.is_listening}
                        self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return

            def do_OPTIONS(self) -> None:  # noqa: N802
                self._send(HTTPStatus.NO_CONTENT, {})

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/api/system/stream":
                    self._stream_metrics()
                elif self.path == "/api/voice/stream":
                    self._stream_voice()
                elif self.path == "/api/health":
                    self._send(HTTPStatus.OK, {"ok": True, "status": core.status, "name": core.name})
                elif self.path == "/api/system/metrics":
                    self._send(HTTPStatus.OK, metrics.latest())
                elif self.path == "/api/settings":
                    self._send(HTTPStatus.OK, {"ok": True, "settings": public_settings()})
                elif self.path == "/api/activity":
                    self._send(HTTPStatus.OK, {"ok": True, "entries": activity_log.recent()})
                elif self.path == "/api/memory":
                    self._send(HTTPStatus.OK, {"ok": True, "memories": memory.list()})
                elif self.path == "/api/memory/tags":
                    self._send(HTTPStatus.OK, {"ok": True, "tags": memory.get_all_tags()})
                elif self.path == "/api/wake/status":
                    self._send(HTTPStatus.OK, {"ok": True, "running": wake_detector.is_running, "phrase": wake_detector.wake_phrase})
                elif self.path.startswith("/api/memory/"):
                    mem_id = self.path.split("/api/memory/")[-1]
                    mem = memory.get(mem_id)
                    if mem:
                        self._send(HTTPStatus.OK, {"ok": True, "memory": mem})
                    else:
                        self._send(HTTPStatus.NOT_FOUND, {"ok": False, "message": "Memory not found"})
                else:
                    self._serve_frontend()

            def do_POST(self) -> None:  # noqa: N802
                if self.path == "/api/voice/start":
                    result = voice.start()
                    self._send(HTTPStatus.OK if result["ok"] else HTTPStatus.INTERNAL_SERVER_ERROR, result)
                elif self.path == "/api/voice/stop":
                    self._send(HTTPStatus.OK, voice.stop())
                elif self.path == "/api/voice/speak":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length) or b"{}")
                        text = str(payload.get("text", "")).strip()
                        res = tts.speak(text, rate=payload.get("rate"), volume=payload.get("volume"))
                        self._send(HTTPStatus.OK, res)
                    except Exception as e:
                        self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": str(e)})
                elif self.path == "/api/voice/stop_speech":
                    self._send(HTTPStatus.OK, tts.stop())
                elif self.path == "/api/wake/start":
                    res = wake_detector.start()
                    self._send(HTTPStatus.OK if res.get("ok") else HTTPStatus.INTERNAL_SERVER_ERROR, res)
                elif self.path == "/api/wake/stop":
                    self._send(HTTPStatus.OK, wake_detector.stop())
                elif self.path == "/api/commands/confirm":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length) or b"{}")
                        result = core.confirm_action(str(payload.get("action", "")), str(payload.get("target", "")), str(payload.get("source", "console")))
                        activity_log.record("confirmation", action=payload.get("action"), target=payload.get("target"), approved=True, ok=result["ok"])
                        if payload.get("source") in ("voice", "voice-text"):
                            tts.speak(result.get("message", ""))
                        self._send(HTTPStatus.OK if result["ok"] else HTTPStatus.BAD_REQUEST, result)
                    except (ValueError, json.JSONDecodeError):
                        self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Invalid JSON request."})
                elif self.path == "/api/commands/cancel":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length) or b"{}")
                        activity_log.record("confirmation", action=payload.get("action"), target=payload.get("target"), approved=False, ok=False)
                        self._send(HTTPStatus.OK, {"ok": True, "message": "Action cancelled."})
                    except (ValueError, json.JSONDecodeError):
                        self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Invalid JSON request."})
                elif self.path == "/api/commands":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length) or b"{}")
                        result = core.execute_command(
                            str(payload.get("command", "")), str(payload.get("source", "console"))
                        )
                        activity_log.record("command", command=payload.get("command", ""), source=payload.get("source", "console"), action=result.get("action"), requires_confirmation=result.get("requires_confirmation", False), ok=result["ok"])
                        cfg = load_config()
                        if payload.get("source") in ("voice", "voice-text") or cfg.get("tts_enabled", True):
                            tts.stop()
                            tts.speak(result.get("message", ""))
                        self._send(HTTPStatus.OK if result["ok"] else HTTPStatus.BAD_REQUEST, result)
                    except (ValueError, json.JSONDecodeError):
                        self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Invalid JSON request."})
                elif self.path == "/api/settings":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length) or b"{}")
                        if save_settings_patch(payload):
                            self._send(HTTPStatus.OK, {"ok": True, "message": "Settings saved"})
                        else:
                            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "message": "Failed to save settings"})
                    except (ValueError, json.JSONDecodeError):
                        self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Invalid JSON request."})
                elif self.path == "/api/memory":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length) or b"{}")
                        title = str(payload.get("title", "")).strip()
                        content = str(payload.get("content", "")).strip()
                        tags = payload.get("tags", [])
                        synced = bool(payload.get("synced", False))
                        if not title or not content:
                            self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Title and content required"})
                            return
                        mem = memory.add(title, content, tags, synced)
                        self._send(HTTPStatus.CREATED, {"ok": True, "memory": mem})
                    except (ValueError, json.JSONDecodeError):
                        self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Invalid JSON request."})
                elif self.path == "/api/chat":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length) or b"{}")
                        message = str(payload.get("message", "")).strip()
                        history = payload.get("history") or None
                        if not message:
                            self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Message required"})
                            return
                        result = ai_chat(message, history)
                        cfg = load_config()
                        if payload.get("source") in ("voice", "voice-text") or cfg.get("tts_enabled", True):
                            tts.stop()
                            tts.speak(result.get("message", ""))
                        self._send(HTTPStatus.OK, {"ok": result.get("ok", False), "message": result.get("message", ""), "action": result.get("action"), "data": result.get("data")})
                    except (ValueError, json.JSONDecodeError):
                        self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Invalid JSON request."})
                else:
                    self._send(HTTPStatus.NOT_FOUND, {"ok": False, "message": "Endpoint not found."})

            def do_PUT(self) -> None:  # noqa: N802
                if self.path.startswith("/api/memory/"):
                    mem_id = self.path.split("/api/memory/")[-1]
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        payload = json.loads(self.rfile.read(length) or b"{}")
                        updates = {}
                        if "title" in payload:
                            updates["title"] = str(payload["title"]).strip()
                        if "content" in payload:
                            updates["content"] = str(payload["content"]).strip()
                        if "tags" in payload:
                            updates["tags"] = payload["tags"]
                        if "synced" in payload:
                            updates["synced"] = bool(payload["synced"])
                        if memory.update(mem_id, **updates):
                            mem = memory.get(mem_id)
                            self._send(HTTPStatus.OK, {"ok": True, "memory": mem})
                        else:
                            self._send(HTTPStatus.NOT_FOUND, {"ok": False, "message": "Memory not found"})
                    except (ValueError, json.JSONDecodeError):
                        self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "message": "Invalid JSON request."})
                else:
                    self._send(HTTPStatus.NOT_FOUND, {"ok": False, "message": "Endpoint not found."})

            def do_DELETE(self) -> None:  # noqa: N802
                if self.path.startswith("/api/memory/"):
                    mem_id = self.path.split("/api/memory/")[-1]
                    if memory.delete(mem_id):
                        self._send(HTTPStatus.OK, {"ok": True, "message": "Memory deleted"})
                    else:
                        self._send(HTTPStatus.NOT_FOUND, {"ok": False, "message": "Memory not found"})
                else:
                    self._send(HTTPStatus.NOT_FOUND, {"ok": False, "message": "Endpoint not found."})

            def log_message(self, _format: str, *_args: Any) -> None:
                return

        return Handler

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.core.start()
        self._stopping.clear()
        self.metrics_sampler.start()
        # Seed initial memories
        initial_memories = [
            {
                "id": "1",
                "title": "System Configuration",
                "content": "Primary interface configured with Gemini 2.5 model. Performance mode: Ultra. Voice recognition sensitivity: 0.92.",
                "tags": ["system", "config"],
                "timestamp": int(time.time() * 1000) - 86400000 * 2,
                "synced": True,
            },
            {
                "id": "2",
                "title": "Voice Command Macro",
                "content": 'Created shortcut: "Deploy" = git push origin main && run deploy --production',
                "tags": ["voice", "dev"],
                "timestamp": int(time.time() * 1000) - 86400000,
                "synced": True,
            },
            {
                "id": "3",
                "title": "Research: Quantum Computing",
                "content": "Summarized 14 papers on quantum decoherence and error correction. Key finding: surface codes most viable for near-term QC implementation.",
                "tags": ["research", "quantum"],
                "timestamp": int(time.time() * 1000) - 3600000 * 5,
                "synced": False,
            },
            {
                "id": "4",
                "title": "API Integration Log",
                "content": "OpenWeather API integrated. Custom Search Engine ID configured. Gemini 2.5 API key stored in secure vault.",
                "tags": ["api", "config"],
                "timestamp": int(time.time() * 1000) - 3600000 * 2,
                "synced": True,
            },
            {
                "id": "5",
                "title": "User Preference Update",
                "content": "Dark mode holographic theme selected. Response verbosity: detailed. Gesture sensitivity calibrated to user profile.",
                "tags": ["preferences", "ui"],
                "timestamp": int(time.time() * 1000) - 1800000,
                "synced": True,
            },
        ]
        self.memory.seed_initial(initial_memories)
        if load_config().get("wake_detection_enabled", True):
            self.wake_detector.start()
        self._thread = threading.Thread(target=self._server.serve_forever, name="jarvis-api", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stopping.set()
        self.metrics_sampler.stop()
        self.wake_detector.stop()
        self.voice.stop()
        self.tts.close()
        self._server.shutdown()
        self._server.server_close()


def start_api_server() -> JarvisApiServer:
    server = JarvisApiServer()
    server.start()
    return server
