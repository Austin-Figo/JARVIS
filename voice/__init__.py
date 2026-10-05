"""Voice engine package for JARVIS."""

from voice.windows_recognizer import WindowsSpeechRecognizer
from voice.windows_synthesizer import WindowsSpeechSynthesizer, speak, get_synthesizer

__all__ = [
    "WindowsSpeechRecognizer",
    "WindowsSpeechSynthesizer",
    "speak",
    "get_synthesizer",
]
