import os

file_path = "../scrape_top100.py"

try:
    with open(file_path, 'rb') as f:
        content = f.read()

    print(f"Original size: {len(content)} bytes")
    
    # Remove null bytes (common artifact of UTF-16 append)
    new_content = content.replace(b'\x00', b'')
    
    print(f"New size: {len(new_content)} bytes")
    
    with open(file_path, 'wb') as f:
        f.write(new_content)
        
    print("Fixed null bytes.")
    
except Exception as e:
    print(f"Error: {e}")
