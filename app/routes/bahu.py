"""
Bahu.tv Routes - Hungarian movie source
"""
from flask import Blueprint, render_template, jsonify, request
import json
import os
import sys
import threading
from datetime import datetime
from app import db
from app.models import Movie, MovieGroup

# Add bahu directory to path
BAHU_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bahu')
sys.path.insert(0, BAHU_DIR)

bp = Blueprint('bahu', __name__, url_prefix='/sources')

# Global Import Status
IMPORT_STATUS = {
    'running': False,
    'total': 0,
    'current': 0,
    'imported': 0,
    'skipped': 0,
    'message': 'Idle',
    'type': 'movie' # 'movie' or 'series'
}

@bp.route('/bahu-import-status')
def bahu_import_status():
    """Get current import status"""
    return jsonify(IMPORT_STATUS)

def load_bahu_data():
    """Load movies from bahu/data.json"""
    data_file = os.path.join(BAHU_DIR, 'data.json')
    if not os.path.exists(data_file):
        return []
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def load_bahu_series():
    """Load series from bahu/series_data.json"""
    data_file = os.path.join(BAHU_DIR, 'series_data.json')
    if not os.path.exists(data_file):
        return []
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def run_import_task(app_instance, data_items, content_type='movie', category_filter=None):
    """Background task for importing items"""
    with app_instance.app_context():
        global IMPORT_STATUS
        IMPORT_STATUS['running'] = True
        IMPORT_STATUS['total'] = len(data_items)
        IMPORT_STATUS['current'] = 0
        IMPORT_STATUS['imported'] = 0
        IMPORT_STATUS['skipped'] = 0
        IMPORT_STATUS['message'] = f'Starting import of {len(data_items)} items...'
        IMPORT_STATUS['type'] = content_type
        
        try:
            for i, item_data in enumerate(data_items):
                title = item_data.get('title', 'Unknown')
                IMPORT_STATUS['current'] = i + 1
                IMPORT_STATUS['message'] = f"Processing: {title}"
                
                # Check if already exists by URL (most reliable unique key)
                url = item_data.get('url', '')
                existing = None
                if url:
                    existing = Movie.query.filter_by(url=url).first()
                
                # Fallback check
                if not existing:
                    # Match source format from import_bahu.py
                    check_source = 'web:bahu:series' if content_type == 'series' else 'web:bahu:movie'
                    existing = Movie.query.filter_by(
                        title=title,
                        source=check_source,
                        content_type=content_type
                    ).first()
                
                if existing:
                    # Optional: Update metadata if needed
                    IMPORT_STATUS['skipped'] += 1
                    continue
                
                # Create new entry
                item_cat = item_data.get('category', '') or (category_filter if category_filter else '')
                
                new_item = Movie(
                    title=title,
                    description=item_data.get('description', item_cat),
                    image=item_data.get('poster', ''),
                    url=item_data.get('url', ''),
                    source='web:bahu:series' if content_type == 'series' else 'web:bahu:movie',
                    tags=item_cat,
                    content_type=content_type,
                    language='hu',
                    added_at=datetime.utcnow()
                )
                
                db.session.add(new_item)
                IMPORT_STATUS['imported'] += 1
                
                # Update group count occasionally or at end? 
                # Doing it per item ensures consistency but is slower. 
                # Let's do it per item for now as sqlite is fast enough.
                group_source = 'web:bahu' # Consistent with importer
                group = MovieGroup.query.filter_by(name=item_cat, source=group_source).first()
                if not group:
                    group_name = f'Bahu.tv (Series) - {item_cat}' if content_type == 'series' else f'Bahu.tv - {item_cat}'
                    group = MovieGroup(
                        name=item_cat,
                        source=group_source,
                        description=group_name,
                        movie_count=0
                    )
                    db.session.add(group)
                
                group.movie_count += 1
                
                # Commit every 10 items or so? 
                if i % 10 == 0:
                    db.session.commit()
            
            db.session.commit()
            IMPORT_STATUS['message'] = 'Import complete!'
            
        except Exception as e:
            db.session.rollback()
            IMPORT_STATUS['message'] = f'Error: {str(e)}'
        finally:
            IMPORT_STATUS['running'] = False

