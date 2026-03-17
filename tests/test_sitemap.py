import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://tipp.gov.pk/index.php?r=site/display&id=9"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers, verify=False, timeout=20)
    print(f"Status Code: {response.status_code}")
    print(f"Snippet: {response.text[:500]}")
    if "SQLSTATE" in response.text:
        print("DB Error found on Sitemap too.")
    else:
        print("Sitemap seems clean.")
except Exception as e:
    print(f"Error: {e}")
