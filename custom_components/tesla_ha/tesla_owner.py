"""Tesla Owner API access with modern transport requirements.

Purpose:
    Provides the small Tesla cloud client used by this Home Assistant
    integration. The client keeps the existing Owner API data shape so the
    entity files can stay simple and unchanged.

Input / Output:
    Inputs are the Tesla account email, the Home Assistant cache file path, and
    OAuth callback URLs or cached tokens. Outputs are Python dictionaries shaped
    like Tesla's Owner API responses: product lists, vehicle data and command
    responses.

Important invariants:
    Tokens are read from and written to Home Assistant's private `.storage`
    path only. Token values are never logged. All Tesla HTTPS requests use an
    HTTP/2-capable client and require TLS 1.3 when the Python runtime supports
    that setting.

Debugging:
    Enable Home Assistant debug logging for `custom_components.tesla_ha`.
    Logs show request method, Tesla path, status code and negotiated HTTP
    version, but never Authorization headers, refresh tokens or access tokens.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import secrets
import ssl
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

_LOGGER = logging.getLogger(__name__)

TESLA_AUTH_BASE_URL = "https://auth.tesla.com"
TESLA_OWNER_BASE_URL = "https://owner-api.teslamotors.com"
OWNER_CLIENT_ID = "ownerapi"
OWNER_REDIRECT_URI = "https://auth.tesla.com/void/callback"
OWNER_SCOPE = ("openid", "email", "offline_access")

TOKEN_REFRESH_MARGIN_SECONDS = 300
REQUEST_TIMEOUT_SECONDS = 20.0
WAKE_UP_PATH = "api/1/vehicles/{vehicle_id}/wake_up"
VEHICLE_DATA_ENDPOINTS = (
    "location_data;charge_state;climate_state;vehicle_state;"
    "gui_settings;vehicle_config"
)

COMMAND_PATHS = {
    "ACTUATE_TRUNK": "actuate_trunk",
    "CHANGE_CHARGE_LIMIT": "set_charge_limit",
    "CHANGE_CLIMATE_TEMPERATURE_SETTING": "set_temps",
    "CHARGE_PORT_DOOR_CLOSE": "charge_port_door_close",
    "CHARGE_PORT_DOOR_OPEN": "charge_port_door_open",
    "CHARGING_AMPS": "set_charging_amps",
    "CLIMATE_OFF": "auto_conditioning_stop",
    "CLIMATE_ON": "auto_conditioning_start",
    "FLASH_LIGHTS": "flash_lights",
    "HONK_HORN": "honk_horn",
    "LOCK": "door_lock",
    "MAX_DEFROST": "set_preconditioning_max",
    "MEDIA_NEXT_TRACK": "media_next_track",
    "MEDIA_PREVIOUS_TRACK": "media_prev_track",
    "MEDIA_TOGGLE_PLAYBACK": "media_toggle_playback",
    "MEDIA_VOLUME_DOWN": "media_volume_down",
    "MEDIA_VOLUME_UP": "media_volume_up",
    "REMOTE_SEAT_COOLING_REQUEST": "remote_seat_cooler_request",
    "REMOTE_SEAT_HEATER_REQUEST": "remote_seat_heater_request",
    "REMOTE_STEERING_WHEEL_HEATER_REQUEST": (
        "remote_steering_wheel_heater_request"
    ),
    "SET_SENTRY_MODE": "set_sentry_mode",
    "START_CHARGE": "charge_start",
    "STOP_CHARGE": "charge_stop",
    "UNLOCK": "door_unlock",
}

COMMAND_ALIASES = {
    # Older entity code used this clearer local name. Tesla's endpoint name is
    # still `set_charge_limit`, so we keep the UI command stable here.
    "SET_CHARGE_LIMIT": "CHANGE_CHARGE_LIMIT",
}


@dataclass(frozen=True)
class TeslaOAuthSession:
    """OAuth details that Home Assistant keeps between config-flow steps."""

    authorization_url: str
    code_verifier: str
    state: str


class TeslaOwnerApiError(Exception):
    """Actionable Tesla cloud error safe to show in Home Assistant."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        context: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.context = context
        details = []
        if status_code is not None:
            details.append(f"Status: {status_code}")
        if context:
            details.append(f"Kontext: {context}")
        full_message = f"{message} ({'; '.join(details)})" if details else message
        super().__init__(full_message)


