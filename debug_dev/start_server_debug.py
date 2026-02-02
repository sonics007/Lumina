
import subprocess
import time
import sys
import os

print(f"DEBUG: Spúšťam server.py z {os.getcwd()}...")
try:
    # Use unbuffered output to catch prints
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    p = subprocess.Popen([sys.executable, 'server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    
    # Wait a bit
    time.sleep(5)
    
    if p.poll() is not None:
        print(f"Server CRASHED with code {p.returncode}")
        stdout, stderr = p.communicate()
        print("--- STDOUT ---")
        print(stdout)
        print("--- STDERR ---")
        print(stderr)
    else:
        print(f"Server RUNNING (PID: {p.pid})")
        p.terminate()
        try:
            stdout, stderr = p.communicate(timeout=2)
        except:
            p.kill()
            stdout, stderr = p.communicate()
            
        print("--- STDOUT (Partial) ---")
        print(stdout[:1000])
        print("--- STDERR (Partial) ---")
        print(stderr[:1000])

except Exception as e:
    print(f"Chyba debug skriptu: {e}")