def get_bahu_stats():
    """Get statistics about bahu movies and series"""
    movies = load_bahu_data()
    series = load_bahu_series()
    
    # Count by category
    from collections import Counter
    movie_categories = Counter([m.get('category', 'Unknown') for m in movies])
    series_categories = Counter([s.get('category', 'Unknown') for s in series])
    
    # Count imported movies
    # Count imported movies (support both web:bahu and bahu.tv source formats)
    imported_movies_count = Movie.query.filter(Movie.source.ilike('%bahu%'), Movie.content_type == 'movie').count()
    imported_series_count = Movie.query.filter(Movie.source.ilike('%bahu%'), Movie.content_type == 'series').count()
    
    # Get last scrape time
    summary_file = os.path.join(BAHU_DIR, 'summary.txt')
    last_scrape = 'Never'
    if os.path.exists(summary_file):
        try:
            mtime = os.path.getmtime(summary_file)
            last_scrape = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        except:
            pass
    
    return {
        'total_movies': len(movies),
        'total_series': len(series),
        'imported_movies': imported_movies_count,
        'imported_series': imported_series_count,
        'movie_categories': movie_categories,
        'series_categories': series_categories,
        'last_scrape': last_scrape
    }

@bp.route('/bahu-manage')
def bahu_manage():
    """Bahu.tv management page"""
    stats = get_bahu_stats()
    
    # Prepare category data for movies
    categories = []
    for cat_name, count in sorted(stats['movie_categories'].items(), key=lambda x: x[1], reverse=True):
        # Count how many from this category are imported
        # Count how many from this category are imported
        imported = Movie.query.filter(Movie.source.ilike('%bahu%'), Movie.content_type == 'movie').filter(
            Movie.tags.like(f'%{cat_name}%')
        ).count()
        
        categories.append({
            'name': cat_name,
            'count': count,
            'imported': imported
        })
        
    # Prepare category data for series
    series_categories = []
    for cat_name, count in sorted(stats['series_categories'].items(), key=lambda x: x[1], reverse=True):
        # Count how many from this category are imported
        # Count how many from this category are imported
        imported = Movie.query.filter(Movie.source.ilike('%bahu%'), Movie.content_type == 'series').filter(
            Movie.tags.like(f'%{cat_name}%')
        ).count()
        
        series_categories.append({
            'name': cat_name,
            'count': count,
            'imported': imported
        })
    
    return render_template('sources_bahu.html',
                         title='Bahu.tv Management',
                         active_page='bahu_manage',
                         bahu_count=stats['total_movies'],
                         bahu_series_count=stats['total_series'],
                         imported_count=stats['imported_movies'],
                         imported_series_count=stats['imported_series'],
                         categories_count=len(stats['movie_categories']),
                         series_categories_count=len(stats['series_categories']),
                         last_scrape=stats['last_scrape'],
                         categories=categories,
                         series_categories=series_categories)

@bp.route('/bahu-import-all', methods=['POST'])
def bahu_import_all():
    """Import all movies from bahu.tv"""
    from flask import current_app
    movies = load_bahu_data()
    
    app = current_app._get_current_object()
    thread = threading.Thread(target=run_import_task, args=(app, movies, 'movie'))
    thread.start()
    
    return jsonify({'success': True, 'message': 'Import started in background'})

@bp.route('/bahu-import-series-all', methods=['POST'])
def bahu_import_series_all():
    """Import all series from bahu.tv"""
    from flask import current_app
    series_list = load_bahu_series()
    
    app = current_app._get_current_object()
    thread = threading.Thread(target=run_import_task, args=(app, series_list, 'series'))
    thread.start()
    
    return jsonify({'success': True, 'message': 'Import started in background'})

@bp.route('/bahu-import-category', methods=['POST'])
def bahu_import_category():
    """Import movies from specific category"""
    from flask import current_app
    data = request.get_json()
    category = data.get('category')
    content_type = data.get('type', 'movie') # 'movie' or 'series'
    
    if not category:
        return jsonify({'success': False, 'error': 'No category specified'}), 400
    
    if content_type == 'series':
        source_data = load_bahu_series()
    else:
        source_data = load_bahu_data()
        
    category_items = [m for m in source_data if m.get('category') == category]
    
    app = current_app._get_current_object()
    thread = threading.Thread(target=run_import_task, args=(app, category_items, content_type, category))
    thread.start()
    
    return jsonify({'success': True, 'message': f'Import of {category} started in background'})

