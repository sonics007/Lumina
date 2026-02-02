from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from ..models import db, Movie
from ..services import group_service
from sqlalchemy import or_, not_

groups_bp = Blueprint('groups', __name__, url_prefix='/groups')

@groups_bp.route('/')
def index():
    return redirect(url_for('groups.manage'))

@groups_bp.route('/manage')
def manage():
    """Page to manage group names and ordering, separated by type."""
    username = request.args.get('username')
    config = group_service.load_config(username)
    
    def process_groups(query_result, context):
        # query_result is list of (tag_str, source_str)
        
        # 1. Aggregate sources per tag
        tag_sources = {} # { 'CleanTagName': set([source1, source2]) }
        
        for t_str, s_str in query_result:
            if not t_str: continue
            
            # Format source for display
            display_source = s_str or "Unknown"
            if s_str:
                if s_str.startswith('xtream:'):
                    # Format: xtream:SourceName:type -> SourceName
                    parts = s_str.split(':')
                    if len(parts) >= 2:
                        display_source = parts[1]
                elif s_str.startswith('web:'):
                    start = s_str.find(':') + 1
                    display_source = s_str[start:].capitalize()
            
            # Normalize Bahu variants
            if display_source and display_source.lower() in ['bahu.tv', 'bahz']:
                display_source = 'Bahu'

            items = []
            items = []
            # Logic for all types: split by comma
            items = [x.strip() for x in t_str.split(',')]
                 
            valid_items = []
            for item in items:
                if not item: continue
                if context == 'live' and item.lower() == 'live tv': continue 
                if context == 'series' and item == 'Series': continue
                valid_items.append(item)
            
            if not valid_items:
                valid_items.append('Uncategorized')

            for item in valid_items:
                if item not in tag_sources: tag_sources[item] = set()
                tag_sources[item].add(display_source)

        # 2. Build List
        groups = []
        for tag_name, sources in tag_sources.items():
            conf = config.get(tag_name, {})
            key_order = f'order_{context}'
            # Fallback to global order if specific not found, then 9999
            order = conf.get(key_order, conf.get('order', 9999))
            
            groups.append({
                'original_name': tag_name,
                'display_name': conf.get('display_name', tag_name),
                'order': order,
                'enabled': conf.get('enabled', True),
                'sources': sorted(list(sources))
            })
        
        # Sort by order, then display name
        groups.sort(key=lambda x: (x['order'], x['display_name']))
        return groups

    # 1. Movies (Exclude Series and Live)
    # Query: (tags, source)
    movie_tags_q = db.session.query(Movie.tags, Movie.source).filter(
        not_(Movie.source.ilike('%:series')),
        not_(Movie.source.ilike('%:live')),
        not_(Movie.tags.ilike('%Live TV%'))
    ).distinct().all()
    movie_groups = process_groups(movie_tags_q, 'movie')
    
    # 2. Series
    series_tags_q = db.session.query(Movie.tags, Movie.source).filter(Movie.source.ilike('%:series')).distinct().all()
    series_groups = process_groups(series_tags_q, 'series')
    
    # 3. Live
    live_tags_q = db.session.query(Movie.tags, Movie.source).filter(
        or_(Movie.tags.ilike('%Live TV%'), Movie.source.ilike('%:live'))
    ).distinct().all()
    live_groups = process_groups(live_tags_q, 'live')
    
    # Collect Unique Sources
    all_sources = set()
    for g in movie_groups + series_groups + live_groups:
        for s in g.get('sources', []):
            all_sources.add(s)
    
    return render_template('groups_manage.html', 
                           username=username,
                           movie_groups=movie_groups,
                           series_groups=series_groups,
                           live_groups=live_groups,
                           sources=sorted(list(all_sources)))

@groups_bp.route('/api/save', methods=['POST'])
def api_save():
    try:
        data = request.json
        # Expected format: { 'movie': [...], 'series': [...], 'live': [...] }
        
        username = data.get('username')
        config = group_service.load_config(username)
        
        for context in ['movie', 'series', 'live']:
            items = data.get(context, [])
            for item in items:
                original = item.get('original')
                if not original: continue
                
                if original not in config:
                    config[original] = {}
                
                # Update display name (Global, last write wins)
                config[original]['display_name'] = item.get('display', original)
                
                # Update Order (Context Specific)
                config[original][f'order_{context}'] = int(item.get('order', 9999))
                config[original]['enabled'] = item.get('enabled', True)
                
        group_service.save_config(config, username)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
