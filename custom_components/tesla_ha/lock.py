from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
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
    async_add_entities([TeslaLock(coordinator, entry)])


class TeslaLock(CoordinatorEntity[TeslaDataCoordinator], LockEntity):
    _attr_has_entity_name = True
    _attr_name = "Türschloss"
    _attr_icon = "mdi:car-door-lock"

    def __init__(self, coordinator: TeslaDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_lock"
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
    def is_locked(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("vehicle_state", {}).get("locked", True)

    async def async_lock(self, **kwargs: Any) -> None:
        await self.coordinator.async_command("LOCK")

    async def async_unlock(self, **kwargs: Any) -> None:
        await self.coordinator.async_command("UNLOCK")
