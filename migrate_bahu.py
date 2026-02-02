"""
Database migration script - Add new columns to movies table
"""
import sqlite3
import os

# Path to database
DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')

def migrate_database():
    print("Starting database migration...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(movies)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"Current columns: {columns}")
    
    # Add language column if not exists
    if 'language' not in columns:
        print("Adding 'language' column...")
        cursor.execute("ALTER TABLE movies ADD COLUMN language VARCHAR(10) DEFAULT 'en'")
        print("✓ Added 'language' column")
    else:
        print("✓ 'language' column already exists")
    
    # Add content_type column if not exists
    if 'content_type' not in columns:
        print("Adding 'content_type' column...")
        cursor.execute("ALTER TABLE movies ADD COLUMN content_type VARCHAR(20) DEFAULT 'movie'")
        print("✓ Added 'content_type' column")
    else:
        print("✓ 'content_type' column already exists")
    
    # Add added_at column if not exists
    if 'added_at' not in columns:
        print("Adding 'added_at' column...")
        cursor.execute("ALTER TABLE movies ADD COLUMN added_at DATETIME")
        # Update existing rows to have current timestamp
        cursor.execute("UPDATE movies SET added_at = created_at WHERE added_at IS NULL")
        print("✓ Added 'added_at' column")
    else:
        print("✓ 'added_at' column already exists")
    
    # Create movie_groups table if not exists
    print("\nCreating 'movie_groups' table...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movie_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            source VARCHAR(100) NOT NULL,
            description TEXT,
            movie_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Created 'movie_groups' table")
    
    # Create indexes for better performance
    print("\nCreating indexes...")
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_language ON movies(language)")
        print("✓ Created index on language")
    except:
        pass
    
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_content_type ON movies(content_type)")
        print("✓ Created index on content_type")
    except:
        pass
    
    try:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movie_groups_source ON movie_groups(source)")
        print("✓ Created index on movie_groups.source")
    except:
        pass
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database migration completed successfully!")

if __name__ == '__main__':
    migrate_database()
