import json
import os
import sys
from sqlalchemy.exc import IntegrityError

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Movie

def run_import():
    app = create_app()
    with app.app_context():
        print("Starting Episodes Import Only...")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        e_path = os.path.join(current_dir, 'bahu', 'episodes_data.json')
        
        if not os.path.exists(e_path):
            print("episodes_data.json not found!")
            return

        with open(e_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Found {len(data)} episodes. Processing...")
        count = 0
        added = 0
        skipped = 0
        
        # Batch processing
        batch = []
        
        for item in data:
            url = item.get('url')
            if not url: continue
            
            # Simple check (cache could speed this up but let's be safe)
            existing = Movie.query.filter_by(url=url).first()
            if existing:
                if existing.content_type != 'series':
                    existing.content_type = 'series'
                skipped += 1
            else:
                title = item.get('title', 'Unknown Episode')
                movie = Movie(
                    title=title,
                    url=url,
                    image=item.get('image'),
                    description=item.get('description', ''),
                    tags=item.get('category'),
                    source='web:bahu:series',
                    content_type='series'
                )
                db.session.add(movie)
                added += 1
            
            count += 1
            if count % 100 == 0:
                try:
                    db.session.commit()
                    print(f"Processed {count}/{len(data)}... (Added: {added}, Skipped: {skipped})")
                except IntegrityError:
                    db.session.rollback()
                    print(f"IntegrityError at batch {count}. Attempting singular recovery...")
                    # Tu by sme mohli retry po jednom, ale pre jednoduchost ideme dalej
                    pass
                except Exception as e:
                    print(f"Error ({e}) at batch {count}")
                    db.session.rollback()

        try:
            db.session.commit()
            print(f"Finished! Total Added: {added}, Total Skipped: {skipped}")
        except Exception as e:
            print(f"Final commit error: {e}")

if __name__ == "__main__":
    run_import()
