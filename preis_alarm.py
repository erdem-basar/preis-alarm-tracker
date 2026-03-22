"""
Price Alert Tracker v3.0
Price comparison across multiple shops via Geizhals URL or search term.
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

# ── Translations ─────────────────────────────────────────────────────────────
LANGUAGES = {
    "en": "🇬🇧 English",
    "de": "🇩🇪 Deutsch",
    "fr": "🇫🇷 Français",
    "es": "🇪🇸 Español",
    "it": "🇮🇹 Italiano",
    "nl": "🇳🇱 Nederlands",
    "pl": "🇵🇱 Polski",
    "pt": "🇵🇹 Português",
    "tr": "🇹🇷 Türkçe",
    "ru": "🇷🇺 Русский",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
    "ar": "🇸🇦 العربية",
}

TRANSLATIONS = {
    "en": {
        "app_title": "Price Alert Tracker", "tab_compare": "  ⚖ Price Comparison  ",
        "tab_settings": "  ⚙ Settings  ", "tab_log": "  📄 Log  ",
        "new_group": "＋  New Group", "check_all": "↺  Check All",
        "checking": "⏳  Checking...", "delete": "🗑  Delete",
        "price_history": "📈 Price History", "add_url": "+ URL",
        "product_groups": "GROUPS", "select_group": "Select a group or create new",
        "best_price": "🏆 Best Price", "target_reached": "🔔 Target reached!",
        "no_price": "⚠ No Price", "still_too_much": "still {diff} too much",
        "save": "💾  Save", "test_email": "✉  Test Email",
        "settings_saved": "Settings saved successfully.", "email_sent": "Test email sent!",
        "autostart_on": "Autostart enabled.", "autostart_off": "Autostart disabled.",
        "start_windows": "Start with Windows (Autostart)",
        "minimize_tray": "Minimize to system tray on close",
        "smtp_presets": "ℹ  SMTP Presets  —  click to apply",
        "interval_label": "Every X Hours", "interval_hint": " hours (1–24)",
        "sender_email": "Sender Email", "password": "Password",
        "recipient_email": "Recipient Email", "clear_log": "🗑  Clear Log",
        "search_hint": "Product name, search term or Geizhals/PriceSpy URL",
        "url_tip": "Tip: Paste a Geizhals URL (.de/.eu) or PriceSpy URL",
        "target_price": "Target Price", "create_group": "✅  Create group & track",
        "all_btn": "All", "none_btn": "None", "language": "Language",
        "buy_now": "🟢 BUY NOW", "wait": "⏳ WAIT", "monitor": "⏳ MONITOR",
        "buy_soon": "🔴 BUY SOON — Price rising", "almost": "🟡 ALMOST THERE",
        "wait_falling": "🟡 WAIT — Price falling",
        "ai_title": "Smart Price Analysis",
        "recommendation": "RECOMMENDATION",
        "price_analysis": "Price Analysis",
        "trend_volatility": "Trend & Volatility",
        "insight": "Insight",
        "cur_best": "Current best price",
        "your_target": "Your target",
        "dist_target": "Distance to target",
        "vs_alltime": "vs. all-time low",
        "price_trend": "Price trend",
        "price_stab": "Price stability",
        "data_points": "Data points",
        "seasonal": "Seasonal pattern",
        "price_spread": "Price spread (shops)",
        "close": "Close",
        "shops_tracked": "Shops tracked",
        "target_price_lbl": "Target price",
        "cur_avg": "Current avg price",
        "cur_worst": "Current worst price",
        "alltime_low": "All-time lowest",
        "alltime_high": "All-time highest",
        "alltime_avg": "All-time average",
        "total_points": "Total data points",
        "cheapest_shop": "Cheapest shop",
        "expensive_shop": "Most expensive shop",
        "max_savings": "Max savings possible",
        "period": "Period:",
        "day": "Day",
        "week": "Week",
        "month": "Month",
        "all": "All",
        "subtitle": "Smart price monitoring",
        "email_config": "Email Configuration",
        "check_interval": "Check Interval",
        "above_target_track": "Price is {pct}% above target — keep tracking",
        "above_target_wait": "Price is {pct}% above target — set an alert and be patient",
        "above_target_falling": "Price is falling and {pct}% above target — likely to reach it soon",
        "price_rising_grund": "Price is rising — buy before it gets more expensive",
        "at_target": "Price is at or below your target",
        "almost_grund": "Only {pct}% above your target — consider buying now",
        "avg_legend": "Ø Average",
        "search_btn": "🔍  Search",
        "alert_hint": "← Alert when a shop is ≤ this price",
        "loading_url": "🔍  Loading shops from URL...",
        "searching": "🔍  Searching on Geizhals...",
        "prices_checked": "{n} prices checked — {ts}",
        "target_lbl": "Target Price (€)",
        "theme": "Theme",
        "theme_hint": "Restart to apply theme change",
        "font_label": "Font"},
    "de": {
        "app_title": "Preis-Alarm Tracker", "tab_compare": "  ⚖ Preisvergleich  ",
        "tab_settings": "  ⚙ Einstellungen  ", "tab_log": "  📄 Log  ",
        "new_group": "＋  Neue Gruppe", "check_all": "↺  Alle prüfen",
        "checking": "⏳  Prüfe...", "delete": "🗑  Löschen",
        "price_history": "📈 Preisverlauf", "add_url": "+ URL",
        "product_groups": "GRUPPEN", "select_group": "Gruppe auswählen oder neu erstellen",
        "best_price": "🏆 Günstigster Preis", "target_reached": "🔔 Zielpreis erreicht!",
        "no_price": "⚠ Kein Preis", "still_too_much": "noch {diff} zu viel",
        "save": "💾  Speichern", "test_email": "✉  Test-E-Mail",
        "settings_saved": "Einstellungen gespeichert.", "email_sent": "Test-E-Mail gesendet!",
        "autostart_on": "Autostart aktiviert.", "autostart_off": "Autostart deaktiviert.",
        "start_windows": "Mit Windows starten (Autostart)",
        "minimize_tray": "Beim Schließen in System-Tray minimieren",
        "smtp_presets": "ℹ  SMTP Voreinstellungen  —  klicken zum Übernehmen",
        "interval_label": "Alle X Stunden", "interval_hint": " Stunden (1–24)",
        "sender_email": "Absender E-Mail", "password": "Passwort",
        "recipient_email": "Empfänger E-Mail", "clear_log": "🗑  Log leeren",
        "search_hint": "Produktname, Suchbegriff oder Geizhals-/PriceSpy-URL",
        "url_tip": "Tipp: Geizhals URL (.de/.eu) oder PriceSpy URL einfügen",
        "target_price": "Zielpreis", "create_group": "✅  Gruppe erstellen & tracken",
        "all_btn": "Alle", "none_btn": "Keine", "language": "Sprache",
        "buy_now": "🟢 JETZT KAUFEN", "wait": "⏳ WARTEN", "monitor": "⏳ BEOBACHTEN",
        "buy_soon": "🔴 BALD KAUFEN — Preis steigt", "almost": "🟡 FAST ERREICHT",
        "wait_falling": "🟡 WARTEN — Preis fällt",
        "ai_title": "Smarte Preisanalyse",
        "recommendation": "EMPFEHLUNG",
        "price_analysis": "Preisanalyse",
        "trend_volatility": "Trend & Volatilität",
        "insight": "Einblick",
        "cur_best": "Aktuell günstigster Preis",
        "your_target": "Dein Zielpreis",
        "dist_target": "Abstand zum Ziel",
        "vs_alltime": "vs. Allzeit-Tief",
        "price_trend": "Preistrend",
        "price_stab": "Preisstabilität",
        "data_points": "Datenpunkte",
        "seasonal": "Saisonales Muster",
        "price_spread": "Preisunterschied (Shops)",
        "close": "Schließen",
        "shops_tracked": "Verfolgte Shops",
        "target_price_lbl": "Zielpreis",
        "cur_avg": "Durchschnittspreis",
        "cur_worst": "Teuerster Preis",
        "alltime_low": "Allzeit-Tief",
        "alltime_high": "Allzeit-Hoch",
        "alltime_avg": "Allzeit-Durchschnitt",
        "total_points": "Gesamte Datenpunkte",
        "cheapest_shop": "Günstigster Shop",
        "expensive_shop": "Teuerster Shop",
        "max_savings": "Maximale Ersparnis",
        "period": "Zeitraum:",
        "day": "Tag",
        "week": "Woche",
        "month": "Monat",
        "all": "Alles",
        "subtitle": "Smarte Preisüberwachung",
        "email_config": "E-Mail Konfiguration",
        "check_interval": "Prüf-Intervall",
        "above_target_track": "Preis liegt {pct}% über Ziel — weiter beobachten",
        "above_target_wait": "Preis liegt {pct}% über Ziel — Alarm setzen und warten",
        "above_target_falling": "Preis fällt und liegt {pct}% über Ziel — bald erreicht",
        "price_rising_grund": "Preis steigt — jetzt kaufen bevor er teurer wird",
        "at_target": "Preis liegt am oder unter deinem Zielpreis",
        "almost_grund": "Nur noch {pct}% über deinem Ziel — jetzt kaufen erwägen",
        "avg_legend": "Ø Durchschnitt",
        "search_btn": "🔍  Suchen",
        "alert_hint": "← Alarm wenn ein Shop ≤ diesem Preis",
        "loading_url": "🔍  Lade Shops von URL...",
        "searching": "🔍  Suche auf Geizhals...",
        "prices_checked": "{n} Preise geprüft — {ts}",
        "target_lbl": "Zielpreis (€)",
        "theme": "Design",
        "theme_hint": "Neustart zum Übernehmen",
        "font_label": "Schriftart"},
    "fr": {
        "app_title": "Suivi des Prix", "tab_compare": "  ⚖ Comparaison  ",
        "tab_settings": "  ⚙ Paramètres  ", "tab_log": "  📄 Journal  ",
        "new_group": "＋  Nouveau groupe", "check_all": "↺  Tout vérifier",
        "checking": "⏳  Vérification...", "delete": "🗑  Supprimer",
        "price_history": "📈 Historique", "add_url": "+ URL",
        "product_groups": "GROUPES", "select_group": "Sélectionner un groupe",
        "best_price": "🏆 Meilleur prix", "target_reached": "🔔 Objectif atteint!",
        "no_price": "⚠ Pas de prix", "still_too_much": "encore {diff} de trop",
        "save": "💾  Enregistrer", "test_email": "✉  E-mail test",
        "settings_saved": "Paramètres enregistrés.", "email_sent": "E-mail test envoyé!",
        "autostart_on": "Démarrage auto activé.", "autostart_off": "Démarrage auto désactivé.",
        "start_windows": "Démarrer avec Windows",
        "minimize_tray": "Réduire dans la barre système",
        "smtp_presets": "ℹ  Préréglages SMTP", "interval_label": "Toutes les X heures",
        "interval_hint": " heures (1–24)", "sender_email": "E-mail expéditeur",
        "password": "Mot de passe", "recipient_email": "E-mail destinataire",
        "clear_log": "🗑  Effacer journal",
        "search_hint": "Nom du produit, terme de recherche ou URL",
        "url_tip": "Astuce: Collez une URL Geizhals ou PriceSpy",
        "target_price": "Prix cible", "create_group": "✅  Créer le groupe",
        "all_btn": "Tout", "none_btn": "Aucun", "language": "Langue",
        "buy_now": "🟢 ACHETER", "wait": "⏳ ATTENDRE", "monitor": "⏳ SURVEILLER",
        "buy_soon": "🔴 ACHETER VITE", "almost": "🟡 PRESQUE",
        "wait_falling": "🟡 ATTENDRE — Prix en baisse",
        "ai_title": "Analyse intelligente",
        "recommendation": "RECOMMANDATION",
        "price_analysis": "Analyse des prix",
        "trend_volatility": "Tendance & Volatilité",
        "insight": "Aperçu",
        "cur_best": "Meilleur prix actuel",
        "your_target": "Votre objectif",
        "dist_target": "Distance à l'objectif",
        "vs_alltime": "vs. plus bas historique",
        "price_trend": "Tendance",
        "price_stab": "Stabilité",
        "data_points": "Points de données",
        "seasonal": "Modèle saisonnier",
        "price_spread": "Écart de prix",
        "close": "Fermer",
        "shops_tracked": "Boutiques suivies",
        "target_price_lbl": "Prix cible",
        "cur_avg": "Prix moyen",
        "cur_worst": "Prix le plus élevé",
        "alltime_low": "Plus bas historique",
        "alltime_high": "Plus haut historique",
        "alltime_avg": "Moyenne historique",
        "total_points": "Total des points",
        "cheapest_shop": "Boutique la moins chère",
        "expensive_shop": "Boutique la plus chère",
        "max_savings": "Économies max",
        "period": "Période:",
        "day": "Jour",
        "week": "Semaine",
        "month": "Mois",
        "all": "Tout",
        "subtitle": "Suivi intelligent des prix",
        "email_config": "Configuration e-mail",
        "check_interval": "Intervalle de vérification",
        "above_target_track": "Prix {pct}% au-dessus de l'objectif",
        "above_target_wait": "Prix {pct}% au-dessus — attendre",
        "above_target_falling": "Prix en baisse, {pct}% au-dessus",
        "price_rising_grund": "Prix en hausse — achetez maintenant",
        "at_target": "Prix atteint l'objectif",
        "almost_grund": "Seulement {pct}% au-dessus",
        "avg_legend": "Ø Moyenne",
        "search_btn": "🔍  Rechercher",
        "alert_hint": "← Alerte si boutique ≤ ce prix",
        "loading_url": "🔍  Chargement...",
        "searching": "🔍  Recherche...",
        "prices_checked": "{n} prix vérifiés — {ts}",
        "target_lbl": "Prix cible (€)",
        "theme": "Thème",
        "theme_hint": "Redémarrer pour appliquer",
        "font_label": "Police"},
    "es": {
        "app_title": "Rastreador de Precios", "tab_compare": "  ⚖ Comparación  ",
        "tab_settings": "  ⚙ Ajustes  ", "tab_log": "  📄 Registro  ",
        "new_group": "＋  Nuevo grupo", "check_all": "↺  Verificar todo",
        "checking": "⏳  Verificando...", "delete": "🗑  Eliminar",
        "price_history": "📈 Historial", "add_url": "+ URL",
        "product_groups": "GRUPOS", "select_group": "Seleccionar un grupo",
        "best_price": "🏆 Mejor precio", "target_reached": "🔔 ¡Objetivo alcanzado!",
        "no_price": "⚠ Sin precio", "still_too_much": "{diff} demasiado",
        "save": "💾  Guardar", "test_email": "✉  Correo de prueba",
        "settings_saved": "Ajustes guardados.", "email_sent": "¡Correo enviado!",
        "autostart_on": "Inicio automático activado.", "autostart_off": "Inicio automático desactivado.",
        "start_windows": "Iniciar con Windows",
        "minimize_tray": "Minimizar a la bandeja del sistema",
        "smtp_presets": "ℹ  Preajustes SMTP", "interval_label": "Cada X horas",
        "interval_hint": " horas (1–24)", "sender_email": "Correo remitente",
        "password": "Contraseña", "recipient_email": "Correo destinatario",
        "clear_log": "🗑  Limpiar registro",
        "search_hint": "Nombre del producto, término de búsqueda o URL",
        "url_tip": "Consejo: Pega una URL de Geizhals o PriceSpy",
        "target_price": "Precio objetivo", "create_group": "✅  Crear grupo",
        "all_btn": "Todo", "none_btn": "Ninguno", "language": "Idioma",
        "buy_now": "🟢 COMPRAR", "wait": "⏳ ESPERAR", "monitor": "⏳ VIGILAR",
        "buy_soon": "🔴 COMPRAR PRONTO", "almost": "🟡 CASI",
        "wait_falling": "🟡 ESPERAR — Precio bajando",
        "ai_title": "Análisis inteligente",
        "recommendation": "RECOMENDACIÓN",
        "price_analysis": "Análisis de precio",
        "trend_volatility": "Tendencia & Volatilidad",
        "insight": "Perspectiva",
        "cur_best": "Mejor precio actual",
        "your_target": "Tu objetivo",
        "dist_target": "Distancia al objetivo",
        "vs_alltime": "vs. mínimo histórico",
        "price_trend": "Tendencia",
        "price_stab": "Estabilidad",
        "data_points": "Puntos de datos",
        "seasonal": "Patrón estacional",
        "price_spread": "Diferencia de precio",
        "close": "Cerrar",
        "shops_tracked": "Tiendas seguidas",
        "target_price_lbl": "Precio objetivo",
        "cur_avg": "Precio promedio",
        "cur_worst": "Precio más alto",
        "alltime_low": "Mínimo histórico",
        "alltime_high": "Máximo histórico",
        "alltime_avg": "Promedio histórico",
        "total_points": "Total de puntos",
        "cheapest_shop": "Tienda más barata",
        "expensive_shop": "Tienda más cara",
        "max_savings": "Ahorro máximo",
        "period": "Período:",
        "day": "Día",
        "week": "Semana",
        "month": "Mes",
        "all": "Todo",
        "subtitle": "Monitoreo inteligente",
        "email_config": "Configuración de correo",
        "check_interval": "Intervalo de verificación",
        "above_target_track": "Precio {pct}% sobre objetivo",
        "above_target_wait": "Precio {pct}% sobre objetivo — esperar",
        "above_target_falling": "Precio bajando, {pct}% sobre objetivo",
        "price_rising_grund": "Precio subiendo — compra ahora",
        "at_target": "Precio en el objetivo",
        "almost_grund": "Solo {pct}% sobre objetivo",
        "avg_legend": "Ø Promedio",
        "search_btn": "🔍  Buscar",
        "alert_hint": "← Alerta si tienda ≤ este precio",
        "loading_url": "🔍  Cargando...",
        "searching": "🔍  Buscando...",
        "prices_checked": "{n} precios verificados — {ts}",
        "target_lbl": "Precio objetivo (€)",
        "theme": "Tema",
        "theme_hint": "Reiniciar para aplicar",
        "font_label": "Fuente"},
    "it": {
        "app_title": "Monitoraggio Prezzi", "tab_compare": "  ⚖ Confronto  ",
        "tab_settings": "  ⚙ Impostazioni  ", "tab_log": "  📄 Registro  ",
        "new_group": "＋  Nuovo gruppo", "check_all": "↺  Controlla tutto",
        "checking": "⏳  Controllo...", "delete": "🗑  Elimina",
        "price_history": "📈 Storico", "add_url": "+ URL",
        "product_groups": "GRUPPI", "select_group": "Seleziona un gruppo",
        "best_price": "🏆 Miglior prezzo", "target_reached": "🔔 Obiettivo raggiunto!",
        "no_price": "⚠ Nessun prezzo", "still_too_much": "ancora {diff} troppo",
        "save": "💾  Salva", "test_email": "✉  Email di test",
        "settings_saved": "Impostazioni salvate.", "email_sent": "Email inviata!",
        "autostart_on": "Avvio auto attivato.", "autostart_off": "Avvio auto disattivato.",
        "start_windows": "Avvia con Windows",
        "minimize_tray": "Riduci a icona nella barra",
        "smtp_presets": "ℹ  Preimpostazioni SMTP", "interval_label": "Ogni X ore",
        "interval_hint": " ore (1–24)", "sender_email": "Email mittente",
        "password": "Password", "recipient_email": "Email destinatario",
        "clear_log": "🗑  Cancella registro",
        "search_hint": "Nome prodotto, termine di ricerca o URL",
        "url_tip": "Suggerimento: Incolla un URL Geizhals o PriceSpy",
        "target_price": "Prezzo target", "create_group": "✅  Crea gruppo",
        "all_btn": "Tutti", "none_btn": "Nessuno", "language": "Lingua",
        "buy_now": "🟢 COMPRA ORA", "wait": "⏳ ASPETTA", "monitor": "⏳ MONITORA",
        "buy_soon": "🔴 COMPRA PRESTO", "almost": "🟡 QUASI",
        "wait_falling": "🟡 ASPETTA — Prezzo in calo",
        "ai_title": "Analisi intelligente",
        "recommendation": "RACCOMANDAZIONE",
        "price_analysis": "Analisi prezzi",
        "trend_volatility": "Tendenza & Volatilità",
        "insight": "Approfondimento",
        "cur_best": "Miglior prezzo attuale",
        "your_target": "Il tuo obiettivo",
        "dist_target": "Distanza dall'obiettivo",
        "vs_alltime": "vs. minimo storico",
        "price_trend": "Tendenza",
        "price_stab": "Stabilità",
        "data_points": "Punti dati",
        "seasonal": "Schema stagionale",
        "price_spread": "Differenza di prezzo",
        "close": "Chiudi",
        "shops_tracked": "Negozi tracciati",
        "target_price_lbl": "Prezzo target",
        "cur_avg": "Prezzo medio",
        "cur_worst": "Prezzo più alto",
        "alltime_low": "Minimo storico",
        "alltime_high": "Massimo storico",
        "alltime_avg": "Media storica",
        "total_points": "Totale punti",
        "cheapest_shop": "Negozio più economico",
        "expensive_shop": "Negozio più caro",
        "max_savings": "Risparmio massimo",
        "period": "Periodo:",
        "day": "Giorno",
        "week": "Settimana",
        "month": "Mese",
        "all": "Tutto",
        "subtitle": "Monitoraggio intelligente",
        "email_config": "Configurazione email",
        "check_interval": "Intervallo di controllo",
        "above_target_track": "Prezzo {pct}% sopra obiettivo",
        "above_target_wait": "Prezzo {pct}% sopra — aspettare",
        "above_target_falling": "Prezzo in calo, {pct}% sopra",
        "price_rising_grund": "Prezzo in aumento — compra ora",
        "at_target": "Prezzo all'obiettivo",
        "almost_grund": "Solo {pct}% sopra obiettivo",
        "avg_legend": "Ø Media",
        "search_btn": "🔍  Cerca",
        "alert_hint": "← Avviso se negozio ≤ questo prezzo",
        "loading_url": "🔍  Caricamento...",
        "searching": "🔍  Ricerca...",
        "prices_checked": "{n} prezzi verificati — {ts}",
        "target_lbl": "Prezzo target (€)",
        "theme": "Tema",
        "theme_hint": "Riavvia per applicare",
        "font_label": "Carattere"},
    "nl": {
        "app_title": "Prijsalarm Tracker", "tab_compare": "  ⚖ Vergelijking  ",
        "tab_settings": "  ⚙ Instellingen  ", "tab_log": "  📄 Log  ",
        "new_group": "＋  Nieuwe groep", "check_all": "↺  Alles controleren",
        "checking": "⏳  Controleren...", "delete": "🗑  Verwijderen",
        "price_history": "📈 Prijsgeschiedenis", "add_url": "+ URL",
        "product_groups": "GROEPEN", "select_group": "Selecteer een groep",
        "best_price": "🏆 Beste prijs", "target_reached": "🔔 Doelprijs bereikt!",
        "no_price": "⚠ Geen prijs", "still_too_much": "nog {diff} te veel",
        "save": "💾  Opslaan", "test_email": "✉  Test e-mail",
        "settings_saved": "Instellingen opgeslagen.", "email_sent": "Test e-mail verzonden!",
        "autostart_on": "Autostart ingeschakeld.", "autostart_off": "Autostart uitgeschakeld.",
        "start_windows": "Starten met Windows",
        "minimize_tray": "Minimaliseren naar systeemvak",
        "smtp_presets": "ℹ  SMTP Presets", "interval_label": "Elke X uur",
        "interval_hint": " uur (1–24)", "sender_email": "Afzender e-mail",
        "password": "Wachtwoord", "recipient_email": "Ontvanger e-mail",
        "clear_log": "🗑  Log wissen",
        "search_hint": "Productnaam, zoekterm of URL",
        "url_tip": "Tip: Plak een Geizhals of PriceSpy URL",
        "target_price": "Doelprijs", "create_group": "✅  Groep aanmaken",
        "all_btn": "Alle", "none_btn": "Geen", "language": "Taal",
        "buy_now": "🟢 KOOP NU", "wait": "⏳ WACHT", "monitor": "⏳ MONITOR",
        "buy_soon": "🔴 KOOP SNEL", "almost": "🟡 BIJNA",
        "wait_falling": "🟡 WACHT — Prijs daalt",
        "ai_title": "Slimme analyse",
        "recommendation": "AANBEVELING",
        "price_analysis": "Prijsanalyse",
        "trend_volatility": "Trend & Volatiliteit",
        "insight": "Inzicht",
        "cur_best": "Huidige beste prijs",
        "your_target": "Jouw doel",
        "dist_target": "Afstand tot doel",
        "vs_alltime": "vs. historisch laagst",
        "price_trend": "Prijstrend",
        "price_stab": "Prijsstabiliteit",
        "data_points": "Datapunten",
        "seasonal": "Seizoenspatroon",
        "price_spread": "Prijsverschil",
        "close": "Sluiten",
        "shops_tracked": "Gevolgde winkels",
        "target_price_lbl": "Doelprijs",
        "cur_avg": "Gemiddelde prijs",
        "cur_worst": "Hoogste prijs",
        "alltime_low": "Historisch laagst",
        "alltime_high": "Historisch hoogst",
        "alltime_avg": "Historisch gemiddeld",
        "total_points": "Totaal punten",
        "cheapest_shop": "Goedkoopste winkel",
        "expensive_shop": "Duurste winkel",
        "max_savings": "Maximale besparing",
        "period": "Periode:",
        "day": "Dag",
        "week": "Week",
        "month": "Maand",
        "all": "Alles",
        "subtitle": "Slimme prijsbewaking",
        "email_config": "E-mailconfiguratie",
        "check_interval": "Controle-interval",
        "above_target_track": "Prijs {pct}% boven doel",
        "above_target_wait": "Prijs {pct}% boven doel — wachten",
        "above_target_falling": "Prijs daalt, {pct}% boven doel",
        "price_rising_grund": "Prijs stijgt — nu kopen",
        "at_target": "Prijs op doel",
        "almost_grund": "Nog maar {pct}% boven doel",
        "avg_legend": "Ø Gemiddelde",
        "search_btn": "🔍  Zoeken",
        "alert_hint": "← Melding als winkel ≤ deze prijs",
        "loading_url": "🔍  Laden...",
        "searching": "🔍  Zoeken...",
        "prices_checked": "{n} prijzen gecontroleerd — {ts}",
        "target_lbl": "Doelprijs (€)",
        "theme": "Thema",
        "theme_hint": "Herstart om toe te passen",
        "font_label": "Lettertype"},
    "pl": {
        "app_title": "Śledzenie Cen", "tab_compare": "  ⚖ Porównanie  ",
        "tab_settings": "  ⚙ Ustawienia  ", "tab_log": "  📄 Dziennik  ",
        "new_group": "＋  Nowa grupa", "check_all": "↺  Sprawdź wszystko",
        "checking": "⏳  Sprawdzanie...", "delete": "🗑  Usuń",
        "price_history": "📈 Historia cen", "add_url": "+ URL",
        "product_groups": "GRUPY", "select_group": "Wybierz grupę",
        "best_price": "🏆 Najlepsza cena", "target_reached": "🔔 Cel osiągnięty!",
        "no_price": "⚠ Brak ceny", "still_too_much": "jeszcze {diff} za dużo",
        "save": "💾  Zapisz", "test_email": "✉  E-mail testowy",
        "settings_saved": "Ustawienia zapisane.", "email_sent": "E-mail wysłany!",
        "autostart_on": "Autostart włączony.", "autostart_off": "Autostart wyłączony.",
        "start_windows": "Uruchom z Windows",
        "minimize_tray": "Minimalizuj do zasobnika",
        "smtp_presets": "ℹ  Presety SMTP", "interval_label": "Co X godzin",
        "interval_hint": " godzin (1–24)", "sender_email": "E-mail nadawcy",
        "password": "Hasło", "recipient_email": "E-mail odbiorcy",
        "clear_log": "🗑  Wyczyść dziennik",
        "search_hint": "Nazwa produktu, hasło lub URL",
        "url_tip": "Wskazówka: Wklej URL Geizhals lub PriceSpy",
        "target_price": "Cena docelowa", "create_group": "✅  Utwórz grupę",
        "all_btn": "Wszystkie", "none_btn": "Żadne", "language": "Język",
        "buy_now": "🟢 KUP TERAZ", "wait": "⏳ CZEKAJ", "monitor": "⏳ MONITORUJ",
        "buy_soon": "🔴 KUP WKRÓTCE", "almost": "🟡 PRAWIE",
        "wait_falling": "🟡 CZEKAJ — Cena spada",
        "ai_title": "Inteligentna analiza",
        "recommendation": "REKOMENDACJA",
        "price_analysis": "Analiza cen",
        "trend_volatility": "Trend & Zmienność",
        "insight": "Wgląd",
        "cur_best": "Najlepsza cena",
        "your_target": "Twój cel",
        "dist_target": "Odległość od celu",
        "vs_alltime": "vs. historyczne minimum",
        "price_trend": "Trend cenowy",
        "price_stab": "Stabilność",
        "data_points": "Punkty danych",
        "seasonal": "Wzorzec sezonowy",
        "price_spread": "Różnica cen",
        "close": "Zamknij",
        "shops_tracked": "Śledzone sklepy",
        "target_price_lbl": "Cena docelowa",
        "cur_avg": "Średnia cena",
        "cur_worst": "Najwyższa cena",
        "alltime_low": "Historyczne minimum",
        "alltime_high": "Historyczne maksimum",
        "alltime_avg": "Historyczna średnia",
        "total_points": "Łączne punkty",
        "cheapest_shop": "Najtańszy sklep",
        "expensive_shop": "Najdroższy sklep",
        "max_savings": "Maks. oszczędności",
        "period": "Okres:",
        "day": "Dzień",
        "week": "Tydzień",
        "month": "Miesiąc",
        "all": "Wszystko",
        "subtitle": "Inteligentne śledzenie cen",
        "email_config": "Konfiguracja e-mail",
        "check_interval": "Interwał sprawdzania",
        "above_target_track": "Cena {pct}% powyżej celu",
        "above_target_wait": "Cena {pct}% powyżej — czekaj",
        "above_target_falling": "Cena spada, {pct}% powyżej",
        "price_rising_grund": "Cena rośnie — kup teraz",
        "at_target": "Cena osiągnęła cel",
        "almost_grund": "Tylko {pct}% powyżej celu",
        "avg_legend": "Ø Średnia",
        "search_btn": "🔍  Szukaj",
        "alert_hint": "← Alert gdy sklep ≤ tej ceny",
        "loading_url": "🔍  Ładowanie...",
        "searching": "🔍  Szukanie...",
        "prices_checked": "{n} cen sprawdzonych — {ts}",
        "target_lbl": "Cena docelowa (€)",
        "theme": "Motyw",
        "theme_hint": "Uruchom ponownie aby zastosować",
        "font_label": "Czcionka"},
    "pt": {
        "app_title": "Rastreador de Preços", "tab_compare": "  ⚖ Comparação  ",
        "tab_settings": "  ⚙ Definições  ", "tab_log": "  📄 Registo  ",
        "new_group": "＋  Novo grupo", "check_all": "↺  Verificar tudo",
        "checking": "⏳  Verificando...", "delete": "🗑  Eliminar",
        "price_history": "📈 Histórico", "add_url": "+ URL",
        "product_groups": "GRUPOS", "select_group": "Selecionar um grupo",
        "best_price": "🏆 Melhor preço", "target_reached": "🔔 Objetivo atingido!",
        "no_price": "⚠ Sem preço", "still_too_much": "ainda {diff} a mais",
        "save": "💾  Guardar", "test_email": "✉  Email de teste",
        "settings_saved": "Definições guardadas.", "email_sent": "Email enviado!",
        "autostart_on": "Início auto ativado.", "autostart_off": "Início auto desativado.",
        "start_windows": "Iniciar com o Windows",
        "minimize_tray": "Minimizar para a bandeja",
        "smtp_presets": "ℹ  Predefinições SMTP", "interval_label": "A cada X horas",
        "interval_hint": " horas (1–24)", "sender_email": "Email remetente",
        "password": "Senha", "recipient_email": "Email destinatário",
        "clear_log": "🗑  Limpar registo",
        "search_hint": "Nome do produto, termo de pesquisa ou URL",
        "url_tip": "Dica: Cole um URL do Geizhals ou PriceSpy",
        "target_price": "Preço alvo", "create_group": "✅  Criar grupo",
        "all_btn": "Todos", "none_btn": "Nenhum", "language": "Idioma",
        "buy_now": "🟢 COMPRAR", "wait": "⏳ AGUARDAR", "monitor": "⏳ MONITORAR",
        "buy_soon": "🔴 COMPRAR RÁPIDO", "almost": "🟡 QUASE",
        "wait_falling": "🟡 AGUARDAR — Preço a cair",
        "ai_title": "Análise inteligente",
        "recommendation": "RECOMENDAÇÃO",
        "price_analysis": "Análise de preço",
        "trend_volatility": "Tendência & Volatilidade",
        "insight": "Perspectiva",
        "cur_best": "Melhor preço atual",
        "your_target": "Seu objetivo",
        "dist_target": "Distância ao objetivo",
        "vs_alltime": "vs. mínimo histórico",
        "price_trend": "Tendência",
        "price_stab": "Estabilidade",
        "data_points": "Pontos de dados",
        "seasonal": "Padrão sazonal",
        "price_spread": "Diferença de preço",
        "close": "Fechar",
        "shops_tracked": "Lojas rastreadas",
        "target_price_lbl": "Preço alvo",
        "cur_avg": "Preço médio",
        "cur_worst": "Preço mais alto",
        "alltime_low": "Mínimo histórico",
        "alltime_high": "Máximo histórico",
        "alltime_avg": "Média histórica",
        "total_points": "Total de pontos",
        "cheapest_shop": "Loja mais barata",
        "expensive_shop": "Loja mais cara",
        "max_savings": "Poupança máxima",
        "period": "Período:",
        "day": "Dia",
        "week": "Semana",
        "month": "Mês",
        "all": "Tudo",
        "subtitle": "Monitoramento inteligente",
        "email_config": "Configuração de e-mail",
        "check_interval": "Intervalo de verificação",
        "above_target_track": "Preço {pct}% acima do objetivo",
        "above_target_wait": "Preço {pct}% acima — aguardar",
        "above_target_falling": "Preço a cair, {pct}% acima",
        "price_rising_grund": "Preço subindo — compre agora",
        "at_target": "Preço no objetivo",
        "almost_grund": "Só {pct}% acima do objetivo",
        "avg_legend": "Ø Média",
        "search_btn": "🔍  Pesquisar",
        "alert_hint": "← Alerta se loja ≤ este preço",
        "loading_url": "🔍  Carregando...",
        "searching": "🔍  Pesquisando...",
        "prices_checked": "{n} preços verificados — {ts}",
        "target_lbl": "Preço alvo (€)",
        "theme": "Tema",
        "theme_hint": "Reiniciar para aplicar",
        "font_label": "Fonte"},
    "tr": {
        "app_title": "Fiyat Takip Aracı", "tab_compare": "  ⚖ Karşılaştırma  ",
        "tab_settings": "  ⚙ Ayarlar  ", "tab_log": "  📄 Günlük  ",
        "new_group": "＋  Yeni Grup", "check_all": "↺  Hepsini Kontrol Et",
        "checking": "⏳  Kontrol ediliyor...", "delete": "🗑  Sil",
        "price_history": "📈 Fiyat Geçmişi", "add_url": "+ URL",
        "product_groups": "GRUPLAR", "select_group": "Bir grup seçin",
        "best_price": "🏆 En İyi Fiyat", "target_reached": "🔔 Hedef ulaşıldı!",
        "no_price": "⚠ Fiyat yok", "still_too_much": "hâlâ {diff} fazla",
        "save": "💾  Kaydet", "test_email": "✉  Test E-postası",
        "settings_saved": "Ayarlar kaydedildi.", "email_sent": "Test e-postası gönderildi!",
        "autostart_on": "Otomatik başlatma açık.", "autostart_off": "Otomatik başlatma kapalı.",
        "start_windows": "Windows ile başlat",
        "minimize_tray": "Sistem tepsisine küçült",
        "smtp_presets": "ℹ  SMTP Önayarları", "interval_label": "Her X saatte",
        "interval_hint": " saat (1–24)", "sender_email": "Gönderen e-posta",
        "password": "Şifre", "recipient_email": "Alıcı e-posta",
        "clear_log": "🗑  Günlüğü temizle",
        "search_hint": "Ürün adı, arama terimi veya URL",
        "url_tip": "İpucu: Geizhals veya PriceSpy URL'si yapıştırın",
        "target_price": "Hedef Fiyat", "create_group": "✅  Grup oluştur",
        "all_btn": "Tümü", "none_btn": "Hiçbiri", "language": "Dil",
        "buy_now": "🟢 ŞİMDİ AL", "wait": "⏳ BEKLE", "monitor": "⏳ İZLE",
        "buy_soon": "🔴 YAKINDA AL", "almost": "🟡 NEREDEYSE",
        "wait_falling": "🟡 BEKLE — Fiyat düşüyor",
        "ai_title": "Akıllı analiz",
        "recommendation": "TAVSİYE",
        "price_analysis": "Fiyat analizi",
        "trend_volatility": "Trend & Oynaklık",
        "insight": "Görüş",
        "cur_best": "Mevcut en iyi fiyat",
        "your_target": "Hedefiniz",
        "dist_target": "Hedefe uzaklık",
        "vs_alltime": "vs. tüm zamanların en düşüğü",
        "price_trend": "Fiyat trendi",
        "price_stab": "Fiyat istikrarı",
        "data_points": "Veri noktaları",
        "seasonal": "Mevsimsel desen",
        "price_spread": "Fiyat farkı",
        "close": "Kapat",
        "shops_tracked": "Takip edilen mağazalar",
        "target_price_lbl": "Hedef fiyat",
        "cur_avg": "Ortalama fiyat",
        "cur_worst": "En yüksek fiyat",
        "alltime_low": "Tüm zamanların en düşüğü",
        "alltime_high": "Tüm zamanların en yükseği",
        "alltime_avg": "Tarihsel ortalama",
        "total_points": "Toplam nokta",
        "cheapest_shop": "En ucuz mağaza",
        "expensive_shop": "En pahalı mağaza",
        "max_savings": "Maks. tasarruf",
        "period": "Dönem:",
        "day": "Gün",
        "week": "Hafta",
        "month": "Ay",
        "all": "Tümü",
        "subtitle": "Akıllı fiyat takibi",
        "email_config": "E-posta yapılandırması",
        "check_interval": "Kontrol aralığı",
        "above_target_track": "Fiyat hedefin {pct}% üzerinde",
        "above_target_wait": "Fiyat {pct}% üzerinde — bekle",
        "above_target_falling": "Fiyat düşüyor, {pct}% üzerinde",
        "price_rising_grund": "Fiyat artıyor — şimdi al",
        "at_target": "Fiyat hedefe ulaştı",
        "almost_grund": "Sadece {pct}% üzerinde",
        "avg_legend": "Ø Ortalama",
        "search_btn": "🔍  Ara",
        "alert_hint": "← Mağaza ≤ bu fiyata alarmı",
        "loading_url": "🔍  Yükleniyor...",
        "searching": "🔍  Aranıyor...",
        "prices_checked": "{n} fiyat kontrol edildi — {ts}",
        "target_lbl": "Hedef fiyat (€)",
        "theme": "Tema",
        "theme_hint": "Uygulamak için yeniden başlat",
        "font_label": "Yazı tipi"},
    "ru": {
        "app_title": "Отслеживание цен", "tab_compare": "  ⚖ Сравнение  ",
        "tab_settings": "  ⚙ Настройки  ", "tab_log": "  📄 Журнал  ",
        "new_group": "＋  Новая группа", "check_all": "↺  Проверить всё",
        "checking": "⏳  Проверка...", "delete": "🗑  Удалить",
        "price_history": "📈 История цен", "add_url": "+ URL",
        "product_groups": "ГРУППЫ", "select_group": "Выберите группу",
        "best_price": "🏆 Лучшая цена", "target_reached": "🔔 Цель достигнута!",
        "no_price": "⚠ Нет цены", "still_too_much": "ещё {diff} лишних",
        "save": "💾  Сохранить", "test_email": "✉  Тест почты",
        "settings_saved": "Настройки сохранены.", "email_sent": "Письмо отправлено!",
        "autostart_on": "Автозапуск включён.", "autostart_off": "Автозапуск выключен.",
        "start_windows": "Запускать с Windows",
        "minimize_tray": "Свернуть в трей",
        "smtp_presets": "ℹ  Настройки SMTP", "interval_label": "Каждые X часов",
        "interval_hint": " часов (1–24)", "sender_email": "Email отправителя",
        "password": "Пароль", "recipient_email": "Email получателя",
        "clear_log": "🗑  Очистить журнал",
        "search_hint": "Название товара, поисковый запрос или URL",
        "url_tip": "Совет: Вставьте URL Geizhals или PriceSpy",
        "target_price": "Целевая цена", "create_group": "✅  Создать группу",
        "all_btn": "Все", "none_btn": "Ни одного", "language": "Язык",
        "buy_now": "🟢 КУПИТЬ", "wait": "⏳ ЖДАТЬ", "monitor": "⏳ СЛЕДИТЬ",
        "buy_soon": "🔴 КУПИТЬ СКОРО", "almost": "🟡 ПОЧТИ",
        "wait_falling": "🟡 ЖДАТЬ — Цена падает",
        "ai_title": "Умный анализ",
        "recommendation": "РЕКОМЕНДАЦИЯ",
        "price_analysis": "Анализ цен",
        "trend_volatility": "Тренд & Волатильность",
        "insight": "Вывод",
        "cur_best": "Лучшая цена сейчас",
        "your_target": "Ваша цель",
        "dist_target": "Расстояние до цели",
        "vs_alltime": "vs. исторический минимум",
        "price_trend": "Тренд цены",
        "price_stab": "Стабильность",
        "data_points": "Точки данных",
        "seasonal": "Сезонная закономерность",
        "price_spread": "Разброс цен",
        "close": "Закрыть",
        "shops_tracked": "Отслеживаемые магазины",
        "target_price_lbl": "Целевая цена",
        "cur_avg": "Средняя цена",
        "cur_worst": "Самая высокая цена",
        "alltime_low": "Исторический минимум",
        "alltime_high": "Исторический максимум",
        "alltime_avg": "Среднее за всё время",
        "total_points": "Всего точек",
        "cheapest_shop": "Самый дешёвый магазин",
        "expensive_shop": "Самый дорогой магазин",
        "max_savings": "Макс. экономия",
        "period": "Период:",
        "day": "День",
        "week": "Неделя",
        "month": "Месяц",
        "all": "Всё",
        "subtitle": "Умный мониторинг цен",
        "email_config": "Настройка почты",
        "check_interval": "Интервал проверки",
        "above_target_track": "Цена на {pct}% выше цели",
        "above_target_wait": "Цена на {pct}% выше — ждать",
        "above_target_falling": "Цена падает, {pct}% выше цели",
        "price_rising_grund": "Цена растёт — покупайте сейчас",
        "at_target": "Цена достигла цели",
        "almost_grund": "Только {pct}% выше цели",
        "avg_legend": "Ø Среднее",
        "search_btn": "🔍  Найти",
        "alert_hint": "← Оповещение если магазин ≤ этой цены",
        "loading_url": "🔍  Загрузка...",
        "searching": "🔍  Поиск...",
        "prices_checked": "{n} цен проверено — {ts}",
        "target_lbl": "Целевая цена (€)",
        "theme": "Тема",
        "theme_hint": "Перезапустите для применения",
        "font_label": "Шрифт"},
    "zh": {
        "app_title": "价格追踪器", "tab_compare": "  ⚖ 价格比较  ",
        "tab_settings": "  ⚙ 设置  ", "tab_log": "  📄 日志  ",
        "new_group": "＋  新建组", "check_all": "↺  全部检查",
        "checking": "⏳  检查中...", "delete": "🗑  删除",
        "price_history": "📈 价格历史", "add_url": "+ URL",
        "product_groups": "分组", "select_group": "选择一个分组",
        "best_price": "🏆 最低价", "target_reached": "🔔 已达目标价!",
        "no_price": "⚠ 无价格", "still_too_much": "还差 {diff}",
        "save": "💾  保存", "test_email": "✉  测试邮件",
        "settings_saved": "设置已保存。", "email_sent": "测试邮件已发送！",
        "autostart_on": "开机自启已开启。", "autostart_off": "开机自启已关闭。",
        "start_windows": "随Windows启动",
        "minimize_tray": "关闭时最小化到托盘",
        "smtp_presets": "ℹ  SMTP 预设", "interval_label": "每 X 小时",
        "interval_hint": " 小时 (1–24)", "sender_email": "发件人邮箱",
        "password": "密码", "recipient_email": "收件人邮箱",
        "clear_log": "🗑  清除日志",
        "search_hint": "产品名称、搜索词或URL",
        "url_tip": "提示：粘贴 Geizhals 或 PriceSpy 链接",
        "target_price": "目标价格", "create_group": "✅  创建分组",
        "all_btn": "全选", "none_btn": "取消", "language": "语言",
        "buy_now": "🟢 立即购买", "wait": "⏳ 等待", "monitor": "⏳ 监控",
        "buy_soon": "🔴 尽快购买", "almost": "🟡 快了",
        "wait_falling": "🟡 等待 — 价格下降中",
        "ai_title": "智能分析",
        "recommendation": "建议",
        "price_analysis": "价格分析",
        "trend_volatility": "趋势与波动",
        "insight": "洞察",
        "cur_best": "当前最低价",
        "your_target": "您的目标",
        "dist_target": "距目标差距",
        "vs_alltime": "vs. 历史最低",
        "price_trend": "价格趋势",
        "price_stab": "价格稳定性",
        "data_points": "数据点",
        "seasonal": "季节性规律",
        "price_spread": "价格差距",
        "close": "关闭",
        "shops_tracked": "追踪店铺",
        "target_price_lbl": "目标价格",
        "cur_avg": "当前平均价",
        "cur_worst": "当前最高价",
        "alltime_low": "历史最低",
        "alltime_high": "历史最高",
        "alltime_avg": "历史平均",
        "total_points": "总数据点",
        "cheapest_shop": "最便宜店铺",
        "expensive_shop": "最贵店铺",
        "max_savings": "最大节省",
        "period": "周期:",
        "day": "天",
        "week": "周",
        "month": "月",
        "all": "全部",
        "subtitle": "智能价格监控",
        "email_config": "邮件配置",
        "check_interval": "检查间隔",
        "above_target_track": "价格比目标高{pct}%",
        "above_target_wait": "价格高{pct}% — 等待",
        "above_target_falling": "价格下降中，高{pct}%",
        "price_rising_grund": "价格上涨 — 现在购买",
        "at_target": "价格已达目标",
        "almost_grund": "仅高出{pct}%",
        "avg_legend": "Ø 平均",
        "search_btn": "🔍  搜索",
        "alert_hint": "← 当店铺 ≤ 此价格时提醒",
        "loading_url": "🔍  加载中...",
        "searching": "🔍  搜索中...",
        "prices_checked": "{n} 个价格已检查 — {ts}",
        "target_lbl": "目标价格 (€)",
        "theme": "主题",
        "theme_hint": "重启以应用",
        "font_label": "字体"},
    "ja": {
        "app_title": "価格追跡ツール", "tab_compare": "  ⚖ 価格比較  ",
        "tab_settings": "  ⚙ 設定  ", "tab_log": "  📄 ログ  ",
        "new_group": "＋  新しいグループ", "check_all": "↺  すべて確認",
        "checking": "⏳  確認中...", "delete": "🗑  削除",
        "price_history": "📈 価格履歴", "add_url": "+ URL",
        "product_groups": "グループ", "select_group": "グループを選択",
        "best_price": "🏆 最安値", "target_reached": "🔔 目標達成!",
        "no_price": "⚠ 価格なし", "still_too_much": "まだ {diff} 高い",
        "save": "💾  保存", "test_email": "✉  テストメール",
        "settings_saved": "設定を保存しました。", "email_sent": "テストメール送信完了！",
        "autostart_on": "自動起動オン。", "autostart_off": "自動起動オフ。",
        "start_windows": "Windowsと一緒に起動",
        "minimize_tray": "閉じるときにトレイへ最小化",
        "smtp_presets": "ℹ  SMTPプリセット", "interval_label": "X時間ごと",
        "interval_hint": " 時間 (1–24)", "sender_email": "送信者メール",
        "password": "パスワード", "recipient_email": "受信者メール",
        "clear_log": "🗑  ログを消去",
        "search_hint": "製品名、検索語またはURL",
        "url_tip": "ヒント：GeizhalsまたはPriceSpyのURLを貼り付け",
        "target_price": "目標価格", "create_group": "✅  グループ作成",
        "all_btn": "すべて", "none_btn": "なし", "language": "言語",
        "buy_now": "🟢 今すぐ購入", "wait": "⏳ 待つ", "monitor": "⏳ 監視",
        "buy_soon": "🔴 早めに購入", "almost": "🟡 もうすぐ",
        "wait_falling": "🟡 待つ — 価格下落中",
        "ai_title": "スマート分析",
        "recommendation": "推薦",
        "price_analysis": "価格分析",
        "trend_volatility": "トレンドと変動",
        "insight": "インサイト",
        "cur_best": "現在の最安値",
        "your_target": "目標価格",
        "dist_target": "目標との差",
        "vs_alltime": "vs. 過去最安値",
        "price_trend": "価格トレンド",
        "price_stab": "価格安定性",
        "data_points": "データポイント",
        "seasonal": "季節パターン",
        "price_spread": "店舗間価格差",
        "close": "閉じる",
        "shops_tracked": "追跡中の店舗",
        "target_price_lbl": "目標価格",
        "cur_avg": "現在の平均価格",
        "cur_worst": "現在の最高価格",
        "alltime_low": "過去最安値",
        "alltime_high": "過去最高値",
        "alltime_avg": "過去の平均",
        "total_points": "総データ数",
        "cheapest_shop": "最安値ショップ",
        "expensive_shop": "最高値ショップ",
        "max_savings": "最大節約額",
        "period": "期間:",
        "day": "日",
        "week": "週",
        "month": "月",
        "all": "全期間",
        "subtitle": "スマート価格追跡",
        "email_config": "メール設定",
        "check_interval": "チェック間隔",
        "above_target_track": "価格が目標より{pct}%高い",
        "above_target_wait": "目標より{pct}%高い — 待機",
        "above_target_falling": "価格下落中、{pct}%高い",
        "price_rising_grund": "価格上昇中 — 今すぐ購入",
        "at_target": "目標価格に到達",
        "almost_grund": "目標より{pct}%のみ高い",
        "avg_legend": "Ø 平均",
        "search_btn": "🔍  検索",
        "alert_hint": "← 店舗が≤この価格でアラート",
        "loading_url": "🔍  読み込み中...",
        "searching": "🔍  検索中...",
        "prices_checked": "{n} 件の価格を確認 — {ts}",
        "target_lbl": "目標価格 (€)",
        "theme": "テーマ",
        "theme_hint": "再起動して適用",
        "font_label": "フォント"},
    "ar": {
        "app_title": "متتبع الأسعار", "tab_compare": "  ⚖ مقارنة الأسعار  ",
        "tab_settings": "  ⚙ الإعدادات  ", "tab_log": "  📄 السجل  ",
        "new_group": "＋  مجموعة جديدة", "check_all": "↺  فحص الكل",
        "checking": "⏳  جارٍ الفحص...", "delete": "🗑  حذف",
        "price_history": "📈 تاريخ الأسعار", "add_url": "+ رابط",
        "product_groups": "المجموعات", "select_group": "اختر مجموعة",
        "best_price": "🏆 أفضل سعر", "target_reached": "🔔 تم بلوغ الهدف!",
        "no_price": "⚠ لا يوجد سعر", "still_too_much": "لا يزال {diff} زائداً",
        "save": "💾  حفظ", "test_email": "✉  بريد تجريبي",
        "settings_saved": "تم حفظ الإعدادات.", "email_sent": "تم إرسال البريد التجريبي!",
        "autostart_on": "التشغيل التلقائي مُفعَّل.", "autostart_off": "التشغيل التلقائي مُعطَّل.",
        "start_windows": "بدء التشغيل مع ويندوز",
        "minimize_tray": "تصغير إلى شريط المهام",
        "smtp_presets": "ℹ  إعدادات SMTP المسبقة", "interval_label": "كل X ساعات",
        "interval_hint": " ساعات (1–24)", "sender_email": "البريد المُرسِل",
        "password": "كلمة المرور", "recipient_email": "البريد المُستقبِل",
        "clear_log": "🗑  مسح السجل",
        "search_hint": "اسم المنتج أو رابط URL",
        "url_tip": "تلميح: الصق رابط Geizhals أو PriceSpy",
        "target_price": "السعر المستهدف", "create_group": "✅  إنشاء المجموعة",
        "all_btn": "الكل", "none_btn": "لا شيء", "language": "اللغة",
        "buy_now": "🟢 اشتر الآن", "wait": "⏳ انتظر", "monitor": "⏳ راقب",
        "buy_soon": "🔴 اشتر قريباً", "almost": "🟡 تقريباً",
        "wait_falling": "🟡 انتظر — السعر ينخفض",
        "ai_title": "تحليل ذكي",
        "recommendation": "التوصية",
        "price_analysis": "تحليل الأسعار",
        "trend_volatility": "الاتجاه والتقلب",
        "insight": "رؤية",
        "cur_best": "أفضل سعر حالي",
        "your_target": "هدفك",
        "dist_target": "المسافة إلى الهدف",
        "vs_alltime": "vs. أدنى مستوى تاريخي",
        "price_trend": "اتجاه السعر",
        "price_stab": "استقرار السعر",
        "data_points": "نقاط البيانات",
        "seasonal": "النمط الموسمي",
        "price_spread": "فجوة الأسعار",
        "close": "إغلاق",
        "shops_tracked": "المتاجر المتتبعة",
        "target_price_lbl": "السعر المستهدف",
        "cur_avg": "متوسط السعر",
        "cur_worst": "أعلى سعر",
        "alltime_low": "أدنى مستوى تاريخي",
        "alltime_high": "أعلى مستوى تاريخي",
        "alltime_avg": "المتوسط التاريخي",
        "total_points": "إجمالي النقاط",
        "cheapest_shop": "أرخص متجر",
        "expensive_shop": "أغلى متجر",
        "max_savings": "أقصى توفير",
        "period": "الفترة:",
        "day": "يوم",
        "week": "أسبوع",
        "month": "شهر",
        "all": "الكل",
        "subtitle": "تتبع الأسعار الذكي",
        "email_config": "إعداد البريد",
        "check_interval": "فترة الفحص",
        "above_target_track": "السعر أعلى من الهدف بـ{pct}%",
        "above_target_wait": "أعلى من الهدف بـ{pct}% — انتظر",
        "above_target_falling": "السعر ينخفض، أعلى بـ{pct}%",
        "price_rising_grund": "السعر يرتفع — اشتر الآن",
        "at_target": "السعر وصل للهدف",
        "almost_grund": "أعلى بـ{pct}% فقط",
        "avg_legend": "Ø متوسط",
        "search_btn": "🔍  بحث",
        "alert_hint": "← تنبيه إذا كان المتجر ≤ هذا السعر",
        "loading_url": "🔍  جارٍ التحميل...",
        "searching": "🔍  جارٍ البحث...",
        "prices_checked": "تم فحص {n} سعر — {ts}",
        "target_lbl": "السعر المستهدف (€)",
        "theme": "السمة",
        "theme_hint": "أعد التشغيل للتطبيق",
        "font_label": "الخط"},
}
def T(key):
    """Get translation for current language."""
    lang = _current_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

def _current_lang():
    try:
        import json as _json, os as _os
        from pathlib import Path as _P
        cfg = _P(_os.getenv("APPDATA", ".")) / "PreisAlarm" / "config.json"
        if cfg.exists():
            data = _json.loads(cfg.read_text(encoding="utf-8"))
            return data.get("language", "en")
    except:
        pass
    return "en"


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
# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = {
    "dark_mint": {
        "name": "🌑 Dark Mint",
        "BG":     "#0d0d12", "BG2":    "#13131a", "BG3":    "#1c1c27",
        "AKZENT": "#6ee7b7", "ROT":    "#f87171", "GELB":   "#fbbf24",
        "GRAU":   "#64748b", "TEXT":   "#f0f4ff", "TEXT2":  "#8b9cc8",
        "BORDER": "#252535", "PURPLE": "#a78bfa", "BLUE":   "#60a5fa",
    },
    "dark_blue": {
        "name": "🔵 Dark Blue",
        "BG":     "#0a0f1e", "BG2":    "#111827", "BG3":    "#1e2a3a",
        "AKZENT": "#60a5fa", "ROT":    "#f87171", "GELB":   "#fbbf24",
        "GRAU":   "#64748b", "TEXT":   "#f0f8ff", "TEXT2":  "#93c5fd",
        "BORDER": "#1e3a5f", "PURPLE": "#818cf8", "BLUE":   "#38bdf8",
    },
    "dark_purple": {
        "name": "🟣 Dark Purple",
        "BG":     "#0f0a1e", "BG2":    "#1a1030", "BG3":    "#251840",
        "AKZENT": "#c084fc", "ROT":    "#f87171", "GELB":   "#fbbf24",
        "GRAU":   "#6b7280", "TEXT":   "#faf5ff", "TEXT2":  "#d8b4fe",
        "BORDER": "#3b1f6e", "PURPLE": "#a855f7", "BLUE":   "#818cf8",
    },
    "dark_orange": {
        "name": "🟠 Dark Orange",
        "BG":     "#1a0f00", "BG2":    "#241500", "BG3":    "#321d00",
        "AKZENT": "#fb923c", "ROT":    "#f87171", "GELB":   "#fbbf24",
        "GRAU":   "#a8906a", "TEXT":   "#fff7ed", "TEXT2":  "#fed7aa",
        "BORDER": "#5c3d10", "PURPLE": "#c084fc", "BLUE":   "#60a5fa",
    },
    "light": {
        "name": "☀ Light",
        "BG":     "#f0f4f8", "BG2":    "#ffffff", "BG3":    "#e8edf2",
        "AKZENT": "#059669", "ROT":    "#dc2626", "GELB":   "#b45309",
        "GRAU":   "#64748b", "TEXT":   "#1a2332", "TEXT2":  "#334155",
        "BORDER": "#cbd5e1", "PURPLE": "#7c3aed", "BLUE":   "#1d4ed8",
    },
    "light_blue": {
        "name": "🔵 Light Blue",
        "BG":     "#eef4ff", "BG2":    "#ffffff", "BG3":    "#dce8ff",
        "AKZENT": "#1d4ed8", "ROT":    "#dc2626", "GELB":   "#b45309",
        "GRAU":   "#64748b", "TEXT":   "#0f2040", "TEXT2":  "#1e40af",
        "BORDER": "#93c5fd", "PURPLE": "#6d28d9", "BLUE":   "#1d4ed8",
    },
}

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONTS = {
    "segoe":    {"name": "Segoe UI",    "label": "Segoe UI (Standard)"},
    "bahnschrift": {"name": "Bahnschrift", "label": "Bahnschrift (Modern)"},
    "calibri":  {"name": "Calibri",        "label": "Calibri (Office)"},
    "verdana":  {"name": "Verdana",        "label": "Verdana (Readable)"},
    "trebuchet":{"name": "Trebuchet MS",   "label": "Trebuchet MS (Clean)"},
    "tahoma":   {"name": "Tahoma",         "label": "Tahoma (Classic)"},
    "arial":    {"name": "Arial",          "label": "Arial (Universal)"},
    "gothic":   {"name": "Century Gothic", "label": "Century Gothic (Round)"},
}

def _load_font():
    try:
        import json as _j, os as _o
        from pathlib import Path as _P
        cfg = _P(_o.getenv("APPDATA", ".")) / "PreisAlarm" / "config.json"
        if cfg.exists():
            data = _j.loads(cfg.read_text(encoding="utf-8"))
            font_id = data.get("font", "segoe")
            return FONTS.get(font_id, FONTS["segoe"])["name"], font_id
    except: pass
    return UI_FONT, "segoe"

UI_FONT, _font_id = _load_font()


def _load_theme():
    """Load theme from config."""
    try:
        import json as _j, os as _o
        from pathlib import Path as _P
        cfg = _P(_o.getenv("APPDATA", ".")) / "PreisAlarm" / "config.json"
        if cfg.exists():
            data = _j.loads(cfg.read_text(encoding="utf-8"))
            theme_id = data.get("theme", "dark_mint")
            return THEMES.get(theme_id, THEMES["dark_mint"]), theme_id
    except: pass
    return THEMES["dark_mint"], "dark_mint"

_theme, _theme_id = _load_theme()
BG     = _theme["BG"]
BG2    = _theme["BG2"]
BG3    = _theme["BG3"]
AKZENT = _theme["AKZENT"]
ROT    = _theme["ROT"]
GELB   = _theme["GELB"]
GRAU   = _theme["GRAU"]
TEXT   = _theme["TEXT"]
TEXT2  = _theme["TEXT2"]
BORDER = _theme["BORDER"]
PURPLE = _theme["PURPLE"]
BLUE   = _theme["BLUE"]

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
                "smtp_server": "mail.gmx.net", "smtp_port": 587, "intervall": 6, "language": "en"}
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
    """Returns the internal shop key. Unknown shops keep their name."""
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
    """No longer used — redirects are resolved via product page."""
    return url


def redirects_aufloesen_via_produktseite(source_url, shops):
    """
    Loads the Geizhals product page ONCE with Selenium,
    clicks each shop link and captures the final URL in a new tab.
    Returns a dict {shop_name -> real_url}.
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
        log(f"  URL resolution: Loading {source_url[:60]}")
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
                if (btn && btn.textContent.trim() !== 'No more offers') {
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
            if not ("geizhals.de/redir/" in redir_url or "geizhals.at/redir/" in redir_url or "geizhals.eu/redir/" in redir_url):
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
                    if "geizhals.de" not in final_url and "geizhals.at" not in final_url and "geizhals.eu" not in final_url:
                        ergebnis[shop_name] = final_url
                        log(f"  ✓ {shop_name}: {final_url[:50]}")
                    else:
                        log(f"  ✗ {shop_name}: redirect blocked")
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
        log(f"  URL resolution error: {e}")
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
    """Loads a URL with real Chrome."""
    if not SELENIUM_OK:
        return ""
    driver = None
    try:
        opts = Options()
        ist_geizhals = "geizhals.de" in url or "geizhals.eu" in url or "geizhals.at" in url or "geizhals.eu" in url
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
                    if (btn && btn.textContent.trim() !== 'No more offers') {
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
                    log(f"  More offers loaded (Klick {i+1})...")
                else:
                    break

        # PriceSpy: "Show more prices" button klicken
        ist_pricespy = "pricespy.co.uk" in url or "pricespy.com" in url
        if ist_pricespy:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            for i in range(10):
                try:
                    btn_el = driver.find_element(
                        By.XPATH,
                        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'more price')]"
                    )
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_el)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", btn_el)
                    log(f"  PriceSpy: more prices loaded (click {i+1})")
                    time.sleep(3)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                except:
                    break  # Button gone = all loaded

        return driver.page_source
    except Exception as e:
        log(f"Selenium error: {e}")
        return ""
    finally:
        if driver:
            try: driver.quit()
            except: pass


