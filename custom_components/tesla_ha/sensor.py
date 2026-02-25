from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfLength,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeslaDataCoordinator


@dataclass(frozen=True, kw_only=True)
class TeslaSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any] | None = None


SENSOR_TYPES: tuple[TeslaSensorDescription, ...] = (
    TeslaSensorDescription(
        key="battery_level",
        name="Ladestand",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("charge_state", {}).get("battery_level"),
    ),
    TeslaSensorDescription(
        key="battery_range",
        name="Reichweite",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: round(
            (d.get("charge_state", {}).get("battery_range") or 0) * 1.60934, 1
        ),
    ),
    TeslaSensorDescription(
        key="charge_limit",
        name="Ladelimit",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-lock",
        value_fn=lambda d: d.get("charge_state", {}).get("charge_limit_soc"),
    ),
    TeslaSensorDescription(
        key="charging_state",
        name="Ladezustand",
        icon="mdi:ev-station",
        value_fn=lambda d: d.get("charge_state", {}).get("charging_state"),
    ),
    TeslaSensorDescription(
        key="charger_power",
        name="Ladeleistung",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("charge_state", {}).get("charger_power"),
    ),
    TeslaSensorDescription(
        key="charger_voltage",
        name="Ladespannung",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("charge_state", {}).get("charger_voltage"),
    ),
    TeslaSensorDescription(
        key="charger_current",
        name="Ladestrom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("charge_state", {}).get("charger_actual_current"),
    ),
    TeslaSensorDescription(
        key="energy_added",
        name="Energie geladen",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda d: d.get("charge_state", {}).get("charge_energy_added"),
    ),
    TeslaSensorDescription(
        key="odometer",
        name="Kilometerstand",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        value_fn=lambda d: round(
            (d.get("vehicle_state", {}).get("odometer") or 0) * 1.60934, 0
        ),
    ),
    TeslaSensorDescription(
        key="inside_temp",
        name="Innentemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("climate_state", {}).get("inside_temp"),
    ),
    TeslaSensorDescription(
        key="outside_temp",
        name="Außentemperatur",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("climate_state", {}).get("outside_temp"),
    ),
    TeslaSensorDescription(
        key="software_version",
        name="Software Version",
        icon="mdi:update",
        value_fn=lambda d: d.get("vehicle_state", {}).get("car_version"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TeslaDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TeslaSensor(coordinator, description, entry)
        for description in SENSOR_TYPES
    )


class TeslaSensor(CoordinatorEntity[TeslaDataCoordinator], SensorEntity):
    entity_description: TeslaSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeslaDataCoordinator,
        description: TeslaSensorDescription,
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
    def native_value(self) -> Any:
        if self.coordinator.data is None:
            return None
        if self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
