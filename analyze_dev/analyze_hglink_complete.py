import requests
import re
import json
import logging

logging.basicConfig(level=logging.INFO)
requests.packages.urllib3.disable_warnings()

def analyze_hglink_complete():
    url = "https://hglink.to/e/124fixrcqqxb"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://film-adult.top/',
        'Origin': 'https://film-adult.top'
    }
    
    print(f"=== ANALYZING HGLINK: {url} ===\n")
    
    # 1. Get main page
    print("1. Fetching main page...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        html = r.text
        
        with open('hglink_embed_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"   Status: {r.status_code}")
        print(f"   Saved to: hglink_embed_page.html")
        print(f"   Page size: {len(html)} bytes")
        
        # Check for main.js
        if 'main.js' in html:
            print("   ⚠️  Loading page detected (main.js present)")
            
            # Extract main.js URL
            main_js_match = re.search(r'<script src="([^"]*main\.js[^"]*)"', html)
            if main_js_match:
                main_js_url = main_js_match.group(1)
                if not main_js_url.startswith('http'):
                    main_js_url = 'https://hglink.to' + main_js_url
                print(f"   Main.js URL: {main_js_url}")
                
                # Download main.js
                print("\n2. Downloading main.js...")
                r_js = requests.get(main_js_url, headers=headers, verify=False)
                with open('hglink_main_full.js', 'w', encoding='utf-8') as f:
                    f.write(r_js.text)
                print(f"   Saved to: hglink_main_full.js ({len(r_js.text)} bytes)")
                
                # Analyze main.js structure
                print("\n3. Analyzing main.js structure...")
                
                # Look for domain arrays
                dmca_match = re.search(r'const dmca=\[(.*?)\]', r_js.text, re.DOTALL)
                main_match = re.search(r'const main=\[(.*?)\]', r_js.text, re.DOTALL)
                rules_match = re.search(r'const rules=\[(.*?)\]', r_js.text, re.DOTALL)
                
                if dmca_match:
                    print("   ✓ Found 'dmca' array")
                if main_match:
                    print("   ✓ Found 'main' array")
                    # Try to extract domains
                    main_content = main_match.group(1)
                    # Look for string concatenations
                    domains = re.findall(r'["\']([^"\']+)["\']', main_content)
                    print(f"   Main array elements: {len(domains)}")
                    if domains:
                        print(f"   Sample: {domains[:3]}")
                        
                if rules_match:
                    print("   ✓ Found 'rules' array")
                
                # Look for URL construction
                print("\n4. Looking for URL construction logic...")
                url_pattern = re.search(r'const finalURL\s*=\s*([^;]+);', r_js.text)
                if url_pattern:
                    print(f"   finalURL construction: {url_pattern.group(1)[:100]}...")
                
                # Look for window.location assignment
                location_pattern = re.search(r'window\[.*?\]\s*=\s*finalURL', r_js.text)
                if location_pattern:
                    print("   ✓ Found redirect logic")
                    
        else:
            print("   ✓ Direct player page (no loading screen)")
            
            # Look for video sources
            print("\n2. Looking for video sources...")
            
            # Packed JS
            packed = re.search(r"eval\(function\(p,a,c,k,e,d\)", html)
            if packed:
                print("   ✓ Found Packed JS")
            
            # Direct m3u8/txt/urlset
            m3u8 = re.findall(r'https?://[^\s"\'<>]+\.(?:m3u8|txt|urlset)', html)
            if m3u8:
                print(f"   ✓ Found {len(m3u8)} playlist URLs:")
                for m in m3u8[:3]:
                    print(f"      - {m}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Try common API endpoints
    print("\n5. Testing API endpoints...")
    video_id = url.split('/')[-1]
    
    api_tests = [
        f"https://hglink.to/api/source/{video_id}",
        f"https://hglink.to/api/player/{video_id}",
        f"https://hglink.to/sources/{video_id}",
    ]
    
    for api_url in api_tests:
        try:
            r_api = requests.post(api_url, headers=headers, json={'id': video_id}, verify=False, timeout=5)
            print(f"   {api_url}")
            print(f"      Status: {r_api.status_code}")
            if r_api.status_code == 200:
                print(f"      Response: {r_api.text[:200]}")
        except Exception as e:
            print(f"   {api_url}: {str(e)[:50]}")

if __name__ == "__main__":
    analyze_hglink_complete()
