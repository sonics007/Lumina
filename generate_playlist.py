"""
Script na generovanie playlistu s filmom z film-adult.top
Extrahuje HGLink URL a vytvori channels.txt
"""

import requests
import re
import sys

def extract_hglink_from_page(page_url):
    """
    Extrahuje HGLink URL z film-adult.top stranky
    """
    print(f"[*] Fetching page: {page_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        r = requests.get(page_url, headers=headers, timeout=10)
        html = r.text
        
        # Hladat HGLink URL v HTML
        # Pattern 1: Direct iframe src
        pattern1 = r'src\s*=\s*["\']https://hglink\.to/e/([a-zA-Z0-9]+)["\']'
        match1 = re.search(pattern1, html)
        
        # Pattern 2: JavaScript variable
        pattern2 = r'https://hglink\.to/e/([a-zA-Z0-9]+)'
        match2 = re.search(pattern2, html)
        
        if match1:
            video_id = match1.group(1)
            hglink_url = f"https://hglink.to/e/{video_id}"
            print(f"[+] Found HGLink URL (pattern 1): {hglink_url}")
            return hglink_url
        elif match2:
            video_id = match2.group(1)
            hglink_url = f"https://hglink.to/e/{video_id}"
            print(f"[+] Found HGLink URL (pattern 2): {hglink_url}")
            return hglink_url
        else:
            print("[-] No HGLink URL found in page")
            
            # Debug: Show all URLs found
            all_urls = re.findall(r'https?://[^\s"\'<>]+', html)
            print(f"[*] All URLs found: {len(all_urls)}")
            for url in all_urls[:10]:
                print(f"    - {url}")
            
            return None
            
    except Exception as e:
        print(f"[-] Error fetching page: {e}")
        return None

def extract_movie_info(page_url):
    """
    Extrahuje nazov filmu a obrazok
    """
    print(f"[*] Extracting movie info...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        r = requests.get(page_url, headers=headers, timeout=10)
        html = r.text
        
        # Extract title
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        title = title_match.group(1).strip() if title_match else "Unknown Movie"
        
        # Extract image
        img_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if not img_match:
            img_match = re.search(r'<img[^>]+src="([^"]+)"[^>]*class="[^"]*poster', html)
        
        image = img_match.group(1) if img_match else ""
        
        print(f"[+] Title: {title}")
        print(f"[+] Image: {image}")
        
        return title, image
        
    except Exception as e:
        print(f"[-] Error extracting info: {e}")
        return "Unknown Movie", ""

def create_playlist(hglink_url, title, image):
    """
    Vytvori channels.txt playlist
    """
    print(f"\n[*] Creating playlist...")
    
    # Format: URL|Title|Image
    playlist_entry = f"{hglink_url}|{title}|{image}\n"
    
    # Write to channels.txt
    with open('channels.txt', 'w', encoding='utf-8') as f:
        f.write(playlist_entry)
    
    print(f"[+] Playlist created: channels.txt")
    print(f"\n[*] Playlist content:")
    print(f"    {playlist_entry.strip()}")
    
    return True

def main():
    print("=" * 80)
    print("FILM-ADULT.TOP PLAYLIST GENERATOR")
    print("=" * 80)
    
    # Movie URL
    movie_url = "https://film-adult.top/en/8051-secretaries-in-heat-3.html"
    
    # Extract HGLink URL
    hglink_url = extract_hglink_from_page(movie_url)
    
    if not hglink_url:
        print("\n[-] Failed to extract HGLink URL")
        sys.exit(1)
    
    # Extract movie info
    title, image = extract_movie_info(movie_url)
    
    # Create playlist
    create_playlist(hglink_url, title, image)
    
    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python server.py")
    print("2. Open VLC and load: http://127.0.0.1:5001/playlist.m3u8")
    print("=" * 80)

if __name__ == "__main__":
    main()
