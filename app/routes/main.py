from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session
from ..models import db, Movie, Stream, Playlist, History, SiteConfig
from ..services.history_service import log_history
import datetime
import os
import json
from urllib.parse import quote
from sqlalchemy import desc, or_, not_, func, and_

main_bp = Blueprint('main', __name__)

@main_bp.before_request
def require_login():
    # Public routes that don't need auth
    # static is handled by flask automatically usually, but let's be safe
    # xtream API must be public or have its own auth (it has check_auth)
    # stream routes might need to be public for players
    # api routes might need public access or token
    
    if request.endpoint == 'main.login': return
    if request.path.startswith('/static'): return
    if request.path.startswith('/api'): return
    # Xtream routes handled by their own auth logic or public
    if request.endpoint and 'xtream' in request.endpoint: return 
    # Stream routes (raw video)
    if request.endpoint and 'stream' in request.endpoint: return
    
    # Check session
    if 'user' not in session:
        return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Hardcoded Admin credentials as requested
        if username == 'admin' and password == 'admin':
            session['user'] = 'admin'
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid credentials. Please try again.')
            
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('main.login'))

# --- Helper Functions ---
# --- Helper Functions ---
# log_history is imported from services.history_service

@main_bp.context_processor
def inject_latest_movies():
    try:
        latest = Movie.query.order_by(desc(Movie.id)).limit(15).all()
        return dict(latest_movies=latest)
    except:
        return dict(latest_movies=[])

# --- Routes ---

@main_bp.route('/')
def dashboard():
    movie_count = Movie.query.count()
    # Active clients logic needs revision for DB, skipped for basic dash now
    active_clients_count = 0 
    provider_count = 0 # Need detailed query for this, skip for speed
    
    # Simple history fetch
    history = History.query.order_by(desc(History.time)).limit(10).all()
    
    return render_template('index.html', title="Dashboard", active_page='home',
                           movie_count=movie_count, active_clients_count=active_clients_count,
                           provider_count=provider_count, uptime="Running", history=history)


@main_bp.route('/movies')
@main_bp.route('/playlist') # Keep old route for compatibility
def playlist_page():
    q = request.args.get('q')
    tag = request.args.get('tag')
    
    # Exclude Live TV and Series based on tags AND source
    query = Movie.query.filter(
        not_(Movie.tags.ilike('%Live TV%')),
        not_(Movie.tags.ilike('%Series%')),
        not_(Movie.source.ilike('%:live')),
        not_(Movie.source.ilike('%:series'))
    )
    
    if q:
        query = query.filter(Movie.title.ilike(f'%{q}%'))
    if tag:
        query = query.filter(Movie.tags.ilike(f'%{tag}%'))
        
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    movies_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Extract Categories for Menu (VOD only)
    # Re-use base filter logic for consistent category list
    base_vod_filter = and_(
        not_(Movie.tags.ilike('%Live TV%')),
        not_(Movie.tags.ilike('%Series%')),
        not_(Movie.source.ilike('%:live')),
        not_(Movie.source.ilike('%:series'))
    )
    
    tags_data = Movie.query.with_entities(Movie.tags).filter(base_vod_filter).distinct().all()
    categories = set()
    for (t_str,) in tags_data:
        if t_str:
            parts = [x.strip() for x in t_str.split(',')]
            for p in parts:
                if p and p != 'Movies' and p != 'VOD': # Exclude generic tags
                    categories.add(p)
                    
    sorted_categories = sorted(list(categories))

    return render_template('playlist.html', title="Movies", active_page='movies', 
                           movies=movies_pagination.items, pagination=movies_pagination,
                           categories=sorted_categories, current_tag=tag)

