"""
A9 Value Assurance Agent

Closes the insight-to-outcome loop: after a principal approves a solution at HITL,
this agent tracks whether that solution actually delivered measurable KPI impact.

Core capabilities (Phase 7A):
    1. register_solution        — record an approved solution with strategy snapshot
    2. evaluate_solution_impact — DiD attribution (baseline vs. current vs. control group)
    3. check_strategy_alignment — compare snapshot vs. current principal / registry state
    4. project_inaction_cost    — linear trend forecast if no action taken
    5. get_portfolio_summary    — aggregate attributable impact across all solutions
    6. generate_narrative       — LLM-generated executive summary for a solution

All LLM calls are routed through A9_LLM_Service_Agent via the orchestrator.
No direct anthropic/openai imports.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List, Optional

from src.agents.agent_config_models import A9ValueAssuranceAgentConfig
from src.agents.models.value_assurance_models import (
    AcceptedSolution,
    CheckStrategyAlignmentRequest,
    CheckStrategyAlignmentResponse,
    CompositeVerdict,
    ConfidenceLevel,
    EvaluateSolutionRequest,
    EvaluateSolutionResponse,
    GenerateNarrativeRequest,
    GenerateNarrativeResponse,
    ImpactEvaluation,
    InactionCostProjection,
    PortfolioSummaryRequest,
    ProjectInactionCostRequest,
    ProjectInactionCostResponse,
    RecordKPIMeasurementRequest,
    RecordKPIMeasurementResponse,
    RegisterSolutionRequest,
    RegisterSolutionResponse,
    SolutionPhase,
    SolutionVerdict,
    UpdateSolutionPhaseRequest,
    UpdateSolutionPhaseResponse,
    StrategyAlignment,
    StrategyAlignmentCheck,
    StrategyAwarePortfolio,
    StrategySnapshot,
)
from src.agents.new.a9_llm_service_agent import (
    A9_LLM_AnalysisRequest,
)
from src.llm_services.claude_service import ClaudeTaskType, get_claude_model_for_task

logger = logging.getLogger(__name__)

# Model used for narrative generation — cheap, fast
_NARRATIVE_MODEL = get_claude_model_for_task(ClaudeTaskType.NLP_PARSING)


# ---------------------------------------------------------------------------
# Composite verdict lookup matrix
# ---------------------------------------------------------------------------

# Keys: (SolutionVerdict, StrategyAlignment)
_COMPOSITE_MATRIX: Dict[tuple, Dict[str, Any]] = {
    (SolutionVerdict.VALIDATED, StrategyAlignment.ALIGNED): {
        "label": "Full success",
        "include_in_roi": True,
        "exec_attention": False,
        "action": "Document outcome and replicate approach.",
    },
    (SolutionVerdict.VALIDATED, StrategyAlignment.DRIFTED): {
        "label": "Misdirected win",
        "include_in_roi": True,
        "exec_attention": True,
        "action": "Re-align solution focus with current priorities.",
    },
    (SolutionVerdict.VALIDATED, StrategyAlignment.SUPERSEDED): {
        "label": "Obsolete win",
        "include_in_roi": False,
        "exec_attention": False,
        "action": "Archive — strategy has moved on.",
    },
    (SolutionVerdict.PARTIAL, StrategyAlignment.ALIGNED): {
        "label": "Work in progress",
        "include_in_roi": True,
        "exec_attention": False,
        "action": "Extend measurement window; check implementation completeness.",
    },
    (SolutionVerdict.PARTIAL, StrategyAlignment.DRIFTED): {
        "label": "Partial misdirection",
        "include_in_roi": False,
        "exec_attention": True,
        "action": "Review whether continued investment is warranted.",
    },
    (SolutionVerdict.PARTIAL, StrategyAlignment.SUPERSEDED): {
        "label": "Acceptable loss",
        "include_in_roi": False,
        "exec_attention": False,
        "action": "Close out; redirect resources to current priorities.",
    },
    (SolutionVerdict.FAILED, StrategyAlignment.ALIGNED): {
        "label": "Failure",
        "include_in_roi": False,
        "exec_attention": True,
        "action": "Root-cause analysis required; escalate to principal.",
    },
    (SolutionVerdict.FAILED, StrategyAlignment.DRIFTED): {
        "label": "Strategic waste",
        "include_in_roi": False,
        "exec_attention": True,
        "action": "Immediate review — resources spent on wrong priority.",
    },
    (SolutionVerdict.FAILED, StrategyAlignment.SUPERSEDED): {
        "label": "Irrelevant failure",
        "include_in_roi": False,
        "exec_attention": False,
        "action": "Archive — strategy has moved on; failure no longer material.",
    },
    # MEASURING is a transient state; provide a sensible default
    (SolutionVerdict.MEASURING, StrategyAlignment.ALIGNED): {
        "label": "In measurement",
        "include_in_roi": False,
        "exec_attention": False,
        "action": "Continue monitoring; re-evaluate at window close.",
    },
    (SolutionVerdict.MEASURING, StrategyAlignment.DRIFTED): {
        "label": "Measuring — priorities drifted",
        "include_in_roi": False,
        "exec_attention": True,
        "action": "Re-confirm measurement criteria given priority shift.",
    },
    (SolutionVerdict.MEASURING, StrategyAlignment.SUPERSEDED): {
        "label": "Measuring — superseded",
        "include_in_roi": False,
        "exec_attention": False,
        "action": "Consider stopping measurement; strategy has moved on.",
    },
}


def _build_composite_verdict(
    kpi_verdict: SolutionVerdict,
    strategy_verdict: StrategyAlignment,
) -> CompositeVerdict:
    entry = _COMPOSITE_MATRIX.get(
        (kpi_verdict, strategy_verdict),
        {
            "label": f"{kpi_verdict.value} / {strategy_verdict.value}",
            "include_in_roi": False,
            "exec_attention": False,
            "action": "Review manually.",
        },
    )
    return CompositeVerdict(
        kpi_verdict=kpi_verdict,
        strategy_verdict=strategy_verdict,
        composite_label=entry["label"],
        include_in_roi_totals=entry["include_in_roi"],
        recommended_action=entry["action"],
        executive_attention_required=entry["exec_attention"],
    )


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


class A9_Value_Assurance_Agent:
    """
    Value Assurance Agent.

    Tracks whether human-approved solutions from Solution Finder actually deliver
    their expected KPI impact, using counterfactual (DiD) attribution and
    strategy-context drift detection.

    Registration:
        Class name starts with A9_ and ends with _Agent; async ``create``
        classmethod is discovered by AgentBootstrap.
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> "A9_Value_Assurance_Agent":
        """
        Factory classmethod — used by AgentBootstrap / AgentRegistry.

        Creates the agent and opens its connections.
        """
        inst = cls(config or {})
        await inst.connect()
        return inst

    # create_from_registry is the canonical protocol alias
    @classmethod
    async def create_from_registry(
        cls, config: Dict[str, Any] = None
    ) -> "A9_Value_Assurance_Agent":
        return await cls.create(config)

    def __init__(self, config: Dict[str, Any]) -> None:
        self.name = "A9_Value_Assurance_Agent"
        self.version = "1.0.0"
        self.config = A9ValueAssuranceAgentConfig(**(config or {}))
        self.logger = logging.getLogger(self.__class__.__name__)

        # In-memory store backed by Supabase persistence (Phase 7C).
        self._solutions_store: Dict[str, AcceptedSolution] = {}
        self._va_store: Optional[Any] = None  # VASolutionsStore — initialized in connect()

        # Injected by orchestrator during connect()
        self.orchestrator: Optional[Any] = None
        self._llm_service: Optional[Any] = None
        self._registry_factory: Optional[Any] = None
        self._pc_agent: Optional[Any] = None

    async def connect(self, orchestrator: Any = None) -> bool:
        """
        Open connections and discover peer agents.

        Args:
            orchestrator: Optional A9_Orchestrator_Agent instance.  When supplied
                          the agent resolves A9_LLM_Service_Agent and
                          A9_Principal_Context_Agent through it.
        """
        try:
            self.orchestrator = orchestrator

            # Acquire registry factory for KPI / data-product lookups
            try:
                from src.registry.factory import RegistryFactory
                self._registry_factory = RegistryFactory()
            except Exception as exc:
                self.logger.warning(
                    "%s: RegistryFactory unavailable — alignment checks will be partial: %s",
                    self.name, exc,
                )

            if orchestrator is not None:
                try:
                    self._llm_service = await orchestrator.get_agent("A9_LLM_Service_Agent")
                except Exception as exc:
                    self.logger.warning(
                        "%s: LLM service via orchestrator unavailable: %s", self.name, exc
                    )
                try:
                    self._pc_agent = await orchestrator.get_agent(
                        "A9_Principal_Context_Agent"
                    )
                except Exception as exc:
                    self.logger.warning(
                        "%s: PC Agent via orchestrator unavailable: %s", self.name, exc
                    )
            else:
                # Fallback: try AgentRegistry directly (useful in unit tests)
                try:
                    from src.agents.new.a9_orchestrator_agent import AgentRegistry
                    self._llm_service = await AgentRegistry.get_agent("A9_LLM_Service_Agent")
                except Exception as exc:
                    self.logger.warning(
                        "%s: LLM service via AgentRegistry unavailable: %s", self.name, exc
                    )

            # Initialize Supabase persistence (non-fatal if unavailable)
            try:
                from src.database.va_solutions_store import VASolutionsStore
                self._va_store = VASolutionsStore()
                if self._va_store.enabled:
                    self.logger.info("%s: Supabase VA persistence enabled", self.name)
                else:
                    self.logger.info("%s: Supabase VA persistence disabled (env vars not set)", self.name)
            except Exception as exc:
                self.logger.warning("%s: VASolutionsStore init failed (non-fatal): %s", self.name, exc)
                self._va_store = None

            self.logger.info(
                "%s: connected (llm=%s, pc=%s, registry=%s, supabase=%s)",
                self.name,
                self._llm_service is not None,
                self._pc_agent is not None,
                self._registry_factory is not None,
                self._va_store is not None and self._va_store.enabled,
            )
            return True
        except Exception as exc:
            self.logger.error("%s: connect error: %s", self.name, exc)
            return False

    async def disconnect(self) -> None:
        """Release resources."""
        self.logger.info("%s: disconnected", self.name)

    # ------------------------------------------------------------------
    # Entrypoint 1 — register_solution
    # ------------------------------------------------------------------

    async def register_solution(
        self, request: RegisterSolutionRequest
    ) -> RegisterSolutionResponse:
        """
        Record a HITL-approved solution and begin measurement.

        If no strategy_snapshot is provided the agent builds a minimal one from
        the Principal Context Agent if available, otherwise uses safe defaults.
        """
        if self.config.log_all_requests:
            self.logger.info(
                "%s: register_solution — req=%s principal=%s kpi=%s",
                self.name, request.request_id, request.principal_id, request.kpi_id,
            )

        # Deterministic ID: same KPI + same situation always produces the same solution_id.
        # Prevents duplicate rows when the same HITL approval fires more than once
        # (e.g. dev re-runs or retry paths). The upsert on `id` then merges rather than inserts.
        import hashlib as _hashlib
        _dedup_key = f"{request.kpi_id}:{request.situation_id or ''}"
        solution_id = _hashlib.sha256(_dedup_key.encode()).hexdigest()[:32]

        # Build strategy snapshot if not supplied
        snapshot = request.strategy_snapshot or await self._build_strategy_snapshot(
            request
        )

        # --- Compute three-trajectory projections ---
        approved_at = _utcnow()
        baseline = snapshot.kpi_threshold_at_approval
        window_months = max(request.measurement_window_days // 30, 1)
        inaction_horizon = max(window_months * 2, 12)

        # Pre-approval slope: rate of KPI change per month before approval
        pre_slope = 0.0
        if request.pre_approval_kpi_value is not None and baseline != 0:
            # Assume comparison period is ~1 month by default
            pre_slope = baseline - request.pre_approval_kpi_value  # positive = improving

        # Inaction trend: extrapolate pre-approval decline (negative slope = deteriorating)
        inaction_trend = [baseline + pre_slope * m for m in range(inaction_horizon + 1)]

        # Expected trend: linear interpolation from baseline to baseline + midpoint recovery
        midpoint_recovery = (request.expected_impact_lower + request.expected_impact_upper) / 2.0
        expected_trend = [
            baseline + midpoint_recovery * (m / window_months) if window_months > 0 else baseline
            for m in range(window_months + 1)
        ]

        # Actual trend: starts with baseline at approval
        actual_trend = [baseline]
        actual_trend_dates = [approved_at]

        solution = AcceptedSolution(
            solution_id=solution_id,
            situation_id=request.situation_id,
            kpi_id=request.kpi_id,
            principal_id=request.principal_id,
            approved_at=approved_at,
            solution_description=request.solution_description,
            expected_impact_lower=request.expected_impact_lower,
            expected_impact_upper=request.expected_impact_upper,
            measurement_window_days=request.measurement_window_days,
            status=SolutionVerdict.MEASURING,
            phase=SolutionPhase.APPROVED,
            strategy_snapshot=snapshot,
            ma_market_signals=request.ma_market_signals,
            control_group_segments=request.control_group_segments,
            benchmark_segments=request.benchmark_segments,
            # Trajectory arrays
            inaction_trend=inaction_trend,
            expected_trend=expected_trend,
            inaction_horizon_months=inaction_horizon,
            actual_trend=actual_trend,
            actual_trend_dates=actual_trend_dates,
            baseline_kpi_value=baseline,
            pre_approval_slope=pre_slope,
        )

        self._solutions_store[solution_id] = solution

        # Persist to Supabase (non-fatal)
        if self._va_store and self._va_store.enabled:
            try:
                await self._va_store.upsert_solution(solution)
            except Exception as exc:
                self.logger.warning("%s: Supabase upsert failed (non-fatal): %s", self.name, exc)

        self.logger.info("%s: solution registered — id=%s", self.name, solution_id)

        return RegisterSolutionResponse(
            solution_id=solution_id,
            status=SolutionVerdict.MEASURING,
            phase=SolutionPhase.APPROVED,
            message=f"Solution approved and registered (window={request.measurement_window_days}d).",
        )

    # ------------------------------------------------------------------
    # Entrypoint 2 — evaluate_solution_impact
    # ------------------------------------------------------------------

    async def evaluate_solution_impact(
        self, request: EvaluateSolutionRequest
    ) -> EvaluateSolutionResponse:
        """
        Run Difference-in-Differences attribution and determine verdict.

        Modifies the in-memory solution record with the resulting ImpactEvaluation.
        """
        if self.config.log_all_requests:
            self.logger.info(
                "%s: evaluate_solution_impact — req=%s sol=%s",
                self.name, request.request_id, request.solution_id,
            )

        solution = self._solutions_store.get(request.solution_id)
        if solution is None:
            raise ValueError(
                f"Solution '{request.solution_id}' not found in store."
            )

        baseline_kpi_value = solution.strategy_snapshot.kpi_threshold_at_approval
        current_kpi_value = request.current_kpi_value

        # DiD components
        total_change = current_kpi_value - baseline_kpi_value
        control_change = (
            mean(request.control_group_kpi_values)
            if request.control_group_kpi_values
            else 0.0
        )
        market_recovery = request.market_recovery_estimate or 0.0
        seasonal = request.seasonal_estimate or 0.0

        attributable = total_change - control_change - market_recovery - seasonal

        # Verdict
        expected_lower = solution.expected_impact_lower
        expected_upper = solution.expected_impact_upper

        if attributable >= expected_lower and attributable > 0:
            verdict = SolutionVerdict.VALIDATED
        elif attributable > 0:
            verdict = SolutionVerdict.PARTIAL
        else:
            verdict = SolutionVerdict.FAILED

        # Confidence
        signals_present = sum([
            bool(request.control_group_kpi_values),
            bool(request.market_recovery_estimate is not None),
            bool(request.seasonal_estimate is not None),
        ])
        if signals_present == 3:
            confidence = ConfidenceLevel.HIGH
            confidence_rationale = (
                "Control group, market recovery, and seasonal estimates all provided."
            )
        elif signals_present >= 1:
            confidence = ConfidenceLevel.MODERATE
            confidence_rationale = (
                f"{signals_present}/3 attribution inputs provided; some confounders unaccounted."
            )
        else:
            confidence = ConfidenceLevel.LOW
            confidence_rationale = (
                "No control group or external estimates provided; "
                "attributable impact equals total KPI change."
            )

        # Strategy alignment
        alignment_req = CheckStrategyAlignmentRequest(
            request_id=request.request_id,
            principal_id=request.principal_id,
            solution_id=request.solution_id,
        )
        alignment_resp = await self.check_strategy_alignment(alignment_req)
        strategy_check = alignment_resp.alignment

        # Composite verdict
        composite = _build_composite_verdict(verdict, strategy_check.alignment_verdict)

        # Attribution method description
        method_parts = ["Total change"]
        if request.control_group_kpi_values:
            method_parts.append("minus control-group mean")
        if request.market_recovery_estimate is not None:
            method_parts.append("minus market-driven recovery estimate")
        if request.seasonal_estimate is not None:
            method_parts.append("minus seasonal component")
        attribution_method = " ".join(method_parts) + " (Difference-in-Differences)."

        evaluation = ImpactEvaluation(
            solution_id=request.solution_id,
            baseline_kpi_value=baseline_kpi_value,
            current_kpi_value=current_kpi_value,
            total_kpi_change=total_change,
            control_group_change=control_change,
            market_driven_recovery=market_recovery,
            seasonal_component=seasonal,
            attributable_impact=attributable,
            expected_impact_lower=expected_lower,
            expected_impact_upper=expected_upper,
            verdict=verdict,
            confidence=confidence,
            confidence_rationale=confidence_rationale,
            attribution_method=attribution_method,
            control_group_description=(
                f"Mean of {len(request.control_group_kpi_values)} control observations."
                if request.control_group_kpi_values
                else None
            ),
            market_context_summary=(
                "; ".join(solution.ma_market_signals[:3])
                if solution.ma_market_signals
                else None
            ),
            strategy_check=strategy_check,
            composite_verdict=composite,
            evaluated_at=_utcnow(),
        )

        # Persist evaluation, update status + auto-transition phase to COMPLETE
        updated_solution = solution.model_copy(
            update={
                "impact_evaluation": evaluation,
                "status": verdict,
                "phase": SolutionPhase.COMPLETE,
                "completed_at": _utcnow(),
            }
        )
        self._solutions_store[request.solution_id] = updated_solution

        # Persist to Supabase (non-fatal)
        if self._va_store and self._va_store.enabled:
            try:
                await self._va_store.upsert_evaluation(evaluation, request.solution_id)
                await self._va_store.update_status(request.solution_id, verdict.value)
                await self._va_store.update_phase(request.solution_id, SolutionPhase.COMPLETE.value, completed_at=_utcnow())
            except Exception as exc:
                self.logger.warning("%s: Supabase evaluation persist failed (non-fatal): %s", self.name, exc)

        return EvaluateSolutionResponse(
            solution_id=request.solution_id,
            evaluation=evaluation,
        )

    # ------------------------------------------------------------------
    # Entrypoint 3 — check_strategy_alignment
    # ------------------------------------------------------------------

    async def check_strategy_alignment(
        self, request: CheckStrategyAlignmentRequest
    ) -> CheckStrategyAlignmentResponse:
        """
        Compare the strategy snapshot against the current principal / registry state.

        Falls back gracefully when PC Agent or RegistryFactory are unavailable.
        """
        if self.config.log_all_requests:
            self.logger.info(
                "%s: check_strategy_alignment — req=%s sol=%s",
                self.name, request.request_id, request.solution_id,
            )

        solution = self._solutions_store.get(request.solution_id)
        if solution is None:
            raise ValueError(
                f"Solution '{request.solution_id}' not found in store."
            )

        snapshot: StrategySnapshot = solution.strategy_snapshot
        original_priorities = snapshot.principal_priorities

        # --- Retrieve current principal priorities ---
        current_priorities: List[str] = []
        principal_still_accountable = True
        current_principal_id: Optional[str] = None
        drift_factors: List[str] = []

        if self._pc_agent is not None:
            try:
                from src.agents.models.principal_context_models import (
                    PrincipalContextRequest,
                )
                pc_req = PrincipalContextRequest(
                    request_id=request.request_id,
                    principal_id=request.principal_id,
                )
                pc_resp = await self._pc_agent.get_principal_context(pc_req)
                if pc_resp and hasattr(pc_resp, "principal"):
                    p = pc_resp.principal
                    current_priorities = getattr(p, "priorities", []) or []
                    current_principal_id = getattr(p, "id", None)
                    if current_principal_id != request.principal_id:
                        principal_still_accountable = False
                        drift_factors.append("Principal account ID changed.")
            except Exception as exc:
                self.logger.warning(
                    "%s: PC Agent lookup failed — defaulting to ALIGNED: %s",
                    self.name, exc,
                )
                current_priorities = list(original_priorities)
        else:
            # PC Agent not available — assume priorities unchanged
            current_priorities = list(original_priorities)

        # --- Priority overlap ---
        orig_set = set(p.lower() for p in original_priorities)
        curr_set = set(p.lower() for p in current_priorities)
        if orig_set and curr_set:
            overlap = len(orig_set & curr_set) / max(len(orig_set), len(curr_set))
        elif not orig_set and not curr_set:
            overlap = 1.0
        else:
            overlap = 0.0

        priority_drift = overlap < 0.5
        if priority_drift:
            drift_factors.append(f"Priority overlap dropped to {overlap:.0%}.")

        # --- KPI still monitored ---
        kpi_still_monitored = True
        threshold_changed = False
        current_threshold: Optional[float] = None

        if self._registry_factory is not None:
            try:
                kpi_provider = self._registry_factory.get_provider("kpi")
                if kpi_provider is not None:
                    kpi_record = kpi_provider.get(solution.kpi_id)
                    if kpi_record is None:
                        kpi_still_monitored = False
                        drift_factors.append(f"KPI '{solution.kpi_id}' no longer in registry.")
                    else:
                        # Try to extract current threshold
                        raw_threshold = (
                            getattr(kpi_record, "warning_threshold", None)
                            or getattr(kpi_record, "threshold", None)
                        )
                        if raw_threshold is not None:
                            try:
                                current_threshold = float(raw_threshold)
                                pct_change = abs(
                                    (current_threshold - snapshot.kpi_threshold_at_approval)
                                    / max(abs(snapshot.kpi_threshold_at_approval), 1e-9)
                                )
                                if pct_change > 0.20:
                                    threshold_changed = True
                                    drift_factors.append(
                                        f"KPI threshold changed by {pct_change:.0%} "
                                        f"(was {snapshot.kpi_threshold_at_approval}, "
                                        f"now {current_threshold})."
                                    )
                            except (TypeError, ValueError):
                                pass
            except Exception as exc:
                self.logger.warning(
                    "%s: KPI registry lookup failed: %s", self.name, exc
                )

        # --- Data product still active ---
        data_product_active = True
        if self._registry_factory is not None:
            try:
                dp_provider = self._registry_factory.get_provider("data_product")
                if dp_provider is not None:
                    dp_record = dp_provider.get(snapshot.data_product_id)
                    if dp_record is None:
                        data_product_active = False
                        drift_factors.append(
                            f"Data product '{snapshot.data_product_id}' no longer in registry."
                        )
            except Exception as exc:
                self.logger.warning(
                    "%s: Data product registry lookup failed: %s", self.name, exc
                )

        # --- Alignment verdict ---
        if not data_product_active or not principal_still_accountable:
            alignment_verdict = StrategyAlignment.SUPERSEDED
        elif priority_drift or threshold_changed:
            alignment_verdict = StrategyAlignment.DRIFTED
        else:
            alignment_verdict = StrategyAlignment.ALIGNED

        drift_summary: Optional[str] = (
            " ".join(drift_factors) if drift_factors else None
        )

        alignment = StrategyAlignmentCheck(
            original_priorities=original_priorities,
            current_priorities=current_priorities,
            priority_drift=priority_drift,
            priority_overlap=overlap,
            kpi_still_monitored=kpi_still_monitored,
            threshold_changed=threshold_changed,
            current_threshold=current_threshold,
            business_process_active=True,  # MVP: assume active unless proven otherwise
            data_product_active=data_product_active,
            principal_still_accountable=principal_still_accountable,
            current_principal_id=current_principal_id,
            alignment_verdict=alignment_verdict,
            drift_factors=drift_factors,
            drift_summary=drift_summary,
        )

        # Use the existing KPI verdict if an evaluation exists; otherwise MEASURING
        existing_verdict = (
            solution.impact_evaluation.verdict
            if solution.impact_evaluation is not None
            else SolutionVerdict.MEASURING
        )
        composite = _build_composite_verdict(existing_verdict, alignment_verdict)

        return CheckStrategyAlignmentResponse(
            solution_id=request.solution_id,
            alignment=alignment,
            composite=composite,
        )

    # ------------------------------------------------------------------
    # Entrypoint 3b — record_kpi_measurement
    # ------------------------------------------------------------------

    async def record_kpi_measurement(
        self, request: RecordKPIMeasurementRequest
    ) -> RecordKPIMeasurementResponse:
        """
        Append a monthly KPI measurement to the solution's actual_trend.

        Called manually (Portfolio UI), by scheduled trigger, or by the
        Enterprise Assessment Pipeline (Phase 9).
        """
        if self.config.log_all_requests:
            self.logger.info(
                "%s: record_kpi_measurement — req=%s sol=%s value=%.4f",
                self.name, request.request_id, request.solution_id, request.kpi_value,
            )

        solution = self._solutions_store.get(request.solution_id)
        if solution is None:
            raise ValueError(
                f"Solution '{request.solution_id}' not found in store."
            )

        measured_at = request.measured_at or _utcnow()

        # Append to in-memory arrays
        new_actual = list(solution.actual_trend) + [request.kpi_value]
        new_dates = list(solution.actual_trend_dates) + [measured_at]

        updated = solution.model_copy(
            update={"actual_trend": new_actual, "actual_trend_dates": new_dates}
        )
        self._solutions_store[request.solution_id] = updated

        # Persist to Supabase (non-fatal)
        if self._va_store and self._va_store.enabled:
            try:
                await self._va_store.append_actual_measurement(
                    request.solution_id, request.kpi_value, measured_at
                )
            except Exception as exc:
                self.logger.warning(
                    "%s: Supabase measurement append failed (non-fatal): %s",
                    self.name, exc,
                )

        self.logger.info(
            "%s: measurement recorded — sol=%s points=%d",
            self.name, request.solution_id, len(new_actual),
        )

        return RecordKPIMeasurementResponse(
            solution_id=request.solution_id,
            actual_trend=new_actual,
            actual_trend_dates=new_dates,
            message=f"Measurement recorded ({len(new_actual)} total data points).",
        )

    # ------------------------------------------------------------------
    # Entrypoint 3c — update_solution_phase
    # ------------------------------------------------------------------

    _PHASE_ORDER = [
        SolutionPhase.APPROVED,
        SolutionPhase.IMPLEMENTING,
        SolutionPhase.LIVE,
        SolutionPhase.MEASURING,
        SolutionPhase.COMPLETE,
    ]

    async def update_solution_phase(
        self, request: UpdateSolutionPhaseRequest
    ) -> UpdateSolutionPhaseResponse:
        """
        Advance a solution through its lifecycle.

        Valid forward transitions only:
            APPROVED → IMPLEMENTING → LIVE → MEASURING → COMPLETE

        On LIVE transition: sets go_live_at and resets actual_trend for
        fresh measurement from the deployment date.
        """
        if self.config.log_all_requests:
            self.logger.info(
                "%s: update_solution_phase — req=%s sol=%s → %s",
                self.name, request.request_id, request.solution_id, request.new_phase.value,
            )

        solution = self._solutions_store.get(request.solution_id)
        if solution is None:
            raise ValueError(f"Solution '{request.solution_id}' not found in store.")

        current_idx = self._PHASE_ORDER.index(solution.phase)
        new_idx = self._PHASE_ORDER.index(request.new_phase)

        if new_idx <= current_idx:
            raise ValueError(
                f"Cannot transition from {solution.phase.value} to {request.new_phase.value}. "
                f"Only forward transitions are allowed."
            )

        updates: Dict[str, Any] = {"phase": request.new_phase}

        if request.new_phase == SolutionPhase.LIVE:
            # Go-live is a HITL event — reset actual tracking from deployment date
            now = _utcnow()
            updates["go_live_at"] = now
            updates["actual_trend"] = [solution.baseline_kpi_value]
            updates["actual_trend_dates"] = [now]

        if request.new_phase == SolutionPhase.COMPLETE:
            updates["completed_at"] = _utcnow()

        updated = solution.model_copy(update=updates)
        self._solutions_store[request.solution_id] = updated

        # Persist to Supabase (non-fatal)
        if self._va_store and self._va_store.enabled:
            try:
                await self._va_store.update_phase(
                    request.solution_id,
                    request.new_phase.value,
                    go_live_at=updates.get("go_live_at"),
                    completed_at=updates.get("completed_at"),
                )
            except Exception as exc:
                self.logger.warning(
                    "%s: Supabase phase update failed (non-fatal): %s", self.name, exc,
                )

        self.logger.info(
            "%s: phase updated — sol=%s %s → %s",
            self.name, request.solution_id, solution.phase.value, request.new_phase.value,
        )

        return UpdateSolutionPhaseResponse(
            solution_id=request.solution_id,
            phase=request.new_phase,
            message=f"Phase updated to {request.new_phase.value}.",
        )

    # ------------------------------------------------------------------
    # Entrypoint 4 — project_inaction_cost
    # ------------------------------------------------------------------

    async def project_inaction_cost(
        self, request: ProjectInactionCostRequest
    ) -> ProjectInactionCostResponse:
        """
        Fit a linear trend to historical_trend and project forward 30 and 90 days.

        Revenue impact is a heuristic: 1% KPI change ≈ 0.5% revenue impact.
        """
        if self.config.log_all_requests:
            self.logger.info(
                "%s: project_inaction_cost — req=%s kpi=%s",
                self.name, request.request_id, request.kpi_id,
            )

        trend = request.historical_trend
        n = len(trend)

        if n == 0:
            raise ValueError("historical_trend must contain at least one value.")

        current_value = request.current_kpi_value

        if n == 1:
            # No trend information — assume stable
            slope = 0.0
            trend_direction = "stable"
            trend_confidence = ConfidenceLevel.LOW
            projection_method = "No trend data — constant projection (LOW confidence)."
        else:
            # Ordinary least-squares slope using index as x-axis
            x_mean = (n - 1) / 2.0
            y_mean = sum(trend) / n
            num = sum((i - x_mean) * (trend[i] - y_mean) for i in range(n))
            den = sum((i - x_mean) ** 2 for i in range(n))
            slope = num / den if den != 0 else 0.0

            if slope < -0.001 * abs(y_mean if y_mean != 0 else 1):
                trend_direction = "deteriorating"
            elif slope > 0.001 * abs(y_mean if y_mean != 0 else 1):
                trend_direction = "recovering"
            else:
                trend_direction = "stable"

            trend_confidence = (
                ConfidenceLevel.MODERATE if n >= 5 else ConfidenceLevel.LOW
            )
            projection_method = (
                f"OLS linear regression over {n} observations "
                f"(slope={slope:+.4f}/period); heuristic revenue multiplier "
                f"{self.config.inaction_cost_revenue_multiplier}."
            )

        projected_30d = current_value + slope * 30
        projected_90d = current_value + slope * 90

        # Revenue impact heuristic — flagged LOW confidence regardless
        rev_30d: Optional[float] = None
        rev_90d: Optional[float] = None
        if current_value != 0:
            pct_change_30 = (projected_30d - current_value) / abs(current_value)
            pct_change_90 = (projected_90d - current_value) / abs(current_value)
            rev_30d = pct_change_30 * self.config.inaction_cost_revenue_multiplier
            rev_90d = pct_change_90 * self.config.inaction_cost_revenue_multiplier

        projection = InactionCostProjection(
            solution_id=request.situation_id,  # situation_id is the closest proxy pre-registration
            kpi_id=request.kpi_id,
            current_kpi_value=current_value,
            projected_kpi_value_30d=projected_30d,
            projected_kpi_value_90d=projected_90d,
            estimated_revenue_impact_30d=rev_30d,
            estimated_revenue_impact_90d=rev_90d,
            trend_direction=trend_direction,
            trend_confidence=trend_confidence,
            projection_method=projection_method,
            projected_at=_utcnow(),
        )

        return ProjectInactionCostResponse(projection=projection)

    # ------------------------------------------------------------------
    # Entrypoint 5 — get_portfolio_summary
    # ------------------------------------------------------------------

    async def get_portfolio_summary(
        self, request: PortfolioSummaryRequest
    ) -> StrategyAwarePortfolio:
        """
        Aggregate all in-store solutions into a portfolio summary.

        When include_superseded=False, solutions whose strategy verdict is
        SUPERSEDED are excluded from counts and ROI totals (but still returned
        in the solutions list so the caller has full visibility).
        """
        if self.config.log_all_requests:
            self.logger.info(
                "%s: get_portfolio_summary — req=%s principal=%s",
                self.name, request.request_id, request.principal_id,
            )

        # Load from Supabase if in-memory store is empty (e.g., after restart)
        if not self._solutions_store and self._va_store and self._va_store.enabled:
            try:
                rows = await self._va_store.get_solutions_by_principal(request.principal_id)
                for row in rows:
                    try:
                        sol = AcceptedSolution(**row)
                        self._solutions_store[sol.solution_id] = sol
                    except Exception as parse_exc:
                        self.logger.warning(
                            "%s: failed to parse Supabase solution row: %s", self.name, parse_exc
                        )
            except Exception as exc:
                self.logger.warning(
                    "%s: Supabase portfolio load failed (non-fatal): %s", self.name, exc
                )

        all_solutions = list(self._solutions_store.values())

        total = validated = partial = failed = measuring = 0
        total_attributable = 0.0
        roi_eligible = 0
        aligned = drifted = superseded = 0
        exec_attention: List[str] = []

        for sol in all_solutions:
            total += 1

            if sol.status == SolutionVerdict.VALIDATED:
                validated += 1
            elif sol.status == SolutionVerdict.PARTIAL:
                partial += 1
            elif sol.status == SolutionVerdict.FAILED:
                failed += 1
            else:
                measuring += 1

            if sol.impact_evaluation is not None:
                ev = sol.impact_evaluation
                strategy_v = ev.strategy_check.alignment_verdict
                if strategy_v == StrategyAlignment.ALIGNED:
                    aligned += 1
                elif strategy_v == StrategyAlignment.DRIFTED:
                    drifted += 1
                else:
                    superseded += 1

                # Only count superseded if explicitly requested
                if request.include_superseded or strategy_v != StrategyAlignment.SUPERSEDED:
                    if ev.composite_verdict.include_in_roi_totals:
                        total_attributable += ev.attributable_impact
                        roi_eligible += 1

                if ev.composite_verdict.executive_attention_required:
                    exec_attention.append(sol.solution_id)
            else:
                # No evaluation yet — treat as aligned for counting purposes
                aligned += 1

        return StrategyAwarePortfolio(
            total_solutions=total,
            validated_count=validated,
            partial_count=partial,
            failed_count=failed,
            measuring_count=measuring,
            total_attributable_impact=total_attributable,
            roi_eligible_solutions=roi_eligible,
            strategy_aligned_count=aligned,
            strategy_drifted_count=drifted,
            strategy_superseded_count=superseded,
            executive_attention_required=exec_attention,
            solutions=all_solutions,
        )

    # ------------------------------------------------------------------
    # Entrypoint 6 — generate_narrative
    # ------------------------------------------------------------------

    async def generate_narrative(
        self, request: GenerateNarrativeRequest
    ) -> GenerateNarrativeResponse:
        """
        Generate an LLM executive narrative for a solution's outcome.

        Uses claude-haiku-4-5-20251001 (NLP_PARSING task) for cost efficiency.
        Falls back to a structured text summary if the LLM service is unavailable.
        """
        if self.config.log_all_requests:
            self.logger.info(
                "%s: generate_narrative — req=%s sol=%s",
                self.name, request.request_id, request.solution_id,
            )

        solution = self._solutions_store.get(request.solution_id)
        if solution is None:
            raise ValueError(
                f"Solution '{request.solution_id}' not found in store."
            )

        evaluation = solution.impact_evaluation

        # Build prompt content
        ev_section = ""
        if evaluation is not None:
            ev_section = (
                f"KPI verdict: {evaluation.verdict.value}\n"
                f"Attributable impact: {evaluation.attributable_impact:+.4f} "
                f"(baseline {evaluation.baseline_kpi_value:.4f} → "
                f"current {evaluation.current_kpi_value:.4f})\n"
                f"Confidence: {evaluation.confidence.value} — {evaluation.confidence_rationale}\n"
                f"Strategy alignment: {evaluation.strategy_check.alignment_verdict.value}\n"
                f"Composite: {evaluation.composite_verdict.composite_label}\n"
                f"Recommended action: {evaluation.composite_verdict.recommended_action}\n"
            )
            if evaluation.strategy_check.drift_summary:
                ev_section += (
                    f"Drift factors: {evaluation.strategy_check.drift_summary}\n"
                )
        else:
            ev_section = "Solution is still in the measurement window; no evaluation available yet.\n"

        prompt = (
            "You are an executive communications specialist for a finance operations team.\n\n"
            f"Solution approved: {solution.solution_description}\n"
            f"KPI tracked: {solution.kpi_id}\n"
            f"Approved: {solution.approved_at}\n"
            f"Expected impact range: [{solution.expected_impact_lower:.4f}, "
            f"{solution.expected_impact_upper:.4f}]\n\n"
            f"Outcome summary:\n{ev_section}\n"
            "Write a concise (3–5 sentence) executive narrative that explains:\n"
            "1. What was attempted and why.\n"
            "2. What the data shows happened.\n"
            "3. Whether the investment was strategically sound.\n"
            "4. What the recommended next action is.\n"
            "Be direct, data-anchored, and avoid jargon. Do not use bullet points."
        )

        narrative = await self._call_llm_for_narrative(
            request_id=request.request_id,
            principal_id=request.principal_id,
            prompt=prompt,
        )

        # Persist narrative back to the solution record
        updated = solution.model_copy(update={"narrative": narrative})
        self._solutions_store[request.solution_id] = updated

        # Persist to Supabase (non-fatal)
        if self._va_store and self._va_store.enabled:
            try:
                await self._va_store.upsert_solution(updated)
            except Exception as exc:
                self.logger.warning("%s: Supabase narrative persist failed (non-fatal): %s", self.name, exc)

        return GenerateNarrativeResponse(
            solution_id=request.solution_id,
            narrative=narrative,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _build_strategy_snapshot(
        self, request: RegisterSolutionRequest
    ) -> StrategySnapshot:
        """
        Construct a StrategySnapshot from available context.

        Tries to enrich from the Principal Context Agent when connected;
        falls back to minimal defaults so registration always succeeds.
        """
        principal_role = "unknown"
        priorities: List[str] = []
        business_process_domain = "unknown"
        data_product_id = request.kpi_id  # fallback: use KPI id as proxy
        threshold_at_approval = 0.0
        key_assumptions: List[str] = []
        business_context_name = "unspecified"

        if self._pc_agent is not None:
            try:
                from src.agents.models.principal_context_models import (
                    PrincipalContextRequest,
                )
                pc_req = PrincipalContextRequest(
                    request_id=request.request_id,
                    principal_id=request.principal_id,
                )
                pc_resp = await self._pc_agent.get_principal_context(pc_req)
                if pc_resp and hasattr(pc_resp, "principal"):
                    p = pc_resp.principal
                    principal_role = getattr(p, "role", principal_role) or principal_role
                    priorities = getattr(p, "priorities", []) or []
                    business_process_domain = (
                        getattr(p, "primary_domain", business_process_domain)
                        or business_process_domain
                    )
            except Exception as exc:
                self.logger.warning(
                    "%s: could not enrich snapshot from PC Agent: %s", self.name, exc
                )

        if self._registry_factory is not None:
            try:
                kpi_provider = self._registry_factory.get_provider("kpi")
                if kpi_provider is not None:
                    kpi_record = kpi_provider.get(request.kpi_id)
                    if kpi_record is not None:
                        raw_t = (
                            getattr(kpi_record, "warning_threshold", None)
                            or getattr(kpi_record, "threshold", None)
                        )
                        if raw_t is not None:
                            try:
                                threshold_at_approval = float(raw_t)
                            except (TypeError, ValueError):
                                pass
                        dp_id = getattr(kpi_record, "data_product_id", None)
                        if dp_id:
                            data_product_id = dp_id
            except Exception as exc:
                self.logger.warning(
                    "%s: KPI lookup for snapshot failed: %s", self.name, exc
                )

        return StrategySnapshot(
            principal_priorities=priorities,
            principal_role=principal_role,
            business_process_domain=business_process_domain,
            data_product_id=data_product_id,
            kpi_threshold_at_approval=threshold_at_approval,
            key_assumptions=key_assumptions,
            business_context_name=business_context_name,
            captured_at=_utcnow(),
        )

    async def _call_llm_for_narrative(
        self, request_id: str, principal_id: str, prompt: str
    ) -> str:
        """
        Route narrative generation through A9_LLM_Service_Agent.

        Falls back to a structured text summary when the LLM is unavailable.
        """
        llm_service = self._llm_service

        # Attempt to acquire LLM service lazily if not already held
        if llm_service is None and self.orchestrator is not None:
            try:
                llm_service = await self.orchestrator.get_agent("A9_LLM_Service_Agent")
                self._llm_service = llm_service
            except Exception as exc:
                self.logger.warning(
                    "%s: LLM service lazy-acquire failed: %s", self.name, exc
                )

        if llm_service is None:
            # Graceful degradation
            self.logger.warning(
                "%s: LLM service unavailable; returning structured fallback narrative.",
                self.name,
            )
            return (
                "LLM service unavailable.  "
                "Please review the impact evaluation details directly."
            )

        try:
            llm_req = A9_LLM_AnalysisRequest(
                request_id=request_id,
                principal_id=principal_id,
                content=prompt,
                analysis_type="value_assurance_narrative",
                context="Executive narrative for approved solution outcome.",
                model=_NARRATIVE_MODEL,
                max_tokens=512,
            )
            if self.orchestrator is not None:
                resp = await self.orchestrator.execute_agent_method(
                    "A9_LLM_Service_Agent",
                    "analyze",
                    {"request": llm_req},
                )
            else:
                resp = await llm_service.analyze(llm_req)

            # Extract text from response
            if resp is None:
                return "No narrative generated."
            if hasattr(resp, "analysis") and isinstance(resp.analysis, dict):
                return resp.analysis.get("content", str(resp.analysis))
            if hasattr(resp, "content"):
                return str(resp.content)
            return str(resp)
        except Exception as exc:
            self.logger.warning(
                "%s: LLM narrative generation failed: %s", self.name, exc
            )
            return (
                f"Narrative generation encountered an error: {exc}. "
                "Please review the impact evaluation details directly."
            )
