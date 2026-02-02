import requests

def debug():
    url = "http://127.0.0.1:5000/playlist.m3u8"
    try:
        print(f"Downloading {url}...")
        r = requests.get(url)
        print(f"Status: {r.status_code}")
        print(f"Headers: {r.headers}")
        content = r.content
        print(f"Total size: {len(content)} bytes")
        
        # Save locally
        with open("local_playlist.m3u8", "wb") as f:
            f.write(content)
        print("Saved to 'local_playlist.m3u8'. Try opening this file in VLC.")
        
        # Analyze byte 509
        if len(content) > 509:
            start = max(0, 509 - 50)
            end = min(len(content), 509 + 50)
            print(f"\n--- Content around byte 509 ({start}-{end}) ---")
            print(content[start:end])
            try:
                print(content[start:end].decode('utf-8'))
            except:
                print("(Cannot decode as utf-8)")
        else:
            print("Content is too short!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug()
