from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeslaDataCoordinator


@dataclass(frozen=True, kw_only=True)
class TeslaBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict], bool | None] | None = None


BINARY_SENSOR_TYPES: tuple[TeslaBinarySensorDescription, ...] = (
    TeslaBinarySensorDescription(
        key="charging",
        name="Lädt",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda d: d.get("charge_state", {}).get("charging_state") == "Charging",
    ),
    TeslaBinarySensorDescription(
        key="locked",
        name="Verriegelt",
        device_class=BinarySensorDeviceClass.LOCK,
        # BinarySensorDeviceClass.LOCK: on = unlocked, off = locked
        value_fn=lambda d: not d.get("vehicle_state", {}).get("locked", True),
    ),
    TeslaBinarySensorDescription(
        key="climate_on",
        name="Klimaanlage",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.get("climate_state", {}).get("is_climate_on"),
    ),
    TeslaBinarySensorDescription(
        key="sentry_mode",
        name="Sentry Mode",
        icon="mdi:shield-car",
        value_fn=lambda d: d.get("vehicle_state", {}).get("sentry_mode"),
    ),
    TeslaBinarySensorDescription(
        key="cable_connected",
        name="Kabel angesteckt",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda d: d.get("charge_state", {}).get("conn_charge_cable")
        not in ("<invalid>", None, ""),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TeslaDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TeslaBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSOR_TYPES
    )


class TeslaBinarySensor(CoordinatorEntity[TeslaDataCoordinator], BinarySensorEntity):
    entity_description: TeslaBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeslaDataCoordinator,
        description: TeslaBinarySensorDescription,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
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
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        if self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
