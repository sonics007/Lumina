"""
Bahu.tv Series Scraper
Scrapes series from bahu.tv
"""
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
DATA_FILE = "series_data.json"
LOG_FILE = "series_scraper.log"

# Series Collections
COLLECTIONS = [
    {"name": "Legnézettebb Sorozatok", "url": "https://www.bahu.tv/sorozatok/legnezettebb-sorozatok", "type": "sorozatok"},
    {"name": "Jelenleg Követett Sorozatok", "url": "https://www.bahu.tv/sorozatok/jelenleg-kovetett-sorozatok", "type": "sorozatok"},
    {"name": "Legértékeltebb Sorozatok", "url": "https://www.bahu.tv/sorozatok/legertekeltebb-sorozatok", "type": "sorozatok"},
    {"name": "IMDb Top Sorozatok", "url": "https://www.bahu.tv/sorozatok/imdb-toplista", "type": "sorozatok"},
    {"name": "Golden Globe Sorozatok", "url": "https://www.bahu.tv/sorozatok/golden-globe-winner", "type": "sorozatok"},
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

def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_db(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def scrape_series_page(url, category_name):
    """Scrape a single page of series"""
    try:
        r = client.CLIENT.session.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        series_list = []
        
        # Find all series items
        items = soup.find_all('div', class_='movie-item')
        
        for item in items:
            try:
                # Get series link
                link_tag = item.find('a', href=True)
                if not link_tag:
                    continue
                
                series_url = link_tag['href']
                if not series_url.startswith('http'):
                    series_url = BASE_URL + series_url
                
                # Get title
                title_tag = item.find('div', class_='movie-title') or item.find('h3')
                title = title_tag.text.strip() if title_tag else "Unknown"
                
                # Get poster
                img_tag = item.find('img')
                poster = img_tag['src'] if img_tag and 'src' in img_tag.attrs else ""
                if poster and not poster.startswith('http'):
                    poster = BASE_URL + poster
                
                series_list.append({
                    'title': title,
                    'url': series_url,
                    'poster': poster,
                    'category': category_name,
                    'type': 'series',
                    'added_at': datetime.now().isoformat()
                })
                
            except Exception as e:
                logging.error(f"Error parsing series item: {e}")
                continue
        
        return series_list
        
    except Exception as e:
        logging.error(f"Error scraping page {url}: {e}")
        return []

def scrape_collection(collection):
    """Scrape all pages of a collection"""
    logging.info(f"Scraping collection: {collection['name']}")
    
    all_series = []
    page = 1
    max_pages = 5  # Limit to first 5 pages per collection
    
    while page <= max_pages:
        url = f"{collection['url']}?page={page}"
        logging.info(f"  Page {page}: {url}")
        
        series_list = scrape_series_page(url, collection['name'])
        
        if not series_list:
            logging.info(f"  No more series found, stopping at page {page}")
            break
        
        all_series.extend(series_list)
        logging.info(f"  Found {len(series_list)} series on page {page}")
        
        page += 1
        time.sleep(1)  # Be nice to the server
    
    return all_series

def main():
    logging.info("="*60)
    logging.info("Bahu.tv Series Scraper Started")
    logging.info("="*60)
    
    # Login first
    if not client.CLIENT.login():
        logging.error("Login failed! Exiting.")
        return
    
    # Load existing database
    db = load_db()
    existing_urls = set([s['url'] for s in db])
    
    total_found = 0
    total_added = 0
    total_exists = 0
    
    # Scrape all collections
    for collection in COLLECTIONS:
        series_list = scrape_collection(collection)
        
        for series in series_list:
            total_found += 1
            
            if series['url'] in existing_urls:
                total_exists += 1
            else:
                db.append(series)
                existing_urls.add(series['url'])
                total_added += 1
                logging.info(f"  ✓ Added: {series['title']}")
    
    # Save database
    save_db(db)
    
    # Summary
    logging.info("="*60)
    logging.info("SCRAPING COMPLETE")
    logging.info("="*60)
    logging.info(f"Total Found: {total_found}")
    logging.info(f"Total Added: {total_added}")
    logging.info(f"Total Exists: {total_exists}")
    logging.info(f"Total in DB: {len(db)}")
    logging.info("="*60)
    
    # Save summary
    with open('series_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f"Scraping completed at: {datetime.now()}\n")
        f.write(f"Total Found: {total_found}\n")
        f.write(f"Total Added: {total_added}\n")
        f.write(f"Total Exists: {total_exists}\n")
        f.write(f"Total in DB: {len(db)}\n")

if __name__ == '__main__':
    main()
