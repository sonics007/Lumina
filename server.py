from flask import Flask, Response, redirect, request, render_template, url_for, flash
from app.services import extractor
import os
import subprocess
import requests
from curl_cffi import requests as c_requests

def get_scraper():
    return c_requests.Session(impersonate="chrome110")

import time
import logging
import sys
import traceback
import json
import datetime
from urllib.parse import quote, unquote, urljoin

# Add parent dir for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from providers_config import PROVIDERS
except ImportError:
    PROVIDERS = {}

# Add parent dir for scraping tool
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uiiu_data'))
try:
    from scrape_top100 import get_movie_details
except ImportError as e:
    print(f"Warning: Could not import scraper: {e}")
    # Dummy function backup
    def get_movie_details(url): return {'error': 'Scraper not available'}

try:
    from scrape_uiiu import scrape_single_movie
except ImportError:
    def scrape_single_movie(u): return {}

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me' # Required for flashing

# Logging setup
# Logging setup
# File Handler
file_handler = logging.FileHandler('server_log.txt', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

# Console Handler (StreamHandler)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

logging.getLogger().setLevel(logging.INFO)
requests.packages.urllib3.disable_warnings()

# Config
DB_FILE = 'movies_db.json'
HISTORY_FILE = 'history.json'
CONFIG_FILE = 'scraper_config.json'
PLAYLISTS_FILE = 'playlists.json'
UNKNOWN_FILE = 'nezname_providery.txt'
BROKEN_FILE = 'not_working_providers.txt'
HOST = '0.0.0.0'
PORT = 5001

START_TIME = time.time()
STREAM_CACHE = {}
CACHE_DURATION = 3600 * 12
IP_COUNTRY_CACHE = {}

DEFAULT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# --- HELPERS ---

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERROR loading DB: {e}")
            return []
    return []

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_playlists():
    if os.path.exists(PLAYLISTS_FILE):
        try:
            with open(PLAYLISTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    # Default if missing
    return [{"id": "default", "name": "Default Public", "max_connections": 0, "allowed_countries": ""}]

def save_playlists(data):
    with open(PLAYLISTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def log_history(action, content="", playlist=""):
    try:
        entry = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": request.remote_addr,
            "action": action,
            "content": content,
            "playlist": playlist,
            "ua": request.headers.get('User-Agent', '')
        }
        
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        
        history.insert(0, entry) # Add to top
        history = history[:100] # Keep last 100
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"History Log Error: {e}")

def get_uptime():
    seconds = int(time.time() - START_TIME)
    return str(datetime.timedelta(seconds=seconds))

def get_country_by_ip(ip):
    if ip == '127.0.0.1': return 'LO' # Localhost
    if ip in IP_COUNTRY_CACHE: return IP_COUNTRY_CACHE[ip]
    
    try:
        r = requests.get(f'http://ip-api.com/json/{ip}', timeout=1.5)
        if r.status_code == 200:
            data = r.json()
            cc = data.get('countryCode', 'XX')
            IP_COUNTRY_CACHE[ip] = cc
            return cc
    except:
        pass
    return 'XX' # Unknown

def check_active_connections(pid, limit):
    if limit <= 0: return True # Unlimited
    
    # Calculate active clients for this PID from history (last 5 mins)
    # Simple heuristic
    active_ips = set()
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: history = json.load(f)
        
    cutoff = datetime.datetime.now() - datetime.timedelta(minutes=5)
    
    for h in history:
        try:
            t = datetime.datetime.strptime(h['time'], "%Y-%m-%d %H:%M:%S")
            if t > cutoff and h.get('action') == 'Watch' and h.get('playlist') == pid:
                active_ips.add(h['ip'])
        except: pass
        
    # Check current requesting IP too (if not already counted)
    # Actually, allow if current IP is already active or if count < limit
    current_ip = request.remote_addr
    if current_ip in active_ips: return True
    
    return len(active_ips) < limit

@app.context_processor
def inject_latest_movies():
    try:
        movies = load_db()
        latest = movies[-15:]
        latest.reverse()
        return dict(latest_movies=latest)
    except:
        return dict(latest_movies=[])

# --- ROUTES: WEB INTERFACE ---

@app.route('/')
def dashboard():
    movies = load_db()
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: history = json.load(f)
    
    active_clients = set()
    one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
    for h in history:
        try:
            t = datetime.datetime.strptime(h['time'], "%Y-%m-%d %H:%M:%S")
            if t > one_hour_ago:
                active_clients.add(h['ip'])
        except: pass
        
    return render_template('index.html', title="Dashboard", active_page='home',
                           movie_count=len(movies), active_clients_count=len(active_clients),
                           provider_count=len(PROVIDERS), uptime=get_uptime(), history=history)

@app.route('/playlist')
def playlist_page():
    movies = load_db()
    return render_template('playlist.html', title="DB Filmov", active_page='playlist', movies=movies)

@app.route('/player')
def player_page():
    url = request.args.get('url')
    return render_template('player.html', title="Player", active_page='player', url=url)



@app.route('/manage_playlists')
def manage_playlists():
    playlists = load_playlists()
    edit_id = request.args.get('edit')
    edit_pl = None
    if edit_id:
        for p in playlists:
            if p['id'] == edit_id:
                edit_pl = p
                break
    return render_template('manage_playlists.html', title="Správa Playlistov", active_page='manage_playlists', playlists=playlists, edit_pl=edit_pl)

@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    playlists = load_playlists()
    old_id = request.form.get('old_id')
    new_id = request.form.get('id').strip()
    name = request.form.get('name')
    max_conn = int(request.form.get('max_connections', 0))
    countries = request.form.get('allowed_countries', '').strip()
    
    if old_id:
        # Edit existing
        for p in playlists:
            if p['id'] == old_id:
                p['name'] = name
                # p['id'] = new_id # Don't change ID easily to avoid breaking links
                p['max_connections'] = max_conn
                p['allowed_countries'] = countries
                break
    else:
        # Create new
        # Check if ID exists
        if any(p['id'] == new_id for p in playlists):
            return "Playlist ID already exists!", 400
            
        playlists.append({
            "id": new_id,
            "name": name,
            "max_connections": max_conn,
            "allowed_countries": countries
        })
        
    save_playlists(playlists)
    return redirect(url_for('manage_playlists'))

@app.route('/delete_playlist')
def delete_playlist():
    pid = request.args.get('id')
    if pid == 'default': return "Cannot delete default playlist", 403
    
    playlists = load_playlists()
    playlists = [p for p in playlists if p['id'] != pid]
    save_playlists(playlists)
    return redirect(url_for('manage_playlists'))

@app.route('/webs')
def webs_page():
    config = {"urls": []}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: config = json.load(f)
    return render_template('webs.html', title="Scrapers", active_page='webs', sites=config['urls'])

@app.route('/add_site', methods=['POST'])
def add_site():
    config = {"urls": [], "settings": {}}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: config = json.load(f)
    config['urls'].append({"name": request.form['name'], "url": request.form['url'], "last_scraped": "Never"})
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f, indent=2)
    return redirect(url_for('webs_page'))

