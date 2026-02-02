from app import create_app, db
from app.models import Movie
from sqlalchemy import or_

app = create_app()

with app.app_context():
    print("Fixing missing sources in DB...")
    
    # 1. Update film-adult.top based on URL
    updated_fa = Movie.query.filter(
        Movie.url.like('%film-adult%'),
        or_(Movie.source == None, Movie.source == 'manual', Movie.source == '')
    ).update({
        'source': 'film-adult.top'
    }, synchronize_session=False)
    
    # 2. Update uiiumovie.com based on URL
    updated_uiiu = Movie.query.filter(
        Movie.url.like('%uiiu%'),
        or_(Movie.source == None, Movie.source == 'manual', Movie.source == '')
    ).update({
        'source': 'uiiumovie.com'
    }, synchronize_session=False)
    
    db.session.commit()
    print(f"Fixed {updated_fa} film-adult entries.")
    print(f"Fixed {updated_uiiu} uiiu entries.")
    print("Done.")
