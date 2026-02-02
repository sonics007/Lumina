import requests
import re

url = "https://film-adult.top/en/5005-father-figure.html"
try:
    print(f"Fetching {url}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=15)
    html = r.text
    
    # Check all providers
    print("\n[+] Searching for ALL providers...")
    for p in ['hglink', 'filmcdn', 'myvidplay', 'dood', 'youtube']:
        matches = re.findall(f".{{0,100}}{p}.{{0,100}}", html)
        if matches:
            print(f"✅ Found provider: {p}")
            for m in matches[:3]:
                print(f"   Context: ...{m.strip()}...")
                
    # Check iframes
    print("\n[+] IFrames:")
    iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
    for i in iframes:
        print(f"   {i}")

except Exception as e:
    print(f"Error: {e}")
