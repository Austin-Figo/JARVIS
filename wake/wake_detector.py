"""Wake detection engine for JARVIS.

Integrates with the unified Windows speech recognizer to detect wake phrases
offline using System.Speech without audio device contention.
"""

from __future__ import annotations

import queue
import time
from typing import Any, Callable, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from voice.windows_recognizer import WindowsSpeechRecognizer


class WakeDetector:
    """Continuous offline detector for wake phrases."""

    def __init__(
        self,
        wake_phrase: str = "Daddy's home",
        on_wake: Callable[[Dict[str, Any]], None] | None = None,
        recognizer: Any | None = None,
    ) -> None:
        self.wake_phrase = wake_phrase
        self._on_wake = on_wake
        self._recognizer: Any | None = recognizer
        self._events: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._is_running = False

        if self._recognizer is not None:
            self._recognizer.set_wake_callback(self._handle_wake)

    @property
    def is_running(self) -> bool:
        if self._recognizer is not None:
            return self._recognizer.is_listening
        return self._is_running

    def _handle_wake(self, event: Dict[str, Any]) -> None:
        self._events.put(event)
        if self._on_wake:
            try:
                self._on_wake(event)
            except Exception:
                pass

    def start(self) -> Dict[str, Any]:
        """Start the wake detector."""
        if self._recognizer is not None:
            res = self._recognizer.start()
            self._is_running = self._recognizer.is_listening
            return {"ok": res.get("ok", True), "running": self.is_running, "message": res.get("message", "Wake detector active.")}

        if self.is_running:
            return {"ok": True, "running": True, "message": "Wake detector is already active."}

        from voice.windows_recognizer import WindowsSpeechRecognizer
        self._recognizer = WindowsSpeechRecognizer(wake_phrase=self.wake_phrase, on_wake=self._handle_wake)
        res = self._recognizer.start()
        self._is_running = self._recognizer.is_listening
        return {"ok": res.get("ok", True), "running": self.is_running, "message": f"Wake detector started (listening for '{self.wake_phrase}')."}

    def stop(self) -> Dict[str, Any]:
        """Stop the wake detector."""
        self._is_running = False
        if self._recognizer is not None:
            res = self._recognizer.stop()
            return {"ok": res.get("ok", True), "running": False, "message": "Wake detector stopped."}
        return {"ok": True, "running": False, "message": "Wake detector stopped."}

    def next_event(self, timeout: float = 1.0) -> Dict[str, Any] | None:
        """Poll the next detected wake event."""
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None
