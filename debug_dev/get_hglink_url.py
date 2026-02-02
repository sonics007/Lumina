import requests
import re
import logging

logging.basicConfig(level=logging.INFO)

def get_embed_url():
    url = "https://film-adult.top/en/8051-secretaries-in-heat-3.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print(f"Fetching {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        # Look for iframes
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', r.text)
        
        print("Found iframes:")
        hglink_url = None
        for iframe in iframes:
            print(f" - {iframe}")
            if "hglink" in iframe or "highload" in iframe:
                hglink_url = iframe
        
        if hglink_url:
            print(f"\nTarget HGLink URL: {hglink_url}")
            return hglink_url
        else:
            print("\nWARNING: HGLink iframe not found. Checking for other providers...")
            
    except Exception as e:
        print(f"Error: {e}")
        
    return None

if __name__ == "__main__":
    get_embed_url()
