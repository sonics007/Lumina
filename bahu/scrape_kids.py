import sys
import os
# Fix path to import client/scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import scraper_v2
import client

if __name__ == "__main__":
    print("Logging in...")
    if client.CLIENT.login():
        print("Scraping Kids Series...")
        scraper_v2.scrape_category("Gyerekeknek Sorozatok", "", "sorozatok", max_pages=5, url_override="https://www.bahu.tv/gyerekeknek-sorozatok")
        print("Scraping Kids Movies...")
        scraper_v2.scrape_category("Gyerekeknek Filmek", "", "filmek", max_pages=5, url_override="https://www.bahu.tv/gyerekeknek-filmek")
