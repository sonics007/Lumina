import client
import json
from bs4 import BeautifulSoup

def check_resources():
    client.CLIENT.login()
    
    # 1. Check Sitemap
    sitemaps = [
        "https://www.bahu.tv/sitemap.xml",
        "https://www.bahu.tv/sitemap_index.xml",
        "https://www.bahu.tv/robots.txt"
    ]
    
    print("--- Checking Sitemaps ---")
    for url in sitemaps:
        r = client.CLIENT.session.get(url)
        print(f"{url}: {r.status_code}")
        if r.status_code == 200:
            print(f"Preview: {r.text[:200]}")

    # 2. Check Autocomplete API
    print("\n--- Checking AutoComplete API ---")
    url = "https://www.bahu.tv/site/autoComplete"
    queries = ["a", "avengers", "%", ""]
    
    for q in queries:
        params = {"term": q}
        r = client.CLIENT.session.get(url, params=params)
        print(f"Query '{q}': {r.status_code}")
        try:
            data = r.json()
            print(f"Found {len(data)} items")
            if len(data) > 0:
                print(f"Sample: {data[0]}")
        except:
            print("Not JSON")

check_resources()
