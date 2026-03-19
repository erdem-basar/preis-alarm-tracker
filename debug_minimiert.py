"""
Test: Chrome minimiert (kein headless) auf Geizhals
Ausfuehren: python debug_minimiert.py
"""
import time, sys, re
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "selenium", "webdriver-manager"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager

URL = "https://geizhals.de/asus-rog-strix-xg27acdng-90lm0an0-b01970-a3328098.html"

def zaehle_shops(html):
    soup = BeautifulSoup(html, "html.parser")
    return len(soup.find_all(class_="offer"))

print("Test 1: Headless")
opts1 = Options()
opts1.add_argument("--headless=new")
opts1.add_argument("--window-size=1280,900")
opts1.add_argument("--lang=de-DE")
opts1.add_argument("--no-sandbox")
opts1.add_argument("--disable-gpu")
opts1.add_experimental_option("excludeSwitches", ["enable-logging"])
d1 = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts1)
d1.get(URL)
time.sleep(5)
for sel in ["#onetrust-accept-btn-handler","button[id*=accept]"]:
    try: d1.find_element(By.CSS_SELECTOR, sel).click(); time.sleep(1); break
    except: pass
time.sleep(3)
for i in range(10):
    r = d1.execute_script("""
        var btn = document.querySelector('.button--load-more-offers');
        if (btn && btn.textContent.trim() !== 'Keine weiteren Angebote') {
            btn.click(); return 'geklickt';
        } return 'kein button';
    """)
    if r == "kein button": break
    time.sleep(2.5)
h1 = d1.page_source
d1.quit()
print(f"  Headless: {zaehle_shops(h1)} Shops")

print("\nTest 2: Minimiert (kein headless)")
opts2 = Options()
opts2.add_argument("--window-size=1280,900")
opts2.add_argument("--lang=de-DE")
opts2.add_argument("--no-sandbox")
opts2.add_argument("--disable-gpu")
opts2.add_experimental_option("excludeSwitches", ["enable-logging"])
d2 = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts2)
d2.minimize_window()
d2.get(URL)
time.sleep(5)
for sel in ["#onetrust-accept-btn-handler","button[id*=accept]"]:
    try: d2.find_element(By.CSS_SELECTOR, sel).click(); time.sleep(1); break
    except: pass
time.sleep(3)
for i in range(10):
    r = d2.execute_script("""
        var btn = document.querySelector('.button--load-more-offers');
        if (btn && btn.textContent.trim() !== 'Keine weiteren Angebote') {
            btn.click(); return 'geklickt ' + document.querySelectorAll('.offer').length;
        } return 'kein button';
    """)
    print(f"  Klick {i+1}: {r}")
    if r == "kein button": break
    time.sleep(2.5)
h2 = d2.page_source
d2.quit()
print(f"  Minimiert: {zaehle_shops(h2)} Shops")

print("\nTest 3: Normal sichtbar")
opts3 = Options()
opts3.add_argument("--window-size=1280,900")
opts3.add_argument("--lang=de-DE")
opts3.add_argument("--no-sandbox")
opts3.add_experimental_option("excludeSwitches", ["enable-logging"])
d3 = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts3)
d3.get(URL)
time.sleep(5)
for sel in ["#onetrust-accept-btn-handler","button[id*=accept]"]:
    try: d3.find_element(By.CSS_SELECTOR, sel).click(); time.sleep(1); break
    except: pass
time.sleep(3)
for i in range(10):
    r = d3.execute_script("""
        var btn = document.querySelector('.button--load-more-offers');
        if (btn && btn.textContent.trim() !== 'Keine weiteren Angebote') {
            btn.click(); return 'geklickt ' + document.querySelectorAll('.offer').length;
        } return 'kein button';
    """)
    print(f"  Klick {i+1}: {r}")
    if r == "kein button": break
    time.sleep(2.5)
h3 = d3.page_source
d3.quit()
print(f"  Sichtbar: {zaehle_shops(h3)} Shops")

input("\nEnter zum Beenden...")
