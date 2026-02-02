import sys
import os

# Add bahu dir to path
sys.path.append(os.path.join(os.getcwd(), 'bahu'))

import scraper_v2
import client

def run():
    print("Logging in...")
    if not client.CLIENT.login():
        print("Login failed")
        return

    print("Scraping Kids content...")
    
    # Override log file to avoid conflicts
    scraper_v2.LOG_FILE = "bahu/kids_scraper.log"

    kids_cols = [
        {"name": "Gyerekeknek Sorozatok", "url": "https://www.bahu.tv/gyerekeknek-sorozatok", "type": "sorozatok"},
        {"name": "Gyerekeknek Filmek", "url": "https://www.bahu.tv/gyerekeknek-filmek", "type": "filmek"},
    ]
    
    for col in kids_cols:
        scraper_v2.scrape_category(col['name'], "", col['type'], max_pages=100, url_override=col['url'])
        
    print("Kids scraping done.")

if __name__ == "__main__":
    run()
