from app import create_app, db
from app.models import Movie

app = create_app()

with app.app_context():
    print("--- Database Content Check ---")
    movies = Movie.query.limit(20).all()
    count = Movie.query.count()
    print(f"Total Movies in DB: {count}")
    
    if count == 0:
        print("DATABASE IS EMPTY!")
    else:
        print(f"Showing first {len(movies)} items:")
        for m in movies:
            print(f"ID: {m.id} | Title: {m.title[:30]} | Source: {m.source} | Tags: {m.tags}")
            
    print("\n--- Checking Xtream Sources ---")
    from app.models import XtreamSource
    sources = XtreamSource.query.all()
    print(f"Xtream Sources Count: {len(sources)}")
    for s in sources:
        print(f"ID: {s.id} | Name: {s.name} | URL: {s.server_url} | Live Count: {s.live_count} | VOD Count: {s.vod_count}")
        print(f"  Settings: Live={s.import_live}, VOD={s.import_vod}, Series={s.import_series}")
