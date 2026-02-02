import sys
import os
import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.join(os.getcwd(), 'bahu'))
import client

def debug():
    print("Logging in...")
    if not client.CLIENT.login():
        print("Login failed")
        return

    url = "https://www.bahu.tv/sorozatok"
    
    # Try mimic browser form data exactly
    # Form fields: category, recommended_age, releaseDate
    # And maybe 'field_name_desktop' or 'field_name_mobile' if they are part of form submission? 
    # They are outside the form in navbar, but maybe JS includes them?
    # Form id="series-filter-form" only includes the selects.
    
    payload = {
        "category": "1", # Akció (as string)
        "recommended_age": "",
        "releaseDate": ""
    }
    
    print(f"POSTing to {url} with {payload}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://www.bahu.tv/sorozatok",
        "Origin": "https://www.bahu.tv"
    }
    # Note: If it's AJAX, X-Requested-With needed. But form action="/sorozatok" implies standard POST.
    
    r = client.CLIENT.session.post(url, data=payload, headers=headers)
    print(f"Status: {r.status_code}")
    print(f"Length: {len(r.text)}")
    
    soup = BeautifulSoup(r.text, 'html.parser')
    items = soup.select('li.item')
    print(f"Items found: {len(items)}")
    
    if items:
        print(f"First item: {items[0].find('a').get('title')}")
    else:
        print("No items.")
        
    with open('bahu/debug_post_result.html', 'w', encoding='utf-8') as f:
        f.write(r.text)

if __name__ == "__main__":
    debug()