def shops_aus_url_laden(url, max_shops=999):
    """
    Loads all shops directly from a Geizhals or Idealo product page.
    Uses Selenium (real Chrome) so JavaScript content is loaded.
    """
    shops = []
    produkt_name = ""
    try:
        log(f"Loading URL: {url[:80]}")
        html = _selenium_get(url, wait=5)
        if not html:
            r = requests.get(url, headers=HEADERS, timeout=20)
            html = r.text
            log("Fallback: regular HTTP request")

        soup = BeautifulSoup(html, "html.parser")

        # Produktname
        for sel in ["h1.variant__header__headline","h1[class*=headline]",
                    "h1[class*=product]","h1[class*=title]","h1"]:
            el = soup.select_one(sel)
            if el:
                produkt_name = el.get_text(strip=True)[:80]
                break

        anbieter = set()
        ist_geizhals = "geizhals.de" in url or "geizhals.eu" in url or "geizhals.at" in url or "geizhals.eu" in url
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
                    log(f"Offer parse error: {e}")
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
        log(f"Total: {len(shops)} Shops von {url[:60]}")
        return shops, produkt_name
    except Exception as e:
        log(f"Error loading: {e}")
        return [], ""


def geizhals_suchen(suchbegriff, max_shops=999):
    """Sucht auf Geizhals (DE + EU), Fallback auf Idealo."""
    log(f"Search: '{suchbegriff}'")
    try:
        # Geizhals: DE first, then EU (both .de and .eu domains)
        for base, hloc in [
            ("https://geizhals.de", "de"),
            ("https://geizhals.de", "de,at,ch,eu,uk"),
            ("https://geizhals.eu", "de,at,ch,eu,uk,pl"),
        ]:
            # Suche nach Relevanz (kein sort=p damit nicht Zubehör zuerst kommt)
            such_url = "{}/?fs={}&bl=&hloc={}&in=&v=e&sort=n".format(
                base, requests.utils.quote(suchbegriff), hloc)
            log(f"Geizhals search ({hloc}): {such_url[:80]}")
            html = _selenium_get(such_url, wait=4)
            if not html:
                r = requests.get(such_url, headers=HEADERS, timeout=20)
                html = r.text
            soup = BeautifulSoup(html, "html.parser")

            # Produktlink finden — URL-Slug basiertes Scoring
            produkt_link = None
            suchwoerter = suchbegriff.lower().split()

            gesehen = set()
            kandidaten = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if not re.search(r"-a\d{4,}\.htm", href): continue
                basis = re.sub(r"[#?].*", "", href)
                if basis in gesehen: continue
                gesehen.add(basis)

                # URL-Slug als Produktname (Geizhals rendert Namen per JS)
                slug = basis.split("/")[-1].lower()
                slug_clean = re.sub(r"-a\d+.*", "", slug).replace("-", " ")

                # Relevanz: Suchwörter im URL-Slug
                wort_treffer = sum(1 for w in suchwoerter if w in slug_clean)
                # Bonus: alle Wörter vorhanden
                alle_bonus = 3 if wort_treffer == len(suchwoerter) else 0
                # Malus: Zubehör-Keywords in URL
                zubehoer = ["screen-protector","schutzglas","huelle","case","cover",
                            "kameraschutz","lens","wallet","folie","panzerglass",
                            "protector","displayschutz","hard-case","tpu","glass",
                            "schutzfolie","hulle","bumper","strap"]
                malus = sum(3 for z in zubehoer if z in slug)

                score = wort_treffer + alle_bonus - malus
                kandidaten.append((score, basis, slug_clean[:60]))

            if kandidaten:
                kandidaten.sort(key=lambda x: x[0], reverse=True)
                bester_score, produkt_link, slug_text = kandidaten[0]
                log(f"Best match (score {bester_score}): '{slug_text}'")
                for s, h, t in kandidaten[:3]:
                    log(f"  [{s:+d}] {t[:55]}")

            if not produkt_link and kandidaten:
                produkt_link = kandidaten[0][1]

            if produkt_link:
                if not produkt_link.startswith("http"):
                    produkt_link = "https://geizhals.de" + produkt_link
                log(f"Product page: {produkt_link}")
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

        log("No shops found on Geizhals/Idealo")
        return [], suchbegriff
    except Exception as e:
        log(f"Search error: {e}")
        return [], suchbegriff, ""


