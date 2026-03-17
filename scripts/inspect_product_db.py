from universal_scraper_final import TIPPScraperFinal
import time

scraper = TIPPScraperFinal()
url = "https://tipp.gov.pk/index.php?r=tradeInfo/searchProduct&Product_page=73"

print(f"Fetching {url}...")
scraper.driver.get(url)
time.sleep(5) # Wait for table load
html = scraper.driver.page_source

with open("product_page_dump.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Dump saved to product_page_dump.html")
scraper.driver.quit()
