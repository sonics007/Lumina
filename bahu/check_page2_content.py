import client
from bs4 import BeautifulSoup

def check_content_change():
    client.CLIENT.login()
    
    # 1. Fetch Page 1
    print("Fetching Page 1...")
    r1 = client.CLIENT.session.get("https://www.bahu.tv/filmek")
    s1 = BeautifulSoup(r1.text, 'html.parser')
    titles1 = [img['alt'] for img in s1.find_all('img', alt=True) if img.parent.name == 'a' and '/film/' in img.parent['href']]
    print(f"Page 1 Titles: {titles1[:3]}")

    # 2. Fetch Page 2 (AJAX URL but returns Full HTML apparently)
    print("Fetching Page 2 (AJAX URL)...")
    url = "https://www.bahu.tv/filmek"
    params = {
        "ajax": "moviesListView",
        "category": "1", # Action
        "sort": "",
        "Movie_page": "2",
        "rating": "", "recommended_age": "", "releaseDate": ""
    }
    r2 = client.CLIENT.session.get(url, params=params)
    s2 = BeautifulSoup(r2.text, 'html.parser')
    titles2 = [img['alt'] for img in s2.find_all('img', alt=True) if img.parent.name == 'a' and '/film/' in img.parent['href']]
    print(f"Page 2 Titles: {titles2[:3]}")
    
    # Compare
    if titles1 == titles2:
        print("\nFAILURE: Page 1 and Page 2 are IDENTICAL.")
    else:
        print("\nSUCCESS! Page 2 has different content!")
        print("We can scrape this even if it is full HTML.")

check_content_change()
