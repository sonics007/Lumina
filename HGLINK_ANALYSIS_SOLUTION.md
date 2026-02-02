# HGLink Analýza a Riešenie

## 1. ANALÝZA PROBLÉMU - Prečo testing_new neprehráva HGLink

### Zistené problémy:

#### A. Extractor.py (riadok 176-178)
```python
# 5. Native Redirect / API Handling (TODO: Implement HGLink JS RE)
# Selenium removed per user request.
pass
```
**PROBLÉM**: Extractor má zakomentovanú/prázdnu implementáciu pre HGLink JS redirect logiku.

#### B. HGLink používa JavaScript redirect
- HGLink stránka načíta obfuskovaný `main.js` súbor
- Tento JS súbor obsahuje redirect logiku, ktorá presmeruje na finálny video stream
- **Extractor.py NEVIE spracovať tento JavaScript redirect** - preto neprehráva

#### C. Chýbajúca podpora pre .urlset a .woff2
- HGLink používa neštandardné prípony: `.urlset` (playlists) a `.woff2` (segmenty)
- Extractor má základnú podporu (riadok 135), ale chýba kompletná implementácia

---

## 2. ANALÝZA STRÁNKY film-adult.top

### Zistenia z browser analýzy:

#### A. Embed URL je hardkódovaný v HTML
```javascript
$(document).one('click', '#video2_container', function () {
  var s2 = document.createElement("iframe");
  s2.src = "https://hglink.to/e/124fixrcqqxb";
  $("#video2_container").append(s2);
  $("#trailer_play_btn3").hide();
});
```

**Kľúčové zistenie**: HGLink URL je priamo v HTML stránky, nie je potrebné volať API!

#### B. HGLink embed stránka obsahuje obfuskovaný JS
```javascript
eval(function(p,a,c,k,e,d){ ... }('...'))
```

Po rozbalení obsahuje:
```javascript
"file": "/stream/uySbN8p50oXaRd-ujPcvcQ/kjhhiuahiuhgihdf/1768706156/67072706/master.m3u8"
```

**Finálna URL**: `https://hglink.to/stream/uySbN8p50oXaRd-ujPcvcQ/kjhhiuahiuhgihdf/1768706156/67072706/master.m3u8`

---

## 3. ANALÝZA main.js (hglink_main_full.js)

### Štruktúra:
```javascript
const dmca = [/* zoznam dmca domén */];
const main = [/* zoznam hlavných domén */];
const rules = [/* pravidlá pre redirect */];

// Logika:
let destination;
if (rules.includes(url.hostname)) {
    destination = main[Math.floor(Math.random() * main.length)];
} else {
    destination = dmca[Math.floor(Math.random() * dmca.length)];
}

const finalURL = 'https://' + destination + url.pathname + url.search;
window.location.href = finalURL;
```

### Domény v main.js:
- **dmca**: `hglink.to`, `hglink.com`, `hglink.net`, `hglink.org`, `hglink.info`
- **main**: `hglink.to`, `hglink.com`, `hglink.net`
- **rules**: `film-adult.top`, `film-adult.com`

---

## 4. RIEŠENIE - Ako získať HGLink bez Selenium

### Metóda 1: Fetch embed HTML + Unpack JS (ODPORÚČANÉ)

```python
import requests
import re
from urllib.parse import unquote

def get_hglink_stream(embed_url):
    """
    Získa HGLink stream URL bez Selenium
    
    Args:
        embed_url: https://hglink.to/e/VIDEO_ID
    
    Returns:
        tuple: (stream_url, headers)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://film-adult.top/',
    }
    
    # 1. Fetch embed page
    r = requests.get(embed_url, headers=headers, verify=False)
    html = r.text
    
    # 2. Find packed JS
    pattern = r"}\\('((?:[^']|\\\\')*?)',(\\d+),(\\d+),'((?:[^']|\\\\')*?)'\\.split\\('\\|'\\)"
    match = re.search(pattern, html)
    
    if not match:
        return None, None
    
    p, a, c, k = match.groups()
    
    # 3. Unpack JS
    unpacked = _unpack_js(p, a, c, k)
    
    # 4. Extract stream URL
    # Look for: "file": "/stream/..."
    file_match = re.search(r'"file"\\s*:\\s*"([^"]+)"', unpacked)
    if file_match:
        stream_path = file_match.group(1)
        if stream_path.startswith('/'):
            stream_url = f"https://hglink.to{stream_path}"
        else:
            stream_url = stream_path
        
        return stream_url, headers
    
    return None, None

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
        unpacked = re.sub(r'\\b' + token + r'\\b', keywords[i], unpacked)
    
    return unpacked
```

### Metóda 2: Simulácia main.js logiky (ALTERNATÍVA)

