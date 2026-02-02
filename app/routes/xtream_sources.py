from flask import Blueprint, render_template, request, jsonify
from ..models import db, XtreamSource, Movie
from ..services.xtream_importer import xtream_importer
from datetime import datetime

xtream_sources_bp = Blueprint('xtream_sources', __name__, url_prefix='/xtream_sources')

@xtream_sources_bp.before_request
def log_request():
    """Log all requests to this blueprint."""
    print(f"[REQUEST] {request.method} {request.path} - {request.endpoint}")

@xtream_sources_bp.route('/')
def index():
    """Display all Xtream sources."""
    sources = XtreamSource.query.all()
    
    # Calculate totals
    total_vod = sum(s.vod_count or 0 for s in sources)
    total_live = sum(s.live_count or 0 for s in sources)
    total_series = sum(s.series_count or 0 for s in sources)
    
    # Format last_sync for display
    for source in sources:
        if source.last_sync:
            source.last_sync = source.last_sync.strftime('%Y-%m-%d %H:%M')
    
    return render_template('xtream_sources.html',
                         title="Xtream Sources",
                         active_page='xtream_sources',
                         sources=sources,
                         total_vod=total_vod,
                         total_live=total_live,
                         total_series=total_series)

@xtream_sources_bp.route('/<int:source_id>/manage')
def manage_source(source_id):
    """Advanced management for a specific source."""
    source = XtreamSource.query.get_or_404(source_id)
    
    # Get all unique categories (tags) for this source
    # This acts as our "Groups"
    # We query strictly by source string matching f"xtream:{source.name}"
    
    # SQLite optimization to get counts per category
    from sqlalchemy import func
    categories = db.session.query(
        Movie.tags, func.count(Movie.id)
    ).filter(
        Movie.source == f"xtream:{source.name}"
    ).group_by(Movie.tags).all()
    
    # Format: [{'name': 'Action', 'count': 50}, ...]
    groups = [{'name': c[0] or 'Uncategorized', 'count': c[1]} for c in categories]
    groups.sort(key=lambda x: x['name'])
    
    return render_template('xtream_manage.html',
                         source=source,
                         groups=groups,
                         active_page='xtream_sources')

@xtream_sources_bp.route('/api/rename_group', methods=['POST'])
def api_rename_group():
    """Rename a category/group for a source."""
    source_id = request.form.get('source_id')
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')
    
    if not all([source_id, old_name, new_name]):
        return jsonify({'success': False, 'error': 'Missing fields'})
        
    source = XtreamSource.query.get(source_id)
    if not source: return jsonify({'success': False, 'error': 'Source not found'})
    
    # Bulk update
    try:
        movies = Movie.query.filter(
            Movie.source == f"xtream:{source.name}",
            Movie.tags == old_name
        ).all()
        
        count = 0
        for m in movies:
            m.tags = new_name
            count += 1
            
        db.session.commit()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@xtream_sources_bp.route('/<int:source_id>/category/<path:category_name>')
def view_category(source_id, category_name):
    """View movies in a specific category."""
    source = XtreamSource.query.get_or_404(source_id)
    
    if category_name == 'Uncategorized':
        category_name = '' # logic mapping
        
    movies = Movie.query.filter(
        Movie.source == f"xtream:{source.name}",
        Movie.tags == category_name
    ).all()
    
    return render_template('xtream_category.html',
                         source=source,
                         category=category_name or 'Uncategorized',
                         movies=movies)

@xtream_sources_bp.route('/api/delete_content', methods=['POST'])
def api_delete_content():
    """Delete specific content item."""
    movie_id = request.form.get('movie_id')
    Movie.query.filter_by(id=movie_id).delete()
    # Also delete streams
    from ..models import Stream
    Stream.query.filter_by(movie_id=movie_id).delete()
    
    db.session.commit()
    return jsonify({'success': True})

# API Routes
@xtream_sources_bp.route('/api/test_connection', methods=['POST'])
def api_test_connection():
    """Test connection to Xtream server before adding."""
    server_url = request.form.get('server_url')
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not all([server_url, username, password]):
        return jsonify({'success': False, 'error': 'Missing required fields'})
    
    result = xtream_importer.test_connection(server_url, username, password)
    return jsonify(result)