@main_bp.route('/live')
def live_page():
    q = request.args.get('q')
    tag = request.args.get('tag')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Base Filters
    base_filter = or_(
        Movie.tags.ilike('%Live TV%'),
        Movie.source.ilike('%:live')
    )
    
    query = Movie.query.filter(base_filter)
    
    if q:
        query = query.filter(Movie.title.ilike(f'%{q}%'))
    if tag:
        # Filter by specific category tag
        query = query.filter(Movie.tags.ilike(f'%{tag}%'))
        
    movies_pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Extract Categories for Menu
    # Optimized: Fetch only tags column
    tags_data = Movie.query.with_entities(Movie.tags).filter(base_filter).distinct().all()
    
    categories = set()
    for (t_str,) in tags_data:
        if t_str:
            parts = [x.strip() for x in t_str.split(',')]
            for p in parts:
                # Exclude main tag 'Live TV' to find sub-groups
                if p and p != 'Live TV':
                    categories.add(p)
                    
    sorted_categories = sorted(list(categories))
    
    return render_template('live_tv.html', title="Live TV", active_page='live', 
                           movies=movies_pagination.items, pagination=movies_pagination,
                           categories=sorted_categories, current_tag=tag)

@main_bp.route('/series')
def series_page():
    q = request.args.get('q')
    tag = request.args.get('tag')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Include if tagged Series OR source ends with :series
    query = Movie.query.filter(
         or_(
            Movie.tags.ilike('%Series%'),
            Movie.source.ilike('%:series')
        )
    )
    
    if q:
        query = query.filter(Movie.title.ilike(f'%{q}%'))
    if tag:
        query = query.filter(Movie.tags.ilike(f'%{tag}%'))
        
    movies_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Extract Categories (Series)
    base_series_filter = or_(
        Movie.tags.ilike('%Series%'),
        Movie.source.ilike('%:series')
    )
    
    tags_data = Movie.query.with_entities(Movie.tags).filter(base_series_filter).distinct().all()
    categories = set()
    for (t_str,) in tags_data:
        if t_str:
            parts = [x.strip() for x in t_str.split(',')]
            for p in parts:
                if p and p != 'Series' and p != 'Live TV':
                    categories.add(p)
                    
    sorted_categories = sorted(list(categories))

    return render_template('playlist.html', title="Series", active_page='series', 
                           movies=movies_pagination.items, pagination=movies_pagination,
                           categories=sorted_categories, current_tag=tag)

@main_bp.route('/groups')
def groups_page():
    # Fetch all tags and count them
    # This might be heavy on large DBs, but fine for SQLite < 100k items
    from collections import Counter
    import re
    
    all_movies = Movie.query.with_entities(Movie.tags, Movie.source).all()
    
    categories = {'movies': Counter(), 'live': Counter(), 'series': Counter()}
    
    for m in all_movies:
        if not m.tags: continue
        
        # Determine type
        ctype = 'movies'
        if m.source and ':live' in m.source: ctype = 'live'
        elif m.source and ':series' in m.source: ctype = 'series'
        
        # Split tags (usually comma separated)
        tags = [t.strip() for t in m.tags.split(',')]
        for t in tags:
            if t: categories[ctype][t] += 1
            
    return render_template('groups.html', title="Categories / Groups", active_page='groups', categories=categories)

@main_bp.route('/player')
def player_page():
    url = request.args.get('url')
    
    # Auto-Proxy for provider URLs entered manually
    if url:
        NEEDS_PROXY = ['hglink', 'streamtape', 'dood', 'voe.sx', 'mixdrop', 'filemoon', 'earnvid', 'myvidplay']
        if any(x in url for x in NEEDS_PROXY) and 'http' in url and '/watch' not in url:
             from urllib.parse import quote
             host_base = request.host_url.rstrip('/')
             
             # Add default referer for HGLink if manually played
             ref_param = ""
             if 'hglink' in url:
                 ref_param = f"&referer={quote('https://film-adult.top/')}"
                 
             url = f"{host_base}/watch?url={quote(url)}{ref_param}&pid=web"

    return render_template('player.html', title="Player", active_page='player', url=url)

