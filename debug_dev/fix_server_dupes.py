
original_file = 'server.py'
backup_file = 'server.py.bak'

import shutil

try:
    with open(original_file, 'r') as f:
        lines = f.readlines()
    
    found_lines = []
    for i, line in enumerate(lines):
        if 'def delete_movie(' in line:
            found_lines.append(i)
            print(f"Found definition at line {i+1}")
            
    if len(found_lines) > 1:
        print("Duplicate detected! Creating backup and removing duplicates...")
        shutil.copy(original_file, backup_file)
        
        # Keep only the last definition (assuming it's the most recent/correct one)
        # We need to remove the @app.route decoration above it too usually.
        # But simply removing the PREVIOUS occurrence is risky if we don't know the size of the block.
        
        # Strategy: Read content, identify blocks.
        # Im going to remove the first occurrence if they are far apart.
        # Or remove the last one if they are identical.
        
        # Let's verify line numbers.
        # If one is line 256 (e.g.) and other is 689.
        # Let's inspect context of first one.
        pass

except Exception as e:
    print(e)