@app.route('/run_scrape')
def run_scrape():
    import subprocess
    try:
        subprocess.Popen([sys.executable, 'scraper_advanced.py'], cwd=app.root_path)
        log_history("System", "Started Manual Scrape")
        return {"status": "success", "message": "Scraper bol spustený na pozadí!"}
    except Exception as e: return {"status": "error", "message": f"Chyba: {e}"}

@app.route('/clients')
def clients_page():
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: history = json.load(f)
    return render_template('clients.html', title="Clients", active_page='clients', history=history)

@app.route('/settings')
def settings_page():
    movies = load_db()
    return render_template('settings.html', title="Settings", active_page='settings', db_size=len(movies))

# --- NEW ROUTES FOR MENU ---

@app.route('/source_movies')
def source_movies():
    source = request.args.get('source', '')
    all_movies = load_db()
    filtered = []
    for i, m in enumerate(all_movies):
        if m.get('source', 'film-adult') == source:
            m_copy = m.copy()
            m_copy['original_index'] = i
            filtered.append(m_copy)
    return render_template('playlist.html', title=f"Movies from {source}", active_page='source_movies', movies=filtered)

@app.route('/new_movies')
def new_movies_page():
    all_movies = load_db()
    # Preserve indices for delete/edit actions
    indexed = []
    for i, m in enumerate(all_movies):
        m_copy = m.copy()
        m_copy['original_index'] = i
        indexed.append(m_copy)
        
    latest = indexed[-50:]
    latest.reverse()
    return render_template('playlist.html', title="New Movies (Last 50)", active_page='new_movies', movies=latest)

