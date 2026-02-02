import client
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)

def check_structure():
    client.CLIENT.login()
    
    url = "https://www.bahu.tv/filmek"
    print(f"Fetching {url}...")
    r = client.CLIENT.session.get(url)
    
    # Save full HTML for deep inspection
    with open("structure_dump.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print("Saved structure_dump.html")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    print("\n--- Analysing Menu / Sidebar ---")
    # Finding elements that might contain categories/groups
    # Usually lists <ul> or divs with many links
    
    # Try finding the "Kategória" text from your screenshot
    # And see parent element
    target = soup.find(string="Kategória")
    if target:
        parent = target.parent
        print(f"Found 'Kategória' in: {parent.name} (Class: {parent.get('class')})")
        
        # Traverse up to find the container
        container = parent.find_parent('div') or parent.find_parent('ul')
        if container:
            print("\nLinks in this container:")
            for a in container.find_all('a'):
                print(f"Link: {a.text.strip()} -> {a.get('href')}")
    else:
        print("'Kategória' text not found directly. Maybe in a placeholder or attribute.")
        
    print("\n--- Searching for Hungarian Category names (Sample) ---")
    # Akcio, Drama, Horror
    for cat in ["Akció", "Dráma", "Horror", "Vígjáték"]:
        l = soup.find('a', string=cat)
        if l:
            print(f"Found {cat}: {l.get('href')}")
        else:
            print(f"Not found: {cat}")

check_structure()
