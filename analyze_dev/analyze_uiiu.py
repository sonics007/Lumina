
from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import sys
import os

# Utf-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

url = "https://uiiumovie.com/follow-me-vol-2-2026/"
print(f"Analyzing {url}...")

try:
    session = requests.Session(impersonate="chrome120")
    r = session.get(url, timeout=15)
    print(f"Status: {r.status_code}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Check Title
    print(f"Title: {soup.title.string if soup.title else 'No Title'}")
    
    # 1. Look for iframes
    iframes = soup.find_all('iframe')
    print(f"\nFound {len(iframes)} iframes:")
    for i, fr in enumerate(iframes):
        src = fr.get('src')
        print(f"  [{i+1}] {src}")
        
    # 2. Look for data-type servers
    # Usually in ul#playeroptionsul li
    ul_tabs = soup.select('ul#playeroptionsul li')
    if ul_tabs:
         print(f"\nFound {len(ul_tabs)} server tabs (Doopaly style?):")
         for li in ul_tabs:
             oid = li.get('data-post')
             ntype = li.get('data-type')
             noption = li.get('data-option') # This might be the encoded URL/ID
             title = li.get_text(strip=True)
             print(f"  - [{title}] Type: {ntype}, Option: {noption}")
             
             # If ajax needed, we need to POST to admin-ajax.php usually.
             
    # Look for generic links that look like streams
    print("\nScanning for known providers in links:")
    for a in soup.find_all('a', href=True):
        href = a['href']
        if any(x in href for x in ['dood', 'vidplay', 'filemoon', 'streamtape', 'mixdrop', 'voe']):
            print(f"  Link: {href}")

    # Dump HTML to file for manual inspect if needed
    with open('uiiu_dump.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print("\nSaved HTML to uiiu_dump.html")

except Exception as e:
    print(f"Error: {e}")
