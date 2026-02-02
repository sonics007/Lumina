
from curl_cffi import requests

base = "https://znOMC6AzQ2DC.solutionportal.site/kyw0p84c/hls3/01/11554/vbe115wq7yj1_,l,n,.urlset/"
url = base + "index-f1-v1-a1.txt"
referer = "https://haxloppd.com/e/vbe115wq7yj1"
session = requests.Session(impersonate="chrome120")

print("Checking variant playlist content via curl_cffi stream=True")
try:
    headers = {"Referer": referer, "User-Agent": "Mozilla/5.0 ..."}
    r = session.get(url, headers=headers, verify=False, timeout=10, stream=True)
    print(f"Status: {r.status_code}")
    
    content = b""
    for chunk in r.iter_content(chunk_size=1024):
        if chunk: content += chunk
            
    text = content.decode('utf-8')
    print(f"Content-Length: {len(text)}")
    print(f"Sample:\n{text[:200]}")
    
except Exception as e:
    print(f"Error: {e}")
