# Contributing to tesla-ha

Danke, dass du zu `Feberdin/tesla-ha` beitragen möchtest.

## Ziel des Projekts

Diese Integration soll Tesla-Daten und -Steuerung in Home Assistant zuverlässig,
nachvollziehbar und für Nicht-Programmierer nutzbar machen.

## Voraussetzungen

- Python 3.11+
- Home Assistant Core Entwicklungsumgebung
- GitHub Account

## Lokale Entwicklung

1. Fork erstellen und klonen.
2. Branch erstellen:
   - `feature/<kurze-beschreibung>`
   - `fix/<kurze-beschreibung>`
3. Abhängigkeiten installieren (Beispiel):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements-dev.txt
```

Falls `requirements-dev.txt` noch fehlt, bitte die benötigten Pakete im PR
klar benennen.

## Coding Guidelines

- Kleine, klar benannte Funktionen
- Defensive Fehlerbehandlung mit klaren Log-Meldungen
- Keine Secrets, Tokens oder persönliche Daten committen
- API-Änderungen in README dokumentieren
- Nutzerwirkung von Änderungen im PR erklären

## Tests

Vor jedem PR bitte lokal ausführen:

```bash
pytest -q
python3 -m compileall -q custom_components
```

Mindestens:

- Happy-Path Test(s)
- Wichtige Edge Cases
- 1-2 Negativtests

## Commit- und PR-Richtlinien

- Aussagekräftige Commit Messages, z. B.:
  - `feat: add seat cooling detection`
  - `fix: handle wake-up timeout gracefully`
- Ein PR sollte ein Thema behandeln (kein Big-Bang).
- PR-Beschreibung enthält:
  - Was wurde geändert?
  - Warum wurde es geändert?
  - Wie wurde es getestet?
  - Gibt es Risiken oder Breaking Changes?

## Review-Erwartung

Wir reviewen auf:

- Korrektheit
- Lesbarkeit
- Robustheit/Fehlerfälle
- Testabdeckung
- Nutzerverständlichkeit (README/Logs/Fehlermeldungen)

## Security

Bitte melde Sicherheitslücken **nicht** als öffentliches Issue.
Siehe Security Policy: `.github/SECURITY.md`.
