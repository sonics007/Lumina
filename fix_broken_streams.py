import json
import os

DB_FILE = 'movies_db.json'

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("Cleaning broken HGLink streams from movies_db.json...")
    
    movies = load_json(DB_FILE)
    if not movies:
        print("DB not found or empty.")
        return
    
    print(f"Total movies before: {len(movies)}")
    
    fixed_count = 0
    removed_count = 0
    
    for m in movies:
        if 'streams' not in m:
            continue
            
        original_count = len(m['streams'])
        
        # Filter out broken HGLink streams (ending with /e/)
        valid_streams = []
        for s in m['streams']:
            url = s.get('url', '')
            if '/e/' in url and (url.endswith('/e/') or url.strip().endswith('/e')):
                removed_count += 1
            else:
                valid_streams.append(s)
        
        m['streams'] = valid_streams
        
        if len(valid_streams) < original_count:
            fixed_count += 1
    
    # Remove movies with no valid streams
    movies_with_streams = [m for m in movies if m.get('streams')]
    removed_movies = len(movies) - len(movies_with_streams)
    
    save_json(DB_FILE, movies_with_streams)
    
    print(f"\nRemoved {removed_count} broken streams from {fixed_count} movies")
    print(f"Removed {removed_movies} movies with no valid streams")
    print(f"Total movies after: {len(movies_with_streams)}")
    print("\nDone! Now run: python migrate_to_sqlite.py")

if __name__ == '__main__':
    main()