@main_bp.route('/player/<int:movie_id>')
def player_by_id(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    # Best stream?
    stream_url = movie.url
    if movie.streams and len(movie.streams) > 0:
        stream_url = movie.streams[0].url
        
    # Validation/Fix for Xtream URLs (Strip .mp4 to allow server detection for HLS/etc)
    if stream_url and stream_url.endswith('.mp4') and ('/movie/' in stream_url or '/series/' in stream_url):
         stream_url = stream_url[:-4]
        
    # Proxy the stream for Web Player to handle CORS/Extensions
    encoded = quote(stream_url, safe='')
    host_base = request.host_url.rstrip('/')
    stream_url = f"{host_base}/watch?url={encoded}&pid=web&force_video=true"

    return render_template('player.html', title=f"Playing: {movie.title}", active_page='player', url=stream_url)

@main_bp.route('/manage_playlists')
def manage_playlists():
    playlists = Playlist.query.all()
    edit_id = request.args.get('edit')
    edit_pl = Playlist.query.get(edit_id) if edit_id else None
    return render_template('manage_playlists.html', title="Správa Playlistov", active_page='manage_playlists', playlists=playlists, edit_pl=edit_pl)

@main_bp.route('/save_playlist', methods=['POST'])
def save_playlist():
    old_id = request.form.get('old_id')
    new_id = request.form.get('id').strip()
    
    if old_id:
        # Update
        pl = Playlist.query.get(old_id)
        if pl:
            pl.name = request.form.get('name')
            pl.max_connections = int(request.form.get('max_connections', 0))
            pl.allowed_countries = request.form.get('allowed_countries', '').strip()
            db.session.commit()
    else:
        # Create
        if Playlist.query.get(new_id):
            return "Playlist ID already exists!", 400
        
        pl = Playlist(
            id=new_id,
            name=request.form.get('name'),
            max_connections=int(request.form.get('max_connections', 0)),
            allowed_countries=request.form.get('allowed_countries', '').strip()
        )
        db.session.add(pl)
        db.session.commit()
    
    return redirect(url_for('main.manage_playlists'))

@main_bp.route('/delete_playlist')
def delete_playlist():
    pid = request.args.get('id')
    if pid == 'default': return "Cannot delete default playlist", 403
    
    Playlist.query.filter_by(id=pid).delete()
    db.session.commit()
    return redirect(url_for('main.manage_playlists'))

@main_bp.route('/settings')
def settings_page():
    count = Movie.query.count()
    return render_template('settings.html', title="Settings", active_page='settings', db_size=count)

@main_bp.route('/database')
def database_overview():
    from collections import Counter
    from datetime import datetime, timedelta
    
    stats = {}
    
    # Movies
    # Movies
    movies_total = Movie.query.count()
    
    # Calculate Live TV vs VOD
    live_count = Movie.query.filter(
        or_(
            Movie.tags.ilike('%Live TV%'),
            Movie.source.ilike('%:live')
        )
    ).count()
    vod_count = movies_total - live_count
    
    stats['movies_total'] = movies_total
    stats['live_count'] = live_count
    stats['vod_count'] = vod_count
    
    stats['movies_with_streams'] = db.session.query(Movie).join(Stream).distinct().count()
    stats['movies_without_streams'] = stats['movies_total'] - stats['movies_with_streams']
    
    # Movies by source
    sources = db.session.query(Movie.source, func.count(Movie.id)).group_by(Movie.source).all()
    stats['movies_by_source'] = {src or 'Unknown': count for src, count in sources}
    
    # Streams
    stats['streams_total'] = Stream.query.count()
    
    # Streams by provider
    providers = db.session.query(Stream.provider, func.count(Stream.id)).group_by(Stream.provider).all()
    stats['streams_by_provider'] = {prov or 'Unknown': count for prov, count in providers}
    
    # Xtream Users
    from ..models import XtreamUser, XtreamSource
    stats['xtream_users_total'] = XtreamUser.query.count()
    stats['xtream_users_active'] = XtreamUser.query.filter_by(is_active=True).count()
    stats['xtream_users_inactive'] = stats['xtream_users_total'] - stats['xtream_users_active']
    
    # Xtream Sources
    stats['xtream_sources_total'] = XtreamSource.query.count()
    stats['xtream_sources_active'] = XtreamSource.query.filter_by(is_active=True).count()
    stats['xtream_sources_autosync'] = XtreamSource.query.filter_by(auto_sync=True).count()
    
    # Sum of content from sources
    stats['xtream_vod_count'] = db.session.query(func.sum(XtreamSource.vod_count)).scalar() or 0
    stats['xtream_live_count'] = db.session.query(func.sum(XtreamSource.live_count)).scalar() or 0
    stats['xtream_series_count'] = db.session.query(func.sum(XtreamSource.series_count)).scalar() or 0
    
    # Playlists
    stats['playlists_total'] = Playlist.query.count()
    stats['playlists'] = Playlist.query.all()
    
    # History
    stats['history_total'] = History.query.count()
    now = datetime.now()
    stats['history_24h'] = History.query.filter(History.time >= now - timedelta(hours=24)).count()
    stats['history_7d'] = History.query.filter(History.time >= now - timedelta(days=7)).count()
    
    # Database file info
    db_path = os.path.join(current_app.instance_path, 'movies.db')
    if os.path.exists(db_path):
        size_bytes = os.path.getsize(db_path)
        stats['db_size'] = f"{size_bytes / (1024*1024):.2f} MB"
        stats['db_modified'] = datetime.fromtimestamp(os.path.getmtime(db_path)).strftime('%Y-%m-%d %H:%M:%S')
    else:
        stats['db_size'] = 'N/A'
        stats['db_modified'] = 'N/A'
    
    return render_template('database_overview.html', title="Database Overview", active_page='database', stats=stats)


@main_bp.route('/clean_db')
def clean_db_route():
    Movie.query.delete()
    Stream.query.delete()
    db.session.commit()
    log_history("System", "Database Cleaned (Emptied)")
    return redirect(url_for('main.settings_page'))
    
@main_bp.route('/add_movie')
def add_movie_page():
    return render_template('add_movie.html', title="Add Movie", active_page='add_movie')

@main_bp.route('/analyze_movie', methods=['POST'])
def analyze_movie():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
        
    try:
        from curl_cffi import requests as crequests
        from bs4 import BeautifulSoup
        
        session = crequests.Session(impersonate="chrome120")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        }
        
        r = session.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # 1. Metadata
        title = "Unknown"
        # Try typical title locations
        og_title = soup.find('meta', property='og:title')
        if og_title: title = og_title.get('content')
        else:
            t = soup.find('h1')
            if t: title = t.get_text(strip=True)
            
        desc = ""
        og_desc = soup.find('meta', property='og:description')
        if og_desc: desc = og_desc.get('content')
        
        image = ""
        og_image = soup.find('meta', property='og:image')
        if og_image: image = og_image.get('content')
        
        # 2. Find Streams (Iframes & Links)
        streams = []
        
        # Helper to check provider
        def detect_provider(link):
            if not link: return "unknown"
            link = link.lower()
            if 'myvidplay' in link: return 'myvidplay'
            if 'hglink' in link: return 'hglink'
            if 'streamtape' in link: return 'streamtape'
            if 'dood' in link: return 'doodstream'
            if 'voe.sx' in link or 'voe.lx' in link: return 'voe'
            if 'mixdrop' in link: return 'mixdrop'
            if 'filemoon' in link: return 'filemoon'
            if 'earnvid' in link or 'dingtezuni' in link or 'earnvids' in link or 'minochinos' in link: return 'earnvid'
            return "unknown"

        junk = ['googletagmanager', 'google-analytics', 'facebook', 'twitter', 'youtube', 'doubleclick', 'adnxs', 'recaptcha']

        # Check Iframes
        iframes = soup.find_all('iframe')
        for iframe in iframes:
            src = iframe.get('src') or iframe.get('data-src')
            if not src: continue
            if any(j in src.lower() for j in junk): continue # Ignore junk iframes
            
            provider = detect_provider(src)
            # Only add if known or looks like a stream? No, add all iframes for manual review but mark unknown
            
            streams.append({
                'provider': provider,
                'url': src,
                'domain': src.split('/')[2] if '//' in src else 'unknown',
                'label': 'Iframe',
                'broken': False if provider != 'unknown' else True
            })

        # Check Links (Buttons)
        links = soup.find_all('a')
        for a in links:
            href = a.get('href')
            if not href or href.startswith('#') or href.startswith('javascript'): continue
            
            provider = detect_provider(href)
            if provider != "unknown":
                # Ensure we don't add duplicates (if same url already found in iframe)
                if any(s['url'] == href for s in streams): continue
                
                streams.append({
                    'provider': provider,
                    'url': href,
                    'domain': href.split('/')[2] if '//' in href else 'unknown',
                    'label': a.get_text(strip=True) or 'Link',
                    'broken': False
                })
            
        return jsonify({
            'title': title,
            'description': desc,
            'image': image,
            'original_url': url,
            'streams': streams
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/save_analyzed_movie', methods=['POST'])
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
            
        # Check if movie exists
        movie = Movie.query.filter_by(url=url).first()
        if movie:
            # Update
            movie.title = title
            movie.image = image
            movie.description = desc
            movie.source = source
            # Replace streams
            Stream.query.filter_by(movie_id=movie.id).delete()
        else:
            # Create
            # Determine tags
            tags = request.form.get('tags')
            if not tags:
                # Auto-tag based on source or content
                # User specifically requested 'xxxv' group (interpreted as XXX category) for Uiiu
                if 'uiiu' in (source or '') or 'uiiu' in url:
                    tags = "XXX, Movies"
                else:
                    tags = "Movies"

            movie = Movie(
                title=title,
                url=url,
                image=image,
                description=desc,
                source=source,
                tags=tags
            )
            db.session.add(movie)
            db.session.flush() # Get ID
            
        # Add Stream
        stream = Stream(
            movie_id=movie.id,
            provider=provider,
            url=stream_url
        )
        db.session.add(stream)
        db.session.commit()
        
        log_history("Add", f"Manual add: {title} ({provider})", playlist="manual")
        return "OK", 200
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}", 500

@main_bp.route('/delete_movie/<int:id>')
def delete_movie(id):
    movie = Movie.query.get(id)
    if movie:
        db.session.delete(movie)
        db.session.commit()
        log_history("Delete", f"Deleted movie: {movie.title}")
    return redirect(url_for('main.playlist_page'))

@main_bp.route('/edit_movie/<int:id>')
def edit_movie_page(id):
    movie = Movie.query.get_or_404(id)
    return render_template('edit_movie.html', movie=movie, index=id, title="Edit Movie") 

@main_bp.route('/update_movie/<int:id>', methods=['POST'])
def update_movie(id):
    movie = Movie.query.get_or_404(id)
    movie.title = request.form.get('title')
    movie.image = request.form.get('image')
    movie.description = request.form.get('description')
    if request.form.get('movie_url'):
        movie.url = request.form.get('movie_url')
        
    # Update streams - naive aproach: delete all and recreate valid ones
    Stream.query.filter_by(movie_id=movie.id).delete()
    
    i = 0
    while True:
        prov = request.form.get(f'provider_{i}')
        url_str = request.form.get(f'stream_url_{i}')
        if prov is None: break
        if prov and url_str:
             db.session.add(Stream(movie_id=movie.id, provider=prov, url=url_str))
        i += 1
        
    new_prov = request.form.get('new_provider')
    new_url = request.form.get('new_stream_url')
    if new_prov and new_url and new_prov != 'manual':
         db.session.add(Stream(movie_id=movie.id, provider=new_prov, url=new_url))
         
    db.session.commit()
    log_history("Update", f"Updated movie: {movie.title}")
    return redirect(url_for('main.playlist_page'))

# --- Helper for Ignored Movies ---
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

# --- Restored Routes ---

@main_bp.route('/import_movies')
def import_movies_page():
    # Try multiple paths for the scraped file (adjusting logic for new structure?)
    # Since we run from root, relative paths should work if folders are in root.
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
        
    # Get existing URLs from DB
    existing_urls = set(m.url for m in Movie.query.with_entities(Movie.url).all())
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

@main_bp.route('/ignore_movie', methods=['POST'])
def ignore_movie():
    url = request.form.get('url')
    if url:
        ignored = load_ignored()
        if url not in ignored:
            ignored.append(url)
            save_ignored(ignored)
    return 'OK'

@main_bp.route('/sources/film-adult-manage')
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

@main_bp.route('/sources/uiiu-manage')
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

@main_bp.route('/movies')
def all_movies_page():
    page = request.args.get('page', 1, type=int)
    source_filter = request.args.get('source')
    letter_filter = request.args.get('letter')
    tag_filter = request.args.get('tag')
    per_page = 50
    
    query = Movie.query
    
    # Source Filter
    if source_filter:
        if source_filter == 'manual':
             query = query.filter(or_(Movie.source == 'manual', Movie.source == None, Movie.source == ''))
        elif source_filter == 'uiiu':
             query = query.filter(Movie.source.ilike('%uiiu%'))
        elif source_filter == 'adult':
             query = query.filter(Movie.source.ilike('%film-adult%'))
        else:
             query = query.filter(Movie.source.ilike(f'%{source_filter}%'))
             
    # Letter Filter
    if letter_filter:
        if letter_filter == '#':
            # Check for digits or symbols (simple check for starting with digit)
            # using SQLite GLOB
            query = query.filter(Movie.title.op('GLOB')('[0-9]*'))
        elif letter_filter:
            query = query.filter(Movie.title.ilike(f'{letter_filter}%'))
            
    # Tag Filter
    if tag_filter:
        query = query.filter(Movie.tags.ilike(f'%{tag_filter}%'))

    movies_pagination = query.order_by(Movie.title).paginate(page=page, per_page=per_page, error_out=False)
    
    # Extract Categories (VOD)
    # Re-use base filter logic for consistent category list logic
    base_vod_filter = and_(
        not_(Movie.tags.ilike('%Live TV%')),
        not_(Movie.tags.ilike('%Series%')),
        not_(Movie.source.ilike('%:live')),
        not_(Movie.source.ilike('%:series'))
    )
    
    tags_data = Movie.query.with_entities(Movie.tags).filter(base_vod_filter).distinct().all()
    categories = set()
    for (t_str,) in tags_data:
        if t_str:
            parts = [x.strip() for x in t_str.split(',')]
            for p in parts:
                if p and p != 'Movies' and p != 'VOD':
                    categories.add(p)
                    
    sorted_categories = sorted(list(categories))

    return render_template('playlist.html', 
                           title="Movies Library", 
                           active_page='movies',
                           movies=movies_pagination.items, 
                           pagination=movies_pagination,
                           current_source=source_filter,
                           current_letter=letter_filter,
                           show_filters=True,
                           categories=sorted_categories,
                           current_tag=tag_filter)


@main_bp.route('/source_movies')
def source_movies():
    source = request.args.get('source', '')
    movies = Movie.query.filter(Movie.source.ilike(f"%{source}%")).all()
    # Need to simulate "original_index" if templates use it, but for DB we use ID
    # Actually templates might iterate. Let's pass movies as is, but template expects dict access?
    # SQLAlchemy objects are object access. Jinja handles both usually or we might need updates.
    # Checking template... playlist.html uses movie.title, movie.streams.
    # It seems to use dot notation, which works for Objects too.
    return render_template('playlist.html', title=f"Movies from {source}", active_page='source_movies', movies=movies)

@main_bp.route('/new_movies')
def new_movies_page():
    # Last 50 added
    latest = Movie.query.order_by(desc(Movie.id)).limit(50).all()
    return render_template('playlist.html', title="New Movies (Last 50)", active_page='new_movies', movies=latest)

@main_bp.route('/clients')
def clients_page():
    history = History.query.order_by(desc(History.time)).limit(200).all()
    return render_template('clients.html', title="Clients", active_page='clients', history=history)

@main_bp.route('/webs')
def webs_page():
    # Using JSON config for this one as requested in models but previously was JSON.
    # Keeping JSON for scraper config compatibility for now.
    CONFIG_FILE = 'scraper_config.json'
    config = {"urls": []}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: config = json.load(f)
    return render_template('webs.html', title="Scrapers", active_page='webs', sites=config['urls'])

@main_bp.route('/add_site', methods=['POST'])
def add_site():
    CONFIG_FILE = 'scraper_config.json'
    config = {"urls": [], "settings": {}}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: config = json.load(f)
    config['urls'].append({"name": request.form['name'], "url": request.form['url'], "last_scraped": "Never"})
    with open(CONFIG_FILE, 'w') as f: json.dump(config, f, indent=2)
    return redirect(url_for('main.webs_page'))

@main_bp.route('/restart')
def restart_server():
    import sys
    log_history("System", "Restart Request")
    os.execl(sys.executable, sys.executable, *sys.argv)

# Import subprocess for scripts
import subprocess

@main_bp.route('/api/run_script/<script_type>', methods=['POST'])
def run_script_api_route(script_type):
    from flask import Response
    
    # Map types to scripts - Adjust paths for root execution
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
        
    cmd = scripts[script_type].copy() # Make a copy to avoid appending to global dict
    
    # Handle parameters
    if request.is_json:
        data = request.get_json()
        if script_type == 'uiiu_scrape':
             if 'limit_pages' in data and data['limit_pages']:
                 cmd.extend(['--pages', str(data['limit_pages'])])
             if 'max_workers' in data and data['max_workers']:
                 cmd.extend(['--workers', str(data['max_workers'])])
             if 'providers' in data and data['providers']:
                 # Pass as comma-separated list
                 cmd.extend(['--providers', ','.join(data['providers'])])
    
    try:
        # Run DETACHED process
        subprocess.Popen(cmd, cwd=os.getcwd(), creationflags=subprocess.CREATE_NEW_CONSOLE)
        return Response(json.dumps({'status': 'started', 'message': f'Script {script_type} started in new window.'}), mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({'status': 'error', 'message': str(e)}), mimetype='application/json'), 500

@main_bp.route('/providers')
def providers_page():
    # Recalculate stats from DB
    from providers_config import PROVIDERS
    
    provider_stats = {}
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

    for p, conf in PROVIDERS.items():
        key = aliases.get(p, p)
        if key not in provider_stats:
            provider_stats[key] = {
                'domain': key,
                'count': 0, 
                'status': 'Active', 
                'ref': conf.get('referer', 'N/A')
            }
            
    # Efficient DB query
    streams = Stream.query.all()
    for s in streams:
         prov = s.provider
         if prov:
             found_key = None
             for p_key in PROVIDERS:
                 if p_key in prov or prov in p_key:
                     found_key = aliases.get(p_key, p_key)
                     break
             
             if not found_key and prov in provider_stats:
                 found_key = prov # exact match
                 
             if found_key and found_key in provider_stats:
                 provider_stats[found_key]['count'] += 1
                 
    return render_template('providers.html', title="Providers", active_page='providers', stats=provider_stats)

@main_bp.route('/unknown_providers')
def unknown_providers():
    content = ""
    UNKNOWN_FILE = 'nezname_providery.txt'
    if os.path.exists(UNKNOWN_FILE):
        try:
            with open(UNKNOWN_FILE, 'r', encoding='utf-8') as f: content = f.read()
        except: pass
    return render_template('file_list.html', title="Unknown Providers", active_page='unknown', content=content, allow_clear=True, clear_url='/clear_unknown')

@main_bp.route('/clear_unknown')
def clear_unknown():
    UNKNOWN_FILE = 'nezname_providery.txt'
    try:
        open(UNKNOWN_FILE, 'w').close()
    except: pass
    return redirect(url_for('main.unknown_providers'))

@main_bp.route('/broken_providers')
def broken_providers():
    content = ""
    BROKEN_FILE = 'not_working_providers.txt'
    if os.path.exists(BROKEN_FILE):
        try:
           with open(BROKEN_FILE, 'r', encoding='utf-8') as f: content = f.read()
        except: pass
    return render_template('file_list.html', title="Broken Providers", active_page='broken', content=content, allow_clear=False)

# --- TiviMate Clients Routes ---
@main_bp.route('/tivimate_clients')
def tivimate_clients():
    # TODO: Implement actual client tracking from database
    clients = []
    return render_template('tivimate_clients.html', 
                         title="TiviMate Clients", 
                         active_page='tivimate_clients',
                         clients=clients)

# --- Scraper Manager Implementation ---
import threading
import subprocess
import time

# Global State for Scraper
scraper_state = {
    'process': None,
    'status': 'Idle',
    'log': [],
    'progress': {'current': 0, 'max': 388, 'found': 0},
    'thread': None
}

def scraper_monitor_task():
    global scraper_state
    proc = scraper_state['process']
    
    while proc and proc.poll() is None:
        line = proc.stdout.readline()
        if line:
            line_str = line.decode('utf-8', errors='ignore').strip()
            if not line_str: continue
            
            scraper_state['log'].append(line_str)
            if len(scraper_state['log']) > 50: scraper_state['log'].pop(0)
            
            # Parsing logic
            # Format: "[001] Scraping..."
            if line_str.startswith('[') and '] Scraping' in line_str:
                try:
                    # Extract page number
                    parts = line_str.split(']')
                    if len(parts) > 0:
                        p_txt = parts[0].replace('[', '')
                        scraper_state['progress']['current'] = int(p_txt)
                        scraper_state['status'] = f"Scraping Page {p_txt}"
                except: pass
            
            # Format: " +5 movies."
            if '+' in line_str and 'movies' in line_str:
                try:
                    # Find number e.g. +5
                    import re
                    m = re.search(r'\+(\d+)', line_str)
                    if m:
                        scraper_state['progress']['found'] += int(m.group(1))
                except: pass
                
    scraper_state['status'] = "Finished" if proc.returncode == 0 else "Stopped/Error"
    if proc.returncode != 0:
        scraper_state['log'].append(f"Process ended with code {proc.returncode}")
        
    scraper_state['process'] = None

@main_bp.route('/api/scraper/start', methods=['POST'])
def scraper_api_start():
    global scraper_state
    
    if scraper_state['process'] and scraper_state['process'].poll() is None:
        return jsonify({'status': 'running', 'message': 'Scraper already running'})
        
    scraper_state['log'] = ["Starting scraper process..."]
    scraper_state['progress'] = {'current': 0, 'max': 388, 'found': 0}
    scraper_state['status'] = "Starting"
    
    script_path = os.path.join('adult_film_data', 'scrape_film_adult_full.py')
    
    try:
        # Run python -u (unbuffered)
        proc = subprocess.Popen(
            ['python', '-u', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=os.getcwd()
        )
        scraper_state['process'] = proc
        
        # Start monitor thread
        t = threading.Thread(target=scraper_monitor_task)
        t.daemon = True
        t.start()
        scraper_state['thread'] = t
        
        return jsonify({'status': 'started'})
    except Exception as e:
        scraper_state['status'] = "Error"
        scraper_state['log'].append(f"Failed to start: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/api/scraper/stop', methods=['POST'])
def scraper_api_stop():
    global scraper_state
    if scraper_state['process']:
        scraper_state['process'].terminate()
        scraper_state['status'] = "Stopping..."
        return jsonify({'status': 'stopping'})
    return jsonify({'status': 'not_running'})

@main_bp.route('/api/scraper/status')
def scraper_api_status():
    global scraper_state
    return jsonify({
        'status': scraper_state['status'],
        'current_page': scraper_state['progress']['current'],
        'max_pages': scraper_state['progress']['max'],
        'total_found': scraper_state['progress']['found'],
        'log': scraper_state['log']
    })

# --- EPG Manager Routes ---
@main_bp.route('/epg')
def epg_manager():
    # TODO: Implement actual EPG source management
    epg_sources = []
    total_programs = 0
    last_update = None
    coverage_days = 7
    
    return render_template('epg.html',
                         title="EPG Manager",
                         active_page='epg',
                         epg_sources=epg_sources,
                         total_programs=total_programs,
                         last_update=last_update,
                         coverage_days=coverage_days)

# Reload trigger
