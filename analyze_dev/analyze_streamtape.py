
from curl_cffi import requests
import re

url = "https://streamtape.com/v/7wqGq16Y8YCAk3K" 

print(f"Fetching {url}")
session = requests.Session(impersonate="chrome120")
try:
    r = session.get(url, timeout=15)
    print(f"Status: {r.status_code}")
    
    # Debug snippet
    # print(r.text[:2000])
    
    # Try Regex
    # Pattern: document.getElementById('ideoolink').innerHTML = '/streamtape.com/get_video?id=...'
    # Or similar variable names.
    
    # Generic pattern: .innerHTML = '...'
    # And usually combined with some concatenation if obfuscated.
    
    # Simple check
    pattern = r"document\.getElementById\('([a-zA-Z0-9_]+)'\)\.innerHTML\s*=\s*['\"]([^'\"]+)['\"]"
    matches = re.findall(pattern, r.text)
    
    found = False
    for mid, content in matches:
        if "get_video" in content or "stream" in content:
            print(f"Found candidate: ID={mid}, CONTENT={content}")
            full_url = "https:" + content if content.startswith('//') else "https://streamtape.com" + content
            print(f"Full URL: {full_url}")
            found = True
            
    if not found:
        print("No exact match found.")
        
    idx = r.text.find('norobotlink')
    if idx != -1:
        print("\nCONTEXT for norobotlink:")
        print(r.text[idx-100:idx+400]) 
        
except Exception as e:
    print(f"Error: {e}")
