from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check if columns exist, if not add them
    try:
        with db.engine.connect() as conn:
            # SQLite specific column addition
            conn.execute(text("ALTER TABLE movies ADD COLUMN rating VARCHAR(10)"))
            conn.execute(text("ALTER TABLE movies ADD COLUMN duration VARCHAR(20)"))
            conn.execute(text("ALTER TABLE movies ADD COLUMN tags VARCHAR(255)"))
            conn.execute(text("ALTER TABLE movies ADD COLUMN cast TEXT"))
            print("Columns added successfully.")
    except Exception as e:
        print(f"Migration might have already run or failed: {e}")
