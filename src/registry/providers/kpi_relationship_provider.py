"""Provider for the kpi_relationships table (Phase 11I-B).

Uses the shared asyncpg pool from RegistryBootstrap — same lazy pool pattern
as KPIAccountabilityProvider.  Instantiated directly where needed; not
registered in RegistryFactory.
"""
from __future__ import annotations

import logging
from typing import List

import asyncpg

from src.registry.models.kpi_relationship import KPIRelationship

logger = logging.getLogger(__name__)


def _row_to_model(row: asyncpg.Record) -> KPIRelationship:
    return KPIRelationship(
        kpi_id=row["kpi_id"],
        related_kpi_id=row["related_kpi_id"],
        client_id=row["client_id"],
        relationship_type=row["relationship_type"],
        conflict_direction=row["conflict_direction"],
        description=row["description"],
    )


class KPIRelationshipProvider:
    """Direct asyncpg provider for the kpi_relationships table.

    The pool is accessed lazily from RegistryBootstrap so this provider
    can be instantiated before the runtime is fully started.
    """

    def _pool(self) -> asyncpg.Pool:
        from src.registry.bootstrap import RegistryBootstrap

        pool = getattr(RegistryBootstrap._db_manager, "pool", None)
        if pool is None:
            raise RuntimeError(
                "KPIRelationshipProvider: database pool is not available — "
                "registry has not been initialized."
            )
        return pool

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_relationships_for_kpi(
        self, kpi_id: str, client_id: str
    ) -> List[KPIRelationship]:
        """Return all relationships where kpi_id OR related_kpi_id matches.

        The relationship is bidirectional for detection purposes.
        """
        async with self._pool().acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM kpi_relationships
                WHERE client_id = $1 AND (kpi_id = $2 OR related_kpi_id = $2)
                """,
                client_id,
                kpi_id,
            )
        return [_row_to_model(r) for r in rows]

    async def get_all(self, client_id: str) -> List[KPIRelationship]:
        """Return all relationships for a client (strict match)."""
        async with self._pool().acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM kpi_relationships WHERE client_id = $1 ORDER BY kpi_id",
                client_id,
            )
        return [_row_to_model(r) for r in rows]

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    async def upsert(self, item: KPIRelationship) -> KPIRelationship:
        """Insert or update a KPI relationship on composite PK (client_id, kpi_id, related_kpi_id)."""
        async with self._pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO kpi_relationships
                    (kpi_id, related_kpi_id, client_id, relationship_type, conflict_direction, description)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (client_id, kpi_id, related_kpi_id) DO UPDATE SET
                    relationship_type = EXCLUDED.relationship_type,
                    conflict_direction = EXCLUDED.conflict_direction,
                    description = EXCLUDED.description
                RETURNING *
                """,
                item.kpi_id,
                item.related_kpi_id,
                item.client_id,
                item.relationship_type,
                item.conflict_direction,
                item.description,
            )
        logger.info(
            "Upserted KPI relationship '%s' ↔ '%s' for client '%s'",
            item.kpi_id,
            item.related_kpi_id,
            item.client_id,
        )
        return _row_to_model(row)

    async def delete(self, kpi_id: str, related_kpi_id: str, client_id: str) -> bool:
        """Delete a relationship by composite key (tries both orderings).

        Returns True if at least one row was deleted.
        """
        deleted = False
        async with self._pool().acquire() as conn:
            async with conn.transaction():
                result1 = await conn.execute(
                    "DELETE FROM kpi_relationships WHERE client_id = $1 AND kpi_id = $2 AND related_kpi_id = $3",
                    client_id,
                    kpi_id,
                    related_kpi_id,
                )
                result2 = await conn.execute(
                    "DELETE FROM kpi_relationships WHERE client_id = $1 AND kpi_id = $2 AND related_kpi_id = $3",
                    client_id,
                    related_kpi_id,
                    kpi_id,
                )
        # asyncpg returns 'DELETE N' where N is the row count
        deleted = result1.endswith("1") or result2.endswith("1")
        if deleted:
            logger.info(
                "Deleted KPI relationship '%s' ↔ '%s' for client '%s'",
                kpi_id,
                related_kpi_id,
                client_id,
            )
        return deleted
