"""Fernet encryption for connection profile credentials.

Credentials (passwords, service-account JSON, API keys) are encrypted before
being written to Supabase and decrypted only when the server needs to open a
connection.  The encrypted blob is NEVER returned to the browser.

Key derivation: SHA-256 of CONNECTION_PROFILE_ENCRYPTION_KEY env var, then
base64url-encoded to produce a valid 32-byte Fernet key.  If the env var is
not set, a deterministic dev-only key is used with a loud warning — this
must never be used in production.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

_ENV_VAR = "CONNECTION_PROFILE_ENCRYPTION_KEY"
_DEV_FALLBACK = "dev-only-insecure-key-replace-in-production"


def _fernet():
    from cryptography.fernet import Fernet

    raw = os.getenv(_ENV_VAR, "").strip()
    if not raw:
        logger.warning(
            "CONNECTION_PROFILE_ENCRYPTION_KEY is not set — "
            "using insecure dev fallback key. Set this env var before going to production."
        )
        raw = _DEV_FALLBACK

    key = base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
    return Fernet(key)


def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """Encrypt a credentials dict to a Fernet token string."""
    return _fernet().encrypt(json.dumps(credentials).encode()).decode()


def decrypt_credentials(token: str) -> Dict[str, Any]:
    """Decrypt a Fernet token string back to a credentials dict."""
    return json.loads(_fernet().decrypt(token.encode()))


MASKED = "••••••"


def mask_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Replace every value in a credentials dict with the mask sentinel."""
    return {k: MASKED for k in credentials}
