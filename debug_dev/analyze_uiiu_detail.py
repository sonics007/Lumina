
from curl_cffi import requests
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://uiiumovie.com/wet-hot-indian-wedding-2025/"
print(f"Fetching {url}")

session = requests.Session(impersonate="chrome120")
try:
    r = session.get(url, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    print("--- EARNVID SEARCH ---")
    found = False
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        
        # Check explicit
        if 'earnvid' in href.lower() or 'earnvid' in text.lower():
            print(f"MATCH: Text='{text}', Href='{href}'")
            found = True
            
    if not found:
        print("No explicit 'earnvid' links found.")
        print("Dumping all external links/player links:")
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True)
            if 'uiiumovie.com' not in href and not href.startswith('/') and not href.startswith('#'):
                 print(f"External: {text} -> {href}")
                 
except Exception as e:
    print(f"Error: {e}")
