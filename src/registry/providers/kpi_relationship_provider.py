"""Provider for the kpi_relationships table (Phase 11I-B).

Uses the shared asyncpg pool from RegistryBootstrap — same lazy pool pattern
as KPIAccountabilityProvider.  Instantiated directly where needed; not
registered in RegistryFactory.
"""
from __future__ import annotations

import logging
from typing import List

import asyncpg

from src.database.tenant_scope import tenant_scope
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
        # Phase 15 Stage D/E causal typing — must be mapped here or reads
        # silently drop real DB values back to Pydantic field defaults.
        mechanism=row["mechanism"],
        lag_periods=row["lag_periods"],
        causal_rung=row["causal_rung"],
        provenance=row["provenance"],
        confidence=row["confidence"],
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
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM kpi_relationships
                WHERE client_id = $1 AND (kpi_id = $2 OR related_kpi_id = $2)
                """,
                client_id,
                kpi_id,
            )
        return [_row_to_model(r) for r in rows]

    async def get_causal_neighbourhood(
        self,
        kpi_id: str,
        client_id: str,
        max_hops: int = 2,
        max_edges: int = 25,
    ) -> List[tuple]:
        """Walk outward from `kpi_id`, returning [(KPIRelationship, hops), ...].

        WHY THIS EXISTS
        ---------------
        `get_relationships_for_kpi` returns only edges that TOUCH the KPI. That is
        correct for SA's compound-alert detection (two KPIs breaching together are
        directly related) and for the registry API, but it is one hop short for
        Solution Finding.

        Measured on the lubricants seed (2026-08-12): of six edges, only three
        touch `gross_margin_pct`. The invisible three include
        `base_oil_cost -> cogs` — the "11F anchor scenario", carrying the single
        most important causal fact for that client (base oil is ~41% of COGS and
        passes through with a one-month inventory-buffered lag). The real chain is
        `base_oil_cost -> cogs -> gross_margin_pct`: two hops. A margin analysis
        could never see the cause of its own margin problem.

        Edges are undirected for traversal (the schema is bidirectional for
        detection purposes), and `hops` is the shortest distance found — so a
        consumer can weight a 2-hop inference below a direct one. Prompts MUST
        surface that distance rather than flattening it: a two-hop chain is
        weaker evidence, and presenting it as equivalent would manufacture
        confidence the graph does not support.

        Bounded twice: `max_hops` (default 2) and `max_edges` (default 25), so a
        dense graph cannot flood a prompt. Cycles are handled — a KPI is expanded
        at most once, at its shortest distance.
        """
        edges = await self.get_all(client_id)
        if not edges:
            return []

        adjacency: Dict[str, List[KPIRelationship]] = {}
        for e in edges:
            adjacency.setdefault(e.kpi_id, []).append(e)
            adjacency.setdefault(e.related_kpi_id, []).append(e)

        out: List[tuple] = []
        seen_edges: set = set()
        visited: set = {kpi_id}
        frontier = [kpi_id]

        for hop in range(1, max_hops + 1):
            next_frontier: List[str] = []
            for node in frontier:
                for e in adjacency.get(node, []):
                    key = (e.kpi_id, e.related_kpi_id, e.relationship_type)
                    if key in seen_edges:
                        continue
                    seen_edges.add(key)
                    out.append((e, hop))
                    if len(out) >= max_edges:
                        logger.info(
                            "Causal neighbourhood for '%s' truncated at %d edges (max_hops=%d)",
                            kpi_id, max_edges, max_hops,
                        )
                        return out
                    for other in (e.kpi_id, e.related_kpi_id):
                        if other not in visited:
                            visited.add(other)
                            next_frontier.append(other)
            frontier = next_frontier
            if not frontier:
                break

        return out

    async def get_all(self, client_id: str) -> List[KPIRelationship]:
        """Return all relationships for a client (strict match, RLS-scoped)."""
        async with tenant_scope(self._pool(), client_id) as conn:
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
                    (kpi_id, related_kpi_id, client_id, relationship_type, conflict_direction, description,
                     mechanism, lag_periods, causal_rung, provenance, confidence)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (client_id, kpi_id, related_kpi_id) DO UPDATE SET
                    relationship_type = EXCLUDED.relationship_type,
                    conflict_direction = EXCLUDED.conflict_direction,
                    description = EXCLUDED.description,
                    mechanism = EXCLUDED.mechanism,
                    lag_periods = EXCLUDED.lag_periods,
                    causal_rung = EXCLUDED.causal_rung,
                    provenance = EXCLUDED.provenance,
                    confidence = EXCLUDED.confidence
                RETURNING *
                """,
                item.kpi_id,
                item.related_kpi_id,
                item.client_id,
                item.relationship_type,
                item.conflict_direction,
                item.description,
                item.mechanism,
                item.lag_periods,
                item.causal_rung,
                item.provenance,
                item.confidence,
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
