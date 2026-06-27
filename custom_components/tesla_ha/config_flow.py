"""Config flow for the official Tesla Fleet API connection.

Purpose:
    Replaces the blocked legacy Owner API login with Home Assistant's standard
    OAuth/Application-Credentials flow for Tesla Fleet API. The flow also
    performs Tesla partner domain registration and shows the Virtual Key link
    required for signed vehicle commands.

Input / Output:
    Inputs are the Tesla Developer Portal client id/secret stored as Home
    Assistant application credentials plus a public domain that hosts the
    Tesla public key. Output is a Home Assistant config entry containing only
    OAuth token metadata managed by Home Assistant.

Important invariants:
    No Tesla password is ever collected. No raw token or client secret is
    logged. The generated private key stays in Home Assistant's config
    directory; only the public key is shown to the user for hosting.

Debugging:
    If setup fails before login, check Application Credentials. If domain
    registration fails, verify the Tesla Developer Portal allowed origin and
    that the public key is hosted at the exact well-known URL shown in the
    form. If commands fail after setup, pair the Virtual Key in the Tesla app.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
import logging
import re
from typing import Any, cast

import jwt
from tesla_fleet_api import TeslaFleetApi
from tesla_fleet_api.const import SERVERS, Scope
from tesla_fleet_api.exceptions import (
    InvalidToken,
    LoginRequired,
    OAuthExpired,
    PreconditionFailed,
    TeslaFleetError,
)
import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.const import CONF_DOMAIN
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError

from .const import DOMAIN
from .oauth import TeslaFleetUserImplementation
from .oauth_preflight import OAuthPreflightResult, async_check_tesla_authorize_url
from .oauth_redirect import get_oauth_redirect_uri
from .public_key_view import async_register_public_key_view
from .tesla_fleet import CONF_FLEET_DOMAIN, FLEET_PRIVATE_KEY_FILE

_LOGGER = logging.getLogger(__name__)

OAUTH_AUTHORIZE_URL_TIMEOUT_SEC = 30


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler,
    domain=DOMAIN,
):
    """Handle Tesla Fleet API OAuth2 authentication."""

    DOMAIN = DOMAIN

    def __init__(self) -> None:
        super().__init__()
        self._domain: str | None = None
        self._data: dict[str, Any] = {}
        self._uid: str | None = None
        self._partner_apis: list[TeslaFleetApi] = []

    @property
    def logger(self) -> logging.Logger:
        """Return the config-flow logger."""

        return _LOGGER

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Show Tesla OAuth redirect guidance before opening Tesla login."""

        return await self.async_step_oauth_redirect_info(user_input)

    async def async_step_oauth_redirect_info(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Explain the redirect URI Tesla must know before OAuth starts."""

        if user_input is not None:
            return await super().async_step_user()

        return self.async_show_form(
            step_id="oauth_redirect_info",
            data_schema=vol.Schema({}),
            description_placeholders={
                "dashboard": "https://developer.tesla.com/dashboard",
                "redirect_uri": get_oauth_redirect_uri(self.hass),
            },
        )

    async def async_step_auth(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Preflight Tesla authorize settings before browser redirect."""

        if user_input is not None:
            return await super().async_step_auth(user_input)

        try:
            async with asyncio.timeout(OAUTH_AUTHORIZE_URL_TIMEOUT_SEC):
                authorize_url = await self.async_generate_authorize_url()
        except TimeoutError as err:
            _LOGGER.error("Timeout generating Tesla authorize URL: %s", err)
            return self.async_abort(reason="authorize_url_timeout")
        except NoURLAvailableError:
            return self.async_abort(
                reason="no_url_available",
                description_placeholders={
                    "docs_url": (
                        "https://www.home-assistant.io/more-info/"
                        "no-url-available"
                    )
                },
            )

        try:
            async with asyncio.timeout(OAUTH_AUTHORIZE_URL_TIMEOUT_SEC):
                preflight = await async_check_tesla_authorize_url(
                    self.hass, authorize_url
                )
        except TimeoutError as err:
            preflight = OAuthPreflightResult(
                ok=False,
                error_key="oauth_preflight_unreachable",
                detail=str(err),
            )

        if preflight.ok:
            return self.async_external_step(step_id="auth", url=authorize_url)

        implementation = cast(TeslaFleetUserImplementation, self.flow_impl)
        description_placeholders = {
            "client_id": implementation.client_id,
            "dashboard": "https://developer.tesla.com/dashboard",
            "detail": preflight.detail or "-",
            "redirect_uri": get_oauth_redirect_uri(self.hass),
        }

        if preflight.error_key == "oauth_preflight_unreachable":
            _LOGGER.warning(
                "Tesla OAuth preflight could not reach authorize endpoint: %s",
                preflight.detail,
            )
            return self.async_show_form(
                step_id="oauth_preflight_warning",
                data_schema=vol.Schema({}),
                description_placeholders=description_placeholders,
            )

        return self.async_show_form(
            step_id="oauth_preflight_failed",
            data_schema=vol.Schema({}),
            errors={"base": preflight.error_key or "oauth_preflight_failed"},
            description_placeholders=description_placeholders,
        )

    async def async_step_oauth_preflight_failed(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Re-run the OAuth preflight after the Tesla app was corrected."""

        if user_input is not None:
            return await self.async_step_auth()

        return self.async_show_form(
            step_id="oauth_preflight_failed",
            data_schema=vol.Schema({}),
            errors={"base": "oauth_preflight_failed"},
            description_placeholders={
                "client_id": "-",
                "dashboard": "https://developer.tesla.com/dashboard",
                "detail": "-",
                "redirect_uri": get_oauth_redirect_uri(self.hass),
            },
        )

    async def async_step_oauth_preflight_warning(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Allow continuing when only the unauthenticated preflight failed."""

        if user_input is not None:
            return await super().async_step_auth()

        return self.async_show_form(
            step_id="oauth_preflight_warning",
            data_schema=vol.Schema({}),
            description_placeholders={
                "client_id": "-",
                "dashboard": "https://developer.tesla.com/dashboard",
                "detail": "-",
                "redirect_uri": get_oauth_redirect_uri(self.hass),
            },
        )

    async def async_oauth_create_entry(
        self,
        data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Handle OAuth completion and continue with Fleet domain setup."""

        token = jwt.decode(
            data["token"]["access_token"],
            options={"verify_signature": False},
        )

        self._data = data
        self._uid = str(token["sub"])

        await self.async_set_unique_id(self._uid)
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="reauth_account_mismatch")
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(),
                data=data,
            )
        self._abort_if_unique_id_configured()

        partner_login_result = await self._async_partner_login_all_regions()
        if partner_login_result:
            return partner_login_result

        return await self.async_step_domain_input()

    async def async_step_domain_input(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, str] | None = None,
    ) -> ConfigFlowResult:
        """Ask for the public domain hosting Tesla's public key."""

        errors = errors or {}

        if user_input is not None:
            domain = user_input[CONF_DOMAIN].strip().lower()
            if not _is_valid_domain(domain):
                errors[CONF_DOMAIN] = "invalid_domain"
            else:
                self._domain = domain
                return await self.async_step_domain_registration()

        return self.async_show_form(
            step_id="domain_input",
            description_placeholders={
                "dashboard": "https://developer.tesla.com/dashboard",
            },
            data_schema=vol.Schema({vol.Required(CONF_DOMAIN): str}),
            errors=errors,
        )

    async def async_step_domain_registration(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Register the public-key domain with Tesla Fleet API."""

        if not self._partner_apis:
            return self.async_abort(reason="oauth_error")
        if not self._domain:
            return await self.async_step_domain_input()

        primary_api = self._partner_apis[0]
        if not primary_api.private_key:
            await primary_api.get_private_key(
                self.hass.config.path(FLEET_PRIVATE_KEY_FILE)
            )
        async_register_public_key_view(self.hass)

        errors: dict[str, str] = {}
        description_placeholders = {
            "public_key_url": (
                f"https://{self._domain}/.well-known/appspecific/"
                "com.tesla.3p.public-key.pem"
            ),
            "pem": primary_api.public_pem,
        }

        successful_response: dict[str, Any] | None = None
        failed_regions: list[str] = []

        for api in self._partner_apis:
            try:
                register_response = await api.partner.register(self._domain)
            except PreconditionFailed:
                return await self.async_step_domain_input(
                    errors={CONF_DOMAIN: "precondition_failed"}
                )
            except TeslaFleetError as err:
                _LOGGER.warning(
                    "Tesla Fleet partner registration failed for %s: %s",
                    api.server,
                    err.message,
                )
                failed_regions.append(api.server or "unknown")
                continue

            if successful_response is None:
                successful_response = register_response

        if successful_response is None:
            errors["base"] = "invalid_response"
            return self.async_show_form(
                step_id="domain_registration",
                description_placeholders=description_placeholders,
                errors=errors,
            )

        if failed_regions:
            _LOGGER.warning(
                "Tesla Fleet partner registration succeeded only partially. "
                "Failed regions: %s",
                ", ".join(failed_regions),
            )

        registered_public_key = successful_response.get("response", {}).get(
            "public_key"
        )
        if not registered_public_key:
            errors["base"] = "public_key_not_found"
        elif (
            registered_public_key.lower()
            != primary_api.public_uncompressed_point.lower()
        ):
            errors["base"] = "public_key_mismatch"
        else:
            return await self.async_step_registration_complete()

        return self.async_show_form(
            step_id="domain_registration",
            description_placeholders=description_placeholders,
            errors=errors,
        )

    async def async_step_registration_complete(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Show final Virtual Key instructions and create the entry."""

        if user_input is not None and self._uid and self._data and self._domain:
            return self.async_create_entry(
                title=f"Tesla Fleet ({self._uid})",
                data={**self._data, CONF_FLEET_DOMAIN: self._domain},
            )

        if not self._domain:
            return await self.async_step_domain_input()

        virtual_key_url = f"https://www.tesla.com/_ak/{self._domain}"
        return self.async_show_form(
            step_id="registration_complete",
            data_schema=vol.Schema({}),
            description_placeholders={"virtual_key_url": virtual_key_url},
        )

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, Any],
    ) -> ConfigFlowResult:
        """Perform reauth when Tesla rejects the stored OAuth token."""

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm reauth before restarting the OAuth flow."""

        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                description_placeholders={"name": "Tesla Fleet"},
            )
        return await super().async_step_user()

    async def _async_partner_login_all_regions(self) -> ConfigFlowResult | None:
        """Create partner API sessions used for domain registration."""

        implementation = cast(TeslaFleetUserImplementation, self.flow_impl)
        session = async_get_clientsession(self.hass)
        failed_regions: list[str] = []

        for region, server_url in SERVERS.items():
            if region == "cn":
                continue

            api = TeslaFleetApi(
                session=session,
                access_token="",
                server=server_url,
                partner_scope=True,
                charging_scope=False,
                energy_scope=False,
                user_scope=False,
                vehicle_scope=False,
            )
            await api.get_private_key(self.hass.config.path(FLEET_PRIVATE_KEY_FILE))

            try:
                await api.partner_login(
                    implementation.client_id,
                    implementation.client_secret,
                    [Scope.OPENID],
                )
            except (InvalidToken, OAuthExpired, LoginRequired) as err:
                _LOGGER.warning(
                    "Tesla Fleet partner login failed for %s due to auth: %s",
                    server_url,
                    err,
                )
                return self.async_abort(reason="oauth_error")
            except TeslaFleetError as err:
                _LOGGER.warning(
                    "Tesla Fleet partner login failed for %s: %s",
                    server_url,
                    err,
                )
                failed_regions.append(server_url)
                continue

            self._partner_apis.append(api)

        if not self._partner_apis:
            _LOGGER.warning(
                "Tesla Fleet partner login failed for all regions: %s",
                ", ".join(failed_regions),
            )
            return self.async_abort(reason="oauth_error")

        return None


def _is_valid_domain(domain: str) -> bool:
    """Return True if the value is a plausible public DNS domain."""

    pattern = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )
    return bool(pattern.match(domain))
