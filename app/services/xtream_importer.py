"""
Xtream Codes Source Importer Service
Imports content from external Xtream Codes servers
"""

import requests
from datetime import datetime
import logging
from ..models import db, Movie, Stream, XtreamSource

class XtreamImporter:
    """Service for importing content from external Xtream Codes servers."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def test_connection(self, server_url, username, password):
        """
        Test connection to Xtream server and get server info.
        
        Returns:
            dict: {
                'success': bool,
                'server_info': dict,
                'vod_count': int,
                'live_count': int,
                'series_count': int,
                'error': str (if failed)
            }
        """
        try:
            # Clean server URL
            server_url = server_url.rstrip('/')
            
            # Test connection with player_api.php
            url = f"{server_url}/player_api.php"
            params = {
                'username': username,
                'password': password
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if authentication was successful
            if 'user_info' not in data:
                return {
                    'success': False,
                    'error': 'Invalid credentials or server response'
                }
            
            # Get VOD count
            vod_count = 0
            try:
                vod_params = params.copy()
                vod_params['action'] = 'get_vod_streams'
                vod_response = self.session.get(url, params=vod_params, timeout=10)
                vod_data = vod_response.json()
                vod_count = len(vod_data) if isinstance(vod_data, list) else 0
            except:
                pass
            
            # Get Live count
            live_count = 0
            try:
                live_params = params.copy()
                live_params['action'] = 'get_live_streams'
                live_response = self.session.get(url, params=live_params, timeout=10)
                live_data = live_response.json()
                live_count = len(live_data) if isinstance(live_data, list) else 0
            except:
                pass
            
            # Get Series count
            series_count = 0
            try:
                series_params = params.copy()
                series_params['action'] = 'get_series'
                series_response = self.session.get(url, params=series_params, timeout=10)
                series_data = series_response.json()
                series_count = len(series_data) if isinstance(series_data, list) else 0
            except:
                pass
            
            return {
                'success': True,
                'server_info': data.get('server_info', {}),
                'user_info': data.get('user_info', {}),
                'vod_count': vod_count,
                'live_count': live_count,
                'series_count': series_count
            }
            
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Connection timeout'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Could not connect to server'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _fetch_categories(self, source, action):
        """
        Fetch categories map (id -> name) for a specific action.
        """
        try:
            url = f"{source.server_url.rstrip('/')}/player_api.php"
            params = {
                'username': source.username,
                'password': source.password,
                'action': action
            }
            res = self.session.get(url, params=params, timeout=45)
            if res.status_code != 200: 
                logging.error(f"Failed to fetch categories: HTTP {res.status_code}")
                return {}
            
            data = res.json()
            if not isinstance(data, list): return {}
            
            # Create map: category_id -> category_name
            cat_map = {}
            for c in data:
                cid = c.get('category_id')
                cname = c.get('category_name')
                if cid and cname:
                    cat_map[str(cid)] = cname
            
            logging.info(f"Fetched {len(cat_map)} categories for {action}")
            return cat_map
        except Exception as e:
            logging.error(f"Error fetching categories for {action}: {e}")
            return {}

    def import_vod(self, source, progress_callback=None):
        """Import VOD (movies) from Xtream source."""
        try:
            server_url = source.server_url.rstrip('/')
            url = f"{server_url}/player_api.php"
            
            # 1. Fetch Categories first
            logging.info(f"Fetching VOD categories from {source.name}...")
            if progress_callback: progress_callback(f"Fetching VOD categories from {source.name}...")
            cat_map = self._fetch_categories(source, 'get_vod_categories')
            
            # Get VOD streams
            params = {
                'username': source.username,
                'password': source.password,
                'action': 'get_vod_streams'
            }
            
            logging.info(f"Fetching VOD list from {source.name}...")
            if progress_callback: progress_callback(f"Fetching VOD list from {source.name}...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            vod_list = response.json()
            
            if not isinstance(vod_list, list):
                return {'success': False, 'error': 'Invalid VOD data received'}
            
            total_items = len(vod_list)
            logging.info(f"Processing {total_items} VOD items from {source.name}...")
            
            logging.info("Loading global existing index...")
            if progress_callback: progress_callback("Loading existing index...")
            existing_query = db.session.query(Movie.id, Movie.url, Movie.tags, Movie.image, Movie.source)
            # ... existing_map logic ...
            
            existing_map = {
                m.url: {
                    'id': m.id, 
                    'tags': m.tags, 
                    'image': m.image,
                    'source': m.source
                } for m in existing_query.all()
            }
            logging.info(f"Loaded global index of {len(existing_map)} items.")
            
            imported = 0
            skipped = 0
            updated = 0
            count_since_commit = 0
            
            processed = 0
            
            for vod in vod_list:
                processed += 1
                if progress_callback and processed % 50 == 0:
                     progress_callback(f"Importing Movies ({processed}/{total_items})...", 
                                      {'vod': {'imported': imported, 'updated': updated, 'skipped': skipped, 'total': total_items}})
                try:
                    stream_id = vod.get('stream_id')
                    if not stream_id: continue
                    
                    ext = vod.get('container_extension', 'mp4')
                    stream_url = f"{server_url}/movie/{source.username}/{source.password}/{stream_id}.{ext}"
                    existing_data = existing_map.get(stream_url)
                    
                    # Resolve Category Name
                    cat_name = vod.get('category_name')
                    if not cat_name:
                        cid = vod.get('category_id')
                        if cid: cat_name = cat_map.get(str(cid), '')
                    if not cat_name: 
                        cat_name = 'Uncategorized'
                        if processed < 20 and vod.get('category_id'): # Log sample
                             logging.warning(f"Unmapped VOD category ID: {vod.get('category_id')}")
                    
                    if existing_data:
                        current_source_name = f"xtream:{source.name}"
                        if existing_data['source'] == current_source_name:
                            changed = False
                            # Compare tags
                            current_tags = existing_data['tags'] or ''
                            if current_tags != cat_name:
                                changed = True
                            
                            # Compare image
                            current_image = existing_data['image'] or ''
                            new_image = vod.get('stream_icon', '')
                            if new_image and current_image != new_image:
                                changed = True

                            if changed:
                                movie = Movie.query.get(existing_data['id'])
                                if movie:
                                    movie.tags = cat_name
                                    if new_image: movie.image = new_image
                                    updated += 1
                                    count_since_commit += 1
                            else:
                                skipped += 1
                        else:
                            skipped += 1
                    else:
                        movie = Movie(
                            title=vod.get('name', 'Unknown'),
                            url=stream_url,
                            image=vod.get('stream_icon', ''),
                            description=vod.get('plot', ''),
                            rating=vod.get('rating', ''),
                            duration=vod.get('duration', ''),
                            tags=cat_name,
                            source=f"xtream:{source.name}"
                        )
                        db.session.add(movie)
                        db.session.flush()
                        
                        stream = Stream(
                            movie_id=movie.id,
                            provider=f"xtream:{source.name}",
                            url=stream_url
                        )
                        db.session.add(stream)
                        imported += 1
                        count_since_commit += 1
                        
                        existing_map[stream_url] = {
                            'id': movie.id,
                            'tags': movie.tags,
                            'image': movie.image,
                            'source': movie.source
                        }
                    
                    if count_since_commit >= batch_size:
                        db.session.commit()
                        logging.info(f"Sync progress: {imported} imported, {updated} updated, {skipped} skipped")
                        count_since_commit = 0
                        
                except Exception as e:
                    logging.error(f"Error processed item: {e}")
                    db.session.rollback()
                    continue
            
            db.session.commit()
            source.vod_count = len(vod_list)
            source.last_sync = datetime.now()
            db.session.commit()
            
            return {'success': True, 'imported': imported, 'updated': updated, 'skipped': skipped, 'total': len(vod_list)}
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error importing VOD from {source.name}: {e}")
            return {'success': False, 'error': str(e)}
    
    def import_series(self, source, progress_callback=None):
        """Import Series from Xtream source."""
        try:
            server_url = source.server_url.rstrip('/')
            url = f"{server_url}/player_api.php"
            
            # Fetch Series Categories
            logging.info(f"Fetching Series categories from {source.name}...")
            if progress_callback: progress_callback(f"Fetching Series categories from {source.name}...")
            cat_map = self._fetch_categories(source, 'get_series_categories')
            
            params = {
                'username': source.username,
                'password': source.password,
                'action': 'get_series'
            }
            
            if progress_callback: progress_callback(f"Fetching Series list from {source.name}...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            series_list = response.json()
            
            if not isinstance(series_list, list): return {'success': False, 'error': 'Invalid Series data'}
            
            total_items = len(series_list)
            
            imported = 0
            skipped = 0
            count_since_commit = 0
            processed = 0
            
            for series in series_list:
                processed += 1
                if progress_callback and processed % 20 == 0:
                     progress_callback(f"Importing Series ({processed}/{total_items})...", 
                                      {'series': {'imported': imported, 'skipped': skipped, 'total': total_items}})

                try:
                    series_id = series.get('series_id')
                    if not series_id: continue
                    
                    # Resolve Category Name
                    cat_name = series.get('category_name')
                    if not cat_name:
                        cid = series.get('category_id')
                        if cid: cat_name = cat_map.get(str(cid), '')
                    if not cat_name: cat_name = 'Uncategorized'
                    
                    # Get series info with episodes
                    info_params = {
                        'username': source.username,
                        'password': source.password,
                        'action': 'get_series_info',
                        'series_id': series_id
                    }
                    
                    info_response = self.session.get(url, params=info_params, timeout=10)
                    info_data = info_response.json()
                    episodes = info_data.get('episodes', {})
                    
                    for season_num, season_episodes in episodes.items():
                        for episode in season_episodes:
                            try:
                                episode_id = episode.get('id')
                                if not episode_id: continue
                                
                                stream_url = f"{server_url}/series/{source.username}/{source.password}/{episode_id}.mp4"
                                existing = Movie.query.filter_by(url=stream_url).first()
                                if existing:
                                    # Update logic
                                    new_tags = f"Series, {cat_name}"
                                    if existing.tags != new_tags:
                                        existing.tags = new_tags
                                    skipped += 1
                                    continue
                                
                                title = f"{series.get('name', 'Unknown')} - S{season_num}E{episode.get('episode_num', '?')}"
                                if episode.get('title'): title += f" - {episode.get('title')}"
                                
                                movie = Movie(
                                    title=title,
                                    url=stream_url,
                                    image=episode.get('info', {}).get('movie_image', series.get('cover', '')),
                                    description=episode.get('info', {}).get('plot', ''),
                                    rating=episode.get('info', {}).get('rating', ''),
                                    duration=episode.get('info', {}).get('duration', ''),
                                    tags=f"Series, {cat_name}",
                                    source=f"xtream:{source.name}:series"
                                )
                                db.session.add(movie)
                                db.session.flush()
                                db.session.add(Stream(movie_id=movie.id, provider=f"xtream:{source.name}", url=stream_url))
                                imported += 1
                                if imported % 50 == 0: db.session.commit()
                            except: continue
                except: continue
            
            db.session.commit()
            source.series_count = len(series_list)
            source.last_sync = datetime.now()
            db.session.commit()
            return {'success': True, 'imported': imported, 'skipped': skipped}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def import_live(self, source, progress_callback=None):
        """Import Live TV channels."""
        try:
            # ... (fetch logic remains same until loop) ...
            server_url = source.server_url.rstrip('/')
            url = f"{server_url}/player_api.php"
            
            # Fetch Live Categories
            logging.info(f"Fetching Live categories from {source.name}...")
            if progress_callback: progress_callback(f"Fetching Live categories from {source.name}...")
            cat_map = self._fetch_categories(source, 'get_live_categories')
            
            params = {
                'username': source.username,
                'password': source.password,
                'action': 'get_live_streams'
            }
            
            logging.info(f"Fetching Live TV list from {source.name}...")
            if progress_callback: progress_callback(f"Fetching Live TV list from {source.name}...")
            response = self.session.get(url, params=params, timeout=45)
            response.raise_for_status()
            live_list = response.json()
            
            if not isinstance(live_list, list): return {'success': False, 'error': 'Invalid Live TV data'}
            total_items = len(live_list)
            
            logging.info("Loading global existing index for Live TV...")
            existing_query = db.session.query(Movie.id, Movie.url, Movie.tags, Movie.image, Movie.source, Movie.epg_channel_id, Movie.tv_archive, Movie.tv_archive_duration)
            existing_map = {m.url: {
                'id': m.id, 
                'tags': m.tags, 
                'image': m.image, 
                'source': m.source,
                'epg_channel_id': m.epg_channel_id,
                'tv_archive': m.tv_archive,
                'tv_archive_duration': m.tv_archive_duration
            } for m in existing_query.all()}
            
            imported = 0
            updated = 0
            skipped = 0
            count_since_commit = 0
            
            processed = 0
             
            from sqlalchemy.exc import IntegrityError

            for channel in live_list:
                processed += 1
                if progress_callback and processed % 20 == 0:
                     progress_callback(f"Importing Live Channels ({processed}/{total_items})...", 
                                      {'live': {'imported': imported, 'updated': updated, 'skipped': skipped, 'total': total_items}})

                try:
                    stream_id = channel.get('stream_id')
                    if not stream_id: continue
                    # ... (rest of logic) ...
                    
                    stream_url = f"{server_url}/live/{source.username}/{source.password}/{stream_id}.ts"
                    existing_data = existing_map.get(stream_url)
                    
                    # Resolve Category
                    cat_name = channel.get('category_name')
                    if not cat_name:
                        cid = channel.get('category_id')
                        if cid: cat_name = cat_map.get(str(cid), '')
                    if not cat_name: cat_name = 'Uncategorized'
                    
                    effective_tags = f"Live TV, {cat_name}"
                    
                    if existing_data:
                        if existing_data['source'] == f"xtream:{source.name}:live":
                            changed = False
                            if (existing_data['tags'] or '') != effective_tags: changed = True
                            new_image = channel.get('stream_icon', '')
                            if new_image and (existing_data['image'] or '') != new_image: changed = True
                            
                            # Check EPG/Timeshift changes
                            if str(existing_data.get('epg_channel_id') or '') != str(channel.get('epg_channel_id') or ''): changed = True
                            if int(existing_data.get('tv_archive') or 0) != int(channel.get('tv_archive', 0)): changed = True
                            if int(existing_data.get('tv_archive_duration') or 0) != int(channel.get('tv_archive_duration', 0)): changed = True
                            
                            if changed:
                                movie = Movie.query.get(existing_data['id'])
                                if movie:
                                    movie.tags = effective_tags
                                    if new_image: movie.image = new_image
                                    # Update EPG and timeshift data
                                    movie.epg_channel_id = channel.get('epg_channel_id')
                                    movie.tv_archive = channel.get('tv_archive', 0)
                                    movie.tv_archive_duration = channel.get('tv_archive_duration', 0)
                                    updated += 1
                                    count_since_commit += 1
                            else: skipped += 1
                        else: skipped += 1
                    else:
                        movie = Movie(
                            title=channel.get('name', 'Unknown Channel'),
                            url=stream_url,
                            image=channel.get('stream_icon', ''),
                            description=f"Live TV Channel from {source.name}",
                            tags=effective_tags,
                            source=f"xtream:{source.name}:live",
                            epg_channel_id=channel.get('epg_channel_id'),
                            tv_archive=channel.get('tv_archive', 0),
                            tv_archive_duration=channel.get('tv_archive_duration', 0)
                        )
                        db.session.add(movie)
                        try:
                            db.session.flush()
                            db.session.add(Stream(movie_id=movie.id, provider=f"xtream:{source.name}", url=stream_url))
                            imported += 1
                            count_since_commit += 1
                            existing_map[stream_url] = {'id': movie.id, 'tags': movie.tags, 'image': movie.image, 'source': movie.source}
                        except IntegrityError:
                            db.session.rollback()
                            logging.warning(f"IntegrityError (Duplicate): {stream_url} - Skipping.")
                            skipped += 1
                            continue
                            
                    if count_since_commit >= batch_size:
                        db.session.commit()
                        count_since_commit = 0
                        
                except Exception as e:
                    logging.error(f"Error processing channel {channel.get('name')}: {e}")
                    db.session.rollback()
                    continue
            
            db.session.commit()
            source.live_count = len(live_list)
            source.last_sync = datetime.now()
            db.session.commit()
            return {'success': True, 'imported': imported, 'updated': updated, 'skipped': skipped}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def sync_source(self, source_id, progress_callback=None, content_type='all'):
        """Sync content from a source. content_type: 'all', 'vod', 'series', 'live'"""
        source = XtreamSource.query.get(source_id)
        if not source: return {'success': False, 'error': 'Source not found'}
        
        details = {'vod': {'status': 'pending'}, 'series': {'status': 'pending'}, 'live': {'status': 'pending'}}
        total_imported = 0
        total_skipped = 0
        
        # Determine what to sync based on content_type and source settings
        # If content_type is specific (not 'all'), we force sync that type even if disabled in source settings.
        # If 'all', we respect source settings.
        
        do_vod = (content_type == 'vod') or (content_type == 'all' and source.import_vod)
        do_series = (content_type == 'series') or (content_type == 'all' and source.import_series)
        do_live = (content_type == 'live') or (content_type == 'all' and source.import_live)
        
        if do_vod:
            if progress_callback: progress_callback('Importing VOD...', details)
            res = self.import_vod(source, progress_callback=progress_callback)
            details['vod'].update(res)
            details['vod']['status'] = 'completed' if res.get('success') else 'error'
            total_imported += res.get('imported', 0)
            total_skipped += res.get('skipped', 0)
            
        if do_series:
            if progress_callback: progress_callback('Importing Series...', details)
            res = self.import_series(source, progress_callback=progress_callback)
            details['series'].update(res)
            details['series']['status'] = 'completed' if res.get('success') else 'error'
            total_imported += res.get('imported', 0)
            total_skipped += res.get('skipped', 0)
            
        if do_live:
            if progress_callback: progress_callback('Importing Live...', details)
            res = self.import_live(source, progress_callback=progress_callback)
            details['live'].update(res)
            details['live']['status'] = 'completed' if res.get('success') else 'error'
            total_imported += res.get('imported', 0)
            total_skipped += res.get('skipped', 0)
            
        return {'success': True, 'imported_count': total_imported, 'details': details}

# Global instance
xtream_importer = XtreamImporter()
