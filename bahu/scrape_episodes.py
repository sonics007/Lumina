import sys
import os
import json
import re
import logging
from bs4 import BeautifulSoup

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
import client

DATA_FILE_SERIES = os.path.join(BASE_DIR, "series_data.json")
EPISODES_FILE = os.path.join(BASE_DIR, "episodes_data.json")

def scrape_episodes():
    print("Logging into Bahu...")
    if not client.CLIENT.login():
        print("Login failed")
        return

    # Load series
    if not os.path.exists(DATA_FILE_SERIES):
        print("Series data not found.")
        return

    with open(DATA_FILE_SERIES, 'r', encoding='utf-8') as f:
        series_list = json.load(f)

    episodes_db = []
    
    # Load existing episodes if any to avoid duplicates? 
    # For now overwrite to ensure fix.
    
    count = 0
    total = len(series_list)
    print(f"Scraping episodes for {total} series...")
    
    for s_item in series_list:
        count += 1
        s_title = s_item.get('title')
        s_url = s_item.get('url')
        s_img = s_item.get('image')
        s_cats = s_item.get('category')
        
        # print(f"[{count}/{total}] Scraping: {s_title}")
        
        try:
            r = client.CLIENT.session.get(s_url)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Find episodes (Season 1 primarily)
            ep_items = soup.select('.episode-list .item .inner-details')
            
            items_added = 0
            for ep in ep_items:
                link = ep.find('a', class_='episode-link')
                if not link: continue
                
                ep_url = link.get('href')
                if not ep_url.startswith('http'): ep_url = "https://www.bahu.tv" + ep_url
                
                # Title parsing
                desc_div = ep.find('div', class_='description')
                ep_title_full = desc_div.text.strip() if desc_div else "Episode"
                
                # Parse Season/Episode
                # Format: "1 Évad, 1 Rész"
                match = re.search(r'(\d+)\s*Évad.*?(\d+)\s*Rész', ep_title_full, re.IGNORECASE)
                if match:
                    season = int(match.group(1))
                    episode = int(match.group(2))
                    # Xtream Required Format: "Title - SxxExx"
                    fmt_title = f"{s_title} - S{season:02d}E{episode:02d}"
                else:
                    # Fallback
                    fmt_title = f"{s_title} - {ep_title_full}"
                
                # Episode thumbnail usually in 'figure a img'
                thumb = s_img # default to series cover
                img_tag = ep.select_one('figure a img')
                if img_tag and img_tag.get('src'):
                     thumb = img_tag.get('src')
                
                ep_data = {
                    "title": fmt_title,
                    "url": ep_url, # Points to watch page
                    "image": thumb, 
                    "category": s_cats,
                    "source": "web:bahu:series", 
                    "description": s_item.get('description', '')
                }
                
                episodes_db.append(ep_data)
                items_added += 1
            
            print(f"[{count}/{total}] {s_title}: Found {items_added} episodes.")

        except Exception as e:
            print(f"Error scraping {s_title}: {e}")
            
        # Save periodically
        if count % 10 == 0:
            with open(EPISODES_FILE, 'w', encoding='utf-8') as f:
                json.dump(episodes_db, f, indent=4)
                
    # Final save
    with open(EPISODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(episodes_db, f, indent=4)
    print(f"Done. Saved {len(episodes_db)} episodes to episodes_data.json")

if __name__ == "__main__":
    scrape_episodes()
