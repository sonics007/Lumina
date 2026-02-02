from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add new columns
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE movies ADD COLUMN epg_channel_id VARCHAR(100)'))
            conn.execute(text('ALTER TABLE movies ADD COLUMN tv_archive INTEGER DEFAULT 0'))
            conn.execute(text('ALTER TABLE movies ADD COLUMN tv_archive_duration INTEGER DEFAULT 0'))
            conn.commit()
        print('[OK] Migration complete - EPG and timeshift fields added')
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print('[OK] Columns already exist - skipping migration')
        else:
            print(f'[ERROR] Migration failed: {e}')
