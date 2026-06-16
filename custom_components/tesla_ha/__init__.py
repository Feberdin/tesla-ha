"""Home Assistant setup for the Tesla Fleet based integration.

Purpose:
    Creates the official Tesla Fleet API connection after OAuth and wires the
    existing entity platforms to a single vehicle coordinator.

Input / Output:
    Input is a Home Assistant config entry created by the Fleet OAuth config
    flow. Output is `hass.data[DOMAIN][entry_id]`, containing a
    `TeslaDataCoordinator` used by sensors, binary sensors, controls and
    selects.

Important invariants:
    Legacy Owner API token caches are not migrated. Tesla now blocks that path
    for affected accounts, so old config entries must be recreated through
    Fleet OAuth. The generated Fleet private key stays local in Home
    Assistant's config directory and is never logged.

Debugging:
    If setup fails before entities appear, check whether the config entry has
    OAuth token data and whether the Tesla Developer App granted
    `vehicle_device_data`. If commands fail later, check Virtual Key pairing
    and command scopes.
"""

from __future__ import annotations

import logging
from typing import Any

import jwt
from tesla_fleet_api import TeslaFleetApi, is_valid_region
from tesla_fleet_api.const import Scope
from tesla_fleet_api.exceptions import (
    InvalidRegion,
    InvalidToken,
    LibraryError,
    LoginRequired,
    OAuthExpired,
    TeslaFleetError,
)
from tesla_fleet_api.tesla import VehicleFleet

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    OAuth2TokenRequestError,
    OAuth2TokenRequestReauthError,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
    OAuth2Session,
    async_get_config_entry_implementation,
)

from .const import DOMAIN, PLATFORMS
from .coordinator import TeslaDataCoordinator
from .tesla_fleet import (
    CONF_FLEET_DOMAIN,
    FLEET_PRIVATE_KEY_FILE,
    vehicle_id_from_product,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one Tesla Fleet config entry."""

    if CONF_TOKEN not in entry.data:
        raise ConfigEntryAuthFailed(
            "Diese Tesla-Integration nutzt noch den alten Owner-API-Cache. "
            "Bitte die Integration entfernen und mit Tesla Fleet OAuth neu "
            "einrichten."
        )

    oauth_session = await _async_oauth_session(hass, entry)
    access_token = oauth_session.token[CONF_ACCESS_TOKEN]
    token_payload = jwt.decode(access_token, options={"verify_signature": False})
    scopes = _scopes_from_token(token_payload)

    if Scope.VEHICLE_DEVICE_DATA not in scopes:
        raise ConfigEntryAuthFailed(
            "Tesla Fleet OAuth hat keinen Zugriff auf Fahrzeugdaten gewaehlt. "
            "Bitte die Integration neu authentifizieren und den Scope "
            "`vehicle_device_data` erlauben."
        )

    async def _async_get_access_token() -> str:
        await oauth_session.async_ensure_token_valid()
        return oauth_session.token[CONF_ACCESS_TOKEN]

    session = async_get_clientsession(hass)
    region_code = str(token_payload.get("ou_code", "")).lower()
    region = region_code if is_valid_region(region_code) else None
    tesla = TeslaFleetApi(
        session=session,
        access_token=_async_get_access_token,
        region=region,
        charging_scope=False,
        partner_scope=False,
        energy_scope=False,
        vehicle_scope=True,
    )

    products = await _async_get_products(tesla)
    vehicle_products = [product for product in products if "vin" in product]
    if not vehicle_products:
        raise ConfigEntryNotReady("Keine Fahrzeuge im Tesla Fleet Konto gefunden.")

    product = vehicle_products[0]
    vin = vehicle_id_from_product(product)
    vehicle_api = await _async_vehicle_api(hass, tesla, product)

    coordinator = TeslaDataCoordinator(
        hass=hass,
        entry=entry,
        vehicle_api=vehicle_api,
        product=product,
        scopes=scopes,
        fleet_domain=entry.data.get(CONF_FLEET_DOMAIN),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        raise
    except TeslaFleetError as err:
        raise ConfigEntryNotReady(f"Tesla Fleet Verbindung fehlgeschlagen: {err.message}") from err
    except Exception as err:
        raise ConfigEntryNotReady(f"Tesla Fleet Setup fehlgeschlagen: {err}") from err

    _LOGGER.info("Tesla Fleet vehicle %s initialized for tesla_ha", vin[-6:])
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one Tesla Fleet config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_oauth_session(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> OAuth2Session:
    """Return a valid Home Assistant OAuth session for this entry."""

    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            "Tesla Fleet Application Credentials sind nicht verfuegbar."
        ) from err
    except ValueError as err:
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, "auth_implementation": None},
        )
        raise ConfigEntryAuthFailed from err

    oauth_session = OAuth2Session(hass, entry, implementation)
    try:
        await oauth_session.async_ensure_token_valid()
    except OAuth2TokenRequestReauthError as err:
        raise ConfigEntryAuthFailed from err
    except OAuth2TokenRequestError as err:
        raise ConfigEntryNotReady from err
    return oauth_session


async def _async_get_products(tesla: TeslaFleetApi) -> list[dict[str, Any]]:
    """Fetch Tesla products and follow the account region when necessary."""

    try:
        return (await tesla.products())["response"]
    except InvalidRegion:
        _LOGGER.warning("Tesla Fleet region is invalid, trying account region")
    except (InvalidToken, OAuthExpired, LoginRequired, OAuth2TokenRequestReauthError) as err:
        raise ConfigEntryAuthFailed from err
    except (TeslaFleetError, OAuth2TokenRequestError) as err:
        raise ConfigEntryNotReady from err

    try:
        await tesla.find_server()
    except (
        InvalidToken,
        OAuthExpired,
        LoginRequired,
        LibraryError,
        OAuth2TokenRequestReauthError,
    ) as err:
        raise ConfigEntryAuthFailed from err
    except (TeslaFleetError, OAuth2TokenRequestError) as err:
        raise ConfigEntryNotReady from err

    try:
        return (await tesla.products())["response"]
    except (InvalidToken, OAuthExpired, LoginRequired, OAuth2TokenRequestReauthError) as err:
        raise ConfigEntryAuthFailed from err
    except (TeslaFleetError, OAuth2TokenRequestError) as err:
        raise ConfigEntryNotReady from err


async def _async_vehicle_api(
    hass: HomeAssistant,
    tesla: TeslaFleetApi,
    product: dict[str, Any],
) -> VehicleFleet:
    """Create the correct vehicle API for signed or unsigned commands."""

    vin = vehicle_id_from_product(product)
    if product.get("command_signing") == "required":
        await tesla.get_private_key(hass.config.path(FLEET_PRIVATE_KEY_FILE))
        return tesla.vehicles.createSigned(vin)
    return tesla.vehicles.createFleet(vin)


def _scopes_from_token(token_payload: dict[str, Any]) -> set[Scope]:
    """Return known Fleet scopes from a decoded JWT payload."""

    scopes: set[Scope] = set()
    raw_scopes = token_payload.get("scp", [])
    if isinstance(raw_scopes, str):
        raw_scopes = raw_scopes.split()
    for raw_scope in raw_scopes:
        try:
            scopes.add(Scope(raw_scope))
        except ValueError:
            _LOGGER.debug("Ignoring unknown Tesla Fleet scope %s", raw_scope)
    return scopes
