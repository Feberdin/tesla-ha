# Setup

Diese Datei beschreibt den technischen Kurzstart fuer dieses Repository.
Die ausfuehrliche Endnutzer-Anleitung fuer Tesla Developer Portal,
Home Assistant, Cloudflare und Public-Key-Hosting steht in
[TESLA_FLEET_SETUP.md](TESLA_FLEET_SETUP.md).

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
- OAuth Grant Type `Authorization Code` und `Machine-to-Machine`
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

1. Tesla Developer App nach [TESLA_FLEET_SETUP.md](TESLA_FLEET_SETUP.md) konfigurieren.
2. In Home Assistant `Application Credentials` fuer `Tesla` / `tesla_ha` anlegen.
3. `Tesla` als Integration hinzufuegen.
4. Tesla OAuth im Browser abschliessen.
5. Im Domain-Schritt nur den Hostnamen eingeben, zum Beispiel `ha.feberdin.de`.
6. Public-Key-URL extern pruefen:

   ```bash
   curl -i https://ha.feberdin.de/.well-known/appspecific/com.tesla.3p.public-key.pem
   ```

7. Den angezeigten Virtual-Key-Link oeffnen und den Schluessel im Fahrzeug koppeln.

## Zu pruefen

- Welche Python-Version wird im persoenlichen Setup bevorzugt?
- Soll die Integration nur in Home Assistant laufen oder auch in einer separaten lokalen Dev-Umgebung getestet werden?
