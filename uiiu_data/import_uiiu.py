
import json
import os
import sys
import datetime

# Add root dir to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)

from app import create_app, db
from app.models import Movie, Stream

DATA_FILE = os.path.join(CURRENT_DIR, 'data', 'uiiu_movies.json')

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def main():
    print(f"Starting Import from {DATA_FILE}...")
    
    scraped_data = load_json(DATA_FILE)
    if not scraped_data:
        print("No scraped data found. Run scraping first.")
        time.sleep(2)
        return

    print(f"Loaded {len(scraped_data)} movies from scrape file.")
    
    app = create_app()
    with app.app_context():
        # Validation / Dedup using DB
        added_count = 0
        skipped_count = 0
        
        for item in scraped_data:
            source_url = item.get('url') # The movie page URL
            if not source_url: continue
            
            # Check if exists by source_url
            existing = Movie.query.filter_by(url=source_url).first()
            if existing:
                skipped_count += 1
                # print(f"Skipping {item['title'][:20]} - already exists")
                continue
                
            streams_data = item.get('streams', [])
            if not streams_data:
                # If no streams, maybe skip? We want playable stuff.
                # continue 
                pass
                
            # Create Movie
            try:
                # Default stream URL (playable)
                # If streams exist, take first. Else take source_url
                playable_url = source_url
                if streams_data:
                    playable_url = streams_data[0]['url']
                
                new_movie = Movie(
                    title=item['title'],
                    url=source_url, # Unique identifier is source URL
                    image=item.get('image', ''),
                    description=f"Imported from UIIU Movie\nDetails: {len(streams_data)} streams found.",
                    rating=item.get('rating', ''),
                    source='uiiumovie', # Tag as uiiu
                    tags='uiiu, adult',
                    created_at=datetime.datetime.now()
                )
                
                db.session.add(new_movie)
                db.session.flush() # Get ID
                
                # Add streams
                for s in streams_data:
                    stream = Stream(
                        movie_id=new_movie.id,
                        provider=s.get('name', 'Unknown'),
                        url=s['url']
                    )
                    db.session.add(stream)
                    
                added_count += 1
                print(f"Added: {item['title'][:40]}")
                
            except Exception as e:
                print(f"Error adding {item['title']}: {e}")
                db.session.rollback()
                continue
        
        try:
            db.session.commit()
            print(f"Commit successful.")
        except Exception as e:
            print(f"Commit failed: {e}")
            db.session.rollback()

    print(f"Import Finished.")
    print(f"Added: {added_count}")
    print(f"Skipped: {skipped_count}")
    
    try:
        import time
        if sys.platform == 'win32':
             time.sleep(5)
    except: pass

if __name__ == '__main__':
    main()