class TeslaOwnerAuthError(TeslaOwnerApiError):
    """Authentication-specific Tesla cloud error."""


def create_oauth_session() -> TeslaOAuthSession:
    """Create a PKCE authorization URL for Tesla's legacy Owner API client."""

    code_verifier = _new_pkce_verifier()
    code_challenge = _pkce_challenge(code_verifier)
    state = secrets.token_urlsafe(16)
    query = urlencode(
        {
            "client_id": OWNER_CLIENT_ID,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "redirect_uri": OWNER_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(OWNER_SCOPE),
            "state": state,
        }
    )
    return TeslaOAuthSession(
        authorization_url=f"{TESLA_AUTH_BASE_URL}/oauth2/v3/authorize?{query}",
        code_verifier=code_verifier,
        state=state,
    )


def exchange_authorization_response(
    email: str,
    callback_url: str,
    code_verifier: str,
    expected_state: str,
    *,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    """Exchange Tesla's OAuth callback URL for a cache dict.

    Example:
        Input callback URL:
            https://auth.tesla.com/void/callback?code=abc&state=xyz
        Output cache shape:
            {"user@example.com": {"url": "https://auth.tesla.com/",
             "sso": {"access_token": "...", "refresh_token": "...",
             "expires_at": 1770000000}}}
    """

    code = _extract_callback_code(callback_url, expected_state)
    with _build_http_client(TESLA_AUTH_BASE_URL, transport=transport) as client:
        token = _post_token(
            client,
            {
                "grant_type": "authorization_code",
                "client_id": OWNER_CLIENT_ID,
                "code": code,
                "code_verifier": code_verifier,
                "redirect_uri": OWNER_REDIRECT_URI,
            },
            context="OAuth token exchange",
        )
    return _cache_from_token(email, token)


class TeslaOwnerApiClient:
    """Small synchronous Owner API client used from Home Assistant executors."""

    def __init__(
        self,
        email: str,
        cache_file: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not email:
            raise TeslaOwnerAuthError(
                "Tesla E-Mail fehlt. Bitte die Integration neu einrichten.",
                context="email",
            )
        if not cache_file:
            raise TeslaOwnerAuthError(
                "Tesla Token-Cache-Pfad fehlt. Bitte Home Assistant neu starten "
                "oder die Integration neu einrichten.",
                context="cache_file",
            )

        self.email = email
        self.cache_file = cache_file
        self._transport = transport
        self._client: httpx.Client | None = None

    def __enter__(self) -> "TeslaOwnerApiClient":
        self._client = _build_http_client(
            TESLA_OWNER_BASE_URL,
            transport=self._transport,
        )
        return self

    def __exit__(self, *_exc_info: object) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def vehicle_list(self) -> list[dict[str, Any]]:
        """Return Tesla vehicles from the account product list."""

        response = self._request("GET", "api/1/products", context="vehicle list")
        products = response.get("response")
        if not isinstance(products, list):
            raise TeslaOwnerApiError(
                "Tesla lieferte keine gueltige Produktliste. Bitte Debug-Log "
                "aktivieren und pruefen, ob Tesla eine API-Aenderung meldet.",
                context="api/1/products",
            )
        return [product for product in products if "vehicle_id" in product]

    def vehicle_summary(self, vehicle_id: str) -> dict[str, Any]:
        """Return the current summary for one vehicle."""

        response = self._request(
            "GET",
            f"api/1/vehicles/{vehicle_id}",
            context="vehicle summary",
        )
        vehicle = response.get("response")
        if not isinstance(vehicle, dict):
            raise TeslaOwnerApiError(
                "Tesla lieferte keine gueltige Fahrzeug-Zusammenfassung.",
                context=f"vehicle_id={vehicle_id}",
            )
        return vehicle

    def wake_up(self, vehicle_id: str) -> dict[str, Any]:
        """Ask Tesla to wake the vehicle and return the wake response."""

        return self._request(
            "POST",
            WAKE_UP_PATH.format(vehicle_id=vehicle_id),
            context="wake up",
        )

    def get_vehicle_data(self, vehicle_id: str) -> dict[str, Any]:
        """Return full vehicle data in the shape expected by HA entities."""

        response = self._request(
            "GET",
            f"api/1/vehicles/{vehicle_id}/vehicle_data",
            params={"endpoints": VEHICLE_DATA_ENDPOINTS},
            context="vehicle data",
        )
        data = response.get("response")
        if not isinstance(data, dict):
            raise TeslaOwnerApiError(
                "Tesla lieferte keine gueltigen Fahrzeugdaten.",
                context=f"vehicle_id={vehicle_id}",
            )
        return data

    def command(self, vehicle_id: str, command: str, **kwargs: Any) -> dict[str, Any]:
        """Send a legacy Owner API command to the selected vehicle."""

        command_key = COMMAND_ALIASES.get(command, command)
        command_path = COMMAND_PATHS.get(command_key)
        if command_path is None:
            raise TeslaOwnerApiError(
                f"Unbekannter Tesla-Befehl '{command}'. Bitte Command-Mapping "
                "in tesla_owner.py ergaenzen.",
                context=command,
            )

        return self._request(
            "POST",
            f"api/1/vehicles/{vehicle_id}/command/{command_path}",
            json_body=kwargs,
            context=f"command {command}",
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        context: str,
    ) -> dict[str, Any]:
        client = self._ensure_client()
        token = self._access_token()
        headers = {"Authorization": f"Bearer {token}"}

        try:
            response = client.request(
                method,
                path,
                headers=headers,
                params=_without_none(params),
                json=_without_none(json_body),
            )
        except httpx.TimeoutException as err:
            raise TeslaOwnerApiError(
                "Zeitueberschreitung beim Tesla-Zugriff. Pruefe Netzwerk, DNS "
                "und ob Home Assistant ausgehend HTTPS erreichen kann.",
                context=context,
            ) from err
        except httpx.HTTPError as err:
            raise TeslaOwnerApiError(
                f"Tesla-Zugriff fehlgeschlagen: {err}. Pruefe Netzwerk, Proxy "
                "und Home-Assistant-Logs.",
                context=context,
            ) from err

        _LOGGER.debug(
            "Tesla request %s %s -> %s over %s",
            method,
            path,
            response.status_code,
            response.http_version,
        )
        if response.status_code >= 400:
            raise _api_error_from_response(response, context)

        return _json_response(response, context)

    def _ensure_client(self) -> httpx.Client:
        if self._client is None:
            self._client = _build_http_client(
                TESLA_OWNER_BASE_URL,
                transport=self._transport,
            )
        return self._client

    def _access_token(self) -> str:
        token = self._cached_token()
        if _token_needs_refresh(token):
            token = self._refresh_token(token)

        access_token = token.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise TeslaOwnerAuthError(
                "Tesla Access Token fehlt im Cache. Bitte die Integration neu "
                "authentifizieren.",
                context=self.cache_file,
            )
        return access_token

    def _cached_token(self) -> dict[str, Any]:
        cache = _load_cache(self.cache_file)
        account = cache.get(self.email)
        if not isinstance(account, dict):
            raise TeslaOwnerAuthError(
                "Kein Tesla Token fuer dieses Konto gefunden. Bitte die "
                "Integration neu einrichten.",
                context=self.cache_file,
            )
        token = account.get("sso")
        if not isinstance(token, dict):
            raise TeslaOwnerAuthError(
                "Tesla Token-Cache ist unvollstaendig. Bitte die Integration "
                "neu einrichten.",
                context=self.cache_file,
            )
        return token

    def _refresh_token(self, token: dict[str, Any]) -> dict[str, Any]:
        refresh_token = token.get("refresh_token")
        if not isinstance(refresh_token, str) or not refresh_token:
            raise TeslaOwnerAuthError(
                "Tesla Refresh Token fehlt. Bitte die Integration neu "
                "authentifizieren.",
                context=self.cache_file,
            )

        with _build_http_client(
            TESLA_AUTH_BASE_URL,
            transport=self._transport,
        ) as client:
            refreshed = _post_token(
                client,
                {
                    "grant_type": "refresh_token",
                    "client_id": OWNER_CLIENT_ID,
                    "refresh_token": refresh_token,
                    "scope": " ".join(OWNER_SCOPE),
                },
                context="OAuth token refresh",
            )

        merged = {**token, **refreshed}
        if "refresh_token" not in refreshed:
            merged["refresh_token"] = refresh_token
        _store_token(self.cache_file, self.email, merged)
        return merged


def _new_pkce_verifier() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("ascii")


def _pkce_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _extract_callback_code(callback_url: str, expected_state: str) -> str:
    if not callback_url:
        raise TeslaOwnerAuthError(
            "Callback-URL fehlt. Kopiere die komplette URL nach dem Tesla-Login.",
            context="callback_url",
        )

    parsed = urlparse(callback_url.strip())
    query = parse_qs(parsed.query)
    if "error" in query:
        reason = query.get("error_description", query["error"])[0]
        raise TeslaOwnerAuthError(
            f"Tesla hat die Anmeldung abgelehnt: {reason}. Starte den Config "
            "Flow erneut und verwende den neuen Login-Link.",
            context="oauth_error",
        )

    state = query.get("state", [""])[0]
    if state != expected_state:
        raise TeslaOwnerAuthError(
            "OAuth-State passt nicht. Starte den Config Flow erneut; der "
            "Login-Link ist nur fuer diesen Versuch gueltig.",
            context="oauth_state",
        )

    code = query.get("code", [""])[0]
    if not code:
        raise TeslaOwnerAuthError(
            "Callback-URL enthaelt keinen OAuth-Code. Kopiere die komplette "
            "URL aus der Browser-Adresszeile.",
            context="oauth_code",
        )
    return code


def _build_http_client(
    base_url: str,
    *,
    transport: httpx.BaseTransport | None = None,
) -> httpx.Client:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "tesla-ha/1.2",
        "X-Tesla-User-Agent": "TeslaApp/4.10.0",
    }
    return httpx.Client(
        base_url=base_url,
        headers=headers,
        http2=True,
        timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS),
        transport=transport,
        verify=_tls13_context() if transport is None else True,
    )


