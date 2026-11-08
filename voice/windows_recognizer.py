"""Offline Windows Speech Recognition bridge for JARVIS.

The recognizer runs in a single child PowerShell process because System.Speech is a
Windows desktop API. It loads both a constrained WakeGrammar and a freeform
DictationGrammar on one unified audio stream, preventing microphone contention.
It never sends microphone audio to a network service.
"""

from __future__ import annotations

import base64
import os
import queue
import subprocess
import threading
import time
from typing import Any, Callable


def _build_script(wake_phrase: str = "Hey Jarvis") -> str:
    # Ensure wake phrases include defaults + custom phrase
    safe_phrase = wake_phrase.replace("'", "''").strip()
    return f"""
Add-Type -AssemblyName System.Speech
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$engine.SetInputToDefaultAudioDevice()

# Grammar 1: Wake phrases (priority matching)
$wakeChoices = New-Object System.Speech.Recognition.Choices
$wakeChoices.Add([string[]]@(
    "Hey Jarvis", "hey Jarvis", "hey jarvis",
    "He Jarvis", "he Jarvis", "he jarvis",
    "Hi Jarvis", "hi Jarvis", "hi jarvis",
    "Jarvis", "jarvis",
    "Daddy's home", "daddy's home",
    "Wake up Jarvis", "wake up jarvis",
    "Hello Jarvis", "hello jarvis",
    "Ok Jarvis", "Okay Jarvis", "okay jarvis",
    '{safe_phrase}'
))
$wakeBuilder = New-Object System.Speech.Recognition.GrammarBuilder
$wakeBuilder.Append($wakeChoices)
$wakeGrammar = New-Object System.Speech.Recognition.Grammar($wakeBuilder)
$wakeGrammar.Name = "WakeGrammar"
$wakeGrammar.Weight = 1.0
$engine.LoadGrammar($wakeGrammar)

# Grammar 2: Freeform dictation
$dictGrammar = New-Object System.Speech.Recognition.DictationGrammar
$dictGrammar.Name = "DictationGrammar"
$dictGrammar.Weight = 0.6
$engine.LoadGrammar($dictGrammar)

try {{
    $engine.InitialSilenceTimeout = [TimeSpan]::FromSeconds(8)
    $engine.EndSilenceTimeout = [TimeSpan]::FromSeconds(1.2)
    $engine.EndSilenceTimeoutAmbiguous = [TimeSpan]::FromSeconds(1.0)
}} catch {{}}

$engine.add_SpeechDetected({{
    param($sender, $event)
    [Console]::Out.WriteLine("SPEECH_START")
    [Console]::Out.Flush()
}})

$engine.add_SpeechHypothesized({{
    param($sender, $event)
    if ($event.Result -ne $null -and $event.Result.Text) {{
        [Console]::Out.WriteLine("HYPOTHESIS:" + $event.Result.Text)
        [Console]::Out.Flush()
    }}
}})

$engine.add_SpeechRecognized({{
    param($sender, $event)
    if ($event.Result -ne $null -and $event.Result.Text) {{
        $text = $event.Result.Text
        $grammarName = ""
        if ($event.Result.Grammar -ne $null) {{
            $grammarName = $event.Result.Grammar.Name
        }}
        if ($grammarName -eq "WakeGrammar") {{
            [Console]::Out.WriteLine("WAKE:" + $text)
        }} else {{
            [Console]::Out.WriteLine("RESULT:" + $text)
        }}
        [Console]::Out.Flush()
    }}
}})

$engine.add_RecognizeCompleted({{
    param($sender, $event)
    if ($event.Error) {{
        [Console]::Out.WriteLine("ERROR:" + $event.Error.Message)
        [Console]::Out.Flush()
    }}
}})

[Console]::Out.WriteLine("READY")
[Console]::Out.Flush()
$engine.RecognizeAsync([System.Speech.Recognition.RecognizeMode]::Multiple)
while ($true) {{ Start-Sleep -Milliseconds 250 }}
"""


class WindowsSpeechRecognizer:
    def __init__(
        self,
        wake_phrase: str = "Hey Jarvis",
        on_wake: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.wake_phrase = wake_phrase
        self._on_wake = on_wake
        self._events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._process: subprocess.Popen[str] | None = None
        self._reader: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_listening(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def set_wake_callback(self, callback: Callable[[dict[str, Any]], None] | None) -> None:
        """Register or update wake callback."""
        self._on_wake = callback

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
                script = _build_script(self.wake_phrase)
                encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
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
            if not line:
                continue
            if line == "READY":
                self._events.put({"type": "status", "listening": True, "message": "Microphone ready."})
            elif line == "SPEECH_START":
                self._events.put({"type": "speech_start", "message": "Speech detected."})
            elif line.startswith("HYPOTHESIS:"):
                text = line.removeprefix("HYPOTHESIS:").strip()
                if text:
                    self._events.put({"type": "hypothesis", "text": text})
            elif line.startswith("WAKE:"):
                phrase = line.removeprefix("WAKE:").strip()
                event = {
                    "type": "wake",
                    "phrase": phrase,
                    "timestamp": int(time.time() * 1000),
                }
                self._events.put(event)
                if self._on_wake:
                    try:
                        self._on_wake(event)
                    except Exception:
                        pass
            elif line.startswith("RESULT:"):
                text = line.removeprefix("RESULT:").strip()
                if text:
                    self._events.put({"type": "transcript", "text": text})
            elif line.startswith("ERROR:"):
                self._events.put({"type": "error", "message": line.removeprefix("ERROR:").strip()})
        if self.is_listening:
            self._events.put({"type": "error", "message": "Windows speech recognition stopped unexpectedly."})
