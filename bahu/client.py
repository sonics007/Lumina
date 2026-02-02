import requests
import re
import logging
from urllib.parse import urlparse, unquote

# Logging config
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class BahuClient:
    def __init__(self, email, password):
        self.base_url = "https://www.bahu.tv"
        self.login_url = f"{self.base_url}/authorize/login"
        self.email = email
        self.password = password
        self.session = requests.Session()
        
        # User-Agent like standard Chrome
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bahu.tv/",
            "Origin": "https://www.bahu.tv"
        })
        
    def login(self):
        """Performs login and saves cookies to session"""
        logging.info("Attempting login...")
        
        try:
            # 1. Get Login Page first to get CSRF token (if any)
            r = self.session.get(self.login_url)
            
            # Bahu seems to use simple form post, but let's check for csrf token
            # Often hidden input name="_csrf" or similar
            csrf_token = None
            csrf_match = re.search(r'name="(_csrf[^"]*)" value="([^"]*)"', r.text)
            
            payload = {
                "LoginForm[email]": self.email,
                "LoginForm[password]": self.password,
                "yt0": "Belépés"
            }
            
            if csrf_match:
                payload[csrf_match.group(1)] = csrf_match.group(2)
                
            # 2. Post Login
            r = self.session.post(self.login_url, data=payload)
            
            # Check success (redirect or text)
            if "Kijelentkezés" in r.text or r.url == self.base_url:
                logging.info("Login SUCCESS!")
                return True
            else:
                logging.error("Login FAILED. Check credentials.")
                # Debug failed login
                # print(r.text[:500]) 
                return False
                
        except Exception as e:
            logging.error(f"Login error: {e}")
            return False

    def get_video_url(self, page_url):
        """Fetches page and extracts transzfer.net mp4 link"""
        logging.info(f"Extracting: {page_url}")
        
        try:
            r = self.session.get(page_url)
            
            # Regex for transzfer.net URLs (MP4 or M3U8)
            # Pattern from analysis: http://m1.transzfer.net/.../movie_1597.mp4
            
            match = re.search(r'(https?://[^"\']*\.transzfer\.net/[^"\']*\.(?:mp4|m3u8))', r.text)
            
            if match:
                video_url = match.group(1)
                # Cleanup escaped slashes if JSON
                video_url = video_url.replace('\\/', '/')
                logging.info(f"FOUND: {video_url}")
                return video_url
            
            # Sometimes it might be inside a JSON variable 'file': '...'
            match_generic = re.search(r"file['\"]?:\s*['\"](https?://[^'\"]+)['\"]", r.text)
            if match_generic:
                url = match_generic.group(1)
                if 'transzfer' in url:
                    logging.info(f"FOUND (generic match): {url}")
                    return url

            logging.warning("No video URL found in page HTML.")
            return None
            
        except Exception as e:
            logging.error(f"Extraction error: {e}")
            return None

# Singleton instance setup for usage in server
# Replace with REAL credentials from analysis
# Email: krizo.ladislav@gmail.com
# Pass: @Radeberger2017@@

CLIENT = BahuClient("krizo.ladislav@gmail.com", "@Radeberger2017@@")

if __name__ == "__main__":
    # Test
    if CLIENT.login():
        # Test Movie
        # CLIENT.get_video_url("https://www.bahu.tv/film/gengszterzsaruk-pantera") 
        pass
