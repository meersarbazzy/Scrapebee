import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://tipp.gov.pk/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers, verify=False, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Content Length: {len(response.text)}")
    print("Snippet:", response.text[:200])
except Exception as e:
    print(f"Error: {e}")
