import client
from bs4 import BeautifulSoup

def check_series():
    client.CLIENT.login()
    
    url = "https://www.bahu.tv/sorozatok"
    print(f"Fetching {url}...")
    r = client.CLIENT.session.get(url)
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # 1. Check for list items
    items = soup.select('li.item')
    print(f"Items found: {len(items)}")
    
    if items:
        first = items[0]
        print("\nFirst Item HTML:")
        print(first.prettify()[:500])
        
        # Check link class
        link = first.find('a')
        if link:
            print(f"\nLink Class: {link.get('class')}")
            print(f"Link Href: {link.get('href')}")
    else:
        # Maybe structure is totally different
        print("\nNO ITEMS FOUND with 'li.item'. printing first <a> with '/sorozat/':")
        links = soup.find_all('a', href=True)
        for a in links:
            if '/sorozat/' in a['href']:
                print(f"Found specific link: {a} \nParent: {a.parent.name} Class: {a.parent.get('class')}")
                break

check_series()
