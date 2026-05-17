"""Supabase JWT authentication middleware — Infra B.

Validates the Supabase JWT sent in the `Authorization: Bearer <token>` header
and makes the authenticated user available to API routes via FastAPI's
dependency injection system.

Usage:
    from src.api.auth_middleware import get_current_user, AuthUser

    @router.get("/protected")
    async def protected_route(user: AuthUser = Depends(get_current_user)):
        return {"client_id": user.client_id}

For routes that work with OR without auth, use get_optional_user instead.

TENANT_DOMAIN_MAP env var maps email domains to client_ids.
Format: "domain1:client_id1,domain2:client_id2"
Example: "apex.com:apex_lubricants,hess.com:hess,lubricants.com:lubricants"
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)

_SUPABASE_JWT_SECRET_ENV = "SUPABASE_JWT_SECRET"
_TENANT_DOMAIN_MAP_ENV = "TENANT_DOMAIN_MAP"


@dataclass
class AuthUser:
    """Authenticated user extracted from a Supabase JWT."""
    sub: str            # Supabase user UUID
    email: str
    client_id: str      # inferred from email domain via TENANT_DOMAIN_MAP
    role: str = "authenticated"


def _tenant_domain_map() -> dict[str, str]:
    raw = os.getenv(_TENANT_DOMAIN_MAP_ENV, "").strip()
    result: dict[str, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" in pair:
            domain, cid = pair.split(":", 1)
            result[domain.strip().lower()] = cid.strip()
    return result


def _infer_client_id(email: str) -> str:
    domain = email.split("@")[-1].lower() if "@" in email else ""
    mapping = _tenant_domain_map()
    return mapping.get(domain, "lubricants")   # fallback for unmapped domains


def _decode_jwt(token: str) -> dict:
    jwt_secret = os.getenv(_SUPABASE_JWT_SECRET_ENV, "").strip()
    if not jwt_secret:
        logger.warning(
            "SUPABASE_JWT_SECRET not set — falling back to unverified JWT decode. "
            "Set this env var before production."
        )
        # Unverified decode — only for dev; strips signature verification
        import base64, json as _json
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed JWT")
        padded = parts[1] + "=="
        return _json.loads(base64.urlsafe_b64decode(padded))

    from jose import JWTError, jwt as jose_jwt
    try:
        return jose_jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise ValueError(f"JWT validation failed: {exc}") from exc


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> AuthUser:
    """FastAPI dependency — requires a valid Supabase JWT.

    Raises HTTP 401 if the token is missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = _decode_jwt(credentials.credentials)
    except (ValueError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("email") or ""
    sub = payload.get("sub") or ""
    role = payload.get("role") or "authenticated"
    client_id = _infer_client_id(email)

    return AuthUser(sub=sub, email=email, client_id=client_id, role=role)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[AuthUser]:
    """FastAPI dependency — returns None if no token provided.

    Use for routes that work both authenticated and unauthenticated.
    Returns None for missing/invalid tokens rather than raising 401.
    """
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
