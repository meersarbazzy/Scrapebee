from bs4 import BeautifulSoup

dump_path = "c:/Project-DQ/Validata/Scrapper/list_page_dump_v2.html"
with open(dump_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, 'html.parser')

print("Loaded dump.")
main_content = soup.find('main') or soup.find(id='content') or soup.body

# Find whatever is before the first panel
first_panel = main_content.find('div', class_=lambda c: c and 'panel' in c)

if first_panel:
    print(f"First Panel starts at: {first_panel.name} class={first_panel.get('class')}")
    
    # Iterate ALL previous siblings
    pre_content = []
    curr = first_panel.previous_sibling
    while curr:
        txt = curr.get_text(strip=True) if curr.name else str(curr).strip()
        if txt: 
            tag = curr.name if curr.name else "TextNode"
            pre_content.insert(0, f"[{tag}] {txt[:100]}...") # Prepend since we go backwards
        curr = curr.previous_sibling
        
    print("\n--- CONTENT BEFORE FIRST PANEL ---")
    for line in pre_content:
        print(line)
else:
    print("No panels found.")
