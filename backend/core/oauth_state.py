"""Utilities for creating and verifying a signed OAuth `state` token.
Used to prevent CSRF during OAuth login flows by binding the callback to an
initiated login attempt with a short-lived HMAC-signed token. The token is
stateless and does not store server-side session data.
"""

from __future__ import annotations
import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _b64url_encode(raw: bytes) -> str:
    """Encode bytes using URL-safe base64 without padding."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Decode a URL-safe base64 string, restoring required padding."""
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + padding).encode("ascii"))


def make_state_token(secret: str, ttl_seconds: int = 600) -> str:
    """
    Creates a signed, time-limited token suitable for OAuth 'state'.
    Format: base64url(payload_json) + "." + base64url(hmac_sha256(payload))
    """
    if not secret:
        raise ValueError("OAUTH_STATE_SECRET is required")

    payload: dict[str, Any] = {
        "iat": int(time.time()),
        "ttl": int(ttl_seconds),
        "nonce": _b64url_encode(hashlib.sha256(str(time.time_ns()).encode()).digest())[:22],
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()

    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(sig)}"


def verify_state_token(secret: str, token: str) -> bool:
    """
    Verifies signature + expiry for the token created by make_state_token.
    """
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        payload_bytes = _b64url_decode(payload_b64)
        provided_sig = _b64url_decode(sig_b64)
    except Exception:
        return False

    expected_sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    if not hmac.compare_digest(provided_sig, expected_sig):
        return False

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
        iat = int(payload["iat"])
        ttl = int(payload["ttl"])
    except Exception:
        return False

    now = int(time.time())
    return now <= (iat + ttl)