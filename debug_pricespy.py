"""
Debug: Tests PriceSpy UK with Selenium.
Run: python debug_pricespy.py
"""
import time, sys, re, json
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

URL = "https://pricespy.co.uk/product.php?p=14969875"

print(f"Opening: {URL}")
print("Visible browser...\n")

opts = Options()
opts.add_argument("--window-size=1280,900")
opts.add_argument("--lang=en-GB")
opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
opts.add_experimental_option("excludeSwitches", ["enable-logging"])

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=opts)

try:
    driver.get(URL)
    print("Waiting 4s...")
    time.sleep(4)

    # Cookie banner
    for sel in ["#onetrust-accept-btn-handler", "button[id*=accept]",
                "button[class*=accept]", "[class*=consent] button",
                "button[class*=cookie]", "[data-testid*=accept]",
                "button[class*=agree]", "[class*=gdpr] button"]:
        try:
            driver.find_element(By.CSS_SELECTOR, sel).click()
            print(f"Cookie clicked: {sel}")
            time.sleep(1)
            break
        except: pass

    print("Waiting 6s for full load...")
    time.sleep(6)
    driver.execute_script("window.scrollTo(0, 800)")
    time.sleep(2)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    print(f"Page length: {len(html)}")
    print(f"Title: {driver.title}")
    print(f"Final URL: {driver.current_url}")

    # Captcha check
    if any(k in html.lower() for k in ["captcha", "robot", "human", "verify"]):
        print("\n⚠ CAPTCHA/BOT PROTECTION DETECTED!")
    else:
        print("\n✅ No captcha detected")

    # JSON-LD
    print("\n=== JSON-LD ===")
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            txt = json.dumps(data, ensure_ascii=False)
            if any(k in txt.lower() for k in ["price", "offer", "product"]):
                print(txt[:800])
                print("---")
        except: pass

    # Prices
    prices_gbp = re.findall(r"£\s*(\d{1,4}[.,]\d{2})", html)
    prices_eur = re.findall(r"€\s*(\d{1,4}[.,]\d{2})", html)
    print(f"\n£ prices found: {prices_gbp[:10]}")
    print(f"€ prices found: {prices_eur[:10]}")

    # All relevant CSS classes
    klassen = set()
    for el in soup.find_all(True):
        for c in el.get("class", []):
            if any(k in c.lower() for k in ["offer","price","shop","merchant","dealer","product","store","row","list","item"]):
                klassen.add(c)
    print(f"\nRelevant classes ({len(klassen)}): {sorted(klassen)[:40]}")

    # Shop links
    print("\n=== Shop/Offer Links ===")
    count = 0
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if any(k in href.lower() for k in ["shop","store","offer","click","out","redir","goto","buy"]):
            if text and len(text) < 60:
                print(f"  '{text}' -> {href[:100]}")
                count += 1
        if count >= 20: break

    # Elements with price + shop name
    print("\n=== Elements with price + shop ===")
    found = 0

    def parse_price(text):
        m = re.search(r"[£€$]\s*(\d{1,4}[.,]\d{2})", text)
        if m:
            c = m.group(1).replace(",",".")
            try: return float(c)
            except: pass
        return None

    for el in soup.find_all(["article","li","tr","div"], limit=500):
        text = el.get_text(" ", strip=True)
        price = parse_price(text)
        if not price or price < 1: continue
        if len(text) > 400: continue
        links = [a["href"] for a in el.find_all("a", href=True)]
        cls = " ".join(el.get("class",[]))
        if links and el.name in ["article","li","tr"]:
            print(f"\nTag:{el.name} cls:{cls[:60]}")
            print(f"  Text: {text[:120]}")
            print(f"  Links: {links[:2]}")
            found += 1
        if found >= 8: break

    # Save HTML
    out = Path("debug_pricespy_output.html")
    out.write_text(html, encoding="utf-8")
    print(f"\nHTML saved: {out.absolute()}")

    print("\nBrowser stays open 15s...")
    time.sleep(15)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback; traceback.print_exc()
finally:
    driver.quit()

input("\nPress Enter to exit...")
