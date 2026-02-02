# HGLINK & PLAYBACK FIX SUMMARY

## PROBLÉM
Užívateľ hlásil "neprehra film" pri pokuse o prehratie HGLink streamu. Server logy ukazovali chybu `Extractor failed` alebo `No packed JS found`.

## ANALÝZA
1. **Infinite Loop**: HGLink používa "Loading Page", ktorá sa tvári ako redirect. Môj pôvodný script sa zacyklil pri pokuse o simuláciu redirectu, pretože sa vracal na tú istú URL.
2. **Hidden Destination**: Skutočný redirect (vykonávaný prehliadačom) smeruje na inú doménu (`haxloppd.com`), čo nebolo zrejmé zo statickej analýzy.
3. **JS Execution**: `main.js` na HGLink stránke je silne obfuskovaný a dynamicky generuje cieľovú doménu.

## RIEŠENIE
Implementoval som robustnú "Mirror Domain Switch" logiku priamo do `extractor.py`:

1. ✅ **Detekcia Loading Page**: Script rozpozná, ak sa zasekol na HGLink loading screen (prítomnosť `main.js`).
2. ✅ **Mirror Failover**: Namiesto nekonečného čakania script automaticky skúsi známe mirror domény (primárne `haxloppd.com`).
3. ✅ **Úspešný Test**: Testovací script `test_hglink.py` potvrdil, že po prepnutí na `haxloppd.com` sa úspešne extrahuje stream URL.

## VÝSLEDOK
Server teraz dokáže spracovať HGLink URL tak, že automaticky nájde správny stream na `haxloppd.com` a vráti ho prehrávaču.

### Ako postupovať:
1. **Nie je potrebné reštartovať server** (ak beží, mal by sa auto-reloadnúť).
2. Otvorte **VLC**.
3. Zadajte URL playlistu: `http://127.0.0.1:5555/playlist.m3u8`
4. Film "Secretaries In Heat 3" by sa mal začať prehrávať.