@app.route('/unknown_providers')
def unknown_providers():
    content = ""
    if os.path.exists(UNKNOWN_FILE):
        try:
            with open(UNKNOWN_FILE, 'r', encoding='utf-8') as f: content = f.read()
        except: pass
    return render_template('file_list.html', title="Unknown Providers", active_page='unknown', content=content, allow_clear=True, clear_url='/clear_unknown')

@app.route('/broken_providers')
def broken_providers():
    content = ""
    if os.path.exists(BROKEN_FILE):
        try:
           with open(BROKEN_FILE, 'r', encoding='utf-8') as f: content = f.read()
        except: pass
    return render_template('file_list.html', title="Broken Providers", active_page='broken', content=content, allow_clear=False)

@app.route('/clear_unknown')
def clear_unknown():
    try:
        open(UNKNOWN_FILE, 'w').close()
    except: pass
    return redirect(url_for('unknown_providers'))

@app.route('/providers')
def providers_page():
    movies = load_db()
    provider_stats = {}
    
    # Define aliases/groups mapping
    aliases = {
        'myvidplay.com': 'DoodStream (Merged)',
        'dood.to': 'DoodStream (Merged)',
        'dood.so': 'DoodStream (Merged)',
        'doodstream.com': 'DoodStream (Merged)',
        'auvexiug.com': 'DoodStream (Merged)',
        's2.filmcdn.top': 'FilmCDN (Merged)',
        'filmcdn.top': 'FilmCDN (Merged)',
        'cfglobalcdn.com': 'FilmCDN (Merged)',
        'hglink.to': 'HGLink'
    }

    # Init stats based on PROVIDERS config
    for p, conf in PROVIDERS.items():
        # Determine display key (group name) or default to domain
        key = aliases.get(p, p)
        
        if key not in provider_stats:
            provider_stats[key] = {
                'domain': key,
                'count': 0, 
                'status': 'Active', 
                'ref': conf.get('referer', 'N/A') # Shows referer of the first encountered member
            }
        
    # Count usage in DB
    for m in movies:
        for s in m.get('streams', []):
            prov = s.get('provider')
            if prov:
                found_key = None
                
                # Check match against all raw provider keys defined in config
                for p_key in PROVIDERS:
                    if p_key in prov or prov in p_key:
                        # If matched, convert to alias/group name
                        found_key = aliases.get(p_key, p_key)
                        break
                
                # If still not found, maybe the provider name in DB is already the group name?
                if not found_key and prov in provider_stats:
                    found_key = prov

                if found_key and found_key in provider_stats:
                    provider_stats[found_key]['count'] += 1
                        
    return render_template('providers.html', title="Providers", active_page='providers', stats=provider_stats)

@app.route('/restart')
def restart_server():
    log_history("System", "Restart Request")
    os.execl(sys.executable, sys.executable, *sys.argv)

@app.route('/clean_db')
def clean_db_route():
    import subprocess
    # Run simple script to empty DB or just overwrite it
    save_db([])
    log_history("System", "Database Cleaned (Emptied)")
    return redirect(url_for('settings_page'))

# --- ROUTES: STREAMING ---

@app.route('/stream.m3u8')
@app.route('/playlist.m3u')
def playlist_alias():
    return playlist_m3u8()

@app.route('/playlist.m3u8')
def playlist_m3u8():
    pid = request.args.get('id', 'default')
    
    # Validation
    playlists = load_playlists()
    pl_config = next((p for p in playlists if p['id'] == pid), None)
    
    if not pl_config:
        # Fallback to default if unknown? Or 404? 
        return "Playlist not found", 404
        
    log_history("Playlist", f"Requested playlist: {pid} ({pl_config['name']})", playlist=pid)
    
    # GeoIP Check (Only on playlist load? Or on watch? Better on watch, but here too)
    client_ip = request.remote_addr
    allowed_countries = pl_config.get('allowed_countries', '')
    if allowed_countries:
        country = get_country_by_ip(client_ip)
        allowed_list = [c.strip().upper() for c in allowed_countries.split(',')]
        if country not in allowed_list:
            return f"Access Denied for Country: {country}", 403

    movies = load_db()
    m3u = "#EXTM3U\n"
    
    for m in movies:
        title = m.get('title', 'Unknown')
        image = m.get('image', '')
        streams = m.get('streams', [])
        
        for s in streams:
            provider = s.get('provider', 'Unknown')
            name = f"{title} [{provider}]"
            url = s.get('url')
            
            logo = f'tvg-logo="{image}"' if image else ""
            m3u += f'#EXTINF:-1 group-title="Adult" {logo},{name}\n'
            # Add PID to watch URL
            # Revert to standard quote (safe='/') as it worked before
            link = f"http://127.0.0.1:{PORT}/watch?url={quote(url)}&pid={pid}"
            m3u += f"{link}\n"
            
        if not streams and 'url' in m:
             m3u += f'#EXTINF:-1 group-title="Legacy",{title}\n'
             link = f"http://127.0.0.1:{PORT}/watch?url={quote(m['url'])}&pid={pid}"
             m3u += f"{link}\n"
             
    return Response(m3u, mimetype='audio/x-mpegurl')

