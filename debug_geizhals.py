"""
Debug-Script: Zeigt was Selenium wirklich von Geizhals lädt.
Führe aus: python debug_geizhals.py
Ergebnis wird in debug_output.html gespeichert.
"""

import time, re, sys
from pathlib import Path

print("Starte Debug...")
print("Installiere Abhängigkeiten falls nötig...")

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

print(f"\nÖffne: {URL}")
print("Warte auf JavaScript... (kann 15-20 Sekunden dauern)")

driver = None
try:
    opts = Options()
    # KEIN headless - sichtbarer Browser für Debug
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--lang=de-DE")
    opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(30)
    driver.get(URL)

    print("Seite geladen. Warte 3 Sekunden...")
    time.sleep(3)

    # Cookie-Banner wegklicken
    for sel in ["#onetrust-accept-btn-handler", "button[id*=accept]",
                "button[class*=accept]", "[class*=consent] button"]:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, sel)
            btn.click()
            print(f"Cookie-Banner geklickt: {sel}")
            time.sleep(1)
            break
        except:
            pass

    print("Warte 8 Sekunden auf vollständiges Laden...")
    time.sleep(8)

    driver.execute_script("window.scrollTo(0, 600)")
    time.sleep(2)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    print(f"\nSeiten-Länge: {len(html)} Zeichen")
    print(f"Titel: {driver.title}")

    # Preise suchen
    preise = re.findall(r"(\d{1,4}[.,]\d{2})\s*€", html)
    print(f"\nGefundene Preismuster: {preise[:10]}")

    # Alle Klassen die 'offer' oder 'price' enthalten
    klassen = set()
    for el in soup.find_all(True):
        for c in el.get("class", []):
            if any(k in c.lower() for k in ["offer","price","merchant","shop","dealer"]):
                klassen.add(c)
    print(f"\nRelevante CSS-Klassen gefunden: {sorted(klassen)[:30]}")

    # Alle Links die nach Redirect/Shop aussehen
    redirect_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(k in href for k in ["redir","goto","/out/","affiliate","click"]):
            redirect_links.append(href[:80])
    print(f"\nRedirect-Links ({len(redirect_links)} gesamt): {redirect_links[:5]}")

    # HTML speichern
    out = Path("debug_output.html")
    out.write_text(html, encoding="utf-8")
    print(f"\nVollständiges HTML gespeichert in: {out.absolute()}")
    print("Öffne diese Datei im Browser um zu sehen was Selenium geladen hat.")

    # Warte damit du den Browser sehen kannst
    print("\nBrowser bleibt 10 Sekunden offen...")
    time.sleep(10)

except Exception as e:
    print(f"\nFEHLER: {e}")
    import traceback
    traceback.print_exc()
finally:
    if driver:
        driver.quit()

print("\nDebug abgeschlossen.")
input("Enter drücken zum Beenden...")
