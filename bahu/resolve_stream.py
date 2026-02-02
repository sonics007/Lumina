import logging
import requests
from bs4 import BeautifulSoup

def get_stream_url(session, page_url):
    """
    Scrapes the Bahu video page to find the direct MP4 stream URL from the <video> tag.
    """
    try:
        logging.info(f"Resolving stream for: {page_url}")
        r = session.get(page_url)
        if r.status_code != 200:
            logging.error(f"Failed to load page: {r.status_code}")
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Look for <video> tag
        video = soup.find('video')
        if video:
            source = video.find('source')
            if source and source.get('src'):
                stream_url = source.get('src')
                logging.info(f"Found MP4 stream (video tag): {stream_url}")
                return stream_url

        # Fallback: Look for any <source> tag with mp4
        sources = soup.find_all('source')
        for s in sources:
            src = s.get('src')
            if src and '.mp4' in src:
                logging.info(f"Found MP4 stream (fallback source): {src}")
                return src
        
        logging.warning("No video tag or source found.")
        return None
        
    except Exception as e:
        logging.error(f"Error resolving Bahu stream: {e}")
        return None
