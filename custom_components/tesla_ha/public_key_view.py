"""Public HTTP view for Tesla Fleet public-key hosting.

Purpose:
    Lets Home Assistant serve the Tesla Fleet public key at Tesla's required
    well-known path. This removes the need for a separate Cloudflare Worker or
    manual static hosting when the configured domain points to Home Assistant.

Input / Output:
    Input is the local Fleet private key file generated during setup. Output is
    a public unauthenticated HTTP response containing only the derived public
    key PEM.

Important invariants:
    The route is intentionally unauthenticated because Tesla must fetch it
    server-to-server. The private key is never returned, logged or embedded in
    diagnostics. If the private key does not exist yet, the route returns 404
    instead of generating a new key outside the normal setup flow.

Debugging:
    Test from outside the network with:
    `curl -i https://DOMAIN/.well-known/appspecific/com.tesla.3p.public-key.pem`.
    The response must be HTTP 200 and start with `-----BEGIN PUBLIC KEY-----`.
"""

from __future__ import annotations

import logging

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .public_key import public_key_pem_from_private_key_file
from .tesla_fleet import FLEET_PRIVATE_KEY_FILE

_LOGGER = logging.getLogger(__name__)

TESLA_PUBLIC_KEY_PATH = "/.well-known/appspecific/com.tesla.3p.public-key.pem"
_VIEW_REGISTERED = f"{DOMAIN}_public_key_view_registered"


def async_register_public_key_view(hass: HomeAssistant) -> None:
    """Register the unauthenticated Tesla public-key endpoint once."""

    if hass.data.get(_VIEW_REGISTERED):
        return

    hass.http.register_view(TeslaPublicKeyView(hass))
    hass.data[_VIEW_REGISTERED] = True


class TeslaPublicKeyView(HomeAssistantView):
    """Serve Tesla's required public key file from the local private key."""

    requires_auth = False
    name = "tesla_ha:public_key"
    url = TESLA_PUBLIC_KEY_PATH

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return the public key PEM or a clear setup error."""

        private_key_path = self._hass.config.path(FLEET_PRIVATE_KEY_FILE)
        try:
            public_key_pem = await self._hass.async_add_executor_job(
                public_key_pem_from_private_key_file,
                private_key_path,
            )
        except FileNotFoundError:
            return web.Response(
                text="Tesla Fleet private key has not been generated yet.\n",
                status=404,
                content_type="text/plain",
            )
        except (OSError, ValueError) as err:
            _LOGGER.error("Could not serve Tesla Fleet public key: %s", err)
            return web.Response(
                text="Tesla Fleet public key could not be loaded.\n",
                status=500,
                content_type="text/plain",
            )

        return web.Response(
            text=public_key_pem,
            content_type="text/plain",
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )
