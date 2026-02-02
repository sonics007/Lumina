#!/usr/bin/env python3
"""
Test cavanhabg.com extractor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extractor import get_stream_url

# Test URL from movies_db.json
test_url = "https://cavanhabg.com/s4bp3dcmjk1y"

print(f"Testing cavanhabg extractor...")
print(f"URL: {test_url}")
print("="*70)

try:
    result = get_stream_url(test_url)
    if result:
        stream_url, headers = result
        print(f"\n✅ SUCCESS!")
        print(f"Stream URL: {stream_url}")
        print(f"Headers: {headers}")
    else:
        print(f"\n❌ FAILED: No stream URL returned")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
