<p align="center">
  <img src="assets/screenshots/ha-controls-overview-1.png" alt="Tesla controls in Home Assistant" width="220" />
  <img src="assets/screenshots/ha-controls-and-sensors-overview-2.png" alt="Tesla controls and sensors in Home Assistant" width="220" />
  <img src="assets/screenshots/ha-sensors-overview-1.png" alt="Tesla sensors in Home Assistant" width="220" />
</p>

<p align="center">
  <img src="custom_components/tesla_ha/brand/icon.png" alt="Tesla Home Assistant logo" width="140" height="140" />
</p>

<h1 align="center">Tesla fuer Home Assistant</h1>

<p align="center">
  HACS-Integration fuer Tesla-Fahrzeuge ueber die offizielle Tesla Fleet API.
  Owner API wurde entfernt, weil Tesla den Legacy-Zugriff fuer betroffene Accounts mit 403 blockiert.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration">
    <img src="https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge&logo=home-assistant" alt="HACS Custom" />
  </a>
  <a href="https://github.com/Feberdin/tesla-ha/actions/workflows/hacs.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/Feberdin/tesla-ha/hacs.yml?branch=main&style=for-the-badge&label=HACS" alt="HACS Validation" />
  </a>
  <a href="https://github.com/Feberdin/tesla-ha/actions/workflows/hassfest.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/Feberdin/tesla-ha/hassfest.yml?branch=main&style=for-the-badge&label=Hassfest" alt="Hassfest" />
  </a>
  <a href="https://github.com/Feberdin/tesla-ha/releases">
    <img src="https://img.shields.io/github/v/release/Feberdin/tesla-ha?style=for-the-badge" alt="Release Version" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/github/license/Feberdin/tesla-ha?style=for-the-badge" alt="License" />
  </a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2025.1.0%2B-18BCF2?style=for-the-badge&logo=home-assistant&logoColor=white" alt="Home Assistant 2025.1.0+" />
</p>

---

## Overview

`tesla-ha` ist eine Home Assistant Custom Integration fuer Tesla-Fahrzeuge. Die Integration nutzt Teslas offizielle Fleet API ueber Home Assistants Application-Credentials- und OAuth-Flow, richtet eine Fleet-Partnerdomain ein und stellt Fahrzeugdaten sowie Steuerfunktionen als Home Assistant Entitaeten bereit.

Der Fokus des Projekts liegt auf einer nachvollziehbaren und wartbaren Tesla-Anbindung fuer Home Assistant. Seit Teslas Umstellung auf Fleet API und signierte Commands benoetigt der Betrieb eine Tesla Developer App, passende Scopes, eine registrierte Public-Key-Domain und fuer viele Fahrzeuge einen gekoppelten Virtual Key.

---

## Features

- Home Assistant Application Credentials fuer Tesla Client ID und Client Secret
- Offizieller Tesla Fleet OAuth Flow mit `tesla-fleet-api`
- Partner-Domainregistrierung mit lokal erzeugtem Public/Private-Key-Paar
- Virtual-Key-Hinweis fuer signierte Fahrzeugbefehle
- 23 Sensoren fuer Ladezustand, Temperaturen, Reifendruck, Medienstatus und Fahrzeugdaten
- 22 Binaersensoren fuer Tueren, Fenster, Laden, Klima, Sentry Mode und Reifendruckwarnungen
- Steuerung fuer Klima, Laden, Verriegelung, Sitzheizung, Sitzkuehlung, Medien und Komfortfunktionen
- Wake-up-Logik fuer schlafende Fahrzeuge vor expliziten Befehlen
- Deutsche und englische UI-Texte fuer den Einrichtungsdialog
- HACS-kompatible Repository-Struktur inklusive Brand-Assets und Validierungs-Workflows

---

## Screenshots

