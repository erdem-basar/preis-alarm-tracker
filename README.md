# 🔔 Preis-Alarm Tracker

Automatischer Preisvergleich für Windows — überwacht Shops via Geizhals und benachrichtigt per E-Mail wenn dein Zielpreis erreicht wird.

## Features

- 🔍 Automatische Shop-Suche via Geizhals (Suchbegriff oder direkte URL)
- 📊 Preisvergleich über alle verfügbaren Shops
- 🔔 E-Mail-Benachrichtigung bei Preisänderungen und Zielpreis-Alarm
- 📈 Preisverlauf-Chart (Tag / Woche / Monat / Alles)
- 🖥 System-Tray — läuft unsichtbar im Hintergrund
- ⚡ Autostart mit Windows
- 🔄 Automatische Prüfung alle X Stunden

## Voraussetzungen

- Windows 10/11
- Python 3.9+ (wird automatisch installiert falls nicht vorhanden)
- Google Chrome

## Installation

1. Repository herunterladen oder klonen:
```
git clone https://github.com/DEIN-NAME/preis-alarm-tracker.git
```

2. `setup_und_build.bat` als Administrator ausführen — installiert alle Abhängigkeiten automatisch

3. `starten.bat` ausführen

## Konfiguration

Beim ersten Start im Tab **⚙ Einstellungen**:
- E-Mail (Absender, Passwort, Empfänger)
- SMTP-Server (Standard: GMX `mail.gmx.net:587`)
- Prüf-Intervall (Standard: 6 Stunden)
- Autostart aktivieren

## Abhängigkeiten

```
requests
beautifulsoup4
selenium
webdriver-manager
pystray
pillow
win10toast
```

## Nutzung

1. **Neue Gruppe** — Produktname oder Geizhals-URL eingeben → Shops werden automatisch geladen
2. **Zielpreis** setzen → App benachrichtigt wenn ein Shop diesen Preis unterschreitet
3. **Alle prüfen** — manuell alle Preise aktualisieren
4. Preisverlauf über **📈 Preisverlauf** Button ansehen

## Hinweise

- `config.json` (E-Mail-Daten) und `vergleich.json` (deine Produktgruppen) werden **nicht** ins Repository hochgeladen
- Alle Daten werden lokal in `%APPDATA%\PreisAlarm\` gespeichert

## Lizenz

MIT License — frei verwendbar und veränderbar
