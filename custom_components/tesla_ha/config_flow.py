"""Home Assistant setup flow for Tesla account authentication.

Purpose:
    Guides users through Tesla OAuth and stores the resulting token cache in
    the config entry for later use by the coordinator.

Input / Output:
    Input is the Tesla account email and the callback URL copied after login.
    Output is a Home Assistant config entry containing the email and token
    cache. Token values are never logged.

Important invariants:
    Each generated Tesla login URL has a one-time PKCE verifier and OAuth
    state. Callback URLs must match that state before token exchange.

Debugging:
    Enable debug logging for `custom_components.tesla_ha`. Failed auth logs
    contain the reason class and context, not token contents.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .tesla_owner import (
    TeslaOAuthSession,
    create_oauth_session,
    exchange_authorization_response,
)

_LOGGER = logging.getLogger(__name__)


class TeslaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._email: str | None = None
        self._code_verifier: str | None = None
        self._state: str | None = None
        self._auth_url: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._email = user_input["email"]
            return await self.async_step_auth()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("email"): str}),
        )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            callback_url = user_input.get("callback_url", "").strip()

            def _exchange_token() -> dict:
                return exchange_authorization_response(
                    self._email or "",
                    callback_url,
                    self._code_verifier or "",
                    self._state or "",
                )

            try:
                cache_data = await self.hass.async_add_executor_job(_exchange_token)

                await self.async_set_unique_id(self._email)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Tesla ({self._email})",
                    data={"email": self._email, "cache": cache_data},
                )
            except config_entries.data_entry_flow.AbortFlow:
                raise
            except Exception as e:
                _LOGGER.exception("Tesla Authentifizierung fehlgeschlagen: %s", e)
                errors["base"] = "invalid_auth"

        if self._auth_url is None:
            def _get_auth_url() -> tuple[str, str, str]:
                oauth_session: TeslaOAuthSession = create_oauth_session()
                return (
                    oauth_session.authorization_url,
                    oauth_session.code_verifier,
                    oauth_session.state,
                )

            self._auth_url, self._code_verifier, self._state = (
                await self.hass.async_add_executor_job(_get_auth_url)
            )

        return self.async_show_form(
            step_id="auth",
            data_schema=vol.Schema({vol.Required("callback_url"): str}),
            description_placeholders={"auth_url": self._auth_url},
            errors=errors,
        )
