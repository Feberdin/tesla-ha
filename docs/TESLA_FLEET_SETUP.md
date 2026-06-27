# Tesla Fleet Setup fuer Home Assistant

Diese Anleitung beschreibt den aktuellen funktionierenden Weg fuer
`tesla-ha` ab Version `2.0.3`.

## Ziel

Die Integration verbindet Home Assistant mit Teslas offizieller Fleet API.
Dafuer braucht Tesla drei getrennte Dinge, die leicht verwechselt werden:

- OAuth Redirect URI: wohin Tesla nach dem Login zurueckleitet.
- Allowed Origin: welche oeffentliche Domain den Public Key hostet.
- Public Key URL: wo Tesla den Public Key abrufen kann.

Die Integration erzeugt den privaten Schluessel lokal in Home Assistant und
liefert den dazugehoerigen Public Key automatisch unter dem Tesla-Pfad aus,
wenn deine Public-Key-Domain auf Home Assistant zeigt.

## Voraussetzungen

- Home Assistant `2025.1.0` oder neuer
- HACS
- Tesla-Account mit verifizierter E-Mail
- Tesla Developer App
- Oeffentliche HTTPS-Domain fuer Home Assistant oder fuer den Public Key
- Bei Cloudflare Access: Bypass fuer den Public-Key-Pfad

## Tesla Developer App

Erstelle oder bearbeite eine Fleet-API-Anwendung im Tesla Developer Portal.

### OAuth-Genehmigungstyp

Waehle:

```text
Autorisierungscode und Maschine-zu-Maschine
```

Das ist notwendig, weil Home Assistant erst einen Benutzer-Login macht und die
Integration danach einen Partner-Token fuer die Domainregistrierung benoetigt.

### Zulassige Herkunft URL(s)

Trage die oeffentliche Domain ein, die den Tesla Public Key ausliefert.
Beispiel, wenn Home Assistant unter `https://ha.feberdin.de` erreichbar ist:

```text
https://ha.feberdin.de
```

Kein Pfad, kein Slash am Ende.

### Zulassige Weiterleitungs URI(s)

Wenn die Home-Assistant-Integration `my` aktiv ist, trage exakt ein:

```text
https://my.home-assistant.io/redirect/oauth
```

Kein Slash am Ende.

Wenn `my` in Home Assistant deaktiviert ist, nutzt Home Assistant stattdessen
deine externe Home-Assistant-URL:

```text
https://ha.example.com/auth/external/callback
```

Die Integration zeigt die tatsaechlich verwendete Redirect URI vor dem Tesla
Login im Einrichtungsdialog an. Dieser angezeigte Wert ist massgeblich.

### Zulassige Ruecksende URL(s)

Leer lassen.

### API und Arbeitsumfaenge

Fuer Fahrzeuge werden mindestens benoetigt:

- Vehicle Information
- Vehicle Location, falls Standortdaten angezeigt werden sollen
- Vehicle Commands, falls Steuerbefehle genutzt werden sollen
- Vehicle Charging Management, falls Laden gestartet, gestoppt oder geregelt werden soll

## Home Assistant Installation

1. In HACS `Custom repositories` oeffnen.
2. Repository eintragen:

   ```text
   https://github.com/Feberdin/tesla-ha
   ```

3. Kategorie `Integration` waehlen.
4. Integration installieren.
5. Home Assistant neu starten.

## Home Assistant Application Credentials

1. `Einstellungen -> Geraete & Dienste` oeffnen.
2. Drei-Punkte-Menue oeffnen.
3. `Application Credentials` waehlen.
4. Integration `Tesla` oder `tesla_ha` waehlen.
5. Client ID und Client Secret aus der Tesla Developer App eintragen.

Keine Secrets in YAML, Logs, Issues oder Screenshots posten.

## Integration einrichten

1. `Einstellungen -> Geraete & Dienste` oeffnen.
2. `+ Integration hinzufuegen` waehlen.
3. `Tesla` suchen.
4. Die angezeigte Redirect URI mit der Tesla Developer App vergleichen.
5. Tesla OAuth Login abschliessen.
6. Im Domain-Schritt nur den Hostnamen der Public-Key-Domain eingeben.

