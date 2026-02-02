import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://bahu.tv"
OUTPUT_FILE = "data.json"

# Headers to look like a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_page(url):
    print(f"Scraping: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        items = []
        
        # Selectors based on bahu.tv analysis
        # Looking for movie cards
        # Usually inside .movie-item or similar. 
        # Since I can't see the exact HTML, I will use generic robust finding or assumption from prev logs.
        # From logs: images/movies/main/movie_XXX.jpg
        
        # Let's try to find all links that look like /film/ or /sorozat/
        # And have an image inside
        
        # Finding the main catalog container
        # It seems they use standard bootstrap or custom grid.
        
        links = soup.find_all('a', href=True)
        for a in links:
            href = a['href']
            
            # Simple heuristic for content pages
            if href.startswith('/film/') or href.startswith('/sorozat/'):
                full_url = BASE_URL + href if href.startswith('/') else href
                
                # Check for image (poster)
                img = a.find('img')
                poster = ""
                if img:
                    poster_src = img.get('src', '') or img.get('data-src', '')
                    if poster_src:
                        poster = BASE_URL + poster_src if poster_src.startswith('/') else poster_src
                
                # Title
                # Often in an alt tag or a sibling div
                title = ""
                if img and img.get('alt'):
                    title = img['alt']
                else:
                    # Try finding a title div inside
                    t_div = a.find(class_='title') # Generic guess
                    if t_div: title = t_div.text.strip()
                    else: title = href.split('/')[-1].replace('-', ' ').title()
                
                # Filter out duplicates and utility links
                if title and "http" in full_url:
                    items.append({
                        "title": title,
                        "url": full_url,
                        "poster": poster,
                        "type": "series" if "sorozat" in href else "movie"
                    })
                    
        return items
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def main():
    all_data = []
    
    # 1. Scrape Movies (Filmek) - First 3 pages
    for i in range(1, 4):
        page_url = f"{BASE_URL}/filmek?Movie_page={i}" if i > 1 else f"{BASE_URL}/filmek"
        items = scrape_page(page_url)
        print(f"Found {len(items)} items on page {i}")
        all_data.extend(items)
        time.sleep(1) # Be nice
        
    # 2. Scrape Series (Sorozatok) - First 3 pages
    for i in range(1, 4):
        page_url = f"{BASE_URL}/sorozatok?Serial_page={i}" if i > 1 else f"{BASE_URL}/sorozatok"
        items = scrape_page(page_url)
        print(f"Found {len(items)} items on page {i}")
        all_data.extend(items)
        time.sleep(1)

    # Deduplicate by URL
    unique_data = []
    seen = set()
    for item in all_data:
        if item['url'] not in seen:
            unique_data.append(item)
            seen.add(item['url'])
            
    print(f"Total unique items: {len(unique_data)}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, indent=2, ensure_ascii=False)
        
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
