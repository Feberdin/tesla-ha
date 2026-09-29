# Tesla Home Assistant Integration — Projektkontext für Codex

## Projektübersicht

Home Assistant Custom Integration (HACS-kompatibel), die Tesla-Fahrzeuge über Teslas offizielle Fleet API anbindet — basierend auf OAuth2, Developer-App und Public-Key-Partnerregistrierung.

- **HACS-Domain:** `tesla_ha`
- **Version:** `1.2.0`
- **HA Mindestversion:** `2023.1.0`
- **Lizenz:** MIT
- **Abhängigkeit:** `tesla-fleet-api==1.4.7`

---

## Verzeichnisstruktur

```
custom_components/tesla_ha/
├── __init__.py          Setup/Teardown der Integration
├── manifest.json        HA Integration Manifest
├── const.py             Konstanten (Domain, Plattformen, Intervall, Modelle)
├── coordinator.py       Datenabruf, Wake-up-Logik, Befehlsausführung
├── config_flow.py       OAuth2 PKCE Authentifizierungsflow
├── sensor.py            24 Sensoren
├── binary_sensor.py     22 Binärsensoren
├── climate.py           Standheizung / Klimaanlage
├── lock.py              Türschloss
├── switch.py            Schalter (Laden, Sentry, Heizungen)
├── button.py            Tasten (Hupe, Frunk, Mediensteuerung)
├── number.py            Nummern (Ladelimit, Ladestrom)
├── select.py            Auswahl (Sitzheizung/-kühlung)
├── strings.json         UI-Strings (Basis)
└── translations/
    ├── de.json          Deutsche Übersetzung
    └── en.json          Englische Übersetzung
```

---

## Architektur

### coordinator.py — TeslaDataCoordinator

Erbt von `DataUpdateCoordinator`. Alle API-Calls sind synchron (`teslapy`) und laufen über `hass.async_add_executor_job`.

**Datenabruf (`_fetch_data`):**
- Öffnet `teslapy.Tesla`-Session mit E-Mail + Cache-Datei
- Wake-up-Logik: bis zu 12 Versuche × 10 Sekunden
- Ruft `vehicle.get_vehicle_data()` ab
- Ermittelt beim ersten Abruf: VIN → Modell (VIN[3]), `has_seat_cooling`
- Nur `vehicles[0]` (kein Multi-Vehicle-Support)

**Befehlsausführung (`async_command`):**
- Wake-up falls nötig → `vehicle.api(command, **kwargs)` → 3s Pause → Daten-Refresh

**Update-Intervall:** `UPDATE_INTERVAL = 5` Minuten (in `const.py`)

### config_flow.py — Authentifizierung

OAuth2 PKCE-Flow:
1. Benutzer gibt Tesla-E-Mail ein
2. System generiert Authorization-URL + Code-Verifier
3. Benutzer loggt sich bei Tesla ein → kopiert Callback-URL (`https://auth.tesla.com/void/callback?code=...`)
4. Token-Austausch → gespeichert in `.storage/tesla_ha_{entry_id}.json`

### __init__.py — Entry Setup

Liest Cache aus `entry.data["cache"]`, schreibt in `.storage/`, initialisiert Coordinator, lädt alle 8 Plattformen.

---

## Implementierte Entitäten

| Typ | Anzahl | Beispiele |
|---|---|---|
| `sensor` | 24 | Ladestand, Reichweite, Temperaturen, Reifendruck, Wiedergabe |
| `binary_sensor` | 22 | Türen, Fenster, Laden, Klimaanlage, Sentry |
| `climate` | 1 | Standheizung (15–28 °C) |
| `lock` | 1 | Türschloss |
| `switch` | 5 | Laden, Sentry Mode, Lenkradheizung, Maximalheizung |
| `button` | 11 | Hupe, Frunk, Kofferraum, Ladeanschluss, Medien |
| `number` | 2 | Ladelimit (50–100 %), Ladestrom (1 A – max) |
| `select` | 4–6 | Sitzheizung/-kühlung (Sitzkühlung wird automatisch erkannt) |

---

## Bekannte Einschränkungen

1. **Nur 1 Fahrzeug:** `vehicles[0]` — kein Multi-Vehicle-Support
2. **Neuere Fahrzeuge (~2022+, Gigafactory Berlin):** Befehle können wegen Befehls-Signierprotokoll fehlschlagen — Sensoren funktionieren weiterhin
3. **Synchrone API:** `teslapy` ist synchron → alle Calls über `async_add_executor_job`
4. **12V-Akku:** Bei Intervall < 5 Min nachts kein Polling empfehlenswert
5. **Wake-up:** Kann bis zu 2 Minuten dauern bei schlechtem Empfang

---

## Sicherheitshinweis

Eine `cache.json` im Projektwurzelverzeichnis enthält OAuth-Tokens für lokale Entwicklung.
**Diese Datei darf niemals committed oder veröffentlicht werden.**
In der produktiven Integration liegt der Cache ausschließlich in HA `.storage/`.

---

## Testumgebung

- `pytest-homeassistant-custom-component` für Unit-Tests
- Home Assistant Developer Container für Integrationstests
- Mindestversion HA: `2023.1.0`

---

## Git-Historie

```
3996221  feat: Complete integration v1.2.0 — all sensors, controls and full README
cd4c356  fix: Correct lock endpoint names and add delay before state refresh
be9f5f1  feat: Add vehicle controls (climate, lock, switch, button, number)
dd9c2e0  Initial release: Tesla Home Assistant integration v1.0.0
```