<p align="center">
  <img src="assets/screenshots/ha-controls-overview-1.png" alt="Tesla controls overview" width="220" />
  <img src="assets/screenshots/ha-controls-and-sensors-overview-2.png" alt="Tesla controls and sensors overview" width="220" />
  <img src="assets/screenshots/ha-sensors-overview-1.png" alt="Tesla sensors overview" width="220" />
  <img src="assets/screenshots/ha-sensors-overview-2.png" alt="Tesla sensors overview part two" width="220" />
</p>

Die Bilder zeigen Home Assistant Karten mit Entitaeten dieser Integration.

<p align="center">
  <img src="assets/screenshots/external-vehicle-status-card.png" alt="External vehicle status card" width="420" />
</p>

> Hinweis: Die Vehicle Status-Karte im Screenshot oben stammt aus einer externen Integration und dient hier nur zur Darstellung im Dashboard.
> Vielen Dank an die Entwickler:innen dieser Karte.

> TODO: Das Repository enthaelt aktuell kein eigenes breites Banner oder ein dediziertes README-Logo fuer dieses Projekt. Falls spaeter eigenes Branding hinzukommt, sollte es getrennt von den HACS-Brand-Assets unter `assets/branding/` abgelegt werden.

---

## Installation

### Voraussetzungen

