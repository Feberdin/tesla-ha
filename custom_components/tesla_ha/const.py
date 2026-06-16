"""Constants for the Tesla Fleet based Home Assistant integration.

Purpose:
    Keeps domain names, platform lists, polling cadence, OAuth endpoints and
    shared Fleet scopes in one small module.

Input / Output:
    Input is static configuration from Tesla and Home Assistant conventions.
    Output is imported by config flow, OAuth setup, coordinator and entities.

Important invariants:
    The integration domain stays `tesla_ha` so existing HACS installs and
    entity ids remain stable. The API transport is now official Tesla Fleet
    OAuth, not the blocked legacy Owner API.

Debugging:
    If OAuth URLs or required scopes look wrong in Home Assistant, inspect
    these constants first before changing config-flow code.
"""

from __future__ import annotations

from tesla_fleet_api.const import Scope

DOMAIN = "tesla_ha"
PLATFORMS = [
    "sensor",
    "binary_sensor",
    "climate",
    "lock",
    "switch",
    "button",
    "number",
    "select",
]
UPDATE_INTERVAL = 10  # minutes, matches Fleet API's cost-sensitive polling model.

AUTHORIZE_URL = "https://auth.tesla.com/oauth2/v3/authorize"
TOKEN_URL = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token"
DEFAULT_FLEET_API_BASE_URL = "https://fleet-api.prd.eu.vn.cloud.tesla.com"

SCOPES = [
    Scope.OPENID,
    Scope.OFFLINE_ACCESS,
    Scope.USER_DATA,
    Scope.VEHICLE_DEVICE_DATA,
    Scope.VEHICLE_LOCATION,
    Scope.VEHICLE_CMDS,
    Scope.VEHICLE_CHARGING_CMDS,
]

TESLA_MODELS = {
    "3": "Model 3",
    "S": "Model S",
    "X": "Model X",
    "Y": "Model Y",
    "T": "Cybertruck",
    "R": "Roadster",
}
