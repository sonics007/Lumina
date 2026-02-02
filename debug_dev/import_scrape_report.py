#!/usr/bin/env python3
"""
Import scrape_report.json do movies_db.json
Konvertuje výsledky z scrape_top100.py do formátu testing_new

PRAVIDLÁ:
- Každý film len raz v databáze
- Len jeden funkčný stream na film (prvý nájdený)
- FilmCDN streamy -> not_working_providers.txt
- Neznáme providery -> nezname_providery.txt
"""

import json
import os
import sys

# Add parent to path for providers_config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from providers_config import PROVIDERS
except ImportError:
    PROVIDERS = {}
    print("Warning: Could not import PROVIDERS")

# Paths
SCRAPE_REPORT = "../scrape_report.json"
MOVIES_DB = "movies_db.json"
UNKNOWN_FILE = "nezname_providery.txt"
NOT_WORKING_FILE = "not_working_providers.txt"

# Nefunkčné provideri
BROKEN_PROVIDERS = ['filmcdn', 's2.filmcdn.top', 'cfglobalcdn.com']

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return [] if 'movies' in filepath else {}
    return [] if 'movies' in filepath else {}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def append_to_file(filepath, text):
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(text + "\n")

def is_provider_known(provider_name):
    """Check if provider is in our config"""
    if not provider_name:
        return False
    for p_key in PROVIDERS:
        if p_key in provider_name or provider_name in p_key:
            return True
    return False

def is_provider_broken(provider_name):
    """Check if provider is known to be broken"""
    if not provider_name:
        return False
    for broken in BROKEN_PROVIDERS:
        if broken in provider_name.lower():
            return True
    return False

def main():
    print("="*70)
    print("IMPORT SCRAPE_REPORT.JSON -> MOVIES_DB.JSON")
    print("="*70)
    
    # Load scrape report
    if not os.path.exists(SCRAPE_REPORT):
        print(f"Error: {SCRAPE_REPORT} not found!")
        print("Run: cd .. && python scrape_top100.py 1")
        return
    
    report = load_json(SCRAPE_REPORT)
    sources = report.get('sources', [])
    
    if not sources:
        print("No sources found in scrape_report.json")
        return
    
    print(f"Found {len(sources)} sources in scrape_report.json")
    print(f"Known providers: {len(PROVIDERS)} configured")
    
    # Load existing movies_db
    movies_db = load_json(MOVIES_DB)
    existing_titles = {m.get('title', '').lower().strip() for m in movies_db if m.get('title')}
    existing_urls = {m.get('url', '') for m in movies_db}
    
    print(f"Existing movies in DB: {len(movies_db)}")
    
    # Clear output files
    open(UNKNOWN_FILE, 'w').close()
    open(NOT_WORKING_FILE, 'w').close()
    
    # Group sources by movie
    movies_by_url = {}
    for source in sources:
        movie_url = source.get('movie_url')
        if movie_url not in movies_by_url:
            movies_by_url[movie_url] = {
                'title': source.get('title'),
                'url': movie_url,
                'image': source.get('image', ''),
                'description': source.get('description', ''),
                'all_streams': []
            }
        
        movies_by_url[movie_url]['all_streams'].append({
            'provider': source.get('provider', ''),
            'url': source.get('url', '')
        })
    
    # Process movies
    added_db = 0
    added_unknown = 0
    added_broken = 0
    skipped_title = 0
    skipped_url = 0
    
    for movie_url, movie_data in movies_by_url.items():
        title = movie_data['title']
        
        # Check duplicates
        if movie_url in existing_urls:
            skipped_url += 1
            continue
        
        if title.lower().strip() in existing_titles:
            skipped_title += 1
            print(f"  [i] Skipping '{title}' - already in database")
            continue
        
        # Find FIRST working stream (priority: known > unknown > broken)
        working_stream = None
        unknown_streams = []
        broken_streams = []
        
        for stream in movie_data['all_streams']:
            provider = stream['provider']
            
            if is_provider_broken(provider):
                broken_streams.append(stream)
            elif is_provider_known(provider):
                if not working_stream:  # Take only FIRST working stream
                    working_stream = stream
            else:
                unknown_streams.append(stream)
        
        # If no known working stream, try unknown
        if not working_stream and unknown_streams:
            working_stream = unknown_streams[0]
            unknown_streams = unknown_streams[1:]  # Rest go to unknown file
        
        # Save to DB if we have a working stream
        if working_stream:
            db_entry = {
                'title': title,
                'url': movie_url,
                'image': movie_data['image'],
                'description': movie_data['description'],
                'streams': [working_stream]  # Only ONE stream
            }
            movies_db.append(db_entry)
            existing_titles.add(title.lower().strip())
            existing_urls.add(movie_url)
            added_db += 1
            print(f"  [+] DB: {title} (provider: {working_stream['provider']})")
        
        # Save remaining unknown streams to file
        if unknown_streams:
            unknown_text = f"Movie: {title}\nURL: {movie_url}\nAlternative Unknown Providers:\n"
            for s in unknown_streams:
                unknown_text += f"  - {s['provider']}: {s['url']}\n"
            unknown_text += "-"*50
            append_to_file(UNKNOWN_FILE, unknown_text)
            added_unknown += 1
        
        # Save broken streams to file
        if broken_streams:
            broken_text = f"Movie: {title}\nURL: {movie_url}\nBroken Providers (FilmCDN):\n"
            for s in broken_streams:
                broken_text += f"  - {s['provider']}: {s['url']}\n"
            broken_text += "-"*50
            append_to_file(NOT_WORKING_FILE, broken_text)
            if not working_stream:  # Count only if movie has NO working stream
                added_broken += 1
    
    # Save DB
    save_json(MOVIES_DB, movies_db)
    
    print(f"\n{'='*70}")
    print(f"RESULTS:")
    print(f"  Added to DB: {added_db} movies (1 stream each)")
    print(f"  Logged unknown providers: {added_unknown} movies")
    print(f"  Logged broken providers: {added_broken} movies")
    print(f"  Skipped (URL): {skipped_url}")
    print(f"  Skipped (Title): {skipped_title}")
    print(f"  Total in DB: {len(movies_db)}")
    print(f"{'='*70}")
    
    if added_unknown > 0:
        print(f"\n⚠️  Check {UNKNOWN_FILE} for alternative unknown providers")
    if added_broken > 0:
        print(f"⚠️  Check {NOT_WORKING_FILE} for FilmCDN streams")

if __name__ == '__main__':
    main()
