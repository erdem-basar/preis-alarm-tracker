"""
Debug: Tests PriceSpy 'Show more prices' button.
Run: python debug_pricespy_btn.py
"""
import time, sys, re
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "selenium", "webdriver-manager", "beautifulsoup4"])

URL = "https://pricespy.co.uk/product.php?p=14969875"

def count_shops(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return len(soup.find_all(class_="pj-ui-price-row"))

print(f"Opening: {URL}\n")

opts = Options()
# Visible browser
opts.add_argument("--window-size=1280,900")
opts.add_argument("--lang=en-GB")
opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
opts.add_experimental_option("excludeSwitches", ["enable-logging"])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

try:
    driver.get(URL)
    print("Waiting 5s for load...")
    time.sleep(5)

    # Cookie banner
    for sel in ["#onetrust-accept-btn-handler", "button[id*=accept]",
                "button[class*=accept]", "[class*=consent] button"]:
        try:
            driver.find_element(By.CSS_SELECTOR, sel).click()
            print(f"Cookie clicked: {sel}")
            time.sleep(1)
            break
        except: pass

    time.sleep(3)
    print(f"Shops before: {count_shops(driver)}")

    # Scroll to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)

    # Find all buttons and print them
    print("\n=== All buttons on page ===")
    btns = driver.find_elements(By.TAG_NAME, "button")
    for b in btns:
        try:
            txt = b.text.strip()
            cls = b.get_attribute("class") or ""
            if txt:
                print(f"  '{txt[:60]}' | class: {cls[:60]}")
        except: pass

    # Try to find and click the button
    print("\n=== Trying to click 'Show more prices' ===")

    # Method 1: By text content via JS
    result = driver.execute_script("""
        var allBtns = Array.from(document.querySelectorAll('button'));
        var found = allBtns.filter(b => b.innerText && b.innerText.includes('more price'));
        if (found.length > 0) {
            return 'Found ' + found.length + ' button(s): ' + found.map(b => b.innerText.trim()).join(', ');
        }
        return 'Not found';
    """)
    print(f"Method 1 (JS search): {result}")

    # Method 2: Try clicking
    result2 = driver.execute_script("""
        var allBtns = Array.from(document.querySelectorAll('button'));
        var btn = allBtns.find(b => b.innerText && b.innerText.toLowerCase().includes('more price'));
        if (btn) {
            btn.scrollIntoView({block: 'center', behavior: 'smooth'});
            return {found: true, text: btn.innerText.trim(), visible: btn.offsetParent !== null,
                    disabled: btn.disabled, rect: JSON.stringify(btn.getBoundingClientRect())};
        }
        return {found: false};
    """)
    print(f"Method 2 (button info): {result2}")

    if result2 and result2.get("found"):
        time.sleep(1)
        # Try selenium click
        try:
            btn_el = driver.find_element(By.XPATH, "//button[contains(., 'more price')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_el)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", btn_el)
            print("  ✅ Selenium JS click executed")
            time.sleep(3)
            print(f"  Shops after JS click: {count_shops(driver)}")
        except Exception as e:
            print(f"  ❌ Selenium click failed: {e}")

        # Try direct click
        try:
            btn_el2 = driver.find_element(By.XPATH, "//button[contains(., 'more price')]")
            btn_el2.click()
            print("  ✅ Direct click executed")
            time.sleep(3)
            print(f"  Shops after direct click: {count_shops(driver)}")
        except Exception as e:
            print(f"  ❌ Direct click failed: {e}")

    # Save HTML after attempts
    out = Path("debug_pricespy_btn_output.html")
    out.write_text(driver.page_source, encoding="utf-8")
    print(f"\nFinal shops: {count_shops(driver)}")
    print(f"HTML saved: {out.absolute()}")

    print("\nBrowser stays open 15s — check if button was clicked...")
    time.sleep(15)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()

input("\nPress Enter to exit...")
