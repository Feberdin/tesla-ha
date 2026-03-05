from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeslaDataCoordinator

CHARGING_AMPS_MIN = 5
CHARGING_AMPS_MAX = 10


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TeslaDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TeslaChargeLimitNumber(coordinator, entry),
        TeslaChargingAmpsNumber(coordinator, entry),
    ])


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
        self._attr_unique_id = f"{entry.entry_id}_charge_limit"
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
        await self.coordinator.async_command("SET_CHARGE_LIMIT", percent=int(value))


class TeslaChargingAmpsNumber(CoordinatorEntity[TeslaDataCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Ladestrom"
    _attr_icon = "mdi:current-ac"
    _attr_native_min_value = CHARGING_AMPS_MIN
    _attr_native_max_value = CHARGING_AMPS_MAX
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: TeslaDataCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_charging_amps"
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
    def native_max_value(self) -> float:
        if self.coordinator.data:
            vehicle_max = float(
                self.coordinator.data.get("charge_state", {}).get(
                    "charge_current_request_max", CHARGING_AMPS_MAX
                )
            )
            return min(vehicle_max, float(CHARGING_AMPS_MAX))
        return float(CHARGING_AMPS_MAX)

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("charge_state", {}).get("charge_current_request")

    async def async_set_native_value(self, value: float) -> None:
        if value < CHARGING_AMPS_MIN or value > CHARGING_AMPS_MAX:
            raise ValueError(
                f"Ladestrom muss zwischen {CHARGING_AMPS_MIN}A und {CHARGING_AMPS_MAX}A liegen."
            )
        await self.coordinator.async_command("CHARGING_AMPS", charging_amps=int(value))
