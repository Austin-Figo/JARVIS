"""Unit tests for Windows Actions and Workflows."""

import unittest
from actions.system_controls import (
    volume_up,
    volume_down,
    volume_mute,
    media_play_pause,
    get_power_status,
)
from actions.browser import search_web, open_url
from automation.workflows import run_workflow


class TestActions(unittest.TestCase):
    def test_volume_controls(self):
        res_up = volume_up(1)
        self.assertTrue(res_up["ok"])

        res_down = volume_down(1)
        self.assertTrue(res_down["ok"])

        res_mute = volume_mute()
        self.assertTrue(res_mute["ok"])

    def test_media_control(self):
        res = media_play_pause()
        self.assertTrue(res["ok"])

    def test_power_status(self):
        res = get_power_status()
        self.assertTrue(res["ok"])
        self.assertIn("ac_line_status", res.get("data", {}))

    def test_browser_search_formatting(self):
        # Empty query
        empty = search_web("")
        self.assertFalse(empty["ok"])

    def test_workflows(self):
        focus = run_workflow("focus_mode")
        self.assertTrue(focus["ok"])
        self.assertEqual(focus["workflow"], "focus_mode")

        dev = run_workflow("dev_mode")
        self.assertTrue(dev["ok"])
        self.assertEqual(dev["workflow"], "dev_mode")

        diag = run_workflow("diagnostics_mode")
        self.assertTrue(diag["ok"])
        self.assertEqual(diag["workflow"], "diagnostics_mode")


    def test_app_launcher(self):
        from actions.app_launcher import resolve_application, get_available_system_apps
        self.assertIsNotNone(resolve_application("calc"))
        self.assertIsNotNone(resolve_application("notepad"))
        self.assertIsNotNone(resolve_application("cmd"))
        self.assertIsNotNone(resolve_application("settings"))
        self.assertGreater(len(get_available_system_apps()), 10)


if __name__ == "__main__":
    unittest.main()
