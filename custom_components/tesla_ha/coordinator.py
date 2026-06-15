"""Data coordinator for Tesla vehicle state and commands.

Purpose:
    Centralizes Tesla cloud polling, wake-up handling and vehicle commands for
    all Home Assistant entities in this integration.

Input / Output:
    Inputs are a Tesla account email and Home Assistant's private token cache
    file. Outputs are vehicle data dictionaries consumed by sensors, switches,
    climate, lock, buttons, numbers and selects.

Important invariants:
    External Tesla calls always run inside Home Assistant executor jobs because
    the client is synchronous. The coordinator only uses the first vehicle in
    the Tesla account, matching the existing integration behavior.

Debugging:
    Enable debug logging for `custom_components.tesla_ha`. Logs show wake-up
    attempts, command names and safe request metadata, never token values.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, TESLA_MODELS, UPDATE_INTERVAL
from .tesla_owner import TeslaOwnerApiClient, TeslaOwnerApiError

_LOGGER = logging.getLogger(__name__)


def _model_from_vin(vin: str | None) -> str:
    if vin and len(vin) >= 4:
        return TESLA_MODELS.get(vin[3], "Tesla")
    return "Tesla"


class TeslaDataCoordinator(DataUpdateCoordinator):
    def __init__(
        self, hass: HomeAssistant, email: str, cache_file: str
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL),
        )
        self.email = email
        self.cache_file = cache_file
        self.vin: str | None = None
        self.model: str = "Tesla"
        self.has_seat_cooling: bool = False

    def _fetch_data(self) -> dict:
        with TeslaOwnerApiClient(self.email, self.cache_file) as tesla:
            vehicles = tesla.vehicle_list()
            if not vehicles:
                raise UpdateFailed("Keine Fahrzeuge gefunden")

            vehicle = vehicles[0]
            vehicle_id = _vehicle_id(vehicle)

            if vehicle.get("state") != "online":
                _LOGGER.debug("Fahrzeug schläft, wecke auf...")
                self._wake_vehicle(tesla, vehicle_id)

            data = tesla.get_vehicle_data(vehicle_id)

            if self.vin is None:
                self.vin = data.get("vin") or vehicle.get("vin")
                self.model = _model_from_vin(self.vin)
                self.has_seat_cooling = data.get("vehicle_config", {}).get("has_seat_cooling", False)

            return data

    def _wake_vehicle(self, tesla: TeslaOwnerApiClient, vehicle_id: str) -> None:
        for attempt in range(12):
            try:
                response = tesla.wake_up(vehicle_id)
                wake_response = response.get("response", {})
                if wake_response.get("state") == "online":
                    _LOGGER.debug("Fahrzeug aufgewacht")
                    return
            except TeslaOwnerApiError as err:
                _LOGGER.debug("Wake-up Versuch %d fehlgeschlagen: %s", attempt + 1, err)
            time.sleep(10)
        raise UpdateFailed("Fahrzeug konnte nicht aufgeweckt werden")

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except UpdateFailed:
            raise
        except TeslaOwnerApiError as e:
            raise UpdateFailed(str(e)) from e
        except Exception as e:
            raise UpdateFailed(f"Fehler beim Datenabruf: {e}") from e

    def _execute_command(self, command: str, **kwargs: Any) -> dict:
        with TeslaOwnerApiClient(self.email, self.cache_file) as tesla:
            vehicles = tesla.vehicle_list()
            if not vehicles:
                raise Exception("Kein Fahrzeug gefunden")
            vehicle = vehicles[0]
            vehicle_id = _vehicle_id(vehicle)
            if vehicle.get("state") != "online":
                _LOGGER.debug("Wecke Fahrzeug für Befehl '%s'...", command)
                self._wake_vehicle(tesla, vehicle_id)
            return tesla.command(vehicle_id, command, **kwargs)

    async def async_command(self, command: str, **kwargs: Any) -> dict:
        try:
            result = await self.hass.async_add_executor_job(
                functools.partial(self._execute_command, command, **kwargs)
            )
        except TeslaOwnerApiError as err:
            raise HomeAssistantError(str(err)) from err
        # Wait 3 seconds so the vehicle can process the command before we refresh
        await asyncio.sleep(3)
        await self.async_request_refresh()
        return result


def _vehicle_id(vehicle: dict[str, Any]) -> str:
    vehicle_id = vehicle.get("id_s") or vehicle.get("vehicle_id") or vehicle.get("id")
    if vehicle_id is None:
        raise UpdateFailed(
            "Tesla Fahrzeug hat keine nutzbare ID. Bitte Debug-Log aktivieren "
            "und Produktliste pruefen."
        )
    return str(vehicle_id)
