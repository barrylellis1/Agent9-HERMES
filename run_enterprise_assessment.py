"""
Enterprise Assessment Engine — Phase 9B
Replaces run_cfo_assessment.py.

Runs SA-only assessment across all registered KPIs and persists findings
to Supabase assessment_runs / kpi_assessments tables.

DESIGN PRINCIPLE: This engine is SA-only. Detected situations are flagged
for the principal to review in Decision Studio. The principal then chooses
which situations warrant Deep Analysis — DA is never triggered automatically.

Usage:
    python run_enterprise_assessment.py [--principal <id>] [--kpi <kpi_id>] [--dry-run]
"""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, List, Optional, Tuple

from src.agents.models.assessment_models import (
    AssessmentConfig,
    AssessmentRun,
    AssessmentStatus,
    KPIAssessment,
    KPIAssessmentStatus,
)
from src.agents.models.situation_awareness_models import (
    ComparisonType,
    PrincipalContext,
    SituationDetectionRequest,
    SituationSeverity,
    TimeFrame,
)
from src.services.audit_service import AuditService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Runtime initialisation (mirrors src/api/runtime.py inline — no AgentRuntime)
# ---------------------------------------------------------------------------

async def _build_registry_factory():
    from src.registry.bootstrap import RegistryBootstrap

    await RegistryBootstrap.initialize()
    return RegistryBootstrap._factory


async def _create_orchestrator(registry_factory):
    from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent

    orchestrator = await A9_Orchestrator_Agent.create({})
    await orchestrator.connect()
    return orchestrator


async def _connect_agent(agent_name: str, agent: object, orchestrator) -> None:
    connect_method = getattr(agent, "connect", None)
    if not callable(connect_method):
        return

    try:
        result = connect_method(orchestrator)
    except TypeError:
        result = connect_method()

    if inspect.isawaitable(result):
        await result


async def _create_core_agents(orchestrator, registry_factory) -> None:
    from src.agents.new.a9_orchestrator_agent import initialize_agent_registry

    await initialize_agent_registry()

    agent_plan = [
        (
            "A9_Data_Governance_Agent",
            {
                "orchestrator": orchestrator,
                "registry_factory": registry_factory,
            },
        ),
        (
            "A9_Principal_Context_Agent",
            {
                "orchestrator": orchestrator,
                "registry_factory": registry_factory,
            },
        ),
        (
            "A9_Data_Product_Agent",
            {
                "orchestrator": orchestrator,
                "registry_factory": registry_factory,
                "data_directory": "data",
                "database": {
                    "type": "duckdb",
                    "path": "agent9-hermes-api.duckdb",
                },
                "registry_path": "src/registry/data_product",
            },
        ),
        (
            "A9_Situation_Awareness_Agent",
            {
                "orchestrator": orchestrator,
                "registry_factory": registry_factory,
            },
        ),
        (
            "A9_Deep_Analysis_Agent",
            {
                "orchestrator": orchestrator,
                "registry_factory": registry_factory,
            },
        ),
        (
            "A9_NLP_Interface_Agent",
            {
                "orchestrator": orchestrator,
                "registry_factory": registry_factory,
            },
        ),
        (
            "A9_LLM_Service_Agent",
            {
                "orchestrator": orchestrator,
                "registry_factory": registry_factory,
            },
        ),
        (
            "A9_Value_Assurance_Agent",
            {
                "orchestrator": orchestrator,
                "registry_factory": registry_factory,
            },
        ),
    ]

    agents: dict[str, Any] = {}
    for agent_name, config in agent_plan:
        agent = await orchestrator.create_agent_with_dependencies(agent_name, config)
        await _connect_agent(agent_name, agent, orchestrator)
        agents[agent_name] = agent

    # Wire DGA into consuming agents after all agents are created and connected.
    # Mirrors runtime.py _wire_governance_dependencies() — keeps governance routing
    # consistent between API server and assessment CLI.
    dga = agents.get("A9_Data_Governance_Agent")
    if dga:
        wired = []
        for name in ("A9_Situation_Awareness_Agent", "A9_Data_Product_Agent", "A9_Deep_Analysis_Agent"):
            ag = agents.get(name)
            if ag:
                ag.data_governance_agent = dga
                wired.append(name)
        logger.info(f"Data Governance Agent wired into: {', '.join(wired)}")
    else:
        logger.warning("Data Governance Agent not found — governance wiring skipped")


