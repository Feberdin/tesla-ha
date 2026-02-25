from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeslaDataCoordinator


@dataclass(frozen=True, kw_only=True)
class TeslaSwitchDescription(SwitchEntityDescription):
    is_on_fn: Callable[[dict], bool | None] = lambda _: None
    turn_on_command: str = ""
    turn_on_kwargs: dict = None
    turn_off_command: str = ""
    turn_off_kwargs: dict = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "turn_on_kwargs", self.turn_on_kwargs or {})
        object.__setattr__(self, "turn_off_kwargs", self.turn_off_kwargs or {})


SWITCH_TYPES: tuple[TeslaSwitchDescription, ...] = (
    TeslaSwitchDescription(
        key="sentry_mode",
        name="Sentry Mode",
        icon="mdi:shield-car",
        is_on_fn=lambda d: d.get("vehicle_state", {}).get("sentry_mode"),
        turn_on_command="SET_SENTRY_MODE",
        turn_on_kwargs={"on": True},
        turn_off_command="SET_SENTRY_MODE",
        turn_off_kwargs={"on": False},
    ),
    TeslaSwitchDescription(
        key="charging",
        name="Laden",
        icon="mdi:ev-station",
        is_on_fn=lambda d: d.get("charge_state", {}).get("charging_state") == "Charging",
        turn_on_command="START_CHARGE",
        turn_off_command="STOP_CHARGE",
    ),
    TeslaSwitchDescription(
        key="steering_wheel_heater",
        name="Lenkradheizung",
        icon="mdi:steering",
        is_on_fn=lambda d: d.get("climate_state", {}).get("steering_wheel_heater"),
        turn_on_command="REMOTE_STEERING_WHEEL_HEATER_REQUEST",
        turn_on_kwargs={"on": True},
        turn_off_command="REMOTE_STEERING_WHEEL_HEATER_REQUEST",
        turn_off_kwargs={"on": False},
    ),
    TeslaSwitchDescription(
        key="max_defrost",
        name="Maximal-Heizung",
        icon="mdi:car-defrost-front",
        is_on_fn=lambda d: d.get("climate_state", {}).get("defrost_mode", 0) != 0,
        turn_on_command="MAX_DEFROST",
        turn_on_kwargs={"on": True},
        turn_off_command="MAX_DEFROST",
        turn_off_kwargs={"on": False},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TeslaDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TeslaSwitch(coordinator, description, entry)
        for description in SWITCH_TYPES
    )


class TeslaSwitch(CoordinatorEntity[TeslaDataCoordinator], SwitchEntity):
    entity_description: TeslaSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeslaDataCoordinator,
        description: TeslaSwitchDescription,
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
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_command(
            self.entity_description.turn_on_command,
            **self.entity_description.turn_on_kwargs,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_command(
            self.entity_description.turn_off_command,
            **self.entity_description.turn_off_kwargs,
        )
