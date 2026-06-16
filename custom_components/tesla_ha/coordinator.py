"""Data coordinator for Tesla Fleet vehicle state and commands.

Purpose:
    Polls official Tesla Fleet vehicle endpoints and executes Fleet commands
    while preserving the data shape expected by the existing entity classes.

Input / Output:
    Inputs are a Home Assistant config entry, a Fleet vehicle API object,
    Fleet product metadata and the granted OAuth scopes. Output is a
    normalized vehicle-data dictionary exposed through DataUpdateCoordinator.

Important invariants:
    The coordinator does not auto-wake sleeping vehicles during normal polling;
    Fleet `vehicle_data` calls are billable/cost-sensitive and Tesla recommends
    avoiding aggressive polling. User-triggered commands wake the vehicle first
    because the action is explicit.

Debugging:
    Enable debug logging for `custom_components.tesla_ha`. Logs show vehicle
    state transitions, command names, and Tesla Fleet status classes, but never
    OAuth tokens, client secrets, or full VINs.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from tesla_fleet_api.const import Scope
from tesla_fleet_api.exceptions import (
    Forbidden,
    InvalidToken,
    LoginRequired,
    NotOnWhitelistFault,
    OAuthExpired,
    RateLimited,
    TeslaFleetError,
    TeslaFleetMessageFaultUnknownKeyId,
    VehicleOffline,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, TESLA_MODELS, UPDATE_INTERVAL
from .tesla_fleet import (
    CONF_FLEET_DOMAIN,
    FLEET_VEHICLE_ENDPOINTS,
    build_command,
    command_error_reason,
    command_requires_scope,
    command_success,
    normalize_vehicle_data,
    vehicle_id_from_product,
)

_LOGGER = logging.getLogger(__name__)


def _model_from_vin(vin: str | None) -> str:
    if vin and len(vin) >= 4:
        return TESLA_MODELS.get(vin[3], "Tesla")
    return "Tesla"


class TeslaDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch Tesla Fleet data for the first vehicle in the account."""

    def __init__(
        self,
        *,
        hass: HomeAssistant,
        entry: ConfigEntry,
        vehicle_api: Any,
        product: dict[str, Any],
        scopes: set[Scope],
        fleet_domain: str | None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )
        self.entry = entry
        self.vehicle_api = vehicle_api
        self.product = product
        self.scopes = scopes
        self.fleet_domain = fleet_domain or entry.data.get(CONF_FLEET_DOMAIN)
        self.vin: str | None = product.get("vin")
        self.model: str = _model_from_vin(self.vin)
        self.has_seat_cooling: bool = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch current Fleet vehicle data."""

        try:
            summary = await self.vehicle_api.vehicle()
            product = {**self.product, **_response_dict(summary)}
            state = product.get("state")
            if state != "online":
                _LOGGER.debug("Tesla Fleet vehicle %s is %s", self._safe_vehicle_id(), state)
                return normalize_vehicle_data(product, self.data)

            response = await self.vehicle_api.vehicle_data(
                endpoints=FLEET_VEHICLE_ENDPOINTS
            )
            vehicle_data = _response_dict(response)
            data = normalize_vehicle_data(product, vehicle_data)
            self._update_vehicle_metadata(data)
            return data

        except VehicleOffline:
            _LOGGER.debug("Tesla Fleet vehicle %s is offline/asleep", self._safe_vehicle_id())
            return normalize_vehicle_data(self.product, self.data)
        except RateLimited as err:
            _LOGGER.warning("Tesla Fleet rate limit hit, keeping previous data")
            if self.data:
                return self.data
            raise UpdateFailed(err.message) from err
        except (InvalidToken, OAuthExpired, LoginRequired) as err:
            raise ConfigEntryAuthFailed from err
        except TeslaFleetError as err:
            raise UpdateFailed(_fleet_error_message(err)) from err

    async def async_command(self, command: str, **kwargs: Any) -> dict[str, Any]:
        """Wake the vehicle if needed and execute a Fleet command."""

        self._raise_if_scope_missing(command)
        try:
            await self._async_wake_vehicle()
            result = await build_command(self.vehicle_api, command, kwargs)
        except (NotOnWhitelistFault, TeslaFleetMessageFaultUnknownKeyId) as err:
            raise HomeAssistantError(self._virtual_key_error()) from err
        except Forbidden as err:
            raise HomeAssistantError(
                "Tesla Fleet hat den Befehl abgelehnt. Pruefe im Tesla "
                "Developer Portal, ob die App die benoetigten Command-Scopes "
                "besitzt und der Nutzer diese Scopes erlaubt hat."
            ) from err
        except TeslaFleetError as err:
            raise HomeAssistantError(_fleet_error_message(err)) from err
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

        if not command_success(result):
            raise HomeAssistantError(
                f"Tesla Fleet Befehl '{command}' fehlgeschlagen: "
                f"{command_error_reason(result)}"
            )

        await asyncio.sleep(3)
        await self.async_request_refresh()
        return result

    async def _async_wake_vehicle(self) -> None:
        """Wake the vehicle for an explicit command."""

        for attempt in range(4):
            response = (
                await self.vehicle_api.wake_up()
                if attempt == 0
                else await self.vehicle_api.vehicle()
            )
            state = _response_dict(response).get("state")
            if self.data:
                self.data["state"] = state
            if state == "online":
                return
            await asyncio.sleep((attempt + 1) * 5)

        raise HomeAssistantError(
            "Tesla Fahrzeug konnte nicht aufgeweckt werden. Pruefe, ob Mobile "
            "Access im Fahrzeug aktiviert ist und ob das Fahrzeug erreichbar ist."
        )

    def _raise_if_scope_missing(self, command: str) -> None:
        required_scopes = command_requires_scope(command)
        if any(scope in self.scopes for scope in required_scopes):
            return
        required = " oder ".join(scope.value for scope in required_scopes)
        raise HomeAssistantError(
            f"Tesla Fleet Befehl '{command}' ist nicht erlaubt. Der OAuth-Login "
            f"braucht den Scope {required}."
        )

    def _update_vehicle_metadata(self, data: dict[str, Any]) -> None:
        vin = data.get("vin") or self.product.get("vin")
        self.vin = str(vin) if vin else self.vin
        self.model = _model_from_vin(self.vin)
        self.has_seat_cooling = bool(
            data.get("vehicle_config", {}).get("has_seat_cooling", False)
        )

    def _safe_vehicle_id(self) -> str:
        try:
            vehicle_id = vehicle_id_from_product(self.product)
        except ValueError:
            return "unknown"
        return vehicle_id[-6:]

    def _virtual_key_error(self) -> str:
        if self.fleet_domain:
            return (
                "Tesla hat den signierten Befehl abgelehnt, weil der Virtual "
                "Key nicht im Fahrzeug gekoppelt ist. Oeffne "
                f"https://www.tesla.com/_ak/{self.fleet_domain} und fuege den "
                "Schluessel in der Tesla-App hinzu."
            )
        return (
            "Tesla hat den signierten Befehl abgelehnt, weil der Virtual Key "
            "nicht im Fahrzeug gekoppelt ist. Fuehre den Fleet-Setup-Flow "
            "erneut aus und kopple den angezeigten Virtual Key."
        )


def _response_dict(response: dict[str, Any]) -> dict[str, Any]:
    value = response.get("response")
    return value if isinstance(value, dict) else {}


def _fleet_error_message(err: TeslaFleetError) -> str:
    parts = [err.message]
    if err.status:
        parts.append(f"Status: {err.status}")
    if err.data:
        parts.append(f"Kontext: {str(err.data)[:180]}")
    return "; ".join(parts) if parts else "Tesla Fleet Fehler."
