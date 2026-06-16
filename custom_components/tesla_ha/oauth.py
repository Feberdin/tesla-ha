"""OAuth implementation for the official Tesla Fleet API.

Purpose:
    Connects Home Assistant application credentials to Tesla's Fleet OAuth
    endpoints. This file owns only the OAuth server metadata and extra request
    parameters; config-flow state and token storage stay in Home Assistant's
    standard OAuth helpers.

Input / Output:
    Input is a Home Assistant `ClientCredential` containing the Tesla
    Developer Portal client id and client secret. Output is an OAuth
    implementation that Home Assistant can use to create and refresh tokens.

Important invariants:
    The client secret is handled only by Home Assistant's application
    credentials storage. It must never be logged or copied into diagnostics.
    The default Fleet audience is EU because this repository is maintained for
    the Feberdin/Home-Assistant setup in Germany; the API client still reads
    Tesla's region claim after login and can follow the account region.

Debugging:
    If OAuth fails before Tesla redirects back to Home Assistant, compare the
    redirect URI shown in Home Assistant Application Credentials with the
    redirect URI configured in the Tesla Developer Portal. Token errors usually
    mean the client secret, allowed origin, or Fleet API audience is wrong.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.application_credentials import (
    AuthImplementation,
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant

from .const import AUTHORIZE_URL, DEFAULT_FLEET_API_BASE_URL, SCOPES, TOKEN_URL


class TeslaFleetUserImplementation(AuthImplementation):
    """Tesla Fleet user OAuth implementation for Home Assistant."""

    def __init__(
        self,
        hass: HomeAssistant,
        auth_domain: str,
        credential: ClientCredential,
    ) -> None:
        super().__init__(
            hass,
            auth_domain,
            credential,
            AuthorizationServer(AUTHORIZE_URL, TOKEN_URL),
        )

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Return Tesla-specific authorization parameters."""

        return {
            "prompt": "login",
            "prompt_missing_scopes": "true",
            "require_requested_scopes": "true",
            "show_keypair_step": "true",
            "scope": " ".join(SCOPES),
        }

    @property
    def extra_token_resolve_data(self) -> dict[str, Any]:
        """Return Tesla-specific token exchange parameters."""

        return {
            "audience": DEFAULT_FLEET_API_BASE_URL,
            "scope": " ".join(SCOPES),
        }
