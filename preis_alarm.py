"""
Preis-Alarm Tracker v3.0
Preisvergleich über mehrere Shops via Geizhals/Idealo URL oder Suchbegriff.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json, smtplib, threading, time, re, os, sys
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "requests", "beautifulsoup4", "win10toast",
                           "selenium", "webdriver-manager"])
    import requests
    from bs4 import BeautifulSoup

# System Tray
TRAY_OK = False
try:
    import pystray
    from pystray import MenuItem as TrayItem
    from PIL import Image, ImageDraw
    TRAY_OK = True
except ImportError:
    pass

SELENIUM_OK = False
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_OK = True
except ImportError:
    pass

def toast(titel, text):
    try:
        from win10toast import ToastNotifier
        ToastNotifier().show_toast(titel, text, duration=8, threaded=True)
    except Exception:
        pass

# ── Pfade ─────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(os.getenv("APPDATA", ".")) / "PreisAlarm"
BASE_DIR.mkdir(exist_ok=True)
VERGLEICH_DATEI = BASE_DIR / "vergleich.json"
CONFIG_DATEI    = BASE_DIR / "config.json"
LOG_DATEI       = BASE_DIR / "log.txt"

# ── Design ────────────────────────────────────────────────────────────────────
BG     = "#0f0f0f"
BG2    = "#1a1a1a"
BG3    = "#242424"
AKZENT = "#22c55e"
ROT    = "#ef4444"
GELB   = "#f59e0b"
GRAU   = "#6b7280"
TEXT   = "#f1f5f9"
TEXT2  = "#94a3b8"
BORDER = "#2d2d2d"

SHOPS = {
    "amazon": "Amazon.de", "mediamarkt": "MediaMarkt", "saturn": "Saturn",
    "otto": "OTTO", "ebay": "eBay", "alza": "Alza.de", "alternate": "Alternate",
    "mindfactory": "Mindfactory", "notebooksbilliger": "notebooksbilliger",
    "cyberport": "Cyberport", "kaufland": "Kaufland", "caseking": "Caseking",
    "idealo": "Idealo", "geizhals": "Geizhals", "custom": "Sonstiger Shop",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

JS_SHOPS = {"alza", "alternate", "mindfactory", "notebooksbilliger", "cyberport", "caseking"}

# ── Datenverwaltung ───────────────────────────────────────────────────────────
def lade_vergleiche():
    if VERGLEICH_DATEI.exists():
        with open(VERGLEICH_DATEI, "r", encoding="utf-8") as f:
            daten = json.load(f)
        # Migration: alte Einträge mit shop="custom" reparieren
        geaendert = False
        for g in daten:
            for s in g.get("shops", []):
                if s.get("shop") == "custom":
                    # Shop-Name aus URL ableiten
                    url = s.get("url", "")
                    try:
                        from urllib.parse import urlparse
                        domain = urlparse(url).netloc.replace("www.", "")
                        if domain:
                            s["shop"] = domain
                            geaendert = True
                    except:
                        pass
        if geaendert:
            with open(VERGLEICH_DATEI, "w", encoding="utf-8") as f:
                json.dump(daten, f, ensure_ascii=False, indent=2)
        return daten
    return []

def speichere_vergleiche(liste):
    with open(VERGLEICH_DATEI, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)

def lade_config():
    defaults = {"email_absender": "", "email_passwort": "", "email_empfaenger": "",
                "smtp_server": "mail.gmx.net", "smtp_port": 587, "intervall": 6}
    if CONFIG_DATEI.exists():
        with open(CONFIG_DATEI, "r", encoding="utf-8") as f:
            return {**defaults, **json.load(f)}
    return defaults

def speichere_config(cfg):
    with open(CONFIG_DATEI, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def log(msg):
    ts = datetime.now().strftime("%d.%m.%Y %H:%M")
    zeile = f"[{ts}] {msg}\n"
    with open(LOG_DATEI, "a", encoding="utf-8") as f:
        f.write(zeile)
    return zeile.strip()

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────
def _parse(text):
    clean = re.sub(r"[^\d,.]", "", str(text))
    if not clean:
        return None
    if "," in clean and "." in clean:
        clean = clean.replace(".", "").replace(",", ".")
    elif "," in clean:
        clean = clean.replace(",", ".")
    try:
        v = float(clean)
        return v if 0.01 < v < 100000 else None
    except:
        return None

def _shop_key_aus_name(name):
    """Gibt den internen Shop-Key zurück. Unbekannte Shops behalten ihren Namen."""
    name_l = name.lower()
    for keyword, key in [
        ("amazon","amazon"),("mediamarkt","mediamarkt"),("media markt","mediamarkt"),
        ("saturn","saturn"),("otto","otto"),("ebay","ebay"),("alza","alza"),
        ("alternate","alternate"),("mindfactory","mindfactory"),
        ("notebooksbilliger","notebooksbilliger"),("cyberport","cyberport"),
        ("kaufland","kaufland"),("caseking","caseking"),
        ("idealo","idealo"),("geizhals","geizhals"),
    ]:
        if keyword in name_l:
            return key
    # Unbekannte Shops: Name direkt als Key speichern
    return name

def _shop_aus_url(url):
    url_l = url.lower()
    for domain, key in [
        ("amazon.","amazon"),("mediamarkt.","mediamarkt"),("saturn.","saturn"),
        ("otto.","otto"),("ebay.","ebay"),("alza.","alza"),("alternate.","alternate"),
        ("mindfactory.","mindfactory"),("notebooksbilliger.","notebooksbilliger"),
        ("cyberport.","cyberport"),("kaufland.","kaufland"),("caseking.","caseking"),
        ("idealo.","idealo"),("geizhals.","geizhals"),
    ]:
        if domain in url_l:
            return key
    return "custom"



# ── Preisabruf ────────────────────────────────────────────────────────────────
def _redirect_aufloesen(url):
    """Nicht mehr verwendet — Redirects werden über Produktseite aufgelöst."""
    return url


def redirects_aufloesen_via_produktseite(source_url, shops):
    """
    Lädt die Geizhals-Produktseite EINMAL mit Selenium,
    klickt jeden Shop-Link an und fängt die finale URL im neuen Tab ab.
    Gibt ein Dict {shop_name -> echte_url} zurück.
    """
    if not SELENIUM_OK or not source_url:
        return {}
    driver = None
    ergebnis = {}
    try:
        opts = Options()
        opts.add_argument("--window-size=1280,900")
        opts.add_argument("--window-position=-32000,0")
        opts.add_argument("--lang=de-DE")
        opts.add_argument(f"--user-agent={HEADERS['User-Agent']}")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        driver.set_page_load_timeout(30)

        # Produktseite laden (mit Cookie)
        log(f"  URL-Auflösung: Lade {source_url[:60]}")
        driver.get(source_url)
        time.sleep(3)

        # Cookie-Banner wegklicken
        for sel in ["#onetrust-accept-btn-handler", "button[id*=accept]"]:
            try:
                driver.find_element(By.CSS_SELECTOR, sel).click()
                time.sleep(1)
                break
            except: pass

        time.sleep(2)

        # "Mehr Angebote" laden
        for _ in range(15):
            geklickt = driver.execute_script("""
                var btn = document.querySelector('.button--load-more-offers');
                if (btn && btn.textContent.trim() !== 'Keine weiteren Angebote') {
                    btn.click(); return true;
                } return false;
            """)
            if not geklickt: break
            time.sleep(2)

        # Für jeden Shop: Link in neuem Tab öffnen und URL abfangen
        haupt_tab = driver.current_window_handle

        for shop in shops:
            shop_name = shop.get("shop_name") or shop["shop"]
            redir_url = shop.get("url","")
            if not ("geizhals.de/redir/" in redir_url or "geizhals.at/redir/" in redir_url):
                continue

            try:
                # Link per JavaScript in neuem Tab öffnen
                driver.execute_script(f"window.open('{redir_url}', '_blank');")
                time.sleep(3)

                # Zum neuen Tab wechseln
                tabs = driver.window_handles
                if len(tabs) > 1:
                    driver.switch_to.window(tabs[-1])
                    time.sleep(2)
                    final_url = driver.current_url
                    if "geizhals.de" not in final_url and "geizhals.at" not in final_url:
                        ergebnis[shop_name] = final_url
                        log(f"  ✓ {shop_name}: {final_url[:50]}")
                    else:
                        log(f"  ✗ {shop_name}: Redirect blockiert")
                    driver.close()
                    driver.switch_to.window(haupt_tab)
                    time.sleep(0.5)
            except Exception as e:
                log(f"  ✗ {shop_name}: {e}")
                try:
                    tabs = driver.window_handles
                    if len(tabs) > 1:
                        driver.switch_to.window(tabs[-1])
                        driver.close()
                    driver.switch_to.window(haupt_tab)
                except: pass

        return ergebnis
    except Exception as e:
        log(f"  URL-Auflösung Fehler: {e}")
        return {}
    finally:
        if driver:
            try: driver.quit()
            except: pass


def preis_holen(url, shop):
    try:
        html = _selenium_get(url, wait=4) if shop in JS_SHOPS and SELENIUM_OK else ""
        if not html:
            r = requests.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json as _j
                data = _j.loads(script.string or "")
                for item in (data if isinstance(data, list) else [data]):
                    offers = item.get("offers", {})
                    if isinstance(offers, list): offers = offers[0] if offers else {}
                    p = _parse(str(offers.get("price", "")))
                    if p: return p
            except:
                pass

        # itemprop
        el = soup.find(attrs={"itemprop": "price"})
        if el:
            p = _parse(el.get("content", "") or el.get_text())
            if p: return p

        # Shop-Selektoren
        sels = {
            "amazon":     [".a-offscreen", ".a-price-whole"],
            "mediamarkt": ['[data-testid="product-price"]', '[class*="Price_value"]'],
            "saturn":     ['[data-testid="product-price"]', '[class*="Price_value"]'],
            "otto":       [".prd-price__amount"],
            "ebay":       [".x-price-primary"],
            "alza":       [".price-box__price", '[class*="price-final"]'],
            "caseking":   [".js-unit-price", '[data-qa="product-unit-price-value"]'],
        }.get(shop, []) + ['[class*="current-price"]', '[class*="sell-price"]', '.price']

        for sel in sels:
            try:
                el = soup.select_one(sel)
                if el:
                    p = _parse(el.get_text(separator=" ", strip=True))
                    if p and 1 < p < 50000: return p
            except:
                pass

        # Regex-Fallback
        matches = re.findall(r'(?<!\d)(\d{1,4}[.,]\d{2})\s*(?:€|EUR)', html)
        candidates = [c for c in [_parse(m) for m in matches] if c and 1 < c < 50000]
        if candidates:
            from collections import Counter
            return Counter(candidates).most_common(1)[0][0]
        return None
    except:
        return None

# ── Shop-Suche via URL oder Suchbegriff ──────────────────────────────────────
def _selenium_get(url, wait=4):
    """Lädt eine URL mit echtem Chrome."""
    if not SELENIUM_OK:
        return ""
    driver = None
    try:
        opts = Options()
        ist_geizhals = "geizhals.de" in url
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1280,900")
        opts.add_argument("--lang=de-DE")
        opts.add_argument(f"--user-agent={HEADERS['User-Agent']}")
        opts.add_experimental_option("excludeSwitches", ["enable-logging"])
        opts.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=opts)
        driver.set_page_load_timeout(30)

        driver.get(url)
        time.sleep(2)

        # Cookie-Banner wegklicken
        for sel in ["#onetrust-accept-btn-handler", "button[id*=accept]",
                    "button[class*=accept]", "[class*=consent] button",
                    "button[id*=cookie]", "[data-testid*=accept]"]:
            try:
                driver.find_element(By.CSS_SELECTOR, sel).click()
                time.sleep(0.8)
                break
            except: pass

        time.sleep(wait)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2)")
        time.sleep(1.5)

        # Geizhals: "Mehr Angebote" Button klicken bis alle geladen
        if ist_geizhals:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)
            for i in range(15):
                geklickt = driver.execute_script("""
                    var btn = document.querySelector('.button--load-more-offers');
                    if (btn && btn.textContent.trim() !== 'Keine weiteren Angebote') {
                        btn.scrollIntoView({block: 'center'});
                        btn.click();
                        return true;
                    }
                    return false;
                """)
                if geklickt:
                    time.sleep(2.5)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    log(f"  Mehr Angebote geladen (Klick {i+1})...")
                else:
                    break

        return driver.page_source
    except Exception as e:
        log(f"Selenium Fehler: {e}")
        return ""
    finally:
        if driver:
            try: driver.quit()
            except: pass


def shops_aus_url_laden(url, max_shops=999):
    """
    Lädt alle Shops direkt von einer Geizhals- oder Idealo-Produktseite.
    Nutzt Selenium (echter Chrome) damit JavaScript-Inhalte geladen werden.
    """
    shops = []
    produkt_name = ""
    try:
        log(f"Lade URL: {url[:80]}")
        html = _selenium_get(url, wait=5)
        if not html:
            r = requests.get(url, headers=HEADERS, timeout=20)
            html = r.text
            log("Fallback: normaler HTTP-Request")

        soup = BeautifulSoup(html, "html.parser")

        # Produktname
        for sel in ["h1.variant__header__headline","h1[class*=headline]",
                    "h1[class*=product]","h1[class*=title]","h1"]:
            el = soup.select_one(sel)
            if el:
                produkt_name = el.get_text(strip=True)[:80]
                break

        anbieter = set()
        ist_geizhals = "geizhals.de" in url
        ist_idealo   = "idealo.de"   in url

        # ── JSON-LD (zuverlässigste Methode) ──────────────────────────────────
        import json as _j
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = _j.loads(script.string or "")
                for item in (data if isinstance(data, list) else [data]):
                    offers = item.get("offers", [])
                    if isinstance(offers, dict): offers = [offers]
                    for offer in offers[:max_shops]:
                        seller = offer.get("seller", {})
                        name  = seller.get("name","") if isinstance(seller,dict) else str(seller)
                        preis = _parse(str(offer.get("price","")))
                        ourl  = offer.get("url","") or url
                        if name and preis and name not in anbieter:
                            anbieter.add(name)
                            shops.append({"name":name,"url":ourl,"preis":preis,
                                          "shop_key":_shop_key_aus_name(name),
                                          "shop_name":name})
            except: pass

        log(f"JSON-LD: {len(shops)} Shops gefunden")

        # ── Geizhals HTML-Parsing ──────────────────────────────────────────────
        if not shops and ist_geizhals:
            # Geizhals: jedes Angebot ist ein Element mit class="offer"
            # Preis: class="gh_price" → Text "€ 659,00"
            # Shop-Name: <a href="geizhals.de/redir/..."> mit Shop-Name als Text
            for offer in soup.find_all(class_="offer")[:max_shops]:
                try:
                    # Preis aus gh_price
                    preis_el = offer.find(class_="gh_price")
                    if not preis_el: continue
                    preis = _parse(preis_el.get_text(strip=True))
                    if not preis: continue

                    # Shop-Name + URL: Link mit "redir" der NICHT "zum Angebot", "AGB", "Infos", "Bewertung" heißt
                    shop_name = ""
                    shop_url  = ""
                    skip = {"zum angebot","agb","infos","bewertung","store"}
                    for a in offer.find_all("a", href=True):
                        href = a["href"]
                        text = a.get_text(strip=True)
                        if "redir" in href and text and text.lower() not in skip and len(text) > 1:
                            if not href.startswith("http"):
                                href = "https://geizhals.de" + href
                            shop_name = text
                            shop_url  = href
                            break

                    if not shop_name or not shop_url: continue
                    if shop_name not in anbieter:
                        anbieter.add(shop_name)
                        shops.append({"name": shop_name, "url": shop_url,
                                      "preis": preis,
                                      "shop_key": _shop_key_aus_name(shop_name),
                                      "shop_name": shop_name})
                except Exception as e:
                    log(f"Offer-Parse Fehler: {e}")
                    continue

            log(f"Geizhals HTML: {len(shops)} Shops gefunden")

        # ── Idealo HTML-Parsing ────────────────────────────────────────────────
        if not shops and ist_idealo:
            for el in soup.find_all(["article","div","li","tr"], limit=300):
                cls = " ".join(el.get("class",[]))
                if not any(k in cls.lower() for k in ["offer","price","shop","dealer","merchant"]):
                    continue
                text = el.get_text(" ", strip=True)
                m = re.search(r"(\d{1,4}[.,]\d{2})\s*€", text)
                if not m: continue
                preis = _parse(m.group(1))
                if not preis or preis < 10: continue
                # Shop-Name
                shop_name = ""
                for cls_key in ["shop","merchant","dealer","vendor","seller"]:
                    ne = el.find(class_=lambda c: c and cls_key in c.lower() if c else False)
                    if ne:
                        shop_name = ne.get_text(strip=True)[:50]
                        break
                # URL
                shop_url = url
                for a in el.find_all("a", href=True):
                    href = a["href"]
                    if any(k in href for k in ["redir","goto","out","affiliate","click"]):
                        if not href.startswith("http"):
                            href = "https://www.idealo.de" + href
                        shop_url = href
                        if not shop_name:
                            shop_name = a.get_text(strip=True)[:50]
                        break
                if shop_name and shop_name not in anbieter:
                    anbieter.add(shop_name)
                    shops.append({"name":shop_name,"url":shop_url,"preis":preis,
                                  "shop_key":_shop_key_aus_name(shop_name)})
                if len(shops) >= max_shops: break

            log(f"Idealo HTML: {len(shops)} Shops gefunden")

        # Deduplizieren und nach Preis sortieren
        shops = sorted(shops, key=lambda s: s["preis"])
        log(f"Gesamt: {len(shops)} Shops von {url[:60]}")
        return shops, produkt_name
    except Exception as e:
        log(f"Fehler beim Laden: {e}")
        return [], ""


def geizhals_suchen(suchbegriff, max_shops=999):
    """Sucht auf Geizhals (DE + EU), Fallback auf Idealo."""
    log(f"Suche: '{suchbegriff}'")
    try:
        # Geizhals: DE zuerst, dann EU
        for hloc in ["de", "de,at,ch,eu"]:
            such_url = "https://geizhals.de/?fs={}&bl=&hloc={}&in=&v=e&sort=p".format(
                requests.utils.quote(suchbegriff), hloc)
            log(f"Geizhals Suche ({hloc}): {such_url[:80]}")
            html = _selenium_get(such_url, wait=4)
            if not html:
                r = requests.get(such_url, headers=HEADERS, timeout=20)
                html = r.text
            soup = BeautifulSoup(html, "html.parser")

            # Produktlink finden
            produkt_link = None
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.search(r"-a\d{4,}\.htm", href):
                    produkt_link = href
                    break
            if not produkt_link:
                # Fallback: beliebiger Produktlink
                m = re.search(r'href="(/[^"]*-a\d{4,}\.htm[^"]*)"', html)
                if m: produkt_link = m.group(1)

            if produkt_link:
                if not produkt_link.startswith("http"):
                    produkt_link = "https://geizhals.de" + produkt_link
                log(f"Produktseite: {produkt_link}")
                shops, name = shops_aus_url_laden(produkt_link, max_shops=999)
                if shops:
                    return shops, name or suchbegriff, produkt_link

        # Idealo-Fallback
        log("Kein Ergebnis auf Geizhals, versuche Idealo...")
        such_url = "https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={}".format(
            requests.utils.quote(suchbegriff))
        html = _selenium_get(such_url, wait=4)
        if not html:
            r = requests.get(such_url, headers=HEADERS, timeout=20)
            html = r.text
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/preisvergleich/OffersOfProduct/" in href or re.search(r"/preisvergleich/\d+", href):
                if not href.startswith("http"):
                    href = "https://www.idealo.de" + href
                log(f"Idealo Produktseite: {href[:80]}")
                shops, name = shops_aus_url_laden(href, max_shops=999)
                if shops:
                    return shops, name or suchbegriff, href
                break

        log("Keine Shops gefunden auf Geizhals/Idealo")
        return [], suchbegriff
    except Exception as e:
        log(f"Suche Fehler: {e}")
        return [], suchbegriff, ""


def alle_quellen_suchen(suchbegriff, max_shops=999):
    """Haupteinstieg: Sucht auf allen Quellen."""
    return geizhals_suchen(suchbegriff, max_shops)


def email_preisaenderung(cfg, gruppe, geaenderte_shops):
    """Sendet E-Mail mit allen Shops die ihren Preis geändert haben."""
    try:
        zeilen = ""
        for s in geaenderte_shops:
            name     = s["shop_name"]
            url      = s["url"]
            alt      = s["preis_alt"]
            neu      = s["preis_neu"]
            diff     = neu - alt
            pfeil    = "⬇" if diff < 0 else "⬆"
            farbe    = "#22c55e" if diff < 0 else "#ef4444"
            zeilen += f"""
            <tr>
              <td style="padding:10px;color:#f1f5f9;border-bottom:1px solid #2d2d2d">{name}</td>
              <td style="padding:10px;color:#94a3b8;border-bottom:1px solid #2d2d2d">{alt:.2f} €</td>
              <td style="padding:10px;font-weight:bold;color:{farbe};border-bottom:1px solid #2d2d2d">{neu:.2f} €</td>
              <td style="padding:10px;color:{farbe};border-bottom:1px solid #2d2d2d">{pfeil} {abs(diff):.2f} €</td>
              <td style="padding:10px;border-bottom:1px solid #2d2d2d">
                <a href="{url}" style="color:#378ADD;text-decoration:none">Shop öffnen</a>
              </td>
            </tr>"""

        from datetime import datetime as _dt
        html = f"""<html><body style="font-family:Arial;max-width:700px;margin:auto;
                   background:#0f0f0f;color:#f1f5f9;padding:24px">
        <div style="background:#1a3a5c;padding:16px;border-radius:8px;margin-bottom:20px">
          <h2 style="color:#60a5fa;margin:0">📊 Preisänderungen: {gruppe['name']}</h2>
          <p style="color:#94a3b8;margin:4px 0 0">{len(geaenderte_shops)} Shop(s) haben den Preis geändert</p>
        </div>
        <table style="width:100%;border-collapse:collapse">
          <tr style="background:#1a1a1a">
            <th style="padding:10px;text-align:left;color:#94a3b8">Shop</th>
            <th style="padding:10px;text-align:left;color:#94a3b8">Alter Preis</th>
            <th style="padding:10px;text-align:left;color:#94a3b8">Neuer Preis</th>
            <th style="padding:10px;text-align:left;color:#94a3b8">Änderung</th>
            <th style="padding:10px;text-align:left;color:#94a3b8">Link</th>
          </tr>
          {zeilen}
        </table>
        <p style="color:#6b7280;font-size:12px;margin-top:20px">
          Preis-Alarm Tracker · {_dt.now().strftime('%d.%m.%Y %H:%M')}
        </p>
        </body></html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 Preisänderungen: {gruppe['name']} ({len(geaenderte_shops)} Shops)"
        msg["From"]    = formataddr(("Preis Alarm", cfg["email_absender"]))
        msg["To"]      = cfg["email_empfaenger"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"])) as s:
            s.starttls()
            s.login(cfg["email_absender"], cfg["email_passwort"])
            s.sendmail(cfg["email_absender"], cfg["email_empfaenger"], msg.as_string())
        log(f"  Preisänderungs-Mail gesendet ({len(geaenderte_shops)} Shops)")
        return True
    except Exception as e:
        log(f"  Mail Fehler: {e}")
        return False


def email_zusammenfassung(cfg, alle_aenderungen, alarme):
    """Sendet eine einzige zusammengefasste Mail nach dem Check."""
    try:
        from datetime import datetime as _dt
        hat_aenderungen = any(g["shops"] for g in alle_aenderungen)
        hat_alarme      = bool(alarme)
        if not hat_aenderungen and not hat_alarme:
            return

        # Betreff
        alarm_anzahl   = len(alarme)
        aender_anzahl  = sum(len(g["shops"]) for g in alle_aenderungen)
        if hat_alarme:
            betreff = f"🔔 {alarm_anzahl} Zielpreis-Alarm{'e' if alarm_anzahl>1 else ''} + {aender_anzahl} Preisänderung{'en' if aender_anzahl!=1 else ''}"
        else:
            betreff = f"📊 {aender_anzahl} Preisänderung{'en' if aender_anzahl!=1 else ''} beim letzten Check"

        # Alarm-Sektion
        alarm_html = ""
        if hat_alarme:
            alarm_zeilen = ""
            for a in alarme:
                alarm_zeilen += f"""
                <tr>
                  <td style="padding:10px;color:#f1f5f9;font-weight:bold">{a['name']}</td>
                  <td style="padding:10px;color:#22c55e;font-size:18px;font-weight:bold">{a['bester']:.2f} €</td>
                  <td style="padding:10px;color:#f1f5f9">{a['shop']}</td>
                </tr>"""
            alarm_html = f"""
            <div style="background:#14532d;border-radius:8px;padding:16px;margin-bottom:20px">
              <h2 style="color:#4ade80;margin:0 0 12px">🔔 Zielpreis erreicht!</h2>
              <table style="width:100%;border-collapse:collapse">
                <tr style="background:#166534">
                  <th style="padding:8px;text-align:left;color:#86efac">Produkt</th>
                  <th style="padding:8px;text-align:left;color:#86efac">Bester Preis</th>
                  <th style="padding:8px;text-align:left;color:#86efac">Shop</th>
                </tr>
                {alarm_zeilen}
              </table>
            </div>"""

        # Preisänderungs-Sektionen pro Gruppe
        aender_html = ""
        for gruppe in alle_aenderungen:
            if not gruppe["shops"]: continue
            ziel = gruppe["zielpreis"]
            zeilen = ""
            for s in gruppe["shops"]:
                diff    = s["preis_neu"] - s["preis_alt"]
                pfeil   = "⬇" if diff < 0 else "⬆"
                f_diff  = "#22c55e" if diff < 0 else "#f87171"
                ziel_badge = ""
                if s.get("ziel_erreicht"):
                    ziel_badge = '<span style="background:#14532d;color:#4ade80;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:6px">🎯 Zielpreis!</span>'
                zeilen += f"""
                <tr style="{'background:#1a2e1a' if s.get('ziel_erreicht') else ''}">
                  <td style="padding:10px;color:#f1f5f9;border-bottom:1px solid #2d2d2d">
                    {s['shop_name']}{ziel_badge}
                  </td>
                  <td style="padding:10px;color:#94a3b8;border-bottom:1px solid #2d2d2d">{s['preis_alt']:.2f} €</td>
                  <td style="padding:10px;font-weight:bold;color:{f_diff};border-bottom:1px solid #2d2d2d">
                    {s['preis_neu']:.2f} € &nbsp;{pfeil} {abs(diff):.2f} €
                  </td>
                  <td style="padding:10px;border-bottom:1px solid #2d2d2d">
                    <a href="{s['url']}" style="color:#60a5fa;text-decoration:none">Shop →</a>
                  </td>
                </tr>"""

            aender_html += f"""
            <div style="margin-bottom:20px">
              <h3 style="color:#f1f5f9;margin:0 0 8px">{gruppe['gruppe_name']}
                <span style="color:#6b7280;font-size:12px;font-weight:normal;margin-left:8px">
                  Zielpreis: {ziel:.2f} €
                </span>
              </h3>
              <table style="width:100%;border-collapse:collapse;background:#1a1a1a;border-radius:8px">
                <tr style="background:#242424">
                  <th style="padding:8px;text-align:left;color:#94a3b8">Shop</th>
                  <th style="padding:8px;text-align:left;color:#94a3b8">Alter Preis</th>
                  <th style="padding:8px;text-align:left;color:#94a3b8">Neuer Preis</th>
                  <th style="padding:8px;text-align:left;color:#94a3b8">Link</th>
                </tr>
                {zeilen}
              </table>
            </div>"""

        html = f"""<html><body style="font-family:Arial;max-width:700px;margin:auto;
                   background:#0f0f0f;color:#f1f5f9;padding:24px">
          <div style="border-bottom:1px solid #2d2d2d;padding-bottom:12px;margin-bottom:20px">
            <h1 style="color:#f1f5f9;margin:0;font-size:20px">🔔 Preis-Alarm Tracker</h1>
            <p style="color:#6b7280;margin:4px 0 0;font-size:12px">
              Check vom {_dt.now().strftime('%d.%m.%Y um %H:%M Uhr')}
            </p>
          </div>
          {alarm_html}
          {('<h2 style="color:#f1f5f9;margin:0 0 16px">📊 Preisänderungen</h2>' + aender_html) if hat_aenderungen else ''}
          <p style="color:#4b5563;font-size:11px;margin-top:24px;border-top:1px solid #1f2937;padding-top:12px">
            Preis-Alarm Tracker · Automatischer Check
          </p>
        </body></html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = betreff
        msg["From"]    = formataddr(("Preis Alarm", cfg["email_absender"]))
        msg["To"]      = cfg["email_empfaenger"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"])) as s:
            s.starttls()
            s.login(cfg["email_absender"], cfg["email_passwort"])
            s.sendmail(cfg["email_absender"], cfg["email_empfaenger"], msg.as_string())
        log(f"Zusammenfassungs-Mail gesendet ({aender_anzahl} Änderungen, {alarm_anzahl} Alarme)")
    except Exception as e:
        log(f"Mail Fehler: {e}")


def email_senden(cfg, gruppe, bester_preis, bester_shop):
    try:
        alle = "".join(
            f"<tr><td style='padding:8px;color:#94a3b8'>{s.get('shop_name') or SHOPS.get(s['shop'],s['shop'])}</td>"
            f"<td style='padding:8px;{'font-weight:bold;color:#22c55e' if s.get('preis')==bester_preis else ''}'>"
            f"{s['preis']:.2f} €</td>"
            f"<td><a href='{s['url']}' style='color:#378ADD'>Shop</a></td></tr>"
            for s in gruppe.get("shops",[]) if s.get("preis")
        )
        html = f"""<html><body style="font-family:Arial;max-width:600px;margin:auto;background:#0f0f0f;color:#f1f5f9;padding:24px">
        <h2 style="color:#4ade80">🏆 Preisvergleich-Alarm!</h2>
        <h3>{gruppe['name']}</h3>
        <p>Günstigster Preis: <strong style="color:#22c55e;font-size:20px">{bester_preis:.2f} €</strong> bei {bester_shop}</p>
        <table style="width:100%;border-collapse:collapse">{alle}</table>
        <p style="color:#6b7280;font-size:12px">{datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        </body></html>"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🏆 {gruppe['name']} ab {bester_preis:.2f} €"
        msg["From"]    = formataddr(("Preis Alarm", cfg["email_absender"]))
        msg["To"]      = cfg["email_empfaenger"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"])) as s:
            s.starttls()
            s.login(cfg["email_absender"], cfg["email_passwort"])
            s.sendmail(cfg["email_absender"], cfg["email_empfaenger"], msg.as_string())
        return True
    except Exception as e:
        log(f"E-Mail Fehler: {e}")
        return False

# ── Autostart & Tray ─────────────────────────────────────────────────────────
import winreg

AUTOSTART_KEY  = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
AUTOSTART_NAME = "PreisAlarmTracker"

def autostart_aktiv():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, AUTOSTART_NAME)
        winreg.CloseKey(key)
        return True
    except:
        return False

def autostart_setzen(aktiv):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE)
        if aktiv:
            # pythonw.exe nutzen damit kein CMD-Fenster erscheint
            exe = sys.executable.replace("python.exe", "pythonw.exe")
            if not Path(exe).exists():
                exe = sys.executable  # Fallback
            script = str(Path(__file__).resolve())
            pfad = f'"{exe}" "{script}"' 
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, pfad)
            log(f"Autostart gesetzt: {pfad}")
        else:
            try: winreg.DeleteValue(key, AUTOSTART_NAME)
            except: pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        log(f"Autostart Fehler: {e}")
        return False

