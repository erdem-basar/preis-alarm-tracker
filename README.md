# 🔔 Price Alert Tracker

Automatic price comparison for Windows — monitors shops via Geizhals and sends email notifications when your target price is reached.

## Features

- 🔍 Automatic shop search via Geizhals (search term or direct URL)
- 📊 Price comparison across all available shops
- 🔔 Email notification for price changes and target price alerts
- 📈 Price history chart (Day / Week / Month / All)
- 🖥 System tray — runs silently in the background
- ⚡ Start with Windows (autostart)
- 🔄 Automatic price check every X hours

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
- SMTP server (default: GMX `mail.gmx.net:587`)
- Check interval (default: 6 hours)
- Enable autostart

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

1. **New Group** — enter a product name or Geizhals URL → shops are loaded automatically
2. **Set Target Price** → app notifies you when a shop drops below this price
3. **Check All** — manually update all prices
4. View price history via the **📈 Price History** button
5. Double-click a shop row to open it in your browser

## How It Works

The app uses Selenium (headless Chrome) to load Geizhals product pages and extract all shop offers including prices. Price checks run automatically in the background at your configured interval.

## Notes

- `config.json` (email credentials) and `vergleich.json` (your product groups) are **not** included in the repository — stored locally in `%APPDATA%\PreisAlarm\`
- Currently supports Geizhals (DE/AT/CH/EU) as the price comparison source

## License

MIT License — free to use and modify
