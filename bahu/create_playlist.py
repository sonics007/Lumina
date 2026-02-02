"""
Vytvorenie M3U playlistu zo všetkých filmov v data.json
"""
import json

# Load data
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loading {len(data)} movies from data.json...")

# Create M3U playlist
playlist_content = "#EXTM3U\n"

for movie in data:
    title = movie.get('title', 'Unknown')
    url = movie.get('url', '')
    poster = movie.get('poster', '')
    category = movie.get('category', 'Unknown')
    
    # M3U format:
    # #EXTINF:-1 tvg-logo="poster_url" group-title="category",title
    # stream_url
    
    playlist_content += f'#EXTINF:-1 tvg-logo="{poster}" group-title="{category}",{title}\n'
    playlist_content += f'{url}\n'

# Save playlist
output_file = "bahu_playlist_770.m3u"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(playlist_content)

print(f"\n✅ Playlist created: {output_file}")
print(f"   Total movies: {len(data)}")
print(f"   Categories: {len(set([m['category'] for m in data]))}")

# Statistics
from collections import Counter
cats = Counter([m['category'] for m in data])

print(f"\n📊 Movies by category:")
for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"   {cat:40} {count:4} movies")

print(f"\n✅ Done!")