def tray_icon_erstellen():
    """Erstellt ein einfaches grünes Glocken-Icon für den Tray."""
    img = Image.new("RGBA", (64, 64), (0,0,0,0))
    d   = ImageDraw.Draw(img)
    # Glocke zeichnen
    d.ellipse([8, 8, 56, 52], fill="#22c55e")
    d.rectangle([20, 50, 44, 58], fill="#22c55e")
    d.ellipse([24, 54, 40, 64], fill="#22c55e")
    d.rectangle([28, 2, 36, 14], fill="#22c55e")
    return img


# ── GUI ───────────────────────────────────────────────────────────────────────
class PreisAlarmApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Preis-Alarm Tracker")
        self.geometry("960x680")
        self.minsize(800, 560)
        self.configure(bg=BG)
        self.vergleiche  = lade_vergleiche()
        self.config_data = lade_config()
        self._vg_shop_vars      = {}
        self.vg_aktuelle_gruppe = None
        self._setup_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._fenster_schliessen)
        self._tray_icon = None
        self._tray_thread = None
        # Automatische Preisprüfung starten
        self._auto_check_starten()

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, bg=BG3, fg=TEXT):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         activebackground=bg, activeforeground=fg,
                         font=("Segoe UI", 10), relief="flat", cursor="hand2",
                         padx=14, pady=6, bd=0)

    def _aktuelle_vg(self):
        return next((g for g in self.vergleiche if g["id"] == self.vg_aktuelle_gruppe), None)

    # ── Style ──────────────────────────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, fieldbackground=BG3,
                    bordercolor=BORDER, troughcolor=BG2,
                    selectbackground=AKZENT, selectforeground="#000", font=("Segoe UI", 10))
        s.configure("Treeview", background=BG2, foreground=TEXT, fieldbackground=BG2,
                    rowheight=34, borderwidth=0)
        s.configure("Treeview.Heading", background=BG3, foreground=TEXT2, relief="flat",
                    font=("Segoe UI", 9, "bold"))
        s.map("Treeview", background=[("selected", BG3)], foreground=[("selected", AKZENT)])
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG3, foreground=TEXT2, padding=[16, 8])
        s.map("TNotebook.Tab", background=[("selected", BG2)], foreground=[("selected", TEXT)])
        s.configure("TEntry", fieldbackground=BG3, foreground=TEXT, insertcolor=TEXT,
                    bordercolor=BORDER, relief="flat", padding=6)
        s.configure("TCombobox", fieldbackground=BG3, foreground=TEXT,
                    selectbackground=BG3, arrowcolor=TEXT2)
        s.configure("TScrollbar", background=BG2, troughcolor=BG, arrowcolor=GRAU)

    # ── Haupt-UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(hdr, text="🔔 Preis-Alarm Tracker", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(side="left")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=12)
        self.tab_vergleich = tk.Frame(nb, bg=BG)
        self.tab_einst     = tk.Frame(nb, bg=BG)
        self.tab_log       = tk.Frame(nb, bg=BG)
        nb.add(self.tab_vergleich, text="  ⚖ Preisvergleich  ")
        nb.add(self.tab_einst,     text="  ⚙ Einstellungen  ")
        nb.add(self.tab_log,       text="  📄 Log  ")
        self._tab_vergleich()
        self._tab_einstellungen()
        self._tab_log()

    # ── Tab: Preisvergleich ───────────────────────────────────────────────────
    def _tab_vergleich(self):
        f = self.tab_vergleich
        bar = tk.Frame(f, bg=BG)
        bar.pack(fill="x", padx=12, pady=(12, 6))
        self._btn(bar, "➕  Neue Gruppe",    self._vg_neu,          AKZENT, "#000").pack(side="left", padx=(0,8))
        self.btn_pruefen = self._btn(bar, "🔄  Alle prüfen", self._vg_alle_pruefen, BG3, TEXT)
        self.btn_pruefen.pack(side="left", padx=(0,8))
        self.status_check_lbl = tk.Label(bar, text="", bg=BG, fg=TEXT2, font=("Segoe UI", 9))
        self.status_check_lbl.pack(side="left", padx=10)
        self._btn(bar, "🗑  Löschen (ENTF)", self._vg_loeschen,     BG3, ROT).pack(side="right")

        pane = tk.Frame(f, bg=BG)
        pane.pack(fill="both", expand=True, padx=12, pady=(0,12))

        left = tk.Frame(pane, bg=BG, width=220)
        left.pack(side="left", fill="y", padx=(0,12))
        left.pack_propagate(False)
        tk.Label(left, text="PRODUKTGRUPPEN", bg=BG, fg=TEXT2,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(4,6))
        self.vg_listbox = tk.Listbox(
            left, bg=BG2, fg=TEXT, selectbackground=BG3, selectforeground=AKZENT,
            font=("Segoe UI", 10), relief="flat", borderwidth=0, activestyle="none",
            highlightthickness=1, highlightcolor=BORDER, highlightbackground=BORDER)
        self.vg_listbox.pack(fill="both", expand=True)
        self.vg_listbox.bind("<<ListboxSelect>>", lambda e: self._vg_gruppe_waehlen())
        self.vg_listbox.bind("<Delete>",    lambda e: self._vg_loeschen())
        self.vg_listbox.bind("<BackSpace>", lambda e: self._vg_loeschen())

        right = tk.Frame(pane, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        hdr2 = tk.Frame(right, bg=BG)
        hdr2.pack(fill="x", pady=(4,8))
        self.vg_titel_lbl = tk.Label(hdr2, text="← Gruppe auswählen oder neu erstellen",
                                     bg=BG, fg=TEXT2, font=("Segoe UI", 12, "bold"))
        self.vg_titel_lbl.pack(side="left")
        self.vg_ziel_lbl = tk.Label(hdr2, text="", bg=BG, fg=GRAU, font=("Segoe UI", 10))
        self.vg_ziel_lbl.pack(side="left", padx=12)
        self._btn(hdr2, "📈 Preisverlauf", self._vg_chart_zeigen, BG3, TEXT2).pack(side="right", padx=(0,6))
        self._btn(hdr2, "+ URL manuell",  self._vg_shop_manuell, BG3, GRAU).pack(side="right")

        # Sortier-Status: col -> bool (True=aufsteigend)
        self._sort_col   = "preis"
        self._sort_asc   = True

        cols = ("shop","url","preis","diff","status","zuletzt")
        self.vg_tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        col_defs = [("shop","Shop ↕",130),("url","URL ↕",270),("preis","Akt. Preis ↕",95),
                    ("diff","Zielpreis ↕",95),("status","Status ↕",110),("zuletzt","Geprüft ↕",110)]
        for col, text, w in col_defs:
            self.vg_tree.heading(col, text=text,
                                 command=lambda c=col: self._vg_sort_klick(c))
            self.vg_tree.column(col, width=w,
                                anchor="w" if col in ("shop","url","status","zuletzt") else "e")
        sb = ttk.Scrollbar(right, orient="vertical", command=self.vg_tree.yview)
        self.vg_tree.configure(yscrollcommand=sb.set)
        self.vg_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.vg_tree.bind("<Delete>",    lambda e: self._vg_shop_loeschen())
        self.vg_tree.bind("<BackSpace>", lambda e: self._vg_shop_loeschen())
        self.vg_tree.bind("<Double-1>",  lambda e: self._vg_shop_oeffnen())
        self.vg_tree.tag_configure("best",      foreground=AKZENT, font=("Segoe UI", 10, "bold"))
        self.vg_tree.tag_configure("alarm",     foreground=AKZENT)
        self.vg_tree.tag_configure("normal",    foreground=TEXT)
        self.vg_tree.tag_configure("fehler",    foreground=ROT)
        self.vg_tree.tag_configure("gesunken",  foreground="#22c55e", font=("Segoe UI", 10, "bold"))
        self.vg_tree.tag_configure("gestiegen", foreground="#f59e0b", font=("Segoe UI", 10, "bold"))
        self._vg_listbox_laden()

    # ── Tab: Einstellungen ────────────────────────────────────────────────────
    def _tab_einstellungen(self):
        f = self.tab_einst
        wrap = tk.Frame(f, bg=BG)
        wrap.pack(fill="both", expand=True, padx=40, pady=24)

        def section(text):
            tk.Label(wrap, text=text, bg=BG, fg=TEXT2,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(16,4))
            tk.Frame(wrap, bg=BORDER, height=1).pack(fill="x", pady=(0,8))

        def erow(label, var, show=""):
            r = tk.Frame(wrap, bg=BG)
            r.pack(fill="x", pady=5)
            tk.Label(r, text=label, bg=BG, fg=TEXT2, width=18, anchor="w",
                     font=("Segoe UI", 10)).pack(side="left")
            e = ttk.Entry(r, textvariable=var, show=show)
            e.pack(side="left", fill="x", expand=True, ipady=4)
            return e

        cfg = self.config_data
        self.v_abs  = tk.StringVar(value=cfg.get("email_absender",""))
        self.v_pw   = tk.StringVar(value=cfg.get("email_passwort",""))
        self.v_emp  = tk.StringVar(value=cfg.get("email_empfaenger",""))
        self.v_smtp = tk.StringVar(value=cfg.get("smtp_server","mail.gmx.net"))
        self.v_port = tk.StringVar(value=str(cfg.get("smtp_port",587)))
        self.v_int  = tk.StringVar(value=str(cfg.get("intervall",6)))

        section("📧  E-Mail Konfiguration")
        erow("Absender E-Mail",  self.v_abs)
        erow("Passwort",         self.v_pw,  show="●")
        erow("Empfänger E-Mail", self.v_emp)
        erow("SMTP Server",      self.v_smtp)
        erow("SMTP Port",        self.v_port)

        section("⏱  Prüf-Intervall")
        r = tk.Frame(wrap, bg=BG)
        r.pack(fill="x", pady=5)
        tk.Label(r, text="Alle X Stunden", bg=BG, fg=TEXT2, width=18, anchor="w",
                 font=("Segoe UI", 10)).pack(side="left")
        ttk.Entry(r, textvariable=self.v_int, width=6).pack(side="left", ipady=4)
        tk.Label(r, text=" Stunden (1–24)", bg=BG, fg=GRAU,
                 font=("Segoe UI", 9)).pack(side="left", padx=8)

        tk.Frame(wrap, bg=BORDER, height=1).pack(fill="x", pady=16)
        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill="x")
        self._btn(btn_row, "💾  Speichern",  self._cfg_speichern, AKZENT, "#000").pack(side="left", padx=(0,10), ipady=4)
        self._btn(btn_row, "✉  Test-E-Mail", self._test_email,    BG3, TEXT).pack(side="left", ipady=4)

        section("🖥  System")
        sys_row = tk.Frame(wrap, bg=BG)
        sys_row.pack(fill="x", pady=5)
        self.v_autostart = tk.BooleanVar(value=autostart_aktiv())
        tk.Checkbutton(sys_row, variable=self.v_autostart,
                       bg=BG, fg=TEXT, activebackground=BG, selectcolor=BG3,
                       font=("Segoe UI", 10),
                       text="Mit Windows starten (Autostart)",
                       command=self._autostart_toggle).pack(side="left")

        tray_row = tk.Frame(wrap, bg=BG)
        tray_row.pack(fill="x", pady=5)
        self.v_tray = tk.BooleanVar(value=self.config_data.get("minimize_to_tray", True))
        tk.Checkbutton(tray_row, variable=self.v_tray,
                       bg=BG, fg=TEXT, activebackground=BG, selectcolor=BG3,
                       font=("Segoe UI", 10),
                       text="Beim Schließen in System-Tray minimieren (läuft im Hintergrund)",
                       command=self._tray_toggle).pack(side="left")

        section("ℹ  SMTP Einstellungen")
        for name, server, port in [
            ("GMX",     "mail.gmx.net",        "587"),
            ("Web.de",  "smtp.web.de",          "587"),
            ("Outlook", "smtp.office365.com",   "587"),
            ("Gmail",   "smtp.gmail.com",       "587  (App-Passwort nötig)"),
        ]:
            tk.Label(wrap, text=f"{name}: {server}  |  Port: {port}",
                     bg=BG, fg=GRAU, font=("Segoe UI", 9)).pack(anchor="w")

    # ── Tab: Log ──────────────────────────────────────────────────────────────
    def _tab_log(self):
        f = self.tab_log
        bar = tk.Frame(f, bg=BG)
        bar.pack(fill="x", padx=12, pady=(12,4))
        self._btn(bar, "🗑  Log leeren", self._log_leeren, BG3, TEXT).pack(side="left")
        self.log_box = scrolledtext.ScrolledText(
            f, bg=BG2, fg=TEXT, font=("Consolas", 9),
            insertbackground=TEXT, borderwidth=0, relief="flat",
            state="disabled", wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self._log_refresh()

    # ── Vergleich: Gruppen-Logik ──────────────────────────────────────────────
    def _vg_listbox_laden(self):
        self.vg_listbox.delete(0, "end")
        for g in self.vergleiche:
            self.vg_listbox.insert("end", f"  {g['name']}")
        if self.vergleiche:
            idx = next((i for i,g in enumerate(self.vergleiche)
                        if g["id"] == self.vg_aktuelle_gruppe), 0)
            self.vg_listbox.selection_set(idx)
            self._vg_gruppe_waehlen()

    def _vg_gruppe_waehlen(self):
        sel = self.vg_listbox.curselection()
        if not sel or sel[0] >= len(self.vergleiche): return
        g = self.vergleiche[sel[0]]
        self.vg_aktuelle_gruppe = g["id"]
        self.vg_titel_lbl.config(text=g["name"])
        self.vg_ziel_lbl.config(text=f"Zielpreis: {g['zielpreis']:.2f} €")
        self._vg_tabelle_laden(g)

    def _vg_sort_klick(self, col):
        """Klick auf Spaltenüberschrift: aufsteigend/absteigend umschalten."""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        # Pfeil in Überschrift aktualisieren
        col_namen = {"shop":"Shop","url":"URL","preis":"Akt. Preis",
                     "diff":"Zielpreis","status":"Status","zuletzt":"Geprüft"}
        for c, name in col_namen.items():
            if c == self._sort_col:
                pfeil = " ↑" if self._sort_asc else " ↓"
            else:
                pfeil = " ↕"
            self.vg_tree.heading(c, text=name + pfeil)
        g = self._aktuelle_vg()
        if g:
            self._vg_tabelle_laden(g)

    def _vg_filter_anwenden(self):
        g = self._aktuelle_vg()
        if g:
            self._vg_tabelle_laden(g)

    def _vg_tabelle_laden(self, gruppe):
        for row in self.vg_tree.get_children():
            self.vg_tree.delete(row)
        shops = list(gruppe.get("shops", []))
        if not shops: return

        # Filter anwenden
        filter_text = getattr(self, "filter_var", None)
        if filter_text:
            ft = filter_text.get().lower().strip()
            if ft:
                shops = [s for s in shops if
                         ft in (s.get("shop_name") or s["shop"]).lower() or
                         ft in s.get("url","").lower()]

        # Sortierung nach angeklickter Spalte
        col   = getattr(self, "_sort_col", "preis")
        asc   = getattr(self, "_sort_asc", True)
        key_map = {
            "shop":    lambda s: (s.get("shop_name") or s["shop"]).lower(),
            "url":     lambda s: s.get("url","").lower(),
            "preis":   lambda s: s.get("preis") or 99999,
            "diff":    lambda s: gruppe.get("zielpreis", 0),
            "status":  lambda s: s.get("preis") or 0,
            "zuletzt": lambda s: s.get("zuletzt",""),
        }
        if col in key_map:
            shops = sorted(shops, key=key_map[col], reverse=not asc)
        preise = [s["preis"] for s in shops if s.get("preis")]
        bester = min(preise) if preise else None
        for s in shops:
            preis = s.get("preis")
            ziel  = gruppe["zielpreis"]
            preis_vorher = s.get("preis_vorher")
            trend        = s.get("preis_trend", "")
            # Preis-Anzeige mit Änderungs-Pfeil
            if preis and preis_vorher:
                diff  = preis - preis_vorher
                pfeil = "⬇" if diff < 0 else "⬆"
                p_str = f"{preis:.2f} €  {pfeil} {abs(diff):.2f}"
            else:
                p_str = f"{preis:.2f} €" if preis else "–"
            d_str    = f"{ziel:.2f} €"
            ist_best = preis and bester and preis == bester
            alarm    = preis and preis <= ziel
            noch     = f"noch {preis-ziel:.2f} € zu viel" if (preis and not alarm) else ""
            status   = "🏆 Günstigster Preis" if ist_best else ("🔔 Zielpreis erreicht!" if alarm else (f"⬇ {noch}" if preis else "⚠ Kein Preis"))
            # Tag: Preisänderung hat Vorrang vor normalem Status
            if trend == "gesunken":
                tag = "gesunken"
            elif trend == "gestiegen":
                tag = "gestiegen"
            else:
                tag = "best" if ist_best else ("alarm" if alarm else ("fehler" if not preis else "normal"))
            try:
                from urllib.parse import urlparse
                parsed = urlparse(s["url"])
                anzeige_url = parsed.netloc.replace("www.","") + (parsed.path[:30] if parsed.path != "/" else "")
            except:
                anzeige_url = s["url"][:50]
            self.vg_tree.insert("", "end", iid=s["id"],
                                values=(s.get("shop_name") or SHOPS.get(s["shop"], s["shop"]), anzeige_url,
                                        p_str, d_str, status, s.get("zuletzt","–")),
                                tags=(tag,))

    # ── Neue Gruppe Dialog ────────────────────────────────────────────────────
    def _vg_neu(self):
        dlg = tk.Toplevel(self)
        dlg.title("Neue Produktgruppe")
        dlg.geometry("560x440")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Produktname, Suchbegriff oder Geizhals-/Idealo-URL",
                 bg=BG, fg=TEXT2, font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(16,4))
        tk.Label(dlg, text="Tipp: Geizhals- oder Idealo-URL direkt einfügen → alle Shops werden automatisch erkannt",
                 bg=BG, fg=GRAU, font=("Segoe UI", 8)).pack(anchor="w", padx=20)

        such_row = tk.Frame(dlg, bg=BG)
        such_row.pack(fill="x", padx=20, pady=(6,0))
        e_such = ttk.Entry(such_row, font=("Segoe UI", 10))
        e_such.pack(side="left", fill="x", expand=True, ipady=5)
        e_such.focus()

        status_lbl = tk.Label(dlg, text="", bg=BG, fg=TEXT2, font=("Segoe UI", 9), anchor="w")
        status_lbl.pack(fill="x", padx=20, pady=(4,0))

        self._vg_shop_vars = {}
        canvas = tk.Canvas(dlg, bg=BG, height=170, highlightthickness=0)
        scroll = ttk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        inner  = tk.Frame(canvas, bg=BG)
        canvas.create_window((0,0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.pack(fill="both", expand=True, padx=20, pady=(4,0))
        scroll.pack(side="right", fill="y")

        ziel_row = tk.Frame(dlg, bg=BG)
        ziel_row.pack(fill="x", padx=20, pady=(10,0))
        tk.Label(ziel_row, text="Zielpreis (€)", bg=BG, fg=TEXT2, width=14,
                 anchor="w", font=("Segoe UI", 10)).pack(side="left")
        e_ziel = ttk.Entry(ziel_row)
        e_ziel.pack(side="left", fill="x", expand=True, ipady=5)
        tk.Label(ziel_row, text="  ← Alarm wenn ein Shop ≤ diesem Preis",
                 bg=BG, fg=GRAU, font=("Segoe UI", 9)).pack(side="left")

        gefunden = []
        gefundene_source_url = [""]  # Mutable container für thread

        def suchen(*_):
            eingabe = e_such.get().strip()
            if not eingabe: return
            for w in inner.winfo_children(): w.destroy()
            self._vg_shop_vars.clear()
            gefunden.clear()
            btn_such.config(state="disabled", text="  ⏳  ")
            ist_url = eingabe.startswith("http") and (
                "geizhals.de" in eingabe or "idealo.de" in eingabe)
            status_lbl.config(
                text="🔍  Lade Shops von URL..." if ist_url else "🔍  Suche auf Geizhals/Idealo...",
                fg=TEXT2)

            def _thread():
                if ist_url:
                    shops, name = shops_aus_url_laden(eingabe)
                    gefundene_source_url[0] = eingabe
                else:
                    result = alle_quellen_suchen(eingabe)
                    shops, name = result[0], result[1]
                    if len(result) > 2:
                        gefundene_source_url[0] = result[2]
                self.after(0, lambda: _fertig(shops, name))

            threading.Thread(target=_thread, daemon=True).start()

        def _fertig(shops, name):
            btn_such.config(state="normal", text="  🔍 Laden  ")
            if not shops:
                status_lbl.config(
                    text="⚠  Keine Shops gefunden. Tipp: Amazon-/Shop-URL direkt einfügen oder '+ URL manuell' nutzen.",
                    fg=GELB)
                return
            status_lbl.config(
                text=f"✅  {len(shops)} Shops gefunden — Haken entfernen zum Ausschließen:",
                fg=AKZENT)
            gefunden.extend(shops)
            # Produktname als Gruppenname vorschlagen
            if name and name != e_such.get().strip():
                e_such.delete(0, "end")
                e_such.insert(0, name)

            ctrl = tk.Frame(inner, bg=BG)
            ctrl.pack(fill="x", pady=(0,4))
            tk.Button(ctrl, text="Alle",  bg=BG3, fg=TEXT2, font=("Segoe UI",8), relief="flat", padx=6, pady=2,
                      command=lambda: [v.set(True)  for v,_ in self._vg_shop_vars.values()]).pack(side="left", padx=(0,4))
            tk.Button(ctrl, text="Keine", bg=BG3, fg=TEXT2, font=("Segoe UI",8), relief="flat", padx=6, pady=2,
                      command=lambda: [v.set(False) for v,_ in self._vg_shop_vars.values()]).pack(side="left")

            min_preis = min(s["preis"] for s in shops)
            for i, s in enumerate(shops):
                var = tk.BooleanVar(value=True)
                self._vg_shop_vars[str(i)] = (var, s)
                row_f = tk.Frame(inner, bg=BG)
                row_f.pack(fill="x", pady=1)
                tk.Checkbutton(row_f, variable=var, bg=BG, fg=TEXT,
                               activebackground=BG, selectcolor=BG3,
                               font=("Segoe UI",9)).pack(side="left")
                tk.Label(row_f, text=s["name"], bg=BG, fg=TEXT,
                         font=("Segoe UI",9,"bold"), width=24, anchor="w").pack(side="left")
                col = AKZENT if s["preis"] == min_preis else TEXT2
                tk.Label(row_f, text=f"{s['preis']:.2f} €", bg=BG, fg=col,
                         font=("Segoe UI",9,"bold"), width=9, anchor="e").pack(side="left")

            if not e_ziel.get():
                e_ziel.insert(0, f"{min_preis * 0.90:.2f}")
            e_ziel.focus()

        def speichern(*_):
            name = e_such.get().strip()
            # Falls URL eingegeben wurde und kein Produktname gefunden: ersten Shop-Namen nehmen
            if name.startswith("http"):
                name = ""
            if not name and gefunden:
                name = gefunden[0].get("name","")[:60]
            if not name:
                messagebox.showerror("Fehler", "Bitte Namen eingeben.", parent=dlg); return
            try:
                ziel = float(e_ziel.get().replace(",","."))
            except:
                messagebox.showerror("Fehler", "Bitte gültigen Zielpreis eingeben.", parent=dlg); return

            # Geizhals/Idealo URL merken für spätere Preisaktualisierungen
            eingabe_url = e_such.get().strip()
            if eingabe_url.startswith("http") and ("geizhals.de" in eingabe_url or "idealo.de" in eingabe_url):
                source_url = eingabe_url
            elif gefundene_source_url[0]:
                source_url = gefundene_source_url[0]
            else:
                source_url = ""
            log(f"Gruppe source_url: {source_url[:60]}" if source_url else "Gruppe ohne source_url")
            g = {"id": str(int(time.time()*1000)), "name": name, "zielpreis": ziel,
                 "shops": [], "alarm_gesendet": False, "source_url": source_url}
            # Shops erst mit Redirect-URL speichern, dann im Hintergrund auflösen
            shops_roh = []
            for sid, (var, s) in self._vg_shop_vars.items():
                if var.get():
                    shops_roh.append((sid, s))
                    g["shops"].append({
                        "id":        str(int(time.time()*1000)) + sid,
                        "url":       s["url"],  # Erst Redirect-URL
                        "shop":      s["shop_key"],
                        "shop_name": s.get("shop_name", s.get("name", s["shop_key"])),
                        "preis":     s["preis"],
                        "zuletzt":   datetime.now().strftime("%d.%m. %H:%M"),
                    })
            self.vergleiche.append(g)
            speichere_vergleiche(self.vergleiche)
            self.vg_aktuelle_gruppe = g["id"]
            self._vg_listbox_laden()
            dlg.destroy()

            # Im Hintergrund echte URLs auflösen
            def _urls_aufloesen():
                hat_redirects = any(
                    "geizhals.de/redir/" in s["url"] or "geizhals.at/redir/" in s["url"]
                    for s in g["shops"]
                )
                if not hat_redirects:
                    return
                gesamt = len([s for s in g["shops"] if "redir" in s.get("url","")])
                self.after(0, lambda: self.status_check_lbl.config(
                    text=f"🔗 Löse {gesamt} Shop-URLs auf (einmalig, dauert ca. {gesamt//3+1} Min.)...",
                    fg=TEXT2))

                # Produktseite einmal laden, alle Shop-Links in neuen Tabs öffnen
                url_map = redirects_aufloesen_via_produktseite(source_url, g["shops"])

                # Ergebnisse eintragen
                aufgeloest = 0
                for s in g["shops"]:
                    shop_name = s.get("shop_name") or s["shop"]
                    if shop_name in url_map:
                        s["url"]  = url_map[shop_name]
                        s["shop"] = _shop_aus_url(url_map[shop_name])
                        aufgeloest += 1

                speichere_vergleiche(self.vergleiche)
                self.after(0, lambda: self.status_check_lbl.config(
                    text=f"✅ {aufgeloest}/{gesamt} URLs aufgelöst", fg=AKZENT))
                ag = self._aktuelle_vg()
                if ag and ag["id"] == g["id"]:
                    self.after(0, lambda: self._vg_tabelle_laden(ag))

            threading.Thread(target=_urls_aufloesen, daemon=True).start()

        btn_such = self._btn(such_row, "  🔍 Laden  ", suchen, BG3, AKZENT)
        btn_such.pack(side="left", padx=(8,0), ipady=5)
        e_such.bind("<Return>", suchen)
        e_ziel.bind("<Return>", speichern)
        self._btn(dlg, "✅  Gruppe erstellen & tracken", speichern, AKZENT, "#000").pack(
            padx=20, pady=(10,12), fill="x", ipady=8)
        dlg.lift()
        dlg.focus_force()

    # ── Shop manuell hinzufügen ───────────────────────────────────────────────
    def _vg_shop_manuell(self):
        g = self._aktuelle_vg()
        if not g:
            messagebox.showinfo("Hinweis", "Bitte erst eine Gruppe auswählen."); return
        dlg = tk.Toplevel(self)
        dlg.title(f"Shop hinzufügen — {g['name']}")
        dlg.geometry("520x200")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Produkt-URL", bg=BG, fg=TEXT2,
                 font=("Segoe UI",10)).pack(anchor="w", padx=20, pady=(16,4))
        url_row = tk.Frame(dlg, bg=BG)
        url_row.pack(fill="x", padx=20)
        e_url = ttk.Entry(url_row)
        e_url.pack(side="left", fill="x", expand=True, ipady=5)
        e_url.focus()
        status_lbl = tk.Label(dlg, text="", bg=BG, fg=TEXT2, font=("Segoe UI",9), anchor="w")
        status_lbl.pack(fill="x", padx=20, pady=4)
        preis_var = tk.StringVar()

        def laden():
            url = e_url.get().strip()
            if not url.startswith("http"): return
            status_lbl.config(text="🔄  Preis wird geladen...", fg=TEXT2)
            def _t():
                shop = _shop_aus_url(url)
                p = preis_holen(url, shop)
                self.after(0, lambda: (
                    preis_var.set(f"{p:.2f}" if p else ""),
                    status_lbl.config(
                        text=f"✅ {p:.2f} €" if p else "⚠ Nicht gefunden — bitte manuell eintragen",
                        fg=AKZENT if p else GELB)
                ))
            threading.Thread(target=_t, daemon=True).start()

        self._btn(url_row, "🔍", laden, BG3, TEXT).pack(side="left", padx=(6,0), ipady=5)

        preis_row = tk.Frame(dlg, bg=BG)
        preis_row.pack(fill="x", padx=20, pady=4)
        tk.Label(preis_row, text="Preis (€)", bg=BG, fg=TEXT2, width=10, anchor="w",
                 font=("Segoe UI",10)).pack(side="left")
        ttk.Entry(preis_row, textvariable=preis_var, width=10).pack(side="left", ipady=4)

        def hinzufuegen(*_):
            url = e_url.get().strip()
            if not url.startswith("http"):
                messagebox.showerror("Fehler", "Ungültige URL.", parent=dlg); return
            try: preis = float(preis_var.get().replace(",","."))
            except: preis = None
            g["shops"].append({
                "id":      str(int(time.time()*1000)),
                "url":     url,
                "shop":    _shop_aus_url(url),
                "preis":   preis,
                "zuletzt": datetime.now().strftime("%d.%m. %H:%M"),
            })
            speichere_vergleiche(self.vergleiche)
            self._vg_tabelle_laden(g)
            dlg.destroy()

        e_url.bind("<Return>", lambda e: laden())
        self._btn(dlg, "➕  Hinzufügen", hinzufuegen, AKZENT, "#000").pack(
            padx=20, pady=(4,12), fill="x", ipady=7)
        dlg.lift(); dlg.focus_force()

    # ── Löschen ───────────────────────────────────────────────────────────────
    def _vg_shop_oeffnen(self):
        """Öffnet Shop-URL im Browser bei Doppelklick."""
        sel = self.vg_tree.selection()
        if not sel: return
        g = self._aktuelle_vg()
        if not g: return
        shop = next((s for s in g["shops"] if s["id"] == sel[0]), None)
        if not shop: return
        import webbrowser
        webbrowser.open(shop["url"])

    def _vg_loeschen(self):
        sel = self.vg_listbox.curselection()
        if not sel: return
        g = self.vergleiche[sel[0]]
        if messagebox.askyesno("Löschen", f"Gruppe '{g['name']}' löschen?"):
            self.vergleiche = [x for x in self.vergleiche if x["id"] != g["id"]]
            self.vg_aktuelle_gruppe = None
            speichere_vergleiche(self.vergleiche)
            self.vg_titel_lbl.config(text="← Gruppe auswählen oder neu erstellen")
            self.vg_ziel_lbl.config(text="")
            for row in self.vg_tree.get_children(): self.vg_tree.delete(row)
            self._vg_listbox_laden()

    def _vg_shop_loeschen(self):
        sel = self.vg_tree.selection()
        if not sel: return
        g = self._aktuelle_vg()
        if not g: return
        shop = next((s for s in g["shops"] if s["id"] == sel[0]), None)
        if not shop: return
        if messagebox.askyesno("Entfernen",
                               f"'{shop.get('shop_name') or SHOPS.get(shop['shop'], shop['shop'])}' aus Gruppe entfernen?"):
            g["shops"] = [s for s in g["shops"] if s["id"] != sel[0]]
            speichere_vergleiche(self.vergleiche)
            self._vg_tabelle_laden(g)

    # ── Preise prüfen ─────────────────────────────────────────────────────────
    def _vg_alle_pruefen(self):
        if not self.vergleiche:
            self.status_check_lbl.config(text="⚠ Keine Gruppen vorhanden", fg=GELB)
            return
        self.btn_pruefen.config(state="disabled", text="⏳  Prüfe...")
        self.status_check_lbl.config(text="Preise werden abgerufen...", fg=TEXT2)
        threading.Thread(target=self._vg_check_alle, daemon=True).start()

    def _vg_check_alle(self):
        log("Vergleich-Check gestartet")
        gesamt_shops = sum(len(g["shops"]) for g in self.vergleiche)
        geprueft = 0
        alarme = []
        alle_aenderungen = []  # {gruppe_name, gruppe_ziel, shops: [...]}
        geaenderte_shops = []  # Shops mit Preisänderung für aktuelle Gruppe

        for g in self.vergleiche:
            self.after(0, lambda name=g["name"]: self.status_check_lbl.config(
                text=f"🔄  Prüfe: {name[:30]}...", fg=TEXT2))

            source_url = g.get("source_url", "")
            ts = datetime.now().strftime("%d.%m. %H:%M")

            if source_url and ("geizhals.de" in source_url or "idealo.de" in source_url):
                # ── Geizhals/Idealo: Produktseite komplett neu laden
                log(f"  Lade Produktseite: {source_url[:60]}")
                neue_shops, _ = shops_aus_url_laden(source_url, max_shops=999)
                if neue_shops:
                    # Preis-Map: Name (lowercase) → Preis
                    preis_map = {s["name"].lower().strip(): s["preis"] for s in neue_shops}
                    log(f"  Gefunden: {list(preis_map.keys())[:5]}...")
                    for s in g["shops"]:
                        shop_name = (s.get("shop_name") or s["shop"]).lower().strip()
                        # 1. Exakter Match
                        preis = preis_map.get(shop_name)
                        # 2. Teilstring-Match
                        if not preis:
                            for key, val in preis_map.items():
                                if key in shop_name or shop_name in key:
                                    preis = val
                                    break
                        # 3. Fuzzy: ersten 5 Zeichen vergleichen
                        if not preis and len(shop_name) >= 4:
                            prefix = shop_name[:5]
                            for key, val in preis_map.items():
                                if key.startswith(prefix) or key[:5] == prefix:
                                    preis = val
                                    break
                        name_anzeige = s.get("shop_name") or s["shop"]
                        s["zuletzt"] = ts
                        if preis:
                            preis_alt = s.get("preis")
                            # Preisänderung erkennen (mehr als 0.01€ Unterschied)
                            if preis_alt and abs(preis - preis_alt) > 0.01:
                                # Echte Shop-URL ermitteln (nicht Geizhals-Redirect)
                                shop_url = s.get("url_real") or s["url"]
                                if "geizhals.de/redir/" in shop_url or "geizhals.at/redir/" in shop_url:
                                    # Redirect per requests auflösen
                                    try:
                                        r = requests.get(shop_url, headers=HEADERS,
                                                         timeout=10, allow_redirects=True, stream=True)
                                        aufgeloest = r.url
                                        r.close()
                                        if "geizhals" not in aufgeloest:
                                            shop_url = aufgeloest
                                            s["url_real"] = aufgeloest
                                    except:
                                        pass
                                geaenderte_shops.append({
                                    "shop_name": name_anzeige,
                                    "url":       shop_url,
                                    "preis_alt": preis_alt,
                                    "preis_neu": preis,
                                })
                                # Änderung im Shop-Objekt merken für Tabellenanzeige
                                s["preis_vorher"] = preis_alt
                                s["preis_trend"]  = "gesunken" if preis < preis_alt else "gestiegen"
                            else:
                                # Keine Änderung: alten Trend nach 1 Prüfzyklus löschen
                                s.pop("preis_vorher", None)
                                s.pop("preis_trend",  None)
                            s["preis"] = preis
                            # Preisverlauf: jeden Check speichern (max 1000 Einträge)
                            verlauf = s.get("verlauf", [])
                            jetzt = datetime.now().strftime("%Y-%m-%d %H:%M")
                            verlauf.append({"datum": jetzt, "preis": preis})
                            verlauf = verlauf[-1000:]
                            s["verlauf"] = verlauf
                            log(f"  {name_anzeige}: {preis:.2f} € ✓")
                        else:
                            log(f"  {name_anzeige}: nicht gefunden (gespeichert: '{shop_name}')")
                        geprueft += 1

                    # Neue Shops hinzufügen + nicht mehr gelistete entfernen
                    geizhals_namen = {ns["name"].lower() for ns in neue_shops}
                    bestehende_namen = {(s.get("shop_name") or s["shop"]).lower() for s in g["shops"]}

                    # Neue Shops hinzufügen
                    for ns in neue_shops:
                        if ns["name"].lower() not in bestehende_namen:
                            # Redirect durch Geizhals-Produktseite ersetzen
                            shop_url = source_url if ("geizhals.de/redir/" in ns["url"] or "geizhals.at/redir/" in ns["url"]) else ns["url"]
                            g["shops"].append({
                                "id":        str(int(time.time()*1000)) + ns["name"][:5],
                                "url":       shop_url,
                                "url_redir": ns["url"],
                                "shop":      ns["shop_key"],
                                "shop_name": ns["name"],
                                "preis":     ns["preis"],
                                "zuletzt":   ts,
                            })
                            log(f"  Neuer Shop hinzugefügt: {ns['name']} ({ns['preis']:.2f} €)")

                    # Nicht mehr gelistete Shops entfernen
                    vorher = len(g["shops"])
                    g["shops"] = [
                        s for s in g["shops"]
                        if (s.get("shop_name") or s["shop"]).lower() in geizhals_namen
                    ]
                    entfernt = vorher - len(g["shops"])
                    if entfernt > 0:
                        log(f"  {entfernt} Shop(s) nicht mehr auf Geizhals — entfernt")
                else:
                    log(f"  Produktseite konnte nicht geladen werden")
                    geprueft += len(g["shops"])
            else:
                # ── Keine Geizhals-URL: Einzelne Shop-URLs prüfen
                for s in g["shops"]:
                    shop_anzeige = s.get("shop_name") or s["shop"]
                    self.after(0, lambda n=shop_anzeige, i=geprueft, t=gesamt_shops:
                        self.status_check_lbl.config(text=f"🔄  {n} ({i+1}/{t})", fg=TEXT2))
                    p = preis_holen(s["url"], s["shop"])
                    log(f"  {shop_anzeige}: {p:.2f} € ✓" if p else f"  {shop_anzeige}: kein Preis")
                    s["zuletzt"] = ts  # immer aktualisieren
                    if p:
                        s["preis"] = p
                    geprueft += 1

            # Tabelle live aktualisieren
            ag = self._aktuelle_vg()
            if ag and ag["id"] == g["id"]:
                self.after(0, lambda gg=g: self._vg_tabelle_laden(gg))

            preise = [s["preis"] for s in g["shops"] if s.get("preis")]
            if preise:
                bester = min(preise)
                bester_shop = next((s.get("shop_name") or SHOPS.get(s["shop"],s["shop"])
                                    for s in g["shops"] if s.get("preis") == bester), "")
                log(f"  {g['name']}: {bester:.2f} € bei {bester_shop}")

                # Zielpreis-Alarm (Toast bleibt, Mail kommt in Zusammenfassung)
                if bester <= g["zielpreis"] and not g.get("alarm_gesendet"):
                    g["alarm_gesendet"] = True
                    alarme.append({"name": g["name"], "bester": bester, "shop": bester_shop})
                    toast("🏆 Preisvergleich-Alarm!",
                          f"{g['name']}: {bester:.2f} € bei {bester_shop}")
                elif bester > g["zielpreis"]:
                    g["alarm_gesendet"] = False

                # Änderungen sammeln für Gesamt-Mail am Ende
                if geaenderte_shops:
                    gesunken  = len([s for s in geaenderte_shops if s["preis_neu"] < s["preis_alt"]])
                    gestiegen = len([s for s in geaenderte_shops if s["preis_neu"] > s["preis_alt"]])
                    log(f"  Preisänderungen: {gesunken} gesunken, {gestiegen} gestiegen")
                    # Zielpreis-Info pro Shop hinzufügen
                    for s in geaenderte_shops:
                        s["zielpreis"]       = g["zielpreis"]
                        s["ziel_erreicht"]   = s["preis_neu"] <= g["zielpreis"]
                    alle_aenderungen.append({
                        "gruppe_name": g["name"],
                        "zielpreis":   g["zielpreis"],
                        "shops":       list(geaenderte_shops),
                    })

            geaenderte_shops = []  # Reset für nächste Gruppe

        speichere_vergleiche(self.vergleiche)
        ts = datetime.now().strftime("%H:%M")

        # Eine zusammengefasste Mail für alle Änderungen + Alarme
        if self.config_data.get("email_absender") and (alle_aenderungen or alarme):
            threading.Thread(
                target=email_zusammenfassung,
                args=(self.config_data, alle_aenderungen, alarme),
                daemon=True
            ).start()

        def _fertig():
            self.btn_pruefen.config(state="normal", text="🔄  Alle prüfen")
            if alarme:
                self.status_check_lbl.config(
                    text=f"🔔 Alarm! {alarme[0]['name']}: {alarme[0]['bester']:.2f} €", fg=AKZENT)
            else:
                self.status_check_lbl.config(
                    text=f"✅ {geprueft} Preise geprüft — {ts} Uhr", fg=AKZENT)
            self._vg_listbox_laden()
            ag = self._aktuelle_vg()
            if ag:
                self._vg_tabelle_laden(ag)
            self._log_refresh()

        self.after(0, _fertig)
        # Gruppen ohne source_url hinweisen
        ohne_quelle = [g["name"] for g in self.vergleiche if not g.get("source_url")]
        if ohne_quelle:
            log(f"  Hinweis: {len(ohne_quelle)} Gruppe(n) ohne Geizhals-URL — Gruppe löschen und neu anlegen für automatische Updates")
        log(f"Vergleich-Check abgeschlossen ({geprueft} Shops)")

    # ── Einstellungen ─────────────────────────────────────────────────────────
    def _cfg_speichern(self):
        self.config_data.update({
            "email_absender":   self.v_abs.get().strip(),
            "email_passwort":   self.v_pw.get(),
            "email_empfaenger": self.v_emp.get().strip(),
            "smtp_server":      self.v_smtp.get().strip(),
            "smtp_port":        int(self.v_port.get() or 587),
            "intervall":        max(1, min(24, int(self.v_int.get() or 6))),
        })
        speichere_config(self.config_data)
        messagebox.showinfo("Gespeichert", "Einstellungen wurden gespeichert.")

    def _test_email(self):
        if not self.config_data.get("email_absender"):
            messagebox.showerror("Fehler", "Bitte erst Einstellungen speichern."); return
        ok = email_senden(self.config_data, {"name":"Test","shops":[]}, 99.99, "Testshop")
        if ok:
            messagebox.showinfo("Erfolg", "Test-E-Mail wurde gesendet!")
        else:
            messagebox.showerror("Fehler", "E-Mail konnte nicht gesendet werden.")

    # ── Autostart & Tray ─────────────────────────────────────────────────────
    def _autostart_toggle(self):
        aktiv = self.v_autostart.get()
        if autostart_setzen(aktiv):
            msg = "Autostart aktiviert." if aktiv else "Autostart deaktiviert."
            self.status_check_lbl.config(text=f"✅ {msg}", fg=AKZENT)
        else:
            messagebox.showerror("Fehler", "Autostart konnte nicht gesetzt werden.")
            self.v_autostart.set(not aktiv)

    def _tray_toggle(self):
        self.config_data["minimize_to_tray"] = self.v_tray.get()
        speichere_config(self.config_data)

    def _fenster_schliessen(self):
        """X-Button: in Tray minimieren oder beenden je nach Einstellung."""
        if self.config_data.get("minimize_to_tray", True) and TRAY_OK:
            self.withdraw()  # Fenster verstecken
            self._tray_starten()
        else:
            self._beenden()

    def _tray_starten(self):
        if self._tray_icon:
            return
        if not TRAY_OK:
            return

        def zeigen(icon, item):
            icon.stop()
            self._tray_icon = None
            self.after(0, self.deiconify)
            self.after(0, self.lift)

        def beenden(icon, item):
            icon.stop()
            self._tray_icon = None
            self.after(0, self._beenden)

        def pruefen(icon, item):
            self.after(0, self._vg_alle_pruefen)

        menu = pystray.Menu(
            TrayItem("🔔 Preis-Alarm Tracker", zeigen, default=True),
            TrayItem("🔄 Jetzt prüfen",         pruefen),
            pystray.Menu.SEPARATOR,
            TrayItem("❌ Beenden",               beenden),
        )
        img = tray_icon_erstellen()
        self._tray_icon = pystray.Icon("PreisAlarm", img, "Preis-Alarm Tracker", menu)
        self._tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        self._tray_thread.start()

    def _beenden(self):
        if self._tray_icon:
            try: self._tray_icon.stop()
            except: pass
        self.destroy()

    def _auto_check_starten(self):
        """Startet automatische Preisprüfung — sofort beim Start, dann alle X Stunden."""
        def check_und_planen():
            if self.vergleiche:
                threading.Thread(target=self._vg_check_alle, daemon=True).start()
            # Intervall neu einlesen damit Änderungen in Einstellungen wirken
            intervall = self.config_data.get("intervall", 6) * 3600 * 1000
            self.after(intervall, check_und_planen)
        # Sofort beim Start prüfen
        if self.vergleiche:
            self.after(5000, lambda: threading.Thread(target=self._vg_check_alle, daemon=True).start())
        # Ersten Intervall starten
        intervall = self.config_data.get("intervall", 6) * 3600 * 1000
        self.after(intervall, check_und_planen)

    # ── Preisverlauf Chart ───────────────────────────────────────────────────
    def _vg_chart_zeigen(self):
        g = self._aktuelle_vg()
        if not g:
            messagebox.showinfo("Hinweis", "Bitte erst eine Gruppe auswählen.")
            return

        # Preisverlauf: pro Zeitpunkt günstigsten UND Durchschnittspreis sammeln
        tages_preise = {}   # datum -> günstigster Preis
        tages_summen = {}   # datum -> [alle Preise] für Durchschnitt
        for s in g["shops"]:
            for eintrag in s.get("verlauf", []):
                datum = eintrag["datum"][:16]
                preis = eintrag["preis"]
                if datum not in tages_preise or preis < tages_preise[datum]:
                    tages_preise[datum] = preis
                tages_summen.setdefault(datum, []).append(preis)

        if len(tages_preise) < 1:
            messagebox.showinfo("Hinweis",
                "Noch keine Daten.\nBitte erst 'Alle prüfen' ausführen.")
            return
        if len(tages_preise) < 2:
            # Nur ein Datenpunkt — trotzdem anzeigen
            erster = list(tages_preise.items())[0]
            tages_preise[erster[0] + " (2)"] = erster[1]  # Doppelten Punkt für Linie

        # Sortiert nach Datum/Uhrzeit
        punkte    = sorted(tages_preise.items())
        daten     = [p[0][:16] for p in punkte]
        preise    = [p[1] for p in punkte]
        avg_preise = [round(sum(tages_summen.get(d, [p])) / len(tages_summen.get(d, [p])), 2)
                      for d, p in punkte]
        ziel    = g["zielpreis"]

        # Chart-Fenster
        dlg = tk.Toplevel(self)
        dlg.title(f"Preisverlauf — {g['name']}")
        dlg.geometry("750x460")
        dlg.configure(bg=BG)
        dlg.resizable(True, True)

        # Zeitraum-Buttons
        zeitraum_bar = tk.Frame(dlg, bg=BG)
        zeitraum_bar.pack(fill="x", padx=16, pady=(12,0))
        zeitraum_var = tk.StringVar(value="Alles")

        def zeitraum_filtern():
            from datetime import datetime as _dt, timedelta
            zr = zeitraum_var.get()
            jetzt = _dt.now()
            if zr == "Tag":
                grenze = (jetzt - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
            elif zr == "Woche":
                grenze = (jetzt - timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M")
            elif zr == "Monat":
                grenze = (jetzt - timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
            else:
                grenze = ""
            if grenze:
                gefiltert = {d: p for d, p in tages_preise.items() if d >= grenze}
                gefiltert_avg = {d: tages_summen[d] for d in gefiltert if d in tages_summen}
            else:
                gefiltert = tages_preise
                gefiltert_avg = tages_summen
            if not gefiltert:
                return
            pkt = sorted(gefiltert.items())
            return pkt, gefiltert_avg

        tk.Label(zeitraum_bar, text="Zeitraum:", bg=BG, fg=TEXT2,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0,8))
        for zr in ["Tag", "Woche", "Monat", "Alles"]:
            tk.Radiobutton(zeitraum_bar, text=zr, variable=zeitraum_var, value=zr,
                           bg=BG, fg=TEXT, activebackground=BG, selectcolor=BG3,
                           font=("Segoe UI", 9),
                           command=lambda: canvas.event_generate("<Configure>")
                           ).pack(side="left", padx=4)

        # Canvas für Chart
        canvas = tk.Canvas(dlg, bg=BG2, highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=16, pady=(8,16))

        def zeichnen(event=None):
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 50 or h < 50:
                return

            # Zeitraum-Filter anwenden
            from datetime import datetime as _dt, timedelta
            zr = zeitraum_var.get()
            jetzt = _dt.now()
            if zr == "Tag":
                grenze = (jetzt - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
            elif zr == "Woche":
                grenze = (jetzt - timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M")
            elif zr == "Monat":
                grenze = (jetzt - timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
            else:
                grenze = ""
            gefiltertes_dict = {d: p for d, p in tages_preise.items()
                                if not grenze or d >= grenze}
            if not gefiltertes_dict:
                canvas.create_text(w//2, h//2, text="Keine Daten für diesen Zeitraum",
                                   fill=TEXT2, font=("Segoe UI", 11))
                return
            pkt_gefiltert = sorted(gefiltertes_dict.items())
            daten   = [p[0][:16] for p in pkt_gefiltert]
            preise  = [p[1] for p in pkt_gefiltert]
            avg_preise = [round(sum(tages_summen.get(d, [p])) /
                               len(tages_summen.get(d, [p])), 2)
                          for d, p in pkt_gefiltert]

            pad_l, pad_r, pad_t, pad_b = 70, 90, 75, 50
            chart_w = w - pad_l - pad_r
            chart_h = h - pad_t - pad_b

            alle_werte = preise + avg_preise + [ziel]
            min_p = min(alle_werte) * 0.97
            max_p = max(alle_werte) * 1.03

            def cx(i):
                return pad_l + (i / max(len(preise)-1, 1)) * chart_w

            def cy(p):
                return pad_t + (1 - (p - min_p) / (max_p - min_p)) * chart_h

            # Farblegende oben links
            legende = [
                ("Günstigster Preis", TEXT2,    False),
                ("Ø Durchschnitt",    "#60a5fa", True),
                ("Zielpreis",         AKZENT,    True),
            ]
            lx = pad_l
            for i, (ltext, lfarbe, gestrichelt) in enumerate(legende):
                ly = 14 + i * 18
                dash = (5,3) if gestrichelt else None
                kw = {"fill": lfarbe, "width": 2}
                if dash: kw["dash"] = dash
                canvas.create_line(lx, ly, lx+30, ly, **kw)
                canvas.create_text(lx+34, ly, text=ltext, fill=lfarbe,
                                   font=("Segoe UI", 8), anchor="w")

            # Info-Zeile oben rechts
            info = (f"Messpunkte: {len(preise)}   "
                    f"Min: {min(preise):.2f}€   "
                    f"Ø Akt: {avg_preise[-1]:.2f}€   "
                    f"Günstigster: {preise[-1]:.2f}€")
            canvas.create_text(w - pad_r + 80, 14, text=info,
                               fill=TEXT2, font=("Segoe UI", 8), anchor="e")

            # Gitternetz
            for step in range(5):
                py = pad_t + step * chart_h / 4
                preis_val = max_p - step * (max_p - min_p) / 4
                canvas.create_line(pad_l, py, pad_l + chart_w, py,
                                   fill="#2a2a2a", dash=(4,4))
                canvas.create_text(pad_l - 6, py, text=f"{preis_val:.0f}€",
                                   fill=TEXT2, font=("Segoe UI", 8), anchor="e")

            # Zielpreis-Linie
            yz = cy(ziel)
            canvas.create_line(pad_l, yz, pad_l + chart_w, yz,
                               fill=AKZENT, dash=(6,3), width=1.5)
            canvas.create_text(pad_l + chart_w + 6, yz,
                               text=f"Ziel {ziel:.0f}€",
                               fill=AKZENT, font=("Segoe UI", 8), anchor="w")

            # Durchschnittslinie
            avg_xy = [(cx(i), cy(avg_preise[i])) for i in range(len(avg_preise))]
            if len(avg_xy) >= 2:
                for i in range(len(avg_xy)-1):
                    canvas.create_line(avg_xy[i][0], avg_xy[i][1],
                                       avg_xy[i+1][0], avg_xy[i+1][1],
                                       fill="#60a5fa", width=2, dash=(5,3))

            # Günstigster-Preis-Linie
            punkte_xy = [(cx(i), cy(p)) for i, p in enumerate(preise)]
            if len(punkte_xy) >= 2:
                for i in range(len(punkte_xy)-1):
                    farbe = AKZENT if preise[i] <= ziel else TEXT2
                    canvas.create_line(punkte_xy[i][0], punkte_xy[i][1],
                                       punkte_xy[i+1][0], punkte_xy[i+1][1],
                                       fill=farbe, width=2.5)

            # Datenpunkte mit Labels
            for i, (px, py2) in enumerate(punkte_xy):
                farbe = AKZENT if preise[i] <= ziel else "#378ADD"
                canvas.create_oval(px-4, py2-4, px+4, py2+4, fill=farbe, outline="")
                if i == 0 or i == len(preise)-1 or preise[i] == min(preise):
                    anker = "sw" if i == len(preise)-1 else "se"
                    canvas.create_text(px, py2-8, text=f"{preise[i]:.0f}€",
                                       fill=TEXT, font=("Segoe UI", 8, "bold"), anchor=anker)

            # X-Achse
            max_labels = max(2, min(len(daten), chart_w // 70))
            schritt = max(1, len(daten) // max_labels)
            for i in range(0, len(daten), schritt):
                px = cx(i)
                label = daten[i][5:]  # "03-15 10:49"
                canvas.create_text(px, pad_t + chart_h + 14, text=label,
                                   fill=TEXT2, font=("Segoe UI", 8), anchor="n")
                canvas.create_line(px, pad_t + chart_h, px, pad_t + chart_h + 5, fill=BORDER)

            # Achsenlinien
            canvas.create_line(pad_l, pad_t, pad_l, pad_t + chart_h, fill=BORDER, width=1)
            canvas.create_line(pad_l, pad_t + chart_h, pad_l + chart_w,
                               pad_t + chart_h, fill=BORDER, width=1)

        canvas.bind("<Configure>", zeichnen)
        dlg.after(100, zeichnen)

    # ── Log ───────────────────────────────────────────────────────────────────
    def _log_refresh(self):
        try:
            inhalt = open(LOG_DATEI, "r", encoding="utf-8").read() if LOG_DATEI.exists() else ""
            self.log_box.config(state="normal")
            self.log_box.delete("1.0", "end")
            self.log_box.insert("end", inhalt)
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        except:
            pass

    def _log_leeren(self):
        open(LOG_DATEI, "w").close()
        self._log_refresh()


if __name__ == "__main__":
    # pystray + Pillow installieren falls fehlt
    try:
        import pystray
        from PIL import Image
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install",
                               "pystray", "pillow", "--quiet"])
    app = PreisAlarmApp()
    app.mainloop()