def pricespy_laden(url, max_shops=999):
    """Loads all shops from a PriceSpy product page."""
    shops = []
    produkt_name = ""
    try:
        log(f"Loading PriceSpy: {url[:60]}")
        html = _selenium_get(url, wait=5)
        if not html:
            r = requests.get(url, headers=HEADERS, timeout=20)
            html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # Product name
        h1 = soup.find("h1")
        if h1:
            produkt_name = h1.get_text(strip=True)[:80]

        def _parse_gbp(text):
            m = re.search(r"£\s*(\d{1,4}[.,]\d{2})", text)
            if m:
                c = m.group(1).replace(",",".")
                try: return float(c)
                except: pass
            return None

        # Parse shops from pj-ui-price-row
        for row in soup.find_all(class_="pj-ui-price-row")[:max_shops]:
            try:
                text  = row.get_text(" ", strip=True)
                price = _parse_gbp(text)
                if not price: continue

                # Shop name
                store_el = row.find(class_=re.compile("StoreInfoTitle"))
                shop_name = store_el.get_text(strip=True) if store_el else ""

                # Direct shop link
                shop_url = url
                for a in row.find_all("a", href=True):
                    if "go-to-shop" in a["href"]:
                        href = a["href"]
                        if not href.startswith("http"):
                            href = "https://pricespy.co.uk" + href
                        shop_url = href
                        break

                if shop_name and price:
                    shops.append({
                        "name":     shop_name,
                        "url":      shop_url,
                        "preis":    price,
                        "shop_key": _shop_key_aus_name(shop_name),
                    })
            except: pass

        log(f"PriceSpy: {len(shops)} shops found")
        return shops, produkt_name
    except Exception as e:
        log(f"PriceSpy error: {e}")
        return [], ""


