import sys
import os
import requests
from bs4 import BeautifulSoup

# Add bahu dir to path
sys.path.append(os.path.join(os.getcwd(), 'bahu'))
import client

def check():
    print("Logging in...")
    if not client.CLIENT.login():
        print("Login failed")
        return

    url = "https://www.bahu.tv/sorozatok"
    print(f"Checking {url}")
    r = client.CLIENT.session.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    # Find category links
    print("Searching for category links...")
    links = soup.find_all('a')
    found = 0
    for l in links:
        href = l.get('href')
        if href and 'category=' in href:
            print(f"Cat Link: {l.text.strip()} -> {href}")
            found += 1
            
    if found == 0:
        print("No category links found with 'category=' parameter.")
        with open(os.path.join('bahu','sorozatok_dump.html'), 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("Dumped HTML to bahu/sorozatok_dump.html")
        
if __name__ == "__main__":
    check()
