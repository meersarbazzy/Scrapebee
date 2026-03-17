from universal_scraper_final import TIPPScraperFinal
from bs4 import BeautifulSoup
import re

# Mock the item
item = {
    'url': 'https://tipp.gov.pk/index.php?r=site/display&id=217',
    'path': ['Test', 'Debug'],
    'main_cat': 'Test',
    'sub_cat': 'Debug'
}

scraper = TIPPScraperFinal()

print(f"Fetching {item['url']}...")
# We can't easily call process_page because it relies on the driver being in a loop or similar.
# But we can assume the driver works since we have the dump. 
# Actually, let's just use the scraper's driver to fetch and then parse using the SAME logic as extract_entities.

scraper.driver.get(item['url'])
soup = BeautifulSoup(scraper.driver.page_source, 'html.parser')

print("Exacting entities (Debug Mode)...")

# Debugging Strategy 2 (Panels) logic specifically
main_content = soup.find('main') or soup.find(id='content') or soup.body
panels = main_content.find_all('div', class_=lambda c: c and 'panel' in c and 'panel-group' not in c)

print(f"Found {len(panels)} panels.")

for i, p in enumerate(panels):
    heading = p.find('div', class_='panel-heading') or p.find(class_='panel-title')
    title = heading.get_text(strip=True) if heading else "Untitled"
    print(f"\n--- Panel {i}: {title} ---")
    
    # Check all links
    all_links = p.find_all('a', href=True)
    print(f"  Total raw links found: {len(all_links)}")
    for a in all_links:
        print(f"    - href: '{a['href']}' Text: '{a.get_text(strip=True)}'")
        if 'tipp.gov.pk' not in a['href'] and 'localhost' not in a['href']:
            print("      [Candidate: External]")
        else:
            print("      [Ignored: Internal/Local]")

    # Check Regex
    body_div = p.find('div', class_='panel-body') or p
    body_text = body_div.get_text(separator='\n', strip=True)
    body_text = re.sub(r'\n\s*\n', '\n', body_text)
    body_text = re.sub(r' +', ' ', body_text)
    
    match = re.search(r'https?://[a-zA-Z0-9./\-_]+', body_text)
    if match:
        print(f"  Regex Match in Body: {match.group(0)}")
    else:
        print("  No Regex Match in Body.")

scraper.driver.quit()