def pricespy_suchen(suchbegriff, max_shops=999):
    """Searches PriceSpy for a product."""
    try:
        such_url = "https://pricespy.co.uk/search.php?search={}".format(
            requests.utils.quote(suchbegriff))
        log(f"PriceSpy search: {such_url[:80]}")
        html = _selenium_get(such_url, wait=4)
        if not html:
            r = requests.get(such_url, headers=HEADERS, timeout=20)
            html = r.text
        soup = BeautifulSoup(html, "html.parser")

        # Find first product link
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "product.php?p=" in href:
                if not href.startswith("http"):
                    href = "https://pricespy.co.uk" + href
                log(f"PriceSpy product: {href[:80]}")
                return pricespy_laden(href, max_shops)
        return [], suchbegriff
    except Exception as e:
        log(f"PriceSpy search error: {e}")
        return [], suchbegriff


def amazon_suchen(suchbegriff):
    """Searches Amazon.de for a product and returns its direct URL."""
    try:
        url = "https://www.amazon.de/s?k={}".format(requests.utils.quote(suchbegriff))
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for el in soup.select("[data-asin]:not([data-asin=''])"):
            asin = el.get("data-asin","").strip()
            if not asin or len(asin) < 5: continue
            preis_el = el.select_one(".a-price .a-offscreen, .a-price-whole")
            preis = _parse(preis_el.get_text()) if preis_el else None
            titel_el = el.select_one("h2 span, .a-text-normal")
            titel = titel_el.get_text(strip=True)[:60] if titel_el else suchbegriff
            if asin and preis:
                produkt_url = f"https://www.amazon.de/dp/{asin}"
                return [{"name": "Amazon.de", "url": produkt_url,
                         "preis": preis, "shop_key": "amazon",
                         "shop_name": "Amazon.de"}], titel
        return [], suchbegriff
    except Exception as e:
        log(f"Amazon search error: {e}")
        return [], suchbegriff


def alle_quellen_suchen(suchbegriff, max_shops=999):
    """Main entry: searches on all sources."""
    return geizhals_suchen(suchbegriff, max_shops)


APP_VERSION = "1.6.0"
GITHUB_API  = "https://api.github.com/repos/erdem-basar/preis-alarm-tracker/releases/latest"

def check_for_update():
    """Checks GitHub for a newer version. Returns (new_version, release_url, zip_url) or (None, None, None)."""
    try:
        r = requests.get(GITHUB_API, timeout=8,
                         headers={"Accept": "application/vnd.github+json"})
        if r.status_code == 404:
            return None, None, None, None  # No releases yet
        if r.status_code == 200:
            data = r.json()
            latest   = data.get("tag_name","").lstrip("v").lstrip(".").strip()
            html_url = data.get("html_url","")
            zip_url  = data.get("zipball_url","")
            log(f"Update check: GitHub={latest} Local={APP_VERSION}")
            # Also check assets for a preis_alarm_tracker.zip
            for asset in data.get("assets", []):
                if asset["name"].endswith(".zip"):
                    zip_url = asset["browser_download_url"]
                    break
            notes = data.get("body", "No release notes available.")
            if latest and latest != APP_VERSION:
                # Only update if remote version is actually newer
                try:
                    def ver_tuple(v):
                        return tuple(int(x) for x in v.strip().split("."))
                    if ver_tuple(latest) > ver_tuple(APP_VERSION):
                        return latest, html_url, zip_url, notes
                except:
                    if latest != APP_VERSION:
                        return latest, html_url, zip_url, notes
            log(f"Update check: no update needed ({latest} <= {APP_VERSION})")
    except:
        pass
    return None, None, None