@xtream_sources_bp.route('/api/add', methods=['POST'])
def api_add_source():
    """Add a new Xtream source."""
    try:
        name = request.form.get('name')
        server_url = request.form.get('server_url')
        username = request.form.get('username')
        password = request.form.get('password')
        auto_sync = request.form.get('auto_sync') == 'true'
        import_vod = request.form.get('import_vod') == 'on'
        import_series = request.form.get('import_series') == 'on'
        import_live = request.form.get('import_live') == 'on'
        
        if not all([name, server_url, username, password]):
            return jsonify({'success': False, 'error': 'Missing required fields'})
        
        # Test connection first
        test_result = xtream_importer.test_connection(server_url, username, password)
        if not test_result.get('success'):
            return jsonify({'success': False, 'error': test_result.get('error', 'Connection test failed')})
        
        # Create source
        source = XtreamSource(
            name=name,
            server_url=server_url.rstrip('/'),
            username=username,
            password=password,
            auto_sync=auto_sync,
            import_vod=import_vod,
            import_series=import_series,
            import_live=import_live,
            vod_count=test_result.get('vod_count', 0),
            live_count=test_result.get('live_count', 0),
            series_count=test_result.get('series_count', 0)
        )
        
        db.session.add(source)
        db.session.commit()
        
        return jsonify({'success': True, 'source_id': source.id})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@xtream_sources_bp.route('/api/test/<int:source_id>', methods=['POST'])
def api_test_source(source_id):
    """Test connection to an existing source."""
    source = XtreamSource.query.get(source_id)
    if not source:
        return jsonify({'success': False, 'error': 'Source not found'})
    
    result = xtream_importer.test_connection(source.server_url, source.username, source.password)
    
    # Update counts if successful
    if result.get('success'):
        source.vod_count = result.get('vod_count', 0)
        source.live_count = result.get('live_count', 0)
        source.series_count = result.get('series_count', 0)
        db.session.commit()
    
    return jsonify(result)

@xtream_sources_bp.route('/api/sync/<int:source_id>', methods=['POST'])
def api_sync_source(source_id):
    """Sync content from a source with realtime progress streaming."""
    from flask import Response, stream_with_context
    import json
    
    def generate():
        yield f"data: {json.dumps({'status': 'starting', 'message': 'Initializing sync...'})}\n\n"
        
        try:
            source = XtreamSource.query.get(source_id)
            if not source:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Source not found'})}\n\n"
                return

            sync_type = request.values.get('type', 'all')
            
            def progress_cb(msg, details=None):
                yield f"data: {json.dumps({'status': 'progress', 'message': msg, 'details': details})}\n\n"

            # We need to modify sync_source to accept generator yield?
            # No, we cannot yield from inside the callback easily if it's just a function call.
            # We must wrap it or the importer code must be generator-aware.
            # However, since sync_source calls blocking functions import_vod, etc.
            # and calls callback periodically.
            # Wait, `yield` inside a callback passed to a function that is NOT a generator won't work directly to stream the outer generator.
            # The standard way is to use a shared queue or similar, OR rewrite sync_source to yield.
            
            # Since I can't easily rewrite sync_source to be an iterator without big changes to all import methods,
            # I will assume sync_source calls callback synchronously.
            # But `yield` only works in the generator function body.
            pass
            
            # Use a queue to capture callbacks
            import queue
            q = queue.Queue()
            
            def callback_wrapper(msg, details=None):
                q.put({'status': 'progress', 'message': msg, 'details': details})
            
            # Run sync in a thread so we can yield from queue
            import threading
            from flask import current_app
            app = current_app._get_current_object() # Capture real app object for thread
            
            result_container = {}
            
            def run_sync():
                with app.app_context():
                    try:
                        res = xtream_importer.sync_source(source_id, content_type=sync_type, progress_callback=callback_wrapper)
                        result_container['result'] = res
                    except Exception as e:
                        result_container['error'] = str(e)
                    finally:
                        q.put(None) # Sentinel
            
            t = threading.Thread(target=run_sync)
            t.start()
            
            while True:
                item = q.get()
                if item is None: break
                yield f"data: {json.dumps(item)}\n\n"
            
            t.join()
            
            if 'error' in result_container:
                 yield f"data: {json.dumps({'status': 'error', 'message': result_container['error']})}\n\n"
            else:
                 yield f"data: {json.dumps({'status': 'completed', 'result': result_container['result']})}\n\n"
                 
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@xtream_sources_bp.route('/api/remove/<int:source_id>', methods=['DELETE'])
def api_remove_source(source_id):
    """Remove a source (does not delete imported content)."""
    try:
        source = XtreamSource.query.get(source_id)
        if not source:
            return jsonify({'success': False, 'error': 'Source not found'})
        
        db.session.delete(source)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
