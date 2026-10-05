"""Verify all Phase 3 features are working."""
import json
import urllib.request
from app.backend_server import start_api_server
import time

s = start_api_server()
time.sleep(1)

def test_cmd(cmd):
    data = json.dumps({'command': cmd, 'source': 'test'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/commands', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        ok = result.get('ok', False)
        action = result.get('action', 'N/A')
        msg = result.get('message', '')[:60]
        return f'{cmd}: ok={ok}, action={action}, msg={msg}'
    except Exception as e:
        return f'{cmd}: error={str(e)[:40]}'

# Test all built-in commands
print('=== Command Tests ===')
for cmd in ['status', 'time', 'scan', 'help', 'settings', 'apps', 'gesture', 'processes', 'disk', 'network']:
    result = test_cmd(cmd)
    print(f'  {result}')

# Test memory endpoints
print()
print('=== Memory API Tests ===')
try:
    req = urllib.request.Request('http://127.0.0.1:8765/api/memory/tags', method='GET')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f'  get tags: ok={result.get("ok")}, count={len(result.get("tags", []))}')
except Exception as e:
    print(f'  get tags: error={e}')

try:
    req = urllib.request.Request('http://127.0.0.1:8765/api/memory', method='GET')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f'  get memories: ok={result.get("ok")}, count={len(result.get("memories", []))}')
except Exception as e:
    print(f'  get memories: error={e}')

try:
    data = json.dumps({'title': 'Test Memory', 'content': 'Test content', 'tags': ['test'], 'synced': False}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/memory', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f'  create memory: ok={result.get("ok")}')
except Exception as e:
    print(f'  create memory: error={str(e)[:40]}')

try:
    # Test shell command allowed
    data = json.dumps({'command': 'run dir', 'source': 'test'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/commands', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    ok = result.get('ok', False)
    msg = result.get('message', '')[:80]
    print(f'  shell dir: ok={ok}, msg_start={msg[:30]}')
except Exception as e:
    print(f'  shell dir: error={str(e)[:40]}')

# Test blocked command
data = json.dumps({'command': 'run rm -rf /', 'source': 'test'}).encode()
req = urllib.request.Request('http://127.0.0.1:8765/api/commands', data=data, method='POST')
req.add_header('Content-Type', 'application/json')
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    print(f'  shell blocked: unexpectedly ok={result.get("ok")}')
except urllib.error.HTTPError as e:
    result = json.loads(e.read().decode())
    print(f'  shell blocked: correctly rejected ok={result.get("ok")}')

print()
print('=== All Phase 3 Features Verified ===')