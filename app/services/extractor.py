import requests
import re
import logging
import traceback
from urllib.parse import urlparse, unquote
import requests.packages.urllib3
import sys
import os
import subprocess
import time
import random
import string
from curl_cffi import requests as c_requests

# Disable insecure request warnings (legacy)
import requests
requests.packages.urllib3.disable_warnings()

# Ensure local imports work by adding current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Helper to import config
# Adjust path for providers_config if it's in root
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..')) 
try:
    from providers_config import get_provider_config
except ImportError:
    logger.error("Failed to import providers_config. Make sure the file exists.")
    # Fallback dummy function
    def get_provider_config(url): return {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _unpack_js(p, a, c, k_str):
    """
    Dean Edwards Packer Unpacker
    """
    keywords = k_str.split('|')
    encoded_a = int(a)
    encoded_c = int(c)
    
    def to_base36(n):
        if n == 0: return '0'
        # Base conversion logic
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
        # Use word boundaries for replacement
        unpacked = re.sub(r'\b' + token + r'\b', keywords[i], unpacked)
        
    return unpacked

def extract_doodstream(url, session=None):
    if session is None: 
        session = c_requests.Session(impersonate="chrome120")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        # Initial request
        r = session.get(url, headers=headers)
        html = r.text
        
        # 1. Find /pass_md5/ URL
        pass_md5 = re.search(r"['\"](/pass_md5/[^'\"]+)['\"]", html)
        if not pass_md5:
            return None, None
            
        pass_path = pass_md5.group(1)
        pass_url = "https://" + urlparse(url).netloc + pass_path
        
        # 2. Call pass_md5 with Referer!
        headers['Referer'] = url
        r2 = session.get(pass_url, headers=headers)
        part1 = r2.text
        
        # 3. Generate random string
        letters = string.ascii_letters + string.digits
        random_token = "".join(random.choice(letters) for _ in range(10))
        
        # Extract token from path (last segment)
        token_val = pass_path.split('/')[-1]
        
        expiry = int(time.time() * 1000)
        
        final_url = f"{part1}{random_token}?token={token_val}&expiry={expiry}"
        
        return final_url, headers
    except Exception as e:
        logger.error(f"Doodstream error: {e}")
        return None, None

def extract_streamtape(url, session=None):
    if session is None:
        session = c_requests.Session(impersonate="chrome120")
    try:
        r = session.get(url, timeout=10)
        # Look for robotlink or similar pattern - try generic regex
        pattern = r"document\.getElementById\(['\"]([a-zA-Z0-9_]+)['\"]\)\.innerHTML\s*=\s*(.*);"
        matches = re.finditer(pattern, r.text)
        
        for m in matches:
            right_side = m.group(2)
            # Extract all string literals and join them
            parts = re.findall(r"['\"]([^'\"]*)['\"]", right_side)
            full_url = "".join(parts)
            
            if "get_video" in full_url:
                if full_url.startswith('//'): 
                    full_url = "https:" + full_url
                elif not full_url.startswith('http'):
                    if full_url.startswith('/streamtape.com'):
                        full_url = "https://" + full_url.lstrip('/')
                    elif full_url.startswith('/'):
                        full_url = "https://streamtape.com" + full_url
                    else:
                        full_url = "https://streamtape.com/" + full_url
                
                logger.info(f"StreamTape extracted: {full_url}")
                
                # Pass cookies
                headers = {}
                try:
                    if session:
                        cookies = session.cookies.get_dict()
                        if cookies:
                            headers['Cookie'] = "; ".join([f"{k}={v}" for k,v in cookies.items()])
                except: pass
                
                return full_url, headers
        
        logger.warning("StreamTape: No link found.")
                
    except Exception as e:
        logger.error(f"StreamTape extract failed: {e}")
    return None, None

def extract_filemoon(url, session=None):
    if session is None:
        session = c_requests.Session(impersonate="chrome120")
    try:
        r = session.get(url, timeout=10)
        
        # 1. Packed JS
        pattern = r"return p}\('(.*?)',(\d+),(\d+),'([^']+)'\.split\('\|'\)"
        match = re.search(pattern, r.text)
        if match:
             p, a, c, k = match.groups()
             unpacked = _unpack_js(p, a, c, k) 
             
             # 2. Extract links - look for m3u8
             m_link = re.search(r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']', unpacked)
             if m_link:
                 final_url = m_link.group(1)
                 logger.info(f"FileMoon/Callis extracted: {final_url}")
                 
                 # Headers for playback - CRITICAL: Referer must match the EMBED URL, not just origin
                 headers = {
                     'Referer': url,
                     'Origin': f"https://{urlparse(url).netloc}",
                     'User-Agent': session.headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
                     'Accept': '*/*',
                     'Accept-Language': 'en-US,en;q=0.9',
                     'Connection': 'keep-alive'
                 }
                 return final_url, headers
                 
    except Exception as e:
        logger.error(f"FileMoon extract failed: {e}")
    return None, None

def extract_with_ytdlp(url):
    logger.info(f"Attempting yt-dlp extraction for: {url}")
    try:
        cmd = ['yt-dlp', '-g', '--no-warnings', '--no-check-certificate', url]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode != 0:
            logger.warning(f"yt-dlp returned code {result.returncode}: {result.stderr}")
            return None, None
            
        stream_url = result.stdout.strip().split('\n')[0]
        if stream_url and stream_url.startswith('http'):
            logger.info(f"yt-dlp success: {stream_url[:50]}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            return stream_url, headers
    except Exception as e:
        logger.error(f"yt-dlp failed: {e}")
    return None, None

def get_stream_url(input_url, session=None, _recursion_depth=0, referer=None):
    """
    Main extraction function supporting multi-layer obfuscation and nested iframes.
    """
    # Recursion guard
    if _recursion_depth > 3:
        logger.error(f"Max recursion depth reached for extraction: {input_url}")
        return None, None

    # HARD DEBUG PRINTS
    print(f"DEBUG_EXTRACTOR: Starting extraction for {input_url}")
    sys.stdout.flush()
    logger.info(f"Extracting stream for: {input_url}")
    
    config = get_provider_config(input_url)
    print(f"DEBUG_EXTRACTOR: Config loaded: {config}")
    sys.stdout.flush()
    if not config:
        logger.warning(f"No provider config found for {input_url}. This might cause extraction failure.")
    
    # Iframe logic fallback (initial check for obvious embeds)
    if not config:
        try:
            logger.info("Checking for embedded iframe (no config mode)...")
            r_host = requests.get(input_url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
            match_iframe = re.search(r'<iframe[^>]+src=["\'](http[^"\']+)["\']', r_host.text)
            if match_iframe:
                embed_url = match_iframe.group(1)
                if embed_url.startswith('//'): embed_url = 'https:' + embed_url
                logger.info(f"Found embed: {embed_url}")
                return get_stream_url(embed_url, _recursion_depth=_recursion_depth+1, referer=referer)
        except Exception as e:
            logger.error(f"Failed to parse embed page: {e}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': referer if referer else config.get('referer', input_url),
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    headers.update(config.get('extra_headers', {}))
    
    headers.update(config.get('extra_headers', {}))
    
    # Check for known yt-dlp providers (StreamTape, MixDrop, etc.)
    if any(x in input_url for x in ['streamtape', 'mixdrop', 'voe', 'filemoon', 'earnvid']):
         s_url, s_headers = extract_with_ytdlp(input_url)
         if s_url: return s_url, s_headers
    
    # Fallback for StreamTape custom extractor
    if 'streamtape' in input_url:
         s_url, s_headers = extract_streamtape(input_url, session)
         if s_url: return s_url, s_headers

    # Fallback for FileMoon/Callistanise/Earnvid custom
    if any(x in input_url for x in ['callistanise', 'filemoon', 'earnvid', 'dingtezuni']):
         s_url, s_headers = extract_filemoon(input_url, session)
         if s_url: return s_url, s_headers
    
    try:
        # Doodstream / Myvidplay Handler
        if any(x in input_url for x in ['myvidplay', 'dood', 'auvexiug', 'ds2play']):
             s_url, s_headers = extract_doodstream(input_url, session)
             if s_url: return s_url, s_headers

        # Use provided session or create new one
        if session is None:
            session = c_requests.Session(impersonate="chrome120")
            
        r = session.get(input_url, headers=headers, timeout=10, verify=False)
        html = r.text
        
        # 5. HGLink handling - Loading Page Check
        # Check for loading page vs direct page
        if ('hglink.to' in input_url or 'hglink.com' in input_url) and 'main.js' in html:
            logger.info("HGLink loading page detected. Trying mirrors + Wait strategy...")
            
            # Known mirrors/destinations for HGLink
            mirrors = ['haxloppd.com', 'shavtape.com', 'myvidplay.com']
            
            parsed = urlparse(input_url)
            for mirror in mirrors:
                new_url = input_url.replace(parsed.netloc, mirror)
                s_url, s_headers = get_stream_url(new_url, session=session, _recursion_depth=_recursion_depth+1, referer=referer)
                if s_url:
                    return s_url, s_headers
            
            # User Strategy: Wait and Retry (Simulate main.js redirect)
            logger.info("Mirrors failed. Waiting 2.5s for redirect...")
            time.sleep(2.5)
            return get_stream_url(input_url, session=session, _recursion_depth=_recursion_depth+1, referer=referer)

        # 0. Check for unescape() obfuscation - Iterate ALL matches
        if 'unescape' in html:
            matches_unescape = re.findall(r'unescape\s*\(\s*(["\'])(.*?)\1\s*\)', html, re.DOTALL)
            if matches_unescape:
                logger.info(f"Found {len(matches_unescape)} unescape() blocks. Decoding and appending...")
                for quote, content in matches_unescape:
                    try:
                        decoded = unquote(content)
                        html += "\n" + decoded 
                    except Exception as e:
                        logger.warning(f"Failed to unescape block: {e}")

        # 1. Look for PACKED JS code - Iterate ALL matches
        # Fix regex for raw strings and greediness
        pattern = r"}\('((?:[^']|\\')*)',(\d+),(\d+),'((?:[^']|\\')*)'.split\('\|'\)"
        matches_packed = re.findall(pattern, html)
        
        if matches_packed:
            logger.info(f"Found {len(matches_packed)} Packed JS blocks. Iterating...")
            for p, a, c, k in matches_packed:
                try:
                    unpacked_code = _unpack_js(p, a, c, k)
                    
                    # 2. Search for URLs in unpacked code
                    potential_links = []
                    matches_json = re.findall(r'"(hls\d|file)"\s*:\s*["\']([^"\']+)["\']', unpacked_code)
                    for _, link in matches_json: potential_links.append(link)
                        
                    matches_var = re.findall(r'(?:file|src)\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']', unpacked_code)
                    potential_links.extend(matches_var)
                    
                    # 3. Select valid link
                    for link in potential_links:
                        # Support for HgLink extensions (.urlset, .woff2)
                        if any(ext in link for ext in [".m3u8", ".txt", ".urlset", ".woff2"]):
                            if link.startswith('/'):
                                parsed = urlparse(r.url) 
                                link = f"{parsed.scheme}://{parsed.netloc}{link}"
                            
                            logger.info(f"Stream found in Packed JS: {link}")
                            
                            # Clean headers to avoid 500 CDN error on HGLink mirrors
                            # Centaurus CDN often rejects requests with incorrect Origin/Referer
                            parsed = urlparse(r.url)
                            headers['Origin'] = f"{parsed.scheme}://{parsed.netloc}"
                            headers['Referer'] = str(r.url)
                            
                            # Pass cookies (Centaurus might need them)
                            try:
                                if session:
                                    # curl_cffi cookies might be accessed differently, try standard dict
                                    cookies = session.cookies.get_dict()
                                    if cookies:
                                        headers['Cookie'] = "; ".join([f"{k}={v}" for k,v in cookies.items()])
                            except: pass
                            
                            return link, headers
                            
                except Exception as e:
                     logger.warning(f"Error unpacking/parsing block: {e}")
            
            logger.warning("Checked all Packed JS blocks, no stream found.")
            
        else:
            logger.warning("No packed JS found on page.")
        
        # Fallback: Direct M3U8 in HTML
        if ".m3u8" in html:
             direct = re.search(r'["\']([^"\']+\.m3u8[^"\']*)["\']', html)
             if direct:
                 logger.info(f"Found direct m3u8: {direct.group(1)}")
                 return direct.group(1), headers

        # Fallback: Nested Iframes (Loop)
        matches_iframe = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
        if matches_iframe:
            logger.info(f"Found {len(matches_iframe)} fallback iframes. Checking...")
            for iframe_url in matches_iframe:
                if iframe_url.startswith('//'):
                    iframe_url = 'https:' + iframe_url
                elif not iframe_url.startswith(('http:', 'https:')):
                    parsed = urlparse(r.url)
                    iframe_url = f"{parsed.scheme}://{parsed.netloc}/{iframe_url.lstrip('/')}"
                
                if iframe_url == input_url: continue
                
                # Recursive attempt
                s_url, s_headers = get_stream_url(iframe_url, session=session, _recursion_depth=_recursion_depth+1, referer=referer) # Pass session!
                if s_url:
                     return s_url, s_headers

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        traceback.print_exc()
        
    return None, None
