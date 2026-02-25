from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TeslaDataCoordinator


@dataclass(frozen=True, kw_only=True)
class TeslaButtonDescription(ButtonEntityDescription):
    command: str = ""
    command_kwargs: dict = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "command_kwargs", self.command_kwargs or {})


BUTTON_TYPES: tuple[TeslaButtonDescription, ...] = (
    # ── Fahrzeug ─────────────────────────────────────────────────────────────
    TeslaButtonDescription(
        key="flash_lights",
        name="Lichter blinken",
        icon="mdi:car-light-high",
        command="FLASH_LIGHTS",
    ),
    TeslaButtonDescription(
        key="honk_horn",
        name="Hupe",
        icon="mdi:bugle",
        command="HONK_HORN",
    ),
    TeslaButtonDescription(
        key="open_frunk",
        name="Frunk öffnen",
        icon="mdi:car-door",
        command="ACTUATE_TRUNK",
        command_kwargs={"which_trunk": "front"},
    ),
    TeslaButtonDescription(
        key="open_trunk",
        name="Kofferraum öffnen",
        icon="mdi:car-back",
        command="ACTUATE_TRUNK",
        command_kwargs={"which_trunk": "rear"},
    ),
    TeslaButtonDescription(
        key="open_charge_port",
        name="Ladeanschluss öffnen",
        icon="mdi:ev-plug-type2",
        command="CHARGE_PORT_DOOR_OPEN",
    ),
    TeslaButtonDescription(
        key="close_charge_port",
        name="Ladeanschluss schließen",
        icon="mdi:ev-plug-type2",
        command="CHARGE_PORT_DOOR_CLOSE",
    ),
    # ── Medien ───────────────────────────────────────────────────────────────
    TeslaButtonDescription(
        key="media_play_pause",
        name="Wiedergabe Pause/Play",
        icon="mdi:play-pause",
        command="MEDIA_TOGGLE_PLAYBACK",
    ),
    TeslaButtonDescription(
        key="media_next",
        name="Nächster Titel",
        icon="mdi:skip-next",
        command="MEDIA_NEXT_TRACK",
    ),
    TeslaButtonDescription(
        key="media_prev",
        name="Vorheriger Titel",
        icon="mdi:skip-previous",
        command="MEDIA_PREVIOUS_TRACK",
    ),
    TeslaButtonDescription(
        key="media_volume_up",
        name="Lautstärke lauter",
        icon="mdi:volume-plus",
        command="MEDIA_VOLUME_UP",
    ),
    TeslaButtonDescription(
        key="media_volume_down",
        name="Lautstärke leiser",
        icon="mdi:volume-minus",
        command="MEDIA_VOLUME_DOWN",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: TeslaDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TeslaButton(coordinator, description, entry)
        for description in BUTTON_TYPES
    )


class TeslaButton(CoordinatorEntity[TeslaDataCoordinator], ButtonEntity):
    entity_description: TeslaButtonDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TeslaDataCoordinator,
        description: TeslaButtonDescription,
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

    async def async_press(self) -> None:
        await self.coordinator.async_command(
            self.entity_description.command,
            **self.entity_description.command_kwargs,
        )
