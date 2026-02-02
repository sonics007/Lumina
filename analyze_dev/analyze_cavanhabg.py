import requests
import re
import json
import logging

logging.basicConfig(level=logging.INFO)
requests.packages.urllib3.disable_warnings()

def analyze_cavanhabg_complete():
    url = "https://cavanhabg.com/s4bp3dcmjk1y"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://cavanhabg.com/',
        'Accept': '*/*',
        'Accept-Encoding': 'identity'
    }
    
    print(f"=== ANALYZING CAVANHABG: {url} ===\n")
    
    # 1. Get main page
    print("1. Fetching main page...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        html = r.text
        
        with open('cavanhabg_embed_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"   Status: {r.status_code}")
        print(f"   Saved to: cavanhabg_embed_page.html")
        print(f"   Page size: {len(html)} bytes")
        
        # Check cookies
        print(f"\n2. Cookies received:")
        for cookie in r.cookies:
            print(f"   {cookie.name} = {cookie.value}")
        
        # Look for Packed JS
        print("\n3. Looking for Packed JS...")
        packed_matches = re.findall(r"eval\(function\(p,a,c,k,e,d\)", html)
        if packed_matches:
            print(f"   ✓ Found {len(packed_matches)} Packed JS blocks")
            
            # Extract packed code
            pattern = r"\}\\('(.+?)',(\\d+),(\\d+),'(.+?)\\.split\\('\\|'\\)\\)\\)"
            match = re.search(pattern, html, re.DOTALL)
            
            if match:
                p, a, c, k_str = match.groups()
                print(f"   Packed params:")
                print(f"      a (radix): {a}")
                print(f"      c (count): {c}")
                print(f"      keywords: {len(k_str.split('|'))} items")
                
                # Save packed code for analysis
                with open('cavanhabg_packed.txt', 'w', encoding='utf-8') as f:
                    f.write(f"p={p}\n\na={a}\nc={c}\nk={k_str}")
                print(f"   Saved packed code to: cavanhabg_packed.txt")
        
        # Look for direct m3u8/urlset
        print("\n4. Looking for video sources...")
        m3u8_urls = re.findall(r'https?://[^\s"\'<>]+\.(?:m3u8|txt|urlset)[^\s"\'<>]*', html)
        if m3u8_urls:
            print(f"   ✓ Found {len(m3u8_urls)} playlist URLs:")
            for m in m3u8_urls[:5]:
                print(f"      - {m}")
        else:
            print("   ⚠️  No direct playlist URLs found (likely in packed JS)")
        
        # Look for external scripts
        print("\n5. External scripts...")
        scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
        if scripts:
            print(f"   Found {len(scripts)} external scripts:")
            for s in scripts[:5]:
                print(f"      - {s}")
        
        # Look for API calls in JS
        print("\n6. Looking for API endpoints...")
        api_patterns = [
            r'fetch\(["\']([^"\']+)["\']',
            r'ajax\(["\']([^"\']+)["\']',
            r'XMLHttpRequest.*?open\(["\']GET["\'],\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html)
            if matches:
                print(f"   Found API calls:")
                for m in matches[:3]:
                    print(f"      - {m}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Try common API endpoints
    print("\n7. Testing API endpoints...")
    video_id = url.split('/')[-1]
    
    api_tests = [
        f"https://cavanhabg.com/api/source/{video_id}",
        f"https://cavanhabg.com/api/player/{video_id}",
        f"https://cavanhabg.com/sources/{video_id}",
        f"https://cavanhabg.com/api/video/{video_id}",
    ]
    
    for api_url in api_tests:
        try:
            # Try POST
            r_api = requests.post(api_url, headers=headers, json={'id': video_id}, verify=False, timeout=5)
            print(f"   POST {api_url}")
            print(f"      Status: {r_api.status_code}")
            if r_api.status_code == 200:
                print(f"      Response: {r_api.text[:200]}")
        except Exception as e:
            print(f"   POST {api_url}: {str(e)[:50]}")
        
        try:
            # Try GET
            r_api = requests.get(api_url, headers=headers, verify=False, timeout=5)
            print(f"   GET {api_url}")
            print(f"      Status: {r_api.status_code}")
            if r_api.status_code == 200:
                print(f"      Response: {r_api.text[:200]}")
        except Exception as e:
            print(f"   GET {api_url}: {str(e)[:50]}")

if __name__ == "__main__":
    analyze_cavanhabg_complete()
