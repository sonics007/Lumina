import json

data = json.load(open('movies_db.json', 'r', encoding='utf-8'))
broken = [m for m in data if any(s.get('url', '').endswith('/e/') for s in m.get('streams', []))]
print(f'Found {len(broken)} movies with broken HGLink URLs')
if broken:
    for m in broken[:5]:
        streams = [s['url'] for s in m['streams'] if '/e/' in s['url']]
        print(f"  - {m['title']}: {streams}")
