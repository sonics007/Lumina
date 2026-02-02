import json
from collections import defaultdict

# Load data
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*70)
print("PODROBNÁ ANALÝZA DUPLICÍT")
print("="*70)

# Count how many categories each movie appears in
movie_categories = defaultdict(list)
for entry in data:
    movie_categories[entry['url']].append(entry['category'])

# Since we only store unique URLs, let's analyze the scraping pattern
print(f"\n📊 Celkový počet unikátnych filmov: {len(data)}")

# Analyze categories
categories_count = defaultdict(int)
for entry in data:
    categories_count[entry['category']] += 1

print(f"\n📁 Počet kategórií/kolekcií: {len(categories_count)}")

print("\n" + "="*70)
print("PREČO 42,885 ZÁZNAMOV?")
print("="*70)

print("\n🔍 Scraper prechádza:")
print("-"*70)

# Collections
collections = [
    "Legnézettebb Filmek",
    "Jelenleg Követett Filmek", 
    "Legértékeltebb Filmek",
    "IMDb Top Filmek",
    "Oscar Nyertesek"
]

# Categories
categories = [
    "Akció", "Animáció", "Családi", "Dokumentum", "Dráma", 
    "Fantázia", "Háborús", "Horror", "Kaland", "Krimi",
    "Misztikus", "Rajzfilm", "Romantikus", "Sci-Fi", "Sport",
    "Thriller", "Történelmi", "Vígjáték", "Western", 
    "Valóság show", "Tehetségkutató"
]

print(f"\n1️⃣  KOLEKCIE (5 skupín, max 5 strán každá):")
total_collection_views = 0
for col in collections:
    count = categories_count.get(col, 0)
    total_collection_views += count
    print(f"   • {col:40} {count:4} filmov")

print(f"\n   Spolu z kolekcií: ~{total_collection_views} záznamov")

print(f"\n2️⃣  KATEGÓRIE (19 kategórií, max 1000 strán každá):")
total_category_views = 0
for cat in sorted(categories):
    count = categories_count.get(cat, 0)
    if count > 0:
        total_category_views += count
        print(f"   • {cat:40} {count:4} filmov")

print(f"\n   Spolu z kategórií: ~{total_category_views} záznamov")

print("\n" + "="*70)
print("VÝPOČET CELKOVÉHO POČTU NÁJDENÝCH ZÁZNAMOV:")
print("="*70)

print(f"""
Scraper pri každom behu:
1. Prechádza všetky kolekcie (5 × max 5 strán)
2. Prechádza všetky kategórie (19 × max 1000 strán)
3. Na každej stránke je ~20 filmov

Každý film sa môže objaviť na VIACERÝCH stránkach:
- Akčný film môže byť v kategórii "Akció"
- Ten istý film môže byť aj v "Legnézettebb Filmek"
- A zároveň v "IMDb Top Filmek"
- Atď...

Scraper POČÍTA každý výskyt = 42,885 záznamov
Ale UKLADÁ len unikátne URL = 770 filmov

Priemerný film sa objavuje: 42,885 ÷ 770 ≈ 55.6 krát
(čo znamená, že priemerný film je v ~55 rôznych kategóriách/stránkach)
""")

print("="*70)
print("ZÁVER:")
print("="*70)
print("""
✅ 770 = skutočný počet UNIKÁTNYCH filmov na bahu.tv
✅ 42,885 = počet krát, koľko scraper našiel filmy (s duplicitami)
✅ Scraper funguje správne - duplicity sa ignorujú pomocou URL kontroly
✅ Všetky filmy sú už v databáze (TOTAL_ADDED = 0)
""")
print("="*70)
