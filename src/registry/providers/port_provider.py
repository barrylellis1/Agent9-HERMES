"""Provider for the ports table (Phase 17 T4).

Mirrors assumption_provider.py's shape (shared lazy asyncpg pool via
RegistryBootstrap, not registered in RegistryFactory) -- a port is the same
kind of thing as an assumption: a registered fact about this client, with a
provenance, that a human or a future automated query populates.
"""
from __future__ import annotations

import logging
from typing import List, Optional

import asyncpg

from src.database.tenant_scope import tenant_scope
from src.registry.models.port import Port

logger = logging.getLogger(__name__)


def _row_to_model(row: asyncpg.Record) -> Port:
    return Port(
        id=str(row["id"]),
        client_id=row["client_id"],
        name=row["name"],
        port_type=row["port_type"],
        linked_kpi_id=row["linked_kpi_id"],
        lag_periods=row["lag_periods"],
        buffer_description=row["buffer_description"],
        current_signal=row["current_signal"],
        source=row["source"],
    )


class PortProvider:
    """Direct asyncpg provider for the ports table.

    The pool is accessed lazily from RegistryBootstrap so this provider can
    be instantiated before the runtime is fully started.
    """

    def _pool(self) -> asyncpg.Pool:
        from src.registry.bootstrap import RegistryBootstrap

        pool = getattr(RegistryBootstrap._db_manager, "pool", None)
        if pool is None:
            raise RuntimeError(
                "PortProvider: database pool is not available — registry has not been initialized."
            )
        return pool

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_for_kpi(self, kpi_id: str, client_id: str) -> List[Port]:
        """Every port attached to `kpi_id` -- the branch the Core Spine exhibit
        would attach these to."""
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM ports WHERE client_id = $1 AND linked_kpi_id = $2 ORDER BY port_type",
                client_id, kpi_id,
            )
        return [_row_to_model(r) for r in rows]

    async def get_all(self, client_id: str) -> List[Port]:
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM ports WHERE client_id = $1 ORDER BY linked_kpi_id, port_type",
                client_id,
            )
        return [_row_to_model(r) for r in rows]

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    async def upsert(self, item: Port) -> Port:
        """Insert or update on (client_id, linked_kpi_id, port_type) -- a KPI
        has at most one port of a given type."""
        async with self._pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ports
                    (client_id, name, port_type, linked_kpi_id, lag_periods,
                     buffer_description, current_signal, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (client_id, linked_kpi_id, port_type) DO UPDATE SET
                    name = EXCLUDED.name,
                    lag_periods = EXCLUDED.lag_periods,
                    buffer_description = EXCLUDED.buffer_description,
                    current_signal = EXCLUDED.current_signal,
                    source = EXCLUDED.source,
                    updated_at = NOW()
                RETURNING *
                """,
                item.client_id, item.name, item.port_type, item.linked_kpi_id,
                item.lag_periods, item.buffer_description, item.current_signal, item.source,
            )
        logger.info(
            "Upserted port '%s' (%s) on KPI '%s' for client '%s'",
            item.name, item.port_type, item.linked_kpi_id, item.client_id,
        )
        return _row_to_model(row)

    async def delete(self, id: str, client_id: str) -> bool:
        async with self._pool().acquire() as conn:
            result = await conn.execute(
                "DELETE FROM ports WHERE id = $1 AND client_id = $2", id, client_id,
            )
        deleted = result != "DELETE 0"
        if deleted:
            logger.info("Deleted port %s for client '%s'", id, client_id)
        return deleted
