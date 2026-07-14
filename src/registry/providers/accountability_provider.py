"""Provider for the kpi_accountability table.

Uses the shared asyncpg pool from RegistryBootstrap (same pattern as
src/api/routes/connection_profiles.py) rather than the generic
DatabaseRegistryProvider, because kpi_accountability has explicit columns
and no JSON blob.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

import asyncpg

from src.database.tenant_scope import tenant_scope
from src.registry.models.kpi_accountability import AccountabilityRole, KPIAccountability

logger = logging.getLogger(__name__)


def _row_to_model(row: asyncpg.Record) -> KPIAccountability:
    return KPIAccountability(
        id=row["id"],
        client_id=row["client_id"],
        kpi_id=row["kpi_id"],
        principal_id=row["principal_id"],
        scope_dimension=row["scope_dimension"],
        scope_value=row["scope_value"],
        role=AccountabilityRole(row["role"]),
        notes=row["notes"],
        created_by=row["created_by"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class KPIAccountabilityProvider:
    """Direct asyncpg provider for the kpi_accountability table.

    The pool is accessed lazily from RegistryBootstrap so this provider
    can be instantiated before the runtime is fully started.
    """

    def _pool(self) -> asyncpg.Pool:
        from src.registry.bootstrap import RegistryBootstrap

        pool = getattr(RegistryBootstrap._db_manager, "pool", None)
        if pool is None:
            raise RuntimeError(
                "KPIAccountabilityProvider: database pool is not available — "
                "registry has not been initialized."
            )
        return pool

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_all(self, client_id: str) -> List[KPIAccountability]:
        """Return all accountability records for a client (strict match, RLS-scoped)."""
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM kpi_accountability WHERE client_id = $1 ORDER BY kpi_id, role",
                client_id,
            )
        return [_row_to_model(r) for r in rows]

    async def get_for_principal(
        self, client_id: str, principal_id: str
    ) -> List[KPIAccountability]:
        """Return accountability records for a specific principal."""
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM kpi_accountability WHERE client_id = $1 AND principal_id = $2 ORDER BY kpi_id",
                client_id,
                principal_id,
            )
        return [_row_to_model(r) for r in rows]

    async def get_for_kpi(self, client_id: str, kpi_id: str) -> List[KPIAccountability]:
        """Return accountability records for a specific KPI."""
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM kpi_accountability WHERE client_id = $1 AND kpi_id = $2 ORDER BY role",
                client_id,
                kpi_id,
            )
        return [_row_to_model(r) for r in rows]

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    async def upsert(self, item: KPIAccountability) -> KPIAccountability:
        """Insert or update an accountability record.

        Conflicts on the composite unique key (client_id, kpi_id, scope_dimension,
        scope_value) are resolved by updating all mutable fields.
        The primary key (client_id, id) is used for the ON CONFLICT clause.
        """
        now = datetime.now(timezone.utc)
        async with self._pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO kpi_accountability
                    (id, client_id, kpi_id, principal_id, scope_dimension, scope_value,
                     role, notes, created_by, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $10)
                ON CONFLICT (client_id, id) DO UPDATE SET
                    principal_id   = EXCLUDED.principal_id,
                    scope_dimension = EXCLUDED.scope_dimension,
                    scope_value    = EXCLUDED.scope_value,
                    role           = EXCLUDED.role,
                    notes          = EXCLUDED.notes,
                    updated_at     = EXCLUDED.updated_at
                RETURNING *
                """,
                item.id,
                item.client_id,
                item.kpi_id,
                item.principal_id,
                item.scope_dimension,
                item.scope_value,
                item.role.value,
                item.notes,
                item.created_by,
                now,
            )
        logger.info(
            "Upserted accountability record '%s' for client '%s' (kpi=%s, principal=%s, role=%s)",
            item.id,
            item.client_id,
            item.kpi_id,
            item.principal_id,
            item.role.value,
        )
        return _row_to_model(row)

    async def delete(self, client_id: str, record_id: str) -> bool:
        """Delete an accountability record.  Returns True if a row was deleted."""
        async with self._pool().acquire() as conn:
            result = await conn.execute(
                "DELETE FROM kpi_accountability WHERE client_id = $1 AND id = $2",
                client_id,
                record_id,
            )
        # asyncpg returns 'DELETE N' where N is the row count
        deleted = result.endswith("1")
        if deleted:
            logger.info("Deleted accountability record '%s' for client '%s'", record_id, client_id)
        return deleted
