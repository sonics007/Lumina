import client
import logging

def get_stream_url(url):
    """
    Get stream URL using the authenticated BahuClient.
    Auto-logs in if needed.
    """
    # Simply use the singleton client instance
    # It keeps session.
    
    # We might want to ensure login first?
    # Usually session persists, but let's be lazy-safe:
    # If extraction fails, maybe re-login?
    
    # For now, simplistic approach:
    # Ensure login once at start (handled by server init potentially, or here lazy)
    
    # Try to extract
    vid = client.CLIENT.get_video_url(url)
    
    if not vid:
        logging.info("URL not found, maybe session expired? Attempting login...")
        if client.CLIENT.login():
            vid = client.CLIENT.get_video_url(url)
            
    return vid

if __name__ == "__main__":
    print(get_stream_url("https://www.bahu.tv/film/minyonok"))
