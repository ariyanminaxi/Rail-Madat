"""Simple API test - no subprocess cleanup."""
import os, sys, time, subprocess, urllib.request, json

os.chdir(os.path.dirname(__file__))

# Start server in background (detached)
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8004'],
    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
)
time.sleep(4)

# Login
data = json.dumps({'email': 'admin@railmaintain.local', 'password': '123'}).encode()
req = urllib.request.Request('http://localhost:8004/api/auth/login', data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())['access_token']
print('LOGIN OK')

def test(name, path):
    try:
        req = urllib.request.Request(f'http://localhost:8004/api{path}', headers={'Authorization': f'Bearer {token}'})
        resp = urllib.request.urlopen(req)
        d = json.loads(resp.read())
        n = len(d) if isinstance(d, list) else 'OK'
        print(f'  {name}: {n}')
    except urllib.error.HTTPError as e:
        print(f'  {name}: FAIL {e.code}')

test('me', '/auth/me')
test('complaints', '/complaints')
test('tasks', '/tasks')
test('assets', '/assets')
test('teams', '/teams')
test('stats', '/dashboard/stats')
test('alerts', '/dashboard/alerts')
test('audit', '/audit/logs')

print('\nDone!')
# Just kill, don't wait
proc.kill()
