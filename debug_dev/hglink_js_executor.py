import subprocess
import json
import re

def execute_js_with_node(js_code, mock_url):
    """Execute JavaScript using Node.js with proper mocking"""
    
    # Create a wrapper that properly mocks browser environment
    wrapper = f"""
const {{ JSDOM }} = require('jsdom');

// Create a minimal DOM
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {{
    url: '{mock_url}',
    referrer: 'https://film-adult.top/',
    contentType: 'text/html',
    includeNodeLocations: true,
    storageQuota: 10000000
}});

global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;

// Capture redirect
let redirectURL = null;
Object.defineProperty(window.location, 'href', {{
    get: function() {{ return '{mock_url}'; }},
    set: function(url) {{ 
        redirectURL = url;
        console.log('CAPTURED_URL:' + url);
    }}
}});

// Execute main.js
{js_code}

// Wait a bit for async operations
setTimeout(() => {{
    if (redirectURL) {{
        console.log('SUCCESS:' + redirectURL);
    }} else {{
        console.log('FAILED:No redirect captured');
    }}
    process.exit(0);
}}, 500);
"""
    
    try:
        # Try with jsdom
        result = subprocess.run(
            ['node', '-e', wrapper],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Parse output
        for line in result.stdout.split('\n'):
            if line.startswith('CAPTURED_URL:'):
                return line.split(':', 1)[1].strip()
            if line.startswith('SUCCESS:'):
                return line.split(':', 1)[1].strip()
                
    except subprocess.TimeoutExpired:
        print("Timeout - JS execution took too long")
    except FileNotFoundError:
        print("jsdom not installed, trying simpler approach...")
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def parse_main_js_static(js_content):
    """Static analysis of main.js to extract redirect logic"""
    
    print("Attempting static analysis of main.js...")
    
    # Extract the domain arrays
    dmca_match = re.search(r'const dmca=\[(.*?)\];', js_content, re.DOTALL)
    main_match = re.search(r'const main=\[(.*?)\];', js_content, re.DOTALL)
    rules_match = re.search(r'const rules=\[(.*?)\];', js_content, re.DOTALL)
    
    if not main_match:
        print("Could not find main array")
        return None
    
    # The main array contains obfuscated function calls that build URLs
    # Example: _0x4ae481('jhYH',...)+_0xd73fa7(0x79,'etxb',-0x5f,0xd0,0x22)+'om'
    
    # Try to find the final constructed domains
    # This is complex because the functions are obfuscated
    # Let's try a different approach - look for the finalURL construction
    
    final_url_match = re.search(r'const finalURL\s*=\s*([^;]+);', js_content)
    if final_url_match:
        construction = final_url_match.group(1)
        print(f"Final URL construction found: {construction[:200]}...")
        
        # It looks like: 'https://'+destination+url[...]+url[...]
        # Where destination comes from main[] or dmca[]
        
        # The selection logic is in the rules check
        # If URL matches rules, use main[], else dmca[]
        
        # For now, let's try to extract raw strings from main array
        main_content = main_match.group(1)
        
        # Find all string literals (between quotes)
        strings = re.findall(r"['\"]([^'\"]+)['\"]", main_content)
        print(f"\nFound {len(strings)} string fragments in main array")
        
        # Try to reconstruct domains by concatenating adjacent strings
        # This is a heuristic approach
        potential_domains = []
        for i in range(len(strings) - 1):
            combined = strings[i] + strings[i+1]
            if '.' in combined and len(combined) > 5:
                potential_domains.append(combined)
        
        if potential_domains:
            print(f"Potential domains: {potential_domains[:5]}")
            # Return the first one as a guess
            return f"https://{potential_domains[0]}/e/124fixrcqqxb"
    
    return None

if __name__ == "__main__":
    # Read main.js
    with open('hglink_main_full.js', 'r', encoding='utf-8') as f:
        main_js = f.read()
    
    print("=== HGLink JS Execution Attempt ===\n")
    
    # Try Node.js execution first
    print("1. Trying Node.js execution with mocking...")
    url = execute_js_with_node(main_js, 'https://hglink.to/e/124fixrcqqxb')
    
    if url:
        print(f"\n✓ SUCCESS! Redirect URL: {url}")
        with open('hglink_final_url.txt', 'w') as f:
            f.write(url)
        print("Saved to: hglink_final_url.txt")
    else:
        print("\n2. Falling back to static analysis...")
        url = parse_main_js_static(main_js)
        if url:
            print(f"\n✓ Extracted (heuristic): {url}")
            with open('hglink_final_url.txt', 'w') as f:
                f.write(url)
        else:
            print("\n✗ Could not extract URL")
            print("Recommendation: Use Selenium or implement full JS deobfuscator")