Beispiel:

```text
ha.feberdin.de
```

Nicht eingeben:

```text
https://ha.feberdin.de
https://ha.feberdin.de/.well-known/appspecific/com.tesla.3p.public-key.pem
```

Die Integration baut daraus automatisch diese URL:

```text
https://ha.feberdin.de/.well-known/appspecific/com.tesla.3p.public-key.pem
```

Ab `2.0.3` liefert Home Assistant diese URL selbst aus, sobald die Domain auf
Home Assistant zeigt und Cloudflare oder dein Reverse Proxy den Pfad nicht
blockiert.

## Cloudflare Access Konfiguration

Wenn Home Assistant ueber Cloudflare Access geschuetzt ist, darf Tesla nicht
auf der Login-Seite, einem Captcha oder einer Challenge landen. Nur der
Public-Key-Pfad muss oeffentlich sein; Home Assistant selbst kann geschuetzt
bleiben.

### Empfohlen: path-spezifische Access Application

Lege in Cloudflare Zero Trust eine zweite Self-hosted Application an.

Name:

```text
Tesla Public Key
```

Ziel:

```text
Subdomain: ha
Domain: feberdin.de
Path: .well-known/appspecific/com.tesla.3p.public-key.pem
```

Wenn Cloudflare im UI den Slash vor dem Pfad schon anzeigt, den Pfad ohne
fuehrenden Slash eintragen.

Policy:

```text
Action: Bypass
Include: Everyone
```

Keine E-Mail-Regel, kein Login, kein Identity Provider.

### WAF und Bot-Regeln

Falls du WAF, Bot Fight Mode, Managed Challenges oder Rate-Limits nutzt, lege
fuer diesen exakten Pfad eine Ausnahme an:

```text
/.well-known/appspecific/com.tesla.3p.public-key.pem
```

Erlaubt sein sollten:

- `GET`
- optional `HEAD`

Nicht erlaubt fuer diesen Pfad:

- Cloudflare Access Login
- Captcha
- Managed Challenge
- Bot Challenge
- HTML-Loginseite statt PEM-Datei

### Cloudflare Tunnel

Wenn `ha.feberdin.de` ueber Cloudflare Tunnel auf Home Assistant zeigt, muss
keine besondere Tunnel-Route fuer den Key angelegt werden. Wichtig ist nur,
dass der Request fuer den Pfad am Home-Assistant-Origin ankommt und nicht von
Access oder WAF abgefangen wird.

## Andere Betriebsarten

### Direkter Reverse Proxy ohne Cloudflare

Wenn `https://ha.example.com` direkt per NGINX, Caddy, Traefik oder Apache auf
Home Assistant zeigt, ist keine separate Datei noetig. Die Integration liefert
den Public Key selbst aus.

Teste:

```bash
curl -i https://ha.example.com/.well-known/appspecific/com.tesla.3p.public-key.pem
```

### Home Assistant nicht oeffentlich erreichbar

Wenn Home Assistant nicht oeffentlich erreichbar ist, nutze eine separate
Public-Key-Domain, zum Beispiel:

```text
tesla.example.com
```

Dann muss dort exakt diese Datei erreichbar sein:

```text
https://tesla.example.com/.well-known/appspecific/com.tesla.3p.public-key.pem
```

In Home Assistant gibst du dann ein:

```text
tesla.example.com
```

In der Tesla Developer App ist die Allowed Origin:

```text
https://tesla.example.com
```

Moegliche Hosts:

- Cloudflare Worker
- Cloudflare Pages
- NGINX
- Caddy
- statischer Webspace

Der Inhalt ist nur der Public Key, nie der Private Key.

### Manuelles Hosting des Public Keys

Wenn die Domain nicht direkt auf Home Assistant zeigt, kopiere den Public Key
aus dem Home-Assistant-Dialog und lege ihn auf dem Zielhost ab.

Die Datei muss exakt so beginnen und enden:

```text
-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----
```

Nicht veroeffentlichen:

