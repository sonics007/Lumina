# 🎬 Xtream Codes Source Importer - Kompletný Návod

## ✅ ČO SOM IMPLEMENTOVAL

Vytvoril som kompletný systém na import filmov, seriálov a TV kanálov z externých Xtream Codes serverov do vášho projektu.

### 📦 Nové súbory:

1. **`app/templates/xtream_sources.html`** - Webové rozhranie pre správu zdrojov
2. **`app/models.py`** - Pridaný `XtreamSource` model
3. **`app/services/xtream_importer.py`** - Import service
4. **`app/routes/xtream_sources.py`** - API routes
5. **`app/__init__.py`** - Zaregistrovaný nový blueprint
6. **`app/templates/base.html`** - Pridaná položka do menu

### 🎯 Funkcie:

#### 1. **Správa Xtream zdrojov**
- ➕ Pridanie nového Xtream servera
- 🔌 Test pripojenia pred pridaním
- 📊 Zobrazenie štatistík (VOD, Live, Series)
- 🗑️ Odstránenie zdroja
- ✏️ Zobrazenie obsahu zo zdroja

#### 2. **Import obsahu**
- 🎬 **VOD (Filmy)** - automatický import filmov
- 📺 **Seriály** - import seriálov vrátane všetkých epizód
- 📡 **Live TV** - pripravené na import (voliteľné)

#### 3. **Automatizácia**
- 🔄 Auto-sync daily (voliteľné)
- 📈 Sledovanie počtu importovaných položiek
- ⏰ Timestamp posledného syncu

## 🚀 AKO POUŽIŤ

### Krok 1: Reštartujte server

```bash
python run.py
```

### Krok 2: Otvorte web rozhranie

```
http://localhost:5555
```

### Krok 3: Prejdite do menu

```
SOURCES & SCRAPERS
└── 📡 Xtream Sources  ← KLIKNITE SEM
```

### Krok 4: Pridajte váš Xtream zdroj

1. Kliknite na **"Add Xtream Source"**
2. Vyplňte údaje:
   ```
   Source Name: Môj IPTV Provider
   Server URL: http://example.com:8080
   Username: your_username
   Password: your_password
   ```
3. Vyberte čo chcete importovať:
   - ✅ Import VOD (Movies)
   - ✅ Import Series
   - ⬜ Import Live TV
4. Kliknite **"Test Connection"** - overí pripojenie
5. Kliknite **"Add Source"**

### Krok 5: Synchronizujte obsah

1. V zozname zdrojov kliknite na **"Sync"**
2. Počkajte na dokončenie importu
3. Importované filmy sa objavia v **"All Movies"**

## 📊 ČO SA IMPORTUJE

### VOD (Filmy):
```
Názov: Podľa názvu z Xtream servera
URL: http://server:port/movie/username/password/stream_id.mp4
Obrázok: Stream icon z Xtream API
Popis: Plot z VOD info
Rating: Rating z VOD info
Kategória: Category name ako tags
Zdroj: xtream:Názov_Zdroja
```

### Seriály:
```
Názov: Názov Seriálu - S01E01 - Názov Epizódy
URL: http://server:port/series/username/password/episode_id.mp4
Obrázok: Episode image alebo series cover
Popis: Episode plot
Tags: Series, Kategória
Zdroj: xtream:Názov_Zdroja:series
```

## 🎨 Webové rozhranie

### Hlavná stránka:
```
┌─────────────────────────────────────────┐
│  🎬 Xtream Codes Sources                │
│  Import content from external servers   │
│                      [+ Add Source]     │
├─────────────────────────────────────────┤
│  📊 Statistics:                         │
│  ├── Total VOD: 1,234                   │
│  ├── Live Channels: 567                 │
│  ├── Series: 89                         │
│  └── Active Sources: 2                  │
├─────────────────────────────────────────┤
│  📋 Configured Sources:                 │
│  ┌───────────────────────────────────┐  │
│  │ My IPTV Provider                  │  │
│  │ Server: http://example.com:8080   │  │
│  │ Status: ✅ Active                  │  │
│  │ VOD: 1,234 | Live: 567 | Series:89│  │
│  │ [Test] [Sync] [View] [Delete]     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 🔧 Technické detaily

### Databázový model:
```python
class XtreamSource(db.Model):
    id              # Auto-increment ID
    name            # Friendly name
    server_url      # Xtream server URL
    username        # Xtream username
    password        # Xtream password
    is_active       # Active/Inactive
    auto_sync       # Auto-sync daily
    import_vod      # Import VOD flag
    import_series   # Import series flag
    import_live     # Import live TV flag
    vod_count       # Number of VOD items
    live_count      # Number of live channels
    series_count    # Number of series
    last_sync       # Last sync timestamp
    created_at      # Creation timestamp
```

### API Endpointy:
```
POST   /xtream_sources/api/test_connection  - Test pripojenia
POST   /xtream_sources/api/add              - Pridať zdroj
POST   /xtream_sources/api/test/:id         - Test existujúceho zdroja
POST   /xtream_sources/api/sync/:id         - Synchronizovať obsah
DELETE /xtream_sources/api/remove/:id       - Odstrániť zdroj
GET    /xtream_sources/                     - Zoznam zdrojov
GET    /xtream_sources/:id/content          - Obsah zo zdroja
```

### Import proces:
```
1. Test Connection
   ├── Overí prihlasovacie údaje
   ├── Získa server info
   └── Spočíta VOD/Live/Series

2. Add Source
   ├── Uloží do databázy
   └── Zobrazí v zozname

3. Sync Content
   ├── Získa zoznam VOD streams
   ├── Pre každý VOD:
   │   ├── Skontroluje duplicity
   │   ├── Vytvorí Movie záznam
   │   └── Vytvorí Stream záznam
   ├── Získa zoznam Series
   ├── Pre každý seriál:
   │   ├── Získa info o epizódach
   │   └── Importuje každú epizódu
   └── Aktualizuje štatistiky
```

## 📝 Príklad použitia

### Váš Xtream link:
```
Server: http://example.com:8080
Username: myuser
Password: mypass
```

### Po pridaní a syncu:
- Všetky filmy sa objavia v **"All Movies"**
- Seriály sa objavia ako jednotlivé epizódy
- Každý záznam má tag `xtream:Názov_Zdroja`
- Môžete ich filtrovať podľa zdroja

## 🎯 Výhody

✅ **Jednoduchý import** - Stačí zadať prihlasovacie údaje  
✅ **Automatická deduplikácia** - Neskopíruje duplicity  
✅ **Batch import** - Importuje v dávkach po 50  
✅ **Sledovanie progressu** - Vidíte koľko sa importovalo  
✅ **Flexibilné nastavenia** - Vyberte si čo chcete importovať  
✅ **Integrácia s Xtream API** - Importovaný obsah funguje cez váš Xtream server  

## 🔐 Bezpečnosť

- Heslá sa ukladajú v databáze (pre produkciu použite šifrovanie!)
- API endpointy vyžadujú prihlásenie
- Test connection pred pridaním zdroja

## 📈 Ďalšie možnosti

1. **Auto-sync scheduler** - Automatický denný sync
2. **Selective import** - Import len vybraných kategórií
3. **Update detection** - Detekcia nového obsahu
4. **Bandwidth control** - Limit rýchlosti importu
5. **Multi-source merge** - Zlúčenie viacerých zdrojov

---

**Teraz máte plne funkčný systém na import obsahu z Xtream Codes serverov!** 🎉

Stačí zadať váš Xtream link a všetok obsah sa automaticky importuje do vašej databázy.
