# 📸 Sťahovanie obrázkov filmov v lepšej kvalite

## 🎯 Čo to robí?

Tento systém automaticky sťahuje obrázky (postery) filmov z internetu a ukladá ich **lokálne** na váš server. To poskytuje:

- ✅ **Lepšiu kvalitu** - originálne obrázky bez kompresie
- ✅ **Rýchlejšie načítanie** - obrázky sa načítavajú z lokálneho disku
- ✅ **Nezávislosť** - funguje aj keď pôvodný web spadne
- ✅ **Kontrolu** - máte plnú kontrolu nad obrázkami

## 📁 Kde sa ukladajú obrázky?

Všetky obrázky sa ukladajú do:
```
static/posters/
```

Každý obrázok má unikátny názov založený na hash URL (napr. `a3f5b2c1d4e6.jpg`)

## 🔄 Automatické sťahovanie (nové filmy)

Keď spustíte scraper cez webové rozhranie:
1. Scraper nájde nové filmy
2. **Automaticky stiahne obrázky** pre každý nový film
3. Uloží ich do `static/posters/`
4. V databáze sa uloží lokálna cesta namiesto URL

## 📥 Stiahnutie obrázkov pre existujúce filmy

Ak už máte filmy v databáze s URL obrázkami, môžete ich stiahnuť:

### Krok 1: Spustite skript

```bash
python download_existing_images.py
```

### Krok 2: Počkajte

Skript:
- Nájde všetky filmy s vzdialenými URL obrázkami
- Stiahne ich v dávkach (50 naraz)
- Aktualizuje databázu s lokálnymi cestami
- Zobrazí progress

### Príklad výstupu:

```
============================================================
Movie Image Downloader
============================================================

Found 523 movies with images
Found 523 movies with remote images to download

Processing batch 1/11
Downloading 50 images...
✓ Mistaken Nerd Gets Fucked: https://film-adult.com/... -> /static/posters/a3f5b2c1.webp
✓ Kristy Black Private Fuck: https://film-adult.com/... -> /static/posters/d4e6f7a8.webp
...

============================================================
Download complete!
Successfully downloaded: 520
Failed: 3
============================================================
```

## 🎨 Podporované formáty

Systém automaticky rozpozná a uloží:
- `.webp` - moderný formát s najlepšou kompresiou
- `.jpg` / `.jpeg` - štandardný formát
- `.png` - pre obrázky s priehľadnosťou
- `.gif` - animované obrázky

## 🧹 Čistenie nepoužívaných obrázkov

Ak chcete vymazať obrázky, ktoré už nie sú v databáze:

```python
from app.services.image_downloader import image_downloader
from app.models import Movie

# Získať všetky používané obrázky
used_images = set(m.image for m in Movie.query.all() if m.image)

# Vymazať nepoužívané
image_downloader.cleanup_unused_images(used_images)
```

## 📊 Technické detaily

### Ako funguje hash?

Každý obrázok dostane unikátny názov pomocí MD5 hash pôvodnej URL:
```python
url = "https://film-adult.com/uploads/posts/2026-01/movie.webp"
hash = md5(url) = "a3f5b2c1d4e6f7a8b9c0d1e2f3a4b5c6"
filename = "a3f5b2c1d4e6f7a8b9c0d1e2f3a4b5c6.webp"
```

### Paralelné sťahovanie

Systém sťahuje viacero obrázkov naraz (5-10 súčasne) pre rýchlosť:
```python
image_downloader.download_images_batch(urls, max_workers=10)
```

### Kontrola duplicít

Ak obrázok už existuje, preskočí sa (nešetrí bandwidth):
```python
if os.path.exists(local_path) and not force:
    return existing_path
```

## 🔧 Riešenie problémov

### Obrázky sa nesťahujú

1. **Skontrolujte priečinok**:
   ```bash
   ls -la static/posters/
   ```

2. **Skontrolujte oprávnenia**:
   ```bash
   chmod 755 static/posters/
   ```

3. **Skontrolujte logy**:
   - Pozrite sa do konzoly pri scrapovaní
   - Hľadajte chyby typu "Failed to download"

### Obrázky sa nezobrazujú

1. **Skontrolujte cestu v databáze**:
   ```python
   movie = Movie.query.first()
   print(movie.image)  # Malo by byť: /static/posters/xxx.webp
   ```

2. **Skontrolujte, či Flask servuje static súbory**:
   ```
   http://127.0.0.1:5555/static/posters/a3f5b2c1.webp
   ```

### Chyba "Permission denied"

Na Windows:
```bash
# Spustite CMD ako Administrator
python download_existing_images.py
```

## 📈 Štatistiky

Po stiahnutí môžete skontrolovať:

```python
import os
poster_dir = "static/posters"
files = os.listdir(poster_dir)
total_size = sum(os.path.getsize(os.path.join(poster_dir, f)) for f in files)

print(f"Počet obrázkov: {len(files)}")
print(f"Celková veľkosť: {total_size / 1024 / 1024:.2f} MB")
```

## 🎯 Odporúčania

1. **Spustite download_existing_images.py** hneď po prvom scrapovaní
2. **Nechajte scraper automaticky sťahovať** nové obrázky
3. **Pravidelne robte cleanup** nepoužívaných obrázkov
4. **Zálohujte** priečinok `static/posters/` spolu s databázou

## 🔗 Zdroje obrázkov

Obrázky sa sťahujú z:
- `film-adult.top` - hlavný zdroj (WebP formát, vysoká kvalita)
- `uiiumovie.com` - alternatívny zdroj (JPG formát)

Všetky obrázky sú verejne dostupné postery filmov.
