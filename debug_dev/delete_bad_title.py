
import json
import yaml # just kidding
import os

DB = 'movies_db.json'
with open(DB, 'r', encoding='utf-8') as f:
    db = json.load(f)

print(f"Count before: {len(db)}")
# Filter out
new_db = [m for m in db if m.get('title') != "Loading..."]

if len(new_db) < len(db):
    print(f"Removed {len(db) - len(new_db)} movies.")
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(new_db, f, indent=2, ensure_ascii=False)
else:
    print("No movie with title 'Loading...' found.")
