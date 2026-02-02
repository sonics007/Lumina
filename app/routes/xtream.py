from flask import Blueprint, request, jsonify, redirect, url_for, render_template, current_app, Response
from ..models import db, Movie, Stream, XtreamUser
from sqlalchemy import or_, not_, and_, func
import time
import os
import logging
import hashlib
import re
from urllib.parse import quote
from ..services import group_service
from ..services.extractor import get_stream_url

xtream_bp = Blueprint('xtream', __name__)

# --- Authentication Helper ---
def check_auth(username, password):
    user = XtreamUser.query.filter_by(username=username).first()
    if user and user.password == password and user.is_active:
        return True
    return False

# --- UI Routes (Management) ---

@xtream_bp.route('/xtream')
def xtream_page():
    users = XtreamUser.query.all()
    # Also pass server URL info for display
    return render_template('xtream_info.html', title="Xtream API", active_page='xtream', users=users)

@xtream_bp.route('/xtream/add_user', methods=['POST'])
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    try:
        max_conns = int(request.form.get('max_connections', 1))
    except:
        max_conns = 1
    
    if XtreamUser.query.filter_by(username=username).first():
        # User exists - flash message would be nice but for now just log
        logging.warning(f"Xtream Add User Failed: {username} already exists")
        return redirect(url_for('xtream.xtream_page'))
        
    try:
        new_user = XtreamUser(username=username, password=password, max_connections=max_conns)
        db.session.add(new_user)
        db.session.commit()
        logging.info(f"Xtream User Added: {username}")
    except Exception as e:
        logging.error(f"Error adding user: {e}")
        db.session.rollback()
        
    return redirect(url_for('xtream.xtream_page'))

@xtream_bp.route('/xtream/delete_user/<int:user_id>')
def delete_user(user_id):
    user = XtreamUser.query.get(user_id)
    # Don't delete last admin maybe? Or just allow it.
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('xtream.xtream_page'))

# --- Xtream API Routes ---

