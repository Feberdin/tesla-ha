"""Tesla Fleet API compatibility helpers for this Home Assistant integration.

Purpose:
    Bridges Tesla's official Fleet API library to the data shape that the
    existing `tesla_ha` entities already understand. The entity files can keep
    reading `charge_state`, `vehicle_state`, `climate_state` and similar
    dictionaries while the transport underneath is Fleet API instead of the
    blocked legacy Owner API.

Input / Output:
    Inputs are Fleet product rows, Fleet `vehicle_data` responses and local
    command names used by the old entity code. Outputs are normalized vehicle
    data dictionaries and awaitables for the official `tesla-fleet-api`
    command methods.

Important invariants:
    This module never receives raw OAuth secrets. It also does not hide Fleet
    limitations: if the Tesla account lacks command scopes or the vehicle has
    no Virtual Key, the caller gets an actionable Home Assistant error instead
    of a silent no-op.

Debugging:
    If entities are created but show `unknown`, inspect the normalized keys
    here first. If commands fail, compare the local command name with
    `COMMAND_METHODS` and check whether the Fleet app has `vehicle_cmds` or
    `vehicle_charging_cmds` scope plus a paired Virtual Key.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from tesla_fleet_api.const import Scope, VehicleDataEndpoint

CONF_FLEET_DOMAIN = "fleet_domain"
FLEET_PRIVATE_KEY_FILE = "tesla_ha.key"

FLEET_VEHICLE_ENDPOINTS = [
    VehicleDataEndpoint.CHARGE_STATE,
    VehicleDataEndpoint.CLIMATE_STATE,
    VehicleDataEndpoint.DRIVE_STATE,
    VehicleDataEndpoint.GUI_SETTINGS,
    VehicleDataEndpoint.LOCATION_DATA,
    VehicleDataEndpoint.VEHICLE_CONFIG,
    VehicleDataEndpoint.VEHICLE_STATE,
]

COMMAND_REQUIRED_SCOPES: dict[str, tuple[Scope, ...]] = {
    "CHANGE_CHARGE_LIMIT": (Scope.VEHICLE_CHARGING_CMDS, Scope.VEHICLE_CMDS),
    "SET_CHARGE_LIMIT": (Scope.VEHICLE_CHARGING_CMDS, Scope.VEHICLE_CMDS),
    "CHARGING_AMPS": (Scope.VEHICLE_CHARGING_CMDS, Scope.VEHICLE_CMDS),
    "START_CHARGE": (Scope.VEHICLE_CHARGING_CMDS, Scope.VEHICLE_CMDS),
    "STOP_CHARGE": (Scope.VEHICLE_CHARGING_CMDS, Scope.VEHICLE_CMDS),
}


def normalize_vehicle_data(
    product: dict[str, Any],
    vehicle_data: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return Fleet vehicle data in the legacy entity-friendly shape."""

    data = dict(vehicle_data or {})
    data.setdefault("charge_state", {})
    data.setdefault("climate_state", {})
    data.setdefault("drive_state", {})
    data.setdefault("gui_settings", {})
    data.setdefault("vehicle_config", {})
    data.setdefault("vehicle_state", {})

    vin = _text(data.get("vin")) or _text(product.get("vin"))
    if vin:
        data["vin"] = vin

    if state := _text(data.get("state")) or _text(product.get("state")):
        data["state"] = state

    vehicle_state = data["vehicle_state"]
    if "car_version" not in vehicle_state and product.get("car_version"):
        vehicle_state["car_version"] = product.get("car_version")
    if "vehicle_name" not in vehicle_state:
        vehicle_state["vehicle_name"] = (
            product.get("display_name")
            or product.get("vehicle_name")
            or product.get("name")
            or "Tesla"
        )

    vehicle_config = data["vehicle_config"]
    if "car_type" not in vehicle_config and product.get("car_type"):
        vehicle_config["car_type"] = product.get("car_type")

    return data


def vehicle_id_from_product(product: dict[str, Any]) -> str:
    """Return a stable product identifier for diagnostics and unique ids."""

    value = product.get("vin") or product.get("id_s") or product.get("vehicle_id")
    if not value:
        raise ValueError("Tesla Fleet product does not contain a VIN or vehicle id")
    return str(value)


def command_requires_scope(command: str) -> tuple[Scope, ...]:
    """Return acceptable Fleet scopes for a local command name."""

    return COMMAND_REQUIRED_SCOPES.get(command, (Scope.VEHICLE_CMDS,))


