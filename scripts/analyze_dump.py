from bs4 import BeautifulSoup

with open("c:/Project-DQ/Validata/Scrapper/list_page_dump_v2.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, 'html.parser')

# Remove scripts/styles
for s in soup(['script', 'style']):
    s.decompose()

text = soup.get_text(separator='\n', strip=True)
print(text[:2000]) # First 2000 chars
print("---")
# Look for specific keywords
# Find context around the link itself
idx = text.find("invest.gov.pk")
if idx != -1:
    print("\n--- Context near URL ---")
    print(text[idx-100:idx+100])
else:
    print("URL 'invest.gov.pk' not found in text dump.")
