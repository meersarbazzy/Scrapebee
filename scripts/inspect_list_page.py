from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

url = "https://tipp.gov.pk/index.php?r=site/display&id=217"

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled") 
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

# Try disabling eager loading just for the test to ensure full render
# options.add_argument("--page-load-strategy=eager") 

try:
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    # Stealth
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    print(f"Navigating to {url}...")
    driver.get(url)
    time.sleep(8) 
    
    title = driver.title
    print(f"Page Title: {title}")
    
    if "Blocked" in title:
        print("CRITICAL: Still Blocked!")
    else:
        print("SUCCESS: Looks like we got through.")
        
    with open("c:/Project-DQ/Validata/Scrapper/list_page_dump_v2.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Dump V2 saved.")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'driver' in locals():
        driver.quit()
