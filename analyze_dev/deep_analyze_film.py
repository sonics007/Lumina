import requests
import re
import json
import logging

logging.basicConfig(level=logging.INFO)
requests.packages.urllib3.disable_warnings()

def deep_analyze():
    url = "https://film-adult.top/en/8051-secretaries-in-heat-3.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print(f"Deep analysis of {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        html = r.text
        
        # Save full HTML
        with open('film_adult_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved full HTML to film_adult_page.html")
        
        # 1. Look for all script tags
        print("\n=== SCRIPT TAGS ===")
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        print(f"Found {len(scripts)} inline scripts")
        
        # 2. Look for external scripts
        external_scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
        print(f"\nExternal scripts ({len(external_scripts)}):")
        for script in external_scripts:
            print(f"  - {script}")
        
        # 3. Look for player initialization
        print("\n=== PLAYER PATTERNS ===")
        if 'player' in html.lower():
            player_matches = re.findall(r'player[^=]*=\s*["\']?([^"\';\s]+)', html, re.IGNORECASE)
            print(f"Player references: {player_matches[:5]}")
        
        # 4. Look for video/embed URLs
        print("\n=== URL PATTERNS ===")
        urls = re.findall(r'https?://[^\s"\'<>]+', html)
        hglink_urls = [u for u in urls if 'hglink' in u or 'highload' in u]
        if hglink_urls:
            print("HGLink URLs found:")
            for u in hglink_urls:
                print(f"  - {u}")
        else:
            print("No HGLink URLs in HTML")
            
        # 5. Look for data attributes
        print("\n=== DATA ATTRIBUTES ===")
        data_attrs = re.findall(r'data-[a-z-]+=["\']([^"\']+)["\']', html)
        if data_attrs:
            print(f"Found {len(data_attrs)} data attributes (showing first 10):")
            for attr in data_attrs[:10]:
                print(f"  - {attr}")
        
        # 6. Look for API endpoints
        print("\n=== POTENTIAL API ENDPOINTS ===")
        api_patterns = [
            r'/api/[^\s"\'<>]+',
            r'/ajax/[^\s"\'<>]+',
            r'\.php\?[^\s"\'<>]+',
        ]
        for pattern in api_patterns:
            matches = re.findall(pattern, html)
            if matches:
                print(f"Pattern {pattern}: {matches[:3]}")
        
        # 7. Look for player tabs/buttons
        print("\n=== PLAYER TABS ===")
        player_tabs = re.findall(r'<[^>]*(?:player|tab)[^>]*>([^<]+)</[^>]+>', html, re.IGNORECASE)
        if player_tabs:
            print(f"Player tabs found: {player_tabs[:5]}")
            
        # 8. Check for specific player divs
        print("\n=== PLAYER CONTAINERS ===")
        player_divs = re.findall(r'<div[^>]*id=["\']([^"\']*player[^"\']*)["\']', html, re.IGNORECASE)
        if player_divs:
            print(f"Player div IDs: {player_divs}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    deep_analyze()
