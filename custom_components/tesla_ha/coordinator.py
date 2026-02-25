from __future__ import annotations

import asyncio
import functools
import logging
import time
from datetime import timedelta
from typing import Any

import teslapy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, TESLA_MODELS, UPDATE_INTERVAL

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
        with teslapy.Tesla(self.email, cache_file=self.cache_file) as tesla:
            if not tesla.authorized:
                raise UpdateFailed("Tesla ist nicht authentifiziert")

            vehicles = tesla.vehicle_list()
            if not vehicles:
                raise UpdateFailed("Keine Fahrzeuge gefunden")

            vehicle = vehicles[0]

            if vehicle.get("state") != "online":
                _LOGGER.debug("Fahrzeug schläft, wecke auf...")
                for attempt in range(12):
                    try:
                        resp = vehicle.api("WAKE_UP")
                        if resp["response"]["state"] == "online":
                            _LOGGER.debug("Fahrzeug aufgewacht")
                            break
                    except Exception as e:
                        _LOGGER.debug("Wake-up Versuch %d: %s", attempt + 1, e)
                    time.sleep(10)
                else:
                    raise UpdateFailed("Fahrzeug konnte nicht aufgeweckt werden")

            data = vehicle.get_vehicle_data()

            if self.vin is None:
                self.vin = vehicle.get("vin")
                self.model = _model_from_vin(self.vin)
                self.has_seat_cooling = data.get("vehicle_config", {}).get("has_seat_cooling", False)

            return data

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except UpdateFailed:
            raise
        except Exception as e:
            raise UpdateFailed(f"Fehler beim Datenabruf: {e}") from e

    def _execute_command(self, command: str, **kwargs: Any) -> dict:
        with teslapy.Tesla(self.email, cache_file=self.cache_file) as tesla:
            if not tesla.authorized:
                raise Exception("Tesla nicht authentifiziert")
            vehicles = tesla.vehicle_list()
            if not vehicles:
                raise Exception("Kein Fahrzeug gefunden")
            vehicle = vehicles[0]
            if vehicle.get("state") != "online":
                _LOGGER.debug("Wecke Fahrzeug für Befehl '%s'...", command)
                for attempt in range(12):
                    try:
                        resp = vehicle.api("WAKE_UP")
                        if resp["response"]["state"] == "online":
                            break
                    except Exception as e:
                        _LOGGER.debug("Wake-up Versuch %d: %s", attempt + 1, e)
                    time.sleep(10)
            return vehicle.api(command, **kwargs)

    async def async_command(self, command: str, **kwargs: Any) -> dict:
        result = await self.hass.async_add_executor_job(
            functools.partial(self._execute_command, command, **kwargs)
        )
        # Wait 3 seconds so the vehicle can process the command before we refresh
        await asyncio.sleep(3)
        await self.async_request_refresh()
        return result
