import json
import os
import sys

# Add current dir to path to find app module
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from app import create_app
from app.models import db, Movie
from app.services.movie_service import MovieService

def run_import():
    app = create_app()
    with app.app_context():
        print("Starting Bahu Import...")
        duplicates = []
        
        # 1. Series
        s_path = os.path.join(current_dir, 'bahu', 'series_data.json')
        if os.path.exists(s_path):
            print(f"Reading {s_path}...")
            try:
                with open(s_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"Found {len(data)} series items. Importing...")
                count = 0
                for item in data:
                    url = item.get('url')
                    if not url: continue
                    
                    # Check duplicate
                    title = item.get('title', 'Unknown')
                    existing = Movie.query.filter_by(url=url).first()
                    if existing:
                        duplicates.append(f"[Series] {title} - {url}")
                    
                    movie_data = {
                        'title': title,
                        'url': url,
                        'image': item.get('poster'),
                        'description': item.get('description', ''),
                        'tags': item.get('category'),
                        'source': 'web:bahu:series',
                        'streams': [] 
                    }
                    MovieService.add_or_update_movie(movie_data)
                    count += 1
                    if count % 100 == 0:
                        db.session.commit()
                        print(f"  Imported {count} series...")
                
                db.session.commit()
                print(f"Finished Series Import: {count} items.")
            except Exception as e:
                print(f"Error importing series: {e}")
        else:
            print("series_data.json not found.")

        # 2. Movies
        m_path = os.path.join(current_dir, 'bahu', 'data.json')
        if os.path.exists(m_path):
             print(f"Reading {m_path}...")
             try:
                 with open(m_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                 
                 print(f"Found {len(data)} movie items. Importing...")
                 count = 0
                 for item in data:
                    url = item.get('url')
                    if not url: continue
                    
                    # Check duplicate
                    title = item.get('title', 'Unknown')
                    existing = Movie.query.filter_by(url=url).first()
                    if existing:
                        duplicates.append(f"[Movie] {title} - {url}")

                    movie_data = {
                        'title': title,
                        'url': url,
                        'image': item.get('poster'),
                        'description': item.get('description', ''),
                        'tags': item.get('category'),
                        'source': 'web:bahu',
                        'streams': []
                    }
                    MovieService.add_or_update_movie(movie_data)
                    count += 1
                    if count % 100 == 0:
                        db.session.commit()
                        print(f"  Imported {count} movies...")
                        
                 db.session.commit()
                 print(f"Finished Movies Import: {count} items.")
             except Exception as e:
                 print(f"Error importing movies: {e}")
        else:
             print("data.json not found.")

        # 3. Episodes
        e_path = os.path.join(current_dir, 'bahu', 'episodes_data.json')
        if os.path.exists(e_path):
             print(f"Reading {e_path}...")
             try:
                 with open(e_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                 
                 print(f"Found {len(data)} episodes. Importing...")
                 count = 0
                 for item in data:
                    url = item.get('url')
                    if not url: continue
                    
                    title = item.get('title', 'Unknown Episode')
                    
                    movie_data = {
                        'title': title,
                        'url': url,
                        'image': item.get('image'),
                        'description': item.get('description', ''),
                        'tags': item.get('category'),
                        'source': 'web:bahu:series',
                        'streams': [] 
                    }
                    MovieService.add_or_update_movie(movie_data)
                    count += 1
                    if count % 100 == 0:
                        db.session.commit()
                        print(f"  Imported {count} episodes...")
                 
                 db.session.commit()
                 print(f"Finished Episodes Import: {count} items.")
             except Exception as e:
                 print(f"Error importing episodes: {e}")
        
        # Report Duplicates
        if duplicates:
            print(f"\nFound {len(duplicates)} duplicates (already in DB).")
            try:
                with open("duplicates_report.txt", "w", encoding="utf-8") as f:
                    f.write(f"Duplicate Report ({len(duplicates)} items)\n")
                    f.write("=========================================\n")
                    for d in duplicates:
                        f.write(d + "\n")
                print("Duplicates saved to 'duplicates_report.txt'.")
            except Exception as e:
                print(f"Error saving report: {e}")

if __name__ == "__main__":
    run_import()