def email_preisaenderung(cfg, gruppe, geaenderte_shops):
    """Sends email with all shops that changed their price."""
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
                <a href="{url}" style="color:#378ADD;text-decoration:none">Open Shop</a>
              </td>
            </tr>"""

        from datetime import datetime as _dt
        html = f"""<html><body style="font-family:Arial;max-width:700px;margin:auto;
                   background:#0f0f0f;color:#f1f5f9;padding:24px">
        <div style="background:#1a3a5c;padding:16px;border-radius:8px;margin-bottom:20px">
          <h2 style="color:#60a5fa;margin:0">📊 Price Changes: {gruppe['name']}</h2>
          <p style="color:#94a3b8;margin:4px 0 0">{len(geaenderte_shops)} shop(s) changed their price</p>
        </div>
        <table style="width:100%;border-collapse:collapse">
          <tr style="background:#1a1a1a">
            <th style="padding:10px;text-align:left;color:#94a3b8">Shop</th>
            <th style="padding:10px;text-align:left;color:#94a3b8">Old Price</th>
            <th style="padding:10px;text-align:left;color:#94a3b8">New Price</th>
            <th style="padding:10px;text-align:left;color:#94a3b8">Change</th>
            <th style="padding:10px;text-align:left;color:#94a3b8">Link</th>
          </tr>
          {zeilen}
        </table>
        <p style="color:#6b7280;font-size:12px;margin-top:20px">
          Preis-Alarm Tracker · {_dt.now().strftime('%d.%m.%Y %H:%M')}
        </p>
        </body></html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📊 Price Changes: {gruppe['name']} ({len(geaenderte_shops)} shops)"
        msg["From"]    = formataddr(("Price Alert", cfg["email_absender"]))
        msg["To"]      = cfg["email_empfaenger"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"])) as s:
            s.starttls()
            s.login(cfg["email_absender"], cfg["email_passwort"])
            s.sendmail(cfg["email_absender"], cfg["email_empfaenger"], msg.as_string())
        log(f"  Price change email sent ({len(geaenderte_shops)} Shops)")
        return True
    except Exception as e:
        log(f"  Email error: {e}")
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
            betreff = f"🔔 {alarm_anzahl} Target Price Alert{'s' if alarm_anzahl>1 else ''} + {aender_anzahl} Price Change{'s' if aender_anzahl!=1 else ''}"
        else:
            betreff = f"📊 {aender_anzahl} Price Change{'s' if aender_anzahl!=1 else ''} in last check"

        # Alarm-Sektion
        alarm_html = ""
        if hat_alarme:
            alarm_zeilen = ""
            for a in alarme:
                g_cur = a.get('currency','€')
                alarm_zeilen += f"""
                <tr>
                  <td style="padding:10px;color:#f1f5f9;font-weight:bold">{a['name']}</td>
                  <td style="padding:10px;color:#22c55e;font-size:18px;font-weight:bold">{g_cur}{a['bester']:.2f}</td>
                  <td style="padding:10px;color:#f1f5f9">{a['shop']}</td>
                </tr>"""
            alarm_html = f"""
            <div style="background:#14532d;border-radius:8px;padding:16px;margin-bottom:20px">
              <h2 style="color:#4ade80;margin:0 0 12px">🔔 Target Price Reached!</h2>
              <table style="width:100%;border-collapse:collapse">
                <tr style="background:#166534">
                  <th style="padding:8px;text-align:left;color:#86efac">Product</th>
                  <th style="padding:8px;text-align:left;color:#86efac">Best Price</th>
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
                    ziel_badge = '<span style="background:#14532d;color:#4ade80;padding:2px 8px;border-radius:4px;font-size:11px;margin-left:6px">🎯 Target reached!</span>'
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
                  <th style="padding:8px;text-align:left;color:#94a3b8">Old Price</th>
                  <th style="padding:8px;text-align:left;color:#94a3b8">New Price</th>
                  <th style="padding:8px;text-align:left;color:#94a3b8">Link</th>
                </tr>
                {zeilen}
              </table>
            </div>"""

        html = f"""<html><body style="font-family:Arial;max-width:700px;margin:auto;
                   background:#0f0f0f;color:#f1f5f9;padding:24px">
          <div style="border-bottom:1px solid #2d2d2d;padding-bottom:12px;margin-bottom:20px">
            <h1 style="color:#f1f5f9;margin:0;font-size:20px">🔔 Price Alert Tracker</h1>
            <p style="color:#6b7280;margin:4px 0 0;font-size:12px">
              Check vom {_dt.now().strftime('%d.%m.%Y um %H:%M Uhr')}
            </p>
          </div>
          {alarm_html}
          {('<h2 style="color:#f1f5f9;margin:0 0 16px">📊 Price Changes</h2>' + aender_html) if hat_aenderungen else ''}
          <p style="color:#4b5563;font-size:11px;margin-top:24px;border-top:1px solid #1f2937;padding-top:12px">
            Preis-Alarm Tracker · Automatischer Check
          </p>
        </body></html>"""

        msg = MIMEMultipart("alternative")
        msg["Subject"] = betreff
        msg["From"]    = formataddr(("Price Alert", cfg["email_absender"]))
        msg["To"]      = cfg["email_empfaenger"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"])) as s:
            s.starttls()
            s.login(cfg["email_absender"], cfg["email_passwort"])
            s.sendmail(cfg["email_absender"], cfg["email_empfaenger"], msg.as_string())
        log(f"Summary email sent ({aender_anzahl} Änderungen, {alarm_anzahl} Alarme)")
    except Exception as e:
        log(f"Email error: {e}")


def email_senden(cfg, gruppe, bester_preis, bester_shop):
    try:
        alle = "".join(
            f"<tr><td style='padding:8px;color:#94a3b8'>{s.get('shop_name') or SHOPS.get(s['shop'],s['shop'])}</td>"
            f"<td style='padding:8px;{'font-weight:bold;color:#22c55e' if s.get('preis')==bester_preis else ''}'>"
            f"{s.get('preis',0):.2f} €</td>"
            f"<td><a href='{s['url']}' style='color:#378ADD'>Shop</a></td></tr>"
            for s in gruppe.get("shops",[]) if s.get("preis")
        )
        html = f"""<html><body style="font-family:Arial;max-width:600px;margin:auto;background:#0f0f0f;color:#f1f5f9;padding:24px">
        <h2 style="color:#4ade80">🏆 Preisvergleich-Alarm!</h2>
        <h3>{gruppe['name']}</h3>
        <p>Best Price: <strong style="color:#22c55e;font-size:20px">{bester_preis:.2f} €</strong> bei {bester_shop}</p>
        <table style="width:100%;border-collapse:collapse">{alle}</table>
        <p style="color:#6b7280;font-size:12px">{datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        </body></html>"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🏆 {gruppe['name']} from {gruppe.get('currency','€')}{bester_preis:.2f}"
        msg["From"]    = formataddr(("Price Alert", cfg["email_absender"]))
        msg["To"]      = cfg["email_empfaenger"]
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"])) as s:
            s.starttls()
            s.login(cfg["email_absender"], cfg["email_passwort"])
            s.sendmail(cfg["email_absender"], cfg["email_empfaenger"], msg.as_string())
        return True
    except Exception as e:
        log(f"Email error: {e}")
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
            log(f"Autostart set: {pfad}")
        else:
            try: winreg.DeleteValue(key, AUTOSTART_NAME)
            except: pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        log(f"Autostart error: {e}")
        return False

def tray_icon_erstellen():
    """Creates a proper bell icon for the tray."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    # Dark background circle
    d.ellipse([0, 0, size-1, size-1], fill="#1a1a1a")
    # Bell body
    d.ellipse([10, 12, 54, 46], fill="#22c55e")
    # Bell bottom flat
    d.rectangle([10, 28, 54, 46], fill="#22c55e")
    # Bell clapper
    d.ellipse([24, 44, 40, 56], fill="#22c55e")
    # Bell top stem
    d.rectangle([28, 4, 36, 14], fill="#22c55e")
    d.ellipse([24, 2, 40, 16], fill="#22c55e")
    # Shine effect
    d.ellipse([14, 14, 28, 26], fill="#4ade80")
    return img


def app_icon_erstellen():
    """Creates the window icon (32x32)."""
    size = 32
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.ellipse([0, 0, size-1, size-1], fill="#1a1a1a")
    d.ellipse([5, 6, 27, 23], fill="#22c55e")
    d.rectangle([5, 14, 27, 23], fill="#22c55e")
    d.ellipse([12, 22, 20, 28], fill="#22c55e")
    d.rectangle([14, 2, 18, 8], fill="#22c55e")
    d.ellipse([12, 1, 20, 9], fill="#22c55e")
    return img


# ── GUI ───────────────────────────────────────────────────────────────────────
class PreisAlarmApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(T("app_title"))
        # Restore last window position/size
        cfg = self.config_data if hasattr(self, "config_data") else lade_config()
        geo = cfg.get("window_geometry", "960x680")
        try:
            self.geometry(geo)
        except:
            self.geometry("960x680")
        self.minsize(800, 560)
        self.configure(bg=BG)
        # Save position on move/resize
        def _save_geo(e=None):
            try:
                self.config_data["window_geometry"] = self.geometry()
                speichere_config(self.config_data)
            except: pass
        self.bind("<Configure>", lambda e: self.after(500, _save_geo))
        self.vergleiche  = lade_vergleiche()
        self.config_data = lade_config()
        self._vg_shop_vars      = {}
        self.vg_aktuelle_gruppe = None
        self._setup_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._fenster_schliessen)
        # Set window icon
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
            elif TRAY_OK:
                icon_img = app_icon_erstellen()
                from PIL import ImageTk
                self._tk_icon = ImageTk.PhotoImage(icon_img)
                self.iconphoto(True, self._tk_icon)
        except: pass
        self._tray_icon = None
        self._tray_thread = None
        # Automatische Preisprüfung starten
        self._auto_check_starten()

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────
    def _btn(self, parent, text, cmd, bg=BG3, fg=TEXT):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         activebackground=bg, activeforeground=fg,
                         font=(UI_FONT, 10), relief="flat", cursor="hand2",
                         padx=14, pady=6, bd=0)

    def _aktuelle_vg(self):
        return next((g for g in self.vergleiche if g["id"] == self.vg_aktuelle_gruppe), None)

    # ── Style ──────────────────────────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, fieldbackground=BG3,
                    bordercolor=BORDER, troughcolor=BG2,
                    selectbackground=AKZENT, selectforeground="#000", font=(UI_FONT, 10))
        s.configure("Treeview", background=BG2, foreground=TEXT, fieldbackground=BG2,
                    rowheight=36, borderwidth=0, font=(UI_FONT, 10))
        s.configure("Treeview.Heading", background=BG3, foreground=TEXT2, relief="flat",
                    font=(UI_FONT, 9, "bold"), padding=[8, 10])
        s.map("Treeview",
              background=[("selected", BG3)],
              foreground=[("selected", AKZENT)])
        s.configure("TNotebook", background=BG2, borderwidth=0, tabmargins=[0,0,0,0])
        s.configure("TNotebook.Tab", background=BG2, foreground=GRAU,
                    padding=[20, 10], font=(UI_FONT, 10),
                    borderwidth=0, relief="flat")
        s.map("TNotebook.Tab",
              background=[("selected", BG2), ("active", BG2)],
              foreground=[("selected", TEXT), ("active", TEXT2)],
              expand=[("selected", [0, 0, 0, 0])])
        s.configure("TEntry", fieldbackground=BG3, foreground=TEXT, insertcolor=AKZENT,
                    bordercolor=BORDER, relief="flat", padding=8)
        s.configure("TCombobox", fieldbackground=BG3, foreground=TEXT,
                    selectbackground=AKZENT, selectforeground=BG,
                    arrowcolor=TEXT2, insertcolor=TEXT)
        s.map("TCombobox",
              fieldbackground=[("readonly", BG3)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", BG3)],
              selectforeground=[("readonly", TEXT)])
        s.configure("TScrollbar", background=BG2, troughcolor=BG,
                    arrowcolor=GRAU, borderwidth=0, relief="flat")
        s.map("TScrollbar", background=[("active", BG3)])

    # ── Haupt-UI ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Top accent bar
        tk.Frame(self, bg=AKZENT, height=2).pack(fill="x")

        # Header
        hdr = tk.Frame(self, bg=BG2)
        hdr.pack(fill="x")
        inner_hdr = tk.Frame(hdr, bg=BG2)
        inner_hdr.pack(fill="x", padx=24, pady=12)

        # Logo + title
        logo_f = tk.Frame(inner_hdr, bg=BG2)
        logo_f.pack(side="left")
        tk.Label(logo_f, text="🔔", bg=BG2, fg=AKZENT,
                 font=(UI_FONT, 20)).pack(side="left", padx=(0,10))
        title_f = tk.Frame(logo_f, bg=BG2)
        title_f.pack(side="left")
        tk.Label(title_f, text=T("app_title"), bg=BG2, fg=TEXT,
                 font=(UI_FONT, 16, "bold")).pack(anchor="w")
        tk.Label(title_f, text=T("subtitle") if "subtitle" in TRANSLATIONS.get(_current_lang(),{}) else T("subtitle") if "subtitle" in TRANSLATIONS.get(_current_lang(),{}) else T("subtitle"), bg=BG2, fg=GRAU,
                 font=(UI_FONT, 8)).pack(anchor="w")

        # Version badge
        ver_f = tk.Frame(inner_hdr, bg=BG3, cursor="hand2")
        ver_f.pack(side="left", padx=16)
        self.update_lbl = tk.Label(ver_f, text=f"v{APP_VERSION}", bg=BG3, fg=GRAU,
                                   font=(UI_FONT, 8, "bold"), padx=8, pady=3,
                                   cursor="hand2")
        self.update_lbl.pack()
        ver_f.bind("<Button-1>", lambda e: self._update_pruefen())
        self.update_lbl.bind("<Button-1>", lambda e: self._update_pruefen())

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Check for update in background after 3s
        self.after(3000, lambda: threading.Thread(target=self._update_check_bg, daemon=True).start())

        # Chrome-style custom tab bar
        tab_bar = tk.Frame(self, bg=BG2)
        tab_bar.pack(fill="x")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Tab content frames
        self.tab_vergleich = tk.Frame(self, bg=BG)
        self.tab_einst     = tk.Frame(self, bg=BG)
        self.tab_log       = tk.Frame(self, bg=BG)

        self._active_tab = [None]
        self._tab_btns   = {}

        def switch_tab(frame, btn_key):
            for f in [self.tab_vergleich, self.tab_einst, self.tab_log]:
                f.pack_forget()
            frame.pack(fill="both", expand=True)
            # Update tab indicators
            for key, (btn, ind) in self._tab_btns.items():
                if key == btn_key:
                    btn.config(fg=TEXT)
                    ind.config(bg=AKZENT)
                else:
                    btn.config(fg=GRAU)
                    ind.config(bg=BG2)
            self._active_tab[0] = btn_key

        tabs = [
            ("compare", T("tab_compare"), self.tab_vergleich),
            ("settings",T("tab_settings"),          self.tab_einst),
            ("log",     T("tab_log"),              self.tab_log),
        ]
        for key, label, frame in tabs:
            col = tk.Frame(tab_bar, bg=BG2)
            col.pack(side="left")
            btn = tk.Button(col, text=label, bg=BG2, fg=GRAU,
                            font=(UI_FONT, 10), relief="flat",
                            cursor="hand2", borderwidth=0,
                            activebackground=BG2, activeforeground=TEXT,
                            padx=4, pady=10,
                            command=lambda f=frame, k=key: switch_tab(f, k))
            btn.pack()
            ind = tk.Frame(col, bg=BG2, height=2)
            ind.pack(fill="x")
            self._tab_btns[key] = (btn, ind)

        self._tab_vergleich()
        self._tab_einstellungen()
        self._tab_log()
        switch_tab(self.tab_vergleich, "compare")

    # ── Tab: Preisvergleich ───────────────────────────────────────────────────
    def _tab_vergleich(self):
        f = self.tab_vergleich
        bar = tk.Frame(f, bg=BG2)
        bar.pack(fill="x")
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x")
        inner_bar = tk.Frame(bar, bg=BG2)
        inner_bar.pack(fill="x", padx=16, pady=10)
        self._btn(inner_bar, T("new_group"), self._vg_neu, AKZENT, "#000").pack(side="left", padx=(0,6))
        self.btn_pruefen = self._btn(inner_bar, T("check_all"), self._vg_alle_pruefen, BG3, TEXT)
        self.btn_pruefen.pack(side="left", padx=(0,6))
        self.status_check_lbl = tk.Label(inner_bar, text="", bg=BG2, fg=TEXT2, font=(UI_FONT, 9))
        self.status_check_lbl.pack(side="left", padx=10)
        self._btn(inner_bar, T("delete"), self._vg_loeschen, BG3, ROT).pack(side="right")

        pane = tk.Frame(f, bg=BG)
        pane.pack(fill="both", expand=True)

        left = tk.Frame(pane, bg=BG2, width=230)
        left.pack(side="left", fill="y", padx=(0,1))
        left.pack_propagate(False)
        lbl_f = tk.Frame(left, bg=BG2)
        lbl_f.pack(fill="x", padx=12, pady=(12,6))
        tk.Label(lbl_f, text=T("product_groups"), bg=BG2, fg=GRAU,
                 font=(UI_FONT, 8, "bold")).pack(side="left")
        self.vg_listbox = tk.Listbox(
            left, bg=BG2, fg=TEXT, selectbackground="#1e2040",
            selectforeground=AKZENT,
            font=(UI_FONT, 10), relief="flat", borderwidth=0, activestyle="none",
            highlightthickness=0)
        self.vg_listbox.pack(fill="both", expand=True)
        self.vg_listbox.bind("<<ListboxSelect>>", lambda e: self._vg_gruppe_waehlen())
        self.vg_listbox.bind("<Delete>",    lambda e: self._vg_loeschen())
        self.vg_listbox.bind("<BackSpace>", lambda e: self._vg_loeschen())

        # Drag & Drop to reorder groups
        self._drag_start_idx = None
        self._drag_indicator = None

        def _drag_start(e):
            self._drag_start_idx = self.vg_listbox.nearest(e.y)
            self.vg_listbox.config(cursor="fleur")

        def _drag_motion(e):
            idx = self.vg_listbox.nearest(e.y)
            if self._drag_start_idx is None or idx == self._drag_start_idx:
                return
            # Visual feedback - highlight drop target
            self.vg_listbox.selection_clear(0, "end")
            self.vg_listbox.selection_set(idx)

        def _drag_end(e):
            self.vg_listbox.config(cursor="")
            if self._drag_start_idx is None:
                return
            target_idx = self.vg_listbox.nearest(e.y)
            src = self._drag_start_idx
            self._drag_start_idx = None
            if src == target_idx or src < 0 or target_idx < 0:
                return
            if src >= len(self.vergleiche) or target_idx >= len(self.vergleiche):
                return
            # Reorder in data
            g = self.vergleiche.pop(src)
            self.vergleiche.insert(target_idx, g)
            speichere_vergleiche(self.vergleiche)
            # Reload listbox and reselect
            self.vg_aktuelle_gruppe = self.vergleiche[target_idx]
            self._vg_listbox_laden()
            self.vg_listbox.selection_set(target_idx)
            self.vg_listbox.see(target_idx)

        self.vg_listbox.bind("<ButtonPress-1>",  _drag_start)
        self.vg_listbox.bind("<B1-Motion>",      _drag_motion)
        self.vg_listbox.bind("<ButtonRelease-1>", _drag_end)

        right = tk.Frame(pane, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        hdr2 = tk.Frame(right, bg=BG)
        hdr2.pack(fill="x", padx=16, pady=(12,8))
        title_col = tk.Frame(hdr2, bg=BG)
        title_col.pack(side="left")
        self.vg_titel_lbl = tk.Label(title_col, text=T("select_group"),
                                     bg=BG, fg=TEXT2, font=(UI_FONT, 13, "bold"))
        self.vg_titel_lbl.pack(anchor="w")
        self.vg_ziel_lbl = tk.Label(title_col, text="", bg=BG, fg=AKZENT,
                                    font=(UI_FONT, 9))
        self.vg_ziel_lbl.pack(anchor="w")
        btn_col = tk.Frame(hdr2, bg=BG)
        btn_col.pack(side="right")
        self._btn(btn_col, "🤖 AI",       self._vg_ai_analyse,   BG3, PURPLE).pack(side="left", padx=(0,4))
        self._btn(btn_col, "📊 Stats",    self._vg_statistiken,  BG3, TEXT2).pack(side="left", padx=(0,4))
        self._btn(btn_col, T("price_history"),  self._vg_chart_zeigen, BG3, TEXT2).pack(side="left", padx=(0,4))
        self._btn(btn_col, T("add_url"),       self._vg_shop_manuell, BG3, GRAU).pack(side="left")

        # Sortier-Status: col -> bool (True=aufsteigend)
        self._sort_col   = "preis"
        self._sort_asc   = True

        cols = ("shop","url","preis","diff","status","zuletzt")
        self.vg_tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        col_defs = [("shop","Shop ↕",130),("url","URL ↕",270),("preis",T("cur_best")[:10]+"↕",95),
                    ("diff",T("target_price_lbl")+"↕",95),("status","Status ↕",110),("zuletzt",T("data_points")[:7]+"↕",110)]
        for col, text, w in col_defs:
            self.vg_tree.heading(col, text=text,
                                 command=lambda c=col: self._vg_sort_klick(c))
            self.vg_tree.column(col, width=w,
                                anchor="w" if col in ("shop","url","status","zuletzt") else "e")
        # Header separator line
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x")
        sb = ttk.Scrollbar(right, orient="vertical", command=self.vg_tree.yview)
        self.vg_tree.configure(yscrollcommand=sb.set)
        self.vg_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.vg_tree.bind("<Delete>",    lambda e: self._vg_shop_loeschen())
        self.vg_tree.bind("<BackSpace>", lambda e: self._vg_shop_loeschen())
        self.vg_tree.bind("<Double-1>",  lambda e: self._vg_shop_oeffnen())
        self.vg_tree.tag_configure("best",      foreground=AKZENT, font=(UI_FONT, 10, "bold"), background="#0d1f1a")
        self.vg_tree.tag_configure("alarm",     foreground=AKZENT)
        self.vg_tree.tag_configure("normal",    foreground=TEXT)
        self.vg_tree.tag_configure("fehler",    foreground=ROT)
        self.vg_tree.tag_configure("gesunken",  foreground="#6ee7b7", font=(UI_FONT, 10, "bold"), background="#0a1a14")
        self.vg_tree.tag_configure("gestiegen", foreground="#fbbf24", font=(UI_FONT, 10, "bold"), background="#1a1400")
        self._vg_listbox_laden()

    # ── Tab: Einstellungen ────────────────────────────────────────────────────
    def _tab_einstellungen(self):
        f = self.tab_einst
        # Scrollable settings
        canvas = tk.Canvas(f, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        wrap = tk.Frame(canvas, bg=BG)
        wrap_id = canvas.create_window((0,0), window=wrap, anchor="nw")
        def _on_resize(e):
            canvas.itemconfig(wrap_id, width=e.width)
        canvas.bind("<Configure>", _on_resize)
        wrap.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        # Mouse wheel scroll
        def _scroll(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _scroll)
        # Inner padding frame
        inner = tk.Frame(wrap, bg=BG)
        inner.pack(fill="both", expand=True, padx=40, pady=24)
        wrap = inner

        def section(text):
            tk.Label(wrap, text=text, bg=BG, fg=TEXT2,
                     font=(UI_FONT, 9, "bold")).pack(anchor="w", pady=(16,4))
            tk.Frame(wrap, bg=BORDER, height=1).pack(fill="x", pady=(0,8))

        def erow(label, var, show=""):
            r = tk.Frame(wrap, bg=BG)
            r.pack(fill="x", pady=5)
            tk.Label(r, text=label, bg=BG, fg=TEXT2, width=18, anchor="w",
                     font=(UI_FONT, 10)).pack(side="left")
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

        section("📧  " + T("email_config"))
        erow(T("sender_email"),  self.v_abs)
        erow(T("password"),         self.v_pw,  show="●")
        erow(T("recipient_email"), self.v_emp)
        erow("SMTP Server",      self.v_smtp)
        erow("SMTP Port",        self.v_port)

        section("⏱  " + T("check_interval"))
        r = tk.Frame(wrap, bg=BG)
        r.pack(fill="x", pady=5)
        tk.Label(r, text=T("interval_label"), bg=BG, fg=TEXT2, width=18, anchor="w",
                 font=(UI_FONT, 10)).pack(side="left")
        ttk.Entry(r, textvariable=self.v_int, width=6).pack(side="left", ipady=4)
        tk.Label(r, text=T("interval_hint"), bg=BG, fg=GRAU,
                 font=(UI_FONT, 9)).pack(side="left", padx=8)

        tk.Frame(wrap, bg=BORDER, height=1).pack(fill="x", pady=16)
        btn_row = tk.Frame(wrap, bg=BG)
        btn_row.pack(fill="x")
        self._btn(btn_row, T("save"),  self._cfg_speichern, AKZENT, "#000").pack(side="left", padx=(0,10), ipady=4)
        self._btn(btn_row, T("test_email"), self._test_email,    BG3, TEXT).pack(side="left", ipady=4)

        section("🖥  System")
        # Language
        lang_row = tk.Frame(wrap, bg=BG)
        lang_row.pack(fill="x", pady=5)
        tk.Label(lang_row, text=T("language"), bg=BG, fg=TEXT2,
                 width=18, anchor="w", font=(UI_FONT, 10)).pack(side="left")
        cur_lang = self.config_data.get("language","en")
        self.v_lang = tk.StringVar(value=LANGUAGES.get(cur_lang, LANGUAGES["en"]))
        lang_combo = ttk.Combobox(lang_row, textvariable=self.v_lang,
                                   values=list(LANGUAGES.values()),
                                   state="readonly", width=26,
                                   font=(UI_FONT, 10))
        lang_combo.pack(side="left", ipady=4)
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._lang_aendern())

        # Theme selector
        theme_row = tk.Frame(wrap, bg=BG)
        theme_row.pack(fill="x", pady=5)
        tk.Label(theme_row, text=T("theme"), bg=BG, fg=TEXT2,
                 width=18, anchor="w", font=(UI_FONT, 10)).pack(side="left")
        cur_theme = self.config_data.get("theme", "dark_mint")
        self.v_theme = tk.StringVar(value=THEMES.get(cur_theme, THEMES["dark_mint"])["name"])
        theme_combo = ttk.Combobox(theme_row, textvariable=self.v_theme,
                                    values=[t["name"] for t in THEMES.values()],
                                    state="readonly", width=26, font=(UI_FONT, 10))
        theme_combo.pack(side="left", ipady=4)
        tk.Label(theme_row, text=f"  ← {T('theme_hint')}", bg=BG, fg=GRAU,
                 font=(UI_FONT, 8)).pack(side="left")
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self._theme_aendern())

        # Font selector
        font_row = tk.Frame(wrap, bg=BG)
        font_row.pack(fill="x", pady=5)
        tk.Label(font_row, text=T("font_label"), bg=BG, fg=TEXT2,
                 width=18, anchor="w", font=(UI_FONT, 10)).pack(side="left")
        cur_font_id = self.config_data.get("font", "segoe")
        self.v_font = tk.StringVar(value=FONTS.get(cur_font_id, FONTS["segoe"])["label"])
        font_combo = ttk.Combobox(font_row, textvariable=self.v_font,
                                   values=[f["label"] for f in FONTS.values()],
                                   state="readonly", width=26, font=(UI_FONT, 10))
        font_combo.pack(side="left", ipady=4)
        font_combo.bind("<<ComboboxSelected>>", lambda e: self._font_aendern())

        sys_row = tk.Frame(wrap, bg=BG)
        sys_row.pack(fill="x", pady=5)
        self.v_autostart = tk.BooleanVar(value=autostart_aktiv())
        tk.Checkbutton(sys_row, variable=self.v_autostart,
                       bg=BG, fg=TEXT, activebackground=BG, selectcolor=BG3,
                       font=(UI_FONT, 10),
                       text=T("start_windows"),
                       command=self._autostart_toggle).pack(side="left")

        tray_row = tk.Frame(wrap, bg=BG)
        tray_row.pack(fill="x", pady=5)
        self.v_tray = tk.BooleanVar(value=self.config_data.get("minimize_to_tray", True))
        tk.Checkbutton(tray_row, variable=self.v_tray,
                       bg=BG, fg=TEXT, activebackground=BG, selectcolor=BG3,
                       font=(UI_FONT, 10),
                       text=T("minimize_tray"),
                       command=self._tray_toggle).pack(side="left")

        section("ℹ  " + T("smtp_presets"))
        SMTP_PRESETS = [
            ("GMX",          "mail.gmx.net",           587,  "@gmx.de / @gmx.net"),
            ("Web.de",       "smtp.web.de",             587,  "@web.de"),
            ("Freenet",      "mx.freenet.de",           587,  "@freenet.de"),
            ("T-Online",     "securesmtp.t-online.de",  465,  "@t-online.de"),
            ("1&1 / IONOS",  "smtp.1und1.de",           587,  "@1und1.de / @ionos.de"),
            ("Outlook/Live", "smtp.office365.com",      587,  "@outlook.com / @live.de / @hotmail.com"),
            ("Gmail",        "smtp.gmail.com",          587,  "@gmail.com  (App Password required)"),
            ("Yahoo",        "smtp.mail.yahoo.com",     587,  "@yahoo.com / @yahoo.de"),
            ("iCloud",       "smtp.mail.me.com",        587,  "@icloud.com / @me.com"),
            ("Posteo",       "posteo.de",               587,  "@posteo.de"),
            ("Mailbox.org",  "smtp.mailbox.org",        587,  "@mailbox.org"),
        ]
        presets_frame = tk.Frame(wrap, bg=BG)
        presets_frame.pack(fill="x", pady=(0,4))

        def apply_preset(server, port):
            self.v_smtp.set(server)
            self.v_port.set(str(port))

        for i, (name, server, port, hint) in enumerate(SMTP_PRESETS):
            row_f = tk.Frame(presets_frame, bg=BG)
            row_f.pack(fill="x", pady=2)
            btn = tk.Button(row_f, text=name, bg=BG3, fg=TEXT,
                            activebackground=AKZENT, activeforeground="#000",
                            font=(UI_FONT, 9, "bold"), relief="flat",
                            cursor="hand2", padx=10, pady=3, width=12,
                            command=lambda s=server, p=port: apply_preset(s, p))
            btn.pack(side="left", padx=(0,8))
            tk.Label(row_f, text=f"{server}  |  Port: {port}   {hint}",
                     bg=BG, fg=GRAU, font=(UI_FONT, 9), anchor="w").pack(side="left")

    # ── Tab: Log ──────────────────────────────────────────────────────────────
    def _tab_log(self):
        f = self.tab_log
        bar = tk.Frame(f, bg=BG)
        bar.pack(fill="x", padx=12, pady=(12,4))
        self._btn(bar, T("clear_log"), self._log_leeren, BG3, TEXT).pack(side="left")
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
        self.vg_ziel_lbl.config(text=f"{T('target_price_lbl')}: {g.get('currency','€')}{g['zielpreis']:.2f}")
        self._vg_tabelle_laden(g)

    def _vg_sort_klick(self, col):
        """Click on column header: toggle ascending/descending sort."""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True
        # Pfeil in Überschrift aktualisieren
        col_namen = {"shop":"Shop","url":"URL","preis":"Cur. Price",
                     "diff":T("target_price_lbl"),"status":"Status","zuletzt":T("data_points")[:7]}
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
            cur          = gruppe.get("currency", "€")
            # Price display with change arrow
            if preis and preis_vorher:
                diff  = preis - preis_vorher
                pfeil = "⬇" if diff < 0 else "⬆"
                p_str = f"{cur}{preis:.2f}  {pfeil} {abs(diff):.2f}"
            else:
                p_str = f"{cur}{preis:.2f}" if preis else "–"
            d_str    = f"{cur}{ziel:.2f}"
            ist_best = preis and bester and preis == bester
            alarm    = preis and preis <= ziel
            noch     = T("still_too_much").replace("{diff}", f"{preis-ziel:.2f} {cur}") if (preis and not alarm) else ""
            status   = T("best_price") if ist_best else (T("target_reached") if alarm else (f"⬇ {noch}" if preis else T("no_price")))
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
        dlg.title("New Product Group")
        dlg.geometry("560x440")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text=T("search_hint"),
                 bg=BG, fg=TEXT2, font=(UI_FONT, 10)).pack(anchor="w", padx=20, pady=(16,4))
        tk.Label(dlg, text=T("url_tip"),
                 bg=BG, fg=GRAU, font=(UI_FONT, 8)).pack(anchor="w", padx=20)

        such_row = tk.Frame(dlg, bg=BG)
        such_row.pack(fill="x", padx=20, pady=(6,0))
        e_such = ttk.Entry(such_row, font=(UI_FONT, 10))
        e_such.pack(side="left", fill="x", expand=True, ipady=5)
        e_such.focus()

        status_lbl = tk.Label(dlg, text="", bg=BG, fg=TEXT2, font=(UI_FONT, 9), anchor="w")
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
        tk.Label(ziel_row, text=T("target_price")+" (€)", bg=BG, fg=TEXT2, width=14,
                 anchor="w", font=(UI_FONT, 10)).pack(side="left")
        e_ziel = ttk.Entry(ziel_row)
        e_ziel.pack(side="left", fill="x", expand=True, ipady=5)
        tk.Label(ziel_row, text=T("alert_hint"),
                 bg=BG, fg=GRAU, font=(UI_FONT, 9)).pack(side="left")

        gefunden = []
        gefundene_source_url = [""]  # Mutable container for thread

        def suchen(*_):
            eingabe = e_such.get().strip()
            if not eingabe: return
            for w in inner.winfo_children(): w.destroy()
            self._vg_shop_vars.clear()
            gefunden.clear()
            btn_such.config(state="disabled", text="  ⏳  ")
            ist_url = eingabe.startswith("http") and any(
                d in eingabe for d in [
                    "geizhals.de", "geizhals.eu", "geizhals.at",
                    "pricespy.co.uk", "pricespy.com",
                    "amazon.de", "amazon.co.uk", "amazon.com",
                ])
            status_lbl.config(
                text=T("loading_url") if ist_url else T("searching"),
                fg=TEXT2)

            def _thread():
                if ist_url:
                    if any(d in eingabe for d in ["pricespy.co.uk","pricespy.com"]):
                        shops, name = pricespy_laden(eingabe)
                    elif any(d in eingabe for d in ["amazon.de","amazon.co.uk","amazon.com"]):
                        # Single Amazon product URL — fetch price directly
                        shop = _shop_aus_url(eingabe)
                        p = preis_holen(eingabe, shop)
                        shops = [{"name": "Amazon.de", "url": eingabe,
                                  "preis": p, "shop_key": "amazon",
                                  "shop_name": "Amazon.de"}] if p else []
                        name = eingabe
                    else:
                        shops, name = shops_aus_url_laden(eingabe)
                    gefundene_source_url[0] = eingabe
                else:
                    result = alle_quellen_suchen(eingabe)
                    shops, name = result[0], result[1]
                    if len(result) > 2:
                        gefundene_source_url[0] = result[2]
                    # If no results on Geizhals, try Amazon
                    if not shops:
                        shops, name = amazon_suchen(eingabe)
                self.after(0, lambda: _fertig(shops, name))

            threading.Thread(target=_thread, daemon=True).start()

        def _fertig(shops, name):
            btn_such.config(state="normal", text=T("search_btn"))
            if not shops:
                status_lbl.config(
                    text="⚠  No shops found. Tip: Paste a shop URL directly or use '+ Add URL'.",
                    fg=GELB)
                return
            status_lbl.config(
                text=f"✅  {len(shops)} shops found — uncheck to exclude:",
                fg=AKZENT)
            gefunden.extend(shops)
            # Produktname als Gruppenname vorschlagen
            if name and name != e_such.get().strip():
                e_such.delete(0, "end")
                e_such.insert(0, name)

            ctrl = tk.Frame(inner, bg=BG)
            ctrl.pack(fill="x", pady=(0,4))
            tk.Button(ctrl, text=T("all_btn"),  bg=BG3, fg=TEXT2, font=(UI_FONT,8), relief="flat", padx=6, pady=2,
                      command=lambda: [v.set(True)  for v,_ in self._vg_shop_vars.values()]).pack(side="left", padx=(0,4))
            tk.Button(ctrl, text=T("none_btn"), bg=BG3, fg=TEXT2, font=(UI_FONT,8), relief="flat", padx=6, pady=2,
                      command=lambda: [v.set(False) for v,_ in self._vg_shop_vars.values()]).pack(side="left")

            min_preis = min(s["preis"] for s in shops)
            # Detect currency from entered URL
            eingabe_cur = e_such.get().strip()
            dialog_cur = "£" if any(d in eingabe_cur for d in ["pricespy.co.uk","pricespy.com"]) else "€"
            for i, s in enumerate(shops):
                var = tk.BooleanVar(value=True)
                self._vg_shop_vars[str(i)] = (var, s)
                row_f = tk.Frame(inner, bg=BG)
                row_f.pack(fill="x", pady=1)
                tk.Checkbutton(row_f, variable=var, bg=BG, fg=TEXT,
                               activebackground=BG, selectcolor=BG3,
                               font=(UI_FONT,9)).pack(side="left")
                tk.Label(row_f, text=s["name"], bg=BG, fg=TEXT,
                         font=(UI_FONT,9,"bold"), width=24, anchor="w").pack(side="left")
                col = AKZENT if s["preis"] == min_preis else TEXT2
                tk.Label(row_f, text=f"{dialog_cur}{s['preis']:.2f}", bg=BG, fg=col,
                         font=(UI_FONT,9,"bold"), width=9, anchor="e").pack(side="left")

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
                messagebox.showerror("Error", "Please enter a name.", parent=dlg); return
            try:
                ziel = float(e_ziel.get().replace(",","."))
            except:
                messagebox.showerror("Error", "Please enter a valid target price.", parent=dlg); return

            # Geizhals/Idealo URL merken für spätere Preisaktualisierungen
            eingabe_url = e_such.get().strip()
            if eingabe_url.startswith("http") and any(
                    d in eingabe_url for d in [
                        "geizhals.de", "geizhals.eu", "geizhals.at",
                        "pricespy.co.uk", "pricespy.com",
                    ]):
                source_url = eingabe_url
            elif eingabe_url.startswith("http") and any(
                    d in eingabe_url for d in ["amazon.de","amazon.co.uk","amazon.com"]):
                source_url = eingabe_url  # Direct Amazon URL
            elif gefundene_source_url[0]:
                source_url = gefundene_source_url[0]
            else:
                source_url = ""
            log(f"Group source_url: {source_url[:60]}" if source_url else "Gruppe ohne source_url")
            # Detect currency from source
            ist_gbp = any(d in source_url for d in ["pricespy.co.uk","pricespy.com"]) if source_url else False
            waehrung = "£" if ist_gbp else "€"
            g = {"id": str(int(time.time()*1000)), "name": name, "zielpreis": ziel,
                 "shops": [], "alarm_gesendet": False, "source_url": source_url,
                 "currency": waehrung}
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
                    "geizhals.de/redir/" in s.get("url","") or "geizhals.at/redir/" in s.get("url","") or "geizhals.eu/redir/" in s.get("url","")
                    for s in g["shops"]
                )
                if not hat_redirects:
                    return
                gesamt = len([s for s in g["shops"] if "redir" in s.get("url","")])
                self.after(0, lambda: self.status_check_lbl.config(
                    text=f"🔗 Resolving {gesamt} shop URLs (one-time, ~{gesamt//3+1} min.)...",
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
                    text=f"✅ {aufgeloest}/{gesamt} URLs resolved", fg=AKZENT))
                ag = self._aktuelle_vg()
                if ag and ag["id"] == g["id"]:
                    self.after(0, lambda: self._vg_tabelle_laden(ag))

            threading.Thread(target=_urls_aufloesen, daemon=True).start()

        btn_such = self._btn(such_row, T("search_btn"), suchen, BG3, AKZENT)
        btn_such.pack(side="left", padx=(8,0), ipady=5)
        e_such.bind("<Return>", suchen)
        e_ziel.bind("<Return>", speichern)
        self._btn(dlg, T("create_group"), speichern, AKZENT, "#000").pack(
            padx=20, pady=(10,12), fill="x", ipady=8)
        dlg.lift()
        dlg.focus_force()

    # ── Shop manuell hinzufügen ───────────────────────────────────────────────
    def _vg_shop_manuell(self):
        g = self._aktuelle_vg()
        if not g:
            messagebox.showinfo("Info", "Please select a group first."); return
        dlg = tk.Toplevel(self)
        dlg.title(f"Add Shop — {g['name']}")
        dlg.geometry("520x200")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Product URL", bg=BG, fg=TEXT2,
                 font=(UI_FONT,10)).pack(anchor="w", padx=20, pady=(16,4))
        url_row = tk.Frame(dlg, bg=BG)
        url_row.pack(fill="x", padx=20)
        e_url = ttk.Entry(url_row)
        e_url.pack(side="left", fill="x", expand=True, ipady=5)
        e_url.focus()
        status_lbl = tk.Label(dlg, text="", bg=BG, fg=TEXT2, font=(UI_FONT,9), anchor="w")
        status_lbl.pack(fill="x", padx=20, pady=4)
        preis_var = tk.StringVar()

        def laden():
            url = e_url.get().strip()
            if not url.startswith("http"): return
            status_lbl.config(text="🔄  Loading price...", fg=TEXT2)
            def _t():
                shop = _shop_aus_url(url)
                p = preis_holen(url, shop)
                self.after(0, lambda: (
                    preis_var.set(f"{p:.2f}" if p else ""),
                    status_lbl.config(
                        text=f"✅ {p:.2f} €" if p else "⚠ Not found — please enter manually",
                        fg=AKZENT if p else GELB)
                ))
            threading.Thread(target=_t, daemon=True).start()

        self._btn(url_row, "🔍", laden, BG3, TEXT).pack(side="left", padx=(6,0), ipady=5)

        preis_row = tk.Frame(dlg, bg=BG)
        preis_row.pack(fill="x", padx=20, pady=4)
        tk.Label(preis_row, text="Price (€)", bg=BG, fg=TEXT2, width=10, anchor="w",
                 font=(UI_FONT,10)).pack(side="left")
        ttk.Entry(preis_row, textvariable=preis_var, width=10).pack(side="left", ipady=4)

        def hinzufuegen(*_):
            url = e_url.get().strip()
            if not url.startswith("http"):
                messagebox.showerror("Error", "Invalid URL.", parent=dlg); return
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
        self._btn(dlg, "➕  Add", hinzufuegen, AKZENT, "#000").pack(
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
        if messagebox.askyesno("Delete", f"Delete group '{g['name']}'?"):
            self.vergleiche = [x for x in self.vergleiche if x["id"] != g["id"]]
            self.vg_aktuelle_gruppe = None
            speichere_vergleiche(self.vergleiche)
            self.vg_titel_lbl.config(text="← Select a group or create new")
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
        if messagebox.askyesno("Remove",
                               f"'{shop.get('shop_name') or SHOPS.get(shop['shop'], shop['shop'])}' remove from group?"):
            g["shops"] = [s for s in g["shops"] if s["id"] != sel[0]]
            speichere_vergleiche(self.vergleiche)
            self._vg_tabelle_laden(g)

    # ── Preise prüfen ─────────────────────────────────────────────────────────
    def _vg_alle_pruefen(self):
        if not self.vergleiche:
            self.status_check_lbl.config(text="⚠ No groups available", fg=GELB)
            return
        self.btn_pruefen.config(state="disabled", text=T("checking"))
        self.status_check_lbl.config(text="Fetching prices...", fg=TEXT2)
        threading.Thread(target=self._vg_check_alle, daemon=True).start()

    def _vg_check_alle(self):
        log("Price check started")
        gesamt_shops = sum(len(g["shops"]) for g in self.vergleiche)
        geprueft = 0
        alarme = []
        alle_aenderungen = []  # {gruppe_name, gruppe_ziel, shops: [...]}
        geaenderte_shops = []  # Shops with price change for current group

        for g in self.vergleiche:
            self.after(0, lambda name=g["name"]: self.status_check_lbl.config(
                text=f"🔄  Checking: {name[:30]}...", fg=TEXT2))

            source_url = g.get("source_url", "")
            ts = datetime.now().strftime("%d.%m. %H:%M")

            is_pricespy = any(d in source_url for d in ["pricespy.co.uk","pricespy.com"]) if source_url else False
            if source_url and ("geizhals.de" in source_url or "geizhals.eu" in source_url or is_pricespy):
                # ── Geizhals/Idealo: Produktseite komplett neu laden
                log(f"  Loading product page: {source_url[:60]}")
                if is_pricespy:
                    neue_shops, _ = pricespy_laden(source_url, max_shops=999)
                else:
                    neue_shops, _ = shops_aus_url_laden(source_url, max_shops=999)
                if neue_shops:
                    # Preis-Map: Name (lowercase) → Preis
                    preis_map = {s["name"].lower().strip(): s["preis"] for s in neue_shops}
                    log(f"  Found: {list(preis_map.keys())[:5]}...")
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
                                if "geizhals.de/redir/" in shop_url or "geizhals.at/redir/" in shop_url or "geizhals.eu/redir/" in shop_url:
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
                            log(f"  {name_anzeige}: {preis:.2f} ✓")
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
                            shop_url = source_url if ("geizhals.de/redir/" in ns["url"] or "geizhals.at/redir/" in ns["url"] or "geizhals.eu/redir/" in ns["url"]) else ns["url"]
                            g["shops"].append({
                                "id":        str(int(time.time()*1000)) + ns["name"][:5],
                                "url":       shop_url,
                                "url_redir": ns["url"],
                                "shop":      ns["shop_key"],
                                "shop_name": ns["name"],
                                "preis":     ns["preis"],
                                "zuletzt":   ts,
                            })
                            log(f"  New shop added: {ns['name']} ({ns['preis']:.2f} €)")

                    # Nicht mehr gelistete Shops entfernen
                    vorher = len(g["shops"])
                    g["shops"] = [
                        s for s in g["shops"]
                        if (s.get("shop_name") or s["shop"]).lower() in geizhals_namen
                    ]
                    entfernt = vorher - len(g["shops"])
                    if entfernt > 0:
                        log(f"  {entfernt} shop(s) no longer on Geizhals — removed")
                else:
                    log(f"  Product page could not be loaded")
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
                log(f"  {g['name']}: {g.get('currency','€')}{bester:.2f} at {bester_shop}")

                # Zielpreis-Alarm (Toast bleibt, Mail kommt in Zusammenfassung)
                if bester <= g["zielpreis"] and not g.get("alarm_gesendet"):
                    g["alarm_gesendet"] = True
                    alarme.append({"name": g["name"], "bester": bester, "shop": bester_shop, "currency": g.get("currency","€")})
                    toast("🏆 Price Alert!",
                          f"{g['name']}: {g.get('currency','€')}{bester:.2f} at {bester_shop}")
                elif bester > g["zielpreis"]:
                    g["alarm_gesendet"] = False

                # Änderungen sammeln für Gesamt-Mail am Ende
                if geaenderte_shops:
                    gesunken  = len([s for s in geaenderte_shops if s["preis_neu"] < s["preis_alt"]])
                    gestiegen = len([s for s in geaenderte_shops if s["preis_neu"] > s["preis_alt"]])
                    log(f"  Price changes: {gesunken} decreased, {gestiegen} increased")
                    # Zielpreis-Info pro Shop hinzufügen
                    for s in geaenderte_shops:
                        s["zielpreis"]       = g["zielpreis"]
                        s["ziel_erreicht"]   = s["preis_neu"] <= g["zielpreis"]
                    alle_aenderungen.append({
                        "gruppe_name": g["name"],
                        "zielpreis":   g["zielpreis"],
                        "currency":    g.get("currency", "€"),
                        "shops":       list(geaenderte_shops),
                    })

            geaenderte_shops = []  # Reset for next group

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
            self.btn_pruefen.config(state="normal", text=T("check_all"))
            if alarme:
                self.status_check_lbl.config(
                    text=f"🔔 Alert! {alarme[0]['name']}: {alarme[0].get('currency','€')}{alarme[0]['bester']:.2f}", fg=AKZENT)
            else:
                self.status_check_lbl.config(
                    text=T("prices_checked").replace("{n}", str(geprueft)).replace("{ts}", ts), fg=AKZENT)
            self._vg_listbox_laden()
            ag = self._aktuelle_vg()
            if ag:
                self._vg_tabelle_laden(ag)
            self._log_refresh()

        self.after(0, _fertig)
        # Gruppen ohne source_url hinweisen
        ohne_quelle = [g["name"] for g in self.vergleiche if not g.get("source_url")]
        if ohne_quelle:
            log(f"  Note: {len(ohne_quelle)} Gruppe(n) ohne Geizhals-URL — Gruppe löschen und neu anlegen für automatische Updates")
        log(f"Price check completed ({geprueft} Shops)")

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
        messagebox.showinfo("Saved", "Settings saved successfully.")

    def _test_email(self):
        if not self.config_data.get("email_absender"):
            messagebox.showerror("Error", "Please save settings first."); return
        ok = email_senden(self.config_data, {"name":"Test","shops":[]}, 99.99, "Testshop")
        if ok:
            messagebox.showinfo("Success", "Test email sent successfully!")
        else:
            messagebox.showerror("Error", "Email could not be sent.")

    # ── Autostart & Tray ─────────────────────────────────────────────────────
    def _lang_aendern(self):
        """Switch language live — no restart needed."""
        selected = self.v_lang.get()
        lang_code = next((k for k, v in LANGUAGES.items() if v == selected), "en")
        self.config_data["language"] = lang_code
        speichere_config(self.config_data)
        self._rebuild_ui()

    def _font_aendern(self):
        """Switch font live — no restart needed."""
        selected_label = self.v_font.get()
        font_id = next((k for k, v in FONTS.items() if v["label"] == selected_label), "segoe")
        self.config_data["font"] = font_id
        speichere_config(self.config_data)
        global UI_FONT
        UI_FONT = FONTS[font_id]["name"]
        self._rebuild_ui()

    def _rebuild_ui(self):
        """Rebuild entire UI with current language and font."""
        # Remember active tab
        active = self._active_tab[0] if self._active_tab else "compare"
        # Destroy everything below the accent bar
        for widget in self.winfo_children():
            widget.destroy()
        # Reset state
        self._tab_btns = {}
        self._active_tab = [None]
        # Rebuild
        self._build_ui()
        # Restore active tab
        tab_map = {
            "compare":  self.tab_vergleich,
            "settings": self.tab_einst,
            "log":      self.tab_log,
        }
        if active in self._tab_btns and active in tab_map:
            btn, ind = self._tab_btns[active]
            for f in [self.tab_vergleich, self.tab_einst, self.tab_log]:
                f.pack_forget()
            tab_map[active].pack(fill="both", expand=True)
            for key, (b, i) in self._tab_btns.items():
                b.config(fg=TEXT if key == active else GRAU)
                i.config(bg=AKZENT if key == active else BG2)
            self._active_tab[0] = active
        # Reload group list
        self._vg_laden()

    def _theme_aendern(self):
        """Switch theme and restart app."""
        selected_name = self.v_theme.get()
        theme_id = next((k for k, v in THEMES.items() if v["name"] == selected_name), "dark_mint")
        self.config_data["theme"] = theme_id
        speichere_config(self.config_data)
        import subprocess as _sp
        script = str(Path(__file__).resolve())
        exe = sys.executable.replace("python.exe", "pythonw.exe")
        if not Path(exe).exists():
            exe = sys.executable
        _sp.Popen([exe, script], creationflags=getattr(_sp, "DETACHED_PROCESS", 0))
        self.after(300, self.destroy)

    def _autostart_toggle(self):
        aktiv = self.v_autostart.get()
        if autostart_setzen(aktiv):
            msg = "Autostart enabled." if aktiv else "Autostart disabled."
            self.status_check_lbl.config(text=f"✅ {msg}", fg=AKZENT)
        else:
            messagebox.showerror("Error", "Autostart could not be set.")
            self.v_autostart.set(not aktiv)

    def _tray_toggle(self):
        self.config_data["minimize_to_tray"] = self.v_tray.get()
        speichere_config(self.config_data)

    def _fenster_schliessen(self):
        """X button: minimize to tray or quit depending on setting."""
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
            TrayItem(T("app_title"), zeigen, default=True),
            TrayItem("🔄 Check Now",         pruefen),
            pystray.Menu.SEPARATOR,
            TrayItem("❌ Quit",               beenden),
        )
        # Use icon.ico for tray if available
        icon_path = Path(__file__).parent / "icon.ico"
        if icon_path.exists():
            from PIL import Image as _PilImg
            img = _PilImg.open(str(icon_path))
        else:
            img = tray_icon_erstellen()
        self._tray_icon = pystray.Icon("PreisAlarm", img, "Price Alert Tracker", menu)
        self._tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        self._tray_thread.start()

    def _beenden(self):
        if self._tray_icon:
            try: self._tray_icon.stop()
            except: pass
        self.destroy()

    def _auto_check_starten(self):
        """Starts automatic price check — immediately on start, then every X hours."""
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

    # ── AI Analysis ───────────────────────────────────────────────────────────
    def _vg_ai_analyse(self):
        g = self._aktuelle_vg()
        if not g:
            messagebox.showinfo("Info", "Please select a group first.")
            return
        shops  = g.get("shops", [])
        cur    = g.get("currency", "€")
        ziel   = g["zielpreis"]

        # Collect price history
        alle_punkte = []
        for s in shops:
            for e in s.get("verlauf", []):
                try:
                    from datetime import datetime as _dt
                    ts = _dt.strptime(e["datum"][:16], "%Y-%m-%d %H:%M").timestamp()
                    alle_punkte.append((ts, e["preis"]))
                except: pass
        alle_punkte.sort()

        preise_aktuell = [s["preis"] for s in shops if s.get("preis")]
        if not preise_aktuell:
            messagebox.showinfo("Info", "No prices available yet. Run a check first.")
            return

        preis_jetzt = min(preise_aktuell)
        preis_avg   = sum(preise_aktuell) / len(preise_aktuell)

        # ── Analyse-Algorithmen ────────────────────────────────────────────────
        import statistics as _stats

        # 1. Trendanalyse (lineare Regression)
        trend_text = "Not enough data"
        trend_pct  = 0
        if len(alle_punkte) >= 3:
            xs = [p[0] for p in alle_punkte]
            ys = [p[1] for p in alle_punkte]
            n  = len(xs)
            x_mean = sum(xs) / n
            y_mean = sum(ys) / n
            num   = sum((xs[i]-x_mean)*(ys[i]-y_mean) for i in range(n))
            denom = sum((xs[i]-x_mean)**2 for i in range(n))
            slope = num/denom if denom != 0 else 0
            # Slope per day
            slope_per_day = slope * 86400
            trend_pct = (slope_per_day / y_mean) * 100 if y_mean else 0
            if trend_pct < -0.5:
                trend_text = f"📉 Falling  ({trend_pct:.1f}%/day)"
            elif trend_pct > 0.5:
                trend_text = f"📈 Rising  (+{trend_pct:.1f}%/day)"
            else:
                trend_text = f"➡ Stable  ({trend_pct:+.1f}%/day)"

        # 2. Volatilität
        volatil_text = "Not enough data"
        if len(alle_punkte) >= 4:
            vals = [p[1] for p in alle_punkte]
            try:
                std = _stats.stdev(vals)
                cv  = (std / _stats.mean(vals)) * 100
                if cv < 2:
                    volatil_text = f"🟢 Very stable  (±{cv:.1f}%)"
                elif cv < 5:
                    volatil_text = f"🟡 Moderate  (±{cv:.1f}%)"
                else:
                    volatil_text = f"🔴 Volatile  (±{cv:.1f}%)"
            except: pass

        # 3. Saisonale Muster
        saison_text = ""
        if len(alle_punkte) >= 10:
            from datetime import datetime as _dt
            monat_preise = {}
            for ts, pr in alle_punkte:
                m = _dt.fromtimestamp(ts).month
                monat_preise.setdefault(m, []).append(pr)
            if monat_preise:
                guenstigster_monat = min(monat_preise, key=lambda m: sum(monat_preise[m])/len(monat_preise[m]))
                monate = ["Jan","Feb","Mar","Apr","May","Jun",
                          "Jul","Aug","Sep","Oct","Nov","Dec"]
                saison_text = f"Historically cheapest in {monate[guenstigster_monat-1]}"

        # 4. Kaufempfehlung
        abstand_zum_ziel = ((preis_jetzt - ziel) / ziel) * 100 if ziel else 0

        if preis_jetzt <= ziel:
            empfehlung = T("buy_now")
            empf_grund = f"{T('at_target')} ({cur}{ziel:.2f})"
            empf_farbe = "#22c55e"
        elif len(alle_punkte) >= 3 and trend_pct < -0.3 and abstand_zum_ziel < 15:
            empfehlung = T("wait_falling")
            empf_grund = T("above_target_falling").replace("{pct}", f"{abstand_zum_ziel:.1f}")
            empf_farbe = "#f59e0b"
        elif len(alle_punkte) >= 3 and trend_pct > 0.5:
            empfehlung = T("buy_soon")
            empf_grund = T("price_rising_grund")
            empf_farbe = "#ef4444"
        elif abstand_zum_ziel < 5:
            empfehlung = T("almost")
            empf_grund = T("almost_grund").replace("{pct}", f"{abstand_zum_ziel:.1f}")
            empf_farbe = "#f59e0b"
        elif abstand_zum_ziel > 30:
            empfehlung = T("wait")
            empf_grund = T("above_target_wait").replace("{pct}", f"{abstand_zum_ziel:.1f}")
            empf_farbe = "#60a5fa"
        else:
            empfehlung = T("monitor")
            empf_grund = T("above_target_track").replace("{pct}", f"{abstand_zum_ziel:.1f}")
            empf_farbe = "#94a3b8"

        # 5. Allzeit-Tief vs. jetzt
        allzeit_text = ""
        if alle_punkte:
            allzeit_tief = min(p[1] for p in alle_punkte)
            diff_vom_tief = ((preis_jetzt - allzeit_tief) / allzeit_tief) * 100
            if diff_vom_tief < 2:
                allzeit_text = f"🏆 Near all-time low! (+{diff_vom_tief:.1f}% from lowest ever)"
            elif diff_vom_tief < 10:
                allzeit_text = f"✅ Close to all-time low (+{diff_vom_tief:.1f}%)"
            else:
                allzeit_text = f"📊 {diff_vom_tief:.1f}% above all-time low ({cur}{allzeit_tief:.2f})"

        # ── UI ─────────────────────────────────────────────────────────────────
        dlg = tk.Toplevel(self)
        dlg.title(f"🤖 {T('ai_title')} — {g['name']}")
        dlg.geometry("520x560")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)

        # Header
        hdr_f = tk.Frame(dlg, bg="#1e1b4b")
        hdr_f.pack(fill="x")
        tk.Label(hdr_f, text="🤖  " + T("ai_title"), bg="#1e1b4b", fg="#a78bfa",
                 font=(UI_FONT, 13, "bold")).pack(anchor="w", padx=20, pady=(14,2))
        tk.Label(hdr_f, text=g["name"], bg="#1e1b4b", fg=TEXT2,
                 font=(UI_FONT, 10)).pack(anchor="w", padx=20, pady=(0,12))

        # Recommendation box
        rec_f = tk.Frame(dlg, bg=BG2)
        rec_f.pack(fill="x", padx=16, pady=(12,4))
        tk.Label(rec_f, text=T("recommendation"), bg=BG2, fg=TEXT2,
                 font=(UI_FONT, 8, "bold")).pack(anchor="w", padx=14, pady=(10,4))
        tk.Label(rec_f, text=empfehlung, bg=BG2, fg=empf_farbe,
                 font=(UI_FONT, 16, "bold")).pack(anchor="w", padx=14, pady=(0,4))
        tk.Label(rec_f, text=empf_grund, bg=BG2, fg=TEXT2,
                 font=(UI_FONT, 9), wraplength=460, justify="left").pack(
                 anchor="w", padx=14, pady=(0,12))

        def section(text):
            tk.Label(dlg, text=text, bg=BG, fg="#a78bfa",
                     font=(UI_FONT, 9, "bold")).pack(anchor="w", padx=16, pady=(10,2))
            tk.Frame(dlg, bg="#2d2060", height=1).pack(fill="x", padx=16)

        def row(label, value, color=TEXT2):
            r = tk.Frame(dlg, bg=BG2)
            r.pack(fill="x", padx=16, pady=1)
            tk.Label(r, text=label, bg=BG2, fg=GRAU,
                     font=(UI_FONT, 9), width=22, anchor="w").pack(side="left", padx=10, pady=6)
            tk.Label(r, text=value, bg=BG2, fg=color,
                     font=(UI_FONT, 9, "bold"), anchor="e").pack(side="right", padx=10)

        section("📊  " + T("price_analysis"))
        row(T("cur_best"),   f"{cur}{preis_jetzt:.2f}", AKZENT)
        row(T("your_target"),          f"{cur}{ziel:.2f}", "#a78bfa")
        row(T("dist_target"),   f"{abstand_zum_ziel:+.1f}%",
            AKZENT if abstand_zum_ziel <= 0 else ("#f59e0b" if abstand_zum_ziel < 10 else TEXT2))
        if allzeit_text:
            row(T("vs_alltime"), allzeit_text, AKZENT if "all-time low" in allzeit_text else TEXT2)

        section("📈  " + T("trend_volatility"))
        row(T("price_trend"),      trend_text)
        row(T("price_stab"),  volatil_text)
        row(T("data_points"),      str(len(alle_punkte)))
        if saison_text:
            row(T("seasonal"), saison_text, "#60a5fa")

        section("💡  " + T("insight"))
        # Extra insight
        if len(preise_aktuell) > 1:
            spread = max(preise_aktuell) - min(preise_aktuell)
            row(T("price_spread"), f"{cur}{spread:.2f}",
                AKZENT if spread > 20 else TEXT2)
            if spread > 20:
                insight = f"Big difference between shops! Cheapest saves you {cur}{spread:.2f} vs most expensive."
            else:
                insight = "Shops are closely priced — not much to gain from switching shops."
            r2 = tk.Frame(dlg, bg=BG2)
            r2.pack(fill="x", padx=16, pady=1)
            tk.Label(r2, text=insight, bg=BG2, fg=TEXT2,
                     font=(UI_FONT, 9), wraplength=460, justify="left").pack(
                     anchor="w", padx=10, pady=8)

        note = tk.Label(dlg,
            text="ℹ  Analysis based on collected price data. More data = better accuracy.",
            bg=BG, fg=GRAU, font=(UI_FONT, 8), wraplength=460)
        note.pack(anchor="w", padx=16, pady=(8,4))

        self._btn(dlg, T("close"), dlg.destroy, BG3, TEXT).pack(pady=10, ipadx=20)
        dlg.lift()
        dlg.focus_force()

    # ── Statistics ────────────────────────────────────────────────────────────
    def _vg_statistiken(self):
        g = self._aktuelle_vg()
        if not g:
            messagebox.showinfo("Info", "Please select a group first.")
            return
        shops = g.get("shops", [])
        if not shops:
            messagebox.showinfo("Info", "No shops in this group yet.")
            return
        cur = g.get("currency", "€")
        preise = [s["preis"] for s in shops if s.get("preis")]
        if not preise:
            messagebox.showinfo("Info", "No prices available yet. Run a check first.")
            return
        alle_verlauf = []
        for s in shops:
            for e in s.get("verlauf", []):
                alle_verlauf.append(e["preis"])
        guenstigster_shop = min(shops, key=lambda s: s.get("preis") or 99999)
        teuerster_shop    = max(shops, key=lambda s: s.get("preis") or 0)
        dlg = tk.Toplevel(self)
        dlg.title(f"{T('price_analysis')} — {g['name']}"  )
        dlg.geometry("480x420")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        tk.Label(dlg, text=f"📊  {g['name']}", bg=BG, fg=TEXT,
                 font=(UI_FONT, 13, "bold")).pack(anchor="w", padx=20, pady=(16,12))
        def stat_row(label, value, color=TEXT):
            r = tk.Frame(dlg, bg=BG2)
            r.pack(fill="x", padx=20, pady=2)
            tk.Label(r, text=label, bg=BG2, fg=TEXT2,
                     font=(UI_FONT, 10), width=24, anchor="w").pack(side="left", padx=12, pady=8)
            tk.Label(r, text=value, bg=BG2, fg=color,
                     font=(UI_FONT, 10, "bold"), anchor="e").pack(side="right", padx=12)
        stat_row(T("shops_tracked"),        str(len(shops)))
        stat_row(T("target_price_lbl"),         f"{cur}{g['zielpreis']:.2f}")
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x", padx=20, pady=6)
        stat_row(T("cur_best"),   f"{cur}{min(preise):.2f}", AKZENT)
        stat_row(T("cur_avg"),    f"{cur}{sum(preise)/len(preise):.2f}", "#60a5fa")
        stat_row(T("cur_worst"),  f"{cur}{max(preise):.2f}", "#f87171")
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x", padx=20, pady=6)
        if alle_verlauf:
            stat_row(T("alltime_low"),   f"{cur}{min(alle_verlauf):.2f}", AKZENT)
            stat_row(T("alltime_high"),  f"{cur}{max(alle_verlauf):.2f}", "#f87171")
            stat_row(T("alltime_avg"),  f"{cur}{sum(alle_verlauf)/len(alle_verlauf):.2f}", "#60a5fa")
            stat_row(T("total_points"), str(len(alle_verlauf)))
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x", padx=20, pady=6)
        sn = guenstigster_shop.get("shop_name") or guenstigster_shop["shop"]
        stat_row(T("cheapest_shop"),        f"{sn}  ({cur}{guenstigster_shop.get('preis',0):.2f})", AKZENT)
        sn2 = teuerster_shop.get("shop_name") or teuerster_shop["shop"]
        stat_row(T("expensive_shop"),  f"{sn2}  ({cur}{teuerster_shop.get('preis',0):.2f})", "#f87171")
        savings = max(preise) - min(preise)
        stat_row(T("max_savings"), f"{cur}{savings:.2f}", AKZENT)
        self._btn(dlg, T("close"), dlg.destroy, BG3, TEXT).pack(pady=16, ipadx=20)
        dlg.lift()
        dlg.focus_force()

    # ── Preisverlauf Chart ───────────────────────────────────────────────────
    def _vg_chart_zeigen(self):
        g = self._aktuelle_vg()
        if not g:
            messagebox.showinfo("Info", "Please select a group first.")
            return

        # Preisverlauf: pro Zeitpunkt günstigsten UND Durchschnittspreis sammeln
        tages_preise = {}   # timestamp -> lowest price
        tages_summen = {}   # timestamp -> [all prices] for average
        for s in g["shops"]:
            for eintrag in s.get("verlauf", []):
                datum = eintrag["datum"][:16]
                preis = eintrag["preis"]
                if datum not in tages_preise or preis < tages_preise[datum]:
                    tages_preise[datum] = preis
                tages_summen.setdefault(datum, []).append(preis)

        if len(tages_preise) < 1:
            messagebox.showinfo("Info",
                "No data yet.\nPlease run 'Check All' first.")
            return
        if len(tages_preise) < 2:
            # Nur ein Datenpunkt — trotzdem anzeigen
            erster = list(tages_preise.items())[0]
            tages_preise[erster[0] + " (2)"] = erster[1]  # Duplicate point for line rendering

        # Sortiert nach Datum/Uhrzeit
        punkte    = sorted(tages_preise.items())
        daten     = [p[0][:16] for p in punkte]
        preise    = [p[1] for p in punkte]
        avg_preise = [round(sum(tages_summen.get(d, [p])) / len(tages_summen.get(d, [p])), 2)
                      for d, p in punkte]
        ziel    = g["zielpreis"]

        # Chart-Fenster
        dlg = tk.Toplevel(self)
        dlg.title(f"Price History — {g['name']}")
        dlg.geometry("750x460")
        dlg.configure(bg=BG)
        dlg.resizable(True, True)

        # Zeitraum-Buttons
        zeitraum_bar = tk.Frame(dlg, bg=BG)
        zeitraum_bar.pack(fill="x", padx=16, pady=(12,0))
        zeitraum_var = tk.StringVar(value=T("all_btn"))

        def zeitraum_filtern():
            from datetime import datetime as _dt, timedelta
            zr = zeitraum_var.get()
            jetzt = _dt.now()
            if zr == T("day"):
                grenze = (jetzt - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
            elif zr == T("week"):
                grenze = (jetzt - timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M")
            elif zr == T("month"):
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

        tk.Label(zeitraum_bar, text=T("period"), bg=BG, fg=TEXT2,
                 font=(UI_FONT, 9)).pack(side="left", padx=(0,8))
        for zr in [T("day"), T("week"), T("month"), T("all_btn")]:
            tk.Radiobutton(zeitraum_bar, text=zr, variable=zeitraum_var, value=zr,
                           bg=BG, fg=TEXT, activebackground=BG, selectcolor=BG3,
                           font=(UI_FONT, 9),
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
            if zr == T("day"):
                grenze = (jetzt - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
            elif zr == T("week"):
                grenze = (jetzt - timedelta(weeks=1)).strftime("%Y-%m-%d %H:%M")
            elif zr == T("month"):
                grenze = (jetzt - timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
            else:
                grenze = ""
            gefiltertes_dict = {d: p for d, p in tages_preise.items()
                                if not grenze or d >= grenze}
            if not gefiltertes_dict:
                canvas.create_text(w//2, h//2, text="No data for this period",
                                   fill=TEXT2, font=(UI_FONT, 11))
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
                (T("cur_best"), TEXT2, False),
                (T("avg_legend"),    "#60a5fa", True),
                (T("target_price_lbl"), AKZENT, True),
            ]
            lx = pad_l
            for i, (ltext, lfarbe, gestrichelt) in enumerate(legende):
                ly = 14 + i * 18
                dash = (5,3) if gestrichelt else None
                kw = {"fill": lfarbe, "width": 2}
                if dash: kw["dash"] = dash
                canvas.create_line(lx, ly, lx+30, ly, **kw)
                canvas.create_text(lx+34, ly, text=ltext, fill=lfarbe,
                                   font=(UI_FONT, 8), anchor="w")

            # Info-Zeile oben rechts
            info = (f"Data points: {len(preise)}   "
                    f"Min: {min(preise):.2f}€   "
                    f"Ø Avg: {avg_preise[-1]:.2f}€   "
                    f"Best: {preise[-1]:.2f}€")
            canvas.create_text(w - pad_r + 80, 14, text=info,
                               fill=TEXT2, font=(UI_FONT, 8), anchor="e")

            # Gitternetz
            for step in range(5):
                py = pad_t + step * chart_h / 4
                preis_val = max_p - step * (max_p - min_p) / 4
                canvas.create_line(pad_l, py, pad_l + chart_w, py,
                                   fill="#2a2a2a", dash=(4,4))
                canvas.create_text(pad_l - 6, py, text=f"{preis_val:.0f}€",
                                   fill=TEXT2, font=(UI_FONT, 8), anchor="e")

            # Zielpreis-Linie
            yz = cy(ziel)
            canvas.create_line(pad_l, yz, pad_l + chart_w, yz,
                               fill=AKZENT, dash=(6,3), width=1.5)
            canvas.create_text(pad_l + chart_w + 6, yz,
                               text=f"Ziel {ziel:.0f}€",
                               fill=AKZENT, font=(UI_FONT, 8), anchor="w")

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
                                       fill=TEXT, font=(UI_FONT, 8, "bold"), anchor=anker)

            # X-Achse
            max_labels = max(2, min(len(daten), chart_w // 70))
            schritt = max(1, len(daten) // max_labels)
            for i in range(0, len(daten), schritt):
                px = cx(i)
                label = daten[i][5:]  # "03-15 10:49"
                canvas.create_text(px, pad_t + chart_h + 14, text=label,
                                   fill=TEXT2, font=(UI_FONT, 8), anchor="n")
                canvas.create_line(px, pad_t + chart_h, px, pad_t + chart_h + 5, fill=BORDER)

            # Achsenlinien
            canvas.create_line(pad_l, pad_t, pad_l, pad_t + chart_h, fill=BORDER, width=1)
            canvas.create_line(pad_l, pad_t + chart_h, pad_l + chart_w,
                               pad_t + chart_h, fill=BORDER, width=1)

        canvas.bind("<Configure>", zeichnen)
        dlg.after(100, zeichnen)

    # ── Update ────────────────────────────────────────────────────────────────
    def _update_check_bg(self):
        new_ver, url, zip_url, notes = check_for_update()
        if new_ver:
            self.after(0, lambda: self._update_verfuegbar(new_ver, url, zip_url, notes))

    def _update_verfuegbar(self, new_ver, url, zip_url="", notes=""):
        self.update_lbl.config(
            text=f"🆕 Update available — v{new_ver}  (click to install)",
            fg=AKZENT)
        self._update_url     = url
        self._update_zip_url = zip_url
        self._update_version = new_ver
        self._update_notes   = notes

    def _update_pruefen(self):
        # If update already detected, use stored info
        new_ver  = getattr(self, "_update_version", None)
        zip_url  = getattr(self, "_update_zip_url", "")
        html_url = getattr(self, "_update_url", "")
        notes    = getattr(self, "_update_notes", "")

        if not new_ver:
            new_ver, html_url, zip_url, notes = check_for_update()

        if not new_ver:
            messagebox.showinfo("Up to date",
                f"You are running the latest version (v{APP_VERSION}).")
            return

        # Show release notes dialog
        dlg = tk.Toplevel(self)
        dlg.title(f"Update Available — v{new_ver}")
        dlg.geometry("520x440")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        # Header
        hdr_f = tk.Frame(dlg, bg="#14532d")
        hdr_f.pack(fill="x")
        tk.Label(hdr_f, text=f"🆕  Version {new_ver} available!",
                 bg="#14532d", fg="#4ade80",
                 font=(UI_FONT, 13, "bold")).pack(anchor="w", padx=20, pady=(14,2))
        tk.Label(hdr_f, text=f"You are on v{APP_VERSION}",
                 bg="#14532d", fg="#86efac",
                 font=(UI_FONT, 9)).pack(anchor="w", padx=20, pady=(0,12))

        # Release notes
        tk.Label(dlg, text="What's new:", bg=BG, fg=TEXT2,
                 font=(UI_FONT, 10, "bold")).pack(anchor="w", padx=16, pady=(12,4))

        from tkinter import scrolledtext as _st
        notes_box = _st.ScrolledText(dlg, bg=BG2, fg=TEXT, font=(UI_FONT, 9),
                                      height=12, borderwidth=0, relief="flat",
                                      wrap="word", state="normal")
        notes_box.pack(fill="both", expand=True, padx=16, pady=(0,8))
        notes_box.insert("1.0", notes or "No release notes provided.")
        notes_box.config(state="disabled")

        # Buttons
        btn_f = tk.Frame(dlg, bg=BG)
        btn_f.pack(fill="x", padx=16, pady=(0,16))

        antwort = [False]

        def do_install():
            antwort[0] = True
            dlg.destroy()

        self._btn(btn_f, "✅  Install Update", do_install, AKZENT, "#000").pack(
            side="left", ipady=6, padx=(0,8))
        self._btn(btn_f, "Later", dlg.destroy, BG3, TEXT2).pack(
            side="left", ipady=6)

        dlg.wait_window()
        if not antwort[0]:
            return

        # Download and install in background
        self.update_lbl.config(text="⬇ Downloading update...", fg=GELB)
        threading.Thread(target=self._update_installieren,
                         args=(new_ver, zip_url, html_url), daemon=True).start()

    def _update_installieren(self, new_ver, zip_url, html_url):
        """Downloads the update ZIP and replaces preis_alarm.py, then restarts."""
        import zipfile, tempfile, shutil
        try:
            # Download ZIP
            self.after(0, lambda: self.update_lbl.config(
                text="⬇ Downloading...", fg=GELB))
            log(f"Downloading update v{new_ver} from {zip_url[:60]}")

            r = requests.get(zip_url, timeout=60, stream=True)
            r.raise_for_status()

            # Save to temp file
            tmp = Path(tempfile.mktemp(suffix=".zip"))
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.after(0, lambda: self.update_lbl.config(
                text="📦 Installing...", fg=GELB))

            # Extract and find preis_alarm.py
            script_path = Path(__file__).resolve()
            script_dir  = script_path.parent

            with zipfile.ZipFile(tmp, "r") as z:
                # Find preis_alarm.py in the ZIP
                for name in z.namelist():
                    if name.endswith("preis_alarm.py"):
                        # Extract to temp location
                        tmp_py = Path(tempfile.mktemp(suffix=".py"))
                        with z.open(name) as src, open(tmp_py, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        # Replace current file
                        shutil.move(str(tmp_py), str(script_path))
                        log(f"Updated preis_alarm.py from {name}")
                        break

            tmp.unlink(missing_ok=True)

            # Verify the update was applied correctly
            try:
                new_content = open(script_path, "r", encoding="utf-8").read()
                if f'APP_VERSION = "{new_ver}"' in new_content:
                    log(f"Update to v{new_ver} verified and installed successfully")
                else:
                    log(f"Warning: file replaced but version string not found — check asset")
            except: pass

            # Restart app
            self.after(0, lambda: self._update_neustart(new_ver))

        except Exception as e:
            log(f"Update failed: {e}")
            self.after(0, lambda: (
                self.update_lbl.config(
                    text=f"❌ Update failed — click to retry", fg=ROT),
                messagebox.showerror("Update Failed",
                    f"Could not install update automatically.\n"
                    f"Error: {e}\n\n"
                    f"Please download manually from GitHub.")
            ))

    def _update_neustart(self, new_ver):
        """Shows restart dialog and restarts the app."""
        messagebox.showinfo("Update Installed",
            f"Version {new_ver} installed successfully!\n"
            f"The app will now restart.")
        import subprocess
        script = str(Path(__file__).resolve())
        # Use pythonw.exe if available (no CMD window)
        exe = sys.executable
        pythonw = exe.replace("python.exe", "pythonw.exe")
        if Path(pythonw).exists():
            exe = pythonw
        # Start new process then close this one
        subprocess.Popen([exe, script],
                         creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
        self.after(500, self.destroy)

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
