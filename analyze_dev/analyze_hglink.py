import requests
import logging

logging.basicConfig(level=logging.INFO)

def analyze():
    url = "https://hglink.to/e/0m1gvo5g66i8"
    s = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://hglink.to/',
        'Origin': 'https://hglink.to'
    }
    print(f"Testing Session with Headers on {url}...")
    try:
        r = s.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        if "main.js" not in r.text and len(r.text) > 1000:
             print("SUCCESS: Session/Origin got full page!")
             with open('hglink_session.html', 'w', encoding='utf-8') as f: f.write(r.text)
        else:
             print("Session got loading page.")
             # Check cookies
             print("Cookies:", s.cookies.get_dict())
    except Exception as e: print(e)

    # 2. Test API endpoint (common pattern)
    api_url = f"https://hglink.to/api/source/{video_id}"
    print(f"Testing API POST {api_url}...")
    try:
        r = requests.post(api_url, headers={'User-Agent': 'Mozilla/5.0...'}, verify=False)
        print(f"API Status: {r.status_code}")
        print(r.text[:200])
    except Exception as e: print(e)

if __name__ == "__main__":
    analyze()
