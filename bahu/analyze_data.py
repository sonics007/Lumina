import json
from collections import Counter

# Load data
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total entries in database: {len(data)}")
print("\n" + "="*60)

# Count by category
cats = Counter([d['category'] for d in data])
print("\nFilms by Collection/Category:")
print("-"*60)
for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True):
    print(f"{cat:40} {count:5}")

print("\n" + "="*60)

# Count by type
types = Counter([d['type'] for d in data])
print("\nFilms by Type:")
print("-"*60)
for typ, count in types.items():
    print(f"{typ:40} {count:5}")

print("\n" + "="*60)

# Collections (groups)
collections = [
    "Legnézettebb Filmek",
    "Jelenleg Követett Filmek", 
    "Legértékeltebb Filmek",
    "IMDb Top Filmek",
    "Oscar Nyertesek"
]

print("\nMovie Groups (Collections):")
print("-"*60)
total_in_collections = 0
for col in collections:
    count = sum(1 for d in data if d['category'] == col)
    total_in_collections += count
    print(f"{col:40} {count:5}")

print(f"\n{'Total in all collections:':40} {total_in_collections:5}")
