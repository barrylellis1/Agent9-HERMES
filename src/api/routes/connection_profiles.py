"""API routes for connection profiles.

Infra B: Profiles are now persisted in Supabase (not browser localStorage).
- Scoped by client_id — STRICT MATCH; no cross-tenant leakage.
- Credentials encrypted server-side with Fernet before storage.
- Credentials are NEVER returned to the browser — masked as ••••••.
- client_id comes from the request body (POST/PUT) or query param (GET/DELETE).
  Full Supabase Auth session enforcement is gated on Infra B auth work (pre-Sep 2026).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.api.connection_profile_crypto import (
    MASKED,
    decrypt_credentials,
    encrypt_credentials,
    mask_credentials,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/connection-profiles", tags=["connection-profiles"])


# ---------------------------------------------------------------------------
# DB dependency — reuses the shared pool from RegistryBootstrap
# ---------------------------------------------------------------------------

async def _get_pool() -> asyncpg.Pool:
    from src.registry.bootstrap import RegistryBootstrap
    from src.api.runtime import agent_runtime

    # Ensure the agent runtime (and thus the shared DB pool) is initialized.
    # This is a no-op if it's already running.
    await agent_runtime.initialize()

    db_manager = RegistryBootstrap._db_manager
    if db_manager is None or getattr(db_manager, "pool", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available — registry not initialized.",
        )
    return db_manager.pool


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ConnectionProfileOut(BaseModel):
    id: str
    client_id: str
    name: str
    source_system: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None  # values masked as ••••••
    is_default: bool
    created_by: Optional[str] = None
    created_at: str
    updated_at: str
    last_used_at: Optional[str] = None
    last_used_by: Optional[str] = None


class CreateConnectionProfileRequest(BaseModel):
    client_id: str
    name: str
    source_system: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None  # plain-text on write, encrypted at rest
    is_default: bool = False
    created_by: Optional[str] = None


class UpdateConnectionProfileRequest(BaseModel):
    client_id: str  # required for ownership check
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    schema_name: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None  # None = leave unchanged
    is_default: Optional[bool] = None
    last_used_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row_to_out(row: asyncpg.Record) -> ConnectionProfileOut:
    creds_raw = row["credentials_encrypted"]
    masked: Optional[Dict[str, str]] = None
    if creds_raw:
        try:
            plain = decrypt_credentials(creds_raw)
            masked = mask_credentials(plain)
        except Exception:
            masked = {"_error": MASKED}

    def _iso(val) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.isoformat()
        return str(val)

    return ConnectionProfileOut(
        id=str(row["id"]),
        client_id=row["client_id"],
        name=row["name"],
        source_system=row["source_system"],
        host=row["host"],
        port=row["port"],
        database_name=row["database_name"],
        schema_name=row["schema_name"],
        credentials=masked,
        is_default=bool(row["is_default"]),
        created_by=row["created_by"],
        created_at=_iso(row["created_at"]),
        updated_at=_iso(row["updated_at"]),
        last_used_at=_iso(row["last_used_at"]),
        last_used_by=row["last_used_by"],
    )


async def _fetch_owned(pool: asyncpg.Pool, profile_id: str, client_id: str) -> asyncpg.Record:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM connection_profiles WHERE id = $1",
            uuid.UUID(profile_id),
        )
    if row is None:
        raise HTTPException(status_code=404, detail=f"Connection profile '{profile_id}' not found.")
    if row["client_id"] != client_id:
        raise HTTPException(status_code=403, detail="Access denied — profile belongs to a different client.")
    return row


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[ConnectionProfileOut])
async def list_connection_profiles(
    client_id: str = Query(..., description="Tenant client ID — only profiles for this client are returned"),
    source_system: Optional[str] = Query(None, description="Filter by source system"),
    pool: asyncpg.Pool = Depends(_get_pool),
):
    """List connection profiles for a client. Credentials are masked."""
    sql = "SELECT * FROM connection_profiles WHERE client_id = $1"
    params: list = [client_id]
    if source_system:
        sql += " AND source_system = $2"
        params.append(source_system)
    sql += " ORDER BY updated_at DESC"

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)

    return [_row_to_out(r) for r in rows]


@router.get("/{profile_id}", response_model=ConnectionProfileOut)
async def get_connection_profile(
    profile_id: str,
    client_id: str = Query(..., description="Tenant client ID for ownership verification"),
    pool: asyncpg.Pool = Depends(_get_pool),
):
    """Get a single connection profile. Credentials are masked."""
    row = await _fetch_owned(pool, profile_id, client_id)
    return _row_to_out(row)


@router.post("/", response_model=ConnectionProfileOut, status_code=status.HTTP_201_CREATED)
async def create_connection_profile(
    request: CreateConnectionProfileRequest,
    pool: asyncpg.Pool = Depends(_get_pool),
):
    """Create a connection profile. Credentials are encrypted before storage."""
    encrypted = encrypt_credentials(request.credentials or {}) if request.credentials is not None else None
    new_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO connection_profiles
                    (id, client_id, name, source_system, host, port, database_name, schema_name,
                     credentials_encrypted, is_default, created_by, created_at, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$12)
                RETURNING *
                """,
                new_id,
                request.client_id,
                request.name,
                request.source_system,
                request.host,
                request.port,
                request.database_name,
                request.schema_name,
                encrypted,
                request.is_default,
                request.created_by,
                now,
            )
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A connection profile named '{request.name}' already exists for client '{request.client_id}'.",
        )

    logger.info("Created connection profile '%s' for client '%s'", request.name, request.client_id)
    return _row_to_out(row)


