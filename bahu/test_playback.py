import client

def test_extract():
    url = "https://www.bahu.tv/film/a-fantasztikus-4-es-elso-lepesek"
    print(f"Testing extraction for: {url}")
    
    # 1. Login
    if not client.CLIENT.login():
        print("Login failed")
        return

    # 2. Get Video URL
    try:
        video_url = client.CLIENT.get_video_url(url)
        print(f"Result: {video_url}")
        
        if video_url and "transzfer.net" in video_url:
            print("SUCCESS! Extraction works.")
        else:
            print("FAILURE: No valid video URL found.")
            
    except Exception as e:
        print(f"ERROR: {e}")

test_extract()
