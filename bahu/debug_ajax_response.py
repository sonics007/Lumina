import client
import json

def debug_ajax_headers():
    client.CLIENT.login()
    
    url = "https://www.bahu.tv/filmek"
    params = {
        "ajax": "moviesListView",
        "category": "1",
        "sort": "",
        "Movie_page": "2",
        # Empty ones
        "rating": "",
        "recommended_age": "",
        "releaseDate": ""
    }
    
    # Base headers
    headers_list = [
        {"X-Requested-With": "XMLHttpRequest", "Accept": "*/*"},
        {"X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/javascript, */*; q=0.01"},
        {"X-Requested-With": "XMLHttpRequest", "Referer": "https://www.bahu.tv/filmek"},
    ]
    
    for i, h in enumerate(headers_list):
        print(f"\n--- TEST {i+1} ---")
        client.CLIENT.session.headers.update(h)
        
        r = client.CLIENT.session.get(url, params=params)
        
        print(f"Status: {r.status_code}")
        is_html_doc = "<!DOCTYPE html>" in r.text
        print(f"Is Full HTML? {is_html_doc}")
        print(f"Length: {len(r.text)}")
        
        if not is_html_doc:
            print("SUCCESS! Partial response received.")
            print(r.text[:200])
            break

debug_ajax_headers()