@router.put("/{profile_id}", response_model=ConnectionProfileOut)
async def update_connection_profile(
    profile_id: str,
    request: UpdateConnectionProfileRequest,
    pool: asyncpg.Pool = Depends(_get_pool),
):
    """Update a connection profile. Only sends encrypted credentials if new credentials provided."""
    row = await _fetch_owned(pool, profile_id, request.client_id)
    now = datetime.now(timezone.utc)

    name = request.name if request.name is not None else row["name"]
    host = request.host if request.host is not None else row["host"]
    port = request.port if request.port is not None else row["port"]
    db_name = request.database_name if request.database_name is not None else row["database_name"]
    schema = request.schema_name if request.schema_name is not None else row["schema_name"]
    is_default = request.is_default if request.is_default is not None else row["is_default"]
    last_used_by = request.last_used_by if request.last_used_by is not None else row["last_used_by"]

    if request.credentials is not None:
        encrypted = encrypt_credentials(request.credentials)
    else:
        encrypted = row["credentials_encrypted"]

    last_used_at = now if request.last_used_by is not None else row["last_used_at"]

    async with pool.acquire() as conn:
        updated = await conn.fetchrow(
            """
            UPDATE connection_profiles
               SET name=$2, host=$3, port=$4, database_name=$5, schema_name=$6,
                   credentials_encrypted=$7, is_default=$8, updated_at=$9,
                   last_used_at=$10, last_used_by=$11
             WHERE id=$1
            RETURNING *
            """,
            uuid.UUID(profile_id),
            name, host, port, db_name, schema,
            encrypted, is_default, now,
            last_used_at, last_used_by,
        )

    return _row_to_out(updated)


@router.delete("/{profile_id}", status_code=status.HTTP_200_OK)
async def delete_connection_profile(
    profile_id: str,
    client_id: str = Query(..., description="Tenant client ID for ownership verification"),
    pool: asyncpg.Pool = Depends(_get_pool),
):
    """Delete a connection profile. Verifies client_id ownership before deleting."""
    await _fetch_owned(pool, profile_id, client_id)

    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM connection_profiles WHERE id = $1",
            uuid.UUID(profile_id),
        )

    logger.info("Deleted connection profile '%s' for client '%s'", profile_id, client_id)
    return {"message": f"Connection profile '{profile_id}' deleted."}
