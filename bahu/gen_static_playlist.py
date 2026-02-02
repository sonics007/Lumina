import json

def generate_static_playlist():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Loaded {len(data)} items.")
    
    with open("test.m3u8", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for item in data[:50]: # First 50 only
            title = item['title']
            url = item['url']
            poster = item.get('poster', '')
            cat = item.get('category', 'Movie')
            
            # Watch URL needs to point to real server
            watch_url = f"http://127.0.0.1:5000/watch?url={url}"
            
            f.write(f'#EXTINF:-1 tvg-logo="{poster}" group-title="{cat}",{title}\n')
            f.write(f'{watch_url}\n')
            
    print("Generated test.m3u8")

generate_static_playlist()
