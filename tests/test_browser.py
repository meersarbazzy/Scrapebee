from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time

print("Starting test...")
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# options.add_argument("--headless") 
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--page-load-strategy=none")

try:
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    print("Driver created.")
    
    driver.get("https://www.google.com")
    print("Navigated to Google.")
    time.sleep(5)
    print("Title:", driver.title)
    driver.quit()
    print("Done.")
except Exception as e:
    import traceback
    traceback.print_exc()
