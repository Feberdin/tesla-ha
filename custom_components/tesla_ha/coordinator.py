from __future__ import annotations

import logging
import time
from datetime import timedelta

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

    def _fetch_data(self) -> dict:
        with teslapy.Tesla(self.email, cache_file=self.cache_file) as tesla:
            if not tesla.authorized:
                raise UpdateFailed("Tesla ist nicht authentifiziert")

            vehicles = tesla.vehicle_list()
            if not vehicles:
                raise UpdateFailed("Keine Fahrzeuge gefunden")

            vehicle = vehicles[0]

            if self.vin is None:
                self.vin = vehicle.get("vin")
                self.model = _model_from_vin(self.vin)

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

            return vehicle.get_vehicle_data()

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except UpdateFailed:
            raise
        except Exception as e:
            raise UpdateFailed(f"Fehler beim Datenabruf: {e}") from e
