from app import create_app, db
from app.models import Movie, Stream, Playlist, History, SiteConfig
import json
import os
import datetime

app = create_app()

def migrate():
    with app.app_context():
        # Create Tables
        db.create_all()
        
        print("Migrating Movies...")
        if os.path.exists('movies_db.json'):
            with open('movies_db.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for m_data in data:
                # Check exist
                if not Movie.query.filter_by(url=m_data.get('url')).first():
                    m = Movie(
                        title=m_data.get('title', 'Unknown'),
                        url=m_data.get('url'),
                        image=m_data.get('image'),
                        description=m_data.get('description'),
                        source=m_data.get('source', 'manual')
                    )
                    db.session.add(m)
                    db.session.flush() # ID needed
                    
                    for s_data in m_data.get('streams', []):
                        s = Stream(
                            movie_id=m.id,
                            provider=s_data.get('provider'),
                            url=s_data.get('url')
                        )
                        db.session.add(s)
            db.session.commit()
        
        print("Migrating Playlists...")
        if os.path.exists('playlists.json'):
            with open('playlists.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            for p_data in data:
                if not Playlist.query.get(p_data['id']):
                     p = Playlist(
                         id=p_data['id'],
                         name=p_data['name'],
                         max_connections=p_data.get('max_connections', 0),
                         allowed_countries=p_data.get('allowed_countries', '')
                     )
                     db.session.add(p)
            db.session.commit()
            
        print("Migration Complete!")

if __name__ == '__main__':
    migrate()
