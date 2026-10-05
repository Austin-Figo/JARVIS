"""Offline Windows Speech Synthesis (TTS) engine for JARVIS.

Uses Windows native System.Speech.Synthesis.SpeechSynthesizer via a persistent
hidden PowerShell process with zero external Python dependencies.
"""

from __future__ import annotations

import base64
import queue
import subprocess
import threading
import time
from typing import Any, Dict, List


_TTS_SCRIPT = r'''
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
[Console]::Out.WriteLine("READY")
[Console]::Out.Flush()

while ($true) {
    $line = [Console]::In.ReadLine()
    if ($line -eq $null -or $line -eq "QUIT") { break }
    if ($line.StartsWith("RATE:")) {
        try { $synth.Rate = [int]$line.Substring(5) } catch {}
    } elseif ($line.StartsWith("VOLUME:")) {
        try { $synth.Volume = [int]$line.Substring(7) } catch {}
    } elseif ($line.StartsWith("VOICE:")) {
        try { $synth.SelectVoice($line.Substring(6).Trim()) } catch {}
    } elseif ($line.StartsWith("STOP")) {
        try { $synth.SpeakAsyncCancelAll() } catch {}
    } elseif ($line.StartsWith("SPEAK:")) {
        $text = $line.Substring(6)
        try {
            $synth.Speak($text)
        } catch {}
        [Console]::Out.WriteLine("DONE")
        [Console]::Out.Flush()
    }
}
'''


class WindowsSpeechSynthesizer:
    """Thread-safe, queued Windows Speech Synthesizer."""

    def __init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._queue: queue.Queue[tuple[str, int, int]] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._lock = threading.Lock()
        self._running = False
        self._is_speaking = False
        self._active_voice: str | None = None
        self._rate = 0  # -10 to 10
        self._volume = 100  # 0 to 100
        self._start_engine()

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def _start_engine(self) -> bool:
        """Start the background speech synthesis process."""
        with self._lock:
            if self._process and self._process.poll() is None:
                return True

            encoded = base64.b64encode(_TTS_SCRIPT.encode("utf-16-le")).decode("ascii")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            try:
                self._process = subprocess.Popen(
                    ["powershell", "-NoProfile", "-EncodedCommand", encoded],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    bufsize=1,
                    creationflags=flags,
                )
                # Wait briefly for READY banner
                ready_line = self._process.stdout.readline().strip() if self._process.stdout else ""
                self._running = True

                self._worker = threading.Thread(target=self._process_queue, name="jarvis-tts-worker", daemon=True)
                self._worker.start()
                return True
            except Exception:
                self._running = False
                return False

    def _process_queue(self) -> None:
        """Worker thread processing queued speech utterances."""
        while self._running:
            try:
                item = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue

            text, rate, volume = item
            if not self._process or self._process.poll() is not None:
                if not self._start_engine():
                    self._queue.task_done()
                    continue

            try:
                self._is_speaking = True
                clean_text = text.replace("\r", " ").replace("\n", " ").strip()
                if self._process.stdin:
                    self._process.stdin.write(f"RATE:{rate}\n")
                    self._process.stdin.write(f"VOLUME:{volume}\n")
                    if self._active_voice:
                        self._process.stdin.write(f"VOICE:{self._active_voice}\n")
                    self._process.stdin.write(f"SPEAK:{clean_text}\n")
                    self._process.stdin.flush()

                # Read DONE
                if self._process.stdout:
                    _ = self._process.stdout.readline()
            except Exception:
                pass
            finally:
                self._is_speaking = False
                self._queue.task_done()

    def speak(self, text: str, wait: bool = False, rate: int | None = None, volume: int | None = None) -> Dict[str, Any]:
        """Queue text to be spoken aloud."""
        clean = text.strip()
        if not clean:
            return {"ok": False, "message": "Text is empty."}

        # Remove markdown symbols and code fences for cleaner speech
        clean_spoken = clean.replace("`", "").replace("*", "").replace("#", "")

        effective_rate = self._rate if rate is None else max(-10, min(10, rate))
        effective_volume = self._volume if volume is None else max(0, min(100, volume))

        self._queue.put((clean_spoken, effective_rate, effective_volume))

        if wait:
            self._queue.join()

        return {"ok": True, "message": "Speech queued.", "text": clean_spoken}

    def stop(self) -> Dict[str, Any]:
        """Cancel ongoing and queued speech."""
        with self._lock:
            # Drain queue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except queue.Empty:
                    break

            if self._process and self._process.stdin and self._process.poll() is None:
                try:
                    self._process.stdin.write("STOP\n")
                    self._process.stdin.flush()
                except Exception:
                    pass

            self._is_speaking = False
        return {"ok": True, "message": "Speech cancelled."}

    def set_voice(self, voice_name: str) -> None:
        """Set voice by name (e.g., 'Microsoft David Desktop', 'Microsoft Zira Desktop')."""
        self._active_voice = voice_name

    def close(self) -> None:
        """Shut down synthesizer process cleanly."""
        self._running = False
        self.stop()
        with self._lock:
            if self._process and self._process.poll() is None:
                try:
                    if self._process.stdin:
                        self._process.stdin.write("QUIT\n")
                        self._process.stdin.flush()
                    self._process.wait(timeout=2)
                except Exception:
                    self._process.kill()
                self._process = None


# Global synthesizer instance
_synthesizer: WindowsSpeechSynthesizer | None = None


def get_synthesizer() -> WindowsSpeechSynthesizer:
    """Get or create singleton synthesizer."""
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = WindowsSpeechSynthesizer()
    return _synthesizer


def speak(text: str, wait: bool = False) -> Dict[str, Any]:
    """Convenience helper to speak text."""
    return get_synthesizer().speak(text, wait=wait)
