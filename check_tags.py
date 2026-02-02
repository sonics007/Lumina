import sys
import os
sys.path.append(os.getcwd())
try:
    from app import create_app
    from app.models import db, Movie
except ImportError:
    # Handle running from subdir
    sys.path.append(os.path.join(os.getcwd(), '..'))
    from app import create_app
    from app.models import db, Movie

app = create_app()
with app.app_context():
    print("Checking Bahu Series in DB...")
    # Filter for items with 'series' in source
    items = Movie.query.filter(Movie.source.like('%web:bahu%')).all()
    
    series_cnt = 0
    cats = set()
    
    for m in items:
        is_series = 'series' in m.source
        if is_series:
            series_cnt += 1
            cur_tags = m.tags or ""
            # Print sample
            if series_cnt <= 5:
                print(f"ID: {m.id} | Title: {m.title} | Tags: '{cur_tags}'")
            
            if cur_tags:
                for t in cur_tags.split(','):
                    t = t.strip()
                    if t: cats.add(t)
                    
    print(f"\nTotal Bahu Series: {series_cnt}")
    print(f"Categories found in DB: {sorted(list(cats))}")
