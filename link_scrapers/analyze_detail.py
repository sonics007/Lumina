import requests
from bs4 import BeautifulSoup
import re

URL = "https://film-adult.top/en/6155-machine-gunner.html"

def analyze():
    print(f"Fetching {URL}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(URL, headers=headers)
    html = r.text
    
    print(f"Status: {r.status_code}")
    print(f"Length: {len(html)}")
    
    # 1. Hľadáme iframe
    iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
    print(f"Iframes found: {len(iframes)}")
    for i in iframes:
        print(f" - {i}")

    # 2. Hľadáme 'embed'
    if 'embed' in html:
        print("Keyword 'embed' found in HTML.")
        
    # Kontext pre filmcdn
    print("\n--- FILMCDN CONTEXT ---")
    matches = re.finditer(r'.{0,100}filmcdn.{0,100}', html)
    for m in matches:
        print(m.group(0))

    print("\n--- TRAILER CONTEXT ---")
    matches = re.finditer(r'.{0,100}trailer.{0,100}', html)
    for m in matches:
        print(m.group(0))
        
    # Uložíme HTML pre manuálnu kontrolu (prvých 100 riadkov)
    with open("debug_detail.html", "w", encoding='utf-8') as f:
        f.write(html)
    print("Saved debug_detail.html")

if __name__ == "__main__":
    analyze()