def _tls13_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    if hasattr(ssl, "TLSVersion") and hasattr(ssl.TLSVersion, "TLSv1_3"):
        context.minimum_version = ssl.TLSVersion.TLSv1_3
    return context


def _post_token(
    client: httpx.Client,
    data: dict[str, str],
    *,
    context: str,
) -> dict[str, Any]:
    try:
        response = client.post(
            "oauth2/v3/token",
            data=data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
    except httpx.TimeoutException as err:
        raise TeslaOwnerAuthError(
            "Zeitueberschreitung beim Tesla-Token-Endpunkt. Pruefe Netzwerk "
            "und DNS von Home Assistant.",
            context=context,
        ) from err
    except httpx.HTTPError as err:
        raise TeslaOwnerAuthError(
            f"Tesla-Authentifizierung konnte nicht erreicht werden: {err}.",
            context=context,
        ) from err

    _LOGGER.debug(
        "Tesla auth request %s -> %s over %s",
        context,
        response.status_code,
        response.http_version,
    )
    if response.status_code >= 400:
        raise _api_error_from_response(response, context, auth=True)

    token = _json_response(response, context)
    return _token_with_expiry(token)


def _token_with_expiry(token: dict[str, Any]) -> dict[str, Any]:
    expires_in = token.get("expires_in")
    if isinstance(expires_in, (int, float)):
        token["expires_at"] = int(time.time() + expires_in)
    return token


def _cache_from_token(email: str, token: dict[str, Any]) -> dict[str, Any]:
    return {email: {"url": f"{TESLA_AUTH_BASE_URL}/", "sso": token}}


def _load_cache(cache_file: str) -> dict[str, Any]:
    if not os.path.exists(cache_file):
        raise TeslaOwnerAuthError(
            "Tesla Token-Cache existiert nicht. Bitte die Integration neu "
            "authentifizieren.",
            context=cache_file,
        )
    try:
        with open(cache_file, encoding="utf-8") as file:
            cache = json.load(file)
    except OSError as err:
        raise TeslaOwnerAuthError(
            f"Tesla Token-Cache konnte nicht gelesen werden: {cache_file}. "
            "Pruefe Dateirechte und Home-Assistant-Storage.",
            context=cache_file,
        ) from err
    except json.JSONDecodeError as err:
        raise TeslaOwnerAuthError(
            f"Tesla Token-Cache ist kein gueltiges JSON: {cache_file}. "
            "Bitte Integration neu einrichten.",
            context=cache_file,
        ) from err

    if not isinstance(cache, dict):
        raise TeslaOwnerAuthError(
            "Tesla Token-Cache hat ein unerwartetes Format. Bitte die "
            "Integration neu einrichten.",
            context=cache_file,
        )
    return cache


def _store_token(cache_file: str, email: str, token: dict[str, Any]) -> None:
    cache = _load_cache(cache_file)
    cache[email] = {"url": f"{TESLA_AUTH_BASE_URL}/", "sso": token}
    directory = os.path.dirname(cache_file)
    if directory:
        os.makedirs(directory, exist_ok=True)
    try:
        with open(cache_file, "w", encoding="utf-8") as file:
            json.dump(cache, file)
    except OSError as err:
        raise TeslaOwnerAuthError(
            f"Tesla Token-Cache konnte nicht geschrieben werden: {cache_file}. "
            "Pruefe Dateirechte und freien Speicher.",
            context=cache_file,
        ) from err


def _token_needs_refresh(token: dict[str, Any]) -> bool:
    expires_at = token.get("expires_at")
    if not isinstance(expires_at, (int, float)):
        return True
    return expires_at <= time.time() + TOKEN_REFRESH_MARGIN_SECONDS


def _json_response(response: httpx.Response, context: str) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as err:
        raise TeslaOwnerApiError(
            "Tesla lieferte keine JSON-Antwort. Pruefe Debug-Logs auf Status "
            "und HTTP-Version.",
            status_code=response.status_code,
            context=context,
        ) from err
    if not isinstance(data, dict):
        raise TeslaOwnerApiError(
            "Tesla JSON-Antwort hat ein unerwartetes Format.",
            status_code=response.status_code,
            context=context,
        )
    return data


def _api_error_from_response(
    response: httpx.Response,
    context: str,
    *,
    auth: bool = False,
) -> TeslaOwnerApiError:
    data = _safe_error_data(response)
    raw_message = _extract_error_message(data) or response.reason_phrase
    lowered = raw_message.lower()

    if "vehicle command protocol required" in lowered:
        return TeslaOwnerApiError(
            "Tesla hat den Befehl abgelehnt: Dieses Fahrzeug verlangt "
            "signierte Commands ueber das Tesla Vehicle Command Protocol. "
            "Richte eine Fleet-API/Virtual-Key-Loesung ein oder nutze die "
            "offizielle Home-Assistant-Tesla-Fleet-Integration fuer Befehle.",
            status_code=response.status_code,
            context=context,
        )

    if response.status_code == 403 and "fleet-api" in lowered:
        return TeslaOwnerApiError(
            "Tesla blockiert den Legacy Owner API Zugriff und verweist auf die "
            "Fleet API. Diese Integration nutzt bereits HTTP/2 und TLS 1.3; "
            "wenn der Fehler bleibt, ist dieser Account oder Endpunkt nicht "
            "mehr ueber die Owner API nutzbar. Wechsle auf Tesla Fleet mit "
            "Developer-App, Scopes und Virtual Key.",
            status_code=response.status_code,
            context=context,
        )

    if response.status_code in (401, 403) and auth:
        return TeslaOwnerAuthError(
            "Tesla hat den Token-Request abgelehnt. Bitte die Integration neu "
            "authentifizieren; bestehende Refresh Tokens koennen durch neue "
            "Logins ungueltig geworden sein.",
            status_code=response.status_code,
            context=context,
        )

    if response.status_code == 401:
        return TeslaOwnerAuthError(
            "Tesla Access Token ist abgelaufen oder widerrufen. Bitte die "
            "Integration neu authentifizieren.",
            status_code=response.status_code,
            context=context,
        )

    if response.status_code == 429:
        return TeslaOwnerApiError(
            "Tesla Rate Limit erreicht. Erhoehe das Update-Intervall und "
            "vermeide haeufiges Wake-up oder viele Automationen.",
            status_code=response.status_code,
            context=context,
        )

    return TeslaOwnerApiError(
        f"Tesla API Fehler {response.status_code}: {raw_message}. Pruefe "
        "Home-Assistant-Debug-Logs und Tesla API Status.",
        status_code=response.status_code,
        context=context,
    )


def _safe_error_data(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_error_message(data: dict[str, Any]) -> str:
    values = [
        data.get("error"),
        data.get("error_description"),
        data.get("message"),
        data.get("reason"),
    ]
    response = data.get("response")
    if isinstance(response, dict):
        values.extend([response.get("reason"), response.get("error")])
    return ". ".join(str(value).strip(".") for value in values if value)


def _without_none(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if data is None:
        return None
    return {key: value for key, value in data.items() if value is not None}
