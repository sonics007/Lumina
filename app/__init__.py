from flask import Flask
from .models import db
import os

def create_app():
    # Get base directory (project root)
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    static_folder = os.path.join(base_dir, 'static')
    template_folder = os.path.join(os.path.dirname(__file__), 'templates')
    
    app = Flask(__name__, 
                static_folder=static_folder, 
                static_url_path='/static',
                template_folder=template_folder)
    
    # Config
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, '..', 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_in_prod_please_123')
    
    # Initialize extensions
    db.init_app(app)
    
    # Enable WAL mode correctly
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()
    
    # Register Blueprints (Import inside to avoid circular deps)
    from .routes.main import main_bp
    from .routes.stream import stream_bp
    from .routes.api import api_bp
    from .routes.xtream import xtream_bp
    from .routes.xtream_sources import xtream_sources_bp
    from .routes.transcode import transcode_bp
    from .routes.bahu import bp as bahu_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(stream_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(xtream_bp) # Xtream needs to be at root (e.g. /player_api.php)
    app.register_blueprint(xtream_sources_bp)
    app.register_blueprint(transcode_bp)
    app.register_blueprint(bahu_bp)
    
    from .routes.groups import groups_bp
    app.register_blueprint(groups_bp)
    
    with app.app_context():
        db.create_all()
        
    return app
