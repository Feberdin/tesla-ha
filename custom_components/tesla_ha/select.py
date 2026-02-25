from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeslaDataCoordinator

SEAT_OPTIONS = ["Aus", "Stufe 1", "Stufe 2", "Stufe 3"]
LEVEL_TO_OPTION = {0: "Aus", 1: "Stufe 1", 2: "Stufe 2", 3: "Stufe 3"}
OPTION_TO_LEVEL = {"Aus": 0, "Stufe 1": 1, "Stufe 2": 2, "Stufe 3": 3}


@dataclass
class SeatConfig:
    key: str
    name: str
    state_field: str        # field in climate_state
    command: str
    heater_id: int
    icon: str = "mdi:car-seat-heater"


SEAT_HEATERS = [
    SeatConfig("seat_heater_driver",    "Sitzheizung Fahrer",        "seat_heater_left",      "REMOTE_SEAT_HEATER_REQUEST",  0),
    SeatConfig("seat_heater_passenger", "Sitzheizung Beifahrer",     "seat_heater_right",     "REMOTE_SEAT_HEATER_REQUEST",  1),
    SeatConfig("seat_heater_rl",        "Sitzheizung Fond Links",    "seat_heater_rear_left", "REMOTE_SEAT_HEATER_REQUEST",  2),
    SeatConfig("seat_heater_rr",        "Sitzheizung Fond Rechts",   "seat_heater_rear_right","REMOTE_SEAT_HEATER_REQUEST",  3),
    SeatConfig("seat_cooling_driver",   "Sitzkühlung Fahrer",        "seat_fan_front_left",   "REMOTE_SEAT_COOLING_REQUEST", 0, "mdi:car-seat-cooler"),
    SeatConfig("seat_cooling_passenger","Sitzkühlung Beifahrer",     "seat_fan_front_right",  "REMOTE_SEAT_COOLING_REQUEST", 1, "mdi:car-seat-cooler"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TeslaDataCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[TeslaSeatSelect] = []
    for cfg in SEAT_HEATERS:
        # Only add seat cooling if the vehicle supports it
        if "cooling" in cfg.key and not coordinator.has_seat_cooling:
            continue
        entities.append(TeslaSeatSelect(coordinator, cfg, entry))

    async_add_entities(entities)


class TeslaSeatSelect(CoordinatorEntity[TeslaDataCoordinator], SelectEntity):
    _attr_has_entity_name = True
    _attr_options = SEAT_OPTIONS

    def __init__(
        self,
        coordinator: TeslaDataCoordinator,
        cfg: SeatConfig,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._cfg = cfg
        self._attr_unique_id = f"{entry.entry_id}_{cfg.key}"
        self._attr_name = cfg.name
        self._attr_icon = cfg.icon
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
    def current_option(self) -> str | None:
        if self.coordinator.data is None:
            return None
        level = self.coordinator.data.get("climate_state", {}).get(
            self._cfg.state_field, 0
        )
        return LEVEL_TO_OPTION.get(level, "Aus")

    async def async_select_option(self, option: str) -> None:
        level = OPTION_TO_LEVEL.get(option, 0)
        await self.coordinator.async_command(
            self._cfg.command,
            heater=self._cfg.heater_id,
            level=level,
        )
