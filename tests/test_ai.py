"""Unit tests for AI Provider and RAG memory integration."""

import tempfile
import unittest
from pathlib import Path
from ai.provider import AIProvider
from memory.store import MemoryStore


class TestAIProvider(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db_path = Path(self.tmp.name)
        self.store = MemoryStore(self.db_path)
        self.ai = AIProvider(provider="mock", memory=self.store)

    def tearDown(self):
        try:
            self.db_path.unlink()
        except Exception:
            pass

    def test_direct_save_memory_intent(self):
        resp = self.ai.chat("Remember that my secret code is 4209")
        self.assertTrue(resp["ok"])
        self.assertEqual(resp["action"], "memory_saved")
        self.assertIn("secret code", resp["message"])

        # Check DB
        mems = self.store.list(query="4209")
        self.assertEqual(len(mems), 1)

    def test_direct_recall_memory_intent(self):
        self.store.add("Travel Plan", "Trip to Tokyo in September", tags=["travel"])
        resp = self.ai.chat("What are my memories about Tokyo?")
        self.assertTrue(resp["ok"])
        self.assertIn("Tokyo", resp["message"])

    def test_mock_fallback_commands(self):
        # Scan
        res_scan = self.ai.chat("Run system scan")
        self.assertTrue(res_scan["ok"])
        self.assertEqual(res_scan["action"], "scan")

        # Status
        res_stat = self.ai.chat("What is your status?")
        self.assertTrue(res_stat["ok"])
        self.assertEqual(res_stat["action"], "status")

        # Time
        res_time = self.ai.chat("What time is it?")
        self.assertTrue(res_time["ok"])
        self.assertEqual(res_time["action"], "time")

        # Battery
        res_bat = self.ai.chat("Check battery status")
        self.assertTrue(res_bat["ok"])

    def test_function_call_parsing(self):
        mock_llm_output = '{"action": "status", "parameters": {}}'
        parsed = self.ai._try_parse_function_call(mock_llm_output, "test")
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["action"], "status")


if __name__ == "__main__":
    unittest.main()
