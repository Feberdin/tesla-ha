from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeslaDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TeslaDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TeslaClimate(coordinator, entry)])


class TeslaClimate(CoordinatorEntity[TeslaDataCoordinator], ClimateEntity):
    _attr_has_entity_name = True
    _attr_name = "Standheizung"
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT_COOL]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 15.0
    _attr_max_temp = 28.0
    _attr_target_temperature_step = 0.5
    _attr_icon = "mdi:car-seat-heater"

    def __init__(self, coordinator: TeslaDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Tesla {self.coordinator.model}",
            manufacturer="Tesla",
            model=self.coordinator.model,
            serial_number=self.coordinator.vin,
        )

    @property
    def hvac_mode(self) -> HVACMode | None:
        if self.coordinator.data is None:
            return None
        is_on = self.coordinator.data.get("climate_state", {}).get("is_climate_on", False)
        return HVACMode.HEAT_COOL if is_on else HVACMode.OFF

    @property
    def current_temperature(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("climate_state", {}).get("inside_temp")

    @property
    def target_temperature(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("climate_state", {}).get("driver_temp_setting")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.HEAT_COOL:
            await self.coordinator.async_command("CLIMATE_ON")
        else:
            await self.coordinator.async_command("CLIMATE_OFF")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            await self.coordinator.async_command(
                "CHANGE_CLIMATE_TEMPERATURE_SETTING",
                driver_temp=temp,
                passenger_temp=temp,
            )
