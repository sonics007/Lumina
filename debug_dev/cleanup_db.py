#!/usr/bin/env python3
"""
Cleanup movies_db.json - ponechať len jeden stream na film
Priorita: známe providery > neznáme > filmcdn
"""

import json
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from providers_config import PROVIDERS
except ImportError:
    PROVIDERS = {}

MOVIES_DB = "movies_db.json"
BROKEN_PROVIDERS = ['filmcdn', 's2.filmcdn.top', 'cfglobalcdn.com']

def is_provider_known(provider_name):
    if not provider_name:
        return False
    for p_key in PROVIDERS:
        if p_key in provider_name or provider_name in p_key:
            return True
    return False

def is_provider_broken(provider_name):
    if not provider_name:
        return False
    for broken in BROKEN_PROVIDERS:
        if broken in provider_name.lower():
            return True
    return False

def main():
    print("="*70)
    print("CLEANUP MOVIES_DB.JSON - ONE STREAM PER MOVIE")
    print("="*70)
    
    with open(MOVIES_DB, 'r', encoding='utf-8') as f:
        movies = json.load(f)
    
    print(f"Total movies: {len(movies)}")
    
    cleaned = 0
    removed_streams = 0
    
    for movie in movies:
        streams = movie.get('streams', [])
        if len(streams) <= 1:
            continue
        
        # Find best stream
        best_stream = None
        
        # Priority 1: Known working providers
        for stream in streams:
            provider = stream.get('provider', '')
            if is_provider_known(provider) and not is_provider_broken(provider):
                best_stream = stream
                break
        
        # Priority 2: Unknown (if no known found)
        if not best_stream:
            for stream in streams:
                provider = stream.get('provider', '')
                if not is_provider_broken(provider):
                    best_stream = stream
                    break
        
        # Priority 3: Even broken is better than nothing
        if not best_stream and streams:
            best_stream = streams[0]
        
        if best_stream:
            old_count = len(streams)
            movie['streams'] = [best_stream]
            removed_streams += old_count - 1
            cleaned += 1
            print(f"  [{movie['title']}] {old_count} streams -> 1 ({best_stream.get('provider')})")
    
    # Save
    with open(MOVIES_DB, 'w', encoding='utf-8') as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"RESULTS:")
    print(f"  Cleaned movies: {cleaned}")
    print(f"  Removed streams: {removed_streams}")
    print(f"  Total movies: {len(movies)}")
    print(f"{'='*70}")

if __name__ == '__main__':
    main()
