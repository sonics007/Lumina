import logging
import re

def resolve_url(url):
    """
    Resolve direct stream URL from provider links (HGLink, StreamTape, etc.)
    Uses yt-dlp if available.
    """
    # Check if needs resolve
    NEEDS_RESOLVE = ['hglink', 'streamtape', 'dood', 'voe.sx', 'mixdrop', 'filemoon']
    
    if not any(x in url for x in NEEDS_RESOLVE):
        return url
        
    logging.info(f"Resolving provider URL: {url}")
    
    try:
        import yt_dlp
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'url' in info:
                logging.info(f"Resolved to: {info['url'][:50]}...")
                return info['url']
            elif 'entries' in info:
                # Playlist? Take first
                return info['entries'][0].get('url')
                
    except ImportError:
        logging.error("yt-dlp python library not found. Cannot resolve stream.")
    except Exception as e:
        logging.error(f"Resolver error for {url}: {e}")
        
    # If failed, return original (maybe player can handle it or it's already direct)
    return url
