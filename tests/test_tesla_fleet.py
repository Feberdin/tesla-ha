"""Unit tests for Tesla Fleet compatibility helpers.

Purpose:
    Verifies the pure Fleet helper logic without Home Assistant, live Tesla
    credentials or network access.

Input / Output:
    Inputs are mocked product rows, vehicle data dictionaries and fake command
    APIs. Outputs are assertions on normalized entity data, scope handling and
    command dispatch.

Important invariants:
    Tests never contain real Tesla tokens, VINs or client secrets. VIN-like
    strings are deterministic placeholders.

Debugging:
    Run `.venv/bin/python -m pytest tests/test_tesla_fleet.py -q`. A failing
    test points to the Fleet compatibility layer, not to Home Assistant's
    OAuth runtime.
"""

from __future__ import annotations

import importlib.util
import asyncio
import sys
from pathlib import Path

import pytest

TESLA_FLEET_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tesla_ha"
    / "tesla_fleet.py"
)
SPEC = importlib.util.spec_from_file_location("tesla_fleet", TESLA_FLEET_PATH)
assert SPEC is not None
tesla_fleet = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["tesla_fleet"] = tesla_fleet
SPEC.loader.exec_module(tesla_fleet)


class FakeVehicleApi:
    """Minimal async command target used by command-mapping tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    async def set_charge_limit(self, percent: int) -> dict:
        self.calls.append(("set_charge_limit", percent))
        return {"response": {"result": True}}

    async def set_preconditioning_max(
        self,
        *,
        on: bool,
        manual_override: bool,
    ) -> dict:
        self.calls.append(("set_preconditioning_max", (on, manual_override)))
        return {"response": {"result": True}}


def test_normalize_vehicle_data_preserves_legacy_entity_shape() -> None:
    product = {
        "vin": "5YJ3E1EA7PF000000",
        "display_name": "Garage",
        "state": "online",
        "car_type": "model3",
    }
    vehicle_data = {
        "charge_state": {"battery_level": 81},
        "vehicle_state": {"locked": True},
    }

    data = tesla_fleet.normalize_vehicle_data(product, vehicle_data)

    assert data["vin"] == "5YJ3E1EA7PF000000"
    assert data["state"] == "online"
    assert data["charge_state"]["battery_level"] == 81
    assert data["vehicle_state"]["locked"] is True
    assert data["vehicle_state"]["vehicle_name"] == "Garage"
    assert data["climate_state"] == {}
    assert data["vehicle_config"]["car_type"] == "model3"


def test_build_command_maps_charge_limit_alias() -> None:
    api = FakeVehicleApi()

    result = asyncio.run(
        tesla_fleet.build_command(
            api,
            "SET_CHARGE_LIMIT",
            {"percent": 80},
        )
    )

    assert result == {"response": {"result": True}}
    assert api.calls == [("set_charge_limit", 80)]


def test_build_command_fills_preconditioning_manual_override() -> None:
    api = FakeVehicleApi()

    asyncio.run(tesla_fleet.build_command(api, "MAX_DEFROST", {"on": True}))

    assert api.calls == [("set_preconditioning_max", (True, False))]


def test_command_success_accepts_requested_reason() -> None:
    assert tesla_fleet.command_success({"response": {"result": False, "reason": "requested"}})


def test_unknown_command_fails_fast() -> None:
    with pytest.raises(ValueError, match="Unknown Tesla command"):
        tesla_fleet.build_command(FakeVehicleApi(), "DOES_NOT_EXIST", {})
