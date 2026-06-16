# macOS-Migration

Diese Datei dokumentiert projektspezifische Punkte fuer den Umzug auf einen neuen Mac.

## Kurzcheck

- Repository: `git@github.com:Feberdin/tesla-ha.git`
- Branch: `main`
- Projekttyp: HACS-kompatible Home Assistant Custom Integration
- Sprache: Python
- Kritische lokale Voraussetzungen:
  - Git- und SSH-Zugriff auf GitHub
  - Home Assistant `2025.1.0` oder neuer
  - HACS
  - Tesla Developer App mit Client ID und Client Secret
  - oeffentliche HTTPS-Domain fuer Tesla Public Key und Virtual Key

## Manuell zu beachten

- Das Projekt enthaelt keine `.env`-Dateien im Repository.
- Home Assistant Laufzeitdaten und `.storage` liegen nicht im Repository und muessen separat beruecksichtigt werden.
- Alte Owner-API-`cache.json` Dateien werden nicht mehr verwendet und duerfen nicht migriert werden.
- GitHub-Remote nutzt SSH. Auf dem neuen Mac muessen SSH-Key und GitHub-Zugriff eingerichtet werden.

## Risiken

- Fleet API Einrichtung braucht Tesla Developer Portal, Allowed Origin, Public Key Hosting und Virtual-Key-Kopplung
- Kein dokumentierter lokaler Build- oder Startprozess ausser Home Assistant selbst
- Command-Signing kann bei neueren Tesla-Fahrzeugen Steuerbefehle einschranken
- Der Code nutzt aktuell nur das erste gefundene Fahrzeug (`vehicles[0]`)

## Empfohlene Reihenfolge nach dem Umzug

1. Git und SSH fuer GitHub einrichten.
2. Repository klonen.
3. Home Assistant und HACS vorbereiten.
4. Integration ueber HACS einbinden.
5. Tesla Application Credentials in Home Assistant hinterlegen.
6. Tesla Fleet Config Flow in Home Assistant abschliessen.
7. Public Key hosten und Virtual Key koppeln.
8. Lokalen Syntax-Check ausfuehren.
9. Danach GitHub Actions und Verhalten im Home Assistant UI pruefen.
