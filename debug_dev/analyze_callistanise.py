
from curl_cffi import requests
import re
import sys 

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

url = "https://callistanise.com/file/vmbps7u3ghd0"
print(f"Fetching {url}")

session = requests.Session(impersonate="chrome120")
try:
    r = session.get(url, timeout=15, allow_redirects=True)
    print(f"Status: {r.status_code}")
    print(f"Final URL: {r.url}")
    
    html = r.text
    print("\n--- HEAD (2000 chars) ---")
    print(html[:2000])
    
    keywords = ['voe', 'mixdrop', 'streamtape', 'filemoon', 'hls', 'm3u8', 'packing', 'sources', 'jwplayer', 'clrapp', 'player']
    found = [k for k in keywords if k in html.lower()]
    print("\nKeywords found:", found)
    
    # Check for Packed JS
    if "eval(function(p,a,c,k,e,d)" in html:
        print("Packed JS DETECTED!")
        
except Exception as e:
    print(f"Error: {e}")
