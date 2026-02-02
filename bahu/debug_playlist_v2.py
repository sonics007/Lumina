import requests

def debug_v2():
    url = "http://127.0.0.1:5000/playlist.m3u8"
    try:
        print(f"Downloading {url}...")
        r = requests.get(url)
        content = r.text
        
        print(f"Total lines: {len(content.splitlines())}")
        
        print("\n--- FIRST 20 LINES ---")
        lines = content.splitlines()
        for i, line in enumerate(lines[:20]):
            print(f"{i+1}: {line}")
            
        print("\n--- CHECKING FOR BROKEN URLS ---")
        errors = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            if line.startswith("#"): continue
            
            # This is a URL line
            if not line.startswith("http://127.0.0.1:5000/watch?url="):
                print(f"ERROR on line {i+1}: URL does not start with prefix!")
                print(f"Line content: '{line}'")
                errors += 1
                if errors > 5:
                    print("Too many errors, stopping check.")
                    break
        
        if errors == 0:
            print("\nAll URL lines look correct.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_v2()
