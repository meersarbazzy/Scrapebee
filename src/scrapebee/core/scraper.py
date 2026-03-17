import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathvalidate import sanitize_filename
import time
from collections import deque

# Configuration
START_URL = "https://tipp.gov.pk/"
OUTPUT_DIR = "output"
DELAY = 1.0  # Seconds to wait between requests to be polite

# Set of visited URLs to avoid loops
visited_urls = set()
# Queue for BFS crawling
queue = deque([START_URL])
# Domain to constrain crawling
TARGET_DOMAIN = urlparse(START_URL).netloc

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def is_internal_link(url):
    try:
        parsed = urlparse(url)
        # Check if netloc ends with target domain (handles www and other subdomains)
        return parsed.netloc == '' or parsed.netloc.endswith(TARGET_DOMAIN) or parsed.netloc == f"www.{TARGET_DOMAIN}"
    except:
        return False

import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_page_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def save_content(url, soup):
    try:
        # Extract title
        title = soup.title.string.strip() if soup.title else "No Title"
        sanitized_title = sanitize_filename(title)
        
        # If title is empty/invalid after sanitization, use part of URL
        if not sanitized_title:
            sanitized_title = sanitize_filename(urlparse(url).path.strip('/').replace('/', '_'))
            if not sanitized_title:
                 sanitized_title = "index"

        # Extract text content
        # Remove unwanted tags
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
        
        text_content = soup.get_text(separator='\n\n')
        
        # Clean up excessive whitespace
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = '\n'.join(chunk for chunk in chunks if chunk)

        filename = f"{sanitized_title}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Handle duplicates by appending counter if needed (simple approach: overwrite or ignore, 
        # but here we might overwrite pages with same title which is common. 
        # Let's add a safety check.
        if os.path.exists(filepath):
            timestamp = int(time.time())
            filename = f"{sanitized_title}_{timestamp}.txt"
            filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Source URL: {url}\n\n")
            f.write(clean_text)
        
        print(f"Saved: {filename}")
        return True

    except Exception as e:
        print(f"Error saving content for {url}: {e}")
        return False

def crawl():
    ensure_output_dir()
    
    print(f"Starting crawl at {START_URL}")
    print(f"Input Target Domain: {TARGET_DOMAIN}")

    while queue:
        current_url = queue.popleft()
        
        if current_url in visited_urls:
            continue
        
        print(f"Visiting: {current_url}")
        html = get_page_content(current_url)
        visited_urls.add(current_url)
        
        if not html:
            continue

        soup = BeautifulSoup(html, 'html.parser')
        
        # Save content
        save_content(current_url, soup)

        # Find new links
        for link in soup.find_all('a', href=True):
            raw_href = link['href']
            # Join relative URLs
            absolute_url = urljoin(current_url, raw_href)
            
            # Normalize URL (remove fragments)
            parsed_abs = urlparse(absolute_url)
            normalized_url = parsed_abs.scheme + "://" + parsed_abs.netloc + parsed_abs.path
            if parsed_abs.query:
                normalized_url += "?" + parsed_abs.query
            
            if is_internal_link(normalized_url):
                 if normalized_url not in visited_urls and normalized_url not in queue:
                    # Basic filter to avoid non-html resources
                    if not any(normalized_url.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.zip', '.docx', '.css', '.js']):
                         queue.append(normalized_url)
                 else:
                    pass # duplicate
            else:
                 pass # external/rejected

        time.sleep(DELAY) # Be polite

if __name__ == "__main__":
    crawl()
