from __future__ import annotations

import base64
import json
import logging
import os
import tempfile
from typing import Any

import teslapy
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TeslaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._email: str | None = None
        self._code_verifier_b64: str | None = None
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
                fd, cache_file = tempfile.mkstemp(suffix=".json")
                os.close(fd)
                with open(cache_file, "w") as f:
                    f.write("{}")
                try:
                    with teslapy.Tesla(self._email, cache_file=cache_file) as tesla:
                        tesla._state = self._state
                        tesla.code_verifier = base64.b64decode(self._code_verifier_b64)
                        tesla.fetch_token(authorization_response=callback_url)
                    with open(cache_file) as f:
                        return json.load(f)
                finally:
                    if os.path.exists(cache_file):
                        os.unlink(cache_file)

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
                _LOGGER.exception("Authentifizierung fehlgeschlagen: %s", e)
                errors["base"] = "invalid_auth"

        if self._auth_url is None:
            def _get_auth_url() -> tuple[str, str, str]:
                fd, cache_file = tempfile.mkstemp(suffix=".json")
                os.close(fd)
                with open(cache_file, "w") as f:
                    f.write("{}")
                try:
                    with teslapy.Tesla(self._email, cache_file=cache_file) as tesla:
                        url = tesla.authorization_url()
                        verifier_b64 = base64.b64encode(tesla.code_verifier).decode()
                        state = tesla._state
                        return url, verifier_b64, state
                finally:
                    if os.path.exists(cache_file):
                        os.unlink(cache_file)

            self._auth_url, self._code_verifier_b64, self._state = (
                await self.hass.async_add_executor_job(_get_auth_url)
            )

        return self.async_show_form(
            step_id="auth",
            data_schema=vol.Schema({vol.Required("callback_url"): str}),
            description_placeholders={"auth_url": self._auth_url},
            errors=errors,
        )
