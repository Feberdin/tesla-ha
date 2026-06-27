"""Tests for Tesla OAuth setup guidance.

Purpose:
    Verifies that the user-facing setup texts mention the redirect URI that
    Tesla validates before Home Assistant receives any OAuth callback.

Input / Output:
    Inputs are repository JSON and Markdown files. Outputs are assertions that
    the critical setup guidance is present and consistent.

Important invariants:
    Tests contain no real client IDs, tokens or Tesla account data. They only
    check static help text that prevents a common OAuth misconfiguration.

Debugging:
    Run `.venv/bin/python -m pytest tests/test_oauth_guidance.py -q`. If this
    fails, update the setup text together with the OAuth config-flow changes.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
DEFAULT_REDIRECT_URI = "https://my.home-assistant.io/redirect/oauth"


def _read_json(path: str) -> dict:
    """Read a repository JSON file with a clear failure path."""

    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def test_application_credentials_show_redirect_uri_placeholder() -> None:
    strings = _read_json("custom_components/tesla_ha/strings.json")

    description = strings["application_credentials"]["description"]

    assert "{redirect_uri}" in description
    assert "Allowed Origin" in description


def test_config_flow_has_pre_oauth_redirect_step() -> None:
    strings = _read_json("custom_components/tesla_ha/strings.json")

    step = strings["config"]["step"]["oauth_redirect_info"]

    assert "{redirect_uri}" in step["description"]
    assert "Client ID" in step["description"]


def test_readme_documents_default_home_assistant_redirect_uri() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert DEFAULT_REDIRECT_URI in readme
    assert "redirect_uri" in readme
