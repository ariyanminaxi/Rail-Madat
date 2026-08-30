"""Quick endpoint test script."""
import subprocess, time, urllib.request, json, sys

import os
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.join(os.path.dirname(__file__), 'backend')
)
time.sleep(5)

# Read any startup errors
proc.poll()
if proc.returncode is not None:
    stderr = proc.stderr.read().decode()
    print('SERVER FAILED TO START:', stderr[-500:])
    sys.exit(1)

# Login
data = json.dumps({'email': 'admin@railmaintain.local', 'password': '123'}).encode()
req = urllib.request.Request('http://localhost:8000/api/auth/login', data=data, headers={'Content-Type': 'application/json'})
try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    token = result['access_token']
    print('LOGIN OK')
except Exception as e:
    print(f'LOGIN FAILED: {e}')
    proc.terminate()
    sys.exit(1)

def test(name, path):
    try:
        req = urllib.request.Request(f'http://localhost:8000/api{path}', headers={'Authorization': f'Bearer {token}'})
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        if isinstance(data, list):
            print(f'  {name}: OK ({len(data)} items)')
        else:
            print(f'  {name}: OK')
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f'  {name}: FAILED ({e.code}) {body}')
        # Check server stderr
        proc.poll()

test('GET /me', '/auth/me')
test('GET /complaints', '/complaints')
test('GET /tasks', '/tasks')
test('GET /assets', '/assets')
test('GET /teams', '/teams')
test('GET /dashboard/stats', '/dashboard/stats')
test('GET /dashboard/alerts', '/dashboard/alerts')
test('GET /audit/logs', '/audit/logs')
test('GET /inspections/pending', '/inspections/pending')

proc.terminate()
print('\nDone!')
