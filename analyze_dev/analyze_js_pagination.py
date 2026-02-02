import requests
import re
from urllib.parse import urljoin

base_url = "https://film-adult.top/en/top100.html"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}

print(f"Fetching {base_url}...")
try:
    r = requests.get(base_url, headers=headers, timeout=15)
    html = r.text
    
    # 1. Hľadať inline JS pre data-page
    print("\n[1] Searching for 'data-page' logic in HTML...")
    # Hľadáme napr. $(document).on('click', '[data-page]'... alebo podobne
    if 'data-page' in html:
        print("Found 'data-page' in HTML. Context:")
        # Simple context extraction
        match = re.search(r'(.{0,100}data-page.{0,300})', html)
        if match: print(match.group(1))

    # 2. Extract script src files
    print("\n[2] Extracting external JS files...")
    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
    
    js_files = []
    for s in scripts:
        full_url = urljoin(base_url, s)
        print(f"  - {full_url}")
        js_files.append(full_url)
        
    # 3. Analyze specific JS files for "page", "ajax", "pagination"
    print("\n[3] Analyzing JS files for pagination logic...")
    for js_url in js_files:
        if 'jquery' in js_url or 'bootstrap' in js_url: # Skip libraries usually
            continue
            
        try:
            print(f"  Fetching {js_url}...")
            js_content = requests.get(js_url, headers=headers, timeout=10).text
            
            # Look for pagination keywords
            keywords = ['data-page', 'pagination', 'ajax', 'post', 'GET', 'top100']
            found = False
            for kw in keywords:
                if kw in js_content.lower():
                    found = True
                    # Print context
                    loc = js_content.lower().find(kw)
                    print(f"    Match '{kw}': ...{js_content[loc:loc+100]}...")
            
            if found:
                print(f"    => Suspicious file: {js_url}")
                
        except Exception as e:
            print(f"    Error fetching JS: {e}")

except Exception as e:
    print(f"Error: {e}")
