import requests
import re

URL = "https://s2.filmcdn.top/e/VnhFMzJyR1laSVU0V1A0L0JYbjNvZz09"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://s2.filmcdn.top/"
}

def analyze():
    print(f"Fetching {URL}...")
    try:
        r = requests.get(URL, headers=HEADERS, verify=False)
        print(f"Status: {r.status_code}")
        print(f"Length: {len(r.text)}")
        
        from bs4 import BeautifulSoup
        from urllib.parse import unquote
        
        # Save raw
        with open("raw_filmcdn.html", "w", encoding='utf-8') as f: f.write(r.text)

        soup = BeautifulSoup(r.text, 'html.parser')
        scripts = soup.find_all('script')
        print(f"Found {len(scripts)} scripts.")
        
        for s in scripts:
            if s.string and 'unescape' in s.string:
                print("Found unescape script!")
                # Extract the string inside unescape('')
                match = re.search(r"unescape\('([^']+)'\)", s.string)
                if match:
                    content = match.group(1)
                    decoded = unquote(content)
                    print("Decoded content length:", len(decoded))
                    with open("decoded_filmcdn.html", "w", encoding='utf-8') as f:
                        f.write(decoded)
                    print("Saved decoded_filmcdn.html")
                    # Break after first match
                    break
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