```text
-----BEGIN EC PRIVATE KEY-----
...
-----END EC PRIVATE KEY-----
```

## Tests

Teste die Public-Key-URL von einem externen Rechner oder per Terminal:

```bash
curl -i https://ha.feberdin.de/.well-known/appspecific/com.tesla.3p.public-key.pem
```

Erwartung:

```text
HTTP/2 200
content-type: text/plain

-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----
```

Der Test darf nicht zeigen:

- `404: Not Found`
- Cloudflare Access Login
- HTML-Seite
- Captcha
- `-----BEGIN EC PRIVATE KEY-----`

## Virtual Key koppeln

Nach erfolgreicher Domainregistrierung zeigt Home Assistant einen Link:

```text
https://www.tesla.com/_ak/deine-domain
```

Oeffne diesen Link auf einem Smartphone mit installierter Tesla App und kopple
den Virtual Key mit dem Fahrzeug. Ohne Virtual Key funktionieren bei vielen
neueren Fahrzeugen Sensoren, aber keine signierten Steuerbefehle.

## Troubleshooting

### Tesla meldet: redirect_uri supplied is not registered

Ursache: Die Redirect URI aus Home Assistant ist nicht exakt in der Tesla
Developer App eingetragen.

Fix:

1. Home Assistant Dialog lesen.
2. Angezeigte Redirect URI kopieren.
3. In Tesla als `Zulassige Weiterleitungs URI(s)` eintragen.
4. Speichern.
5. Einige Minuten warten.
6. OAuth neu starten.

### Public-Key-URL liefert 404

Moegliche Ursachen:

- Integration ist noch nicht auf `2.0.3` oder neuer.
- Home Assistant wurde nach dem Update nicht neu gestartet.
- Der Tesla-Key wurde im Setup noch nicht erzeugt.
- Reverse Proxy oder Tunnel leitet den Pfad nicht an Home Assistant weiter.
- Du nutzt eine andere Public-Key-Domain, auf der keine Datei liegt.

### Public-Key-URL zeigt Cloudflare Login oder Captcha

Ursache: Cloudflare Access oder WAF greift fuer den Pfad.

Fix:

- Access Application fuer exakt diesen Pfad anlegen.
- Policy `Bypass` mit `Everyone`.
- WAF/Bot-Ausnahme fuer exakt diesen Pfad.

### Tesla meldet Public Key mismatch

Ursache: Der gehostete Public Key passt nicht zum lokalen Private Key in Home
Assistant.

Fix:

- Bei direkter HA-Domain die automatische Route nutzen.
- Bei externem Hosting den Public Key aus dem aktuellen Home-Assistant-Dialog
  neu kopieren.
- Keine alten Keys aus vorherigen Setup-Versuchen verwenden.

### Partnerregistrierung schlaegt fehl

Pruefen:

- Allowed Origin ist exakt `https://deine-domain`.
- Public-Key-URL ist extern erreichbar.
- Zertifikat ist gueltig.
- Keine Cloudflare Challenge.
- Tesla Developer App ist gespeichert.
- Nach Aenderungen einige Minuten warten.

## Sicherheit

- Private Key bleibt lokal in Home Assistant, typischerweise als
  `tesla_ha.key`.
- Public Key darf oeffentlich sein.
- Client Secret gehoert nur in Home Assistant Application Credentials.
- Keine Tokens, Secrets oder Private Keys in Git, Issues, Screenshots oder
  Logs posten.

## Referenzen

- Tesla Fleet API Third-Party Tokens:
  https://developer.tesla.com/docs/fleet-api/authentication/third-party-tokens
- Tesla Fleet API Announcements:
  https://developer.tesla.com/docs/fleet-api/announcements
- Home Assistant Tesla Fleet:
  https://www.home-assistant.io/integrations/tesla_fleet/
- Home Assistant HTTP static files:
  https://www.home-assistant.io/integrations/http/
- Cloudflare Access self-hosted applications:
  https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/
- Cloudflare Access application paths:
  https://developers.cloudflare.com/cloudflare-one/access-controls/policies/app-paths/
