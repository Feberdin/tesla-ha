# Tesla für Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge&logo=home-assistant)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/Feberdin/tesla-ha?style=for-the-badge)](https://github.com/Feberdin/tesla-ha/releases)
[![License](https://img.shields.io/github/license/Feberdin/tesla-ha?style=for-the-badge)](LICENSE)

Vollständige Tesla-Integration für Home Assistant — **kostenlos**, kein Fleet API Abo, kein Developer-Account nötig. Basiert auf der inoffiziellen Tesla Owner API.

---

## Funktionsumfang

### Sensoren (24)

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
| Minuten bis voll | Restzeit bis zum Ladelimit | min |
| Laderate | Reichweite die pro Stunde nachgeladen wird | km/h |
| Kilometerstand | Gesamtkilometer | km |
| Fahrstufe | P / D / R / N | — |
| Leistung | Aktueller Verbrauch / Rekuperation | kW |
| Software Version | Aktuell installierte Version | — |
| Software Update | Verfügbare Update-Version | — |
| Dashcam | Dashcam-Status | — |
| Innentemperatur | Temperatur im Fahrzeuginnenraum | °C |
| Außentemperatur | Außentemperatur | °C |
| Reifendruck VL | Vorne links | bar |
| Reifendruck VR | Vorne rechts | bar |
| Reifendruck HL | Hinten links | bar |
| Reifendruck HR | Hinten rechts | bar |
| Wiedergabe | Aktuell spielender Künstler & Titel | — |

### Binärsensoren (22)

| Sensor | Beschreibung |
|---|---|
| Lädt | Fahrzeug lädt gerade |
| Kabel angesteckt | Ladekabel eingesteckt |
| Ladeanschluss offen | Ladeklappe geöffnet |
| Batterieheizung | Batterieheizung aktiv |
| Verriegelt | Fahrzeug ist verriegelt |
| Nutzer anwesend | Jemand sitzt im Fahrzeug |
| Fahrertür | Fahrertür offen |
| Beifahrertür | Beifahrertür offen |
| Fondtür Links | Hintere Fahrertür offen |
| Fondtür Rechts | Hintere Beifahrertür offen |
| Frunk offen | Vordere Haube geöffnet |
| Kofferraum offen | Kofferraum geöffnet |
| Fenster Fahrer | Fahrerfenster offen |
| Fenster Beifahrer | Beifahrerfenster offen |
| Fenster Fond Links | Hinteres Fahrerfenster offen |
| Fenster Fond Rechts | Hinteres Beifahrerfenster offen |
| Klimaanlage | Klimaanlage aktiv |
| Sentry Mode | Sentry Mode aktiv |
| Reifendruckwarnung VL | Reifendruckproblem vorne links |
| Reifendruckwarnung VR | Reifendruckproblem vorne rechts |
| Reifendruckwarnung HL | Reifendruckproblem hinten links |
| Reifendruckwarnung HR | Reifendruckproblem hinten rechts |

### Steuerung

| Entität | Typ | Beschreibung |
|---|---|---|
| Standheizung | Climate | Ein/Aus + Zieltemperatur 15–28 °C |
| Türschloss | Lock | Verriegeln / Entriegeln |
| Sentry Mode | Switch | Sentry Mode ein-/ausschalten |
| Laden | Switch | Laden starten / stoppen |
| Lenkradheizung | Switch | Lenkradheizung ein-/ausschalten |
| Maximal-Heizung | Switch | Alle Heizungen auf Maximum (Enteisen) |
| Ladelimit | Number | Ladelimit 50–100 % |
| Ladestrom | Number | Ladestrom 1 A – max. A des Fahrzeugs |
| Sitzheizung Fahrer | Select | Aus / Stufe 1 / Stufe 2 / Stufe 3 |
| Sitzheizung Beifahrer | Select | Aus / Stufe 1 / Stufe 2 / Stufe 3 |
| Sitzheizung Fond Links | Select | Aus / Stufe 1 / Stufe 2 / Stufe 3 |
| Sitzheizung Fond Rechts | Select | Aus / Stufe 1 / Stufe 2 / Stufe 3 |
| Sitzkühlung Fahrer | Select | Aus / Stufe 1 / Stufe 2 / Stufe 3 ¹ |
| Sitzkühlung Beifahrer | Select | Aus / Stufe 1 / Stufe 2 / Stufe 3 ¹ |
| Lichter blinken | Button | Lichter kurz aufblinken lassen |
| Hupe | Button | Hupe betätigen |
| Frunk öffnen | Button | Vordere Haube öffnen |
| Kofferraum öffnen | Button | Hintere Klappe öffnen |
| Ladeanschluss öffnen | Button | Ladeklappe öffnen |
| Ladeanschluss schließen | Button | Ladeklappe schließen |
| Wiedergabe Pause/Play | Button | Musik pausieren / fortsetzen |
| Nächster Titel | Button | Nächsten Titel überspringen |
| Vorheriger Titel | Button | Vorherigen Titel wiederholen |
| Lautstärke lauter | Button | Lautstärke erhöhen |
| Lautstärke leiser | Button | Lautstärke verringern |

> ¹ Nur bei Fahrzeugen mit Sitzkühlung (wird automatisch erkannt)

### Welche Funktionen kann die Integration steuern?

Die Integration kann folgende Funktionen aktiv steuern:

- Klima: Standheizung/Klimaanlage ein- und ausschalten, Zieltemperatur setzen (15–28 °C)
- Fahrzeugzugriff: Verriegeln und Entriegeln
- Laden: Laden starten/stoppen, Ladelimit setzen, Ladestrom einstellen
- Sicherheit/Komfort: Sentry Mode, Lenkradheizung, Maximal-Heizung (Defrost)
- Sitze: Sitzheizungen (vorn + hinten) und je nach Fahrzeug Sitzkühlung (vorn)
- Fahrzeugaktionen: Lichter blinken, Hupe, Frunk öffnen, Kofferraum öffnen
- Ladeport: Ladeanschluss öffnen und schließen
- Medien: Wiedergabe/Pause, nächster/vorheriger Titel, Lautstärke lauter/leiser

### Screenshots

**Home Assistant Karten mit Entitäten dieser Integration**

![Steuerelemente Übersicht](assets/screenshots/ha-controls-overview-1.png)
![Steuerelemente und Sensoren](assets/screenshots/ha-controls-and-sensors-overview-2.png)
![Sensoren Übersicht Teil 1](assets/screenshots/ha-sensors-overview-1.png)
![Sensoren Übersicht Teil 2](assets/screenshots/ha-sensors-overview-2.png)

**Vehicle Status-Karte (externe Integration)**

![Externe Vehicle Status-Karte](assets/screenshots/external-vehicle-status-card.png)

> Hinweis: Die Vehicle Status-Karte im Screenshot stammt aus einer externen Integration und dient hier nur der Darstellung.
> Vielen Dank an die Entwickler:innen dieser Karte.

---

## Installation

### Voraussetzungen

- Home Assistant **2023.1.0** oder neuer
- [HACS](https://hacs.xyz) installiert
- Tesla-Account (kein Fleet API Abo nötig)

---

### Schritt 1 — HACS öffnen und Custom Repository hinzufügen

1. In Home Assistant auf **HACS** klicken (linke Seitenleiste)
2. Oben rechts auf das **Drei-Punkte-Menü** (⋮) klicken
3. **Custom repositories** auswählen

   ![HACS Custom Repository Menu](https://img.shields.io/badge/HACS-%E2%8B%AE%20Custom%20repositories-blue)

4. Im Feld **Repository** folgende URL **vollständig** einfügen:

   ```
   https://github.com/Feberdin/tesla-ha
   ```

   > ⚠️ **Wichtig:** Die URL muss exakt so eingegeben werden — inklusive `https://` am Anfang. Keine Schrägstriche am Ende.

5. Als **Kategorie** `Integration` auswählen
6. Auf **Add** klicken

---

### Schritt 2 — Integration herunterladen

1. In HACS nach **Tesla** suchen
   *(oder direkt: HACS → Integrationen → Tesla)*
2. Auf **Herunterladen** klicken
3. Die Versionswahl bestätigen
4. Home Assistant **neu starten**
   *(Einstellungen → System → Neu starten)*

---

### Schritt 3 — Integration einrichten

1. **Einstellungen** → **Geräte & Dienste** öffnen
2. Unten rechts auf **+ Integration hinzufügen** klicken
3. Nach **Tesla** suchen und auswählen
4. Tesla-E-Mail-Adresse eingeben und auf **Weiter** klicken
5. Den angezeigten **Login-Link** in einem neuen Browser-Tab öffnen
6. Mit deinem Tesla-Account **einloggen**
7. Du landest auf einer **leeren weißen Seite** — das ist normal
8. Die vollständige URL aus der Adressleiste kopieren
   *(beginnt mit `https://auth.tesla.com/void/callback?code=...`)*
9. Die URL in das Feld **Callback URL** einfügen
10. Auf **Weiter** klicken — die Integration ist eingerichtet

---

### Schritt 4 — Fertig

Das Fahrzeug erscheint jetzt als Gerät unter **Einstellungen → Geräte & Dienste → Tesla**.

Alle Sensoren und Steuerelemente sind sofort verfügbar und können in Dashboards, Automationen und Skripten verwendet werden.

---

## Konfiguration

### Aktualisierungsintervall

Standardmäßig werden Daten alle **5 Minuten** abgerufen. Das Fahrzeug wird dabei automatisch geweckt, falls es schläft.

> **Hinweis für den 12V-Akku:** Häufige Abfragen können den 12V-Akku belasten. Bei einem Intervall unter 5 Minuten empfiehlt es sich, das Fahrzeug nachts nicht zu pollen (Automation mit Zeitbedingung).

Das Intervall kann in `custom_components/tesla_ha/const.py` angepasst werden:

```python
UPDATE_INTERVAL = 5  # Minuten
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
        message: "Reifendruck prüfen: {{ trigger.to_state.name }}"
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

## Fehlerbehebung

### Integration erscheint nicht in HACS
→ Stelle sicher, dass die URL exakt `https://github.com/Feberdin/tesla-ha` lautet (kein Trailing-Slash, kein `.git`)

### Callback URL wird nicht akzeptiert
→ Der Login-Link ist nur **einmal** gültig. Öffne die Einrichtung erneut, um einen neuen Link zu generieren.

### Befehle funktionieren nicht (z.B. Schloss, Klimaanlage)
→ Neuere Tesla-Fahrzeuge (Gigafactory Berlin, ab ~2022) können das neue Befehls-Signierprotokoll erzwingen. In den HA-Logs erscheint dann eine entsprechende Meldung. Die Sensoren sind davon **nicht** betroffen.

### Fahrzeug schläft und wird nicht aufgeweckt
→ Das Aufwecken kann bis zu 2 Minuten dauern. Prüfe ob das Fahrzeug Mobilfunk- oder WLAN-Empfang hat.

---

## Lizenz

MIT License — siehe [LICENSE](LICENSE)
