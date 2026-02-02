
import json
import os
import time
import sys
import io

# Force UTF-8 for Windows console
try:
    if sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr.encoding.lower() != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except Exception as e:
    print(f"Warning: Could not set UTF-8 encoding: {e}")

# Determine script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Make sure we can import from parent directory (where scrape_top100 is)
sys.path.append(os.path.abspath(os.path.join(SCRIPT_DIR, '..')))

from scrape_top100 import get_movie_details, logger
import logging

# Mute logger from scraper to avoid spamming console if needed
for handler in logger.handlers[:]:
    logger.removeHandler(handler)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# Configuration
DEFAULT_SCRAPED_FILE = os.path.join(SCRIPT_DIR, 'data', 'film_adult_movies_en.json')
DB_FILE = os.path.join(SCRIPT_DIR, '..', 'movies_db.json')
IGNORED_FILE = os.path.join(SCRIPT_DIR, 'playvid_ended', 'ignored_movies.json')
NOT_ADDED_FILE = os.path.join(SCRIPT_DIR, 'playvid_ended', 'nepridane.json')

def load_json(path, default=[]):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(path, data):
    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("Starting Step 1 Import (MyVidPlay Only)...")
    print(f"Reading from: {DEFAULT_SCRAPED_FILE}")
    print(f"Checking DB: {DB_FILE}")
    print(f"Outputting leftovers to: {NOT_ADDED_FILE}")
    
    target_file = DEFAULT_SCRAPED_FILE
    
    if not os.path.exists(target_file):
        print(f"Error: Scraped file not found at {target_file}")
        return

    # Load data
    movies_db = load_json(DB_FILE)
    ignored = load_json(IGNORED_FILE) # Might use ignored from playvid_ended or root? Following instruction to use playvid_ended
    scraped = load_json(target_file)
    
    not_added = [] 
    
    # Helper Sets for fast lookup
    existing_urls = set(m.get('url') for m in movies_db if m.get('url'))
    ignored_urls = set(ignored)
    
    total = len(scraped)
    print(f"Total movies to process: {total}")
    
    added_count = 0
    skipped_count = 0
    already_in_db = 0
    
    try:
        for i, movie in enumerate(scraped):
            url = movie.get('url')
            title = movie.get('title', 'Unknown')
            
            # Check Existance
            if url in existing_urls:
                already_in_db += 1
                if i % 1000 == 0: print(f"[{i+1}/{total}] Skipping existing...")
                continue
                
            if url in ignored_urls:
                continue

            print(f"[{i+1}/{total}] Analyzing: {title} ...", end="", flush=True)
            
            try:
                details = get_movie_details(url)
                
                if 'error' in details:
                     print(" Error fetching/analyzing.")
                     not_added.append(movie)
                     skipped_count += 1
                     continue
                     
                # Find MyVidPlay
                myvidplay_stream = None
                if 'streams' in details:
                    for s in details['streams']:
                        if s.get('provider') == 'myvidplay':
                            myvidplay_stream = s
                            break
                
                if myvidplay_stream:
                    # Add to DB
                    new_entry = {
                        'title': details.get('title', title),
                        'url': details.get('original_url', url),
                        'image': details.get('image', movie.get('image','')),
                        'description': details.get('description', ''),
                        'streams': [myvidplay_stream] 
                    }
                    
                    # Update DB in memory
                    movies_db.append(new_entry)
                    existing_urls.add(url) 
                    
                    print(" ✅ Added (MyVidPlay)")
                    added_count += 1
                    
                    # Save DB periodically (every 5 adds)
                    if added_count % 5 == 0:
                        save_json(DB_FILE, movies_db)
                        # Also save not_added periodically? Ideally yes but it's expensive to write huge file.
                        
                else:
                    print(" ❌ No MyVidPlay found.")
                    not_added.append(movie)
                    skipped_count += 1
                    
            except Exception as e:
                print(f" Exception: {e}")
                not_added.append(movie)
                skipped_count += 1
                
            # Rate limit
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping...")

    # Final Save
    save_json(DB_FILE, movies_db)
    save_json(NOT_ADDED_FILE, not_added)
    save_json(IGNORED_FILE, ignored) # Just to ensure file exists in target dir
    
    print("\nStep 1 Complete.")
    print(f"Already in DB: {already_in_db}")
    print(f"Added: {added_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Saved skipped to {NOT_ADDED_FILE}")

if __name__ == "__main__":
    main()
