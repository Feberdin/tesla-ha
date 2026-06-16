# Setup auf einem neuen Mac

Diese Datei sammelt nur Setup-Schritte, die aus dem aktuellen Repository ableitbar sind.
Wo Details im Projekt fehlen, ist das bewusst als `zu pruefen` markiert.

## Ziel

Das Repository enthaelt eine Home Assistant Custom Integration fuer Tesla-Fahrzeuge.
Es gibt keinen eigenstaendigen lokalen App-Start, sondern die Integration wird in Home Assistant betrieben.

## Voraussetzungen

- Git
- Python 3: genaue Version im Repository nicht explizit dokumentiert, lokal zu pruefen
- Home Assistant `2025.1.0` oder neuer
- HACS
- Tesla-Account
- Tesla Developer App mit Client ID und Client Secret
- oeffentliche HTTPS-Domain fuer den Tesla Public Key

## Repository holen

```bash
git clone git@github.com:Feberdin/tesla-ha.git
cd tesla-ha
```

## Lokale Validierung

Aktuell ist im Repository nur ein sicher ableitbarer lokaler Check dokumentiert:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install pytest tesla-fleet-api==1.4.7
.venv/bin/python -m compileall -q custom_components tests
.venv/bin/python -m pytest tests/test_tesla_fleet.py -q
```

Weitere Validierung laeuft ueber GitHub Actions:

- `hacs`
- `hassfest`

## Installation in Home Assistant

1. In Home Assistant `HACS` oeffnen.
2. `Custom repositories` waehlen.
3. `https://github.com/Feberdin/tesla-ha` als Repository eintragen.
4. Kategorie `Integration` waehlen.
5. Integration herunterladen.
6. Home Assistant neu starten.

## Einrichtung

1. `Einstellungen -> Geraete & Dienste` oeffnen.
2. Unter `Application Credentials` Client ID und Client Secret fuer die Tesla Developer App hinterlegen.
3. `Tesla` als Integration hinzufuegen.
4. Tesla OAuth im Browser abschliessen.
5. Public-Key-Domain eingeben.
6. Den angezeigten Public Key unter der Well-Known-URL hosten.
7. Den angezeigten Virtual-Key-Link oeffnen und den Schluessel im Fahrzeug koppeln.

## Zu pruefen

- Welche Public-Key-Domain wird fuer den jeweiligen Home-Assistant-Betrieb genutzt?
- Welche Python-Version wird im persoenlichen Setup bevorzugt?
- Soll die Integration nur in Home Assistant laufen oder auch in einer separaten lokalen Dev-Umgebung getestet werden?
