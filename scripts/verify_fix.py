from universal_scraper_final import TIPPScraperFinal
import pandas as pd
import os
import shutil

# Setup
output_dir = "c:/Project-DQ/Validata/Scrapper/test_output"
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)

scraper = TIPPScraperFinal(output_dir=output_dir)

# Run strict test on the specific URL
print("--- RUNNING SCRAPER ON ID=217 ---")
scraper.process_single_url("https://tipp.gov.pk/index.php?r=site/display&id=217")

# Save Excel
scraper.save_excel()

# Verify
excel_path = os.path.join(output_dir, "metadata.xlsx")
if not os.path.exists(excel_path):
    print("FAILURE: metadata.xlsx not created.")
    exit(1)

df = pd.read_excel(excel_path)
print("\n--- METADATA CONTENTS ---")
print(df[['Entity_Title', 'External_Reference_URL']].head(20))

entities_to_check = [
    {"name": "Cross-Border Trade Regulatory Agencies", "expected_link": "ANY"}, # Intro Entity
    {"name": "Board of Investment", "expected_link": "https://invest.gov.pk"},
    {"name": "Ministry of Commerce", "expected_link": "commerce.gov.pk"},
    {"name": "Federal Board of Revenue", "expected_link": "fbr.gov.pk"}
]

print("\n--- ENTITY VERIFICATION ---")
for ent in entities_to_check:
    name = ent['name']
    expected = ent['expected_link']
    
    row = df[df['Entity_Title'].astype(str).str.contains(name, case=False, na=False)]
    if row.empty:
        print(f"FAILURE: Entity '{name}' not found.")
        continue
        
    link = str(row.iloc[0]['External_Reference_URL'])
    print(f"Entity: {name} | Link: {link}")
    
    if expected == "ANY":
        print("  -> MATCH (Found)")
    elif expected in link:
        print("  -> MATCH")
    else:
        print("  -> NO MATCH")