@bp.route('/bahu-run-scraper', methods=['POST'])
def bahu_run_scraper():
    """Run bahu.tv scraper"""
    import subprocess
    
    try:
        scraper_path = os.path.join(BAHU_DIR, 'scraper_v2.py')
        subprocess.Popen([sys.executable, scraper_path], cwd=BAHU_DIR)
        return jsonify({
            'success': True,
            'message': 'Bahu.tv scraper started in background'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to start scraper: {str(e)}'
        }), 500

# Register playlist route at root level (not under /sources)
from flask import Response

@bp.route('/bahu-playlist.m3u8')
def bahu_playlist():
    """Generate M3U8 playlist from Bahu.tv movies"""
    from urllib.parse import quote
    
    movies = load_bahu_data()
    
    # Sort by category
    movies.sort(key=lambda x: x.get('category', 'Unknown'))
    
    m3u = "#EXTM3U\n"
    
    # Get server URL from request
    server_url = request.host_url.rstrip('/')
    
    for movie in movies:
        title = movie.get('title', 'Unknown')
        poster = movie.get('poster', '')
        category = movie.get('category', 'Movies')
        page_url = movie.get('url', '')
        
        # M3U format with proxy through /bahu-watch
        m3u += f'#EXTINF:-1 tvg-logo="{poster}" group-title="{category}",{title}\n'
        # Use /sources/bahu-watch endpoint to extract stream
        m3u += f'{server_url}/sources/bahu-watch?url={quote(page_url)}\n'
    
    return Response(m3u, mimetype='audio/x-mpegurl')

@bp.route('/bahu-watch')
def bahu_watch():
    """Extract and redirect to Bahu.tv stream"""
    from urllib.parse import unquote
    from flask import redirect
    import logging
    
    page_url = request.args.get('url')
    if not page_url:
        return "Missing URL parameter", 400
    
    page_url = unquote(page_url)
    logging.info(f"Bahu watch request for: {page_url}")
    
    try:
        # Import bahu extractor
        import sys
        sys.path.insert(0, BAHU_DIR)
        import extractor
        
        # Extract stream URL
        stream_url = extractor.get_stream_url(page_url)
        
        if stream_url:
            logging.info(f"Redirecting to: {stream_url}")
            return redirect(stream_url, code=302)
        else:
            logging.error(f"Failed to extract stream from: {page_url}")
            return "Stream extraction failed", 404
            
    except Exception as e:
        logging.error(f"Bahu watch error: {e}")
        return f"Error: {str(e)}", 500


@bp.route('/bahu-series-playlist.m3u8')
def bahu_series_playlist():
    """Generate M3U8 playlist from Bahu.tv series"""
    from urllib.parse import quote
    
    series_list = load_bahu_series()
    
    # Sort by category
    series_list.sort(key=lambda x: x.get('category', 'Unknown'))
    
    m3u = "#EXTM3U\n"
    
    # Get server URL from request
    server_url = request.host_url.rstrip('/')
    
    for series in series_list:
        title = series.get('title', 'Unknown')
        poster = series.get('poster', '')
        category = series.get('category', 'Series')
        page_url = series.get('url', '')
        
        # M3U format with proxy through /bahu-watch
        m3u += f'#EXTINF:-1 tvg-logo="{poster}" group-title="{category}",{title}\n'
        # Use /sources/bahu-watch endpoint to extract stream
        m3u += f'{server_url}/sources/bahu-watch?url={quote(page_url)}\n'
    
    return Response(m3u, mimetype='audio/x-mpegurl')

@bp.route('/bahu-scraper-status')
def bahu_scraper_status():
    """Get scraper status from JSON file"""
    status_file = os.path.join(BAHU_DIR, 'scraper_status.json')
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except:
            pass
    return jsonify({"status": "Idle", "total_found": 0, "total_added": 0})

@bp.route('/bahu-run-completeness-check', methods=['POST'])
def bahu_run_completeness_check():
    """Run completeness check script"""
    import subprocess
    try:
        check_script = os.path.join(BAHU_DIR, 'check_bahu_completeness.py')
        subprocess.Popen([sys.executable, check_script], cwd=BAHU_DIR)
        
        return jsonify({
            'success': True,
            'message': 'Completeness check started. Check log below.'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/bahu-completeness-log')
def bahu_completeness_log():
    """Get last completeness check log"""
    log_file = os.path.join(BAHU_DIR, 'completeness_last_check.txt')
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'log': content})
        except Exception as e:
            return jsonify({'log': f"Error reading log: {str(e)}"})
    return jsonify({'log': "No log found. Run check first."})
