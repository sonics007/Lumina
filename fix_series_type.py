import os
import sys

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, Movie

def fix():
    app = create_app()
    with app.app_context():
        print("Scanning for incorrectly categorized series...")
        
        # 1. By Source
        series_by_source = Movie.query.filter_by(source='web:bahu:series').all()
        print(f"Found {len(series_by_source)} items with source='web:bahu:series'.")
        
        # 2. By URL pattern
        series_by_url = Movie.query.filter(Movie.url.like('%/sorozat/%')).all()
        print(f"Found {len(series_by_url)} items with URL containing '/sorozat/'.")
        
        # Merge sets
        all_series = set(series_by_source + series_by_url)
        
        count = 0
        for item in all_series:
            changed = False
            if item.content_type != 'series':
                old = item.content_type
                item.content_type = 'series'
                changed = True
                print(f"Fixing Type: {item.title} ({old} -> series)")
                
            if item.source != 'web:bahu:series':
                item.source = 'web:bahu:series'
                changed = True
                print(f"Fixing Source: {item.title}")
                
            if changed:
                count += 1
                
        if count > 0:
            db.session.commit()
            print(f"Successfully fixed {count} items.")
        else:
            print("No items needed fixing.")

if __name__ == "__main__":
    fix()
