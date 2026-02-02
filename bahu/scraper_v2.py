import requests
from bs4 import BeautifulSoup
import json
import time
import os
import logging
from datetime import datetime
import sys

# Add current dir to path to import client
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import client

# Configuration
BASE_URL = "https://www.bahu.tv"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
DATA_FILE_SERIES = os.path.join(BASE_DIR, "series_data.json")
LOG_FILE = os.path.join(BASE_DIR, "scraper.log")
STATUS_FILE = os.path.join(BASE_DIR, "scraper_status.json")

# Map of Categories
CATEGORIES = {
    "Akció": 1, "Animáció": 21, "Családi": 3, "Dokumentum": 24, "Dráma": 4,
    "Fantázia": 22, "Háborús": 23, "Horror": 6, "Kaland": 7, "Krimi": 9,
    "Misztikus": 10, "Rajzfilm": 12, "Romantikus": 14, "Sci-Fi": 15,
    "Sport": 25, "Thriller": 17, "Történelmi": 18, "Vígjáték": 19,
    "Western": 20, "Valóság show": 13, "Tehetségkutató": 26
}

COLLECTIONS = [
    # Movies
    {"name": "Legnézettebb Filmek", "url": "https://www.bahu.tv/filmek/legnezettebb-filmek", "type": "filmek"},
    {"name": "Jelenleg Követett Filmek", "url": "https://www.bahu.tv/filmek/jelenleg-kovetett-filmek", "type": "filmek"},
    {"name": "Legértékeltebb Filmek", "url": "https://www.bahu.tv/filmek/legertekeltebb-filmek", "type": "filmek"},
    {"name": "IMDb Top Filmek", "url": "https://www.bahu.tv/filmek/imdb-toplista", "type": "filmek"},
    {"name": "Oscar Nyertesek", "url": "https://www.bahu.tv/filmek/oscar-winner", "type": "filmek"},
    
    # Series (Enabled)
    {"name": "Legnézettebb Sorozatok", "url": "https://www.bahu.tv/sorozatok/legnezettebb-sorozatok", "type": "sorozatok"},
    {"name": "Jelenleg Követett Sorozatok", "url": "https://www.bahu.tv/sorozatok/jelenleg-kovetett-sorozatok", "type": "sorozatok"},
    {"name": "Legértékeltebb Sorozatok", "url": "https://www.bahu.tv/sorozatok/legertekeltebb-sorozatok", "type": "sorozatok"},
    {"name": "IMDb Top Sorozatok", "url": "https://www.bahu.tv/sorozatok/imdb-toplista", "type": "sorozatok"},
    {"name": "Golden Globe Sorozatok", "url": "https://www.bahu.tv/sorozatok/golden-globe-winner", "type": "sorozatok"},
    {"name": "Gyerekeknek Sorozatok", "url": "https://www.bahu.tv/gyerekeknek-sorozatok", "type": "sorozatok"},
    {"name": "Gyerekeknek Filmek", "url": "https://www.bahu.tv/gyerekeknek-filmek", "type": "filmek"},
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

def update_status(status_msg, category="", current_page=0, total_pages=0):
    data = {
        "status": status_msg,
        "category": category,
        "current_page": current_page,
        "max_pages": total_pages,
        "total_found": TOTAL_FOUND,
        "total_added": TOTAL_ADDED,
        "timestamp": time.time()
    }
    try:
        with open(STATUS_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f)
    except:
        pass

def load_db(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_db(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Global Stats
TOTAL_FOUND = 0
TOTAL_ADDED = 0
TOTAL_EXISTS = 0

def scrape_category(cat_name, cat_id, page_type="filmek", max_pages=2, url_override=None):
    global TOTAL_FOUND, TOTAL_ADDED, TOTAL_EXISTS
    
    # Determine DB file
    if page_type == "sorozatok" or (url_override and "sorozat" in url_override):
        target_file = DATA_FILE_SERIES
        target_type = "series"
    else:
        target_file = DATA_FILE
        target_type = "movie"

    db = load_db(target_file)
    existing_urls = {item['url'] for item in db}
    
    cat_found = 0
    cat_added = 0
    cat_exists = 0
    
    logging.info(f"--- Scraping: {cat_name} ({page_type}) ---")
    update_status(f"Starting {cat_name}...", cat_name, 0, max_pages)

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
            if page_type == "filmek":
                url = f"{BASE_URL}/filmek"
                params = {
                    "category": cat_id,
                    "sort": "id DESC",
                    "Movie_page": i
                }
            else:
                url = f"{BASE_URL}/sorozatok"
                params = {
                    "category": cat_id,
                    "Serial_page": i,
                    "recommended_age": "",
                    "releaseDate": ""
                }
            
        logging.info(f"Page {i}: {url} with params {params}")
        update_status(f"Scraping {cat_name} (Page {i})", cat_name, i, max_pages)
        
        try:
            if page_type == "sorozatok" and not url_override:
                r = client.CLIENT.session.post(url, data=params)
            else:
                r = client.CLIENT.session.get(url, params=params)
                
            soup = BeautifulSoup(r.text, 'html.parser')
            
            page_items_found = 0
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
                # 1. URL and Title
                a_link = item_node.find('a', class_='movies-link')
                if not a_link: continue
                
                href = a_link.get('href', '')
                title = a_link.get('title', '')
                
                # 2. Poster
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

                    if clean_url in existing_urls:
                        # Update Category for existing item
                        for ex_item in db:
                            if ex_item.get('url') == clean_url:
                                cur_cats = ex_item.get('category', '')
                                c_list = [x.strip() for x in cur_cats.split(',') if x.strip()]
                                
                                if cat_name not in c_list:
                                    c_list.append(cat_name)
                                    ex_item['category'] = ", ".join(c_list)
                                    logging.info(f"UPDATED: {title} + {cat_name}")
                                    
                                    # Trigger save if many updates
                                    if cat_exists % 20 == 0: save_db(db, target_file)
                                break

                        # logging.info(f"EXISTS: {title}") 
                        cat_exists += 1
                        TOTAL_EXISTS += 1
                        cat_found += 1
                        TOTAL_FOUND += 1
                        continue
                        
                    if title:
                        logging.info(f"NEW: {title}")
                        item_data = {
                            "title": title,
                            "url": clean_url,
                            "poster": poster,
                            "description": "", 
                            "category": cat_name, 
                            "type": target_type,
                            "added_at": datetime.now().isoformat()
                        }
                        
                        db.append(item_data)
                        existing_urls.add(clean_url)
                        cat_added += 1
                        TOTAL_ADDED += 1
                        cat_found += 1
                        TOTAL_FOUND += 1
                        page_items_found += 1
                        
                        if cat_added % 5 == 0: save_db(db, target_file)
                        
            if page_items_found == 0 and cat_exists == 0 and url_override is None:
                 if len(items) == 0:
                    logging.info("  No items found on this page (Empty). Stopping.")
                    if i > 1: break
                
        except Exception as e:
            logging.error(f"Error: {e}")
            
    save_db(db, target_file)

if __name__ == "__main__":
    update_status("Logging in...", "", 0, 0)
    if not client.CLIENT.login():
        print("Login failed!")
        update_status("Error: Login failed!", "", 0, 0)
        exit()
        
    start_time = time.time()
        
    # 1. Scrape Collections
    logging.info(">>> SCRAPING COLLECTIONS <<<")
    for col in COLLECTIONS:
        scrape_category(col['name'], "", col['type'], max_pages=5, url_override=col['url'])
        
    # 2. Scrape Categories (Movies)
    logging.info(">>> SCRAPING MOVIE CATEGORIES <<<")
    for name, cid in CATEGORIES.items():
        scrape_category(name, cid, "filmek", max_pages=100) 

    # 3. Scrape Categories (Series) - assuming same IDs work
    logging.info(">>> SCRAPING SERIES CATEGORIES <<<")
    for name, cid in CATEGORIES.items():
        scrape_category(name, cid, "sorozatok", max_pages=20)
    
    end_time = time.time()
    duration = end_time - start_time
    
    summary = f"""
========================================
SCRAPING COMPLETE in {duration:.2f} seconds
========================================
TOTAL FOUND:   {TOTAL_FOUND}
TOTAL ADDED:   {TOTAL_ADDED}
TOTAL EXISTS:  {TOTAL_EXISTS}
========================================
"""
    print(summary)
    logging.info(f"Final Stats: Found={TOTAL_FOUND}, Added={TOTAL_ADDED}")
    update_status("Completed!", "", 100, 100)
    
    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)
