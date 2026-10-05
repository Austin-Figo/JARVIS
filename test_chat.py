"""Test the /api/chat endpoint."""
import json
import urllib.request
from app.backend_server import start_api_server
import time

s = start_api_server()
time.sleep(1)

# Test /api/chat endpoint
tests = [
    ("status", {"message": "What is the status?"}),
    ("time", {"message": "What time is it?"}),
    ("help", {"message": "Help me"}),
]

print("=== Chat API Tests ===")
for label, payload in tests:
    data = json.dumps(payload).encode()
    req = urllib.request.Request("http://127.0.0.1:8765/api/chat", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        ok = result.get("ok", False)
        action = result.get("action", "N/A")
        msg = result.get("message", "")[:60]
        print(f"  {label}: ok={ok}, action={action}, msg={msg}")
    except Exception as e:
        print(f"  {label}: error={str(e)[:40]}")

# Test with function call (scan)
data = json.dumps({"message": "scan the system", "history": []}).encode()
req = urllib.request.Request("http://127.0.0.1:8765/api/chat", data=data, method="POST")
req.add_header("Content-Type", "application/json")
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    ok = result.get("ok", False)
    action = result.get("action", "N/A")
    msg = result.get("message", "")[:80]
    print(f"  scan: ok={ok}, action={action}, msg={msg}")
except Exception as e:
    print(f"  scan: error={str(e)[:40]}")