def build_command(
    vehicle_api: Any,
    command: str,
    kwargs: dict[str, Any],
) -> Awaitable[dict[str, Any]]:
    """Return the official Fleet command awaitable for a local command name."""

    command_key = "CHANGE_CHARGE_LIMIT" if command == "SET_CHARGE_LIMIT" else command
    builder = COMMAND_METHODS.get(command_key)
    if builder is None:
        raise ValueError(f"Unknown Tesla command: {command}")
    return builder(vehicle_api, kwargs)


def command_success(result: dict[str, Any]) -> bool:
    """Return whether a Tesla command response represents success."""

    response = result.get("response")
    if isinstance(response, dict):
        if response.get("result") is True:
            return True
        if response.get("reason") in {"already_set", "not_charging", "requested"}:
            return True
    return False


def command_error_reason(result: dict[str, Any]) -> str:
    """Extract a human-readable command failure reason."""

    response = result.get("response")
    if isinstance(response, dict):
        reason = response.get("reason") or response.get("error")
        if reason:
            return str(reason)
    return str(result.get("error") or "Tesla returned no command result")


def _set_preconditioning_max(api: Any, kwargs: dict[str, Any]) -> Awaitable[dict[str, Any]]:
    return api.set_preconditioning_max(
        on=bool(kwargs.get("on")),
        manual_override=bool(kwargs.get("manual_override", False)),
    )


def _seat_heater(api: Any, kwargs: dict[str, Any]) -> Awaitable[dict[str, Any]]:
    return api.remote_seat_heater_request(
        kwargs.get("heater", kwargs.get("seat_position", 0)),
        kwargs.get("level", kwargs.get("seat_heater_level", 0)),
    )


def _seat_cooler(api: Any, kwargs: dict[str, Any]) -> Awaitable[dict[str, Any]]:
    return api.remote_seat_cooler_request(
        kwargs.get("seat_position", kwargs.get("heater", 0)),
        kwargs.get("seat_cooler_level", kwargs.get("level", 0)),
    )


def _temps(api: Any, kwargs: dict[str, Any]) -> Awaitable[dict[str, Any]]:
    driver_temp = kwargs.get("driver_temp")
    passenger_temp = kwargs.get("passenger_temp", driver_temp)
    return api.set_temps(driver_temp=driver_temp, passenger_temp=passenger_temp)


COMMAND_METHODS: dict[str, Callable[[Any, dict[str, Any]], Awaitable[dict[str, Any]]]] = {
    "ACTUATE_TRUNK": lambda api, kwargs: api.actuate_trunk(kwargs.get("which_trunk", "rear")),
    "CHANGE_CHARGE_LIMIT": lambda api, kwargs: api.set_charge_limit(int(kwargs["percent"])),
    "CHANGE_CLIMATE_TEMPERATURE_SETTING": _temps,
    "CHARGE_PORT_DOOR_CLOSE": lambda api, _kwargs: api.charge_port_door_close(),
    "CHARGE_PORT_DOOR_OPEN": lambda api, _kwargs: api.charge_port_door_open(),
    "CHARGING_AMPS": lambda api, kwargs: api.set_charging_amps(int(kwargs["charging_amps"])),
    "CLIMATE_OFF": lambda api, _kwargs: api.auto_conditioning_stop(),
    "CLIMATE_ON": lambda api, _kwargs: api.auto_conditioning_start(),
    "FLASH_LIGHTS": lambda api, _kwargs: api.flash_lights(),
    "HONK_HORN": lambda api, _kwargs: api.honk_horn(),
    "LOCK": lambda api, _kwargs: api.door_lock(),
    "MAX_DEFROST": _set_preconditioning_max,
    "MEDIA_NEXT_TRACK": lambda api, _kwargs: api.media_next_track(),
    "MEDIA_PREVIOUS_TRACK": lambda api, _kwargs: api.media_prev_track(),
    "MEDIA_TOGGLE_PLAYBACK": lambda api, _kwargs: api.media_toggle_playback(),
    "MEDIA_VOLUME_DOWN": lambda api, _kwargs: api.media_volume_down(),
    "MEDIA_VOLUME_UP": lambda api, _kwargs: api.adjust_volume(11.0),
    "REMOTE_SEAT_COOLING_REQUEST": _seat_cooler,
    "REMOTE_SEAT_HEATER_REQUEST": _seat_heater,
    "REMOTE_STEERING_WHEEL_HEATER_REQUEST": lambda api, kwargs: api.remote_steering_wheel_heater_request(
        bool(kwargs.get("on"))
    ),
    "SET_SENTRY_MODE": lambda api, kwargs: api.set_sentry_mode(bool(kwargs.get("on"))),
    "START_CHARGE": lambda api, _kwargs: api.charge_start(),
    "STOP_CHARGE": lambda api, _kwargs: api.charge_stop(),
    "UNLOCK": lambda api, _kwargs: api.door_unlock(),
}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
