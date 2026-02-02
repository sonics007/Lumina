import requests
from urllib.parse import urljoin

base_url = "https://film-adult.top/en/top100.html"
headers = {'User-Agent': 'Mozilla/5.0'}

js_urls = [
    "https://film-adult.top/en/templates/HDFilmAdult4K/js/libs.js",
    "https://film-adult.top/en/engine/classes/min/index.php?g=general&v=927fd", # jQuery + ...
    "https://film-adult.top/en/engine/classes/min/index.php?f=engine/classes/js/jqueryui.js,engine/classes/js/dle_js.js,templates/HDFilmAdult4K/custom/assets/libs.js,engine/classes/js/lazyload.js&v=927fd"
]

print("Scanning JS files for 'data-page' logic...")

for url in js_urls:
    print(f"Fetching {url}...")
    try:
        content = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).text
        if 'data-page' in content:
            print(f"  [!!!] FOUND 'data-page' in {url}")
            idx = content.find('data-page')
            snippet = content[max(0, idx-200):min(len(content), idx+400)]
            print(f"  Snippet:\n{snippet}\n")
            
        if 'ajax' in content and 'page' in content:
             # Look for AJAX calls related to page
             idx = content.find('ajax')
             # Simplistic scan
             pass
    except Exception as e:
        print(f"Error: {e}")
