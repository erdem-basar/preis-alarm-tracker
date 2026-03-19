"""
Debug: Testet ob Selenium den "Mehr Angebote" Button auf Geizhals klickt.
Ausfuehren: python debug_mehr_angebote.py
"""
import time, re, sys

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "selenium", "webdriver-manager", "beautifulsoup4"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    from bs4 import BeautifulSoup

URL = "https://geizhals.de/asus-rog-strix-xg27acdng-90lm0an0-b01970-a3328098.html"

def zaehle_shops(html):
    soup = BeautifulSoup(html, "html.parser")
    offers = soup.find_all(class_="offer")
    return len(offers)

print(f"Oeffne: {URL}")
print("Sichtbarer Browser (kein headless) fuer bessere Ergebnisse...\n")

opts = Options()
# KEIN headless - normaler Browser
opts.add_argument("--window-size=1280,900")
opts.add_argument("--lang=de-DE")
opts.add_experimental_option("excludeSwitches", ["enable-logging"])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

try:
    driver.get(URL)
    print("Warte 3s auf Laden...")
    time.sleep(3)

    # Cookie-Banner
    for sel in ["#onetrust-accept-btn-handler", "button[id*=accept]", ".button--accept"]:
        try:
            driver.find_element(By.CSS_SELECTOR, sel).click()
            print(f"Cookie-Banner geklickt: {sel}")
            time.sleep(1)
            break
        except: pass

    time.sleep(3)
    shops_vorher = zaehle_shops(driver.page_source)
    print(f"Shops vor Klick: {shops_vorher}")

    # Button suchen
    for i in range(15):
        # Erst scrollen
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)

        # Button per JS pruefen
        btn_info = driver.execute_script("""
            var btn = document.querySelector('.button--load-more-offers');
            if (btn) {
                return {
                    exists: true,
                    visible: btn.offsetParent !== null,
                    text: btn.textContent.trim(),
                    disabled: btn.disabled
                };
            }
            return {exists: false};
        """)
        print(f"\nKlick {i+1}: Button = {btn_info}")

        if not btn_info.get("exists"):
            print("Button nicht mehr vorhanden - alle Shops geladen!")
            break

        # Klicken per JS
        result = driver.execute_script("""
            var btn = document.querySelector('.button--load-more-offers');
            if (btn && !btn.disabled) {
                btn.scrollIntoView({block: 'center'});
                btn.click();
                return 'geklickt';
            }
            return 'nicht klickbar';
        """)
        print(f"  Klick-Ergebnis: {result}")
        time.sleep(3)

        shops_jetzt = zaehle_shops(driver.page_source)
        print(f"  Shops jetzt: {shops_jetzt}")

        if shops_jetzt <= shops_vorher:
            print("  Keine neuen Shops - versuche anders...")
            # Versuch 2: Direktklick
            try:
                btn = driver.find_element(By.CSS_SELECTOR, ".button--load-more-offers")
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(3)
                shops_jetzt2 = zaehle_shops(driver.page_source)
                print(f"  Nach direktem Klick: {shops_jetzt2} Shops")
            except Exception as e:
                print(f"  Direktklick fehlgeschlagen: {e}")
            break
        shops_vorher = shops_jetzt

    print(f"\n=== ERGEBNIS ===")
    print(f"Shops gefunden: {zaehle_shops(driver.page_source)}")

    # HTML speichern
    with open("debug_mehr_output.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("HTML gespeichert: debug_mehr_output.html")

    print("\nBrowser bleibt 15s offen zum Anschauen...")
    time.sleep(15)

except Exception as e:
    print(f"FEHLER: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()

input("\nEnter zum Beenden...")
