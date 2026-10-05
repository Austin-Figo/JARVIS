"""Unit tests for JARVIS Core engine."""

import unittest
from core.jarvis_core import JarvisCore, _get_cpu_percent, _get_memory_info, _get_disk_info


class TestJarvisCore(unittest.TestCase):
    def setUp(self):
        self.core = JarvisCore()
        self.core.start()

    def test_core_initialization(self):
        self.assertEqual(self.core.name, "JARVIS")
        self.assertEqual(self.core.status, "ONLINE")

    def test_system_telemetry(self):
        cpu, _ = _get_cpu_percent()
        self.assertGreaterEqual(cpu, 0.0)
        self.assertLessEqual(cpu, 100.0)

        mem = _get_memory_info()
        self.assertIn("percent", mem)
        self.assertGreater(mem["total_bytes"], 0)

        disks = _get_disk_info()
        self.assertIsInstance(disks, list)
        self.assertGreater(len(disks), 0)

    def test_built_in_commands(self):
        # Scan
        scan_res = self.core.execute_command("scan")
        self.assertTrue(scan_res["ok"])
        self.assertEqual(scan_res["action"], "scan")
        self.assertIn("scan_results", scan_res)

        # Status
        status_res = self.core.execute_command("status")
        self.assertTrue(status_res["ok"])
        self.assertEqual(status_res["action"], "status")

        # Time
        time_res = self.core.execute_command("time")
        self.assertTrue(time_res["ok"])
        self.assertEqual(time_res["action"], "time")

        # Help
        help_res = self.core.execute_command("help")
        self.assertTrue(help_res["ok"])
        self.assertEqual(help_res["action"], "help")

    def test_blocked_commands(self):
        blocked = self.core.execute_command("run rm -rf /")
        self.assertFalse(blocked["ok"])
        self.assertIn("disabled", blocked["message"].lower())

    def test_open_app_confirmation(self):
        app_res = self.core.execute_command("open notepad")
        self.assertTrue(app_res["ok"])
        self.assertTrue(app_res.get("requires_confirmation"))
        self.assertIn("confirmation", app_res)


if __name__ == "__main__":
    unittest.main()
