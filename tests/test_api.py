"""Integration tests for local JARVIS HTTP & SSE API server."""

import json
import time
import unittest
import urllib.request
from app.backend_server import start_api_server


class TestApiServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = start_api_server()
        time.sleep(1.0)
        cls.base_url = f"http://{cls.server._host}:{cls.server._port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def _get(self, path):
        req = urllib.request.Request(f"{self.base_url}{path}", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post(self, path, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}{path}", data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_health_endpoint(self):
        res = self._get("/api/health")
        self.assertTrue(res["ok"])
        self.assertEqual(res["name"], "JARVIS")

    def test_metrics_endpoint(self):
        res = self._get("/api/system/metrics")
        self.assertIn("cpu_percent", res)
        self.assertIn("memory_percent", res)

    def test_commands_endpoint(self):
        res = self._post("/api/commands", {"command": "status", "source": "test"})
        self.assertTrue(res["ok"])
        self.assertEqual(res["action"], "status")

    def test_memory_crud_endpoints(self):
        # Create
        create_res = self._post("/api/memory", {
            "title": "API Test Memory",
            "content": "Verified via test_api.py",
            "tags": ["api_test"],
            "synced": False,
        })
        self.assertTrue(create_res["ok"])
        mem_id = create_res["memory"]["id"]

        # List
        list_res = self._get("/api/memory")
        self.assertTrue(list_res["ok"])
        self.assertGreaterEqual(len(list_res["memories"]), 1)

        # Tags
        tags_res = self._get("/api/memory/tags")
        self.assertTrue(tags_res["ok"])
        self.assertIn("api_test", tags_res["tags"])

    def test_chat_endpoint(self):
        res = self._post("/api/chat", {"message": "Run diagnostic", "history": []})
        self.assertTrue(res["ok"])
        self.assertEqual(res["action"], "scan")

    def test_wake_status_endpoint(self):
        res = self._get("/api/wake/status")
        self.assertTrue(res["ok"])
        self.assertIn("phrase", res)


if __name__ == "__main__":
    unittest.main()
