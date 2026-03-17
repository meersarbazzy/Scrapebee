import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

url = "https://tipp.gov.pk/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
}

try:
    print(f"Fetching {url}...")
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    print(f"Status: {r.status_code}")
    soup = BeautifulSoup(r.text, 'html.parser')
    
    links = soup.find_all('a', href=True)
    print(f"Total links with href: {len(links)}")
    
    print("\n--- First 50 Links ---")
    for i, link in enumerate(links[:50]):
        print(f"{i}: {link['href']}")

except Exception as e:
    print(f"Error: {e}")
