# 🔔 Price Alert Tracker

Automatic price comparison for Windows — monitors shops via Geizhals, PriceSpy and Amazon, and sends email notifications when your target price is reached.

![Version](https://img.shields.io/badge/version-1.2.0-green)
![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-yellow)

## Features

- 🔍 Automatic shop search via Geizhals, PriceSpy and Amazon (search term or direct URL)
- 📊 Price comparison across all available shops
- 🔔 Email notification for price changes and target price alerts
- 📈 Price history chart (Day / Week / Month / All)
- 📊 Price statistics — all-time low/high, averages, best shop
- 🌍 Multilingual — English & Deutsch
- 🖥 System tray — runs silently in the background
- ⚡ Start with Windows (autostart)
- 🔄 Automatic price check every X hours
- 🆕 Auto-update notifications from GitHub

## Requirements

- Windows 10/11
- Python 3.9+ (installed automatically if not present)
- Google Chrome

## Installation

1. Clone the repository:
```
git clone https://github.com/erdem-basar/preis-alarm-tracker.git
```

2. Run `setup_und_build.bat` as Administrator — installs all dependencies automatically

3. Run `starten.bat` to start the app

## Configuration

On first launch, go to the **⚙ Settings** tab:
- Email (sender, password, recipient)
- Select your email provider from the **SMTP presets** — click to apply automatically
- Check interval (default: 6 hours)
- Language: English or Deutsch
- Enable autostart

## Supported Email Providers

Click any preset in the Settings tab to auto-fill the SMTP server and port:

| Provider | Email Addresses |
|---|---|
| GMX | @gmx.de / @gmx.net |
| Web.de | @web.de |
| Freenet | @freenet.de |
| T-Online | @t-online.de |
| 1&1 / IONOS | @1und1.de / @ionos.de |
| Outlook / Live | @outlook.com / @live.de / @hotmail.com |
| Gmail | @gmail.com *(App Password required)* |
| Yahoo | @yahoo.com / @yahoo.de |
| iCloud | @icloud.com / @me.com |
| Posteo | @posteo.de |
| Mailbox.org | @mailbox.org |

## Dependencies

```
requests
beautifulsoup4
selenium
webdriver-manager
pystray
pillow
win10toast
```

## Usage

1. **New Group** — enter a product name or paste a URL → shops are loaded automatically
2. **Set Target Price** → app notifies you when a shop drops below this price
3. **Check All** — manually update all prices
4. **📊 Statistics** — view all-time lows, averages and best shops per group
5. **📈 Price History** — view price chart over time (Day / Week / Month / All)
6. Double-click a shop row to open it in your browser

## Supported Price Sources

| Source | Region | URL Example |
|---|---|---|
| **Geizhals.de** | Germany | `geizhals.de/product-a123.html` |
| **Geizhals.eu** | Europe (DE/AT/CH/EU/UK/PL) | `geizhals.eu/product-a123.html` |
| **Geizhals.at** | Austria | `geizhals.at/product-a123.html` |
| **PriceSpy UK** | United Kingdom | `pricespy.co.uk/product.php?p=123` |
| **Amazon.de** | Germany | `amazon.de/dp/ASIN` or search term |

Simply paste any supported URL or enter a search term — the app finds all available shops automatically. If Geizhals finds no results, Amazon.de is used as fallback.

## How It Works

The app uses Selenium (Chrome) to load product pages and extract all shop offers including prices. Price checks run automatically in the background at your configured interval. When prices change, a single summary email is sent listing all changes with old price, new price, and a direct link to the shop.

## Updates

The app checks GitHub for new releases on startup. When an update is available, a notification appears in the title bar — click it to open the releases page.

## Notes

- `config.json` (email credentials) and `vergleich.json` (your product groups) are **not** included in the repository — stored locally in `%APPDATA%\PreisAlarm\`
- Geizhals prices are in **€ (EUR)**, PriceSpy prices are in **£ (GBP)**

## License

MIT License — free to use and modify
