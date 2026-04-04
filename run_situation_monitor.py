"""
Situation Monitor — Phase 9B
Replaces run_enterprise_assessment.py.

Runs an SA-only assessment for a specific principal and client, following
the same orchestrated agent workflow as the Decision Studio UI's
"Detect Situations" button. DA is never triggered automatically — the
principal requests DA interactively from the UI (HITL gate).

Usage:
    python run_situation_monitor.py --principal <principal_id> --client <client_id> [--dry-run]

Example:
    python run_situation_monitor.py --principal cfo_001 --client lubricants_inc
    python run_situation_monitor.py --principal cfo_001 --client lubricants_inc --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime
from typing import Optional

from src.agents.models.assessment_models import (
    AssessmentConfig,
    AssessmentRun,
    AssessmentStatus,
    KPIAssessment,
    KPIAssessmentStatus,
)
from src.agents.models.situation_awareness_models import ComparisonType, TimeFrame

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime initialisation — reuses AgentRuntime from src/api/runtime.py
# ---------------------------------------------------------------------------

async def initialize_runtime():
    """Initialize the full agent runtime using the canonical AgentRuntime class."""
    from src.api.runtime import AgentRuntime

    runtime = AgentRuntime()
    await runtime.initialize()
    return runtime


# ---------------------------------------------------------------------------
# Situation Monitor Engine
# ---------------------------------------------------------------------------

class SituationMonitor:
    """
    Runs an SA-only assessment for one principal + one client.

    Mirrors the workflow in workflows.py::_run_situations_workflow exactly:
      1. PC Agent → resolve real PrincipalContext
      2. Single orchestrator.orchestrate_situation_detection() call
      3. Persist situations to Supabase via SituationsStore
      4. Build KPIAssessment records from returned situations
      5. Delta detection: identify NEW vs known situations
    """

    def __init__(self, runtime, config: AssessmentConfig) -> None:
        self.runtime = runtime
        self.orchestrator = runtime.get_orchestrator()
        self.config = config

    async def run(self) -> AssessmentRun:
        """Full situation monitor run. Returns completed AssessmentRun."""
        run_id = str(uuid.uuid4())
        run = AssessmentRun(
            id=run_id,
            started_at=datetime.utcnow(),
            config=self.config,
        )
        short_id = run_id[:8]
        logger.info(
            f"[{short_id}] Situation Monitor started — "
            f"principal={self.config.principal_id} client={self.config.client_id} "
            f"dry_run={self.config.dry_run} run_id={run_id}"
        )

        # ------------------------------------------------------------------
        # Step 1: Resolve principal context via PC Agent
        # (same call as workflows.py::_run_situations_workflow)
        # ------------------------------------------------------------------
        logger.info(f"[{run_id}] Resolving principal context for {self.config.principal_id}")
        principal_context = await self._resolve_principal_context()
        if principal_context is None:
            logger.error(f"[{run_id}] Could not resolve principal context — aborting")
            run.status = AssessmentStatus.ERROR
            run.completed_at = datetime.utcnow()
            return run

        business_processes = (
            principal_context.get("business_processes")
            or principal_context.get("business_process_ids")
            or []
        )
        logger.info(
            f"[{run_id}] Principal resolved — "
            f"role={principal_context.get('role')} "
            f"business_processes={len(business_processes)}"
        )

        # ------------------------------------------------------------------
        # Step 2: Single SA call via orchestrator
        # (same call as workflows.py::_run_situations_workflow)
        # ------------------------------------------------------------------
        from src.agents.models.situation_awareness_models import SituationDetectionRequest

        detection_request = SituationDetectionRequest(
            request_id=run_id,
            principal_context=principal_context,
            business_processes=business_processes,
            timeframe=TimeFrame.CURRENT_QUARTER.value,
            comparison_type=ComparisonType.YEAR_OVER_YEAR.value,
            client_id=self.config.client_id,
            filters={},
        )

        logger.info(f"[{run_id}] Running situation detection...")
        response = await self.orchestrator.orchestrate_situation_detection(detection_request)

        if isinstance(response, dict):
            situations = response.get("situations", []) or []
            opportunities = response.get("opportunities", []) or []
            kpi_evaluated_count = response.get("kpi_evaluated_count", None)
        else:
            situations = getattr(response, "situations", []) or []
            opportunities = getattr(response, "opportunities", []) or []
            kpi_evaluated_count = getattr(response, "kpi_evaluated_count", None)

        logger.info(
            f"[{run_id}] Detection complete — "
            f"situations={len(situations)} opportunities={len(opportunities)} "
            f"kpis_evaluated={kpi_evaluated_count}"
        )

        run.kpi_count = kpi_evaluated_count or len(situations)
        run.client_id = self.config.client_id

        # ------------------------------------------------------------------
        # Step 3: Persist situations to Supabase via SituationsStore
        # (same persistence as workflows.py::_run_situations_workflow)
        # ------------------------------------------------------------------
        if not self.config.dry_run:
            await self._persist_situations(situations, opportunities)

        # ------------------------------------------------------------------
        # Step 4: Build KPIAssessment records from returned situations
        # ------------------------------------------------------------------
        assessments = self._build_assessments(run_id, situations)

        for ka in assessments:
            if ka.status == KPIAssessmentStatus.DETECTED:
                run.kpis_escalated += 1
            elif ka.status == KPIAssessmentStatus.MONITORING:
                run.kpis_monitored += 1
            elif ka.status == KPIAssessmentStatus.BELOW_THRESHOLD:
                run.kpis_below_threshold += 1
            elif ka.status == KPIAssessmentStatus.ERROR:
                run.kpis_errored += 1

        # ------------------------------------------------------------------
        # Step 5: Delta detection — identify NEW vs known situations
        # ------------------------------------------------------------------
        run = await self._detect_delta(run, assessments)

        # ------------------------------------------------------------------
        # Step 6: Persist assessment run + KPI assessments
        # ------------------------------------------------------------------
        run.status = AssessmentStatus.COMPLETE
        run.completed_at = datetime.utcnow()

        if not self.config.dry_run:
            await self._persist_run(run, assessments)
        else:
            self._log_dry_run_summary(run, assessments)

        logger.info(
            f"[{run_id}] Complete — "
            f"detected={run.kpis_escalated} monitoring={run.kpis_monitored} "
            f"below_threshold={run.kpis_below_threshold} errors={run.kpis_errored}"
        )
        return run

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _resolve_principal_context(self) -> Optional[dict]:
        """Call PC Agent to resolve full PrincipalContext — same as workflows.py."""
        try:
            principal_resp = await self.orchestrator.execute_agent_method(
                "A9_Principal_Context_Agent",
                "get_principal_context_by_id",
                {"principal_id": self.config.principal_id},
            )

            if isinstance(principal_resp, dict):
                return (
                    principal_resp.get("context")
                    or principal_resp.get("principal_context")
                    or principal_resp
                )
            elif hasattr(principal_resp, "context"):
                from src.api.routes.workflows import serialize
                return serialize(principal_resp.context)
            return None

        except Exception as e:
            logger.error(f"PC Agent call failed: {e}", exc_info=True)
            return None

    def _build_assessments(self, run_id: str, situations: list) -> list[KPIAssessment]:
        """Convert SA situations into KPIAssessment records."""
        assessments = []
        for situation in situations:
            kpi_id = (
                situation.get("kpi_id") if isinstance(situation, dict)
                else getattr(situation, "kpi_id", None)
            ) or (
                situation.get("kpi_name") if isinstance(situation, dict)
                else getattr(situation, "kpi_name", None)
            )
            kpi_name = (
                situation.get("kpi_name") if isinstance(situation, dict)
                else getattr(situation, "kpi_name", None)
            )
            raw_severity = (
                situation.get("severity") if isinstance(situation, dict)
                else getattr(situation, "severity", None)
            )
            # Unwrap enum value if needed
            if hasattr(raw_severity, "value"):
                raw_severity = raw_severity.value

            _SEVERITY_SCORES = {
                "critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2,
            }
            severity_score = _SEVERITY_SCORES.get(
                str(raw_severity).lower() if raw_severity else "", 0.0
            )

            status = (
                KPIAssessmentStatus.DETECTED
                if severity_score >= self.config.severity_floor
                else KPIAssessmentStatus.MONITORING
            )

            assessments.append(KPIAssessment(
                id=str(uuid.uuid4()),
                run_id=run_id,
                kpi_id=kpi_id or "unknown",
                kpi_name=kpi_name,
                severity=severity_score,
                confidence=None,
                status=status,
                escalated_to_da=False,  # DA is HITL — principal decides from Decision Studio
            ))

        return assessments

    async def _persist_situations(self, situations: list, opportunities: list) -> None:
        """Persist situations and opportunities via SituationsStore — same as workflows.py."""
        try:
            from src.database.situations_store import SituationsStore
            store = SituationsStore()
            if store.enabled:
                for situation in situations:
                    await store.upsert_situation(situation)
                for opportunity in opportunities:
                    await store.upsert_opportunity(opportunity)
                logger.info(
                    f"Persisted {len(situations)} situations and "
                    f"{len(opportunities)} opportunities to Supabase"
                )
            else:
                logger.warning("SituationsStore not enabled — skipping Supabase persistence")
        except Exception as e:
            logger.warning(f"Situation persistence failed (non-fatal): {e}", exc_info=True)

    async def _detect_delta(
        self, run: AssessmentRun, assessments: list[KPIAssessment]
    ) -> AssessmentRun:
        """Compare current detected KPIs against previous run to find NEW situations."""
        from src.database.assessment_store import AssessmentStore
        store = AssessmentStore()
        if not store.enabled:
            return run

        try:
            prev_row = await store.get_latest_run(
                self.config.principal_id, self.config.client_id
            )
            if prev_row is None:
                # No previous run — everything is new
                run.new_situation_count = sum(
                    1 for a in assessments if a.status == KPIAssessmentStatus.DETECTED
                )
                logger.info(
                    f"[{run.id}] Delta: no previous run — "
                    f"{run.new_situation_count} situations all NEW"
                )
                return run

            run.previous_run_id = prev_row["id"]
            prev_detected = set(await store.get_detected_kpi_ids(prev_row["id"]))
            current_detected = {
                a.kpi_id for a in assessments if a.status == KPIAssessmentStatus.DETECTED
            }
            new_kpi_ids = current_detected - prev_detected
            run.new_situation_count = len(new_kpi_ids)
            logger.info(
                f"[{run.id}] Delta: {run.new_situation_count} new situations "
                f"(prev={len(prev_detected)} current={len(current_detected)})"
            )
        except Exception as e:
            logger.warning(f"[{run.id}] Delta detection failed (non-fatal): {e}", exc_info=True)

        return run

    async def _persist_run(self, run: AssessmentRun, assessments: list[KPIAssessment]) -> None:
        """Persist assessment run + KPI assessments to Supabase."""
        from src.database.assessment_store import AssessmentStore
        store = AssessmentStore()

        ok = await store.upsert_run(run)
        if ok:
            logger.info(f"[{run.id}] Run persisted to Supabase")
        else:
            logger.warning(f"[{run.id}] Run persistence failed — logged only")
            logger.info(
                f"[{run.id}] Run summary: "
                + json.dumps(run.model_dump(), indent=None, default=str)
            )

        for ka in assessments:
            await store.upsert_kpi_assessment(ka)
            logger.info(
                f"[{run.id}] kpi_assessment persisted: kpi={ka.kpi_id} "
                f"status={ka.status} severity={ka.severity}"
            )

    def _log_dry_run_summary(self, run: AssessmentRun, assessments: list[KPIAssessment]) -> None:
        """Log dry-run results without persisting."""
        logger.info(f"[DRY RUN] Run summary: {json.dumps(run.model_dump(), default=str)}")
        detected = [a for a in assessments if a.status == KPIAssessmentStatus.DETECTED]
        if detected:
            logger.info(f"[DRY RUN] Detected situations ({len(detected)}):")
            for a in detected:
                logger.info(f"  - {a.kpi_name or a.kpi_id} | severity={a.severity}")
        else:
            logger.info("[DRY RUN] No situations detected above severity floor")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main(
    principal_id: str,
    client_id: str,
    dry_run: bool = False,
) -> int:
    from src.agents.models.assessment_models import AssessmentConfig as _Config

    # client_id added to AssessmentConfig — see Phase 9C model update below
    config = _Config(
        principal_id=principal_id,
        client_id=client_id,
        dry_run=dry_run,
    )
    runtime = await initialize_runtime()
    monitor = SituationMonitor(runtime, config)
    run = await monitor.run()
    return 0 if run.status == AssessmentStatus.COMPLETE else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Situation Monitor — SA-only assessment for a principal + client. "
            "Detected situations are persisted for principal review in Decision Studio. "
            "DA is HITL — never triggered automatically."
        )
    )
    parser.add_argument(
        "--principal",
        metavar="PRINCIPAL_ID",
        required=True,
        help="Principal ID to run the assessment for (e.g. cfo_001).",
    )
    parser.add_argument(
        "--client",
        metavar="CLIENT_ID",
        required=True,
        help="Client ID to scope the assessment to (e.g. lubricants_inc).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run detection but skip Supabase persistence (results logged only).",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(
        main(
            principal_id=args.principal,
            client_id=args.client,
            dry_run=args.dry_run,
        )
    )
    sys.exit(exit_code)
