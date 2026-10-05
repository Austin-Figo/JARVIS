"""Wake detection engine for JARVIS (Wake phrase 'Daddy's home' & Clap detection).

Runs offline on Windows using System.Speech.Recognition with a constrained grammar
and real-time audio level monitoring for transient spike (clap) detection.
"""

from __future__ import annotations

import base64
import queue
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List


_WAKE_SCRIPT = r'''
Add-Type -AssemblyName System.Speech
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$engine.SetInputToDefaultAudioDevice()

# Build targeted grammar for wake phrases
$builder = New-Object System.Speech.Recognition.GrammarBuilder
$choices = New-Object System.Speech.Recognition.Choices
$choices.Add([string[]]@("Daddy's home", "daddy's home", "Jarvis", "hey Jarvis", "wake up Jarvis"))
$builder.Append($choices)
$grammar = New-Object System.Speech.Recognition.Grammar($builder)
$engine.LoadGrammar($grammar)

# Audio level tracking for clap detection
$script:lastSpike = 0
$script:spikeCount = 0

$engine.add_AudioLevelUpdated({
    param($sender, $event)
    $level = $event.AudioLevel
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()

    # Peak detection: level > 78
    if ($level -ge 78) {
        $diff = $now - $script:lastSpike
        if ($diff -gt 180 -and $diff -lt 850) {
            [Console]::Out.WriteLine("CLAP:2")
            [Console]::Out.Flush()
            $script:lastSpike = 0
        } elseif ($diff -ge 850) {
            $script:lastSpike = $now
        }
    }
})

$engine.add_SpeechRecognized({
    param($sender, $event)
    if ($event.Result.Text) {
        [Console]::Out.WriteLine("WAKE:" + $event.Result.Text)
        [Console]::Out.Flush()
    }
})

[Console]::Out.WriteLine("READY")
[Console]::Out.Flush()

$engine.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)
while ($true) { Start-Sleep -Milliseconds 250 }
'''


class WakeDetector:
    """Continuous offline background detector for wake phrases and claps."""

    def __init__(self, wake_phrase: str = "Daddy's home", on_wake: Callable[[Dict[str, Any]], None] | None = None) -> None:
        self.wake_phrase = wake_phrase
        self._on_wake = on_wake
        self._events: queue.Queue[Dict[str, Any]] = queue.Queue()
        self._process: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._lock = threading.Lock()
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running and self._process is not None and self._process.poll() is None

    def start(self) -> Dict[str, Any]:
        """Start the background wake detector."""
        with self._lock:
            if self.is_running:
                return {"ok": True, "running": True, "message": "Wake detector is already active."}

            encoded = base64.b64encode(_WAKE_SCRIPT.encode("utf-16-le")).decode("ascii")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

            try:
                self._process = subprocess.Popen(
                    ["powershell", "-NoProfile", "-EncodedCommand", encoded],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    bufsize=1,
                    creationflags=flags,
                )
                self._is_running = True
                self._reader = threading.Thread(target=self._read_output, name="jarvis-wake-reader", daemon=True)
                self._reader.start()
                return {"ok": True, "running": True, "message": f"Wake detector started (listening for '{self.wake_phrase}' and claps)."}
            except Exception as e:
                self._is_running = False
                return {"ok": False, "running": False, "message": f"Could not start wake detector: {e}"}

    def stop(self) -> Dict[str, Any]:
        """Stop the wake detector."""
        with self._lock:
            self._is_running = False
            process = self._process
            self._process = None
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except Exception:
                    process.kill()
        return {"ok": True, "running": False, "message": "Wake detector stopped."}

    def next_event(self, timeout: float = 1.0) -> Dict[str, Any] | None:
        """Poll the next detected wake event."""
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def _read_output(self) -> None:
        """Read recognized events from child process."""
        proc = self._process
        if not proc or not proc.stdout:
            return

        for raw_line in proc.stdout:
            line = raw_line.strip()
            if not line:
                continue

            event: Dict[str, Any] | None = None
            if line.startswith("WAKE:"):
                phrase = line.split(":", 1)[1].strip()
                event = {
                    "type": "wake",
                    "trigger": "phrase",
                    "phrase": phrase,
                    "timestamp": int(time.time() * 1000),
                }
            elif line.startswith("CLAP:"):
                event = {
                    "type": "wake",
                    "trigger": "clap",
                    "phrase": "Double Clap",
                    "timestamp": int(time.time() * 1000),
                }

            if event:
                self._events.put(event)
                if self._on_wake:
                    try:
                        self._on_wake(event)
                    except Exception:
                        pass
