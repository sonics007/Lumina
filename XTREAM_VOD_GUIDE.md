# Xtream Codes API - VOD Only Setup

## ✅ Váš setup

- **VOD (Filmy)**: ✅ Funguje (máte stovky filmov v databáze)
- **Live TV**: ❌ Nemáte (channels.txt je prázdny)
- **Admin účet**: ✅ admin/admin

## 📱 Ako pripojiť v TiviMate

### Metóda 1: Xtream Codes API

1. Otvorte **TiviMate**
2. **Settings** → **Playlists** → **Add Playlist**
3. Vyberte **"Xtream Codes API"**
4. Zadajte údaje:
   ```
   Server: http://192.168.1.201:5555
   Username: admin
   Password: admin
   ```
5. Kliknite **"Next"**

**DÔLEŽITÉ:** 
- Použite **IP adresu vášho počítača** namiesto `192.168.1.201`
- Zistite IP: otvorte CMD a napíšte `ipconfig` → hľadajte "IPv4 Address"
- Server musí bežať: `python run.py`

### Metóda 2: M3U Playlist (alternatíva)

Ak Xtream API nefunguje v TiviMate, skúste M3U:
```
http://192.168.1.201:5555/playlist.m3u8?id=default
```

## 🔍 Testovanie API

Otvorte v prehliadači (na počítači kde beží server):

### 1. Test autentifikácie:
```
http://127.0.0.1:5555/player_api.php?username=admin&password=admin
```

**Očakávaná odpoveď:**
```json
{
  "user_info": {
    "auth": 1,
    "status": "Active"
  }
}
```

### 2. Test VOD kategórií:
```
http://127.0.0.1:5555/player_api.php?username=admin&password=admin&action=get_vod_categories
```

**Očakávaná odpoveď:**
```json
[
  {"category_id": "all", "category_name": "All Movies"},
  {"category_id": "film_adult", "category_name": "XXX | Film-Adult.top"},
  {"category_id": "uiiu", "category_name": "XXX | UIIU Movie"}
]
```

### 3. Test filmov:
```
http://127.0.0.1:5555/player_api.php?username=admin&password=admin&action=get_vod_streams&category_id=all
```

Malo by vrátiť zoznam všetkých filmov (máte ich stovky).

## ⚠️ Riešenie problémov TiviMate

### Problém: "Connection failed" alebo "Invalid credentials"

**Riešenie:**
1. Skontrolujte, či server beží:
   - Otvorte prehliadač: `http://127.0.0.1:5555`
   - Malo by sa zobraziť dashboard

2. Skontrolujte IP adresu:
   - V CMD napíšte: `ipconfig`
   - Použite IP z "IPv4 Address" (napr. 192.168.1.201)
   - **NEPOUŽÍVAJTE** `localhost` alebo `127.0.0.1` v TiviMate!

3. Skontrolujte firewall:
   - Windows môže blokovať port 5555
   - Pridajte výnimku pre Python alebo port 5555

### Problém: "No streams found" alebo prázdny zoznam

**Možné príčiny:**
1. **TiviMate zobrazuje len Live TV, nie VOD**
   - V TiviMate prejdite do sekcie **"Movies"** alebo **"VOD"**
   - Nie do sekcie "Channels" (tam sú len live kanály)

2. **Databáza je prázdna**
   - Otestujte API v prehliadači (link vyššie)
   - Ak API vracia filmy, problém je v TiviMate nastavení

### Problém: Filmy sa nezobrazujú v TiviMate

TiviMate môže mať problémy s VOD-only Xtream API. Skúste:

1. **Pridať dummy live kanál** (aby TiviMate nechyboval):
   - Upravte `channels.txt`:
   ```
   http://example.com/dummy.m3u8|Info: VOD Only|
   ```

2. **Použiť M3U playlist namiesto Xtream API**:
   ```
   http://VASA_IP:5555/playlist.m3u8?id=default
   ```

3. **Skúsiť iný IPTV player**:
   - **IPTV Smarters Pro** (lepšia podpora VOD)
   - **Perfect Player**
   - **VLC Player** (základné prehrávanie)

## 🎬 Prehrávanie filmov

### Ako funguje stream URL:

Keď TiviMate požiada o film, Xtream API vráti URL:
```
http://192.168.1.201:5555/movie/admin/admin/123.mp4
```

Tento endpoint:
1. Nájde film v databáze (ID 123)
2. Získa stream URL (napr. DoodStream, HGLink)
3. Presmeruje na `/watch` endpoint
4. `/watch` extrahuje skutočný stream a proxy ho

### Ak filmy nefungujú:

1. Skontrolujte logy: `server_log.txt`
2. Otestujte priamo v prehliadači:
   ```
   http://127.0.0.1:5555/movie/admin/admin/1.mp4
   ```
3. Skontrolujte, či extractor funguje

## 📊 Štatistiky

Podľa API máte:
- ✅ **Stovky VOD filmov** v databáze
- ✅ **3 kategórie**: All Movies, Film-Adult, UIIU
- ✅ **Xtream API** funguje správne
- ❌ **0 live kanálov** (channels.txt je prázdny)

## 💡 Odporúčania

### Pre TiviMate:
1. Použite **IP adresu** namiesto localhost
2. Hľadajte filmy v sekcii **"Movies"** nie "Channels"
3. Ak nefunguje, skúste **IPTV Smarters Pro**

### Pre lepší výkon:
1. Nechajte server bežať na pozadí
2. Nepoužívajte debug mode v produkcii
3. Zvážte použitie Gunicorn namiesto Flask dev servera

## 🔐 Bezpečnosť

Pre produkčné použitie:
1. Zmeňte heslo z `admin` na silnejšie
2. Nastavte `max_connections` pre každého používateľa
3. Použijte HTTPS (nginx reverse proxy)
4. Neexponujte server na internet bez ochrany

## 📝 Poznámky

- `channels.txt` môže zostať prázdny (máte len VOD)
- Server beží na `http://192.168.1.201:5555`
- Pre prístup z mobilu/TV použijte IP adresu počítača
- TiviMate preferuje servery s live TV, pre VOD-only zvážte iný player
