import os
import json
import requests
from bs4 import BeautifulSoup
import sys

# Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BAHU_DIR = os.path.join(BASE_DIR, 'bahu')
sys.path.append(BASE_DIR)

from app import create_app
from app.models import db, Movie

# Bahu info
BASE_URL = "https://www.bahu.tv"
COLLECTIONS = [
     {"name": "Movies (Total)", "url": "https://www.bahu.tv/filmek/legnezettebb-filmek"},
     {"name": "Series (Total)", "url": "https://www.bahu.tv/sorozatok/legnezettebb-sorozatok"}
]

try:
    from bahu import client
    SESSION = client.CLIENT.session
    if not SESSION.cookies: 
        print("Logging in to Bahu...")
        client.CLIENT.login()
except:
    print("Warning: Could not use bahu client session. Using plain requests.")
    SESSION = requests.Session()

def count_json_files():
    print("\n[ LOCAL JSON FILES ]")
    files = {
        'movies': os.path.join(BAHU_DIR, 'movies_data.json'),
        'series': os.path.join(BAHU_DIR, 'series_data.json'),
        'episodes': os.path.join(BAHU_DIR, 'episodes_data.json')
    }
    
    for name, path in files.items():
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"  - {name.capitalize().ljust(10)}: {len(data)} items")
            except:
                 print(f"  - {name.capitalize().ljust(10)}: Error reading file")
        else:
            print(f"  - {name.capitalize().ljust(10)}: 0 items (File not found)")

def count_db_items():
    print("\n[ LUMINA DATABASE ]")
    app = create_app()
    with app.app_context():
        # Movies count (excluding series parent/live)
        movies_count = Movie.query.filter(
            db.not_(Movie.source.ilike('%:series')),
            db.not_(Movie.source.ilike('%:live')),
            db.not_(Movie.tags.ilike('%Live TV%'))
        ).count()
        
        # Series Items (includes both parents and episodes usually)
        series_q = Movie.query.filter(Movie.source.ilike('%:series'))
        all_series_items = series_q.count()
        
        print(f"  - Movies       : {movies_count}")
        print(f"  - Series Items : {all_series_items} (Shows + Episodes)")

def check_web_totals():
    print("\n[ WEB ESTIMATES (Bahu.tv) ]")
    
    for col in COLLECTIONS:
        url = col['url']
        try:
            print(f"  Scanning: {col['name']} ...", end='\r')
            r = SESSION.get(url, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Find pagination
            pag = soup.find('ul', class_='pagination')
            last_page = 1
            if pag:
                links = pag.find_all('a')
                nums = []
                for a in links:
                    if a.text.strip().isdigit():
                        nums.append(int(a.text.strip()))
                if nums:
                    last_page = max(nums)
            
            # Count items on current page
            items = soup.select('li.item')
            items_per_page = len(items)
            if items_per_page == 0: items_per_page = 24
            
            total_est = last_page * items_per_page
            
            print(f"  - {col['name'].ljust(15)}: ~{total_est} items (Pages: {last_page})")
            
        except Exception as e:
            print(f"  - {col['name'].ljust(15)}: Failed to scan ({str(e)[:50]})")

# Helper to log to both stdout and file
class Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode, encoding='utf-8')
        self.stdout = sys.stdout
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()
        self.stdout.flush()
    def __del__(self):
        self.file.close()

if __name__ == "__main__":
    # Setup Logging
    log_path = os.path.join(BAHU_DIR, 'completeness_last_check.txt')
    sys.stdout = Tee(log_path, 'w')
    
    # Print Header with Time
    from datetime import datetime
    print(f"Check started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    count_json_files()
    count_db_items()
    check_web_totals()
    print("\nDone.")
