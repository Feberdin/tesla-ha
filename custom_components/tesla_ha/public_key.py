"""Tesla Fleet public-key derivation helpers.

Purpose:
    Derives the public key Tesla expects from the local Fleet private key file.
    Tesla needs this public key at the well-known URL for partner-domain
    registration and Virtual Key trust.

Input / Output:
    Input is the local private key path managed by `tesla-fleet-api`. Output is
    the PEM-formatted public key that is safe to expose publicly.

Important invariants:
    The private key never leaves Home Assistant. Only the derived public key is
    returned. The public key must be stable for a given private key, otherwise
    Tesla partner registration and vehicle pairing will fail.

Debugging:
    If Tesla reports that the public key is missing or mismatched, compare this
    helper's output with the content served at
    `/.well-known/appspecific/com.tesla.3p.public-key.pem`.
"""

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def public_key_pem_from_private_key_file(path: str) -> str:
    """Return the public PEM derived from a local EC private key file."""

    private_key_path = Path(path)
    key_data = private_key_path.read_bytes()
    private_key = serialization.load_pem_private_key(key_data, password=None)
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise ValueError(f"Tesla key at {path} is not an EC private key")

    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
