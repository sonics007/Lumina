import requests
from bs4 import BeautifulSoup
import re
import os
import sys

# Add parent dir to path to import providers_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from providers_config import PROVIDERS
except ImportError:
    # Fallback ak by sa spustal inak
    PROVIDERS = {'s2.filmcdn.top': {}, 'hlswish.com': {}, 'hglink.to': {}}
    print("Warning: Could not import PROVIDERS, using fallback.")

BASE_URL = "https://film-adult.top/en/movies/"
OUTPUT_FILE = "../channels.txt"
NOT_WORKING_FILE = "../not_working_providers.txt"

def scrape_movies():
    print(f"Scraping {BASE_URL}...")
    headers={'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.get(BASE_URL, headers=headers)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', class_='popular')
        
        movies = []
        unknown_providers = []
        
        # Restore Test Link
        movies.append({
            'title': 'Test Movie (HLSWish)',
            'url': 'https://hlswish.com/lkxwefnpg3ex',
            'image': ''
        })

        for l in links:
            href = l.get('href')
            if not href: continue
            
            title_div = l.find(class_='popular__title')
            title = title_div.get_text(strip=True) if title_div else "Unknown"
            
            img_tag = l.find('img')
            img = img_tag.get('src') if img_tag else ""
            if img and not img.startswith('http'):
                 img = "https://film-adult.top" + img 
            
            # DEEP SCRAPE
            try:
                print(f"  Fetching: {title}")
                r_det = requests.get(href, headers=headers, timeout=5)
                
                # 1. Regex for all embed-like URLs (usually contain /e/ or known domains)
                # Capture everything inside quotes assigned to src or href
                # Looking for patterns like: s2.src = "https://..."
                
                candidates = re.findall(r'["\'](https?://[^"\']+)["\']', r_det.text)
                
                # Filter distinct URLs that look like embeds
                seen_urls = set()
                
                for url in candidates:
                    if url in seen_urls: continue
                    
                    # Check if it is a known provider
                    is_known = False
                    domain = url.split('/')[2]
                    
                    # Check if domain matches any key in PROVIDERS
                    matched_provider = None
                    for p_key in PROVIDERS:
                        if p_key in domain:
                            matched_provider = p_key
                            break
                    
                    # Heuristic: Embed urls often have /e/ in path or are known providers
                    if matched_provider:
                        # It is a known provider!
                        if '/e/' in url or 'hlswish' in url or 'play' in url: # Basic filter to avoid styles/scripts
                            seen_urls.add(url)
                            entry_title =f"{title} ({matched_provider})"
                            movies.append({
                                'title': entry_title,
                                'url': url,
                                'image': img
                            })
                            print(f"    + Found known: {url}")
                    
                    elif '/e/' in url and 'film-adult' not in url:
                        # Unknown provider with /e/ pattern
                        if url not in unknown_providers:
                            unknown_providers.append(url)
                            print(f"    ! Found unknown: {url}")
                            seen_urls.add(url)

            except Exception as e:
                print(f"    Error scraping detail: {e}")

        # Save Channels
        path = os.path.join(os.path.dirname(__file__), OUTPUT_FILE)
        with open(path, 'w', encoding='utf-8') as f:
            for m in movies:
                f.write(f"{m['url']}|{m['title']}|{m['image']}\n")
        print(f"Saved {len(movies)} channels to {OUTPUT_FILE}")

        # Save Unknown
        if unknown_providers:
            upath = os.path.join(os.path.dirname(__file__), NOT_WORKING_FILE)
            with open(upath, 'w', encoding='utf-8') as f:
                for u in unknown_providers:
                    f.write(f"{u}\n")
            print(f"Saved {len(unknown_providers)} unknown provider links to {NOT_WORKING_FILE}")

    except Exception as e:
        print(f"Global Error: {e}")

if __name__ == "__main__":
    scrape_movies()
