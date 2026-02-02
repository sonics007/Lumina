import requests
import re

url = "https://myvidplay.com/e/nvck4fvk16ge"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://film-adult.top/'
}

print(f"Analyzing {url}...")
try:
    r = requests.get(url, headers=headers, timeout=15)
    html = r.text
    
    print(f"Status: {r.status_code}")
    print(f"Length: {len(html)}")
    
    # Check for Packed JS
    if 'eval(function(p,a,c,k,e,d)' in html:
        print("✅ Found Packed JS!")
        # Extract packed
        packed = re.search(r"eval\(function\(p,a,c,k,e,d\).*?\.split\('\|'\)\)\)", html)
        if packed:
            print(f"Packed snippet: {packed.group(0)[:100]}...")
            
    # Check for direct m3u8
    m3u8 = re.findall(r'["\']([^"\']+\.m3u8[^"\']*)["\']', html)
    if m3u8:
        print(f"✅ Found m3u8 links: {m3u8}")
        
    # Check for JWPlayer sources
    if 'sources:' in html:
        print("✅ Found sources config")
        
    # Create file for detailed look
    with open('myvidplay_dump.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
except Exception as e:
    print(f"Error: {e}")
