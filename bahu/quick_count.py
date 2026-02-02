"""
Rýchle počítanie - koľko SKUTOČNE unikátnych filmov je na bahu.tv
"""
import requests
from bs4 import BeautifulSoup
import client
import time

BASE_URL = "https://www.bahu.tv"

# Set to store unique URLs
unique_urls = set()
total_items_seen = 0
pages_checked = 0

def quick_count_category(cat_name, cat_id=None, page_type="filmek", max_pages=1000, url_override=None):
    global unique_urls, total_items_seen, pages_checked
    
    print(f"\n🔍 Checking: {cat_name}")
    first_page_urls = set()
    
    for i in range(1, max_pages + 1):
        params = {}
        
        if url_override:
            url = url_override
            params["Movie_page"] = i if page_type == "filmek" else None
            if params["Movie_page"] is None:
                params["Serial_page"] = i
        else:
            if cat_id is not None:
                params = {"category": cat_id, "sort": "id DESC"}
            url = f"{BASE_URL}/filmek" if page_type == "filmek" else f"{BASE_URL}/sorozatok"
            params["Movie_page"] = i if page_type == "filmek" else None
            if params["Movie_page"] is None:
                params["Serial_page"] = i
        
        try:
            r = client.CLIENT.session.get(url, params=params, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            items = soup.select('li.item')
            
            if not items:
                print(f"   Page {i}: Empty, stopping")
                break
            
            # Loop detection
            first_item = items[0].find('a', class_='movies-link')
            if first_item:
                check_href = first_item.get('href', '')
                if i == 1:
                    first_page_urls.add(check_href)
                elif i > 1 and check_href in first_page_urls:
                    print(f"   Page {i}: Loop detected, stopping")
                    break
            
            page_new_urls = 0
            for item in items:
                a_link = item.find('a', class_='movies-link')
                if a_link:
                    href = a_link.get('href', '')
                    if '/film/' in href or '/sorozat/' in href:
                        if href.startswith('http'):
                            clean_url = href.split('?')[0]
                        else:
                            clean_url = (BASE_URL + href if href.startswith('/') else '/' + href).split('?')[0]
                            clean_url = clean_url.replace(BASE_URL + BASE_URL, BASE_URL)
                        
                        total_items_seen += 1
                        if clean_url not in unique_urls:
                            unique_urls.add(clean_url)
                            page_new_urls += 1
            
            pages_checked += 1
            
            if i % 10 == 0:
                print(f"   Page {i}: {page_new_urls} new, Total unique: {len(unique_urls)}, Total seen: {total_items_seen}")
            
            # Stop if no new URLs found for several pages
            if page_new_urls == 0 and i > 5:
                print(f"   Page {i}: No new URLs, stopping")
                break
                
        except Exception as e:
            print(f"   Error on page {i}: {e}")
            break
    
    print(f"   ✓ Category done: {len(unique_urls)} unique URLs total")

if __name__ == "__main__":
    if not client.CLIENT.login():
        print("Login failed!")
        exit()
    
    print("="*70)
    print("RÝCHLE POČÍTANIE UNIKÁTNYCH FILMOV")
    print("="*70)
    
    start_time = time.time()
    
    # Check main filmek page (all movies)
    print("\n📊 Checking main /filmek page (all categories)...")
    quick_count_category("All Movies", cat_id=None, page_type="filmek", max_pages=1000, url_override=f"{BASE_URL}/filmek")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*70)
    print("VÝSLEDKY:")
    print("="*70)
    print(f"Pages checked:        {pages_checked}")
    print(f"Total items seen:     {total_items_seen}")
    print(f"Unique URLs found:    {len(unique_urls)}")
    print(f"Duplicates:           {total_items_seen - len(unique_urls)}")
    print(f"Time taken:           {duration:.2f} seconds")
    print("="*70)
    
    # Save unique URLs
    with open("unique_urls.txt", "w", encoding="utf-8") as f:
        for url in sorted(unique_urls):
            f.write(url + "\n")
    
    print(f"\n✅ Unique URLs saved to unique_urls.txt")
