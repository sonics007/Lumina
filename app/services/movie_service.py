from ..models import db, Movie, Stream
from .history_service import log_history
import logging

class MovieService:
    @staticmethod
    def add_or_update_movie(data):
        """
        Centrálna metóda pre pridanie alebo update filmu zo scraperov.
        data = {
            'title': str,
            'url': str (source page url),
            'image': str,
            'description': str,
            'tags': str,
            'source': str (napr. 'film-adult.top'),
            'streams': [
                {'provider': 'hglink', 'url': '...'},
                ...
            ]
        }
        Returns: Movie objekt
        """
        try:
            # 1. Hľadáme existujúci film podľa URL stránky (najpresnejšie)
            movie = Movie.query.filter_by(url=data.get('url')).first()
            
            # 2. Ak nenájde, skúsime podľa názvu (menej presné, ale užitočné pre re-scrape)
            if not movie and data.get('title'):
                movie = Movie.query.filter_by(title=data.get('title')).first()
                
            is_new = False
            if not movie:
                is_new = True
                movie = Movie(
                    url=data.get('url'),
                    title=data.get('title', 'Unknown'),
                    source=data.get('source', 'manual')
                )
                db.session.add(movie)
                logging.info(f"Creating new movie: {movie.title}")
            else:
                logging.info(f"Updating existing movie: {movie.title}")

            # Update metadát (len ak sú poskytnuté)
            if data.get('image'): movie.image = data.get('image')
            if data.get('description'): movie.description = data.get('description')
            if data.get('tags'): movie.tags = data.get('tags')
            
            # Musíme flushnúť, aby sme mali movie.id
            db.session.flush()
            
            # Spracovanie streamov
            if 'streams' in data and data['streams']:
                # Získame existujúce streamy pre tento film
                existing_streams = {s.url: s for s in movie.streams}
                
                for s_data in data['streams']:
                    stream_url = s_data.get('url')
                    provider = s_data.get('provider', 'unknown')
                    
                    if not stream_url: continue
                    
                    # Validácia URL (tu môžeme zachytiť napr. tie zlé HGLink /e/ bez ID)
                    if 'hglink.to/e/' in stream_url and stream_url.strip().endswith('/e/'):
                        logging.warning(f"Skipping broken HGLink URL: {stream_url} for movie {movie.title}")
                        continue
                        
                    if stream_url in existing_streams:
                        # Update providera ak treba
                        if existing_streams[stream_url].provider != provider:
                             existing_streams[stream_url].provider = provider
                    else:
                        # Pridať nový stream
                        new_stream = Stream(
                            movie_id=movie.id,
                            provider=provider,
                            url=stream_url
                        )
                        db.session.add(new_stream)
                        logging.info(f"Added stream {provider} to {movie.title}")

            db.session.commit()
            
            if is_new:
                log_history("Import", f"Added movie: {movie.title}")
            
            return movie
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in add_or_update_movie: {e}")
            raise e

    @staticmethod
    def get_stats():
        return {
            'movies': Movie.query.count(),
            'streams': Stream.query.count()
        }

movie_service = MovieService()
