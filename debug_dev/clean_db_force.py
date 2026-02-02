
import json
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

DB = 'movies_db.json'
if not os.path.exists(DB):
    print("DB neexistuje")
    sys.exit()

with open(DB, 'r', encoding='utf-8') as f:
    db = json.load(f)

print(f"Pôvodný počet filmov: {len(db)}")
new_db = []
deleted = 0

for m in db:
    title = m.get('title', 'Unknown')
    desc = m.get('description', '')
    
    # Podmienky pre vymazanie
    if title == "Loading...":
        deleted += 1
        continue
    
    if "Manually added via direct stream URL" in desc:
        deleted += 1
        continue
        
    new_db.append(m)

if deleted > 0:
    with open(DB, 'w', encoding='utf-8') as f:
        json.dump(new_db, f, indent=2, ensure_ascii=False)
    print(f"Úspešne vymazaných {deleted} chybných záznamov.")
else:
    print("Nenašli sa žiadne chybné záznamy.")

print(f"Nový počet filmov: {len(new_db)}")