```python
import random
from urllib.parse import urlparse

def simulate_hglink_redirect(embed_url, referer='https://film-adult.top/'):
    """
    Simuluje redirect logiku z main.js
    
    Táto metóda funguje len ak HGLink používa loading page.
    Ak embed page priamo obsahuje video, použite Metódu 1.
    """
    dmca = ['hglink.to', 'hglink.com', 'hglink.net', 'hglink.org', 'hglink.info']
    main = ['hglink.to', 'hglink.com', 'hglink.net']
    rules = ['film-adult.top', 'film-adult.com']
    
    parsed = urlparse(referer)
    
    if parsed.hostname in rules:
        destination = random.choice(main)
    else:
        destination = random.choice(dmca)
    
    # Konštruuj finálnu URL
    embed_parsed = urlparse(embed_url)
    final_url = f"https://{destination}{embed_parsed.path}{embed_parsed.query}"
    
    # Teraz fetch final_url a použite Metódu 1
    return get_hglink_stream(final_url)
```

---

## 5. IMPLEMENTÁCIA DO EXTRACTOR.PY

### Potrebné zmeny:

#### A. Pridať do extractor.py (nahradiť riadky 176-178):

```python
# 5. HGLink JS Redirect Handling
if 'hglink.to' in input_url or 'hglink.com' in input_url:
    logger.info("Detected HGLink, attempting JS unpack...")
    
    # Check if this is loading page (has main.js)
    if 'main.js' in html:
        logger.info("Loading page detected, simulating redirect...")
        # Simulate redirect logic
        dmca = ['hglink.to', 'hglink.com', 'hglink.net', 'hglink.org', 'hglink.info']
        main_domains = ['hglink.to', 'hglink.com', 'hglink.net']
        rules = ['film-adult.top', 'film-adult.com']
        
        referer_host = urlparse(config.get('referer', input_url)).hostname
        if referer_host in rules:
            destination = main_domains[0]  # Use first for consistency
        else:
            destination = dmca[0]
        
        # Construct new URL
        parsed = urlparse(input_url)
        new_url = f"https://{destination}{parsed.path}"
        logger.info(f"Redirecting to: {new_url}")
        
        # Recursive call with new URL
        return get_stream_url(new_url)
    
    # If not loading page, try to unpack JS directly
    # (This is already handled by existing packed JS logic above)
```

#### B. Aktualizovať providers_config.py:

```python
def get_provider_config(url):
    # ... existing code ...
    
    if 'hglink.to' in url or 'hglink.com' in url:
        return {
            'referer': 'https://film-adult.top/',
            'extra_headers': {
                'Origin': 'https://film-adult.top'
            }
        }
```

---

## 6. TESTOVANIE

### Test script:

```python
from extractor import get_stream_url

# Test HGLink
test_url = "https://hglink.to/e/124fixrcqqxb"
stream_url, headers = get_stream_url(test_url)

if stream_url:
    print(f"✓ SUCCESS: {stream_url}")
    
    # Test if stream is accessible
    import requests
    r = requests.get(stream_url, headers=headers, verify=False)
    print(f"  Status: {r.status_code}")
    print(f"  Content-Type: {r.headers.get('Content-Type')}")
else:
    print("✗ FAILED: Could not extract stream")
```

---

## 7. ENDPOINTY A API

### Testované API endpointy (všetky zlyhali):
- `https://hglink.to/api/source/{video_id}` - 404
- `https://hglink.to/api/player/{video_id}` - 404
- `https://hglink.to/sources/{video_id}` - 404

**Záver**: HGLink NEMÁ verejné API. Jediný spôsob je parsing HTML + unpacking JS.

---

## 8. ZHRNUTIE

### Prečo testing_new neprehráva HGLink:
1. ❌ Extractor.py má prázdnu implementáciu pre HGLink redirect
2. ❌ Chýba logika na spracovanie obfuskovaného JavaScript
3. ❌ Chýba simulácia main.js redirect logiky

### Ako získať HGLink bez Selenium:
1. ✅ Fetch HTML stránky film-adult.top
2. ✅ Extrahovať HGLink embed URL pomocou regex
3. ✅ Fetch HGLink embed page
4. ✅ Nájsť a rozbalit packed JavaScript
5. ✅ Extrahovať "file" URL z rozbaleneho JS
6. ✅ Konštruovať finálnu stream URL

### Kľúčové zistenia:
- **Embed URL**: Hardkódovaný v HTML, nie API
- **Stream URL**: V obfuskovanom JS na embed page
- **Redirect**: main.js obsahuje redirect logiku (ale nie je potrebná ak priamo fetchujeme embed page)
- **Prípony**: `.urlset` = playlists, `.woff2` = segmenty

---

## 9. NEXT STEPS

1. Implementovať zmeny do `extractor.py`
2. Aktualizovať `providers_config.py`
3. Otestovať s reálnymi HGLink URL
4. Pridať do `server.py` podporu pre `.urlset` a `.woff2` v segment proxy
5. Otestovať celý flow: film-adult.top → HGLink → VLC playback
