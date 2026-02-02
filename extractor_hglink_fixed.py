import requests
import re
import logging
import traceback
from urllib.parse import urlparse, unquote
import requests.packages.urllib3
import sys
import os

# Disable insecure request warnings
requests.packages.urllib3.disable_warnings()

# Ensure local imports work by adding current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Helper to import config
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

def get_stream_url(input_url):
    """
    Main extraction function supporting multi-layer obfuscation and nested iframes.
    NOW WITH FULL HGLINK SUPPORT!
    """
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
                return get_stream_url(embed_url)
        except Exception as e:
            logger.error(f"Failed to parse embed page: {e}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': config.get('referer', input_url),
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    headers.update(config.get('extra_headers', {}))
    
    try:
        session = requests.Session()
        r = session.get(input_url, headers=headers, timeout=10, verify=False)
        html = r.text
        
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
                s_url, s_headers = get_stream_url(iframe_url)
                if s_url:
                     return s_url, s_headers

        # 5. HGLink JS Redirect Handling (NEW!)
        if 'hglink.to' in input_url or 'hglink.com' in input_url or 'hglink.net' in input_url:
            logger.info("🔍 Detected HGLink URL, checking for loading page...")
            
            # Check if this is loading page (has main.js)
            if 'main.js' in html:
                logger.info("⚠️  Loading page detected with main.js redirect!")
                logger.info("🔄 Simulating JavaScript redirect logic...")
                
                # Simulate redirect logic from main.js
                dmca = ['hglink.to', 'hglink.com', 'hglink.net', 'hglink.org', 'hglink.info']
                main_domains = ['hglink.to', 'hglink.com', 'hglink.net']
                rules = ['film-adult.top', 'film-adult.com']
                
                referer_host = urlparse(headers.get('Referer', input_url)).hostname
                if referer_host and referer_host in rules:
                    destination = main_domains[0]  # Use first for consistency
                    logger.info(f"   Referer {referer_host} matches rules → using main domain")
                else:
                    destination = dmca[0]
                    logger.info(f"   Referer {referer_host} not in rules → using dmca domain")
                
                # Construct new URL
                parsed = urlparse(input_url)
                new_url = f"https://{destination}{parsed.path}"
                logger.info(f"   🎯 Redirecting to: {new_url}")
                
                # Recursive call with new URL
                return get_stream_url(new_url)
            else:
                logger.info("✓ Direct embed page (no loading screen)")
                # Packed JS should have been processed above
                # If we're here, it means packed JS didn't find stream
                logger.warning("⚠️  HGLink embed page found but no stream extracted from packed JS")

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        traceback.print_exc()
        
    return None, None
