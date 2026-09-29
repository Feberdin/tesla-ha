# Projekt-Kontext: tesla-ha

## Kurzbeschreibung

`tesla-ha` ist eine HACS-kompatible Home Assistant Custom Integration fuer Tesla-Fahrzeuge.
Das Projekt bindet Tesla-Fahrzeuge über die offizielle Tesla Fleet API mittels OAuth2, Developer App und Partner Domain an und stellt Fahrzeugdaten sowie Steuerfunktionen als Home Assistant Entitaeten bereit.

## Pfade

- Projektpfad: `/Users/joachim.stiegler/Tesla/tesla-ha`
- Repository: `tesla-ha`
- Git-Remote: `git@github.com:Feberdin/tesla-ha.git`
- Branch: `main`

## Technischer Stack

- Python
- Home Assistant Custom Integration
- HACS
- `tesla-fleet-api==1.4.7`
- Home Assistant Config Flow / OAuth2 PKCE
- GitHub Actions: `hacs`, `hassfest`
- JSON und Markdown fuer Konfiguration und Dokumentation

## Wichtige Dateien und Verzeichnisse

- `README.md`: Nutzer- und Projektueberblick, Installation, Entitaeten, Automationsbeispiele
- `PROJECT_CONTEXT.md`: kompakter Arbeits- und Migrationskontext fuer KI-Tools
- `CONTRIBUTING.md`: Hinweise fuer Aenderungen und Validierung
- `docs/SETUP.md`: kompaktes Setup fuer neuen Mac und Home Assistant Einrichtung
- `docs/MIGRATION.md`: projektspezifische Migrationshinweise fuer macOS-Umzug
- `hacs.json`: HACS-Metadaten, inklusive minimaler Home Assistant Version
- `custom_components/tesla_ha/manifest.json`: Integrations-Metadaten und Python-Abhaengigkeit
- `custom_components/tesla_ha/__init__.py`: Setup und Unload der Integration
- `custom_components/tesla_ha/config_flow.py`: Login- und Token-Flow ueber OAuth2 PKCE
- `custom_components/tesla_ha/coordinator.py`: Datenabruf, Wake-up-Logik und Befehlsausfuehrung
- `custom_components/tesla_ha/sensor.py`: Sensor-Entitaeten
- `custom_components/tesla_ha/binary_sensor.py`: Binaersensor-Entitaeten
- `custom_components/tesla_ha/climate.py`: Klima-Entitaet
- `custom_components/tesla_ha/lock.py`: Schloss-Entitaet
- `custom_components/tesla_ha/switch.py`: Schalter fuer Laden, Sentry, Heizung
- `custom_components/tesla_ha/button.py`: Buttons fuer Komfort- und Medienfunktionen
- `custom_components/tesla_ha/number.py`: Ladelimit und Ladestrom
- `custom_components/tesla_ha/select.py`: Sitzheizung und Sitzkuehlung
- `custom_components/tesla_ha/translations/`: deutsche und englische Uebersetzungen
- `custom_components/tesla_ha/brand/`: Brand-Assets fuer HACS / Home Assistant
- `assets/screenshots/`: README-Screenshots
- `.github/workflows/`: CI fuer HACS- und Hassfest-Validierung

## Lokales Setup

### Voraussetzungen

- Git mit Zugriff auf `github.com`
- Python 3 auf dem Mac: Version im Repo nicht explizit festgelegt, lokal zu pruefen
- Home Assistant `2023.1.0` oder neuer
- HACS fuer die Installation in Home Assistant
- Tesla-Account fuer die Einrichtung

### Abhaengigkeiten installieren

- Keine klassische Paketmanager-Datei wie `requirements.txt`, `pyproject.toml` oder `package.json` vorhanden
- Python-Abhaengigkeit wird in `custom_components/tesla_ha/manifest.json` ueber Home Assistant eingebunden: `tesla-fleet-api==1.4.7`

### Konfiguration vorbereiten

- Repository nach `custom_components` in Home Assistant ueber HACS einbinden
- Einrichtungsflow in Home Assistant starten
- Tesla-Login im Browser durchfuehren
- Callback-URL aus dem Redirect zurueck in den Config Flow einfuegen
- Falls lokal fuer Entwicklung eine `cache.json` genutzt wird: manuell uebertragen oder neu erzeugen; Pfad und Inhalt sind lokal zu pruefen

### Starten

- Startbefehl fuer eine eigenstaendige lokale App ist im Repo nicht vorhanden
- Betrieb erfolgt als Home Assistant Integration
- Home Assistant nach Installation oder Aktualisierung neu starten

### Testen

- Lokaler Syntax-Check:

```bash
python3 -m compileall -q custom_components
```

- Weitere Validierung erfolgt ueber GitHub Actions: `hacs` und `hassfest`

### Build

- Kein separater Build-Prozess dokumentiert

## Bekannte Befehle

