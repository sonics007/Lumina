
import sys
import os

# Add parent dir to path to import extractor
sys.path.append(os.getcwd())

try:
    from extractor import get_stream_url
except ImportError:
    print("Error importing extractor. Make sure you run this from the project root.")
    sys.exit(1)

import requests
from curl_cffi import requests as c_requests

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

url = "https://callistanise.com/file/vmbps7u3ghd0"

print(f"Testujem extrakciu pre: {url}")
print("-" * 50)

try:
    # Use extractor logic
    final_url, headers = get_stream_url(url)
    
    if final_url:
        print(f"SUCCESS! Extracted URL: {final_url}")
        print(f"Headers: {headers}")
        
        print("-" * 50)
        print("Sťahujem playlist (M3U8)...")
        
        # Use curl_cffi for request (as server does)
        s = c_requests.Session(impersonate="chrome120")
        r = s.get(final_url, headers=headers, timeout=15)
        
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            print("Playlist Content (First 500 chars):")
            print(r.text[:500])
        else:
            print(f"Failed to fetch content: {r.text[:200]}")
            
    else:
        print("FAILED: Extractor returned None.")

except Exception as e:
    print(f"CRITICAL ERROR during test: {e}")
    import traceback
    traceback.print_exc()
