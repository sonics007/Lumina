import client
from bs4 import BeautifulSoup

def debug_pages():
    client.CLIENT.login()
    
    # Get Page 1 Titles
    print("--- PAGE 1 ---")
    r1 = client.CLIENT.session.get("https://bahu.tv/filmek")
    s1 = BeautifulSoup(r1.text, 'html.parser')
    titles1 = []
    for a in s1.find_all('a', href=True):
        if a['href'].startswith('/film/'):
             # Try to find title
             img = a.find('img')
             if img and img.get('alt'):
                 titles1.append(img['alt'])
             elif a.get('title'):
                 titles1.append(a['title'])
    
    print(f"Found {len(titles1)} movies on Page 1")
    print(titles1[:5])

    # Get Page 2 Titles
    print("\n--- PAGE 2 ---")
    r2 = client.CLIENT.session.get("https://bahu.tv/filmek?Movie_page=2")
    s2 = BeautifulSoup(r2.text, 'html.parser')
    titles2 = []
    for a in s2.find_all('a', href=True):
        if a['href'].startswith('/film/'):
             img = a.find('img')
             if img and img.get('alt'):
                 titles2.append(img['alt'])
             elif a.get('title'):
                 titles2.append(a['title'])
                 
    print(f"Found {len(titles2)} movies on Page 2")
    print(titles2[:5])
    
    # Compare
    common = set(titles1).intersection(set(titles2))
    print(f"\nCommon titles: {len(common)}")
    if len(titles2) == 0:
        print("CRITICAL: Page 2 is empty or selectors failed!")
        # Save HTML for inspection
        with open("page2_debug.html", "w", encoding="utf-8") as f:
            f.write(r2.text)
        print("Saved page2_debug.html")

debug_pages()
