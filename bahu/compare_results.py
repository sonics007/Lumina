import json

# Load data.json
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Load unique_urls.txt
with open('unique_urls.txt', 'r', encoding='utf-8') as f:
    urls_from_quick = set([line.strip() for line in f])

urls_from_db = set([d['url'] for d in data])

print("="*70)
print("POROVNANIE: data.json vs quick_count")
print("="*70)

print(f"\nURLs in data.json:        {len(urls_from_db)}")
print(f"URLs from quick scan:     {len(urls_from_quick)}")
print(f"Difference:               {len(urls_from_db) - len(urls_from_quick)}")

missing_in_quick = urls_from_db - urls_from_quick
missing_in_db = urls_from_quick - urls_from_db

print(f"\n📊 URLs in data.json but NOT in quick scan: {len(missing_in_quick)}")
if missing_in_quick:
    print("\nFirst 20 missing URLs:")
    for i, url in enumerate(list(missing_in_quick)[:20]):
        # Find which category this URL belongs to
        for entry in data:
            if entry['url'] == url:
                print(f"  {i+1}. {entry['category']:30} {url}")
                break

print(f"\n📊 URLs in quick scan but NOT in data.json: {len(missing_in_db)}")
if missing_in_db:
    print("\nFirst 10:")
    for i, url in enumerate(list(missing_in_db)[:10]):
        print(f"  {i+1}. {url}")

print("\n" + "="*70)
print("ZÁVER:")
print("="*70)

if len(missing_in_quick) > 0:
    print(f"\n✅ data.json obsahuje {len(missing_in_quick)} filmov navyše")
    print("   Tieto filmy sú pravdepodobne z kolekcií alebo kategórií")
    print("   ktoré quick_count neskontroloval (len hlavnú stránku)")
    
print(f"\n✅ SKUTOČNÝ počet unikátnych filmov: {len(urls_from_db)}")
print(f"   (z data.json, ktorý prešiel všetky kategórie)")
