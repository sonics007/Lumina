
import sys
import os
import requests
from urllib.parse import quote, unquote, urljoin
import re
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()

# Setup paths
sys.path.append(os.getcwd())
try:
    from extractor import get_stream_url
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'testing_new'))
    from extractor import get_stream_url

url = "https://auvexiug.com/e/s4bp3dcmjk1y"
PORT = 5555

print(f"--- Debugging Playback Flow for {url} ---")

# 1. Extract
print("1. Extracting stream URL...")
try:
    real_stream, headers = get_stream_url(url)
    if not real_stream:
        print("ERROR: Extraction failed (None returned).")
        sys.exit(1)
    print(f"SUCCESS: Extracted URL: {real_stream}")
    print(f"Headers: {headers}")
except Exception as e:
    print(f"ERROR: Exception during extraction: {e}")
    sys.exit(1)

# 2. Fetch Content
print("\n2. Fetching content of stream URL...")
try:
    r = requests.get(real_stream, headers=headers, verify=False, timeout=30)
    print(f"Status Code: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type')}")
    content = r.text
    print(f"Content Sample :\n{content[:500]}")
    base_url = r.url
except Exception as e:
    print(f"ERROR: Failed to fetch stream content: {e}")
    sys.exit(1)

# 3. Rewrite Logic Simulation
print("\n3. Simulating Rewrite Logic...")
try:
    new_lines = []
    uri_pattern = re.compile(r'URI="([^"]+)"')
    referer = headers.get('Referer', url)
    
    def replace_uri(match):
        full = urljoin(base_url, match.group(1))
        return f'URI="http://127.0.0.1:{PORT}/segment?url={quote(full)}&ref={quote(referer)}"'
        
    for line in content.split('\n'):
        line = line.strip()
        if not line: continue
        if line.startswith('#'):
            if 'URI="' in line:
                line = uri_pattern.sub(replace_uri, line)
            new_lines.append(line)
        else:
            full = urljoin(base_url, line)
            # Check if it looks valid
            # print(f"  -> Rewriting segment: {line[:50]}... to proxy URL")
            proxy = f"http://127.0.0.1:{PORT}/segment?url={quote(full)}&ref={quote(referer)}"
            new_lines.append(proxy)

    print("\nRewrite Result Sample (first 10 lines):")
    for l in new_lines[:10]:
        print(l)
        
except Exception as e:
    print(f"ERROR: Rewrite logic failed: {e}")

print("\n--- End Debug ---")
