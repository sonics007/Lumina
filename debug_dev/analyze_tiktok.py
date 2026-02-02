
from curl_cffi import requests
import sys
import os
import logging
from urllib.parse import urljoin

# Setup paths
sys.path.append(os.getcwd())
# Also add parent dir for extractor
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from extractor import get_stream_url

# Configure logging to stdout
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)

url = "https://hglink.to/e/vuu0xy4edw1v"
print(f"Analyzing: {url}")

try:
    # 1. Get Stream URL
    link, headers = get_stream_url(url)
    print(f"Master URL: {link}")
    
    session = requests.Session(impersonate="chrome120")
    session.headers.update(headers)
    session.verify = False 
    
    # 2. Fetch Master
    r = session.get(link, timeout=20)
    print(f"Master Status: {r.status_code}")
    print(r.text[:300])
    
    # Parse for variant
    lines = r.text.split('\n')
    variant_url = None
    for line in lines:
        if line.strip() and not line.startswith('#'):
            variant_url = urljoin(link, line.strip())
            break
            
    if variant_url:
        print(f"Variant URL: {variant_url}")
        # 3. Fetch Variant
        r_var = session.get(variant_url, timeout=20)
        print(f"Variant Status: {r_var.status_code}")
        print(r_var.text[:300])
        
        # Parse for segment
        seg_url = None
        for line in r_var.text.split('\n'):
            if line.strip() and not line.startswith('#'):
                seg_url = urljoin(variant_url, line.strip())
                break
                
        if seg_url:
            print(f"Segment URL: {seg_url}")
            # 4. Analyze Segment
            r_seg = session.get(seg_url, stream=True, timeout=20)
            print(f"Segment Status: {r_seg.status_code}")
            print(f"Segment Content-Type: {r_seg.headers.get('Content-Type')}")
            print(f"Segment Size (header): {r_seg.headers.get('Content-Length')}")
            
            # Read a bit
            chunk = b""
            for c in r_seg.iter_content(chunk_size=100):
                chunk = c
                break
            print(f"First 100 bytes hex: {chunk.hex()}")
            
    else:
        print("No variant found in master.")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
