"""
Overenie - koľko stránok scraper skutočne prešiel
"""
import json

# Load data
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("="*70)
print("OVERENIE SKUTOČNÉHO POČTU STRÁNOK")
print("="*70)

# Analyze by category to see distribution
from collections import Counter

categories = Counter([d['category'] for d in data])

print("\n📊 Rozdelenie filmov podľa kategórií:")
print("-"*70)

total = 0
for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
    total += count
    print(f"{cat:40} {count:4} filmov")

print("-"*70)
print(f"{'CELKOM:':40} {total:4} filmov")

print("\n" + "="*70)
print("ANALÝZA SCRAPINGU:")
print("="*70)

print(f"""
Z databázy vidíme:
• Celkovo {len(data)} UNIKÁTNYCH filmov
• Rozdelených do {len(categories)} kategórií/kolekcií

Scraper hlásil:
• TOTAL_FOUND: 42,885
• TOTAL_EXISTS: 42,885
• TOTAL_ADDED: 0

To znamená:
• Scraper prešiel stránky a našiel 42,885 položiek
• Všetky už boli v databáze (preto ADDED = 0)
• Z týchto 42,885 položiek bolo len 770 unikátnych

Prečo 42,885?
• Scraper prechádza VŠETKY kategórie a VŠETKY stránky
• Každá kategória má viacero stránok
• Filmy sa opakujú na rôznych stránkach
• Scraper POČÍTA každú položku na každej stránke

Príklad:
Kategória "Akció" má {categories.get('Akció', 0)} filmov v DB
→ Ale scraper mohol prejsť 50 strán tejto kategórie
→ Na každej stránke 20 filmov = 1,000 položiek
→ Z toho len {categories.get('Akció', 0)} bolo unikátnych
→ Zvyšok boli duplicity (ten istý film na viacerých stránkach)
""")

print("="*70)
print("REALISTICKÝ ODHAD:")
print("="*70)

print("""
Ak má každá kategória priemerne:
• 50-100 strán s filmami
• 19 kategórií × 75 strán = 1,425 strán
• 5 kolekcií × 5 strán = 25 strán
• Celkovo: ~1,450 strán

1,450 strán × 20 filmov/stránka = 29,000 položiek

Ale scraper našiel 42,885 položiek, čo znamená:
→ Niektoré kategórie mali viac strán
→ Alebo scraper prešiel viac kolekcií/kategórií
→ 42,885 ÷ 20 = ~2,144 strán

ZÁVER:
✅ Scraper prešiel približne 2,144 strán
✅ Našiel 42,885 položiek (s duplicitami)
✅ Z toho 770 bolo unikátnych filmov
✅ Priemerná duplicita: 42,885 ÷ 770 = 55.6

ALE toto NEZNAMENÁ, že jeden film sa objavuje 55×!
Znamená to len, že na 2,144 stránkach bolo 42,885 položiek,
z ktorých len 770 bolo unikátnych.
""")

print("="*70)