@xtream_bp.route('/player_api.php', methods=['GET', 'POST'])
@xtream_bp.route('/get.php', methods=['GET', 'POST'])  # TiviMate uses this
def player_api():
    username = request.args.get('username')
    password = request.args.get('password')
    action = request.args.get('action')

    # Auth Check
    if not check_auth(username, password):
         logging.warning(f"Xtream API Auth Failed: User={username} IP={request.remote_addr}")
         return jsonify({"user_info": {"auth": 0}}), 401

    host = request.host_url.rstrip('/')
    port = request.host.split(':')[-1] if ':' in request.host else '80'
    
    logging.info(f"Xtream API Request: Action={action} User={username} IP={request.remote_addr}")
    
    config = group_service.load_config(username)

    # 1. Login / Server Info
    if not action:
        user = XtreamUser.query.filter_by(username=username).first()
        exp = user.exp_date if user.exp_date else "1999999999"
        
        return jsonify({
            "user_info": {
                "username": username,
                "password": password,
                "message": "Logged In",
                "auth": 1,
                "status": "Active",
                "exp_date": exp,
                "is_trial": "0",
                "active_cons": "0",
                "created_at": "1514764800",
                "max_connections": str(user.max_connections),
                "allowed_output_formats": ["m3u8", "ts", "mp4"]
            },
            "server_info": {
                "url": host,
                "port": port,
                "https_port": "443",
                "server_protocol": "http",
                "rtmp_port": "8880",
                "timezone": "Europe/Bratislava",
                "timestamp_now": int(time.time()),
                "time_now": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
        })

    # 2. VOD Categories
    if action == 'get_vod_categories':
        temp_cats = []
        # Add "All Movies"
        temp_cats.append({
            "category_id": "all", 
            "category_name": "All Movies", 
            "parent_id": 0,
            "__sort_order": -1
        })
        
        # Base filter for VOD (exclude Live/Series)
        # Handle NULL tags by coalescing to empty string
        base_filter = and_(
            not_(func.coalesce(Movie.tags, '').ilike('%Live TV%')),
            not_(func.coalesce(Movie.tags, '').ilike('%Series%')),
            not_(Movie.source.ilike('%:live')),
            not_(Movie.source.ilike('%:series'))
        )
        
        # Fetch distinct tags
        tags_rows = db.session.query(Movie.tags).filter(base_filter).distinct().all()
        
        seen_ids = set()
        seen_ids.add("all")
        
        for (t_str,) in tags_rows:
            if not t_str: t_str = "Uncategorized"
            
            # Use whole string as category name (matches importer logic)
            cat_name = t_str.strip()
            if not cat_name: continue
            
            # Generate ID
            cat_id = str(int(hashlib.md5(cat_name.encode('utf-8')).hexdigest(), 16) % 100000 + 10000)
            
            if cat_id not in seen_ids:
                seen_ids.add(cat_id)
                
                if not config.get(cat_name, {}).get('enabled', True):
                    continue

                display_name = group_service.get_group_display_name(cat_name, config)
                order = group_service.get_group_order(cat_name, config, context='movie')
                
                temp_cats.append({
                    "category_id": cat_id,
                    "category_name": display_name,
                    "parent_id": 0,
                    "__sort_order": order
                })
        
        temp_cats.sort(key=lambda x: (x['__sort_order'], x['category_name']))
        categories = [{k:v for k,v in c.items() if k != '__sort_order'} for c in temp_cats]
        
        return jsonify(categories)

    # 3. VOD Streams
    if action == 'get_vod_streams':
        cat_id = request.args.get('category_id')
        
        query = Movie.query
        
        # EXCLUDE Series and Live TV to prevent mixing
        query = query.filter(
            not_(func.coalesce(Movie.tags, '').ilike('%Live TV%')),
            not_(func.coalesce(Movie.tags, '').ilike('%Series%')),
            not_(Movie.source.ilike('%:live')),
            not_(Movie.source.ilike('%:series'))
        )
        
        # Optimization: Use raw SQL or keyed tuple query
        movies_query = query.with_entities(
            Movie.id, 
            Movie.title, 
            Movie.image, 
            Movie.rating, 
            Movie.source, 
            Movie.created_at,
            Movie.tags,  # Request Tags
            Movie.url    # Request URL to detect extension
        )
        
        # Execute query and fetch all
        movies_data = movies_query.all()
        
        logging.info(f"Xtream API: Scanning {len(movies_data)} VOD streams for category {cat_id}")
        streams_data = []
        
        for m_id, m_title, m_image, m_rating, m_source, m_created, m_tags, m_url in movies_data:
            # Determine Category ID based on Tag
            t_str = m_tags or "Uncategorized"
            cat_name = t_str.strip() or "Uncategorized"
            
            # Generate ID (Must match get_vod_categories logic)
            c_id = str(int(hashlib.md5(cat_name.encode('utf-8')).hexdigest(), 16) % 100000 + 10000)
            
            # Filter logic
            if cat_id and cat_id != "all":
                if c_id != cat_id: continue
            
            # Force 18+ rating logic if needed
            rating = m_rating
            if m_source and ("film-adult" in m_source or "uiiu" in m_source) and not rating:
                 rating = "18+"
            
            added_ts = str(int(m_created.timestamp())) if m_created else "0"
            
            # Detect Extension
            ext = "mp4"
            if m_url:
                lower_url = m_url.lower()
                if lower_url.endswith('.m3u8'): ext = "m3u8"
                elif lower_url.endswith('.mkv'): ext = "mkv"
                elif lower_url.endswith('.avi'): ext = "avi"
                elif lower_url.endswith('.ts'): ext = "ts"
            
            streams_data.append({
                "num": m_id,
                "name": m_title or "Unknown",
                "stream_type": "movie",
                "stream_id": m_id,
                "stream_icon": m_image or "",
                "rating": rating or "",
                "added": added_ts, 
                "category_id": c_id,
                "container_extension": ext,
                "custom_sid": "",
                "direct_source": ""
            })
            
        logging.info(f"Xtream API: Returning {len(streams_data)} VOD streams")
        return jsonify(streams_data)

    # Live Categories
    if action == 'get_live_categories':
        temp_cats = []
        # Default category
        temp_cats.append({
            "category_id": "1",
            "category_name": "Manual / Test",
            "parent_id": 0,
            "__sort_order": -1
        })
        
        # Get live content from DB
        live_movies = Movie.query.filter(
            or_(
                Movie.tags.ilike('%Live TV%'),
                Movie.source.ilike('%:live')
            )
        ).all()
        
        seen_cats = set()
        
        for m in live_movies:
            # Extract category name from tags (format: "Live TV, CategoryName" or just "CategoryName")
            if not m.tags: continue
            
            parts = [t.strip() for t in m.tags.split(',')]
            for p in parts:
                if p.lower() == "live tv": continue
                if not p: continue
                
                # Generate stable ID from name
                cat_id_int = int(hashlib.md5(p.encode('utf-8')).hexdigest(), 16) % 100000 + 2000
                cid_str = str(cat_id_int)
                
                if cid_str not in seen_cats:
                    seen_cats.add(cid_str)
                    
                    if not config.get(p, {}).get('enabled', True):
                        continue
                        
                    display_name = group_service.get_group_display_name(p, config)
                    order = group_service.get_group_order(p, config, context='live')
                    
                    temp_cats.append({
                        "category_id": cid_str,
                        "category_name": display_name,
                        "parent_id": 0,
                        "__sort_order": order
                    })
        
        temp_cats.sort(key=lambda x: (x['__sort_order'], x['category_name']))
        categories = [{k:v for k,v in c.items() if k != '__sort_order'} for c in temp_cats]
        
        return jsonify(categories)

    # Live Streams
    if action == 'get_live_streams':
        streams = []
        
        # 1. Load from channels.txt (Manual)
        possible_paths = [
            os.path.join(current_app.root_path, 'channels.txt'),
            os.path.join(os.path.dirname(current_app.root_path), 'channels.txt')
        ]
        channels_file = None
        for p in possible_paths:
            if os.path.exists(p):
                channels_file = p
                break
        
        if channels_file:
            try:
                with open(channels_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for idx, line in enumerate(lines):
                    line = line.strip()
                    if not line: continue
                    parts = line.split('|')
                    if len(parts) >= 2:
                        # Use high ID offset for manual channels to avoid collision with DB
                        current_id = 900000 + idx 
                        streams.append({
                            "num": current_id,
                            "name": parts[1],
                            "stream_type": "live",
                            "stream_id": current_id,
                            "stream_icon": parts[2] if len(parts) > 2 else "",
                            "epg_channel_id": None,
                            "added": "0",
                            "category_id": "1", # Manual Category
                            "custom_sid": "",
                            "tv_archive": 0,
                            "direct_source": "",
                            "tv_archive_duration": 0
                        })
            except Exception as e:
                logging.error(f"Error reading channels.txt: {e}")

        # 2. Load from Database
        live_db = Movie.query.filter(
            or_(
                Movie.tags.ilike('%Live TV%'),
                Movie.source.ilike('%:live')
            )
        ).all()
        
        for m in live_db:
            # Determine category ID
            cat_id = "1" # Default
            if m.tags:
                parts = [t.strip() for t in m.tags.split(',')]
                for p in parts:
                    if p.lower() == "live tv": continue
                    if p:
                        # Must match logic in get_live_categories
                        cat_id = str(int(hashlib.md5(p.encode('utf-8')).hexdigest(), 16) % 100000 + 2000)
                        break # Take first valid sub-category
            
            # Direct link or proxy? 
            # Xtream usually returns direct link if possible, or proxy link.
            # Our movies have proxying logic in /live/ endpoint.
            # We should probably point to our own proxy to handle authentications.
            # But here we just return the metadata. TiviMate will request stream_id.
            
            streams.append({
                "num": m.id,
                "name": m.title,
                "stream_type": "live",
                "stream_id": m.id,
                "stream_icon": m.image or "",
                "epg_channel_id": m.epg_channel_id or None,
                "added": str(int(m.created_at.timestamp())) if m.created_at else "0",
                "category_id": cat_id,
                "custom_sid": "",
                "tv_archive": m.tv_archive or 0,
                "direct_source": "",
                "tv_archive_duration": m.tv_archive_duration or 0
            })
            
        logging.info(f"Xtream API: Returning {len(streams)} live channels ({len(live_db)} from DB)")
        return jsonify(streams)

    # 4. VOD Info (Detail for TiviMate)
    if action == 'get_vod_info':
        vod_id = request.args.get('vod_id')
        movie = Movie.query.get(vod_id)
        if not movie:
            return jsonify({})
            
        info = {
            "movie_image": movie.image or "",
            "info": {
                "name": movie.title,
                "tmdb_id": 0,
                "releasedate": "", 
                "plot": movie.description or "",
                "cast": movie.cast or "",
                "rating": movie.rating or "",
                "director": "",
                "genre": movie.tags or "",
                "duration": movie.duration or "",
                "backdrop_path": [movie.image or ""],
                "youtube_trailer": ""
            }
        }
        return jsonify(info)
        
    # 5. Series Categories
    if action == 'get_series_categories':
        temp_cats = []
        series_items = Movie.query.filter(Movie.source.ilike('%:series')).with_entities(Movie.tags).distinct().all()
        seen_cats = set()
        
        for idx, (tag_str,) in enumerate(series_items):
            if not tag_str: continue
            tags = [t.strip() for t in tag_str.split(',')]
            for t in tags:
                if t != 'Series' and t not in seen_cats:
                    seen_cats.add(t)
                    # Stable hash for cat ID
                    cat_id = int(hashlib.md5(t.encode()).hexdigest(), 16) % 10000
                    
                    if not config.get(t, {}).get('enabled', True):
                        continue

                    display_name = group_service.get_group_display_name(t, config)
                    order = group_service.get_group_order(t, config, context='series')
                    
                    temp_cats.append({
                        "category_id": str(cat_id), 
                        "category_name": display_name,
                        "parent_id": 0,
                        "__sort_order": order
                    })
        
        if not temp_cats:
             temp_cats.append({
                "category_id": "1", 
                "category_name": "All Series", 
                "parent_id": 0,
                "__sort_order": -1
             })
             
        temp_cats.sort(key=lambda x: (x['__sort_order'], x['category_name']))
        categories = [{k:v for k,v in c.items() if k != '__sort_order'} for c in temp_cats]
        
        return jsonify(categories)

    # 6. Series List
    if action == 'get_series':
        cat_id = request.args.get('category_id')
        items = Movie.query.filter(Movie.source.ilike('%:series')).with_entities(Movie.title, Movie.image, Movie.tags, Movie.rating, Movie.created_at, Movie.description, Movie.source, Movie.id).all()
        
        series_map = {}
        for title, img, tags, rating, created, desc, src, mid in items:
            match = re.match(r'^(.*?) - S(\d+)E(\d+)', title)
            s_name = match.group(1) if match else title
            
            s_id = int(hashlib.md5(s_name.encode()).hexdigest(), 16) % 10000000
            
            # Determine Category ID (consistent with categories logic)
            real_cat_id = "1"
            if tags:
                parts = [t.strip() for t in tags.split(',')]
                for t in parts:
                    if t != 'Series': # Pick first non-system tag
                        real_cat_id = str(int(hashlib.md5(t.encode()).hexdigest(), 16) % 10000)
                        break
            
            # Filter matches
            if cat_id and cat_id != "1" and cat_id != "all":
                 if real_cat_id != cat_id: continue
            
            if s_id not in series_map:
                series_map[s_id] = {
                    "num": s_id,
                    "name": s_name,
                    "series_id": s_id,
                    "cover": img or "",
                    "plot": desc or "",
                    "cast": "",
                    "director": "",
                    "genre": tags or "",
                    "releaseDate": "",
                    "last_modified": str(int(created.timestamp())) if created else "0",
                    "rating": rating or "",
                    "category_id": real_cat_id 
                }
        
        return jsonify(list(series_map.values()))

    # 7. Series Info (Episodes)
    if action == 'get_series_info':
        s_id_req = request.args.get('series_id')
        try:
            target_sid = int(s_id_req)
        except:
            return jsonify({})
            
        items = Movie.query.filter(Movie.source.ilike('%:series')).all()
        
        series_info = None
        episodes = {}
        
        logging.info(f"Debugging series info for SID={target_sid}. Checking {len(items)} items...")
        for item in items:
            match = re.match(r'^(.*?) - S(\d+)E(\d+)', item.title)
            s_name = match.group(1) if match else item.title
            
            calc_id = int(hashlib.md5(s_name.encode()).hexdigest(), 16) % 10000000
            
            if calc_id == target_sid:
                logging.info(f"Match found! Title='{item.title}', RegexMatch={bool(match)}")
                if not match: continue # Skip parent/placeholder items in episode list
                
                if not series_info:
                    series_info = {
                        "name": s_name,
                        "cover": item.image or "",
                        "plot": item.description or "",
                        "genre": item.tags or "",
                        "director": "",
                        "cast": "",
                        "rating": item.rating or "",
                        "releaseDate": "",
                        "backdrop_path": [item.image or ""]
                    }
                
                season = match.group(2) if match else "1"
                episode_num = match.group(3) if match else "1"
                
                if season not in episodes: episodes[season] = []
                
                # Check for duplicates in this season
                exists = False
                for ep in episodes[season]:
                    if ep['episode_num'] == episode_num: 
                        exists = True
                        break
                if exists: continue

                episodes[season].append({
                    "id": item.id,
                    "episode_num": episode_num, # String, but sortable
                    "title": item.title,
                    "container_extension": "mp4",
                    "info": { "rating": item.rating or "", "plot": item.description or "", "movie_image": item.image or "" },
                    "custom_sid": "",
                    "added": str(int(item.created_at.timestamp())) if item.created_at else "0",
                    "season": int(season),
                    "direct_source": ""
                })
        
        if not series_info: return jsonify({})
        
        # Sort episodes by episode_num (as int)
        for s_num in episodes:
            episodes[s_num].sort(key=lambda x: int(x['episode_num']) if x['episode_num'].isdigit() else 0)
            
        return jsonify({"seasons": [], "info": series_info, "episodes": episodes})

    return jsonify([])

@xtream_bp.route('/xmltv.php')
def xmltv_epg():
    username = request.args.get('username')
    password = request.args.get('password')
    
    # Auth Check
    if not check_auth(username, password):
         return "Auth Failed", 401

    # Find a valid source with EPG (Live enabled)
    from ..models import XtreamSource
    source = XtreamSource.query.filter_by(import_live=True).first()
    
    if source:
        # Construct external EPG URL
        base_url = source.server_url.rstrip('/')
        epg_url = f"{base_url}/xmltv.php?username={source.username}&password={source.password}"
        logging.info(f"Redirecting EPG request to {epg_url}")
        return redirect(epg_url)
    
    # Fallback: empty XML
    return Response('<?xml version="1.0" encoding="UTF-8"?><tv generator-info-name="Lumina"></tv>', mimetype='application/xml')

# Stream Route for VOD
@xtream_bp.route('/movie/<username>/<password>/<int:stream_id>.<ext>')
@xtream_bp.route('/movie/<username>/<password>/<int:stream_id>') # Alias without ext
def movie_stream_vod(username, password, stream_id, ext=None):
    if not check_auth(username, password):
        logging.warning(f"Xtream VOD Auth Failed: User={username}")
        return "Auth Failed", 401
    
    logging.info(f"Xtream VOD Request: StreamID={stream_id} User={username}")
    
    movie = Movie.query.get(stream_id)
    if not movie:
        return "Movie not found", 404
        
    # Prefer m3u8
    best_stream = None
    if movie.streams:
        for s in movie.streams:
            if s.url and '.m3u8' in s.url.lower():
                best_stream = s
                break
        if not best_stream:
            best_stream = movie.streams[0]
        
    if not best_stream:
        # Try direct movie url
        if movie.url:
             target_url = movie.url
             
             # Bahu Resolver
             if 'bahu.tv' in target_url:
                 try:
                     # Add root dir to path to find bahu module
                     import sys, os
                     root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                     if root_dir not in sys.path: sys.path.append(root_dir)
                     
                     from bahu import resolve_stream, client
                     
                     logging.info(f"Resolving Bahu URL: {target_url}")
                     # Ensure login (simple check if session has cookies)
                     # if not client.CLIENT.session.cookies: 
                     # client.CLIENT.login() is safe to call, it checks internally or re-logs
                     client.CLIENT.login()
                         
                     resolved = resolve_stream.get_stream_url(client.CLIENT.session, target_url)
                     if resolved:
                         target_url = resolved
                 except Exception as e:
                     logging.error(f"Bahu Resolve Error: {e}")

        else:
             return "No stream available", 404
    else:
        target_url = best_stream.url
       
    try:
        # User requested DIRECT REDIRECT ("do nothing with link")
        # Ensure scheme exists
        if target_url and not target_url.startswith(('http://', 'https://')):
             target_url = 'http://' + target_url

        # STRIP .mp4 extension for Xtream URLs to allow server auto-detection (fixes MKV/AVI issues)
        if target_url.endswith('.mp4') and ('/movie/' in target_url or '/series/' in target_url):
             target_url = target_url[:-4]
             
        logging.info(f"Redirecting VOD/Series directly to: {target_url}")
        return redirect(target_url)
        
    except Exception as e:
        logging.error(f"Error redirecting VOD: {e}")
        return f"Error: {e}", 500

@xtream_bp.route('/series/<username>/<password>/<int:stream_id>.<ext>')
@xtream_bp.route('/series/<username>/<password>/<int:stream_id>')
def series_stream(username, password, stream_id, ext=None):
    # Reuse VOD logic for Series episodes (they share Movie model)
    return movie_stream_vod(username, password, stream_id, ext)

@xtream_bp.route('/live/<username>/<password>/<int:stream_id>.<ext>')
@xtream_bp.route('/live/<username>/<password>/<int:stream_id>') # Alias without ext
def live_stream(username, password, stream_id, ext=None):
    if not check_auth(username, password):
        logging.warning(f"Xtream LIVE Auth Failed: User={username}")
        return "Auth Failed", 401
    
    logging.info(f"Xtream LIVE Request: StreamID={stream_id} User={username}")
    
    # Try to get from database first
    movie = Movie.query.filter(
        or_(
            Movie.tags.ilike('%Live TV%'),
            Movie.source.ilike('%:live')
        )
    ).filter_by(id=stream_id).first()
    
    if movie:
        # Use first stream if available
        if movie.streams and len(movie.streams) > 0:
            target_url = movie.streams[0].url
        else:
            # Fallback to movie.url
            target_url = movie.url
            
        logging.info(f"Live stream from DB: {movie.title} -> {target_url[:50]}...")
        
        # User requested DIRECT REDIRECT
        if target_url and not target_url.startswith(('http://', 'https://')):
             target_url = 'http://' + target_url
             
        logging.info(f"Redirecting directly: {target_url}")
        return redirect(target_url)
    
    # Fallback to channels.txt (legacy)
    possible_paths = [
        os.path.join(current_app.root_path, 'channels.txt'),
        os.path.join(os.path.dirname(current_app.root_path), 'channels.txt')
    ]
    channels_file = None
    for p in possible_paths:
        if os.path.exists(p):
            channels_file = p
            break
            
    if not channels_file:
        logging.error(f"Live stream {stream_id} not found in DB and channels.txt missing")
        return "Stream not found", 404
        
    target_url = None
    try:
        with open(channels_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        valid_channels = []
        for line in lines:
            line = line.strip()
            if not line: continue
            parts = line.split('|')
            if len(parts) >= 2:
                valid_channels.append(parts[0]) # Store URL
        
        if stream_id >= 900000:
            requested_index = stream_id - 900000
        else:
            requested_index = stream_id - 1 # Fallback for legacy low IDs
            
        if 0 <= requested_index < len(valid_channels):
            target_url = valid_channels[requested_index]
        else:
             logging.error(f"Stream ID {stream_id} out of range (Total: {len(valid_channels)})")
             return "Channel ID out of range", 404
             
    except Exception as e:
        logging.error(f"Error resolving stream index {stream_id}: {e}")
        return "Internal Error", 500
        
    if not target_url:
        return "Stream not found", 404
        
    logging.info(f"Redirection direct: {target_url}")
    if target_url and not target_url.startswith(('http://', 'https://')):
         target_url = 'http://' + target_url
    return redirect(target_url)

# --- M3U Playlist Routes (Legacy Support) ---

@xtream_bp.route('/playlist.m3u8')
@xtream_bp.route('/playlist.m3u')
@xtream_bp.route('/stream.m3u8')
def playlist_m3u8():
    """
    Legacy M3U playlist endpoint for IPTV players that don't support Xtream API.
    Returns all VOD movies as M3U playlist.
    """
    pid = request.args.get('id', 'default')
    username = request.args.get('username', 'admin')
    password = request.args.get('password', 'admin')
    
    # Optional auth check (can be disabled for public access)
    # if not check_auth(username, password):
    #     return "Auth Failed", 401
    
    logging.info(f"M3U Playlist Request: PID={pid} User={username}")
    
    from ..services import group_service
    config = group_service.load_config(username)
    
    # Fetch all movies
    movies = Movie.query.all()
    
    # Sort movies: First by Group Order, then by Title
    def get_sort_key(m):
        tag = m.tags
        return (group_service.get_group_order(tag, config, context='movie'), m.title or "")
        
    movies.sort(key=get_sort_key)
    
    # Build M3U playlist
    m3u_lines = ["#EXTM3U"]
    
    host = request.host_url.rstrip('/')
    
    for movie in movies:
        title = movie.title or "Unknown"
        image = movie.image or ""
        tag = movie.tags
        
        # Get Display Name for Group
        group_name = group_service.get_group_display_name(tag, config)
        
        # Get first stream
        if movie.streams:
            stream = movie.streams[0]
            provider = stream.provider or "Unknown"
            
            # Build stream URL using Xtream format
            stream_url = f"{host}/movie/{username}/{password}/{movie.id}.mp4"
            
            # Add M3U entry
            logo_attr = f'tvg-logo="{image}"' if image else ""
            group_attr = f'group-title="{group_name}"'
            
            m3u_lines.append(f'#EXTINF:-1 {logo_attr} {group_attr},{title} [{provider}]')
            m3u_lines.append(stream_url)
    
    playlist_content = '\n'.join(m3u_lines)
    
    response = Response(playlist_content, mimetype='audio/x-mpegurl')
    response.headers['Content-Disposition'] = 'attachment; filename=playlist.m3u'
    return response
