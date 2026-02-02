from flask import Blueprint, request, Response, redirect, current_app
from ..models import db, Playlist
import requests
from ..services.extractor import get_stream_url
import time
from urllib.parse import quote, unquote, urljoin
import re

stream_bp = Blueprint('stream', __name__)

# Cache for streams
STREAM_CACHE = {} 
CACHE_DURATION = 3600 * 12

# FORCE IPv4 Global Fix (Fixes 'Read timed out' on Debian if IPv6 is broken/unreachable)
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
def allowed_gai_family():
    return socket.AF_INET
urllib3_cn.allowed_gai_family = allowed_gai_family


def get_scraper_session():
    try:
        from curl_cffi import requests as c_requests
        return c_requests.Session(impersonate="chrome110")
    except Exception as e:
        import requests
        s = requests.Session()
        s.headers.update({
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        })
        return s

DEFAULT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

@stream_bp.route('/watch')
def watch():
    import logging
    source_url = unquote(request.args.get('url'))
    pid = request.args.get('pid', 'default')
    
    logging.info(f"Watch Proxy Request: URL={source_url} PID={pid}")
    
    # --- LOGGING START ---
    try:
        from ..models import Movie
        movie = Movie.query.filter_by(url=source_url).first()
        title = movie.title if movie else "Unknown Content"
        
        # Console Log with flush for immediate output
        print(f"\n[PLAYBACK] 🎬 Starting: {title}", flush=True)
        print(f"[PLAYBACK] URL: {source_url}", flush=True)
        
        # History Log (if we can import it)
        try:
            from .main import log_history
            log_history("Watch", f"Started watching {title}")
        except ImportError:
            # Avoid circular import issues if main not initialized yet
            pass
        except Exception as e:
            print(f"[PLAYBACK] History log error: {e}", flush=True)
            
    except Exception as e:
        print(f"[PLAYBACK] Log error: {e}", flush=True)
    # --- LOGGING END ---
    
    # --- LOGGING END ---
    
    if not source_url: return "Missing URL", 400
    
    # 2. Extraction & Caching
    real_stream = None
    headers = {'User-Agent': DEFAULT_UA}
    
    # Check for direct file extensions or Xtream patterns BEFORE calling extractor
    is_direct = source_url.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.ts', '.m3u8', '.txt'))
    is_xtream = '/movie/' in source_url or '/series/' in source_url or '/live/' in source_url
    is_bahu = 'bahu.tv' in source_url.lower()
    
    if is_direct or is_xtream:
        logging.info(f"Direct/Xtream link detected, bypassing extractor: {source_url}")
        real_stream = source_url
        # Use simple cache just to store it was "resolved"
        STREAM_CACHE[source_url] = (real_stream, headers, time.time())
    
    elif is_bahu:
        # Use Bahu extractor
        logging.info(f"Bahu.tv link detected, using Bahu extractor: {source_url}")
        cached = STREAM_CACHE.get(source_url)
        if cached:
            url, h, ts = cached
            if time.time() - ts < CACHE_DURATION:
                real_stream = url
                headers = h
        
        if not real_stream:
            try:
                import sys
                import os
                # Add bahu directory to path
                bahu_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bahu')
                sys.path.insert(0, bahu_dir)
                import extractor as bahu_extractor
                
                # Extract stream URL
                stream_url = bahu_extractor.get_stream_url(source_url)
                
                if stream_url:
                    logging.info(f"Bahu extraction successful: {stream_url}")
                    real_stream = stream_url
                    STREAM_CACHE[source_url] = (real_stream, headers, time.time())
                else:
                    return "Bahu extraction failed", 404
                    
            except Exception as e:
                logging.error(f"Bahu extractor error: {e}")
                return f"Bahu Error: {e}", 500
    
    else:
        # Use Cache
        cached = STREAM_CACHE.get(source_url)
        if cached:
            url, h, ts = cached
            if time.time() - ts < CACHE_DURATION:
                real_stream = url
                headers = h
                
        if not real_stream:
            try:
               # Increase timeout
               import socket
               socket.setdefaulttimeout(30)
               
               res = get_stream_url(source_url)
               if res and res[0]:
                   real_stream, headers = res
                   STREAM_CACHE[source_url] = (real_stream, headers, time.time())
               else:
                   return "Extractor failed", 404
            except Exception as e:
                return f"Error: {e}", 500

    # 3. Proxying
    # 3. Proxying
    # 3. Proxying
    try:
        # Use standard requests for playback stability (curl_cffi can hang on stream=True in some envs)
        import requests as std_requests
        session = std_requests.Session()
        
        # Standard path (Probe first)
        max_retries = 2
        r = None
        
        print(f"[PLAYBACK] Probing stream ({max_retries} retries): {real_stream}", flush=True)
        
        for attempt in range(max_retries):
            try:
                # Use stream=True to handle large files and not download everything at once
                # BUT DISABLE for playlists (.m3u8/.txt) to prevent hanging/buffering issues on small files
                do_stream = True
                if real_stream and ('.m3u8' in real_stream or '.txt' in real_stream or '.urlset' in real_stream):
                    do_stream = False
                
                r = session.get(real_stream, headers=headers, timeout=30, stream=do_stream, verify=False)
                print(f"[PLAYBACK] Probe attempt {attempt+1}: Status {r.status_code}", flush=True)
                if r.status_code < 400:
                    break
                else:
                    print(f"[PLAYBACK] Probe failed with status {r.status_code}", flush=True)
            except Exception as e:
                print(f"[PLAYBACK] Probe Error (attempt {attempt+1}): {e}", flush=True)
                if attempt == max_retries - 1: return f"Fetch Error: {e}", 502
                time.sleep(1)
        
        if not r: return "Fetch Error", 502

        # Safe header access
        ct_header = r.headers.get('Content-Type', '')
        ct = ct_header.lower() if ct_header else ''
        
        force_video = request.args.get('force_video', 'false').lower() == 'true'
        
        # Logic to determine if it is a binary video stream
        is_video_content = 'video/' in ct or 'application/octet-stream' in ct
        is_hls_content = 'mpegurl' in ct or 'x-mpegurl' in ct
        
        if force_video and not is_hls_content:
             is_video_content = True
        
        # If we identified it as a direct file earlier (.mp4, .mkv), trust that over headers if ambiguous
        if is_direct and not is_hls_content:
            is_video_content = True
            if not ct or 'text' in ct:
                ct = 'video/mp4' # Default fallback
        
        # If video/mp4, stream it with Range support
        if is_video_content and not is_hls_content:
            r.close() # Close probe
            
            # Forward Range header
            req_headers = {k:v for k,v in headers.items()}
            client_range = request.headers.get('Range')
            if client_range:
                req_headers['Range'] = client_range
                
            r_vid = session.get(real_stream, headers=req_headers, timeout=60, stream=True, verify=False)
            
            resp_headers = {}
            for key in ['Content-Range', 'Content-Length', 'Accept-Ranges']:
                 if key in r_vid.headers:
                     resp_headers[key] = r_vid.headers[key]
            
            # Force inline disposition so player plays it instead of downloading
            resp_headers['Content-Disposition'] = 'inline'

            def generate_stream():
                # Use larger chunk size for video performance
                for chunk in r_vid.iter_content(chunk_size=65536):
                    yield chunk
                    
            return Response(generate_stream(), status=r_vid.status_code, mimetype=ct, headers=resp_headers)

        # If m3u8, rewrite it
        content_bytes = b""
        for chunk in r.iter_content(chunk_size=4096):
            if chunk: content_bytes += chunk
            
        content = content_bytes.decode('utf-8', errors='ignore')
        base_url = r.url
        referer = headers.get('Referer', source_url)
        
        # Rewrite Logic
        new_lines = []
        uri_pattern = re.compile(r'URI="([^"]+)"')
        
        # We need to point to /api/segment or similar. 
        # Since this is a blueprint 'stream', the route is '/segment' if registered at root, 
        # or '.../segment' if registered with prefix.
        # In __init__.py we registered stream_bp at root? No, we didn't specify prefix, so it is at root.
        
        # Determine current host for rewriting
        host = request.host_url.rstrip('/') # http://127.0.0.1:5555
        
        def replace_uri(match):
            full = urljoin(base_url, match.group(1))
            return f'URI="{host}/segment?url={quote(full)}&ref={quote(referer)}"'
            
        for line in content.split('\n'):
            line = line.strip()
            if not line: continue

            if line.startswith('#'):
                if 'URI="' in line:
                    line = uri_pattern.sub(replace_uri, line)
                new_lines.append(line)
            else:
                full = urljoin(base_url, line)
                proxy = f"{host}/segment?url={quote(full)}&ref={quote(referer)}"
                new_lines.append(proxy)
                
        resp = Response('\n'.join(new_lines), mimetype='application/vnd.apple.mpegurl')
        resp.headers['Cache-Control'] = 'no-cache'
        return resp
        
    except Exception as e:
        return f"Stream Error: {e}", 502