async def initialize_runtime() -> Tuple[Any, Any]:
    """Initialize RegistryBootstrap + Orchestrator + all core agents.

    Returns (orchestrator, registry_factory).
    """
    logger.info("Initializing registry factory")
    registry_factory = await _build_registry_factory()

    logger.info("Initializing orchestrator")
    orchestrator = await _create_orchestrator(registry_factory)

    logger.info("Initializing core agents")
    await _create_core_agents(orchestrator, registry_factory)

    logger.info("Runtime initialization complete")
    return orchestrator, registry_factory


# ---------------------------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------------------------

_SEVERITY_SCORES = {
    SituationSeverity.CRITICAL: 1.0,
    SituationSeverity.HIGH: 0.8,
    SituationSeverity.MEDIUM: 0.5,
    SituationSeverity.LOW: 0.2,
    SituationSeverity.INFORMATION: 0.1,
}

_DEFAULT_CONFIDENCE = {
    SituationSeverity.CRITICAL: 0.7,
    SituationSeverity.HIGH: 0.7,
    SituationSeverity.MEDIUM: 0.5,
    SituationSeverity.LOW: 0.3,
    SituationSeverity.INFORMATION: 0.3,
}

def _period_comparison_for_kpi(kpi, registry_factory) -> str:
    """The named comparison an assessment reads this KPI on (Phase 26): its data product's
    period settings (src/analysis/period_settings.py; no per-KPI exceptions, owner ruling 3).
    Financial products: YTD vs previous year YTD; operational: the last 12 months.

    Replaces `monitoring_profile.comparison_period`, which the kpis table never stored: every
    assessment fell back to year to date whatever it said."""
    from src.analysis.complete_periods import is_period_keyed
    from src.analysis.period_settings import DEFAULT_READING, settings_for
    try:
        dp_provider = registry_factory.get_provider("data_product") if registry_factory else None
        dp_id = getattr(kpi, "data_product_id", None)
        dp = dp_provider.get(dp_id) if (dp_provider and dp_id) else None
        meta = dict(getattr(dp, "metadata", None) or {})
        dims = getattr(dp, "time_dimensions", None) or meta.get("time_dimensions") or []
        first = dims[0] if dims else None
        spec = first.model_dump() if hasattr(first, "model_dump") else first
        return settings_for(meta, period_keyed=is_period_keyed(spec)).reading
    except Exception as e:
        logger.error(
            f"Period settings for KPI {getattr(kpi, 'id', kpi)} could not be read ({e}); reading {DEFAULT_READING}"
        )
        return DEFAULT_READING


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class EnterpriseAssessmentEngine:
    """Orchestrates the enterprise-wide SA assessment loop (SA only — DA is HITL)."""

    def __init__(self, orchestrator, registry_factory, config: AssessmentConfig) -> None:
        self.orchestrator = orchestrator
        self.registry_factory = registry_factory
        self.config = config

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def run(self) -> AssessmentRun:
        """Full assessment loop. Returns completed AssessmentRun."""
        run_id = str(uuid.uuid4())[:8]
        run = AssessmentRun(
            id=run_id,
            started_at=datetime.utcnow(),
            config=self.config,
            client_id=self.config.client_id,
        )
        logger.info(f"[{run_id}] Assessment started — config: {self.config}")

        kpis = await self._load_kpis()
        run.kpi_count = len(kpis)
        logger.info(f"[{run_id}] {len(kpis)} KPIs in scope")

        for i, kpi in enumerate(kpis, 1):
            kpi_label = getattr(kpi, "id", str(kpi))
            logger.info(f"[{run_id}] KPI {i}/{len(kpis)}: {kpi_label}")
            try:
                ka = await self._assess_kpi(run_id, kpi)

                if ka.status == KPIAssessmentStatus.DETECTED:
                    # Flagged for principal review — DA is HITL, not automatic.
                    run.kpis_escalated += 1
                elif ka.status == KPIAssessmentStatus.MONITORING:
                    run.kpis_monitored += 1
                elif ka.status == KPIAssessmentStatus.BELOW_THRESHOLD:
                    run.kpis_below_threshold += 1
                elif ka.status == KPIAssessmentStatus.ERROR:
                    run.kpis_errored += 1

                await self._persist_kpi_assessment(ka)

            except Exception as e:
                logger.error(f"[{run_id}] KPI {kpi_label} ERROR: {e}", exc_info=True)
                run.kpis_errored += 1

        run.status = AssessmentStatus.COMPLETE
        run.completed_at = datetime.utcnow()
        await self._persist_run(run)
        logger.info(
            f"[{run_id}] Complete — escalated={run.kpis_escalated} "
            f"monitoring={run.kpis_monitored} errors={run.kpis_errored}"
        )
        return run

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _load_kpis(self) -> list:
        """Load all KPIs for client_id via the KPI registry provider."""
        kpi_provider = self.registry_factory.get_provider("kpi")
        all_kpis = kpi_provider.get_all()

        if self.config.client_id:
            all_kpis = [
                k for k in all_kpis
                if getattr(k, "client_id", None) == self.config.client_id
            ]
            logger.info(
                f"Client filter ({self.config.client_id}): {len(all_kpis)} KPIs in scope"
            )

        return all_kpis

    async def _assess_kpi(self, run_id: str, kpi) -> KPIAssessment:
        """Run SA detection for one KPI. Returns KPIAssessment with escalate_to_da set."""
        kpi_id = getattr(kpi, "id", str(kpi))
        kpi_name = getattr(kpi, "name", kpi_id)
        # code-review (2026-10-02): `x or y` does not fall through on an empty
        # string, only on None/falsy -- if self.config.client_id were ever ""
        # (reachable via ?client_id= on the assessments route, Optional[str]
        # with no non-empty validation) this would write an audit row with an
        # unscoped client_id instead of skipping, unlike the `if client_id:`
        # guards DA and SA use for the same signal elsewhere in this same
        # change. Resolved once here, explicitly normalized to None, and
        # every call site below checks it before writing.
        _event_client_id = getattr(kpi, "client_id", None) or self.config.client_id or None

        # Retrieve per-KPI calibration overrides when available.
        monitoring_profile = getattr(kpi, "monitoring_profile", None)
        volatility_band: float = (
            getattr(monitoring_profile, "volatility_band", 0.05)
            if monitoring_profile is not None
            else 0.05
        )
        confidence_floor: float = (
            getattr(monitoring_profile, "confidence_floor", 0.6)
            if monitoring_profile is not None
            else 0.6
        )

        try:
            # The request still names a timeframe word (a required field); the named comparison
            # decides the period read (Phase 26).
            timeframe = TimeFrame.YEAR_TO_DATE
            period_comparison = _period_comparison_for_kpi(kpi, self.registry_factory)

            principal_context = PrincipalContext(
                principal_id="system",
                role="system",
                client_id=self.config.client_id,
                business_processes=getattr(kpi, "business_process_ids", []) or [],
                default_filters={},
                decision_style="analytical",
                communication_style="formal",
                preferred_timeframes=[timeframe],
            )

            request = SituationDetectionRequest(
                request_id=str(uuid.uuid4()),
                principal_context=principal_context,
                business_processes=getattr(kpi, "business_process_ids", []) or [],
                timeframe=timeframe,
                comparison_type=ComparisonType.YEAR_OVER_YEAR,
                period_comparison=period_comparison,
                client_id=getattr(kpi, "client_id", None),
                filters=getattr(kpi, "filters", None) or {},
            )

            raw_result = await self.orchestrator.orchestrate_situation_detection(request)

            # orchestrate_situation_detection returns a plain dict with "situations" key.
            if isinstance(raw_result, dict):
                situations = raw_result.get("situations", [])
            else:
                situations = getattr(raw_result, "situations", [])

            # Find the best-matching situation for this KPI.
            matched = None
            for s in situations:
                s_kpi_name = getattr(s, "kpi_name", None) or (
                    s.get("kpi_name") if isinstance(s, dict) else None
                )
                if s_kpi_name and (
                    s_kpi_name.lower() == kpi_name.lower()
                    or s_kpi_name.lower() == kpi_id.lower()
                ):
                    matched = s
                    break

            if matched is None:
                return KPIAssessment(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    kpi_id=kpi_id,
                    kpi_name=kpi_name,
                    severity=None,
                    confidence=None,
                    status=KPIAssessmentStatus.BELOW_THRESHOLD,
                    escalated_to_da=False,
                )

            # Resolve severity score.
            raw_severity = (
                matched.get("severity") if isinstance(matched, dict)
                else getattr(matched, "severity", None)
            )
            if isinstance(raw_severity, SituationSeverity):
                severity_score = _SEVERITY_SCORES.get(raw_severity, 0.0)
            elif isinstance(raw_severity, str):
                try:
                    severity_score = _SEVERITY_SCORES.get(SituationSeverity(raw_severity), 0.0)
                    raw_severity = SituationSeverity(raw_severity)
                except ValueError:
                    severity_score = 0.0
                    raw_severity = None
            else:
                severity_score = 0.0
                raw_severity = None

            if severity_score < self.config.severity_floor:
                return KPIAssessment(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    kpi_id=kpi_id,
                    kpi_name=kpi_name,
                    severity=severity_score,
                    confidence=None,
                    status=KPIAssessmentStatus.BELOW_THRESHOLD,
                    escalated_to_da=False,
                )

            # Resolve confidence score.
            confidence = (
                matched.get("confidence") if isinstance(matched, dict)
                else getattr(matched, "confidence", None)
            )
            if confidence is None:
                confidence = _DEFAULT_CONFIDENCE.get(raw_severity, 0.5) if raw_severity else 0.5

            if confidence < confidence_floor:
                # Stage-wise reliability panel (2026-10-02 scope extension to
                # docs/architecture/audit_event_system_design.md). outcome='abstain',
                # not 'fail': sitting under confidence_floor means "inconclusive",
                # not "a defect was found" — this is the common case for a
                # borderline KPI, which is exactly why the design note's retention
                # tier for 'abstain' was revised the same day this was wired (see
                # that note's retention table).
                if _event_client_id:
                    await AuditService.log(
                        client_id=_event_client_id,
                        event_type="reliability.detection_confidence",
                        severity="info",
                        outcome="abstain",
                        source_agent="EnterpriseAssessmentEngine",
                        resource_type="kpi",
                        resource_id=kpi_id,
                        payload={"confidence": confidence, "confidence_floor": confidence_floor, "severity_score": severity_score},
                    )
                return KPIAssessment(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    kpi_id=kpi_id,
                    kpi_name=kpi_name,
                    severity=severity_score,
                    confidence=confidence,
                    status=KPIAssessmentStatus.MONITORING,
                    escalated_to_da=False,
                )

            if _event_client_id:
                await AuditService.log(
                    client_id=_event_client_id,
                    event_type="reliability.detection_confidence",
                    severity="info",
                    outcome="pass",
                    source_agent="EnterpriseAssessmentEngine",
                    resource_type="kpi",
                    resource_id=kpi_id,
                    payload={"confidence": confidence, "confidence_floor": confidence_floor, "severity_score": severity_score},
                )
            return KPIAssessment(
                id=str(uuid.uuid4()),
                run_id=run_id,
                kpi_id=kpi_id,
                kpi_name=kpi_name,
                severity=severity_score,
                confidence=confidence,
                status=KPIAssessmentStatus.DETECTED,
                escalated_to_da=False,  # DA is HITL — principal decides from Decision Studio UI
            )

        except Exception as e:
            logger.error(
                f"[{run_id}] SA detection failed for KPI {kpi_id}: {e}", exc_info=True
            )
            # fail, not abstain: an exception here means detection itself broke,
            # not that the signal was merely inconclusive. Rare by construction
            # (unlike the confidence-floor abstain above), so it keeps the
            # long-retention tier.
            if _event_client_id:
                await AuditService.log(
                    client_id=_event_client_id,
                    event_type="reliability.detection_confidence",
                    severity="error",
                    outcome="fail",
                    source_agent="EnterpriseAssessmentEngine",
                    resource_type="kpi",
                    resource_id=kpi_id,
                    payload={"error": str(e)},
                )
            return KPIAssessment(
                id=str(uuid.uuid4()),
                run_id=run_id,
                kpi_id=kpi_id,
                kpi_name=kpi_name,
                severity=None,
                confidence=None,
                status=KPIAssessmentStatus.ERROR,
                escalated_to_da=False,
                error_message=str(e),
            )

    async def _persist_run(self, run: AssessmentRun) -> None:
        """Log the run summary. Supabase persistence is a TODO."""
        # TODO: Phase 9C — write to Supabase assessment_runs table.
        logger.info(
            f"[{run.id}] PERSIST run — "
            + json.dumps(run.model_dump(), indent=None, default=str)
        )

    async def _persist_kpi_assessment(self, ka: KPIAssessment) -> None:
        """Log individual KPI assessment. Supabase persistence is a TODO."""
        # TODO: Phase 9C — write to Supabase kpi_assessments table.
        logger.info(
            f"[{ka.run_id}] PERSIST kpi_assessment kpi={ka.kpi_id} "
            f"status={ka.status} severity={ka.severity} confidence={ka.confidence}"
        )


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

