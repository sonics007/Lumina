import requests

def test_watch():
    # Zoberiem priklad z playlistu
    # http://127.0.0.1:5000/watch?url=https://www.bahu.tv/film/a-galaxis-orzoi-unnepi-kulonkiadas
    
    # Skusim nejaky realny film co tam urcite je, napr Shazam
    target_url = "https://www.bahu.tv/film/shazam-az-istenek-haragja"
    watch_url = f"http://127.0.0.1:5000/watch?url={target_url}"
    
    print(f"Testing WATCH URL: {watch_url}")
    print("Sending request... (this might take 10-20 seconds for Selenium)")
    
    try:
        # allow_redirects=False aby sme videli 302 presmerovanie
        r = requests.get(watch_url, allow_redirects=False, timeout=30)
        print(f"Status Code: {r.status_code}")
        print(f"Headers: {r.headers}")
        
        if r.status_code == 302:
            print(f"SUCCESS! Redirect Location: {r.headers.get('Location')}")
        else:
            print("FAILED. Did not redirect.")
            print(r.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_watch()
