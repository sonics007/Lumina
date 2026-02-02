from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_login import UserMixin

db = SQLAlchemy()

class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(512), unique=True, nullable=False) # Source URL
    image = db.Column(db.String(512))
    description = db.Column(db.Text)
    rating = db.Column(db.String(10))    # e.g. "8.5"
    duration = db.Column(db.String(20))  # e.g. "1h 30m"
    tags = db.Column(db.String(255), index=True)     # e.g. "Action, Drama"
    cast = db.Column(db.Text)            # e.g. "Actor A, Actor B"
    source = db.Column(db.String(100), default='manual', index=True)
    language = db.Column(db.String(10), default='en', index=True)  # e.g. "en", "hu", "sk"
    content_type = db.Column(db.String(20), default='movie', index=True)  # movie, series, live
    added_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Live TV / EPG fields
    epg_channel_id = db.Column(db.String(100))  # EPG channel ID for mapping
    tv_archive = db.Column(db.Integer, default=0)  # 1 if timeshift available, 0 otherwise
    tv_archive_duration = db.Column(db.Integer, default=0)  # Timeshift duration in days
    
    # Relationship
    streams = db.relationship('Stream', backref='movie', cascade='all, delete-orphan', lazy=True)

class Stream(db.Model):
    __tablename__ = 'streams'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    provider = db.Column(db.String(100))
    url = db.Column(db.String(2048), nullable=False) # Stream URL
    
class Playlist(db.Model):
    __tablename__ = 'playlists'
    id = db.Column(db.String(50), primary_key=True) # e.g. 'default'
    name = db.Column(db.String(100))
    max_connections = db.Column(db.Integer, default=0)
    allowed_countries = db.Column(db.String(200)) # e.g. "SK,CZ"
    
class History(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime(timezone=True), server_default=func.now())
    ip = db.Column(db.String(50))
    action = db.Column(db.String(50))
    content = db.Column(db.String(255))
    playlist = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    
class SiteConfig(db.Model):
    __tablename__ = 'site_config'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    url = db.Column(db.String(512))
    last_scraped = db.Column(db.String(50), default='Never')

class XtreamUser(db.Model):
    __tablename__ = 'xtream_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    max_connections = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    exp_date = db.Column(db.String(20), default="1999999999") # Unlimited default
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

class XtreamSource(db.Model):
    __tablename__ = 'xtream_sources'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    server_url = db.Column(db.String(512), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    auto_sync = db.Column(db.Boolean, default=True)
    import_vod = db.Column(db.Boolean, default=True)
    import_series = db.Column(db.Boolean, default=True)
    import_live = db.Column(db.Boolean, default=True)
    vod_count = db.Column(db.Integer, default=0)
    live_count = db.Column(db.Integer, default=0)
    series_count = db.Column(db.Integer, default=0)
    last_sync = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

class MovieGroup(db.Model):
    __tablename__ = 'movie_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)  # e.g. "bahu.tv", "film-adult"
    description = db.Column(db.Text)
    movie_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

