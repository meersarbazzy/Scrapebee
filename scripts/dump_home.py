import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://tipp.gov.pk/"
try:
    response = requests.get(url, verify=False, timeout=20)
    with open("c:/Project-DQ/Validata/Scrapper/homepage_dump.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("Dumped homepage.")
except Exception as e:
    print(f"Error: {e}")
