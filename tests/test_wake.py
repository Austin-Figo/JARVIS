"""Unit tests for WakeDetector lifecycle and configuration."""

import unittest
from wake.wake_detector import WakeDetector


class TestWakeDetector(unittest.TestCase):
    def test_detector_initialization(self):
        detector = WakeDetector(wake_phrase="Daddy's home")
        self.assertEqual(detector.wake_phrase, "Daddy's home")
        self.assertFalse(detector.is_running)

    def test_custom_wake_phrase(self):
        detector = WakeDetector(wake_phrase="Hey Jarvis")
        self.assertEqual(detector.wake_phrase, "Hey Jarvis")


if __name__ == "__main__":
    unittest.main()
