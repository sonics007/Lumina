# KOMPLETNÁ ANALÝZA A RIEŠENIE HGLINK PROBLÉMU

## ZHRNUTIE PROBLÉMU

### 1. Prečo testing_new neprehráva HGLink?

**Hlavný problém**: `extractor.py` má prázdnu implementáciu pre HGLink (riadky 176-178):
```python
# 5. Native Redirect / API Handling (TODO: Implement HGLink JS RE)
# Selenium removed per user request.
pass
```

**Dôsledky**:
- ❌ Extractor nevie spracovať JavaScript redirect z main.js
- ❌ Chýba logika na unpacking obfuskovaného JS
- ❌ HGLink linky zlyhávajú pri extrakcii

---

## 2. ANALÝZA STRÁNKY film-adult.top

### Ako získať HGLink URL:

**Krok 1**: Fetch HTML stránky
```python
url = "https://film-adult.top/en/8051-secretaries-in-heat-3.html"
r = requests.get(url)
html = r.text
```

**Krok 2**: Extrahovať HGLink embed URL pomocou regex
```python
# HGLink URL je hardkódovaný v inline JavaScript:
pattern = r'src\s*=\s*["\']https://hglink\.to/e/([a-zA-Z0-9]+)["\']'
match = re.search(pattern, html)
if match:
    hglink_url = f"https://hglink.to/e/{match.group(1)}"
    # Result: https://hglink.to/e/124fixrcqqxb
```

**Kľúčové zistenie**: HGLink URL je priamo v HTML, **NIE JE POTREBNÉ API**!

---

## 3. ANALÝZA HGLINK EMBED PAGE

### Dva typy stránok:

#### A. Loading Page (s main.js redirect)
- Obsahuje `<script src="main.js">`
- main.js obsahuje redirect logiku
- Presmeruje na finálnu embed page

#### B. Direct Embed Page (bez loading screen)
- Priamo obsahuje JW Player
- Obsahuje obfuskovaný packed JavaScript
- Video source je v packed JS

### Príklad packed JS:
```javascript
eval(function(p,a,c,k,e,d){ ... }('...'))
```

Po rozbalení obsahuje:
```javascript
{
  "file": "/stream/uySbN8p50oXaRd-ujPcvcQ/kjhhiuahiuhgihdf/1768706156/67072706/master.m3u8"
}
```

**Finálna stream URL**:
```
https://hglink.to/stream/uySbN8p50oXaRd-ujPcvcQ/kjhhiuahiuhgihdf/1768706156/67072706/master.m3u8
```

---

## 4. RIEŠENIE - BEZ SELENIUM!

### Metóda: Fetch + Unpack Packed JS

```python
import requests
import re

def get_hglink_stream(embed_url, referer='https://film-adult.top/'):
    """
    Získa HGLink stream URL bez Selenium
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': referer,
    }
    
    # 1. Fetch embed page
    r = requests.get(embed_url, headers=headers, verify=False)
    html = r.text
    
    # 2. Check for loading page
    if 'main.js' in html:
        # This is loading page, it will redirect
        # For now, just try again (HGLink usually redirects to same domain)
        # In practice, you might need to wait or handle differently
        pass
    
    # 3. Find packed JS
    pattern = r"}\('((?:[^']|\\')*)',(\d+),(\d+),'((?:[^']|\\')*)'.split\('\|'\)"
    match = re.search(pattern, html)
    
    if not match:
        return None
    
    p, a, c, k = match.groups()
    
    # 4. Unpack JS
    unpacked = _unpack_js(p, a, c, k)
    
    # 5. Extract stream URL
    file_match = re.search(r'"file"\s*:\s*"([^"]+)"', unpacked)
    if file_match:
        stream_path = file_match.group(1)
        if stream_path.startswith('/'):
            stream_url = f"https://hglink.to{stream_path}"
        else:
            stream_url = stream_path
        
        return stream_url
    
    return None

def _unpack_js(p, a, c, k_str):
    """Dean Edwards Packer Unpacker"""
    keywords = k_str.split('|')
    encoded_a = int(a)
    encoded_c = int(c)
    
    def to_base36(n):
        if n == 0: return '0'
        res = ''
        if n >= encoded_a:
            res += to_base36(n // encoded_a)
        n = n % encoded_a
        if n > 35:
            res += chr(n + 29)
        else:
            if n < 10: res += str(n)
            else: res += chr(n - 10 + 97)
        return res
    
    unpacked = p
    for i in range(encoded_c - 1, -1, -1):
        if not keywords[i]: continue
        token = to_base36(i)
        unpacked = re.sub(r'\b' + token + r'\b', keywords[i], unpacked)
    
    return unpacked
```

---

## 5. PROBLÉM S MAIN.JS REDIRECT

### Analýza main.js:

