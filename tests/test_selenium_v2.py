from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

print("Starting Selenium V2 Test...", flush=True)

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# Eager strategy: Wait for DOMContentLoaded, not full load
options.add_argument("--page-load-strategy=eager") 
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument('--blink-settings=imagesEnabled=false') # Block images
options.add_argument("--ignore-certificate-errors")

# Anti-detection
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

try:
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Mask webdriver
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    print("Driver setup. Navigating...", flush=True)
    driver.set_page_load_timeout(30)
    
    try:
        driver.get("https://tipp.gov.pk/")
    except Exception as e:
        print(f"Navigation Timeout/Error (Expected with 'eager'?): {e}")

    print("Navigation command returned. Checking title...", flush=True)
    print(f"Title: {driver.title}")
    
    # Wait for menu
    print("Waiting for menu...", flush=True)
    try:
        # Check for nav id="A" (seen in dump) or navbar-nav
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "navbar-nav"))
        )
        print("Menu container found!")
        
        # Check for LIs
        nav = driver.find_element(By.CLASS_NAME, "navbar-nav")
        lis = nav.find_elements(By.TAG_NAME, "li")
        print(f"Found {len(lis)} list items in menu.")
        
        for li in lis[:3]:
            print(f" - {li.text}")
            
    except Exception as e:
        print(f"Menu detection failed: {e}")
        print("Dumping Page Source...")
        with open("c:/Project-DQ/Validata/Scrapper/selenium_dump.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

    driver.quit()
    print("Done.", flush=True)

except Exception as e:
    import traceback
    traceback.print_exc()
