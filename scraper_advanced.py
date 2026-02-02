import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import re
import time
import datetime

# Add parent dir to path to import providers_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from providers_config import PROVIDERS
except ImportError:
    PROVIDERS = {'s2.filmcdn.top': {}, 'hlswish.com': {}, 'hglink.to': {}, 'haxloppd.com': {}}
    print("Warning: Could not import PROVIDERS, using fallback.")

CONFIG_FILE = "scraper_config.json"
DB_FILE = "movies_db.json"
UNKNOWN_FILE = "nezname_providery.txt"
EXTRA_PROVIDERS_FILE = "filmy_dalsie_providery.txt"

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return [] if filename == DB_FILE else {}
    return [] if filename == DB_FILE else {}

def save_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def append_to_file(filename, text):
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(text + "\n")

def is_provider_known(url):
    for domain in PROVIDERS:
        if domain in url:
            return domain
    return None

def scrape_single_url(target_url, db, existing_urls):
    print(f"Scraping: {target_url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    added_count = 0
    
    # Build set of existing movie titles for duplicate check
    existing_titles = {m.get('title', '').lower().strip() for m in db if m.get('title')}
    
    try:
        r = requests.get(target_url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Try multiple selectors
        links = soup.find_all('a', class_='popular')
        
        # If no 'popular' links found, try 'poster' (for top100 page)
        if not links:
            print("  [i] No 'a.popular' found, trying 'a.poster'...")
            links = soup.find_all('a', class_='poster')
            
        # If still no links, try regex pattern (most reliable for top100)
        if not links:
            print("  [i] No 'a.poster' found, trying regex pattern...")
            pattern = r'href="(https://film-adult\.top/en/\d+-[^"]+\.html)"'
            hrefs = list(set(re.findall(pattern, r.text)))
            # Convert hrefs to fake link objects with href attribute
            class FakeLink:
                def __init__(self, href):
                    self.href_val = href
                def get(self, attr):
                    return self.href_val if attr == 'href' else None
                def find(self, *args, **kwargs):
                    return None
            links = [FakeLink(href) for href in hrefs]
            print(f"  [i] Found {len(links)} links via regex")
        
        if not links:
            print("  [!] No links found on page (check selectors)")
            return 0
        
        print(f"  [DEBUG] Total links found: {len(links)}")
        skipped_url = 0
        skipped_title = 0
            
        for l in links:
            href = l.get('href')
            if not href: continue
            
            # Make href absolute if needed
            if not href.startswith('http'):
                href = 'https://film-adult.top' + href
             
            # Check URL duplication first (fast check)
            if href in existing_urls:
                skipped_url += 1
                continue
                
            # Get title - try multiple methods
            title_div = l.find(class_='popular__title')
            if title_div:
                title = title_div.get_text(strip=True)
            else:
                # For a.poster links, title is in h3
                h3 = l.find('h3')
                if h3:
                    title = h3.get_text(strip=True)
                else:
                    # Try getting text from link itself or from href
                    title = l.get_text(strip=True) or href.split('/')[-1].replace('.html', '').replace('-', ' ').title()
                    # Clean up title (remove year, quality info)
                    title = re.sub(r'\s+\d{4}\s+.*', '', title).strip()
                    if not title or len(title) < 3:
                        title = "Unknown"
            
            # Check title duplication (user request: skip if title already exists)
            if title.lower().strip() in existing_titles:
                skipped_title += 1
                print(f"  [i] Skipping '{title}' - already in database")
                continue
            
            print(f"  Processing: {title}")
            
            # Get Image
            img_tag = l.find('img')
            img = img_tag.get('src') if img_tag else ""
            if img and not img.startswith('http'):
                 img = "https://film-adult.top" + img 
            
            # DEEP SCRAPE
            try:
                r_det = requests.get(href, headers=headers, timeout=10)
                soup_det = BeautifulSoup(r_det.text, 'html.parser')
                
                # Extract Description
                description = ""
                meta_desc = soup_det.find("meta", property="og:description")
                if meta_desc:
                    description = meta_desc.get("content", "")
                else:
                    desc_div = soup_det.find(class_='description') or soup_det.find(class_='text') or soup_det.find('p')
                    if desc_div:
                        description = desc_div.get_text(strip=True)
                
                # Extract Links (Candidates)
                candidates = re.findall(r'["\'](https?://[^"\']+)["\']', r_det.text)
                
                unique_urls = set()
                known_sources = []
                unknown_sources = []
                
                for url in candidates:
                    if url in unique_urls: continue
                    if 'w3.org' in url or 'schema.org' in url: continue
                    if url == href or url == img: continue
                    if url.endswith(('.jpg', '.png', '.css', '.js')): continue
                    
                    if 'filmcdn' in url: continue # IGNORE FILMCDN
                    
                    looks_like_video = '/e/' in url or 'embed' in url or 'video' in url or any(p in url for p in PROVIDERS)
                    if not looks_like_video: continue
                    
                    unique_urls.add(url)
                    
                    provider = is_provider_known(url)
                    if provider:
                        known_sources.append({'provider': provider, 'url': url})
                    else:
                        unknown_sources.append(url)
                
                if known_sources:
                    # Save to DB
                    movie_data = {
                        "title": title,
                        "url": href,
                        "image": img,
                        "description": description,
                        "streams": known_sources
                    }
                    db.append(movie_data)
                    existing_urls.add(href)
                    existing_titles.add(title.lower().strip())  # Add to title set too
                    added_count += 1
                    print(f"    [+] Added with {len(known_sources)} streams.")
                    
                    if len(known_sources) > 1 or len(unknown_sources) > 0:
                        extra_text = f"Movie: {title} (Saved)\n"
                        extra_text += "Known Sources:\n" + "\n".join([f" - {s['url']}" for s in known_sources])
                        if unknown_sources:
                             extra_text += "\nUnknown Sources:\n" + "\n".join([f" - {u}" for u in unknown_sources])
                        extra_text += "\n" + "-"*30
                        append_to_file(EXTRA_PROVIDERS_FILE, extra_text)
                else:
                    if unknown_sources:
                        print(f"    [!] Only unknown sources.")
                        unk_text = f"Movie: {title}\nLink: {href}\nSources:\n" + "\n".join([f" - {u}" for u in unknown_sources])
                        unk_text += "\n" + "-"*30
                        append_to_file(UNKNOWN_FILE, unk_text)

            except Exception as e:
                print(f"    Error detail: {e}")
                
    except Exception as e:
        print(f"  Error fetching page {target_url}: {e}")
    
    if skipped_url > 0 or skipped_title > 0:
        print(f"  [i] Skipped {skipped_url} duplicate URLs, {skipped_title} duplicate titles")
        
    return added_count

def main():
    print("Starting Multi-Source Scraper...")
    
    # Load DB
    db = load_json(DB_FILE)
    existing_urls = {m['url'] for m in db} if db else set()
    print(f"Loaded {len(db)} existing movies.")
    
    # Load Config
    config = load_json(CONFIG_FILE)
    if not config or "urls" not in config:
        print("Config file missing or invalid. Using default.")
        config = {"urls": [{"url": "https://film-adult.top/en/movies/", "name": "Default", "last_scraped": "Never"}]}
    
    # Clear logs
    open(UNKNOWN_FILE, 'w').close()
    open(EXTRA_PROVIDERS_FILE, 'w').close()
    
    total_new = 0
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for site in config['urls']:
        url = site.get('url')
        name = site.get('name', 'Unknown')
        print(f"\n--- Processing Source: {name} ---")
        
        count = scrape_single_url(url, db, existing_urls)
        
        print(f"  -> Added {count} new movies.")
        total_new += count
        
        # Update timestamp
        site['last_scraped'] = now_str
        
        # Save DB continuously (after each site)
        save_json(DB_FILE, db)
        # Save Config continuously
        save_json(CONFIG_FILE, config)

    print(f"\nDone. Total new movies added: {total_new}")

if __name__ == "__main__":
    main()
