import requests
from bs4 import BeautifulSoup

URL = "https://film-adult.top/en/movies/"

def analyze():
    print(f"Fetching {URL}...")
    try:
        r = requests.get(URL)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        print(f"Final URL: {r.url}")
        print(f"Status Code: {r.status_code}")
        print(f"Preview: {r.text[:500]}...")
        
        # Hľadáme bežné DLE kontajnery
        # .short-story, .movie-item, etc.
        
        # Skúsim nájsť všetky odkazy na filmy (končia na .html) a majú obrazok
        links = soup.find_all('a', href=True)
        # Heuristika: Link konci na .html a obsahuje img tag (thumbnail)
        movie_links = [l for l in links if l['href'].endswith('.html') and l.find('img')]
        
        print(f"Found {len(movie_links)} potential movie links.")
        if movie_links:
             print("\n--- SAMPLE LINK ---")
             first = movie_links[0]
             print(f"Href: {first['href']}")
             print(f"Title: {first.get('title') or first.find('img').get('alt')}")
             
             print("\n--- SAMPLE CONTAINER ---")
             # Vypiseme rodica, aby sme videli kontajner
             parent = first.find_parent('div')
             if parent:
                 # Skusme najst najblizsi div s classou
                 while parent and not parent.get('class'):
                     parent = parent.find_parent('div')
                 if parent:
                     print(f"Container Class: {parent.get('class')}")
                     print(parent.prettify()[:1000]) # Len zaciatok
             else:
                 print(first.parent.prettify())
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze()
