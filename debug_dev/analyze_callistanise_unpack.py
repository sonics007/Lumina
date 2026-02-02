
from curl_cffi import requests
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def unpack_js(p, a, c, k_str):
    keywords = k_str.split('|')
    encoded_a = int(a)
    encoded_c = int(c)
    
    def to_base36(n):
        if n == 0: return '0'
        res = ''
        vals = "0123456789abcdefghijklmnopqrstuvwxyz"
        while n > 0:
            res = vals[n % 36] + res
            n //= 36
        return res if res else '0'
        
    # Standard logic often differs slightly.
    # Let's use the logic from extractor.py which seems correct for HGLink.
    
    def to_base36_v2(n):
        if n < 10: return str(n)
        if n < 36: return chr(n - 10 + 97)
        if n < 62: return chr(n - 36 + 65)
        return str(n) # fallback

    # Actually, let's trust the loop logic
    unpacked = p
    for i in range(encoded_c - 1, -1, -1):
        if keywords[i]:
             # Re-implement base36 generation compatible with standard packer
             # Standard packer use: 0-9, a-z, A-Z?
             # But 'a' argument tells radix.
             
             # Simplified:
             token = ""
             t = i
             if t == 0: token = "0"
             else:
                 # Recursive logic from my extractor.py
                 def tb(n):
                     if n >= encoded_a:
                         return tb(n // encoded_a) + tb(n % encoded_a) # No, concatenation? 
                     # This recursion is tricky without seeing source.
                     
                     if n < 10: return str(n)
                     return chr(n - 10 + 97) # assuming lowercase for radix > 10
                 
                 # Let's rely on simple base36 lib logic?
                 # Or just generic replace.
                 
             # Let's assume standard base 36 (0-9a-z)
             token = ""
             temp = i
             if temp == 0: token = "0"
             else:
                 while temp:
                     temp, rem = divmod(temp, encoded_a) # Use radix 'a'
                     if rem < 10: token = str(rem) + token
                     else: token = chr(rem - 10 + 97) + token
             
             # Replace \btoken\b
             try:
                 unpacked = re.sub(r'\b' + re.escape(token) + r'\b', keywords[i], unpacked)
             except: pass
             
    return unpacked

url = "https://callistanise.com/file/vmbps7u3ghd0"
session = requests.Session(impersonate="chrome120")
r = session.get(url)

pattern = r"return p}\('(.*?)',(\d+),(\d+),'([^']+)'\.split\('\|'\)"
match = re.search(pattern, r.text)

if match:
    p, a, c, k = match.groups()
    print(f"Packed JS: a={a}, c={c}")
    try:
        unpacked = unpack_js(p, a, c, k)
        print("\n--- UNPACKED START ---")
        print(unpacked[:500])
        
        # Look for file: "..."
        m = re.search(r'file\s*:\s*["\']([^"\']+)["\']', unpacked)
        if m:
            print(f"\nFOUND FILE: {m.group(1)}")
    except Exception as e:
        print(f"Unpack error: {e}")
else:
    print("No Packed JS pattern.")
