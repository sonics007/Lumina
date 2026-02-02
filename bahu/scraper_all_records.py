import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging
from datetime import datetime

import client

# Configuration
BASE_URL = "https://www.bahu.tv"
OUTPUT_FILE = "all_records.json"
LOG_FILE = "scraper_all.log"

# Map of Categories
CATEGORIES = {
    "Akció": 1,
    "Animáció": 21,
    "Családi": 3,
    "Dokumentum": 24,
    "Dráma": 4,
    "Fantázia": 22,
    "Háborús": 23,
    "Horror": 6,
    "Kaland": 7,
    "Krimi": 9,
    "Misztikus": 10,
    "Rajzfilm": 12,
    "Romantikus": 14,
    "Sci-Fi": 15, 
    "Sport": 25,
    "Thriller": 17,
    "Történelmi": 18,
    "Vígjáték": 19,
    "Western": 20,
    "Valóság show": 13,
    "Tehetségkutató": 26
}

COLLECTIONS = [
    {"name": "Legnézettebb Filmek", "url": "https://www.bahu.tv/filmek/legnezettebb-filmek", "type": "filmek"},
    {"name": "Jelenleg Követett Filmek", "url": "https://www.bahu.tv/filmek/jelenleg-kovetett-filmek", "type": "filmek"},
    {"name": "Legértékeltebb Filmek", "url": "https://www.bahu.tv/filmek/legertekeltebb-filmek", "type": "filmek"},
    {"name": "IMDb Top Filmek", "url": "https://www.bahu.tv/filmek/imdb-toplista", "type": "filmek"},
    {"name": "Oscar Nyertesek", "url": "https://www.bahu.tv/filmek/oscar-winner", "type": "filmek"},
]

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Global list to store ALL records (including duplicates)
ALL_RECORDS = []
TOTAL_FOUND = 0

def scrape_category(cat_name, cat_id, page_type="filmek", max_pages=2, url_override=None):
    global ALL_RECORDS, TOTAL_FOUND
    
    logging.info(f"--- Scraping: {cat_name} ({page_type}) ---")
    
    first_page_urls = set()
    
    for i in range(1, max_pages + 1):
        params = {}
        
        if url_override:
            url = url_override
            if page_type == "filmek":
                params["Movie_page"] = i
            else:
                params["Serial_page"] = i
        else:
            params = {
                "category": cat_id,
                "sort": "id DESC" 
            }
            if page_type == "filmek":
                url = f"{BASE_URL}/filmek"
                params["Movie_page"] = i
            else:
                url = f"{BASE_URL}/sorozatok"
                params["Serial_page"] = i
            
        logging.info(f"Page {i}: {url} with params {params}")
        
        try:
            r = client.CLIENT.session.get(url, params=params)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            items = soup.select('li.item') 
            
            if not items:
                logging.info("  No items found on this page (Empty HTML). Stopping.")
                break

            # Loop Detection
            first_item_link = items[0].find('a', class_='movies-link')
            if first_item_link:
                check_href = first_item_link.get('href', '')
                if i == 1:
                    first_page_urls.add(check_href)
                elif i > 1 and check_href in first_page_urls:
                    logging.info("  Loop detected! Website redirected to Page 1. Stopping category.")
                    break
            
            for item_node in items:
                a_link = item_node.find('a', class_='movies-link')
                if not a_link: continue
                
                href = a_link.get('href', '')
                title = a_link.get('title', '')
                
                img = item_node.find('img')
                poster = ""
                if img:
                    poster_src = img.get('src', '')
                    if not title: title = img.get('alt', '')
                    if poster_src:
                        poster = BASE_URL + poster_src if poster_src.startswith('/') else poster_src

                if '/film/' in href or '/sorozat/' in href:
                    if href.startswith('http'):
                        clean_url = href.split('?')[0]
                    else:
                        clean_url = (BASE_URL + href if href.startswith('/') else '/' + href).split('?')[0]
                        clean_url = clean_url.replace(BASE_URL + BASE_URL, BASE_URL)
                    
                    if not title:
                         h6 = item_node.find('h6')
                         if h6: title = h6.text.strip()

                    if title:
                        # SAVE EVERYTHING - NO DUPLICATE CHECK!
                        item_data = {
                            "title": title,
                            "url": clean_url,
                            "poster": poster,
                            "category": cat_name, 
                            "type": "series" if "sorozat" in href else "movie",
                            "added_at": datetime.now().isoformat(),
                            "page": i
                        }
                        
                        ALL_RECORDS.append(item_data)
                        TOTAL_FOUND += 1
                        
                        if TOTAL_FOUND % 100 == 0:
                            logging.info(f"  Progress: {TOTAL_FOUND} records collected")
                        
        except Exception as e:
            logging.error(f"Error: {e}")

def save_all_records():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(ALL_RECORDS, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved {len(ALL_RECORDS)} records to {OUTPUT_FILE}")

if __name__ == "__main__":
    if not client.CLIENT.login():
        print("Login failed!")
        exit()
        
    start_time = time.time()
        
    # 1. Scrape Collections
    logging.info(">>> SCRAPING COLLECTIONS <<<")
    for col in COLLECTIONS:
        scrape_category(col['name'], "", col['type'], max_pages=5, url_override=col['url'])
        
    # 2. Scrape Categories
    logging.info(">>> SCRAPING CATEGORIES <<<")
    for name, cid in CATEGORIES.items():
        scrape_category(name, cid, "filmek", max_pages=1000) 
        
    end_time = time.time()
    duration = end_time - start_time
    
    # Save all records
    save_all_records()
    
    # Count unique URLs
    unique_urls = set([r['url'] for r in ALL_RECORDS])
    
    summary = f"""
========================================
SCRAPING COMPLETE in {duration:.2f} seconds
========================================
TOTAL RECORDS FOUND:          {len(ALL_RECORDS)}
UNIQUE URLs:                  {len(unique_urls)}
DUPLICATE RECORDS:            {len(ALL_RECORDS) - len(unique_urls)}
========================================
"""
    print(summary)
    logging.info(summary)
    
    with open("summary_all.txt", "w", encoding="utf-8") as f:
        f.write(summary)
