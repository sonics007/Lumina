
    # Success path continues here (after break from loop)
    # Rewrite Logic
    try:
        new_lines = []
        import re
        uri_pattern = re.compile(r'URI="([^"]+)"')
        
        def replace_uri(match):
            full = urljoin(base_url, match.group(1))
            return f'URI="http://127.0.0.1:{PORT}/segment?url={quote(full)}&ref={quote(referer)}"'
            
        for line in content.split('\n'):
            line = line.strip()
            if not line: continue
            if line.startswith('#'):
                if 'URI="' in line:
                    line = uri_pattern.sub(replace_uri, line)
                new_lines.append(line)
            else:
                full = urljoin(base_url, line)
                proxy = f"http://127.0.0.1:{PORT}/segment?url={quote(full)}&ref={quote(referer)}"
                new_lines.append(proxy)
                
        resp = Response('\n'.join(new_lines), mimetype='application/vnd.apple.mpegurl')
        resp.headers['Cache-Control'] = 'no-cache'
        return resp

    except Exception as e:
        print(f"ERROR in /watch rewrite: {e}")
        import traceback
        traceback.print_exc()
        return f"Fetch/Rewrite Error: {e}", 502
