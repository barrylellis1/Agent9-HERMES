"""
Supabase persistence layer for Value Assurance solutions and evaluations.

Follows the same httpx REST pattern as SituationsStore (situations_store.py):
- env-var gated (SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY)
- non-fatal: all failures log a warning and return False / None / []
- one httpx.AsyncClient() per request (async context manager)
- Upsert via POST with "Prefer": "resolution=merge-duplicates"
- PATCH for updates
- GET with query-string params for reads

Tables
------
  value_assurance_solutions    — one row per AcceptedSolution
  value_assurance_evaluations  — one row per ImpactEvaluation
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

from src.agents.models.value_assurance_models import AcceptedSolution, ImpactEvaluation

logger = logging.getLogger(__name__)

_SOLUTIONS_TABLE = "value_assurance_solutions"
_EVALUATIONS_TABLE = "value_assurance_evaluations"


def _safe_json(obj: Any) -> Any:
    """Convert a Pydantic model (or nested structure) to a JSON-safe dict."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


class VASolutionsStore:
    """Thin async Supabase client for value_assurance_solutions and value_assurance_evaluations."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_service_key:
            logger.warning(
                "VASolutionsStore: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — "
                "VA solution persistence is disabled."
            )
            self.enabled = False
            return

        if httpx is None:
            logger.warning(
                "VASolutionsStore: httpx is not installed — VA solution persistence is disabled."
            )
            self.enabled = False
            return

        self.enabled = True
        self.solutions_endpoint = f"{self.supabase_url}/rest/v1/{_SOLUTIONS_TABLE}"
        self.evaluations_endpoint = f"{self.supabase_url}/rest/v1/{_EVALUATIONS_TABLE}"
        self.headers = {
            "apikey": self.supabase_service_key,
            "Authorization": f"Bearer {self.supabase_service_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Solutions
    # ------------------------------------------------------------------

    async def upsert_solution(self, solution: AcceptedSolution) -> bool:
        """
        Persist an AcceptedSolution to value_assurance_solutions.

        The upsert on solution_id is idempotent — re-registering the same
        solution (e.g. after a status change) is safe.

        Returns True on success, False on any failure.
        """
        if not self.enabled:
            return False
        try:
            row: Dict[str, Any] = {
                "id": solution.solution_id,
                "situation_id": solution.situation_id,
                "kpi_id": solution.kpi_id,
                "principal_id": solution.principal_id,
                "client_id": getattr(solution, "client_id", None),
                "approved_at": solution.approved_at,
                "solution_description": solution.solution_description,
                "expected_impact_lower": solution.expected_impact_lower,
                "expected_impact_upper": solution.expected_impact_upper,
                "measurement_window_days": solution.measurement_window_days,
                # Enum → string
                "status": solution.status.value
                if hasattr(solution.status, "value")
                else str(solution.status),
                # JSONB columns
                "strategy_snapshot": _safe_json(solution.strategy_snapshot),
                "ma_market_signals": solution.ma_market_signals,
                "narrative": solution.narrative,
                # --- Trend / DiD fields (added progressively; use getattr for safety) ---
                "inaction_trend": _safe_json(getattr(solution, "inaction_trend", None)),
                "expected_trend": _safe_json(getattr(solution, "expected_trend", None)),
                "actual_trend": getattr(solution, "actual_trend", None),
                "actual_trend_dates": getattr(solution, "actual_trend_dates", None),
                "baseline_kpi_value": getattr(solution, "baseline_kpi_value", None),
                "pre_approval_slope": getattr(solution, "pre_approval_slope", None),
                "inaction_horizon_months": getattr(solution, "inaction_horizon_months", None),
                "control_group_segments": _safe_json(
                    getattr(solution, "control_group_segments", None)
                ),
                "benchmark_segments": _safe_json(
                    getattr(solution, "benchmark_segments", None)
                ),
                # Lifecycle phase (Phase 11)
                "phase": getattr(solution, "phase", None)
                and (solution.phase.value if hasattr(solution.phase, "value") else str(solution.phase)),
                "go_live_at": getattr(solution, "go_live_at", None),
                "completed_at": getattr(solution, "completed_at", None),
            }

            # Drop None values for trend fields that aren't yet on the model
            # so we don't send null writes for columns that may not exist yet.
            row = {k: v for k, v in row.items() if v is not None or k in {
                "ma_market_signals", "narrative",
                "expected_impact_lower", "expected_impact_upper",
            }}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.solutions_endpoint,
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=row,
                )
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "VASolutionsStore.upsert_solution: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("VASolutionsStore.upsert_solution failed (non-fatal): %s", exc)
            return False

    async def get_solution(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single solution row by solution_id.

        Returns the full row dict if found, or None if not found or on any error.
        """
        if not self.enabled:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.solutions_endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{solution_id}", "select": "*"},
                )
                response.raise_for_status()
                rows = json.loads(response.content) if response.content else []
                if not rows:
                    return None
                row = rows[0]
                # Remap Supabase 'id' column → Pydantic 'solution_id' field
                if "id" in row and "solution_id" not in row:
                    row["solution_id"] = row.pop("id")
                return row
        except Exception as exc:
            logger.warning("VASolutionsStore.get_solution failed (non-fatal): %s", exc)
            return None

    async def get_solutions_by_principal(
        self, principal_id: str, client_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Return all solution rows for a given principal, ordered by approved_at descending.

        When ``client_id`` is provided only solutions belonging to that tenant are returned.
        Returns an empty list on any error.
        """
        if not self.enabled:
            return []
        try:
            params: Dict[str, Any] = {
                "principal_id": f"eq.{principal_id}",
                "select": "*",
                "order": "approved_at.desc",
            }
            if client_id:
                params["client_id"] = f"eq.{client_id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.solutions_endpoint,
                    headers=self.headers,
                    params=params,
                )
                response.raise_for_status()
                rows = json.loads(response.content) if response.content else []
                # Remap Supabase 'id' column → Pydantic 'solution_id' field
                for row in rows:
                    if "id" in row and "solution_id" not in row:
                        row["solution_id"] = row.pop("id")
                return rows
        except Exception as exc:
            logger.warning(
                "VASolutionsStore.get_solutions_by_principal failed (non-fatal): %s", exc
            )
            return []

    async def update_status(self, solution_id: str, status: str) -> bool:
        """
        Update the status column for a solution.

        Returns True on success, False on any failure.
        """
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    self.solutions_endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{solution_id}"},
                    json={"status": status},
                )
                if response.status_code not in (200, 204):
                    logger.warning(
                        "VASolutionsStore.update_status: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("VASolutionsStore.update_status failed (non-fatal): %s", exc)
            return False

    async def update_phase(
        self, solution_id: str, phase: str, *,
        go_live_at: Optional[str] = None,
        completed_at: Optional[str] = None,
    ) -> bool:
        """Update the phase (and optional timestamp) columns for a solution."""
        if not self.enabled:
            return False
        try:
            payload: Dict[str, Any] = {"phase": phase}
            if go_live_at:
                payload["go_live_at"] = go_live_at
            if completed_at:
                payload["completed_at"] = completed_at
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    self.solutions_endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{solution_id}"},
                    json=payload,
                )
                if response.status_code not in (200, 204):
                    logger.warning(
                        "VASolutionsStore.update_phase: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("VASolutionsStore.update_phase failed (non-fatal): %s", exc)
            return False

    async def append_actual_measurement(
        self, solution_id: str, value: float, date: str
    ) -> bool:
        """
        Append a new KPI measurement to the actual_trend and actual_trend_dates JSONB arrays.

        Supabase REST does not support JSONB array_append natively, so this method:
          1. GETs the current arrays.
          2. Appends the new value / date.
          3. PATCHes both columns back.

        Returns True on success, False on any failure (including solution not found).
        """
        if not self.enabled:
            return False
        try:
            # Step 1: fetch current arrays
            async with httpx.AsyncClient() as client:
                get_response = await client.get(
                    self.solutions_endpoint,
                    headers=self.headers,
                    params={
                        "id": f"eq.{solution_id}",
                        "select": "actual_trend,actual_trend_dates",
                    },
                )
                get_response.raise_for_status()
                rows = json.loads(get_response.content) if get_response.content else []
                if not rows:
                    logger.warning(
                        "VASolutionsStore.append_actual_measurement: solution %s not found.",
                        solution_id,
                    )
                    return False

                row = rows[0]
                actual_trend: List[float] = row.get("actual_trend") or []
                actual_trend_dates: List[str] = row.get("actual_trend_dates") or []

                # Step 2: append
                actual_trend.append(value)
                actual_trend_dates.append(date)

                # Step 3: patch
                patch_response = await client.patch(
                    self.solutions_endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{solution_id}"},
                    json={
                        "actual_trend": actual_trend,
                        "actual_trend_dates": actual_trend_dates,
                    },
                )
                if patch_response.status_code not in (200, 204):
                    logger.warning(
                        "VASolutionsStore.append_actual_measurement: PATCH status %s — %s",
                        patch_response.status_code,
                        patch_response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning(
                "VASolutionsStore.append_actual_measurement failed (non-fatal): %s", exc
            )
            return False

    async def store_briefing_snapshot(self, solution_id: str, snapshot: dict) -> bool:
        """Store the briefing snapshot for a VA solution. Returns True on success."""
        if not self.enabled:
            return False
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    self.solutions_endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{solution_id}"},
                    json={"briefing_snapshot": snapshot},
                )
                if response.status_code not in (200, 204):
                    logger.warning(
                        "VASolutionsStore.store_briefing_snapshot: status %s — %s",
                        response.status_code, response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("VASolutionsStore.store_briefing_snapshot failed: %s", exc)
            return False

    async def get_briefing_snapshot(self, solution_id: str) -> Optional[dict]:
        """Retrieve the briefing snapshot for a VA solution."""
        if not self.enabled:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.solutions_endpoint,
                    headers=self.headers,
                    params={"id": f"eq.{solution_id}", "select": "briefing_snapshot"},
                )
                response.raise_for_status()
                rows = json.loads(response.content) if response.content else []
                if not rows or not rows[0].get("briefing_snapshot"):
                    return None
                return rows[0]["briefing_snapshot"]
        except Exception as exc:
            logger.warning("VASolutionsStore.get_briefing_snapshot failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Evaluations
    # ------------------------------------------------------------------

    async def upsert_evaluation(
        self, evaluation: ImpactEvaluation, solution_id: str
    ) -> bool:
        """
        Persist an ImpactEvaluation to value_assurance_evaluations.

        The upsert on solution_id is idempotent — re-evaluating the same
        solution overwrites the previous evaluation row.

        Returns True on success, False on any failure.
        """
        if not self.enabled:
            return False
        try:
            row: Dict[str, Any] = {
                "solution_id": solution_id,
                "baseline_kpi_value": evaluation.baseline_kpi_value,
                "current_kpi_value": evaluation.current_kpi_value,
                "total_kpi_change": evaluation.total_kpi_change,
                "control_group_change": evaluation.control_group_change,
                "market_driven_recovery": evaluation.market_driven_recovery,
                "seasonal_component": evaluation.seasonal_component,
                "attributable_impact": evaluation.attributable_impact,
                "expected_impact_lower": evaluation.expected_impact_lower,
                "expected_impact_upper": evaluation.expected_impact_upper,
                "verdict": evaluation.verdict.value
                if hasattr(evaluation.verdict, "value")
                else str(evaluation.verdict),
                "confidence": evaluation.confidence.value
                if hasattr(evaluation.confidence, "value")
                else str(evaluation.confidence),
                "confidence_rationale": evaluation.confidence_rationale,
                "attribution_method": evaluation.attribution_method,
                "control_group_description": evaluation.control_group_description,
                "market_context_summary": evaluation.market_context_summary,
                # JSONB columns
                "strategy_alignment": _safe_json(evaluation.strategy_check),
                "composite_verdict": _safe_json(evaluation.composite_verdict),
                "evaluated_at": evaluation.evaluated_at,
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.evaluations_endpoint,
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=row,
                )
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "VASolutionsStore.upsert_evaluation: unexpected status %s — %s",
                        response.status_code,
                        response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("VASolutionsStore.upsert_evaluation failed (non-fatal): %s", exc)
            return False
