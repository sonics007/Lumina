
from curl_cffi import requests
from bs4 import BeautifulSoup
import sys

sys.stdout.reconfigure(encoding='utf-8')
url = "https://uiiumovie.com/"

print(f"Analyzing Home: {url}")
session = requests.Session(impersonate="chrome120")
r = session.get(url, timeout=15)
soup = BeautifulSoup(r.text, 'html.parser')

# Find movies
articles = soup.select('article.post') # Generic WP
if not articles:
    articles = soup.select('.item') # Generic theme
if not articles:
    articles = soup.select('div.post')

print(f"Found {len(articles)} movie cards.")
if articles:
    first = articles[0]
    # print(f"First Card HTML: {str(first)[:300]}...")
    
    # Try extract link, title, img
    a_tag = first.find('a')
    link = a_tag['href'] if a_tag else "No link"
    
    img_tag = first.find('img')
    img = img_tag['src'] if img_tag else "No img"
    if not img and img_tag and 'data-src' in img_tag.attrs:
        img = img_tag['data-src']
        
    title = first.get_text(strip=True)
    if not title and a_tag:
        title = a_tag.get('title')
        
    print(f"Sample: {title[:50]} | {link} | {img}")

# Find pagination
# Look for next page link
next_page = soup.find('a', class_='next')
if next_page:
    print(f"Next Page Link: {next_page['href']}")
else:
    print("No 'next' class link found.")
    
# Look for page numbers
pages = soup.select('a.page-numbers')
if pages:
    print(f"Page numbers found: {len(pages)}")
    last_page = pages[-2].get_text() if len(pages) > 1 else '?'
    print(f"Estimate last page: {last_page}")

