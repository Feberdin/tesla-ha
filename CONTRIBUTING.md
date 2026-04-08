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
4. Fuehre mindestens den Syntax-Check lokal aus:

```bash
python3 -m compileall -q custom_components
```

5. Oeffne einen Pull Request mit einer kurzen Beschreibung:
   - was geaendert wurde
   - warum es geaendert wurde
   - wie es geprueft wurde

## Validierung

Dieses Repository hat aktuell keine eingecheckte lokale Test-Suite.
Verfuegbare Qualitaetssicherung ist derzeit:

- lokaler Syntax-Check ueber `python3 -m compileall -q custom_components`
- GitHub Actions fuer `hassfest`
- GitHub Actions fuer `hacs`
- manuelle Pruefung in Home Assistant bei Aenderungen am Config Flow oder an Entitaeten

> TODO: Eine committed Test-Suite fuer Kernlogik und Config Flow waere ein sinnvoller naechster Ausbau.

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
