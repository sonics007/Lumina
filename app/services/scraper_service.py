import threading
import time
import os
import json
import re
from curl_cffi import requests
from bs4 import BeautifulSoup
from ..models import db, Movie, Stream
from flask import current_app
from .movie_service import movie_service

class ScraperService:
    def __init__(self):
        self.is_running = False
        self.stop_event = threading.Event()
        self.progress = {
            'status': 'Idle',
            'current_page': 0,
            'max_pages': 0,
            'total_found': 0,
            'log': []
        }
        self.thread = None

    def start_scrape(self, app):
        if self.is_running:
            return False
            
        self.is_running = True
        self.stop_event.clear()
        self.progress = {
            'status': 'Starting...',
            'current_page': 0,
            'max_pages': 0,
            'total_found': 0,
            'log': ['Starting scraper process...']
        }
        
        # We need to pass the app object to the thread to use app_context
        self.thread = threading.Thread(target=self._scrape_worker, args=(app,))
        self.thread.start()
        return True

    def stop_scrape(self):
        if self.is_running:
            self.stop_event.set()
            self.progress['status'] = 'Stopping...'
            self.log("Stop signal sent...")
            return True
        return False

    def get_status(self):
        return self.progress

    def log(self, message):
        # Keep last 10 log entries
        self.progress['log'].append(message)
        if len(self.progress['log']) > 10:
            self.progress['log'].pop(0)

    def _scrape_worker(self, app):
        with app.app_context():
            self.log("Scraper thread started")
            try:
                base_url = "https://film-adult.top/en"
                max_pages = 388 # Default, or fetch dynamically
                self.progress['max_pages'] = max_pages
                self.progress['status'] = 'Running'
                
                session = requests.Session(impersonate="chrome120")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                }
                
                # Helper function for parallel processing
                def process_card(data):
                    href = data['href']
                    title = data['title']
                    
                    desc, tags_list = "", ""
                    streams = []
                    
                    try:
                        # New session for thread safety
                        t_session = requests.Session(impersonate="chrome120")
                        det_r = t_session.get(href, headers=headers, timeout=15)
                        
                        if det_r.status_code == 200:
                            dsoup = BeautifulSoup(det_r.text, 'html.parser')
                            
                            # --- Metadata ---
                            d_meta = dsoup.find('meta', property='og:description')
                            if d_meta: desc = d_meta.get('content')
                            if not desc:
                                p_desc = dsoup.find('div', class_='description')
                                if p_desc: desc = p_desc.get_text(strip=True)
                                
                            tag_links = dsoup.select('.categories a, .tags a')
                            if tag_links:
                                tags_list = ", ".join([t.get_text(strip=True) for t in tag_links])
                                
                            if desc and title in desc:
                                desc = desc.replace(f"Watch {title} on Film-Adult", "").strip()
                                
                            # --- Stream Extraction ---
                            candidates = re.findall(r'["\'](https?://[^"\']+)["\']', det_r.text)
                            seen_stream_urls = set()
                            PROVIDERS_KEYWORDS = ['hglink', 'haxloppd', 'myvidplay', 'hlswish', 's2.filmcdn', 'play']
                            
                            for url in candidates:
                                if url in seen_stream_urls: continue
                                
                                is_match = False
                                provider_name = 'unknown'
                                for key in PROVIDERS_KEYWORDS:
                                    if key in url:
                                        is_match = True
                                        if 'hglink' in key: provider_name = 'hglink'
                                        elif 'haxloppd' in key: provider_name = 'hglink'
                                        elif 'myvidplay' in key: provider_name = 'myvidplay'
                                        elif 'hlswish' in key: provider_name = 'hlswish'
                                        else: provider_name = key
                                        break
                                
                                # Basic heuristic filter
                                if (is_match or '/e/' in url) and 'film-adult' not in url:
                                    # Fix bad HGLink URLs
                                    if 'hglink.to' in url and '/e/' in url and url.strip().endswith('/e/'):
                                        continue
                                    
                                    seen_stream_urls.add(url)
                                    streams.append({'provider': provider_name, 'url': url})
                                    
                    except Exception as e:
                        pass
                    
                    return {
                        'title': title,
                        'url': href,
                        'image': data['image'],
                        'description': desc,
                        'tags': tags_list,
                        'source': 'film-adult.top',
                        'streams': streams
                    }

                # Main Loop
                import concurrent.futures
                
                seen_urls = set() # Session tracking to avoid duplicates in run
                
                for page in range(1, max_pages + 1):
                    if self.stop_event.is_set():
                        self.log("Scraping stopped by user.")
                        break
                        
                    self.progress['current_page'] = page
                    url = f"{base_url}/page/{page}/" if page > 1 else base_url
                    self.log(f"Scraping page {page}...")
                    
                    try:
                        r = session.get(url, headers=headers, timeout=30)
                        if r.status_code != 200:
                            self.log(f"Failed page {page}: {r.status_code}")
                            break # or continue?
                            
                        # Redirect check (end of pagination)
                        if page > 1 and r.url.rstrip('/') == base_url.rstrip('/'):
                             self.log("Redirected to home. End.")
                             break
                             
                        soup = BeautifulSoup(r.text, 'html.parser')
                        cards = soup.select('a.poster')
                        
                        if not cards:
                            self.log("No cards found.")
                            if not soup.find(id='pagination'): break
                        
                        # Prepare tasks
                        tasks = []
                        skipped_count = 0
                        
                        for card in cards:
                            href = card.get('href')
                            if not href: continue
                            
                            if href in seen_urls: continue
                            seen_urls.add(href)
                            
                            # Check DB
                            existing = Movie.query.filter_by(url=href).first()
                            if existing and len(existing.streams) > 0:
                                skipped_count += 1
                                continue 
                            
                            title = "Unknown"
                            title_tag = card.find(class_='poster__title')
                            if title_tag: title = title_tag.get_text(strip=True)
                            
                            img_tag = card.find('img')
                            image = img_tag.get('src') if img_tag else ""
                            if image and not image.startswith('http'):
                                 if image.startswith('/'): image = "https://film-adult.com" + image 
                                 else: image = base_url + "/" + image
                                 
                            tasks.append({'href': href, 'title': title, 'image': image})
                        
                        if skipped_count > 0:
                            self.log(f"Skipped {skipped_count} existing movies.")
                            
                        if not tasks:
                            self.log(f"No new movies on page {page}.")
                        else:
                            self.log(f"Processing {len(tasks)} items...")
                            # Parallel execution
                            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                                results = list(executor.map(process_card, tasks))
                            
                            # Save to DB
                            saved_count = 0
                            for item in results:
                                try:
                                    # Check streams existence for logging
                                    if not item.get('streams'):
                                        self.log(f"Warning: No streams found for {item['title']}")
                                        
                                    movie_service.add_or_update_movie(item)
                                    saved_count += 1
                                except Exception as e:
                                    self.log(f"Error saving {item['title']}: {e}")
                            
                            self.log(f"Saved {saved_count} movies.")
                            self.progress['total_found'] += saved_count
                            
                        time.sleep(0.5)

                    except Exception as e:
                        self.log(f"Error on page {page}: {e}")
                        
                self.progress['status'] = 'Finished'
                self.log("Scraping finished.")
                
            except Exception as e:
                self.progress['status'] = 'Error'
                self.log(f"Fatal error: {e}")
            finally:
                self.is_running = False

# Global instance
scraper_service = ScraperService()
