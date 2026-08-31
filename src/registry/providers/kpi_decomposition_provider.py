"""Provider for the kpi_decompositions table (Phase 17 T2).

Mirrors kpi_relationship_provider.py's shape exactly (same shared asyncpg
pool via RegistryBootstrap, same lazy-pool pattern, not registered in
RegistryFactory) -- a decomposition edge and a causal-relationship edge are
both KPI-pair facts, just answering different questions (see
kpi_decomposition.py's module docstring for the distinction).
"""
from __future__ import annotations

import logging
from typing import Dict, List

import asyncpg

from src.database.tenant_scope import tenant_scope
from src.registry.models.kpi_decomposition import KPIDecompositionEdge

logger = logging.getLogger(__name__)


def _row_to_model(row: asyncpg.Record) -> KPIDecompositionEdge:
    return KPIDecompositionEdge(
        parent_kpi_id=row["parent_kpi_id"],
        child_kpi_id=row["child_kpi_id"],
        client_id=row["client_id"],
        operation=row["operation"],
        sign=row["sign"],
        weight_kpi_id=row["weight_kpi_id"],
    )


class KPIDecompositionProvider:
    """Direct asyncpg provider for the kpi_decompositions table.

    The pool is accessed lazily from RegistryBootstrap so this provider can
    be instantiated before the runtime is fully started.
    """

    def _pool(self) -> asyncpg.Pool:
        from src.registry.bootstrap import RegistryBootstrap

        pool = getattr(RegistryBootstrap._db_manager, "pool", None)
        if pool is None:
            raise RuntimeError(
                "KPIDecompositionProvider: database pool is not available — "
                "registry has not been initialized."
            )
        return pool

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_children(self, parent_kpi_id: str, client_id: str) -> List[KPIDecompositionEdge]:
        """Direct children of `parent_kpi_id` only -- one level, not the full tree."""
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM kpi_decompositions
                WHERE client_id = $1 AND parent_kpi_id = $2
                ORDER BY child_kpi_id
                """,
                client_id,
                parent_kpi_id,
            )
        return [_row_to_model(r) for r in rows]

    async def get_full_tree(
        self, root_kpi_id: str, client_id: str, max_depth: int = 5,
    ) -> List[KPIDecompositionEdge]:
        """Every edge reachable by walking DOWN from `root_kpi_id` through children.

        Bounded by `max_depth` so a (data-entry-error) cycle cannot loop
        forever; a KPI already visited as a parent on this walk is not
        re-expanded, matching get_causal_neighbourhood's own cycle handling.
        """
        edges = await self.get_all(client_id)
        if not edges:
            return []

        by_parent: Dict[str, List[KPIDecompositionEdge]] = {}
        for e in edges:
            by_parent.setdefault(e.parent_kpi_id, []).append(e)

        out: List[KPIDecompositionEdge] = []
        visited_parents: set = set()
        frontier = [root_kpi_id]

        for _ in range(max_depth):
            if not frontier:
                break
            next_frontier: List[str] = []
            for node in frontier:
                if node in visited_parents:
                    continue
                visited_parents.add(node)
                for e in by_parent.get(node, []):
                    out.append(e)
                    next_frontier.append(e.child_kpi_id)
            frontier = next_frontier

        return out

    async def get_all(self, client_id: str) -> List[KPIDecompositionEdge]:
        """Return all decomposition edges for a client (strict match, RLS-scoped)."""
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM kpi_decompositions WHERE client_id = $1 ORDER BY parent_kpi_id",
                client_id,
            )
        return [_row_to_model(r) for r in rows]

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    async def upsert(self, item: KPIDecompositionEdge) -> KPIDecompositionEdge:
        """Insert or update on composite PK (client_id, parent_kpi_id, child_kpi_id)."""
        async with self._pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO kpi_decompositions
                    (parent_kpi_id, child_kpi_id, client_id, operation, sign, weight_kpi_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (client_id, parent_kpi_id, child_kpi_id) DO UPDATE SET
                    operation = EXCLUDED.operation,
                    sign = EXCLUDED.sign,
                    weight_kpi_id = EXCLUDED.weight_kpi_id
                RETURNING *
                """,
                item.parent_kpi_id,
                item.child_kpi_id,
                item.client_id,
                item.operation,
                item.sign,
                item.weight_kpi_id,
            )
        logger.info(
            "Upserted KPI decomposition edge '%s' -> '%s' (%s) for client '%s'",
            item.parent_kpi_id, item.child_kpi_id, item.operation, item.client_id,
        )
        return _row_to_model(row)

    async def delete(self, parent_kpi_id: str, child_kpi_id: str, client_id: str) -> bool:
        async with self._pool().acquire() as conn:
            result = await conn.execute(
                "DELETE FROM kpi_decompositions WHERE client_id = $1 AND parent_kpi_id = $2 AND child_kpi_id = $3",
                client_id, parent_kpi_id, child_kpi_id,
            )
        deleted = result.endswith("1")
        if deleted:
            logger.info(
                "Deleted KPI decomposition edge '%s' -> '%s' for client '%s'",
                parent_kpi_id, child_kpi_id, client_id,
            )
        return deleted
