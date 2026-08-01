"""Provider for the assumptions table (Phase 15 Stage D/E).

Uses the shared asyncpg pool from RegistryBootstrap — same lazy pool pattern
as KPIRelationshipProvider. Instantiated directly where needed; not
registered in RegistryFactory.
"""
from __future__ import annotations

import logging
from typing import List, Optional

import asyncpg

from src.database.tenant_scope import tenant_scope
from src.registry.models.assumption import Assumption

logger = logging.getLogger(__name__)


def _row_to_model(row: asyncpg.Record) -> Assumption:
    return Assumption(
        id=str(row["id"]),
        client_id=row["client_id"],
        scope=row["scope"],
        record_type=row["record_type"],
        text=row["text"],
        status=row["status"],
        source=row["source"],
        provenance=row["provenance"],
        confidence=row["confidence"],
        validated_by=row["validated_by"],
        falsification_criterion=row["falsification_criterion"],
        expiry=row["expiry"].isoformat() if row["expiry"] else None,
        linked_situation_id=row["linked_situation_id"],
        linked_solution_id=row["linked_solution_id"],
        created_at=row["created_at"].isoformat() if row["created_at"] else None,
        updated_at=row["updated_at"].isoformat() if row["updated_at"] else None,
    )


class AssumptionProvider:
    """Direct asyncpg provider for the assumptions table.

    The pool is accessed lazily from RegistryBootstrap so this provider
    can be instantiated before the runtime is fully started.
    """

    def _pool(self) -> asyncpg.Pool:
        from src.registry.bootstrap import RegistryBootstrap

        pool = getattr(RegistryBootstrap._db_manager, "pool", None)
        if pool is None:
            raise RuntimeError(
                "AssumptionProvider: database pool is not available — "
                "registry has not been initialized."
            )
        return pool

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_active_constraints(
        self, client_id: str, scope: Optional[str] = None
    ) -> List[Assumption]:
        """Return active constraint records for a client, optionally scoped
        to a specific KPI/threshold identifier. Constraints are permanent
        prohibitions (record_type='constraint', status='active') — see
        theory_layer_design.md §5.2."""
        async with tenant_scope(self._pool(), client_id) as conn:
            if scope:
                rows = await conn.fetch(
                    """
                    SELECT * FROM assumptions
                    WHERE client_id = $1 AND record_type = 'constraint' AND status = 'active'
                      AND (scope = $2 OR scope = 'client')
                    ORDER BY created_at DESC
                    """,
                    client_id,
                    scope,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM assumptions
                    WHERE client_id = $1 AND record_type = 'constraint' AND status = 'active'
                    ORDER BY created_at DESC
                    """,
                    client_id,
                )
        return [_row_to_model(r) for r in rows]

    async def get_for_solution(self, solution_id: str, client_id: str) -> List[Assumption]:
        """Return every assumption registered against a solution.

        The grading query: at VA evaluation these are the claims that were
        pre-registered at approval, before the outcome was known.
        """
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM assumptions
                WHERE client_id = $1 AND linked_solution_id = $2
                ORDER BY created_at
                """,
                client_id,
                solution_id,
            )
        return [_row_to_model(r) for r in rows]

    async def get_all(self, client_id: str) -> List[Assumption]:
        """Return all assumption/constraint/explanation records for a client (RLS-scoped)."""
        async with tenant_scope(self._pool(), client_id) as conn:
            rows = await conn.fetch(
                "SELECT * FROM assumptions WHERE client_id = $1 ORDER BY created_at DESC",
                client_id,
            )
        return [_row_to_model(r) for r in rows]

    # ------------------------------------------------------------------
    # Write methods
    # ------------------------------------------------------------------

    async def upsert(self, item: Assumption) -> Assumption:
        """Insert a new record, or update an existing one by id.

        No accretion/extraction pipeline calls this yet — theory §5.2's
        SF-rejection-to-constraint extraction stays gated on tenant-isolation
        tests + a pilot with real SF usage. This is standard CRUD plumbing,
        usable for manual/admin-entered records today.
        """
        async with self._pool().acquire() as conn:
            if item.id:
                row = await conn.fetchrow(
                    """
                    UPDATE assumptions SET
                        scope = $2, record_type = $3, text = $4, status = $5,
                        source = $6, provenance = $7, confidence = $8, expiry = $9,
                        linked_situation_id = $10, linked_solution_id = $11,
                        validated_by = $12, falsification_criterion = $13,
                        updated_at = NOW()
                    WHERE id = $1
                    RETURNING *
                    """,
                    item.id, item.scope, item.record_type, item.text, item.status,
                    item.source, item.provenance, item.confidence, item.expiry,
                    item.linked_situation_id, item.linked_solution_id,
                    item.validated_by, item.falsification_criterion,
                )
            else:
                # ON CONFLICT targets uq_assumptions_solution_text — approving the
                # same solution twice must not double-register its bets, which
                # would double-count at grading time. DO UPDATE rather than DO
                # NOTHING so a re-approval refreshes the claim, and so RETURNING
                # still yields a row (DO NOTHING returns none on conflict, which
                # would surface here as a confusing None-row crash).
                #
                # `status` is deliberately NOT in the SET list: if this bet has
                # already been graded held/falsified, a re-approval must not
                # silently reset it to 'active' and erase the verdict. Same for
                # source/provenance — the original capture context is what it is.
                row = await conn.fetchrow(
                    """
                    INSERT INTO assumptions
                        (client_id, scope, record_type, text, status, source,
                         provenance, confidence, expiry, linked_situation_id, linked_solution_id,
                         validated_by, falsification_criterion)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (linked_solution_id, text) WHERE linked_solution_id IS NOT NULL
                    DO UPDATE SET
                        scope = EXCLUDED.scope,
                        confidence = EXCLUDED.confidence,
                        validated_by = EXCLUDED.validated_by,
                        falsification_criterion = EXCLUDED.falsification_criterion,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    item.client_id, item.scope, item.record_type, item.text, item.status,
                    item.source, item.provenance, item.confidence, item.expiry,
                    item.linked_situation_id, item.linked_solution_id,
                    item.validated_by, item.falsification_criterion,
                )
        logger.info(
            "Upserted assumption record type=%s scope=%s for client '%s'",
            item.record_type, item.scope, item.client_id,
        )
        return _row_to_model(row)

    async def delete(self, id: str, client_id: str) -> bool:
        """Delete an assumption/constraint/explanation record by id.

        Returns True if a row was deleted.
        """
        async with self._pool().acquire() as conn:
            result = await conn.execute(
                "DELETE FROM assumptions WHERE id = $1 AND client_id = $2",
                id,
                client_id,
            )
        deleted = result != "DELETE 0"
        if deleted:
            logger.info("Deleted assumption %s for client '%s'", id, client_id)
        return deleted
