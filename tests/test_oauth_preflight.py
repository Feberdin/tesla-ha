"""Tests for Tesla OAuth authorize preflight parsing.

Purpose:
    Verifies that Tesla authorize error pages are mapped to actionable Home
    Assistant setup errors before the user is sent to the browser.

Input / Output:
    Inputs are representative snippets from Tesla OAuth error pages. Outputs
    are translation keys used by the config flow.

Important invariants:
    Tests contain no real client secrets, OAuth tokens or Tesla account data.
    The Client ID strings are deterministic placeholders.

Debugging:
    Run `.venv/bin/python -m pytest tests/test_oauth_preflight.py -q`. If Tesla
    changes authorize error wording, add a fixture here before changing the
    config flow.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

TESLA_PREFLIGHT_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tesla_ha"
    / "oauth_preflight.py"
)
SPEC = importlib.util.spec_from_file_location("oauth_preflight", TESLA_PREFLIGHT_PATH)
assert SPEC is not None
oauth_preflight = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["oauth_preflight"] = oauth_preflight
SPEC.loader.exec_module(oauth_preflight)


def test_detects_redirect_uri_not_registered_error() -> None:
    body = """
    <html>
      <body>
        The 'redirect_uri' supplied is not registered for this 'client_id'.
      </body>
    </html>
    """

    assert (
        oauth_preflight.detect_authorize_error(body)
        == "oauth_preflight_redirect_uri"
    )


def test_detects_legacy_redirect_uri_error_wording() -> None:
    body = "We don't recognize this redirect_uri. Please use the redirect_uri found in your app details."

    assert (
        oauth_preflight.detect_authorize_error(body)
        == "oauth_preflight_redirect_uri"
    )


def test_detects_client_id_error() -> None:
    body = "Tesla OAuth failed: invalid client_id."

    assert oauth_preflight.detect_authorize_error(body) == "oauth_preflight_client_id"


def test_authorize_login_page_without_error_is_ok() -> None:
    body = "<html><title>Sign in with Tesla</title><body>Passphrase eingeben</body></html>"

    assert oauth_preflight.detect_authorize_error(body) is None


def test_summarize_authorize_error_keeps_relevant_context() -> None:
    body = "Prefix " * 40 + "The redirect_uri supplied is not registered for this client_id."

    summary = oauth_preflight.summarize_authorize_error(body)

    assert "redirect_uri" in summary
    assert len(summary) < 270
