
from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import time
import os
import sys

# Configuration
BASE_URL = "https://film-adult.top/en"
# Path to data directory relative to this script
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_FILE = "film_adult_movies_en.json"
MAX_PAGES = 388 # Set to e.g. 400 to scrape everything. 50 for test.

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def get_session():
    # Use chrome110 to bypass TLS fingerprinting
    return requests.Session(impersonate="chrome110")

def scrape():
    session = get_session()
    all_movies = []
    seen_urls = set()
    
    print(f"Starting scrape of {BASE_URL}...")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Max Pages: {MAX_PAGES}\n")
    
    try:
        for page in range(1, MAX_PAGES + 1):
            url = f"{BASE_URL}/page/{page}/" if page > 1 else BASE_URL
            print(f"[{page:03d}] Scraping {url}...", end='', flush=True)
            
            try:
                r = session.get(url, headers=HEADERS, timeout=30)
                if r.status_code != 200:
                    print(f" Failed (Status {r.status_code}). Stopping.")
                    break
                    
                # Check for redirect to homepage (common infinite loop protection)
                if page > 1 and r.url.rstrip('/') == BASE_URL.rstrip('/'):
                    print(" Redirected to home. Pagination complete.")
                    break
                    
                soup = BeautifulSoup(r.text, 'html.parser')
                
                # Find movie cards using Selector found in analysis (a.poster)
                cards = soup.select('a.poster')
                
                if not cards:
                    print(" No movies found on this page.", end='')
                    # Check if pagination element exists
                    if not soup.find(id='pagination'):
                        print(" No pagination element. End of list.")
                        break
                    else:
                        print(" (Pagination exists, maybe empty page?)")
                    
                count_new = 0
                for card in cards:
                    href = card.get('href')
                    if not href: continue
                    
                    # Basic metadata extraction
                    title = "Unknown"
                    title_tag = card.find(class_='poster__title')
                    if title_tag: title = title_tag.get_text(strip=True)
                    
                    img_tag = card.find('img')
                    image = img_tag.get('src') if img_tag else ""
                    if image and not image.startswith('http'):
                         # Fix relative URLs if any
                         if image.startswith('/'): image = "https://film-adult.com" + image 
                         else: image = BASE_URL + "/" + image
                    
                    if href not in seen_urls:
                        seen_urls.add(href)
                        all_movies.append({
                            'title': title,
                            'url': href,
                            'image': image,
                            'source': 'film-adult.top',
                            'scraped_at': time.time()
                        })
                        count_new += 1
                
                print(f" +{count_new} movies. (Total: {len(all_movies)})")
                
                if count_new == 0 and page > 1:
                    print("No new movies found. Ending.")
                    break
                    
                # Be polite to the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f" Error requesting page: {e}")
                break
                
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
        
    # Save results
    if OUTPUT_DIR and not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    full_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE) if OUTPUT_DIR else OUTPUT_FILE
    
    print(f"\nSaving {len(all_movies)} movies to {full_path}...")
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(all_movies, f, indent=2, ensure_ascii=False)
        
    print("Done.")

if __name__ == "__main__":
    scrape()
