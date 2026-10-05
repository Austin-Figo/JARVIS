"""Final comprehensive verification of JARVIS Phase 3+4."""
import json
import urllib.request
from app.backend_server import start_api_server
import time

s = start_api_server()
time.sleep(1)

results = []
def test(name, fn):
    try:
        fn()
        results.append((name, "PASS"))
    except Exception as e:
        results.append((name, f"FAIL: {str(e)[:30]}"))

# Test 1: Health
def t1():
    req = urllib.request.Request('http://127.0.0.1:8765/api/health', method='GET')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Health not ok: {result}"
test("Health check", t1)

# Test 2: System commands
for cmd in ['status', 'time', 'scan', 'help']:
    def make_test(c):
        def t():
            data = json.dumps({'command': c, 'source': 'test'}).encode()
            req = urllib.request.Request('http://127.0.0.1:8765/api/commands', data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            resp = urllib.request.urlopen(req)
            result = json.loads(resp.read().decode())
            assert result.get('ok') == True, f"Command {c} not ok"
            assert result.get('action') is not None, f"Command {c} has no action"
        test(f"Command {c}", make_test(cmd))
# Run the tests manually
for cmd in ['status', 'time', 'scan', 'help']:
    try:
        data = json.dumps({'command': cmd, 'source': 'test'}).encode()
        req = urllib.request.Request('http://127.0.0.1:8765/api/commands', data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        ok = result.get('ok', False)
        action = result.get('action', 'N/A')
        results.append((f"Command {cmd}", "PASS" if ok else "FAIL"))
    except Exception as e:
        results.append((f"Command {cmd}", f"FAIL: {str(e)[:30]}"))

# Test 3: Memory API
def t3():
    req = urllib.request.Request('http://127.0.0.1:8765/api/memory/tags', method='GET')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Memory tags not ok: {result}"
    assert len(result.get('tags', [])) > 0, "No tags found"
test("Memory tags", t3)

def t4():
    req = urllib.request.Request('http://127.0.0.1:8765/api/memory', method='GET')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Memory list not ok: {result}"
    assert len(result.get('memories', [])) >= 5, f"Expected >=5 memories, got {len(result.get('memories', []))}"
test("Memory list", t4)

def t5():
    data = json.dumps({'title': 'Verify Memory', 'content': 'Verification test', 'tags': ['verify'], 'synced': False}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/memory', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Memory create not ok: {result}"
test("Memory create", t5)

def t6():
    data = json.dumps({'title': 'Verify Memory', 'content': 'Verification test', 'tags': ['verify'], 'synced': False}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/memory', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    mid = result.get('memory', {}).get('id', '')
    # Test PUT
    data = json.dumps({'content': 'Updated content'}).encode()
    req = urllib.request.Request(f'http://127.0.0.1:8765/api/memory/{mid}', data=data, method='PUT')
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Memory update not ok: {result}"
    # Test DELETE
    req = urllib.request.Request(f'http://127.0.0.1:8765/api/memory/{mid}', method='DELETE')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Memory delete not ok: {result}"
test("Memory update/delete", t6)

# Test 4: Settings API
def t7():
    req = urllib.request.Request('http://127.0.0.1:8765/api/settings', method='GET')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Settings GET not ok: {result}"
test("Settings GET", t7)

def t8():
    data = json.dumps({'require_confirmation_for_sensitive_actions': False}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/settings', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Settings POST not ok: {result}"
test("Settings POST", t8)

# Test 5: Chat API
def t9():
    data = json.dumps({'message': 'status'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/chat', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Chat status not ok: {result}"
test("Chat API", t9)

def t10():
    data = json.dumps({'message': 'scan the system'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/chat', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    assert result.get('ok') == True, f"Chat scan not ok: {result}"
    assert result.get('action') == 'scan', f"Expected action=scan, got {result.get('action')}"
test("Chat with function call", t10)

# Test 6: Blocked command
def t11():
    data = json.dumps({'command': 'run rm -rf /', 'source': 'test'}).encode()
    req = urllib.request.Request('http://127.0.0.1:8765/api/commands', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read().decode())
        assert result.get('ok') == False, "Blocked command should not be ok"
    except urllib.error.HTTPError:
        pass  # Expected
test("Blocked command rejection", t11)

print("=" * 60)
passed = sum(1 for _, status in results if "PASS" in status)
failed = sum(1 for _, status in results if "FAIL" in status)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(results)} tests")
print("=" * 60)

if failed == 0:
    print("ALL TESTS PASSED - Phase 4 complete!")
else:
    print("SOME TESTS FAILED - need attention")
    for name, status in results:
        print(f"  {name}: {status}")