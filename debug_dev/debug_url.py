
import logging
import sys
import os

# Setup paths
sys.path.append(os.getcwd())
# Ensure logging goes to stdout
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, stream=sys.stdout, force=True)

try:
    from extractor import get_stream_url
except ImportError:
    # Try parent dir
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from extractor import get_stream_url

url = "https://hglink.to/e/vbe115wq7yj1"
print(f"Testing URL: {url}")

try:
    link, headers = get_stream_url(url)
    print(f"Result Link: {link}")
    if headers:
        print(f"Result Headers Keys: {list(headers.keys())}")
    else:
        print("Result Headers: None")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
