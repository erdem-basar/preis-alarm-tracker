"""
Debug: Testet ob Geizhals-Redirects aufloesbar sind.
Ausfuehren: python debug_redirect.py
"""
import time, sys

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "selenium", "webdriver-manager"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager

# Echte Redirect-URLs von deiner Geizhals-Seite
TEST_URLS = [
    "https://geizhals.de/redir/AwAAANaBjJxLyDV2-nhf-DGYLDbcgDDZc-q6TvSPw6osohOF_usiuftGXxhsBfYJ7qZqU-7zzA",
    "https://geizhals.de/redir/AwAAAJHcN947jiEHLTS-ZKsPbQ1lWze3uKaTl6OpYnExpHdcpRLpHvmTeLeSqQFlJfV4s3zRaS",
    "https://geizhals.de/redir/AwAAAFfCuEQjDAlttHJTIBrP2I0R-kYmjWlHuHFG0hjGn63FG86xZ9z0MQKMMZNw7ShsYWUodS",
]

print("Teste 3 Methoden zum Auflösen von Geizhals-Redirects:\n")

for methode in ["headless", "sichtbar_off_screen", "sichtbar_normal"]:
    print(f"=== Methode: {methode} ===")
    for url in TEST_URLS[:2]:
        driver = None
        try:
            opts = Options()
            if methode == "headless":
                opts.add_argument("--headless=new")
            elif methode == "sichtbar_off_screen":
                opts.add_argument("--window-position=-32000,0")
            # normal = kein extra argument

            opts.add_argument("--window-size=1280,900")
            opts.add_argument("--no-sandbox")
            opts.add_argument("--disable-dev-shm-usage")
            opts.add_argument("--disable-gpu")
            opts.add_argument("--lang=de-DE")
            opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            opts.add_experimental_option("excludeSwitches", ["enable-logging"])

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=opts)
            driver.set_page_load_timeout(20)

            print(f"  URL: {url[:60]}...")
            driver.get(url)
            time.sleep(4)

            final = driver.current_url
            title = driver.title[:50] if driver.title else "–"
            print(f"  Final URL: {final[:80]}")
            print(f"  Titel: {title}")

            if "geizhals.de" not in final and "geizhals.at" not in final:
                print(f"  ✅ AUFGELÖST!")
            else:
                print(f"  ❌ Noch auf Geizhals")
            print()
        except Exception as e:
            print(f"  FEHLER: {e}\n")
        finally:
            if driver:
                try: driver.quit()
                except: pass

input("Enter zum Beenden...")
