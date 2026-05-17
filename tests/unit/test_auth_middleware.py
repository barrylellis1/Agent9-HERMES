"""Unit tests for src/api/auth_middleware.py (Infra B — Supabase Auth)."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


# ---------------------------------------------------------------------------
# _tenant_domain_map + _infer_client_id
# ---------------------------------------------------------------------------

def test_tenant_domain_map_empty(monkeypatch):
    monkeypatch.delenv("TENANT_DOMAIN_MAP", raising=False)
    from src.api.auth_middleware import _tenant_domain_map
    assert _tenant_domain_map() == {}


def test_tenant_domain_map_parses_pairs(monkeypatch):
    monkeypatch.setenv("TENANT_DOMAIN_MAP", "apex.com:apex_lubricants, hess.com:hess")
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    result = mod._tenant_domain_map()
    assert result == {"apex.com": "apex_lubricants", "hess.com": "hess"}


def test_infer_client_id_known_domain(monkeypatch):
    monkeypatch.setenv("TENANT_DOMAIN_MAP", "apex.com:apex_lubricants,hess.com:hess")
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    assert mod._infer_client_id("sarah@apex.com") == "apex_lubricants"
    assert mod._infer_client_id("david@hess.com") == "hess"


def test_infer_client_id_unknown_domain_falls_back(monkeypatch):
    monkeypatch.setenv("TENANT_DOMAIN_MAP", "apex.com:apex_lubricants")
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    assert mod._infer_client_id("user@unknown.com") == "lubricants"


def test_infer_client_id_no_map_falls_back(monkeypatch):
    monkeypatch.delenv("TENANT_DOMAIN_MAP", raising=False)
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    assert mod._infer_client_id("user@anywhere.com") == "lubricants"


def test_infer_client_id_no_at_sign(monkeypatch):
    monkeypatch.delenv("TENANT_DOMAIN_MAP", raising=False)
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    assert mod._infer_client_id("notanemail") == "lubricants"


# ---------------------------------------------------------------------------
# _decode_jwt — unverified fallback (no SUPABASE_JWT_SECRET set)
# ---------------------------------------------------------------------------

def _make_test_token(payload: dict) -> str:
    """Build a minimal JWT (no signature verification — dev path only)."""
    import base64
    import json as _json

    header = base64.urlsafe_b64encode(_json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(_json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


def test_decode_jwt_unverified_fallback(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    token = _make_test_token({"sub": "user-123", "email": "sarah@apex.com", "role": "authenticated"})
    payload = mod._decode_jwt(token)
    assert payload["email"] == "sarah@apex.com"
    assert payload["sub"] == "user-123"


def test_decode_jwt_malformed_raises(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    with pytest.raises(ValueError, match="Malformed JWT"):
        mod._decode_jwt("not.a.valid.jwt.with.six.parts")


def test_decode_jwt_with_secret(monkeypatch):
    secret = "test-jwt-secret-at-least-32-chars!!"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)
    from jose import jwt as jose_jwt
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    token = jose_jwt.encode(
        {"sub": "u1", "email": "cfo@lubricants.com", "role": "authenticated"},
        secret,
        algorithm="HS256",
    )
    payload = mod._decode_jwt(token)
    assert payload["email"] == "cfo@lubricants.com"


def test_decode_jwt_with_wrong_secret_raises(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "correct-secret-that-is-32-chars-ok")
    from jose import jwt as jose_jwt
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    token = jose_jwt.encode(
        {"sub": "u1", "email": "cfo@lubricants.com"},
        "wrong-secret-value-for-signing-x",
        algorithm="HS256",
    )
    with pytest.raises(ValueError):
        mod._decode_jwt(token)


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_no_credentials(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    with pytest.raises(HTTPException) as exc_info:
        await mod.get_current_user(None)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_valid_token(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    monkeypatch.setenv("TENANT_DOMAIN_MAP", "apex.com:apex_lubricants")
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    token = _make_test_token({"sub": "abc", "email": "sarah@apex.com", "role": "authenticated"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await mod.get_current_user(creds)
    assert user.email == "sarah@apex.com"
    assert user.client_id == "apex_lubricants"
    assert user.sub == "abc"


@pytest.mark.asyncio
async def test_get_current_user_bad_token_raises_401(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not.valid")
    with pytest.raises(HTTPException) as exc_info:
        await mod.get_current_user(creds)
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_optional_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_optional_user_no_credentials(monkeypatch):
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    result = await mod.get_optional_user(None)
    assert result is None


@pytest.mark.asyncio
async def test_get_optional_user_invalid_token_returns_none(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token")
    result = await mod.get_optional_user(creds)
    assert result is None


@pytest.mark.asyncio
async def test_get_optional_user_valid_token_returns_user(monkeypatch):
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    monkeypatch.delenv("TENANT_DOMAIN_MAP", raising=False)
    from importlib import reload
    from src.api import auth_middleware as mod
    reload(mod)
    token = _make_test_token({"sub": "xyz", "email": "user@unknown.com", "role": "authenticated"})
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    result = await mod.get_optional_user(creds)
    assert result is not None
    assert result.email == "user@unknown.com"
    assert result.client_id == "lubricants"   # fallback
