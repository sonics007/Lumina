# Xtream Codes API - Návod na použitie

## 🔧 Konfigurácia

### 1. Vytvorenie Xtream používateľa

Predvolený admin účet:
- **Username**: `admin`
- **Password**: `admin`
- **Max Connections**: 999

Ak potrebujete vytvoriť nového používateľa:
```bash
python update_db_xtream.py
```

Alebo cez web rozhranie:
1. Otvorte `http://127.0.0.1:5555/xtream`
2. Pridajte nového používateľa

### 2. Konfigurácia Live kanálov

Live kanály sa načítavajú zo súboru `channels.txt` v root priečinku projektu.

**Formát:**
```
URL|Názov kanála|Logo URL
```

**Príklad:**
```
https://example.com/stream1.m3u8|Test Channel 1|https://example.com/logo1.png
https://example.com/stream2.m3u8|Test Channel 2|https://example.com/logo2.png
```

## 📱 Pripojenie v TiviMate

### Metóda 1: Xtream Codes API (Odporúčané)

1. Otvorte TiviMate
2. Pridajte nový playlist
3. Vyberte **"Xtream Codes API"**
4. Zadajte údaje:
   - **Server URL**: `http://VASA_IP:5555` (napr. `http://192.168.1.100:5555`)
   - **Username**: `admin`
   - **Password**: `admin`
5. Kliknite na **"Next"**

### Metóda 2: M3U Playlist URL

Ak Xtream API nefunguje, použite priamy M3U link:
```
http://VASA_IP:5555/playlist.m3u8?id=default
```

## 🔍 Testovanie API

### Test autentifikácie:
```
http://127.0.0.1:5555/player_api.php?username=admin&password=admin
```

**Očakávaná odpoveď:**
```json
{
  "user_info": {
    "username": "admin",
    "auth": 1,
    "status": "Active"
  },
  "server_info": {
    "url": "http://127.0.0.1:5555",
    "timestamp_now": 1234567890
  }
}
```

### Test VOD kategórií:
```
http://127.0.0.1:5555/player_api.php?username=admin&password=admin&action=get_vod_categories
```

### Test VOD streamov:
```
http://127.0.0.1:5555/player_api.php?username=admin&password=admin&action=get_vod_streams&category_id=all
```

### Test Live kategórií:
```
http://127.0.0.1:5555/player_api.php?username=admin&password=admin&action=get_live_categories
```

### Test Live streamov:
```
http://127.0.0.1:5555/player_api.php?username=admin&password=admin&action=get_live_streams
```

## ⚠️ Riešenie problémov

### Chyba: "Auth Failed"
- Skontrolujte, či používate správne username/password
- Spustite `python update_db_xtream.py` pre vytvorenie admin účtu

### Chyba: "No channels found"
- Skontrolujte, či `channels.txt` existuje a obsahuje platné kanály
- Formát musí byť: `URL|Názov|Logo`

### TiviMate zobrazuje chybu pri pripájaní
1. Skontrolujte, či server beží: `http://VASA_IP:5555`
2. Použite IP adresu namiesto `localhost` alebo `127.0.0.1`
3. Skontrolujte firewall nastavenia
4. Otestujte API endpointy v prehliadači

### VOD streamy sa neprehrávajú
- Skontrolujte logy servera: `server_log.txt`
- Overte, že máte filmy v databáze
- Skontrolujte, či extractor funguje správne

## 📊 Štruktúra API

### VOD (Video on Demand)
- Filmy sa načítavajú z SQLite databázy (`app.db`)
- Kategórie: All Movies, Film-Adult, UIIU, + dynamické podľa source

### Live TV
- Kanály sa načítavajú z `channels.txt`
- Kategória: "Live Channels"

### Stream URL formát

**VOD:**
```
http://VASA_IP:5555/movie/admin/admin/STREAM_ID.mp4
```

**Live:**
```
http://VASA_IP:5555/live/admin/admin/STREAM_ID.ts
```

## 🔐 Bezpečnosť

Pre produkčné použitie:
1. Zmeňte predvolené heslo `admin`
2. Použite silné heslá
3. Nastavte `max_connections` pre každého používateľa
4. Zvážte použitie HTTPS (reverse proxy ako nginx)

## 📝 Poznámky

- Server musí bežať na `0.0.0.0:5555` pre prístup z iných zariadení
- Pre lokálne testovanie použite `127.0.0.1:5555`
- Pre prístup z mobilu/TV použite IP adresu počítača v sieti
