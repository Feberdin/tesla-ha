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
    # ── Laden ────────────────────────────────────────────────────────────────
    TeslaBinarySensorDescription(
        key="charging",
        name="Lädt",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda d: d.get("charge_state", {}).get("charging_state") == "Charging",
    ),
    TeslaBinarySensorDescription(
        key="cable_connected",
        name="Kabel angesteckt",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda d: d.get("charge_state", {}).get("conn_charge_cable")
        not in ("<invalid>", None, ""),
    ),
    TeslaBinarySensorDescription(
        key="charge_port_open",
        name="Ladeanschluss offen",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda d: d.get("charge_state", {}).get("charge_port_door_open"),
    ),
    TeslaBinarySensorDescription(
        key="battery_heater",
        name="Batterieheizung",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda d: d.get("charge_state", {}).get("battery_heater_on"),
    ),
    # ── Fahrzeug ─────────────────────────────────────────────────────────────
    TeslaBinarySensorDescription(
        key="locked",
        name="Verriegelt",
        device_class=BinarySensorDeviceClass.LOCK,
        # LOCK: on = unlocked, off = locked
        value_fn=lambda d: not d.get("vehicle_state", {}).get("locked", True),
    ),
    TeslaBinarySensorDescription(
        key="user_present",
        name="Nutzer anwesend",
        device_class=BinarySensorDeviceClass.PRESENCE,
        value_fn=lambda d: d.get("vehicle_state", {}).get("is_user_present"),
    ),
    # ── Türen ────────────────────────────────────────────────────────────────
    TeslaBinarySensorDescription(
        key="door_driver_front",
        name="Fahrertür",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("df", 0)),
    ),
    TeslaBinarySensorDescription(
        key="door_passenger_front",
        name="Beifahrertür",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("pf", 0)),
    ),
    TeslaBinarySensorDescription(
        key="door_driver_rear",
        name="Fondtür Links",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("dr", 0)),
    ),
    TeslaBinarySensorDescription(
        key="door_passenger_rear",
        name="Fondtür Rechts",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("pr", 0)),
    ),
    TeslaBinarySensorDescription(
        key="frunk_open",
        name="Frunk offen",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("ft", 0)),
    ),
    TeslaBinarySensorDescription(
        key="trunk_open",
        name="Kofferraum offen",
        device_class=BinarySensorDeviceClass.OPENING,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("rt", 0)),
    ),
    # ── Fenster ──────────────────────────────────────────────────────────────
    TeslaBinarySensorDescription(
        key="window_driver_front",
        name="Fenster Fahrer",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("fd_window", 0)),
    ),
    TeslaBinarySensorDescription(
        key="window_passenger_front",
        name="Fenster Beifahrer",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("fp_window", 0)),
    ),
    TeslaBinarySensorDescription(
        key="window_driver_rear",
        name="Fenster Fond Links",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("rd_window", 0)),
    ),
    TeslaBinarySensorDescription(
        key="window_passenger_rear",
        name="Fenster Fond Rechts",
        device_class=BinarySensorDeviceClass.WINDOW,
        value_fn=lambda d: bool(d.get("vehicle_state", {}).get("rp_window", 0)),
    ),
    # ── Klima ────────────────────────────────────────────────────────────────
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
    # ── Reifendruck Warnungen ─────────────────────────────────────────────
    TeslaBinarySensorDescription(
        key="tpms_warn_fl",
        name="Reifendruckwarnung VL",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:tire-alert",
        value_fn=lambda d: d.get("vehicle_state", {}).get("tpms_soft_warning_fl", False)
        or d.get("vehicle_state", {}).get("tpms_hard_warning_fl", False),
    ),
    TeslaBinarySensorDescription(
        key="tpms_warn_fr",
        name="Reifendruckwarnung VR",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:tire-alert",
        value_fn=lambda d: d.get("vehicle_state", {}).get("tpms_soft_warning_fr", False)
        or d.get("vehicle_state", {}).get("tpms_hard_warning_fr", False),
    ),
    TeslaBinarySensorDescription(
        key="tpms_warn_rl",
        name="Reifendruckwarnung HL",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:tire-alert",
        value_fn=lambda d: d.get("vehicle_state", {}).get("tpms_soft_warning_rl", False)
        or d.get("vehicle_state", {}).get("tpms_hard_warning_rl", False),
    ),
    TeslaBinarySensorDescription(
        key="tpms_warn_rr",
        name="Reifendruckwarnung HR",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:tire-alert",
        value_fn=lambda d: d.get("vehicle_state", {}).get("tpms_soft_warning_rr", False)
        or d.get("vehicle_state", {}).get("tpms_hard_warning_rr", False),
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
        if self.coordinator.data is None or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
