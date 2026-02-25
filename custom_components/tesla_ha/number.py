from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
    async_add_entities([TeslaChargeLimitNumber(coordinator, entry)])


class TeslaChargeLimitNumber(CoordinatorEntity[TeslaDataCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Ladelimit"
    _attr_icon = "mdi:battery-lock"
    _attr_native_min_value = 50
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: TeslaDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_charge_limit_number"
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
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("charge_state", {}).get("charge_limit_soc")

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_command(
            "SET_CHARGE_LIMIT", percent=int(value)
        )
