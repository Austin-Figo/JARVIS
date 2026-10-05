"""Unit tests for Windows Speech Synthesizer and Recognizer lifecycle."""

import unittest
from voice.windows_synthesizer import WindowsSpeechSynthesizer


class TestVoice(unittest.TestCase):
    def setUp(self):
        self.synth = WindowsSpeechSynthesizer()

    def tearDown(self):
        self.synth.stop()
        self.synth.close()

    def test_synthesizer_speak_and_stop(self):
        res = self.synth.speak("JARVIS subsystem test.")
        self.assertTrue(res["ok"])
        self.assertEqual(res["text"], "JARVIS subsystem test.")

        stop_res = self.synth.stop()
        self.assertTrue(stop_res["ok"])

    def test_synthesizer_empty_text(self):
        empty = self.synth.speak("")
        self.assertFalse(empty["ok"])


if __name__ == "__main__":
    unittest.main()
