import requests
from bs4 import BeautifulSoup
import re
import logging
import sys
import os

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scrape_top100")

def get_movie_details(url):
    """
    Fetches details for a single movie URL (film-adult.top or similar).
    Returns a dictionary with metadata and found streams.
    Used by import scripts in adult_film_data.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://film-adult.top/'
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return {'error': f"Status {r.status_code}"}
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Title
        title = "Unknown"
        og_title = soup.find('meta', property='og:title')
        if og_title: title = og_title.get('content')
        else:
            t = soup.find('h1')
            if t: title = t.get_text(strip=True)
            
        # Image
        image = ""
        og_image = soup.find('meta', property='og:image')
        if og_image: image = og_image.get('content')
        
        # Description
        description = ""
        og_desc = soup.find('meta', property='og:description')
        if og_desc: description = og_desc.get('content')
        
        # Streams Detection
        streams = []
        unique_urls = set()
        
        # Regex for potential URLs in script or iframes
        candidates = re.findall(r'["\'](https?://[^"\']+)["\']', r.text)
        
        # Also check iframe srcs specifically
        iframes = soup.find_all('iframe')
        for iframe in iframes:
             src = iframe.get('src')
             if src: candidates.append(src)
        
        # Known providers logic
        providers_map = {
            'hglink.to': 'hglink',
            'hglink.com': 'hglink',
            'haxloppd.com': 'hglink', # Mirror
            'myvidplay': 'myvidplay',
            'dood': 'doodstream',
            'ds2play': 'doodstream',
            'streamtape': 'streamtape',
            'voe.sx': 'voe',
            'mixdrop': 'mixdrop',
            'filemoon': 'filemoon',
            'callistanise': 'filemoon'
        }
        
        for c_url in candidates:
            # Fix protocol relative
            if c_url.startswith('//'): c_url = "https:" + c_url
            
            if c_url in unique_urls: continue
            if c_url == url or c_url == image: continue
            
            provider = None
            for key, val in providers_map.items():
                if key in c_url:
                    provider = val
                    break
            
            if provider:
                unique_urls.add(c_url)
                streams.append({'provider': provider, 'url': c_url})
                
        return {
            'title': title,
            'original_url': url,
            'image': image,
            'description': description,
            'streams': streams
        }

    except Exception as e:
        logger.error(f"Error getting details for {url}: {e}")
        return {'error': str(e)}
