import client
from bs4 import BeautifulSoup
import re

def analyze_pagination():
    print("Logging in...")
    if not client.CLIENT.login():
        print("Login failed")
        return

    url = "https://bahu.tv/filmek"
    print(f"Fetching {url}...")
    r = client.CLIENT.session.get(url)
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # 1. Search for 'pagination' classes
    pag = soup.find(class_=re.compile("pagin"))
    if pag:
        print("\nFound Pagination Element:")
        print(pag.prettify())
    else:
        print("\nNo explicit 'pagination' class found.")
        
    # 2. Search for links with 'page' in href
    print("\nSearching for links with 'page' in URL:")
    links = soup.find_all('a', href=re.compile("page"))
    for l in links:
        print(f"Text: {l.text.strip()} | Href: {l['href']}")

    # 3. Print form actions (maybe it's a form?)
    print("\nSearching for forms:")
    forms = soup.find_all('form')
    for f in forms:
        print(f"Form Action: {f.get('action')}")

analyze_pagination()
