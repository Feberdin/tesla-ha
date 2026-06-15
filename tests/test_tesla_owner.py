"""Unit tests for the Tesla Owner API compatibility client.

Purpose:
    Verifies the core Tesla cloud logic without Home Assistant, live Tesla
    credentials or network access.

Input / Output:
    Inputs are mocked HTTP responses and temporary token-cache files. Outputs
    are assertions on OAuth URL generation, token refresh behavior and
    actionable error messages.

Important invariants:
    Tests must never contain real Tesla tokens. Mock token strings are obvious
    placeholders and are only written to pytest temporary directories.

Debugging:
    Run `python -m pytest tests/test_tesla_owner.py -q`. A failing assertion
    points to the affected Owner API helper or error-mapping branch.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

TESLA_OWNER_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tesla_ha"
    / "tesla_owner.py"
)
SPEC = importlib.util.spec_from_file_location("tesla_owner", TESLA_OWNER_PATH)
assert SPEC is not None
tesla_owner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["tesla_owner"] = tesla_owner
SPEC.loader.exec_module(tesla_owner)

TeslaOwnerApiClient = tesla_owner.TeslaOwnerApiClient
TeslaOwnerApiError = tesla_owner.TeslaOwnerApiError
create_oauth_session = tesla_owner.create_oauth_session


def test_oauth_session_builds_pkce_authorization_url() -> None:
    session = create_oauth_session()

    parsed = urlparse(session.authorization_url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.tesla.com"
    assert query["client_id"] == ["ownerapi"]
    assert query["redirect_uri"] == ["https://auth.tesla.com/void/callback"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == [session.state]
    assert len(session.code_verifier) >= 43


def test_refresh_token_keeps_existing_refresh_token_when_not_returned(tmp_path) -> None:
    cache_file = tmp_path / "tesla_cache.json"
    email = "driver@example.test"
    cache_file.write_text(
        json.dumps(
            {
                email: {
                    "url": "https://auth.tesla.com/",
                    "sso": {
                        "access_token": "expired-access-token",
                        "refresh_token": "existing-refresh-token",
                        "expires_at": int(time.time()) - 60,
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/oauth2/v3/token"
        return httpx.Response(
            200,
            json={
                "access_token": "fresh-access-token",
                "expires_in": 28800,
                "token_type": "Bearer",
            },
        )

    transport = httpx.MockTransport(handler)

    with TeslaOwnerApiClient(email, str(cache_file), transport=transport) as client:
        assert client._access_token() == "fresh-access-token"

    stored = json.loads(cache_file.read_text(encoding="utf-8"))
    token = stored[email]["sso"]
    assert token["access_token"] == "fresh-access-token"
    assert token["refresh_token"] == "existing-refresh-token"
    assert token["expires_at"] > time.time()


def test_fleet_api_403_gets_actionable_error(tmp_path) -> None:
    cache_file = _valid_cache(tmp_path)

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "error": "forbidden, see https://developer.tesla.com/docs/fleet-api",
                "error_description": "",
                "response": None,
            },
        )

    transport = httpx.MockTransport(handler)

    with TeslaOwnerApiClient(
        "driver@example.test",
        str(cache_file),
        transport=transport,
    ) as client:
        with pytest.raises(TeslaOwnerApiError, match="Fleet API"):
            client.vehicle_list()


def test_command_signing_error_gets_actionable_error(tmp_path) -> None:
    cache_file = _valid_cache(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/1/products":
            return httpx.Response(
                200,
                json={
                    "response": [
                        {
                            "id_s": "1234567890",
                            "vehicle_id": 1234567890,
                            "vin": "5YJ3E1EA7PF000000",
                            "state": "online",
                        }
                    ]
                },
            )
        return httpx.Response(
            403,
            json={
                "error": "Tesla Vehicle Command Protocol required",
                "response": None,
            },
        )

    transport = httpx.MockTransport(handler)

    with TeslaOwnerApiClient(
        "driver@example.test",
        str(cache_file),
        transport=transport,
    ) as client:
        vehicle = client.vehicle_list()[0]
        with pytest.raises(TeslaOwnerApiError, match="signierte Commands"):
            client.command(vehicle["id_s"], "LOCK")


def _valid_cache(tmp_path) -> object:
    cache_file = tmp_path / "tesla_cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "driver@example.test": {
                    "url": "https://auth.tesla.com/",
                    "sso": {
                        "access_token": "valid-access-token",
                        "refresh_token": "valid-refresh-token",
                        "expires_at": int(time.time()) + 3600,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return cache_file
