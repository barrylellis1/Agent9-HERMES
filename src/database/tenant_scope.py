"""Tenant-scoped database access (Infra B3).

Runs queries under the RLS-enforced ``a9_tenant_scope`` role with the
``app.client_id`` GUC set for the transaction, so the database — not
application code — guarantees that only the tenant's rows are visible.
The RLS policies are fail-closed: with the GUC unset the tenant role
sees zero rows.

Requires migration ``supabase/migrations/20260713_rls_client_isolation.sql``.
If the role is not present (migration not yet applied to this database),
queries fall back to the pool's normal role with a loud error log. Callers
keep their strict ``WHERE client_id = $1`` filters, so the fallback is never
more permissive than pre-B3 behavior — it only loses the database-level
guarantee until the migration is applied.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import asyncpg

logger = logging.getLogger(__name__)

TENANT_ROLE = "a9_tenant_scope"

# Tri-state cache: None = not probed yet, True/False = probe result.
_role_available: Optional[bool] = None


def reset_role_probe() -> None:
    """Forget the cached probe result (test hook / after applying migration)."""
    global _role_available
    _role_available = None


async def _probe_role(conn: asyncpg.Connection) -> bool:
    """Check once whether the RLS tenant role exists and is grantable."""
    global _role_available
    if _role_available is None:
        try:
            async with conn.transaction():
                await conn.execute(f"SET LOCAL ROLE {TENANT_ROLE}")
            _role_available = True
        except asyncpg.PostgresError as e:
            logger.error(
                "Infra B3: RLS tenant role '%s' unavailable (%s). Database-level "
                "isolation is NOT active — apply migration "
                "20260713_rls_client_isolation.sql. Falling back to "
                "application-layer client_id filtering.",
                TENANT_ROLE,
                e,
            )
            _role_available = False
    return _role_available


@asynccontextmanager
async def tenant_scope(
    pool: asyncpg.Pool, client_id: str
) -> AsyncIterator[asyncpg.Connection]:
    """Yield a connection whose transaction is RLS-scoped to ``client_id``.

    All statements executed on the yielded connection run inside a single
    transaction as ``a9_tenant_scope`` with ``app.client_id`` set, so RLS
    limits visibility to the tenant's rows regardless of the SQL itself.
    """
    if not client_id:
        raise ValueError("tenant_scope requires a non-empty client_id (fail-closed)")
    async with pool.acquire() as conn:
        use_rls = await _probe_role(conn)
        async with conn.transaction():
            if use_rls:
                await conn.execute(f"SET LOCAL ROLE {TENANT_ROLE}")
                await conn.execute(
                    "SELECT set_config('app.client_id', $1, true)", client_id
                )
            yield conn
