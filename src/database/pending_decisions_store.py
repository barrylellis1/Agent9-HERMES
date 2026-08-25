"""
Supabase persistence layer for solutions awaiting a decision-maker's sign-off.

Follows the same httpx REST pattern as SituationsStore / VASolutionsStore.
Falls back silently if SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set
(so local dev without Supabase configured continues to work).

Why this table exists: before this, "awaiting a decision" was a same-payload
flag (SolutionFinderResponse.human_action_required) living only in
workflows.py's in-memory _workflow_store, with no endpoint listing it by
principal. This store is the durable record that flag needed --
docs/architecture/decision_framer_and_decision_maker_personas_design.md.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)

_TABLE = "sf_pending_decisions"


class PendingDecisionsStore:
    """Thin async Supabase client for the sf_pending_decisions table."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_service_key:
            logger.warning(
                "PendingDecisionsStore: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — "
                "pending-decision persistence is disabled."
            )
            self.enabled = False
            return

        if httpx is None:
            logger.warning(
                "PendingDecisionsStore: httpx is not installed — pending-decision persistence is disabled."
            )
            self.enabled = False
            return

        self.enabled = True
        self.endpoint = f"{self.supabase_url}/rest/v1/{_TABLE}"
        self.headers = {
            "apikey": self.supabase_service_key,
            "Authorization": f"Bearer {self.supabase_service_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_pending(
        self,
        *,
        request_id: str,
        client_id: str,
        principal_id: str,
        situation_id: Optional[str] = None,
        kpi_id: Optional[str] = None,
        human_action_type: Optional[str] = None,
        summary: Optional[str] = None,
        human_action_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record that an SF run completed and is awaiting the principal's
        decision. Idempotent on request_id (unique) via upsert -- a re-run
        of the same request_id (should not normally happen) replaces rather
        than duplicates.

        Returns True on success, False on any failure. Never raises -- a
        persistence failure here must not fail the SF workflow response
        that triggered it.
        """
        if not self.enabled:
            return False
        try:
            row = {
                "request_id": request_id,
                "client_id": client_id,
                "principal_id": principal_id,
                "situation_id": situation_id,
                "kpi_id": kpi_id,
                "human_action_type": human_action_type,
                "summary": summary,
                "human_action_context": human_action_context,
                "resolved": False,
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=row,
                )
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "PendingDecisionsStore.create_pending: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("PendingDecisionsStore.create_pending failed (non-fatal): %s", exc)
            return False

    async def resolve(self, request_id: str, action: str) -> bool:
        """
        Mark a pending decision resolved (approve / request-changes / iterate).

        Returns True on success, False on any failure (including "no such
        row" -- a decision that was never persisted, e.g. store was
        disabled when SF completed, is not itself an error worth raising).
        """
        if not self.enabled:
            return False
        try:
            from datetime import datetime, timezone

            patch_body = {
                "resolved": True,
                "resolved_action": action,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            }
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    self.endpoint,
                    headers=self.headers,
                    params={"request_id": f"eq.{request_id}"},
                    json=patch_body,
                )
                if response.status_code not in (200, 204):
                    logger.warning(
                        "PendingDecisionsStore.resolve: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("PendingDecisionsStore.resolve failed (non-fatal): %s", exc)
            return False

    async def list_unresolved(self, principal_id: str, client_id: str) -> List[Dict[str, Any]]:
        """
        Return unresolved pending-decision rows for a principal, newest first.

        Returns an empty list on any error -- callers (the landing view)
        must treat "nothing pending" and "lookup failed" the same way:
        show an empty queue, never crash the page.
        """
        if not self.enabled:
            return []
        try:
            params: Dict[str, Any] = {
                "principal_id": f"eq.{principal_id}",
                "client_id": f"eq.{client_id}",
                "resolved": "eq.false",
                "select": "*",
                "order": "created_at.desc",
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(self.endpoint, headers=self.headers, params=params)
                response.raise_for_status()
                return json.loads(response.content) if response.content else []
        except Exception as exc:
            logger.warning("PendingDecisionsStore.list_unresolved failed (non-fatal): %s", exc)
            return []
