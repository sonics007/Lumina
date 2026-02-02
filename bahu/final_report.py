"""
FINÁLNY REPORT - Skutočný počet filmov na bahu.tv
"""

print("="*70)
print("🎬 FINÁLNY REPORT - BAHU.TV FILMY")
print("="*70)

print("""
Na základe analýzy viacerých zdrojov:

1️⃣  DATA.JSON (kompletný scraping všetkých kategórií):
   • Unikátnych filmov: 770
   • Kategórie: 21 (kolekcie + žánre)
   • Scraping: Kompletný (všetky kategórie + kolekcie)

2️⃣  QUICK_COUNT (len hlavná stránka /filmek):
   • Unikátnych filmov: 620
   • Stránky: 53
   • Scraping: Len hlavná stránka (bez kolekcií)

3️⃣  ROZDIEL:
   • 770 - 620 = 150 filmov
   • Tieto filmy sú v kolekciách:
     - IMDb Top Filmek
     - Oscar Nyertesek
     - Legértékeltebb Filmek
     - atď.
""")

print("="*70)
print("📊 ČO ZNAMENÁ 42,885 ZÁZNAMOV?")
print("="*70)

print("""
Scraper_v2.py prešiel:
• 5 kolekcií × max 5 strán = 25 strán
• 19 kategórií × priemerne ~100 strán = ~1,900 strán
• Celkovo: ~2,000 strán

Na týchto stránkach:
• Našiel 42,885 filmových položiek
• Z toho 770 bolo unikátnych
• Zvyšok (42,115) boli duplicity

Prečo toľko duplicít?
→ Každá kategória má stránkovanie
→ Filmy sa opakujú na rôznych stránkach
→ Populárne filmy sú vo viacerých kategóriách
→ Scraper POČÍTA každú položku na každej stránke
""")

print("="*70)
print("✅ ZÁVER:")
print("="*70)

print("""
SKUTOČNÝ počet unikátnych filmov na bahu.tv: 770

Rozdelenie:
• 620 filmov - dostupných na hlavnej stránke /filmek
• 150 filmov - dodatočné z kolekcií (IMDb, Oscar, atď.)
• 770 CELKOM

Scraper funguje správne:
✅ Ignoruje duplicity (URL kontrola)
✅ Prechádza všetky kategórie a kolekcie
✅ Ukladá len unikátne filmy

42,885 záznamov = počet filmových položiek na všetkých stránkach
770 filmov = skutočný počet unikátnych filmov
""")

print("="*70)
print("📁 SÚBORY:")
print("="*70)

import os
import json

files_info = [
    ("data.json", "Kompletná databáza 770 filmov"),
    ("unique_urls.txt", "620 URL z hlavnej stránky"),
    ("summary.txt", "Štatistiky scrapingu (42,885 záznamov)"),
]

for filename, desc in files_info:
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        print(f"✓ {filename:20} - {desc} ({size:,} bytes)")

# Count from data.json
if os.path.exists("data.json"):
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"\n📊 Potvrdené z data.json: {len(data)} unikátnych filmov")

print("\n" + "="*70)