@app.route('/watch')
def watch():
    source_url = unquote(request.args.get('url'))
    try:
        print(f"DEBUG: Watch URL Raw: {source_url!r}")
    except: 
        pass
    pid = request.args.get('pid', 'default')
    
    if not source_url: return "Missing URL", 400

    # Load Playlist Config
    playlists = load_playlists()
    pl_config = next((p for p in playlists if p['id'] == pid), None)
    
    if pl_config:
        # 1. GeoIP Check
        client_ip = request.remote_addr
        allowed_countries = pl_config.get('allowed_countries', '')
        if allowed_countries:
            country = get_country_by_ip(client_ip)
            allowed_list = [c.strip().upper() for c in allowed_countries.split(',')]
            if country not in allowed_list:
                log_history("Block", f"GeoIP Block ({country}) for stream: {source_url}", playlist=pid)
                return "GeoIP Blocked", 403

        # 2. Max Connections Check
        max_conn = int(pl_config.get('max_connections', 0))
        if not check_active_connections(pid, max_conn):
             log_history("Block", f"Max Connections Limit ({max_conn}) Reached", playlist=pid)
             return "Max Connections Reached", 429
    
    log_history("Watch", f"Started stream: {source_url}", playlist=pid)

    # --- Cache Check ---
    real_stream = None
    headers = {}
    
    cached = STREAM_CACHE.get(source_url)
    if cached:
        url, h, ts = cached
        if time.time() - ts < CACHE_DURATION:
            real_stream = url
            headers = h
            
    if not real_stream:
        try:
            # Increase timeout for extraction (some providers are slow)
            import socket
            socket.setdefaulttimeout(30)
            
            res = extractor.get_stream_url(source_url)
            if res and res[0]:
                real_stream, headers = res
                STREAM_CACHE[source_url] = (real_stream, headers, time.time())
            else:
                return "Extractor failed", 404
        except Exception as e:
            return f"Error: {e}", 500

    # Fetch Master Playlist
    # Use FRESH session for every request to avoid threading crashes with curl_cffi
    scraper_session = c_requests.Session(impersonate="chrome120")
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"Fetching source (attempt {attempt+1}/{max_retries}): {real_stream[:100]}...")
            
            # Initial fetch to get content (not stream=True for playlist)
            r = scraper_session.get(real_stream, headers=headers, timeout=30, verify=False)
            
            # Check content type for direct video stream
            ct = r.headers.get('Content-Type', '').lower()
            if 'video/' in ct and 'mpegurl' not in ct and 'x-mpegurl' not in ct:
                print(f"Direct video stream detected ({ct}), proxying with Range support...")
                
                # Forward Range header
                req_headers = {k:v for k,v in headers.items()}
                client_range = request.headers.get('Range')
                if client_range:
                    req_headers['Range'] = client_range
                
                # Re-request stream with range (stream=True)
                r_vid = scraper_session.get(real_stream, headers=req_headers, timeout=60, stream=True, verify=False)
                
                # Copy headers
                resp_headers = {}
                for key in ['Content-Range', 'Content-Length', 'Accept-Ranges']:
                    if key in r_vid.headers:
                        resp_headers[key] = r_vid.headers[key]
                        
                return Response(
                    r_vid.iter_content(chunk_size=32768), 
                    status=r_vid.status_code,
                    mimetype=ct,
                    headers=resp_headers
                )
            
            # Playlist content
            content_bytes = r.content
            
            try:
                content = content_bytes.decode('utf-8', errors='ignore')
            except:
                content = ""
            
            # Auto-detect HTML error
            if not content.strip().startswith('#EXTM3U') and 'html' in ct:
                logging.error(f"Got HTML instead of HLS: {content[:200]}")
                return Response("Proxy Error: Source returned HTML (blocked?)", status=502)

            print(f"DEBUG: Playlist Content START ({len(content)} chars)")
            base_url = r.url
            referer = headers.get('Referer', source_url)
            break  # Success
            
        except Exception as e:
            print(f"Fetch error: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return f"Fetch Error: {e}", 502
    else:
        return f"Fetch Error: Max retries exceeded", 502
        
    # Rewrite Logic
    try:
        new_lines = []
        import re
        uri_pattern = re.compile(r'URI="([^"]+)"')
        
        # Use host from request to handle local IP network access
        host_base = request.host_url.rstrip('/')
        
        def replace_uri(match):
            full = urljoin(base_url, match.group(1))
            return f'URI="{host_base}/segment?url={quote(full)}&ref={quote(referer)}"'
            
        for line in content.split('\n'):
            line = line.strip()
            if not line: continue

            if line.startswith('#'):
                if 'URI="' in line:
                    line = uri_pattern.sub(replace_uri, line)
                new_lines.append(line)
            else:
                full = urljoin(base_url, line)
                proxy = f"{host_base}/segment?url={quote(full)}&ref={quote(referer)}"
                new_lines.append(proxy)
                
        resp = Response('\n'.join(new_lines), mimetype='application/vnd.apple.mpegurl')
        resp.headers['Cache-Control'] = 'no-cache'
        return resp

    except Exception as e:
        print(f"ERROR in /watch rewrite: {e}")
        import traceback
        traceback.print_exc()
        return f"Fetch/Rewrite Error: {e}", 502

@app.route('/segment')
def segment():
    target = unquote(request.args.get('url'))
    ref = unquote(request.args.get('ref', ''))
    
    headers = {'User-Agent': DEFAULT_UA, 'Referer': ref}
    
    # FRESH session for segments
    scraper_session = c_requests.Session(impersonate="chrome120")
    
    try:
        r = scraper_session.get(target, headers=headers, stream=True, timeout=60, verify=False)
        
        if target.endswith(('.m3u8','.txt','.urlset')) or 'mpegurl' in r.headers.get('Content-Type',''):
             # Playlist segment/sub-playlist
             content_bytes = b""
             # Safe read
             if hasattr(r, 'iter_content'):
                 for chunk in r.iter_content(chunk_size=4096):
                     if chunk: content_bytes += chunk
             else:
                 content_bytes = r.content

             
             content = content_bytes.decode('utf-8', errors='ignore')
             base_url = r.url
             new_lines = []
             import re
             uri_pattern = re.compile(r'URI="([^"]+)"')
             
             for line in content.split('\n'):
                 line = line.strip()
                 if not line: continue
                 if line.startswith('#'):
                     if 'URI="' in line:
                         line = uri_pattern.sub(
                             lambda m: f'URI="http://127.0.0.1:{PORT}/segment?url={quote(urljoin(base_url, m.group(1)))}&ref={quote(ref)}"', 
                             line
                         )
                     new_lines.append(line)
                 else:
                     full = urljoin(base_url, line)
                     proxy = f"http://127.0.0.1:{PORT}/segment?url={quote(full)}&ref={quote(ref)}"
                     new_lines.append(proxy)
                     
             return Response('\n'.join(new_lines), mimetype='application/vnd.apple.mpegurl')
        
        return Response(r.iter_content(chunk_size=8192), mimetype=r.headers.get('Content-Type'))
        
    except Exception as e:
        return f"Segment Error: {e}", 502

@app.route('/add_movie')
def add_movie_page():
    return render_template('add_movie.html', title="Add Movie", active_page='add_movie')

@app.route('/analyze_movie', methods=['POST'])
def analyze_movie():
    url = request.form.get('url')
    if not url: return {"error": "Missing URL"}, 400
    
    try:
        if 'uiiumovie' in url:
             data = scrape_single_movie(url)
             if not data: return {"error": "Failed to scrape UIIU url"}, 500
             if not data.get('description'): data['description'] = ''
             return data

        data = get_movie_details(url)
        return data  # Returns JSON
    except Exception as e:
        print(f"Analyze error: {e}")
        return {"error": str(e)}, 500

@app.route('/save_analyzed_movie', methods=['POST'])
def save_analyzed_movie():
    try:
        title = request.form.get('title')
        url = request.form.get('url')
        image = request.form.get('image')
        desc = request.form.get('description')
        stream_url = request.form.get('stream_url')
        provider = request.form.get('provider')
        source = request.form.get('source')
        
        if not title or not url or not stream_url:
            return "Missing mandatory fields", 400
            
        new_entry = {
            "title": title,
            "url": url,
            "image": image,
            "description": desc,
            "source": source,
            "streams": [
                {
                    "provider": provider,
                    "url": stream_url
                }
            ]
        }
        
        db = load_db()
        # Check duplicates and update if exists
        updated = False
        for i, m in enumerate(db):
            if m['url'] == url: # Allow title dupes (remakes), unique URL
                print(f"Updating existing movie: {title}")
                db[i]['title'] = title
                db[i]['image'] = image
                db[i]['description'] = desc
                if source: db[i]['source'] = source
                # Overwrite stream with new selection
                db[i]['streams'] = [{
                    "provider": provider,
                    "url": stream_url
                }]
                updated = True
                break
                
        if not updated:
            db.append(new_entry)
        save_db(db)
        log_history("Add", f"Manual add: {title} ({provider})", playlist="manual")
        
        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/delete_movie/<int:index>', methods=['GET', 'POST'])
def delete_movie(index):
    try:
        app.logger.info(f"DEBUG: DELETE Request for index {index}")
        db = load_db()
        app.logger.info(f"DEBUG: DB size loaded: {len(db)}")
        if 0 <= index < len(db):
            title = db[index].get('title', 'Unknown')
            app.logger.info(f"DEBUG: Deleting movie: {title}")
            del db[index]
            save_db(db)
            app.logger.info("DEBUG: DB saved.")
            log_history("Delete", f"Deleted movie: {title}")
            import time
            time.sleep(0.2) # Ensure file system sync
        else:
            app.logger.info(f"DEBUG: Index {index} out of range (0-{len(db)-1})")
        return redirect('/playlist')
    except Exception as e:
        app.logger.error(f"Error deleting movie: {e}")
        return f"Error: {e}", 500

@app.route('/edit_movie/<int:index>')
def edit_movie_page(index):
    try:
        db = load_db()
        if 0 <= index < len(db):
            return render_template('edit_movie.html', movie=db[index], index=index, title="Edit Movie")
        return "Movie not found", 404
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/update_movie/<int:index>', methods=['POST'])
def update_movie(index):
    try:
        db = load_db()
        if not (0 <= index < len(db)):
            return "Movie not found", 404
            
        m = db[index]
        m['title'] = request.form.get('title')
        m['image'] = request.form.get('image')
        m['description'] = request.form.get('description')
        # Update Source Page URL if provided (important for refresh)
        if request.form.get('movie_url'):
            m['url'] = request.form.get('movie_url')
        
        # Update streams
        new_streams = []
        i = 0
        while True:
            prov = request.form.get(f'provider_{i}')
            url_str = request.form.get(f'stream_url_{i}')
            if prov is None: break
            if prov and url_str: # Keep valid only
                 new_streams.append({'provider': prov, 'url': url_str})
            i += 1
            
        # Check new stream
        new_prov = request.form.get('new_provider')
        new_url = request.form.get('new_stream_url')
        if new_prov and new_url and new_prov != 'manual':
             new_streams.append({'provider': new_prov, 'url': new_url})
             
        if new_streams:
            m['streams'] = new_streams
        
        # If no streams remain but we have image/title, keep entry but maybe set error?
        # Assuming user knows what they do.
            
        save_db(db)
        log_history("Update", f"Updated movie: {m['title']}")
        return redirect('/playlist')
        
    except Exception as e:
        return f"Error: {e}", 500


# Import Functionality
def load_ignored():
    if not os.path.exists('ignored_movies.json'):
        return []
    try:
        with open('ignored_movies.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_ignored(ignored_list):
    with open('ignored_movies.json', 'w', encoding='utf-8') as f:
        json.dump(ignored_list, f, indent=2)

@app.route('/import_movies')
def import_movies_page():
    # Try multiple paths for the scraped file
    paths = [
        os.path.join('scraped_data', 'film_adult_movies_en.json'),
        'film_adult_movies_en.json',
        'film_adult_movies.json'
    ]
    
    scraped_path = None
    for p in paths:
        if os.path.exists(p):
            scraped_path = p
            break
            
    if not scraped_path:
        return f'''
        <div style="font-family:sans-serif; padding:50px; text-align:center; background:#121212; color:white;">
            <h1>Scraped Data Not Found</h1>
            <p>Please run the scraper script first:</p>
            <pre style="background:#333; padding:10px; display:inline-block;">python link_scrappers/scrape_film_adult_full.py</pre>
            <br><br>
            <a href="/" style="color:#aaa;">Back to Dashboard</a>
        </div>
        '''
        
    with open(scraped_path, 'r', encoding='utf-8') as f:
        scraped_movies = json.load(f)
        
    db = load_db()
    
    # Existing URLs from DB + Pending/Processing logic could be here
    existing_urls = set(m.get('url','') for m in db)
    ignored = set(load_ignored())
    
    candidates = []
    count = 0
    
    for m in scraped_movies:
        if m['url'] and m['url'] not in existing_urls and m['url'] not in ignored:
            candidates.append(m)
            count += 1
            if count >= 50: break 
            
    remaining_count = len(scraped_movies) - len(existing_urls) - len(ignored) - len(candidates)
    if remaining_count < 0: remaining_count = 0
    
    return render_template('import_movies.html', movies=candidates, remaining=remaining_count)

@app.route('/ignore_movie', methods=['POST'])
def ignore_movie():
    url = request.form.get('url')
    if url:
        ignored = load_ignored()
        if url not in ignored:
            ignored.append(url)
            save_ignored(ignored)
    return 'OK'

@app.route('/sources/film-adult-manage')
def source_film_adult_manage():
    # Gather stats
    scrape_path = os.path.join('adult_film_data', 'data', 'film_adult_movies_en.json')
    scrape_size = "N/A"
    scrape_time = "Never"
    if os.path.exists(scrape_path):
        try:
            size_mb = os.path.getsize(scrape_path) / (1024*1024)
            scrape_size = f"{size_mb:.2f} MB"
            mtime = os.path.getmtime(scrape_path)
            scrape_time = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except: pass
        
    return render_template('sources_film_adult.html', 
                          title="Manage: film-adult.top", 
                          active_page='film_adult_manage',
                          scrape_size=scrape_size,
                          scrape_time=scrape_time)

@app.route('/sources/uiiu-manage')
def source_uiiu_manage():
    # Gather stats
    scrape_path = os.path.join('uiiu_data', 'data', 'uiiu_movies.json')
    scrape_size = "N/A"
    scrape_time = "Never"
    if os.path.exists(scrape_path):
        try:
            size_mb = os.path.getsize(scrape_path) / (1024*1024)
            scrape_size = f"{size_mb:.2f} MB"
            mtime = os.path.getmtime(scrape_path)
            scrape_time = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        except: pass
        
    return render_template('sources_uiiu.html', 
                          title="Manage: uiiumovie.com", 
                          active_page='uiiu_manage',
                          scrape_size=scrape_size,
                          scrape_time=scrape_time)

@app.route('/api/run_script/<script_type>', methods=['POST'])
def run_script_api_route(script_type):
    # Map types to scripts
    scripts = {
        'scrape': ['python', os.path.join('adult_film_data', 'scrape_film_adult_full.py')],
        'import1': ['python', os.path.join('adult_film_data', '1_import_myvidplay.py')],
        'import2': ['python', os.path.join('adult_film_data', '2_import_hglink.py')],
        'clean': ['python', os.path.join('debug_dev', 'clean_broken_links.py')],
        'uiiu_scrape': ['python', os.path.join('uiiu_data', 'scrape_uiiu.py')],
        'uiiu_import': ['python', os.path.join('uiiu_data', 'import_uiiu.py')]
    }
    
    if script_type not in scripts:
        return Response(json.dumps({'status': 'error', 'message': 'Unknown script type'}), mimetype='application/json'), 400
        
    cmd = scripts[script_type]
    
    try:
        # Run DETACHED process
        subprocess.Popen(cmd, cwd=os.getcwd(), creationflags=subprocess.CREATE_NEW_CONSOLE)
        return Response(json.dumps({'status': 'started', 'message': f'Script {script_type} started in new window.'}), mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({'status': 'error', 'message': str(e)}), mimetype='application/json'), 500

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()
    print(f"WEB DASHBOARD running at http://127.0.0.1:{PORT}")
    app.run(host=HOST, port=PORT, debug=True)
