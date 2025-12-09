from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import os

# --- Configuration for Docker ---
# We map this path to the host volume
DOWNLOAD_DIR = "/app/output"
URL = "https://palert.earth.sinica.edu.tw/database"

def setup_driver():
    """Configures and initializes the Chrome WebDriver for Docker."""
    
    # 1. Ensure download directory exists
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        print(f"Created download directory: {DOWNLOAD_DIR}")

    options = webdriver.ChromeOptions()
    # DOCKER CONFIGURATION:
    options.binary_location = "/usr/bin/chromium"  # Use system browser
    options.add_argument('--headless=new')         # Must be headless in Docker
    options.add_argument('--no-sandbox')           # Required for root user in Docker
    options.add_argument('--disable-dev-shm-usage') # Prevents shared memory crashes
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    try:
        # Use the system-installed driver from the Dockerfile
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print("\n❌ DRIVER ERROR: Could not start Chrome.")
        print(f"Details: {e}")
        raise e
    return driver

def download_data():
    """Navigates to the page, clicks the button, and waits for the file."""
    driver = setup_driver()
    
    try:
        print(f"Navigating to {URL}...")
        driver.get(URL)

        # 1. Wait for the button container to be visible first
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "downloadBtns"))
        )

        print("Container found. Searching for download button...")
        
        # 2. TARGETED SELECTOR (Your working logic):
        try:
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.downloadBtns button[title='下載表格資料']"))
            )
            print("Button found via CSS Selector.")
        except:
            # Fallback
            print("CSS failed, trying XPath...")
            download_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '下載表格資料')]"))
            )

        print("Initiating click...")
        # JavaScript click is safest for headless browsers
        driver.execute_script("arguments[0].click();", download_button)

        # 3. Wait for file download
        timeout = 60
        start_time = time.time()
        file_downloaded = False

        print("Waiting for file...")
        while (time.time() - start_time) < timeout:
            if os.path.exists(DOWNLOAD_DIR):
                downloaded_files = os.listdir(DOWNLOAD_DIR)
                # Check for non-temporary files
                if any(not f.endswith(('.crdownload', '.tmp')) for f in downloaded_files):
                    downloaded_file = next(f for f in downloaded_files if not f.endswith(('.crdownload', '.tmp')))
                    print(f"✅ Download successful! File saved: {os.path.join(DOWNLOAD_DIR, downloaded_file)}")
                    file_downloaded = True
                    break
            time.sleep(2)
        
        if not file_downloaded:
            print("❌ Download failed or timed out.")

    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    download_data()
