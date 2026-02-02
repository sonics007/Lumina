import sys
import os
import requests
from bs4 import BeautifulSoup
import re

# Add bahu to path
sys.path.append(os.path.join(os.getcwd(), 'bahu'))
import client

def analyze():
    print("Logging in...")
    if not client.CLIENT.login():
        print("Login failed")
        return

    # Try to find a movie URL
    print("Getting movie list to find a target...")
    try:
        r = client.CLIENT.session.get("https://www.bahu.tv/filmek", params={"category": 1, "sort": "id DESC"})
        soup = BeautifulSoup(r.text, 'html.parser')
        item = soup.select_one('li.item a.poster')
        if not item:
            print("No items found on listing page.")
            # Fallback to series analysis only
        else:
            movie_url = item.get('href')
            if not movie_url.startswith('http'):
                movie_url = "https://www.bahu.tv" + movie_url
                
            print(f"Target Movie URL: {movie_url}")
            
            r2 = client.CLIENT.session.get(movie_url)
            with open('bahu/movie_dump.html', 'w', encoding='utf-8') as f:
                f.write(r2.text)
            print("Dumped Movie HTML.")
            
        # Analyze Series
        series_url = "https://www.bahu.tv/sorozat/a-ferfi-a-meh-ellen"
        print(f"Analyzing Series URL: {series_url}")
        r3 = client.CLIENT.session.get(series_url)
        with open('bahu/series_dump.html', 'w', encoding='utf-8') as f:
            f.write(r3.text)
        print("Dumped Series HTML.")
        
        # Analyze Episode
        ep_url = "https://www.bahu.tv/watch/63899"
        print(f"Analyzing Episode URL: {ep_url}")
        r4 = client.CLIENT.session.get(ep_url)
        with open('bahu/episode_dump.html', 'w', encoding='utf-8') as f:
            f.write(r4.text)
        print("Dumped Episode HTML.")

        soup4 = BeautifulSoup(r4.text, 'html.parser')
        iframes = soup4.find_all('iframe')
        for i in iframes:
             print(f"Episode Iframe: {i.get('src')}")

        
        # Quick check for iframe or providers
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        
        # Look for typical patterns
        iframes = soup2.find_all('iframe')
        for i in iframes:
            print(f"Iframe found: {i.get('src')}")
            
        # Look for 'a' tags with specific classes
        links = soup2.find_all('a')
        for l in links:
            href = l.get('href')
            if href and ('videa' in href or 'stream' in href or 'play' in href):
                print(f"Interesting link: {l.text.strip()} -> {href}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
