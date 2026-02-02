
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DB = 'movies_db.json'
if not os.path.exists(DB):
    print("DB not found")
    sys.exit()

with open(DB, 'r', encoding='utf-8') as f:
    db = json.load(f)

print(f"Total movies: {len(db)}")
to_delete_indices = []

for i, m in enumerate(db):
    title = m.get('title', '')
    desc = m.get('description', '')
    url = m.get('url', '')
    
    # Check for the specific issue reported
    # "Manually added via direct stream URL"
    if "Manually added via direct stream URL" in str(desc) or not title:
         print(f"Found BAD entry at index {i}:")
         print(f"  Title: {title}")
         print(f"  Desc:  {desc}")
         print(f"  URL:   {url}")
         to_delete_indices.append(i)

if not to_delete_indices:
    print("No matching bad entries found.")
else:
    print(f"\nDeleting {len(to_delete_indices)} entries...")
    new_db = [m for i, m in enumerate(db) if i not in to_delete_indices]
    
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(new_db, f, indent=2, ensure_ascii=False)
    print(f"Done. DB saved. New size: {len(new_db)}")
