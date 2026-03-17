from bs4 import BeautifulSoup
import re
import os

# 1. Load the dump
dump_path = "c:/Project-DQ/Validata/Scrapper/list_page_dump_v2.html"
with open(dump_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, 'html.parser')

print("Loaded dump.")

# 2. Mimic Strategy 2 (Panels)
main_content = soup.find('main') or soup.find(id='content') or soup.body
panels = main_content.find_all('div', class_=lambda c: c and 'panel' in c and 'panel-group' not in c)
print(f"Found {len(panels)} panels.")

for i, p in enumerate(panels):
    heading = p.find('div', class_='panel-heading') or p.find(class_='panel-title')
    title = heading.get_text(strip=True) if heading else "Untitled"
    
    # Limit to first 20 for brevity, or search for known ones
    if "Revenue" in title or "Commerce" in title or "Investment" in title:
        print(f"\n--- Panel {i}: {title} ---")
    else:
        continue # Skip others for now to keep output clean
    print(f"  Classes: {p.get('class')}")
    print(f"  Style: {p.get('style')}")
    print(f"  Hidden attribute: {p.get('hidden')}")
    
    # Logic from Universal Scraper Final
    link = None
    all_links = p.find_all('a', href=True)
    for a in all_links:
        href = a['href']
        print(f"  Found link: {href}")
        if href.startswith('#') or href.startswith('javascript'):
            continue
        
        if 'tipp.gov.pk' not in href and 'localhost' not in href:
            link = href
            print("    -> Accepted as External")
            break 
    
    if not link:
        print("  No external link found in first pass.")
        # Try any non-collpas
        for a in all_links:
             href = a['href']
             if not href.startswith('#') and 'collapse' not in str(a):
                 link = href
                 print(f"    -> Fallback Accepted: {href}")
                 break

    # Regex
    body_div = p.find('div', class_='panel-body') or p
    body_text = body_div.get_text(separator='\n', strip=True)
    body_text = re.sub(r'\n\s*\n', '\n', body_text)
    
    match = re.search(r'https?://[a-zA-Z0-9./\-_]+', body_text)
    if match:
        print(f"  Regex Match: {match.group(0)}")
    
    print(f"  FINAL LINK DECISION: {link}")
