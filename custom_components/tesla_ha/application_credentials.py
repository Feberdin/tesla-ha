"""Application Credentials hook for Tesla Fleet OAuth.

Purpose:
    Lets Home Assistant create a Tesla Fleet OAuth implementation from the
    client id and client secret stored in Settings -> Devices & services ->
    Application Credentials.

Input / Output:
    Input is the Home Assistant application credential for the `tesla_ha`
    domain. Output is a reusable OAuth implementation for the config flow and
    token refreshes.

Important invariants:
    Secrets are never inspected here. Home Assistant passes the credential
    object directly to the OAuth helper.

Debugging:
    If this function is not called, check that `application_credentials` is
    listed as a manifest dependency and Home Assistant was restarted after the
    HACS download.
"""

from __future__ import annotations

from homeassistant.components.application_credentials import ClientCredential
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .oauth import TeslaFleetUserImplementation
from .oauth_redirect import get_oauth_redirect_uri


async def async_get_auth_implementation(
    hass: HomeAssistant,
    auth_domain: str,
    credential: ClientCredential,
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return the Tesla Fleet OAuth implementation."""

    return TeslaFleetUserImplementation(hass, auth_domain, credential)


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return placeholders shown in Home Assistant's credentials dialog."""

    return {
        "dashboard": "https://developer.tesla.com/dashboard",
        "redirect_uri": get_oauth_redirect_uri(hass),
    }
