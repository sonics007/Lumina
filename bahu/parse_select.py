from bs4 import BeautifulSoup

def parse_selects():
    with open("structure_dump.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    print("Searching for SELECT elements...")
    selects = soup.find_all('select')
    
    for s in selects:
        print(f"\nSELECT found (Name: {s.get('name')}, Class: {s.get('class')})")
        options = s.find_all('option')
        
        count = 0
        for o in options:
            txt = o.text.strip()
            val = o.get('value')
            if txt and val:
                print(f"  Option: '{txt}' -> Value: '{val}'")
                count += 1
                if count > 10: 
                    print("  ... (more options) ...")
                    break

parse_selects()
