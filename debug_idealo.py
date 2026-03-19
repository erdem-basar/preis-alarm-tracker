"""
Debug: Testet Idealo-Seite mit Selenium.
Ausfuehren: python debug_idealo.py
"""
import time, sys, re
from pathlib import Path

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

URL = "https://www.idealo.de/preisvergleich/OffersOfProduct/203766386_-tempest-gz2711-cooler-master.html"

print(f"Oeffne: {URL}")
print("Sichtbarer Browser...\n")

opts = Options()
opts.add_argument("--window-size=1280,900")
opts.add_argument("--lang=de-DE")
opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
opts.add_experimental_option("excludeSwitches", ["enable-logging"])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

try:
    driver.get(URL)
    print("Warte 4s...")
    time.sleep(4)

    # Cookie-Banner
    for sel in ["#onetrust-accept-btn-handler", "button[id*=accept]",
                "button[class*=accept]", "[class*=consent] button"]:
        try:
            driver.find_element(By.CSS_SELECTOR, sel).click()
            print(f"Cookie geklickt: {sel}")
            time.sleep(1)
            break
        except: pass

    print("Warte 5s auf vollstaendiges Laden...")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 800)")
    time.sleep(2)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    print(f"Seiten-Laenge: {len(html)}")
    print(f"Titel: {driver.title}")

    # JSON-LD
    import json
    print("\n=== JSON-LD ===")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            txt = json.dumps(data, ensure_ascii=False)[:400]
            if "price" in txt.lower() or "offer" in txt.lower():
                print(txt)
        except: pass

    # Preise
    preise = re.findall(r"(\d{1,4}[.,]\d{2})\s*€", html)
    print(f"\nPreise gefunden: {preise[:10]}")

    # Relevante CSS-Klassen
    klassen = set()
    for el in soup.find_all(True):
        for c in el.get("class", []):
            if any(k in c.lower() for k in ["offer","price","shop","merchant","dealer"]):
                klassen.add(c)
    print(f"\nRelevante Klassen: {sorted(klassen)[:30]}")

    # Shop-Links
    print("\n=== Shop-Links ===")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if any(k in href for k in ["redir","goto","click","out","shop"]) and text and len(text) < 50:
            print(f"  '{text}' -> {href[:80]}")

    # HTML speichern
    out = Path("debug_idealo_output.html")
    out.write_text(html, encoding="utf-8")
    print(f"\nHTML gespeichert: {out.absolute()}")

    print("\nBrowser bleibt 10s offen...")
    time.sleep(10)

except Exception as e:
    print(f"FEHLER: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()

input("\nEnter zum Beenden...")