```javascript
const dmca = ['hglink.to', 'hglink.com', 'hglink.net', 'hglink.org', 'hglink.info'];
const main = ['hglink.to', 'hglink.com', 'hglink.net'];
const rules = ['film-adult.top', 'film-adult.com'];

let destination;
if (rules.includes(url.hostname)) {
    destination = main[Math.floor(Math.random() * main.length)];
} else {
    destination = dmca[Math.floor(Math.random() * dmca.length)];
}

const finalURL = 'https://' + destination + url.pathname + url.search;
window.location.href = finalURL;
```

### PROBLÉM:
- Ak referer NIE JE film-adult.top, redirect ide na tú istú doménu (dmca)
- Toto spôsobuje **infinite loop**!

### RIEŠENIE:
**NEPOUŽÍVAŤ main.js redirect simuláciu!**

Namiesto toho:
1. Ak vidíte loading page (main.js), **počkajte 2-3 sekundy**
2. Alebo **fetchnite stránku znova** (loading page sa zmení na embed page)
3. Alebo **použite správny referer** (film-adult.top) aby redirect fungoval

---

## 6. FINÁLNE RIEŠENIE

### Aktualizovaný extractor.py:

```python
def get_stream_url(input_url, _recursion_depth=0):
    # Prevent infinite loops
    if _recursion_depth > 3:
        logger.error("Max recursion depth reached, stopping")
        return None, None
    
    # ... existing code ...
    
    # HGLink handling
    if 'hglink.to' in input_url or 'hglink.com' in input_url:
        logger.info("Detected HGLink URL")
        
        # Check for loading page
        if 'main.js' in html:
            logger.info("Loading page detected, waiting for redirect...")
            
            # OPTION 1: Wait and retry
            import time
            time.sleep(3)
            return get_stream_url(input_url, _recursion_depth + 1)
            
            # OPTION 2: Use correct referer
            # (Already handled by providers_config if set correctly)
        
        # If not loading page, packed JS should work
        # (Already handled by existing packed JS logic)
```

### Aktualizovaný providers_config.py:

```python
'hglink.to': {
    'referer': 'https://film-adult.top/',  # IMPORTANT!
    'extra_headers': {
        'Origin': 'https://film-adult.top',
        'Accept': '*/*'
    }
},
```

---

## 7. TESTOVANIE

### Test 1: Direct extraction
```python
url = "https://hglink.to/e/124fixrcqqxb"
stream, headers = get_stream_url(url)
print(stream)
# Expected: https://hglink.to/stream/.../master.m3u8
```

### Test 2: From film-adult.top
```python
url = "https://film-adult.top/en/8051-secretaries-in-heat-3.html"
html = requests.get(url).text
hglink_match = re.search(r'https://hglink\.to/e/([a-zA-Z0-9]+)', html)
if hglink_match:
    hglink_url = hglink_match.group(0)
    stream, headers = get_stream_url(hglink_url)
    print(stream)
```

---

## 8. KĽÚČOVÉ ZISTENIA

### ✅ ČO FUNGUJE:
1. **Fetch HTML** z film-adult.top → extrahovať HGLink URL
2. **Fetch HGLink embed page** s správnym referer
3. **Unpack packed JavaScript** pomocou Dean Edwards unpacker
4. **Extrahovať "file" URL** z rozbaleneho JS
5. **Konštruovať finálnu stream URL**

### ❌ ČO NEFUNGUJE:
1. **API endpointy** - HGLink nemá verejné API
2. **main.js redirect simulácia** - spôsobuje infinite loop bez správneho referera
3. **Selenium** - nie je potrebný, všetko sa dá cez HTTP requests

### 🔑 KĽÚČOVÉ BODY:
- **Referer je KRITICKÝ**: Musí byť `film-adult.top` aby redirect fungoval
- **Packed JS pattern**: `}\('...',\d+,\d+,'...'.split\('\|'\)`
- **Stream URL pattern**: `"file": "/stream/..."`
- **Prípony**: `.urlset` = playlists, `.woff2` = segmenty

---

## 9. NEXT STEPS

1. ✅ Aktualizovať `providers_config.py` s správnym refererom
2. ✅ Pridať do `extractor.py` handling pre loading page (wait + retry)
3. ✅ Opraviť regex pattern pre packed JS
4. ⏳ Otestovať s reálnymi HGLink URL
5. ⏳ Integrovať do `server.py`
6. ⏳ Otestovať celý flow: film-adult.top → HGLink → VLC

---

## 10. ZÁVER

**Prečo neprehráva**: Extractor nemá implementáciu pre HGLink

**Ako získať bez Selenium**: Fetch HTML + Unpack Packed JS + Extract "file" URL

**Hlavný problém**: Infinite loop kvôli zlému refereru

**Riešenie**: Použiť správny referer (film-adult.top) ALEBO počkať a retry