- Home Assistant `2025.1.0` oder neuer
- [HACS](https://hacs.xyz) installiert
- Tesla-Account
- Tesla Developer App mit Client ID und Client Secret
- OAuth Redirect URI in der Tesla Developer App:
  `https://my.home-assistant.io/redirect/oauth`
- Oeffentliche HTTPS-Domain, die den Tesla Public Key unter `/.well-known/appspecific/com.tesla.3p.public-key.pem` ausliefert

### HACS Installation

1. Oeffne in Home Assistant `HACS`.
2. Oeffne das Drei-Punkte-Menue oben rechts.
3. Waehle `Custom repositories`.
4. Trage `https://github.com/Feberdin/tesla-ha` als Repository ein.
5. Waehle als Kategorie `Integration`.
6. Lade die Integration herunter und starte Home Assistant neu.

### Einrichtung in Home Assistant

1. Oeffne `Einstellungen -> Geraete & Dienste -> Drei-Punkte-Menue -> Application Credentials`.
2. Lege fuer `Tesla` / `tesla_ha` die Client ID und das Client Secret aus dem Tesla Developer Portal an.
   Der Dialog zeigt dir die OAuth Redirect URI, die in der Tesla Developer App exakt registriert sein muss.
3. Oeffne `Einstellungen -> Geraete & Dienste`.
4. Waehle `+ Integration hinzufuegen` und suche nach `Tesla`.
5. Folge dem Tesla OAuth Login.
6. Gib im Domain-Schritt die oeffentliche Domain ein, die den Tesla Public Key hostet.
7. Lege den angezeigten Public Key exakt unter der angezeigten Well-Known-URL ab.
8. Schließe die Partnerregistrierung ab.
9. Oeffne den angezeigten Virtual-Key-Link und fuege den Schluessel in der Tesla-App hinzu.

Nach erfolgreicher Einrichtung erscheint das Fahrzeug unter `Einstellungen -> Geraete & Dienste -> Tesla`.

---

## Entitaeten

| Typ | Anzahl | Hinweise |
| --- | --- | --- |
| Sensor | 23 | Batterie, Laden, Klima, Reifendruck, Medien, Software |
| Binary Sensor | 22 | Tueren, Fenster, Laden, Klima, Sentry, TPMS-Warnungen |
| Climate | 1 | Standheizung / Klimaanlage |
| Lock | 1 | Tuerschloss |
| Switch | 4 | Laden, Sentry Mode, Lenkradheizung, Maximal-Heizung |
| Button | 11 | Hupe, Frunk, Kofferraum, Ladeport, Medien |
| Number | 2 | Ladelimit, Ladestrom |
| Select | 4-6 | Sitzheizung immer, Sitzkuehlung nur falls unterstuetzt |

### Was die Integration steuern kann

- Klima: Standheizung oder Klimaanlage ein- und ausschalten sowie Zieltemperatur setzen
- Fahrzeugzugriff: verriegeln und entriegeln
- Laden: Start, Stop, Ladelimit und Ladestrom zwischen `5 A` und `10 A`
- Komfort: Lenkradheizung und Maximal-Heizung
- Sicherheit: Sentry Mode
- Sitze: Sitzheizung vorne und hinten, Sitzkuehlung vorne falls vom Fahrzeug gemeldet
- Fahrzeugaktionen: Lichter blinken, Hupe, Frunk oeffnen, Kofferraum oeffnen
- Ladeport: Ladeanschluss oeffnen und schliessen
- Medien: Wiedergabe, naechster oder vorheriger Titel, Lautstaerke hoch oder runter

<details>
<summary><strong>Sensoren (23)</strong></summary>

| Sensor | Beschreibung | Einheit |
| --- | --- | --- |
| Ladestand | Aktueller Akkustand | `%` |
| Reichweite | Geschaetzte Reichweite | `km` |
| Ladelimit | Eingestelltes Ladelimit | `%` |
| Ladezustand | `Charging`, `Complete`, `Disconnected` | - |
| Ladeleistung | Aktuelle Ladeleistung | `kW` |
| Ladespannung | Spannung am Ladepunkt | `V` |
| Ladestrom | Strom am Ladepunkt | `A` |
| Energie geladen | Geladene Energie seit Anschluss | `kWh` |
| Minuten bis voll | Restzeit bis zum Ladelimit | `min` |
| Laderate | Reichweite pro Stunde Nachladung | `km/h` |
| Kilometerstand | Gesamtkilometer | `km` |
| Fahrstufe | `P`, `D`, `R`, `N` | - |
| Leistung | Verbrauch oder Rekuperation | `kW` |
| Software Version | Installierte Fahrzeugversion | - |
| Software Update | Verfuegbare Update-Version | - |
| Dashcam | Dashcam-Status | - |
| Innentemperatur | Temperatur im Innenraum | `degC` |
| Aussentemperatur | Temperatur ausserhalb des Fahrzeugs | `degC` |
| Reifendruck VL | Vorne links | `bar` |
| Reifendruck VR | Vorne rechts | `bar` |
| Reifendruck HL | Hinten links | `bar` |
| Reifendruck HR | Hinten rechts | `bar` |
| Wiedergabe | Aktuell gespielter Kuenstler und Titel | - |

</details>

<details>
<summary><strong>Binaersensoren (22)</strong></summary>

| Sensor | Beschreibung |
| --- | --- |
| Laedt | Fahrzeug laedt gerade |
| Kabel angesteckt | Ladekabel ist verbunden |
| Ladeanschluss offen | Ladeklappe ist geoeffnet |
| Batterieheizung | Batterieheizung ist aktiv |
| Verriegelt | Fahrzeug ist verriegelt |
| Nutzer anwesend | Jemand sitzt im Fahrzeug |
| Fahrertuer | Fahrertuer offen |
| Beifahrertuer | Beifahrertuer offen |
| Fondtuer Links | Hintere Fahrertuer offen |
| Fondtuer Rechts | Hintere Beifahrertuer offen |
| Frunk offen | Vordere Haube offen |
| Kofferraum offen | Hintere Klappe offen |
| Fenster Fahrer | Fahrerfenster offen |
| Fenster Beifahrer | Beifahrerfenster offen |
| Fenster Fond Links | Hinteres Fahrerfenster offen |
| Fenster Fond Rechts | Hinteres Beifahrerfenster offen |
| Klimaanlage | Klimaanlage aktiv |
| Sentry Mode | Sentry Mode aktiv |
| Reifendruckwarnung VL | Problem vorne links |
| Reifendruckwarnung VR | Problem vorne rechts |
| Reifendruckwarnung HL | Problem hinten links |
| Reifendruckwarnung HR | Problem hinten rechts |

</details>

<details>
<summary><strong>Steuerbare Entitaeten</strong></summary>

| Entitaet | Typ | Beschreibung |
| --- | --- | --- |
| Standheizung | Climate | Ein oder Aus und Zieltemperatur `15-28 degC` |
| Tuerschloss | Lock | Verriegeln und entriegeln |
| Sentry Mode | Switch | Sentry Mode ein oder ausschalten |
| Laden | Switch | Laden starten oder stoppen |
| Lenkradheizung | Switch | Lenkradheizung ein oder ausschalten |
| Maximal-Heizung | Switch | Alle Heizungen auf Maximum |
| Ladelimit | Number | Ladelimit `50-100 %` |
| Ladestrom | Number | Ladestrom `5-10 A` |
| Sitzheizung Fahrer | Select | `Aus`, `Stufe 1`, `Stufe 2`, `Stufe 3` |
| Sitzheizung Beifahrer | Select | `Aus`, `Stufe 1`, `Stufe 2`, `Stufe 3` |
| Sitzheizung Fond Links | Select | `Aus`, `Stufe 1`, `Stufe 2`, `Stufe 3` |
| Sitzheizung Fond Rechts | Select | `Aus`, `Stufe 1`, `Stufe 2`, `Stufe 3` |
| Sitzkuehlung Fahrer | Select | `Aus`, `Stufe 1`, `Stufe 2`, `Stufe 3` falls verfuegbar |
| Sitzkuehlung Beifahrer | Select | `Aus`, `Stufe 1`, `Stufe 2`, `Stufe 3` falls verfuegbar |
| Lichter blinken | Button | Fahrzeuglichter kurz aufblinken lassen |
| Hupe | Button | Hupe betaetigen |
| Frunk oeffnen | Button | Vordere Haube oeffnen |
| Kofferraum oeffnen | Button | Hintere Klappe oeffnen |
| Ladeanschluss oeffnen | Button | Ladeklappe oeffnen |
| Ladeanschluss schliessen | Button | Ladeklappe schliessen |
| Wiedergabe Pause/Play | Button | Musik pausieren oder fortsetzen |
| Naechster Titel | Button | Naechsten Titel ueberspringen |
| Vorheriger Titel | Button | Vorherigen Titel wiederholen |
| Lautstaerke lauter | Button | Lautstaerke erhoehen |
| Lautstaerke leiser | Button | Lautstaerke verringern |

</details>

---

## Konfiguration

### Update-Intervall

Das Datenupdate laeuft standardmaessig alle `10 Minuten`.
Der Wert ist in [const.py](custom_components/tesla_ha/const.py) als `UPDATE_INTERVAL` hinterlegt.

```python
UPDATE_INTERVAL = 10  # minutes
```

> Hinweis: Tesla Fleet `vehicle_data` Abrufe koennen kosten- und rate-limit-relevant sein. Die Integration weckt schlafende Fahrzeuge deshalb nicht mehr fuer normale Polling-Updates, sondern nur bei expliziten Befehlen.

### Authentifizierung

Die Integration verwendet Home Assistants Application-Credentials- und OAuth2-Flow in [config_flow.py](custom_components/tesla_ha/config_flow.py).
Das Token wird nach erfolgreichem Abschluss durch Home Assistant gespeichert und erneuert.

Seit Version `2.0.0` nutzt die Integration keine Legacy Owner API mehr. Der Tesla Developer Flow benoetigt:

- Client ID und Client Secret aus dem Tesla Developer Portal
- Redirect URI aus Home Assistant. Standard mit aktivem `my`-Modul:
  `https://my.home-assistant.io/redirect/oauth`
- Scopes `openid`, `offline_access`, `user_data`, `vehicle_device_data`, `vehicle_location`, `vehicle_cmds`, `vehicle_charging_cmds`
- eine Allowed Origin passend zur Public-Key-Domain
- einen Public Key unter `https://deine-domain/.well-known/appspecific/com.tesla.3p.public-key.pem`
- fuer signierte Befehle einen gekoppelten Virtual Key im Fahrzeug

Wenn Tesla direkt nach dem Oeffnen der Login-Seite meldet, dass `redirect_uri`
nicht fuer die `client_id` registriert ist, ist die Tesla Developer App noch
nicht passend konfiguriert. Trage exakt die von Home Assistant angezeigte
Redirect URI ein, speichere die App und starte den OAuth-Flow danach erneut.

### Lokale Entwicklung

Fuer lokale Entwicklung werden keine echten Tesla-Tokens benoetigt. Application Credentials, OAuth Tokens und private Keys gehoeren ausschliesslich in Home Assistants lokalen Storage und duerfen nicht committed oder veroeffentlicht werden.

Lokale Pruefung ohne echte Tesla-Zugangsdaten:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest tesla-fleet-api==1.4.7
.venv/bin/python -m compileall -q custom_components tests
.venv/bin/python -m pytest tests/test_tesla_fleet.py -q
```

---

## Automationsbeispiele

### Standheizung automatisch einschalten

```yaml
automation:
  alias: "Tesla vorheizen"
  trigger:
    - platform: time
      at: "07:30:00"
  action:
    - service: climate.set_hvac_mode
      target:
        entity_id: climate.tesla_model_3_standheizung
      data:
        hvac_mode: heat_cool
    - service: climate.set_temperature
      target:
        entity_id: climate.tesla_model_3_standheizung
      data:
        temperature: 22
```

### Benachrichtigung bei niedrigem Reifendruck

```yaml
automation:
  alias: "Tesla Reifendruck Warnung"
  trigger:
    - platform: state
      entity_id:
        - binary_sensor.tesla_model_3_reifendruckwarnung_vl
        - binary_sensor.tesla_model_3_reifendruckwarnung_vr
        - binary_sensor.tesla_model_3_reifendruckwarnung_hl
        - binary_sensor.tesla_model_3_reifendruckwarnung_hr
      to: "on"
  action:
    - service: notify.mobile_app
      data:
        title: "Tesla Reifendruck"
        message: "Reifendruck pruefen: {{ trigger.to_state.name }}"
```

### Laden stoppen wenn Ladestand erreicht

```yaml
automation:
  alias: "Tesla Laden bei 80% stoppen"
  trigger:
    - platform: numeric_state
      entity_id: sensor.tesla_model_3_ladestand
      above: 80
  condition:
    - condition: state
      entity_id: binary_sensor.tesla_model_3_ladt
      state: "on"
  action:
    - service: switch.turn_off
      target:
        entity_id: switch.tesla_model_3_laden
```

---

## Architektur

Die Integration ist bewusst kompakt aufgebaut:

- [application_credentials.py](custom_components/tesla_ha/application_credentials.py) verbindet Home Assistant Application Credentials mit Tesla OAuth
- [oauth.py](custom_components/tesla_ha/oauth.py) definiert Tesla Fleet OAuth-Server, Scopes und Token-Exchange-Parameter
- [config_flow.py](custom_components/tesla_ha/config_flow.py) implementiert OAuth, Partner-Domainregistrierung und Virtual-Key-Hinweise
- [tesla_fleet.py](custom_components/tesla_ha/tesla_fleet.py) kapselt Fleet-Datenmapping und Command-Mapping
- [coordinator.py](custom_components/tesla_ha/coordinator.py) kapselt Fleet-Abrufe, Wake-up-Logik und Tesla-Befehle
- Die Plattformdateien unter `custom_components/tesla_ha/` definieren die Home Assistant Entitaeten fuer Sensoren und Steuerung

Der Coordinator arbeitet mit `DataUpdateCoordinator` und nutzt die asynchrone `tesla-fleet-api` Library, die auch Home Assistants offizielle Tesla-Fleet-Integration verwendet.

---

## Einschraenkungen und Fehlerbehebung

### Bekannte Einschraenkungen

- Aktuell wird nur das erste gefundene Fahrzeug verwendet (`vehicles[0]`)
- Normale Polling-Updates wecken das Fahrzeug nicht automatisch
- Signierte Befehle funktionieren nur mit registrierter Domain, gehostetem Public Key und gekoppeltem Virtual Key
- Tesla Fleet API kann je nach Developer-App, Region und Nutzung kosten- oder rate-limit-relevant sein
- Das Aufwecken eines schlafenden Fahrzeugs fuer Befehle kann fehlschlagen, wenn Mobile Access deaktiviert ist

### Haeufige Probleme

- Integration erscheint nicht in HACS:
  Stelle sicher, dass `https://github.com/Feberdin/tesla-ha` als Custom Repository eingetragen ist.
- Application Credentials fehlen:
  Lege Client ID und Client Secret in Home Assistant unter `Application Credentials` fuer diese Integration an.
- Domainregistrierung schlaegt fehl:
  Pruefe Allowed Origin im Tesla Developer Portal und ob der Public Key exakt unter der angezeigten Well-Known-URL erreichbar ist.
- Befehle funktionieren nicht, Sensoren aber schon:
  Pruefe, ob der Virtual Key ueber `https://www.tesla.com/_ak/deine-domain` gekoppelt wurde und ob die OAuth-Scopes `vehicle_cmds` sowie `vehicle_charging_cmds` erlaubt sind.
- Token-Refresh schlaegt fehl:
  Entferne die Integration und richte sie mit einem frischen Tesla Fleet Login neu ein.
- Fahrzeug wacht nicht auf:
  Pruefe Mobile Access, Mobilfunk- oder WLAN-Empfang des Fahrzeugs und gib dem Wake-up etwas Zeit.

---

## Projektstruktur

```text
tesla-ha/
├── .github/workflows/              # HACS- und Hassfest-Validierung
├── assets/screenshots/             # README-Screenshots
├── docs/                           # Setup- und Migrationsdokumentation
├── custom_components/tesla_ha/     # Home Assistant Integration
│   ├── brand/                      # HACS/Home Assistant Brand-Assets
│   ├── translations/               # de/en Config-Flow Uebersetzungen
│   ├── config_flow.py
│   ├── coordinator.py
│   ├── sensor.py
│   ├── binary_sensor.py
│   ├── climate.py
│   ├── lock.py
│   ├── switch.py
│   ├── button.py
│   ├── number.py
│   └── select.py
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── hacs.json
```

### Vorgeschlagene Doku- und Asset-Struktur

Die `docs/`-Struktur ist jetzt als Ausgangspunkt vorhanden und kann bei Bedarf weiter ausgebaut werden:

```text
docs/
├── SETUP.md
├── MIGRATION.md
├── installation.md
├── configuration.md
├── automations.md
└── troubleshooting.md

assets/branding/                   # TODO
└── readme-banner.png
```

> TODO: Falls die Projektdoku weiter waechst, sollten Installationsanleitung, Automationsbeispiele und Troubleshooting schrittweise in eigene Dateien unter `docs/` ausgelagert werden.

---

## Contributing

Beitraege sind willkommen. Die projektspezifischen Hinweise stehen in [CONTRIBUTING.md](CONTRIBUTING.md).

Wichtig fuer dieses Repository:

- Keine Secrets, Tokens oder lokale `cache.json` Dateien committen
- Dokumentationsaenderungen immer gegen die echte Implementierung pruefen
- Externe Dashboard-Karten oder Drittanbieter-Assets in Screenshots klar kennzeichnen

---

## Security

Bitte keine sensiblen Sicherheitsdetails in oeffentlichen Issues posten.
Siehe [SECURITY.md](.github/SECURITY.md) fuer den bevorzugten Meldeweg.

---

## License

Dieses Projekt steht unter der MIT License. Details stehen in [LICENSE](LICENSE).

---

## Support

- Issues: [github.com/Feberdin/tesla-ha/issues](https://github.com/Feberdin/tesla-ha/issues)
- Releases: [github.com/Feberdin/tesla-ha/releases](https://github.com/Feberdin/tesla-ha/releases)
- Maintainer: [Feberdin](https://github.com/Feberdin)

Wenn du einen Bug meldest, sind Home Assistant Version, Integrationsversion, relevante Logs und reproduzierbare Schritte am hilfreichsten.
