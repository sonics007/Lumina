import requests

url = "http://127.0.0.1:5555/watch?url=https://cavanhabg.com/s4bp3dcmjk1y&pid=default"

print(f"Testing: {url}")
print("="*70)

try:
    r = requests.get(url, timeout=60)
    print(f"Status: {r.status_code}")
    print(f"Headers: {dict(r.headers)}")
    print(f"\nContent (first 500 chars):\n{r.text[:500]}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
