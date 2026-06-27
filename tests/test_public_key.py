"""Tests for Tesla Fleet public-key helpers.

Purpose:
    Ensures the integration derives the public key Tesla needs from the local
    private key without exposing or modifying the private key itself.

Input / Output:
    Inputs are temporary EC private key files. Outputs are PEM public keys used
    by the unauthenticated Home Assistant well-known endpoint.

Important invariants:
    Tests only create throwaway keys. No real Tesla, Home Assistant or
    Cloudflare secrets are read.

Debugging:
    Run `.venv/bin/python -m pytest tests/test_public_key.py -q`. A failure
    means the public well-known endpoint would serve an invalid Tesla key.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

PUBLIC_KEY_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tesla_ha"
    / "public_key.py"
)
SPEC = importlib.util.spec_from_file_location("tesla_public_key", PUBLIC_KEY_PATH)
assert SPEC is not None
tesla_public_key = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["tesla_public_key"] = tesla_public_key
SPEC.loader.exec_module(tesla_public_key)


def test_public_key_pem_is_derived_from_private_key(tmp_path: Path) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_key_path = tmp_path / "tesla_ha.key"
    private_key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    public_key = tesla_public_key.public_key_pem_from_private_key_file(
        str(private_key_path)
    )

    assert public_key.startswith("-----BEGIN PUBLIC KEY-----")
    assert public_key.endswith("-----END PUBLIC KEY-----\n")
    assert "PRIVATE KEY" not in public_key
