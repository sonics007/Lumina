
import subprocess
import time
import sys
import requests
import os

PORT = 5555
SERVER_URL = f"http://127.0.0.1:{PORT}"
TARGET_URL = "https://streamtape.com/v/7wqGq16Y8YCAk3K"

print(f"DEBUG: Spúšťam server.py na porte {PORT}...")

# Kill existing python servers on port? No, assume user stopped it or it crashed.

env = os.environ.copy()
env["PYTHONUNBUFFERED"] = "1"
env["PORT"] = str(PORT)

p = subprocess.Popen([sys.executable, 'server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

time.sleep(8) # Wait for startup

if p.poll() is not None:
    print(f"Server CRASHED immediately with code {p.returncode}")
    print(p.stdout.read())
    print(p.stderr.read())
    sys.exit()

print(f"Server beží (PID {p.pid}). Posielam request na /watch...")
watch_url = f"{SERVER_URL}/watch?url={TARGET_URL}"
print(f"GET {watch_url}")

try:
    # Use short timeout to trigger processing
    r = requests.get(watch_url, timeout=30)
    print(f"Response Status: {r.status_code}")
    print("Response Body Head:")
    print(r.text[:300])
except Exception as e:
    print(f"Client Request Error: {e}")

time.sleep(2)
if p.poll() is not None:
    print("Server CRASHED during/after request!")
    print("--- STDOUT ---")
    print(p.stdout.read())
    print("--- STDERR ---")
    print(p.stderr.read())
else:
    print("Server SURVIVED the request.")
    p.terminate()
    try:
        stdout, stderr = p.communicate(timeout=2)
        print("Server Output:")
        print(stdout[:1000])
        if stderr:
            print("Server Errors:")
            print(stderr)
    except:
        p.kill()
