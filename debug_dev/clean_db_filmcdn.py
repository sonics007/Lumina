import json
import os

DB_FILE = 'movies_db.json'

def clean_db():
    if not os.path.exists(DB_FILE):
        print("DB file not found.")
        return

    with open(DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cleaned_data = []
    removed_count = 0
    
    for item in data:
        original_streams = item.get('streams', [])
        # Filter streams: keep only if NOT filmcdn
        new_streams = [s for s in original_streams if 'filmcdn' not in s['url'] and 'filmcdn' not in s['provider']]
        
        removed = len(original_streams) - len(new_streams)
        removed_count += removed
        
        item['streams'] = new_streams
        
        # Only keep item if it still has streams OR if it was a legacy item without streams
        if new_streams or (not original_streams and 'url' in item):
             cleaned_data.append(item)
        else:
             print(f"Removing movie '{item['title']}' because no valid streams left after cleaning.")

    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
    print(f"Done. Removed {removed_count} FilmCDN streams. Database size: {len(cleaned_data)} movies.")

if __name__ == "__main__":
    clean_db()