async def main(
    principal_id: Optional[str] = None,
    kpi_id: Optional[str] = None,
    client_id: str | None = None,
    dry_run: bool = False,
) -> int:
    # Client_id is mandatory — all assessments must be scoped to a tenant
    if not client_id:
        logger.error("client_id is required. Pass --client <client_id> or set ACTIVE_CLIENT_ID env var")
        return 1

    config = AssessmentConfig(client_id=client_id, dry_run=dry_run)
    orchestrator, registry_factory = await initialize_runtime()
    engine = EnterpriseAssessmentEngine(orchestrator, registry_factory, config)
    run = await engine.run()
    return 0 if run.status == AssessmentStatus.COMPLETE else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enterprise Assessment Engine — runs SA across all registered KPIs. "
        "Detected situations are flagged for principal review; DA is HITL."
    )
    parser.add_argument(
        "--principal",
        metavar="PRINCIPAL_ID",
        default=None,
        help="Restrict the assessment to KPIs owned by this principal.",
    )
    parser.add_argument(
        "--client",
        metavar="CLIENT_ID",
        default=os.getenv("ACTIVE_CLIENT_ID"),
        required=not os.getenv("ACTIVE_CLIENT_ID"),
        help="Restrict the assessment to KPIs belonging to this client (e.g. 'lubricants'). "
             "Defaults to ACTIVE_CLIENT_ID env var if set, otherwise required.",
    )
    parser.add_argument(
        "--kpi",
        metavar="KPI_ID",
        default=None,
        help="(Reserved) restrict the assessment to a single KPI by ID.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run detection but skip persistence (results logged only).",
    )
    args = parser.parse_args()

    exit_code = asyncio.run(
        main(
            principal_id=args.principal,
            client_id=args.client,
            kpi_id=args.kpi,
            dry_run=args.dry_run,
        )
    )
    sys.exit(exit_code)
