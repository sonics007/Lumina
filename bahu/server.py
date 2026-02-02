from flask import Flask, Response, request, redirect
import json
import os
import sys
import logging

# Ensure we can find the extractor
try:
    import extractor
except ImportError:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import extractor

app = Flask(__name__)

# Config
DATA_FILE = "data.json"
PORT = 5002
HOST = "0.0.0.0"
PUBLIC_URL = f"http://127.0.0.1:{PORT}"

# Logging
logging.basicConfig(level=logging.INFO)

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

@app.route('/')
def index():
    count = len(load_data())
    return (f"<h1>Bahu.tv Server</h1>"
            f"<p>Movies in DB: {count}</p>"
            f"<p>Playlist URL: <a href='/playlist.m3u8'>{PUBLIC_URL}/playlist.m3u8</a></p>")

@app.route('/playlist.m3u8')
def playlist():
    """Generates a rich M3U8 playlist with metadata"""
    items = load_data()
    
    # Sort by Added Date (Newest first)
    # Assuming 'added_at' exists, otherwise fallback to index
    items.sort(key=lambda x: x.get('added_at', ''), reverse=True)
    
    m3u = "#EXTM3U\n"
    
    for item in items:
        # Normalize title: Strip non-ASCII to prevent VLC parsing errors on Windows
        raw_title = item.get('title', 'Unknown')
        title = raw_title.encode('ascii', 'ignore').decode().replace(',', ' -').replace('\n', ' ').strip()
        
        page_url = item.get('url')
        poster = item.get('poster', '')
        group = item.get('category', 'Movies')
        
        # Simple and standard M3U format
        m3u += f'#EXTINF:-1 tvg-logo="{poster}" group-title="{group}",{title}\n'
        
        # Stream URL points to our extractor
        m3u += f"{PUBLIC_URL}/watch?url={page_url}\n"
        
    return Response(m3u, mimetype='audio/x-mpegurl')

@app.route('/watch')
def watch():
    url = request.args.get('url')
    if not url:
        return "Missing URL", 400
        
    logging.info(f"Extracting stream for: {url}")
    
    # Run extractor
    # extractor.py uses headless chrome to get the real MP4 link
    try:
        stream_url = extractor.get_stream_url(url)
        if stream_url:
            logging.info(f"Redirecting to: {stream_url}")
            return redirect(stream_url, code=302)
        else:
            return "Could not extract video. Site changes or premium check failed.", 500
    except Exception as e:
        logging.error(f"Extraction error: {e}")
        return f"Error: {e}", 500

if __name__ == '__main__':
    print(f"Server running on {PUBLIC_URL}")
    app.run(host=HOST, port=PORT, threaded=True)
