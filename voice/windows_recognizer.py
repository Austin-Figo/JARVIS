"""Offline Windows Speech Recognition bridge for JARVIS.

The recognizer runs in a child PowerShell process because System.Speech is a
Windows desktop API. It never sends microphone audio to a network service.
"""

from __future__ import annotations

import base64
import os
import queue
import subprocess
import threading
from typing import Any


_SCRIPT = r'''
Add-Type -AssemblyName System.Speech
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$engine.SetInputToDefaultAudioDevice()
$engine.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))

try {
  $engine.InitialSilenceTimeout = [TimeSpan]::FromSeconds(8)
  $engine.EndSilenceTimeout = [TimeSpan]::FromSeconds(1.2)
  $engine.EndSilenceTimeoutAmbiguous = [TimeSpan]::FromSeconds(1.0)
} catch {}

$engine.add_SpeechDetected({
  param($sender, $event)
  [Console]::Out.WriteLine("SPEECH_START")
  [Console]::Out.Flush()
})

$engine.add_SpeechRecognized({
  param($sender, $event)
  if ($event.Result.Text) {
    [Console]::Out.WriteLine("RESULT:" + $event.Result.Text)
    [Console]::Out.Flush()
  }
})
$engine.add_RecognizeCompleted({
  param($sender, $event)
  if ($event.Error) {
    [Console]::Out.WriteLine("ERROR:" + $event.Error.Message)
    [Console]::Out.Flush()
  }
})
[Console]::Out.WriteLine("READY")
[Console]::Out.Flush()
$engine.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)
while ($true) { Start-Sleep -Milliseconds 250 }
'''


class WindowsSpeechRecognizer:
    def __init__(self) -> None:
        self._events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._process: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_listening(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self.is_listening:
                return {"ok": True, "listening": True, "message": "Voice recognition is already listening."}
            kwargs = {}
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                kwargs["startupinfo"] = startupinfo
            try:
                encoded = base64.b64encode(_SCRIPT.encode("utf-16le")).decode("ascii")
                self._process = subprocess.Popen(
                    ["powershell", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-EncodedCommand", encoded],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    **kwargs,
                )
            except OSError as error:
                return {"ok": False, "listening": False, "message": f"Unable to start Windows speech recognition: {error}"}
            self._reader = threading.Thread(target=self._read_events, name="jarvis-voice", daemon=True)
            self._reader.start()
            return {"ok": True, "listening": True, "message": "Offline Windows speech recognition started."}

    def stop(self) -> dict[str, Any]:
        with self._lock:
            process, self._process = self._process, None
            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            self._events.put({"type": "status", "listening": False, "message": "Voice recognition stopped."})
        return {"ok": True, "listening": False, "message": "Voice recognition stopped."}

    def next_event(self, timeout: float = 1.0) -> dict[str, Any] | None:
        try:
            return self._events.get(timeout=timeout)
        except queue.Empty:
            return None

    def _read_events(self) -> None:
        process = self._process
        if not process or not process.stdout:
            return
        for raw_line in process.stdout:
            line = raw_line.strip()
            if line == "READY":
                self._events.put({"type": "status", "listening": True, "message": "Microphone ready."})
            elif line == "SPEECH_START":
                self._events.put({"type": "speech_start", "message": "Speech detected."})
            elif line.startswith("RESULT:"):
                self._events.put({"type": "transcript", "text": line.removeprefix("RESULT:").strip()})
            elif line.startswith("ERROR:"):
                self._events.put({"type": "error", "message": line.removeprefix("ERROR:").strip()})
        if self.is_listening:
            self._events.put({"type": "error", "message": "Windows speech recognition stopped unexpectedly."})
