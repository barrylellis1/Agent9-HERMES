"""
Supabase persistence layer for assessment runs, KPI assessments, and situation actions.

Follows the same httpx REST pattern as SituationsStore.
Falls back silently if SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set.
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

from src.agents.models.assessment_models import (
    AssessmentRun,
    KPIAssessment,
    KPIAssessmentStatus,
    SituationAction,
)

logger = logging.getLogger(__name__)


class AssessmentStore:
    """Thin async Supabase client for assessment_runs, kpi_assessments, situation_actions."""

    def __init__(self) -> None:
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_service_key:
            logger.warning(
                "AssessmentStore: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — "
                "assessment persistence is disabled."
            )
            self.enabled = False
            return

        if httpx is None:
            logger.warning(
                "AssessmentStore: httpx is not installed — assessment persistence is disabled."
            )
            self.enabled = False
            return

        self.enabled = True
        self.headers = {
            "apikey": self.supabase_service_key,
            "Authorization": f"Bearer {self.supabase_service_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._runs_url = f"{self.supabase_url}/rest/v1/assessment_runs"
        self._assessments_url = f"{self.supabase_url}/rest/v1/kpi_assessments"
        self._actions_url = f"{self.supabase_url}/rest/v1/situation_actions"

    # ------------------------------------------------------------------
    # Assessment runs
    # ------------------------------------------------------------------

    async def upsert_run(self, run: AssessmentRun) -> bool:
        """Persist or update an AssessmentRun row. Returns True on success."""
        if not self.enabled:
            return False
        try:
            row = {
                "id": run.id,
                "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "status": run.status.value,
                "kpi_count": run.kpi_count,
                "kpis_escalated": run.kpis_escalated,
                "kpis_monitored": run.kpis_monitored,
                "kpis_below_threshold": run.kpis_below_threshold,
                "kpis_errored": run.kpis_errored,
                "new_situation_count": run.new_situation_count,
                "previous_run_id": run.previous_run_id,
                "client_id": run.client_id,
                "config": run.config.model_dump(),
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._runs_url,
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=row,
                )
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "AssessmentStore.upsert_run: unexpected status %s — %s",
                        response.status_code, response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("AssessmentStore.upsert_run failed (non-fatal): %s", exc)
            return False

    async def get_latest_run(self, principal_id: str, client_id: str) -> Optional[Dict[str, Any]]:
        """Return the most recent completed run for a principal+client pair."""
        if not self.enabled:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._runs_url,
                    headers=self.headers,
                    params={
                        "client_id": f"eq.{client_id}",
                        "status": "eq.complete",
                        "order": "started_at.desc",
                        "limit": "1",
                        "select": "*",
                    },
                )
                response.raise_for_status()
                rows = json.loads(response.content) if response.content else []
                # Filter by principal_id from config JSONB
                for row in rows:
                    cfg = row.get("config") or {}
                    if cfg.get("principal_id") == principal_id:
                        return row
                return None
        except Exception as exc:
            logger.warning("AssessmentStore.get_latest_run failed (non-fatal): %s", exc)
            return None

    # ------------------------------------------------------------------
    # KPI assessments
    # ------------------------------------------------------------------

    async def upsert_kpi_assessment(self, ka: KPIAssessment) -> bool:
        """Persist or update a KPIAssessment row. Returns True on success."""
        if not self.enabled:
            return False
        try:
            row = {
                "id": ka.id,
                "run_id": ka.run_id,
                "kpi_id": ka.kpi_id,
                "kpi_name": ka.kpi_name,
                "kpi_value": ka.kpi_value,
                "comparison_value": ka.comparison_value,
                "severity": ka.severity,
                "confidence": ka.confidence,
                "status": ka.status.value,
                "escalated_to_da": ka.escalated_to_da,
                "da_result": ka.da_result,
                "benchmark_segments": ka.benchmark_segments,
                "error_message": ka.error_message,
                "created_at": ka.created_at.isoformat(),
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._assessments_url,
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=row,
                )
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "AssessmentStore.upsert_kpi_assessment: unexpected status %s — %s",
                        response.status_code, response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("AssessmentStore.upsert_kpi_assessment failed (non-fatal): %s", exc)
            return False

    async def get_detected_kpi_ids(self, run_id: str) -> List[str]:
        """Return kpi_id list for all DETECTED assessments in a given run."""
        if not self.enabled:
            return []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._assessments_url,
                    headers=self.headers,
                    params={
                        "run_id": f"eq.{run_id}",
                        "status": f"eq.{KPIAssessmentStatus.DETECTED.value}",
                        "select": "kpi_id",
                    },
                )
                response.raise_for_status()
                rows = json.loads(response.content) if response.content else []
                return [r["kpi_id"] for r in rows]
        except Exception as exc:
            logger.warning("AssessmentStore.get_detected_kpi_ids failed (non-fatal): %s", exc)
            return []

    # ------------------------------------------------------------------
    # Situation actions
    # ------------------------------------------------------------------

    async def insert_action(self, action: SituationAction) -> bool:
        """Insert a new situation action record. Returns True on success."""
        if not self.enabled:
            return False
        try:
            row = {
                "id": action.id,
                "situation_id": action.situation_id,
                "kpi_assessment_id": action.kpi_assessment_id,
                "run_id": action.run_id,
                "principal_id": action.principal_id,
                "action_type": action.action_type.value,
                "target_principal_id": action.target_principal_id,
                "snooze_expires_at": action.snooze_expires_at.isoformat() if action.snooze_expires_at else None,
                "notes": action.notes,
                "created_at": action.created_at.isoformat(),
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._actions_url,
                    headers=self.headers,
                    json=row,
                )
                if response.status_code not in (200, 201, 204):
                    logger.warning(
                        "AssessmentStore.insert_action: unexpected status %s — %s",
                        response.status_code, response.text[:200],
                    )
                    return False
            return True
        except Exception as exc:
            logger.warning("AssessmentStore.insert_action failed (non-fatal): %s", exc)
            return False

    async def get_active_snoozes(self, principal_id: str) -> List[str]:
        """Return situation_ids that are currently snoozed (snooze not yet expired)."""
        if not self.enabled:
            return []
        try:
            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._actions_url,
                    headers=self.headers,
                    params={
                        "principal_id": f"eq.{principal_id}",
                        "action_type": "eq.snooze",
                        "snooze_expires_at": f"gt.{now_iso}",
                        "select": "situation_id",
                    },
                )
                response.raise_for_status()
                rows = json.loads(response.content) if response.content else []
                return [r["situation_id"] for r in rows]
        except Exception as exc:
            logger.warning("AssessmentStore.get_active_snoozes failed (non-fatal): %s", exc)
            return []
