# Contributing

Dieses Repository enthaelt eine HACS-kompatible Home Assistant Integration fuer Tesla-Fahrzeuge.
Beitraege sollen die Integration robuster, besser dokumentiert und leichter wartbar machen.

## Scope

Sinnvolle Beitraege verbessern mindestens einen dieser Bereiche:

- Stabilitaet und Fehlerbehandlung der Integration
- Nachvollziehbarkeit der Home Assistant Entitaeten und Steuerfunktionen
- Einrichtungs- und Betriebsdokumentation
- HACS-, Hassfest- und Repository-Qualitaet

## Lokaler Workflow

1. Erstelle einen Branch mit klarem Scope, zum Beispiel `fix/wakeup-timeout` oder `docs/readme-cleanup`.
2. Halte Aenderungen klein und zusammenhaengend.
3. Pruefe bei Doku-Aenderungen, ob README und Screenshots wirklich zum aktuellen Code passen.
4. Fuehre mindestens Syntax-Check und Unit-Tests lokal aus:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest "httpx[http2]==0.28.1"
.venv/bin/python -m compileall -q custom_components tests
.venv/bin/python -m pytest tests/test_tesla_owner.py -q
```

5. Oeffne einen Pull Request mit einer kurzen Beschreibung:
   - was geaendert wurde
   - warum es geaendert wurde
   - wie es geprueft wurde

## Validierung

Verfuegbare Qualitaetssicherung ist derzeit:

- lokaler Syntax-Check ueber `.venv/bin/python -m compileall -q custom_components tests`
- Unit-Tests fuer die Tesla Owner API Kernlogik ueber `.venv/bin/python -m pytest tests/test_tesla_owner.py -q`
- GitHub Actions fuer `hassfest`
- GitHub Actions fuer `hacs`
- manuelle Pruefung in Home Assistant bei Aenderungen am Config Flow oder an Entitaeten

## Stilrichtlinien

- Dokumentiere nur Verhalten, das im Repository wirklich existiert.
- Erfinde keine Features, Konfigurationen oder Installationswege in der Doku.
- Halte Commit-Nachrichten kurz und eindeutig, zum Beispiel:
  - `fix: handle wake-up timeout gracefully`
  - `docs: restructure readme for hacs release`
- Kennzeichne externe Karten, Bilder oder Dashboard-Elemente klar, wenn sie nicht Teil dieser Integration sind.
- Committe niemals Tokens, lokale `cache.json` Dateien oder andere sensible Daten.

## Pull Requests

Ein guter Pull Request ist:

- fachlich klar abgegrenzt
- fuer Reviewer schnell nachvollziehbar
- mit angepasster Dokumentation, wenn sich Verhalten oder Einrichtung aendert
- ohne unnoetige Nebenbaustellen

## Fragen und Abstimmung

Wenn unklar ist, ob eine Aenderung in dieses Repository gehoert, nutze zuerst ein Issue oder eine PR-Beschreibung zur Einordnung.
Das hilft besonders bei Themen wie neuem Branding, zusaetzlichen Dokumentationsseiten oder groesseren funktionalen Erweiterungen.
