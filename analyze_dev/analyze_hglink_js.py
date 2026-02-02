import requests
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()

def get_js():
    url = "https://hglink.to/main.js?v=1.1.3"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://hglink.to/'
    }
    print(f"Downloading {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        with open('hglink_main.js', 'w', encoding='utf-8') as f:
            f.write(r.text)
        print("Saved hglink_main.js")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_js()
