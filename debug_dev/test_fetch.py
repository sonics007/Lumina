
import requests
import time

url = "https://in1rhjc5cqhz.mindfullivingguide.space/qEivq6d5YqUZ/hls3/01/09323/s4bp3dcmjk1y_,l,n,.urlset/master.txt"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://auvexiug.com/',
    'Origin': 'https://auvexiug.com',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive'
}

print(f"Fetching {url}...")
try:
    s = requests.Session()
    r = s.get(url, headers=headers, verify=False, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Headers: {r.headers}")
    print(f"Content:\n{r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
