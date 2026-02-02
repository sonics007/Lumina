import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup

# Config
DATA_FILE = "data.json"
BASE_URL = "https://www.bahu.tv"

CATEGORIES = {
    # Main ID based categories
    "Akció": 1,
    "Animáció": 21,
    # "Családi": 3,
    # "Dokumentum": 24,
    "Dráma": 4,
    # "Fantázia": 22,
    # "Háborús": 23,
    "Horror": 6,
    # "Kaland": 7,
    "Krimi": 9,
    # "Misztikus": 10,
    "Sci-Fi": 12,
    "Thriller": 14,
    "Vígjáték": 5
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def load_db():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def save_db(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def scrape_selenium():
    logging.info("Starting Selenium Scraper...")
    
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Visible mode to see progress (can be headless later)
    
    driver = uc.Chrome(options=options)
    db = load_db()
    existing_urls = {item['url'] for item in db}
    new_count = 0
    
    try:
        # 1. Login
        logging.info("Logging in - Please login manually if scripts fails to submit (60s wait)")
        driver.get("https://www.bahu.tv/authorize/login")
        
        # Try Auto Login if fields available (Optional, better to assist user)
        # Assuming user logs in manually for now to be safe
        time.sleep(3)
        input("Please Login in the browser window, then press ENTER here to continue...")
        
        logging.info("Starting Crawl...")
        
        # 2. Iterate Categories
        for cat_name, cat_id in CATEGORIES.items():
            url = f"https://www.bahu.tv/filmek?category={cat_id}&sort=id+DESC"
            logging.info(f"Navigating to Category: {cat_name} ({url})")
            
            driver.get(url)
            time.sleep(3)
            
            # 3. Click PROCEED/LOAD MORE multiple times
            clicks = 0
            max_clicks = 10 # Adjust depth here
            
            while clicks < max_clicks:
                try:
                    # Scroll to bottom
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    
                    # Find 'Tovább' button
                    # Class might be 'list-pagination-preloader' or similar via AJAX
                    # Or a link with text "Tovább"
                    
                    # Try finding by text (Hungarian)
                    # Using XPath for text contains
                    buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Tovább')]")
                    
                    clicked = False
                    for btn in buttons:
                        if btn.is_displayed():
                            logging.info(f"  Clicking Load More ({clicks+1}/{max_clicks})...")
                            # Use js click for stability
                            driver.execute_script("arguments[0].click();", btn)
                            time.sleep(2) # Wait for content
                            clicked = True
                            clicks += 1
                            break
                    
                    if not clicked:
                        logging.info("  No more 'Tovább' button found.")
                        break
                        
                except Exception as e:
                    logging.warning(f"  Error clicking load more: {e}")
                    break
            
            # 4. Parse content
            logging.info("  Parsing loaded content...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            links = soup.find_all('a', href=True)
            
            cat_new = 0
            for a in links:
                href = a['href']
                if href.startswith('/film/'):
                    full_url = BASE_URL + href
                    if full_url in existing_urls: continue
                    
                    # Extract Metadata from HTML
                    title = ""
                    poster = ""
                    img = a.find('img')
                    if img:
                        poster = img.get('src') or img.get('data-src', '')
                        if poster and not poster.startswith('http'): poster = BASE_URL + poster
                        title = img.get('alt', '')
                    
                    if not title: title = a.text.strip()
                    
                    if title:
                        item = {
                            "title": title,
                            "url": full_url,
                            "poster": poster,
                            "category": cat_name,
                            "type": "movie",
                            "added_at": datetime.now().isoformat()
                        }
                        db.append(item)
                        existing_urls.add(full_url)
                        cat_new += 1
            
            logging.info(f"  Added {cat_new} new movies from {cat_name}")
            save_db(db)
            new_count += cat_new
            
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        driver.quit()
        
    logging.info(f"Total new items: {new_count}")

if __name__ == "__main__":
    scrape_selenium()
