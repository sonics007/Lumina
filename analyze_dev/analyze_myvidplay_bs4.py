import requests
from bs4 import BeautifulSoup
import re

url = "https://myvidplay.com/e/nvck4fvk16ge"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://film-adult.top/'
}

print(f"Analyzing {url}...")
try:
    r = requests.get(url, headers=headers, timeout=15)
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    
    # Scripts
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} scripts.")
    
    for i, s in enumerate(scripts):
        if not s.string: continue
        content = s.string[:200].replace('\n', ' ')
        print(f"Script {i}: {content}...")
        
        if 'var dsplayer = videojs' in s.string:
            print(f"Found dsplayer config in script {i}!")
            # Save for check
            with open('myvidplay_config.js', 'w', encoding='utf-8') as f:
                f.write(s.string)

            # Extract basic m3u8
            m3u8_matches = re.findall(r'["\']([^"\']+\.m3u8[^"\']*)["\']', s.string)
                     
        # Check for packed
        if 'eval(function' in s.string:
            print("  -> Found Packed JS in this script!")
            # Save packed for analysis
            with open('myvidplay_packed.js', 'w', encoding='utf-8') as f:
                f.write(s.string)
    
    # Iframes
    iframes = soup.find_all('iframe')
    for i, f in enumerate(iframes):
        print(f"Iframe {i}: src={f.get('src')}")
        
    # Video tag
    video = soup.find('video')
    if video:
        print(f"Video tag found! src={video.get('src')}")
        for source in video.find_all('source'):
            print(f"  Source: {source.get('src')} type={source.get('type')}")
            
except Exception as e:
    print(f"Error: {e}")