- Installation:
  - HACS Custom Repository `https://github.com/Feberdin/tesla-ha`
- Entwicklung:
  - kein dedizierter Dev-Server dokumentiert
- Tests:
  - `python3 -m compileall -q custom_components`
- Build:
  - kein Build-Befehl dokumentiert
- Linting:
  - kein separater Lint-Befehl dokumentiert
- Deployment:
  - kein Deployment-Befehl dokumentiert

## Konfiguration und Secrets

- Vorhandene Konfigurationsdateien:
  - `custom_components/tesla_ha/manifest.json`
  - `hacs.json`
  - `custom_components/tesla_ha/strings.json`
  - `custom_components/tesla_ha/translations/de.json`
  - `custom_components/tesla_ha/translations/en.json`
  - `.github/workflows/hacs.yml`
  - `.github/workflows/hassfest.yml`
- Beispiel-Dateien:
  - keine `.env.example`
  - keine dokumentierte Beispiel-Konfigurationsdatei ausser README / Docs
- Secret-Dateien im Projekt:
  - keine `.env`-Dateien im Projekt gefunden
- Manuell zu uebertragende oder neu zu erstellende lokale Konfiguration:
  - Home Assistant Konfiguration
  - HACS-Installation
  - Tesla-Account-Login ueber Config Flow
  - eventuell lokal genutzte `cache.json` fuer Entwicklungszwecke, falls ausserhalb des Repos verwendet

## Git-Status

- Branch: `main`
- Remote: `git@github.com:Feberdin/tesla-ha.git`
- uncommitted changes: ja
- letzte Commits:
  - `ecf784b docs: restyle readme with template layout`
  - `0cca01a chore: bump version to 1.2.1`
  - `c9d967e fix: satisfy hassfest and hacs validation requirements`
  - `6e3e710 ci: add hassfest and hacs validation workflows`
  - `68c1947 fix: restrict charging amps to 5-10A and update docs`
- offene lokale Aenderungen grob:
  - `AGENTS.md` war bereits untracked vorhanden
  - `README.md` wurde in dieser Session dokumentarisch erweitert
  - diese Session fuegt ausserdem `PROJECT_CONTEXT.md`, `docs/SETUP.md` und `docs/MIGRATION.md` hinzu

## Offene Enden

- keine committed Test-Suite im Repository
- kein lokaler Start- oder Build-Befehl fuer eine eigenstaendige App dokumentiert
- keine `.env.example` oder andere Beispielkonfiguration fuer Entwicklungsumgebungen vorhanden
- kein eigenes dediziertes README-Banner oder Projekt-Branding ausser den vorhandenen HACS-Brand-Assets
- nur ein Fahrzeug wird aktuell genutzt (`vehicles[0]`)
- moegliche Einschraenkungen bei neueren Tesla-Fahrzeugen durch Command Signing
- Python-Version fuer lokale Entwicklung nicht explizit dokumentiert

## Empfohlene naechste Schritte

1. Auf dem neuen Mac Git- und SSH-Zugriff auf `github.com` testen.
2. Home Assistant und HACS auf dem Zielsystem vorbereiten.
3. Repository klonen und die Integration in Home Assistant ueber HACS oder den vorhandenen Setup-Weg einbinden.
4. Lokalen Syntax-Check ausfuehren und danach die GitHub Actions fuer `hacs` und `hassfest` beobachten.
5. Pruefen, ob fuer lokale Entwicklung eine externe `cache.json` oder andere nicht versionierte Dateien benoetigt werden.
6. Mittel- bis langfristig eine kleine Test-Suite und klarere lokale Entwicklungsanleitung ergaenzen.

## Hinweise fuer macOS-Umzug

- benoetigte Tools:
  - `git`
  - `python3`
  - Browser fuer Tesla-Login und Callback-Flow
- benoetigte Paketmanager:
  - kein separater Paketmanager im Repo dokumentiert
  - HACS fuer die Nutzung in Home Assistant
- manuell zu uebertragende Dateien:
  - keine `.env`-Dateien im Projekt gefunden
  - eventuell lokal genutzte `cache.json` ausserhalb des Repos, falls fuer Entwicklung relevant
- lokale Daten:
  - Home Assistant `.storage` und Integrationszustand liegen nicht im Repository
- Konfigurationsdateien:
  - Home Assistant Konfiguration und HACS muessen auf dem neuen Mac bzw. auf dem Zielsystem vorhanden sein
- SSH/Git-Zugriff:
  - Remote nutzt SSH (`git@github.com:Feberdin/tesla-ha.git`), daher SSH-Key und GitHub-Zugriff auf dem neuen Mac einrichten
- moegliche Stolperfallen:
  - fehlende lokale Test-Suite
  - unklare lokale Python-Version
  - moegliche Tesla-Command-Signing-Einschraenkungen
  - Single-Vehicle-Annahme im Coordinator
