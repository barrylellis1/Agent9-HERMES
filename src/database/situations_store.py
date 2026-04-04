"""
Supabase persistence layer for detected situations and opportunities.

Follows the same httpx REST pattern as SupabaseBusinessContextProvider.
Falls back silently if SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set
(so local dev without Supabase configured continues to work).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

from src.agents.models.situation_awareness_models import OpportunitySignal, Situation

logger = logging.getLogger(__name__)

_TABLE = "situations"


def _stable_opportunity_id(opportunity: OpportunitySignal) -> str:
    """
    Generate a stable, deterministic ID for an OpportunitySignal.

    OpportunitySignal has no dedicated id field; we derive one from
    kpi_name + opportunity_type so that re-running SA on the same data
    produces the same ID and the upsert deduplicates correctly.
    """
    raw = f"{opportunity.kpi_name}::{opportunity.opportunity_type}"
    return "opp_" + hashlib.sha256(raw.encode()).hexdigest()[:32]


def _safe_json(obj: Any) -> Any:
    """Convert a Pydantic model (or nested structure) to a JSON-safe dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    return obj


class SituationsStore:
    """Thin async Supabase client for the situations table."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_service_key:
            logger.warning(
                "SituationsStore: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — "
                "situation persistence is disabled."
            )
            self.enabled = False
            return

        if httpx is None:
            logger.warning(
                "SituationsStore: httpx is not installed — situation persistence is disabled."
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

    async def upsert_situation(self, situation: Situation) -> bool:
        """
        Persist a problem Situation card to Supabase.

        Returns True on success, False on any failure.
        Re-running SA on the same data is safe: the upsert on situation_id
        is idempotent.
        """
        if not self.enabled:
            return False
        try:
            kpi_value_num: Optional[float] = None
            if situation.kpi_value is not None:
                kpi_value_num = getattr(situation.kpi_value, "value", None)

            row = {
                "id": situation.situation_id,
                "card_type": "problem",
                "kpi_id": situation.kpi_name,
                "kpi_name": situation.kpi_name,
                "severity": situation.severity.value if hasattr(situation.severity, "value") else str(situation.severity),
                "title": situation.description[:255] if situation.description else situation.kpi_name,
                "description": situation.description,
                "kpi_value": kpi_value_num,
                "status": "OPEN",
                "full_payload": _safe_json(situation),
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=row,
                )
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "SituationsStore.upsert_situation: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("SituationsStore.upsert_situation failed (non-fatal): %s", exc)
            return False

    async def upsert_opportunity(self, opportunity: OpportunitySignal) -> bool:
        """
        Persist an OpportunitySignal to Supabase.

        A stable ID is derived from kpi_name + opportunity_type so repeated
        SA runs produce the same ID and the upsert deduplicates.

        Returns True on success, False on any failure.
        """
        if not self.enabled:
            return False
        try:
            opp_id = _stable_opportunity_id(opportunity)

            row = {
                "id": opp_id,
                "card_type": "opportunity",
                "kpi_id": opportunity.kpi_name,
                "kpi_name": opportunity.kpi_name,
                "title": opportunity.headline[:255] if opportunity.headline else opportunity.kpi_name,
                "description": opportunity.headline,
                "kpi_value": opportunity.current_value,
                "deviation_pct": opportunity.delta_pct,
                "opportunity_type": opportunity.opportunity_type,
                "status": "OPEN",
                "full_payload": _safe_json(opportunity),
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=row,
                )
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "SituationsStore.upsert_opportunity: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("SituationsStore.upsert_opportunity failed (non-fatal): %s", exc)
            return False

    async def get_situation(self, situation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a situation or opportunity row by ID.

        Returns the full_payload dict if the row exists, or None if not found
        or on any error.
        """
        if not self.enabled:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{situation_id}", "select": "*"},
                )
                response.raise_for_status()
                rows = response.content and __import__("json").loads(response.content) or []
                if not rows:
                    return None
                row = rows[0]
                # Return the full row dict; caller can access full_payload from it
                return row
        except Exception as exc:
            logger.warning("SituationsStore.get_situation failed (non-fatal): %s", exc)
            return None

    async def update_status(
        self,
        situation_id: str,
        status: str,
        **kwargs: Any,
    ) -> bool:
        """
        Update the status column and any additional keyword fields
        (e.g. da_request_id="...", solution_id="...").

        Returns True on success, False on any failure.
        """
        if not self.enabled:
            return False
        try:
            patch_body: Dict[str, Any] = {"status": status}
            for key, value in kwargs.items():
                patch_body[key] = value

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    self.endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{situation_id}"},
                    json=patch_body,
                )
                if response.status_code not in (200, 204):
                    logger.warning(
                        "SituationsStore.update_status: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("SituationsStore.update_status failed (non-fatal): %s", exc)
            return False

    async def get_open_situations(
        self, principal_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Return all OPEN situation rows, optionally filtered by principal_id.

        Returns an empty list on any error.
        """
        if not self.enabled:
            return []
        try:
            params: Dict[str, Any] = {"status": "eq.OPEN", "select": "*"}
            if principal_id:
                params["principal_id"] = f"eq.{principal_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.endpoint,
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()
                return __import__("json").loads(response.content) if response.content else []
        except Exception as exc:
            logger.warning("SituationsStore.get_open_situations failed (non-fatal): %s", exc)
            return []
