import requests
import urllib3
urllib3.disable_warnings()

try:
    print("Testing connection to google.com...")
    r = requests.get("https://www.google.com", timeout=5, verify=False)
    print(f"Status: {r.status_code}")
except Exception as e:
    print(f"Google failed: {e}")

try:
    print("\nTesting connection to tipp.gov.pk...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    r = requests.get("https://tipp.gov.pk/", headers=headers, timeout=10, verify=False)
    print(f"Status: {r.status_code}")
except Exception as e:
    print(f"Tipp failed: {e}")
