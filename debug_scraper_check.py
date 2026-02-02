from curl_cffi import requests
from bs4 import BeautifulSoup
import re

url = "https://film-adult.top/en"

print(f"Fetching {url}...")
try:
    session = requests.Session(impersonate="chrome110")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    }
    r = session.get(url, headers=headers, timeout=30)
    print(f"Status: {r.status_code}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Check posters
    cards = soup.select('a.poster')
    print(f"Found {len(cards)} cards using 'a.poster'")
    
    
    if cards:
        href = cards[0].get('href')
        print(f"Checking detail: {href}")
        
        det_r = session.get(href, headers=headers)
        print(f"Detail status: {det_r.status_code}")
        
        candidates = re.findall(r'["\'](https?://[^"\']+)["\']', det_r.text)
        print(f"Regex candidates found: {len(candidates)}")
        
        PROVIDERS_KEYWORDS = ['hglink', 'haxloppd', 'myvidplay', 'hlswish', 's2.filmcdn', 'play']
        found = []
        for url in candidates:
             for key in PROVIDERS_KEYWORDS:
                 if key in url:
                     found.append(url)
                     break
                     
        print(f"Matched Streams: {len(found)}")
        for s in found[:5]:
            print(f" - {s}")

            
except Exception as e:
    print(f"Error: {e}")
