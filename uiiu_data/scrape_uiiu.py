
import sys
import os
import json
import time
import re
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Setup
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(OUTPUT_DIR, 'data')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(DATA_DIR, 'uiiu_movies.json')

# Config
LIMIT_PAGES = 20  # Fetch first 20 pages (approx 280 movies)
DELAY = 0.5

session = requests.Session(impersonate="chrome120")

def get_soup(url):
    try:
        r = session.get(url, timeout=15)
        return BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def scrape_movie_detail(movie_url, allowed_providers=None):
    """Deep scrape to find streams (MixDrop, StreamTape, etc.)
    allowed_providers: list of provider names to include (e.g. ['mixdrop', 'streamtape'])
                       If None, includes all providers
    """
    if allowed_providers is None:
        allowed_providers = ['mixdrop', 'streamtape', 'voe', 'filemoon', 'hglink', 'earnvid']
    soup = get_soup(movie_url)
    if not soup: return []
    
    streams = []
    # Find links
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True)
        name = None
        
        if 'mixdrop' in href: name = "MixDrop"
        elif 'streamtape' in href: name = "StreamTape"
        elif 'voe.sx' in href: name = "Voe"
        elif 'filemoon' in href: name = "FileMoon"
        elif 'earnvid' in href: name = "Earnvid"
        elif any(x in href.lower() for x in ['hglink', 'haxloppd', 'shavtape', 'myvidplay', 'streamhd']): name = "HGLink"
        
        # Fallback text check
        if not name:
            if 'StreamHD' in text or 'HGLink' in text: name = "HGLink"
            if 'Earnvid' in text: name = "Earnvid"

        # Quality
        label = ""
        res_match = re.search(r'(\d{3,4}p)', text)
        if res_match: label = res_match.group(1)
        elif 'HD' in text: label = 'HD'
        
        if name:
            # Check if provider is allowed
            provider_key = name.lower().replace(' ', '')
            if allowed_providers and provider_key not in allowed_providers:
                continue  # Skip this provider
                
            # Avoid duplicates
            if not any(s['url'] == href for s in streams):
                streams.append({
                    'name': name,
                    'url': href,
                    'type': name.lower(),
                    'label': label
                })
                
    # Sort by quality preference (1080p > 720p > HD > others)
    streams.sort(key=lambda s: 3 if '1080p' in s.get('label','') else 2 if '720p' in s.get('label','') else 1 if 'HD' in s.get('label','') else 0, reverse=True)
    
    return streams

def scrape_single_movie(url):
    """Scrape details for a single movie URL (for Add Movie feature)"""
    soup = get_soup(url)
    if not soup: return {}
    
    # Title
    title = "Unknown"
    # Try h1 first
    h1 = soup.find('h1')
    if h1:
        title = h1.get_text(strip=True)
    else:
        # Fallback to page title
        if soup.title:
            title = soup.title.get_text(strip=True).split('Download')[0].strip()
            
    # Image
    image = ""
    # Try finding image in content
    content = soup.select_one('.entry-content') or soup.find('article') or soup.select_one('.post')
    if content:
        img_tag = content.find('img')
        if img_tag:
            image = img_tag.get('src') or img_tag.get('data-src') or ""
            
    # Streams
    streams = scrape_movie_detail(url, allowed_providers=None)  # Single movie fetch uses all providers
    for s in streams: s['provider'] = s.get('name', 'Unknown')
    
    # Select main playable URL if streams exist
    main_url = url # Default to page url if no streams (will likely fail playback but stores data)
    if streams:
        main_url = streams[0]['url']
        
    return {
        'title': title,
        'poster': image, # using 'poster' key to match scraping_top100 format
        'image': image,  # duplicate for safety
        'url': main_url, # The playable stream
        'source_url': url,
        'streams': streams,
        'source': 'uiiumovie'
    }


def process_article(art):
    try:
        # Title & Link
        title = "Unknown"
        movie_link = None
        
        # Priority: h2.entry-title > .title > a
        h2 = art.select_one('h2.entry-title a') or art.select_one('.title a')
        if h2:
            title = h2.get_text(strip=True)
            movie_link = h2['href']
        else:
            a_tag = art.find('a')
            if a_tag:
                 movie_link = a_tag['href']
                 title = a_tag.get('title') or a_tag.get_text(strip=True)
                 
        # Image
        img = ""
        img_tag = art.find('img')
        if img_tag:
            img = img_tag.get('src') or img_tag.get('data-src') or ""
        
        if not movie_link or not title: return None
        
        print(f"    [Fetching] {title[:30]}...", end='\r')
        
        # Fetch Streams
        streams = scrape_movie_detail(movie_link, allowed_providers=ALLOWED_PROVIDERS)
        
        if streams:
            print(f"    [Done] {title[:30]} ({len(streams)} streams)")
            return {
                'title': title,
                'url': movie_link, 
                'image': img,
                'streams': streams,
                'source': 'uiiumovie'
            }
        return None
        
    except Exception as e:
        print(f"    Error processing article: {e}")
        return None

def run(limit_pages=20, max_workers=5, allowed_providers=None):
    global ALLOWED_PROVIDERS
    ALLOWED_PROVIDERS = allowed_providers if allowed_providers else ['mixdrop', 'streamtape', 'voe', 'filemoon', 'hglink', 'earnvid']
    print(f"Starting Scrape UIIU Movie (Limit: {limit_pages} pages, Workers: {max_workers}, Providers: {ALLOWED_PROVIDERS})...")
    all_movies = []
    
    page = 1
    
    import concurrent.futures
    
    while page <= limit_pages:
        print(f"Scraping Page {page}...")
        url = f"https://uiiumovie.com/page/{page}/" if page > 1 else "https://uiiumovie.com/"
        
        soup = get_soup(url)
        if not soup: break
        
        # Select cards - generic WP
        articles = soup.select('article')
        if not articles: articles = soup.select('.post')
        if not articles: articles = soup.select('.item')
             
        if not articles:
            print("No articles found on page.")
            break
            
        print(f"  Found {len(articles)} movies. Processing details parallelly...")
        
        new_items = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(process_article, articles))
            for r in results:
                if r: new_items.append(r)
                
        all_movies.extend(new_items)
        print(f"  Added {len(new_items)} movies from page {page}.")
        
        print("") # Newline
        
        # Detect next
        next_link = soup.find('a', class_='next')
        if not next_link:
            print("No next page. Finishing.")
            break
            
        page += 1
        time.sleep(DELAY)
        
        # Save incremental
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_movies, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Save error: {e}")
                
    # Final save
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_movies, f, indent=2, ensure_ascii=False)
        print(f"Done. Saved {len(all_movies)} movies to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Final save error: {e}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages', type=int, default=20, help='Number of pages to scrape')
    parser.add_argument('--workers', type=int, default=5, help='Number of threads')
    parser.add_argument('--providers', type=str, default='', help='Comma-separated list of providers (e.g. mixdrop,streamtape)')
    args = parser.parse_args()
    
    # Parse providers
    allowed_providers = None
    if args.providers:
        allowed_providers = [p.strip().lower() for p in args.providers.split(',')]
    
    run(limit_pages=args.pages, max_workers=args.workers, allowed_providers=allowed_providers)
