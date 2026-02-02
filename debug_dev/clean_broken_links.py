
import json
import os
import sys

# Path setup
sys.path.append(os.getcwd())
# Also try parent dir if run from debug_dev
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

DB_FILE = 'movies_db.json'
# If running from debug_dev, db file is one level up
if not os.path.exists(DB_FILE) and os.path.exists(os.path.join('..', DB_FILE)):
    DB_FILE = os.path.join('..', DB_FILE)

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("Starting Deep Clean of Broken Links...")
    print(f"Target DB: {DB_FILE}")
    
    movies = load_json(DB_FILE)
    if not movies:
        print("DB not found or empty.")
        input("\nPress Enter to exit...")
        return

    print(f"Total movies before: {len(movies)}")
    
    valid_movies = []
    removed_count = 0
    
    for m in movies:
        url = m.get('url', '')
        
        # Check specific broken pattern reported by user
        # https://hglink.to/e/ (empty ID)
        if '/e/' in url and (url.endswith('/e/') or url.strip().endswith('/e')):
             print(f"Removing broken URL: {url} - {m.get('title')}")
             removed_count += 1
             continue
             
        # Check if URL is completely empty
        if not url:
             removed_count += 1
             continue

        valid_movies.append(m)
        
    if removed_count > 0:
        save_json(DB_FILE, valid_movies)
        print(f"Removed {removed_count} broken movies.")
        print(f"Total movies after: {len(valid_movies)}")
    else:
        print("No broken links found.")
        
    print("\nDone.")
    try:
        # Keep window open for 10 seconds or input
        import time
        time.sleep(2)
        print("Window will close in 10 seconds (or press Enter)...")
        if sys.platform == 'win32':
             # input() might block automation if run headless? But user runs it in NEW_CONSOLE.
             # So input is fine.
             input()
    except: pass

if __name__ == '__main__':
    main()
