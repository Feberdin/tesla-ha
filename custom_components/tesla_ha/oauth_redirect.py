"""OAuth redirect URI helpers for Tesla Fleet setup guidance.

Purpose:
    Centralizes how the integration discovers and displays the Home Assistant
    OAuth redirect URI that must be registered in the Tesla Developer Portal.

Input / Output:
    Input is the current Home Assistant instance. Output is a display-safe
    redirect URI string used only in setup forms and documentation text.

Important invariants:
    The helper never reads OAuth tokens, client secrets or Tesla account data.
    The returned URI must match the value Home Assistant places into the Tesla
    authorization URL; otherwise Tesla rejects login before Home Assistant sees
    a callback.

Debugging:
    If Tesla shows "redirect_uri supplied is not registered", compare the URI
    shown by this helper with the Redirect URI list in the Tesla Developer
    Portal. With Home Assistant's `my` integration enabled, the expected value
    is usually `https://my.home-assistant.io/redirect/oauth`.
"""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

_LOGGER = logging.getLogger(__name__)

DEFAULT_OAUTH_REDIRECT_URI = "https://my.home-assistant.io/redirect/oauth"


def get_oauth_redirect_uri(hass: HomeAssistant) -> str:
    """Return the OAuth redirect URI Home Assistant will send to Tesla."""

    try:
        return config_entry_oauth2_flow.async_get_redirect_uri(hass)
    except RuntimeError as err:
        _LOGGER.debug(
            "Could not read Home Assistant OAuth redirect URI, using default: %s",
            err,
        )
        return DEFAULT_OAUTH_REDIRECT_URI
