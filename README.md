# Tesla Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Kostenlose Tesla-Integration für Home Assistant via inoffizielle Owner API — kein Tesla Fleet API Abo nötig.

## Sensoren

| Sensor | Beschreibung | Einheit |
|---|---|---|
| Ladestand | Aktueller Akkustand | % |
| Reichweite | Geschätzte Reichweite | km |
| Ladelimit | Eingestelltes Ladelimit | % |
| Ladezustand | Charging / Complete / Disconnected | — |
| Ladeleistung | Aktuelle Ladeleistung | kW |
| Ladespannung | Spannung am Ladepunkt | V |
| Ladestrom | Strom am Ladepunkt | A |
| Energie geladen | Geladene Energie seit Anschluss | kWh |
| Kilometerstand | Gesamtkilometer | km |
| Innentemperatur | Temperatur im Fahrzeuginnenraum | °C |
| Außentemperatur | Außentemperatur | °C |
| Software Version | Aktuelle Fahrzeugsoftware | — |

## Binärsensoren

| Sensor | Beschreibung |
|---|---|
| Lädt | Fahrzeug lädt gerade |
| Verriegelt | Fahrzeug ist verriegelt |
| Klimaanlage | Klimaanlage aktiv |
| Sentry Mode | Sentry Mode aktiv |
| Kabel angesteckt | Ladekabel eingesteckt |

## Installation via HACS

1. HACS öffnen → **Integrationen** → Menü (⋮) → **Custom repositories**
2. URL eingeben: `https://github.com/Feberdin/tesla-ha`
3. Kategorie: **Integration** → **Add**
4. Integration suchen: **Tesla** → **Herunterladen**
5. Home Assistant neu starten

## Einrichtung

1. **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen**
2. Nach **Tesla** suchen
3. E-Mail-Adresse eingeben
4. Dem Link folgen, bei Tesla einloggen
5. Callback-URL einfügen → fertig

## Aktualisierungsintervall

Die Daten werden alle **5 Minuten** aktualisiert. Das Fahrzeug wird dabei geweckt, falls es schläft. Um den 12V-Akku zu schonen, kann das Intervall in `const.py` angepasst werden (`UPDATE_INTERVAL`).

## Voraussetzungen

- Home Assistant 2023.1.0+
- HACS
- Tesla-Konto (kein Fleet API Abo nötig)