@stream_bp.route('/segment')
def segment():
    import logging
    target = unquote(request.args.get('url'))
    ref = unquote(request.args.get('ref', ''))
    
    # Verbose logging can be spammy for segments, but useful for debugging simple issues
    logging.info(f"Segment Request: URL={target}")
    
    headers = {'User-Agent': DEFAULT_UA, 'Referer': ref}
    
    try:
        # Use standard requests
        import requests as std_requests
        session = std_requests.Session()
        r = session.get(target, headers=headers, stream=True, timeout=30, verify=False)
        
        ct = r.headers.get('Content-Type', '').lower()
        
        # If it's a nested playlist (variant stream or encryption key), rewrite it too
        if target.endswith(('.m3u8','.txt','.urlset')) or 'mpegurl' in ct:
             content_bytes = b""
             for chunk in r.iter_content(chunk_size=4096):
                 if chunk: content_bytes += chunk
             content = content_bytes.decode('utf-8', errors='ignore')
             
             base_url = r.url
             host = request.host_url.rstrip('/')
             new_lines = []
             uri_pattern = re.compile(r'URI="([^"]+)"')
             
             for line in content.split('\n'):
                 line = line.strip()
                 if not line: continue
                 if line.startswith('#'):
                     if 'URI="' in line:
                         line = uri_pattern.sub(
                             lambda m: f'URI="{host}/segment?url={quote(urljoin(base_url, m.group(1)))}&ref={quote(ref)}"', 
                             line
                         )
                     new_lines.append(line)
                 else:
                     full = urljoin(base_url, line)
                     proxy = f"{host}/segment?url={quote(full)}&ref={quote(ref)}"
                     new_lines.append(proxy)
                     
             return Response('\n'.join(new_lines), mimetype='application/vnd.apple.mpegurl')
        
        # Binary content (segment TS, Key, etc.)
        # Fix MIME for TS if generic
        if target.lower().endswith('.ts') and ('video' not in ct and 'mpegurl' not in ct):
            ct = 'video/mp2t'

        def generate():
            # Increased chunk size for performance
            for chunk in r.iter_content(chunk_size=65536):
                 yield chunk
                 
        resp = Response(generate(), mimetype=ct)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
        
    except Exception as e:
        return f"Segment Error: {e}", 502
