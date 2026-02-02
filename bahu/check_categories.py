import client
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

def check_categories():
    client.CLIENT.login()
    
    url = "https://www.bahu.tv/filmek"
    r = client.CLIENT.session.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Try looking for links inside a dropdown or category list
    # Based on image, it's a list. Probably <ul> or just many <a> tags in a sidebar/menu.
    
    print("Searching for Category Links...")
    
    # Heuristic: Links that contain /filmek/SOMETHING but not ?page or specific movie
    links = soup.find_all('a', href=True)
    categories = set()
    
    for a in links:
        href = a['href']
        # Normalized check
        if '/filmek/' in href and href.count('/') == 2 and '?' not in href:
             # Exclude specific movies if their URL is also /filmek/name-of-movie
             # Categories usually standard words. 
             # Let's print candidate
             print(f"Candidate: {href} (Text: {a.text.strip()})")
             categories.add(href)
             
    print(f"Found {len(categories)} potential categories.")

check_categories()
