from bs4 import BeautifulSoup

file_path = "c:/Project-DQ/Validata/Scrapper/list_page_dump_v2.html"
with open(file_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

# Find the "Chambers of Commerce" text
# Note: analyze_dump showed "Chambers of Commerce & Industry"
targets = soup.find_all(string=lambda t: "Board of Investment" in t if t else False)

print(f"Found {len(targets)} occurrences.")

for i, t in enumerate(targets):
    parent = t.parent
    print(f"\n--- Occurrence {i+1} ---")
    print(f"Text: {t.strip()}")
    print(f"Parent Tag: <{parent.name} class='{parent.get('class')}'>")
    
    # Grandparent
    grand = parent.parent
    if grand:
        print(f"Grandparent Tag: <{grand.name} class='{grand.get('class')}'>")
    
    # Siblings?
    print("Next Siblings:")
    for sib in parent.next_siblings:
        if sib.name:
            print(f"  <{sib.name}> Text: {sib.get_text(strip=True)[:50]}...")
            if sib.name == 'a':
                print(f"    LINK: {sib.get('href')}")
        elif sib.strip():
            print(f"  [Text]: {sib.strip()[:50]}...")

# Also check for repeating divs structure
print("\n--- Checking DIV structure ---")
main = soup.find('main') or soup.find(id='content') or soup.body
if main:
    divs = main.find_all('div', recursive=True)
    classes = {}
    for d in divs:
        c = ".".join(d.get('class', []))
        classes[c] = classes.get(c, 0) + 1
    
    # Print common classes
    for c, count in classes.items():
        if count > 3:
            print(f"Class '{c}': {count} times")
