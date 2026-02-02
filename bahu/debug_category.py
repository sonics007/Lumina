import client
from bs4 import BeautifulSoup

def debug_cat():
    client.CLIENT.login()
    
    # Try the URL that failed 
    url = "https://www.bahu.tv/filmek?category=1&sort=id+DESC&Movie_page=1"
    
    print(f"Fetching {url}...")
    r = client.CLIENT.session.get(url)
    
    print(f"Status Code: {r.status_code}")
    print(f"Final URL: {r.url}") # Check for redirects
    
    with open("category_debug.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print("Saved category_debug.html")
    
    # Quick check for movie links
    soup = BeautifulSoup(r.text, 'html.parser')
    links = soup.find_all('a', href=True)
    count = 0
    for a in links:
        if a['href'].startswith('/film/'):
            count += 1
            if count < 5: print(f"Found Key Link: {a['href']}")
            
    print(f"Total /film/ links found: {count}")
    
    # Check if we are logged in?
    if "Kijelentkezés" in r.text:
        print("Confirmed: We are logged in.")
    else:
        print("WARNING: Login indicator not found in HTML!")

debug_cat()
