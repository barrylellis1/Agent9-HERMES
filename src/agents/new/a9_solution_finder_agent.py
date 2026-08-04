# doc-sync-skip
"""
A9 Solution Finder Agent (MVP with optional LLM debate)
- Implements SolutionFinderProtocol
- Generates/evaluates solution options, builds trade-off matrix
- Emits a single HITL event per cycle (per PRD)
- Optional: persona debate via A9_LLM_Service_Agent when enabled in config
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List

from src.agents.agent_config_models import A9_Solution_Finder_Agent_Config
from src.agents.protocols.solution_finder_protocol import SolutionFinderProtocol
from src.agents.models.solution_finder_models import (
    SolutionFinderRequest,
    SolutionFinderResponse,
    SolutionOption,
    TradeOffCriterion,
    TradeOffMatrix,
    PerspectiveAnalysis,
    UnresolvedTension,
    # Phase 15 Stage B — unified trust/output schema
    SolutionAssumption,
    DecisionAsk,
    ImmediateAction,
    ImpactEstimate,
    RecoveryRange,
    SFSynthesisSchema,
)
from src.agents.new.a9_llm_service_agent import (
    A9_LLM_AnalysisRequest,
    A9_LLM_AnalysisResponse,
)
from src.llm_services.claude_service import get_claude_model_for_task, ClaudeTaskType
from src.registry.consulting_personas import (
    get_consulting_persona,
    get_council_preset,
    get_personas_for_principal,
    ConsultingPersona,
)
from src.registry.consulting_personas.consulting_persona_provider import (
    get_personas_for_decision_style,
    get_framing_context_for_decision_style,
    DECISION_STYLE_TO_PERSONA,
)


logger = logging.getLogger(__name__)


def _model_to_dict(obj: Any) -> Any:
    """Best-effort conversion of Pydantic/BaseModel objects to plain dicts."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    try:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
    except Exception:
        pass
    try:
        return dict(obj.__dict__)
    except Exception:
        return obj


def _limit(items: Optional[List[Any]], limit: int = 5) -> List[Any]:
    if not items:
        return []
    try:
        return list(items)[: max(0, limit)]
    except Exception:
        return list(items) if isinstance(items, list) else []


def _format_driver_entry(entry: Dict[str, Any]) -> Optional[str]:
    try:
        dim = entry.get("dimension")
        key = entry.get("key")
        delta = entry.get("delta")
        cur = entry.get("current_value") or entry.get("current")
        prev = entry.get("previous_value") or entry.get("previous")
        parts: List[str] = []
        if dim:
            parts.append(str(dim))
        if key is not None:
            parts.append(str(key))
        label = " / ".join(parts) if parts else None
        delta_val = None
        try:
            if delta is not None:
                delta_val = float(delta)
        except Exception:
            delta_val = None
        cur_val = None
        prev_val = None
        try:
            if cur is not None:
                cur_val = float(cur)
        except Exception:
            cur_val = None
        try:
            if prev is not None:
                prev_val = float(prev)
        except Exception:
            prev_val = None
        text_parts: List[str] = []
        if label:
            text_parts.append(label)
        if delta_val is not None:
            text_parts.append(f"Δ {delta_val:+,.2f}")
        if cur_val is not None and prev_val is not None:
            text_parts.append(f"current {cur_val:,.2f} vs prev {prev_val:,.2f}")
        elif cur_val is not None:
            text_parts.append(f"current {cur_val:,.2f}")
        if not text_parts:
            return None
        return "; ".join(text_parts)
    except Exception:
        return None


def _collect_text_entries(entries: Optional[List[Any]], limit: int = 4) -> List[str]:
    out: List[str] = []
    if not entries:
        return out
    for item in entries:
        if len(out) >= limit:
            break
        entry = _model_to_dict(item)
        if isinstance(entry, dict):
            txt = entry.get("text")
            if isinstance(txt, str) and txt.strip():
                out.append(txt.strip())
                continue
            formatted = _format_driver_entry(entry)
            if formatted:
                out.append(formatted)
        else:
            out.append(str(entry))
    return out


def _extract_deep_analysis_summary(da_ctx: Any) -> Dict[str, Any]:
    ctx = _model_to_dict(da_ctx)
    if not isinstance(ctx, dict):
        return {}

    # The workflow may pass the Deep Analysis workflow payload as:
    # {"plan": <DeepAnalysisResponse>, "execution": <DeepAnalysisResponse>}
    # Remember: execution contains the KPI drivers (change_points/kt/scqa), while plan
    # contains kpi_name/timeframe/dimensions. Prefer extracting from execution when present.
    exec_ctx = _model_to_dict(ctx.get("execution"))
    if isinstance(exec_ctx, dict):
        data_ctx: Dict[str, Any] = exec_ctx
    else:
        data_ctx = ctx

    summary: Dict[str, Any] = {}
    plan = _model_to_dict(ctx.get("plan"))
    if not isinstance(plan, dict) and isinstance(exec_ctx, dict):
        plan = _model_to_dict(exec_ctx.get("plan"))
    timeframe_map = _model_to_dict(data_ctx.get("timeframe_mapping"))

    def _first_str(value: Any) -> Optional[str]:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    kpi_name = None
    if isinstance(plan, dict):
        kpi_name = plan.get("kpi_name")
        _plan_client_id = plan.get("client_id")
        if _plan_client_id:
            summary["client_id"] = str(_plan_client_id)
    if not kpi_name:
        kpi_name = data_ctx.get("kpi_name")
    if kpi_name:
        summary["kpi_name"] = str(kpi_name)

    timeframe = None
    if isinstance(plan, dict):
        timeframe = plan.get("timeframe")
    if not timeframe and isinstance(timeframe_map, dict):
        timeframe = timeframe_map.get("current")
    if timeframe:
        summary["timeframe"] = str(timeframe)
    if isinstance(timeframe_map, dict) and timeframe_map.get("previous"):
        summary["comparison_timeframe"] = str(timeframe_map.get("previous"))

    scqa = _first_str(data_ctx.get("scqa_summary"))
    if scqa:
        summary["scqa_summary"] = scqa

    if isinstance(plan, dict):
        dims = plan.get("dimensions")
        if isinstance(dims, list) and dims:
            summary["dimension_focus"] = _limit([str(d) for d in dims if d], 6)

    change_points_raw = data_ctx.get("change_points") or []
    change_points: List[Dict[str, Any]] = []
    for cp in change_points_raw:
        cp_dict = _model_to_dict(cp)
        if isinstance(cp_dict, dict):
            slim = {
                "dimension": cp_dict.get("dimension"),
                "key": cp_dict.get("key"),
                "delta": cp_dict.get("delta"),
                "current_value": cp_dict.get("current_value"),
                "previous_value": cp_dict.get("previous_value"),
                "percent_growth": cp_dict.get("percent_growth"),
            }
            change_points.append(slim)
    if change_points:
        summary["top_change_points"] = _limit(change_points, 5)

    kt = _model_to_dict(data_ctx.get("kt_is_is_not"))
    if isinstance(kt, dict):
        summary["what_is_highlights"] = _collect_text_entries(kt.get("what_is"))
        summary["where_signals"] = _collect_text_entries(kt.get("where_is"))
        summary["when_signals"] = _collect_text_entries(kt.get("when_is"))
        # IS-NOT side: which dimensions/segments are NOT affected — eliminates solution space
        _where_not = _collect_text_entries(kt.get("where_is_not"))
        _what_not = _collect_text_entries(kt.get("what_is_not"))
        _when_not = _collect_text_entries(kt.get("when_is_not"))
        if _where_not:
            summary["where_is_not"] = _where_not
        if _what_not:
            summary["what_is_not"] = _what_not
        if _when_not:
            summary["when_is_not"] = _when_not

        # Benchmark segments: internal_benchmark = replication targets (top quartile IS NOT)
        benchmarks_raw = kt.get("benchmark_segments") or []
        internal_benchmarks: List[Dict[str, Any]] = []
        for seg in benchmarks_raw:
            seg_dict = _model_to_dict(seg)
            if isinstance(seg_dict, dict) and seg_dict.get("benchmark_type") == "internal_benchmark":
                internal_benchmarks.append({
                    "dimension": seg_dict.get("dimension"),
                    "key": seg_dict.get("key"),
                    "current_value": seg_dict.get("current_value"),
                    "previous_value": seg_dict.get("previous_value"),
                    "delta": seg_dict.get("delta"),
                    "replication_potential": seg_dict.get("replication_potential"),
                })
        if internal_benchmarks:
            summary["benchmark_segments"] = _limit(internal_benchmarks, 3)

        # Phase 11I-D segment matrix: when DA cross-classified each segment across both
        # comparison bases (matrix_ran), surface the CONFIRMED problem segments (adverse on
        # both bases) and the BASIS-SPECIFIC ones (adverse on only one — likely a comparison
        # artifact). SF should prioritise confirmed and NOT build primary options around
        # basis_specific segments. Derived tiers only — SF never reasons across the raw matrix.
        if ctx.get("matrix_ran"):
            _all_rows = (kt.get("where_is") or []) + (kt.get("where_is_not") or [])
            _confirmed = [str(r.get("key")) for r in _all_rows
                          if isinstance(r, dict) and r.get("basis_agreement") == "confirmed" and r.get("key")]
            _basis_specific = [str(r.get("key")) for r in _all_rows
                               if isinstance(r, dict) and r.get("basis_agreement") == "basis_specific" and r.get("key")]
            if _confirmed:
                summary["confirmed_problem_segments"] = _limit(_confirmed, 5)
            if _basis_specific:
                summary["basis_specific_segments"] = _limit(_basis_specific, 5)

    when_started = _first_str(ctx.get("when_started"))
    if when_started:
        summary["when_started"] = when_started

    highlights: List[str] = []
    if scqa:
        highlights.append(scqa)
    for driver in summary.get("where_signals", [])[:3]:
        highlights.append(f"Driver: {driver}")
    for change in summary.get("top_change_points", [])[:3]:
        formatted = _format_driver_entry(change)
        if formatted:
            highlights.append(f"Change point: {formatted}")
    if when_started:
        highlights.append(f"Issue started around {when_started}")
    if highlights:
        summary["key_highlights"] = highlights[:6]

    return summary


def _trim_deep_analysis_context(da_ctx: Any) -> Any:
    ctx = _model_to_dict(da_ctx)
    if not isinstance(ctx, dict):
        return ctx

    trimmed: Dict[str, Any] = {}
    plan = _model_to_dict(ctx.get("plan"))
    if isinstance(plan, dict):
        trimmed["plan"] = {
            "kpi_name": plan.get("kpi_name"),
            "timeframe": plan.get("timeframe"),
            "filters": plan.get("filters"),
            "dimensions": _limit(plan.get("dimensions"), 6),
            "steps": _limit(plan.get("steps"), 6),
        }
    if ctx.get("scqa_summary"):
        trimmed["scqa_summary"] = ctx.get("scqa_summary")
    if ctx.get("timeframe_mapping"):
        trimmed["timeframe_mapping"] = ctx.get("timeframe_mapping")
    if ctx.get("when_started"):
        trimmed["when_started"] = ctx.get("when_started")

    change_points_raw = ctx.get("change_points") or []
    change_points: List[Dict[str, Any]] = []
    for cp in change_points_raw:
        cp_dict = _model_to_dict(cp)
        if isinstance(cp_dict, dict):
            change_points.append({
                "dimension": cp_dict.get("dimension"),
                "key": cp_dict.get("key"),
                "delta": cp_dict.get("delta"),
                "current_value": cp_dict.get("current_value"),
                "previous_value": cp_dict.get("previous_value"),
            })
    if change_points:
        trimmed["change_points"] = _limit(change_points, 6)

    kt = _model_to_dict(ctx.get("kt_is_is_not"))
    if isinstance(kt, dict):
        trimmed_kt: Dict[str, Any] = {}
        for key in ["what_is", "what_is_not", "where_is", "where_is_not", "when_is", "when_is_not", "extent_is"]:
            entries = kt.get(key)
            if entries:
                trimmed_entries: List[Any] = []
                for entry in _limit(entries, 5):
                    entry_dict = _model_to_dict(entry)
                    if isinstance(entry_dict, dict):
                        trimmed_entries.append({k: entry_dict.get(k) for k in entry_dict.keys() if k in {"text", "dimension", "key", "delta", "current", "previous", "bucket", "note"}})
                    else:
                        trimmed_entries.append(entry_dict)
                trimmed_kt[key] = trimmed_entries
        # Include internal_benchmark segments for replication opportunity framing
        benchmarks_raw = kt.get("benchmark_segments") or []
        trimmed_benchmarks = []
        for seg in benchmarks_raw:
            seg_dict = _model_to_dict(seg)
            if isinstance(seg_dict, dict) and seg_dict.get("benchmark_type") == "internal_benchmark":
                trimmed_benchmarks.append({
                    "dimension": seg_dict.get("dimension"),
                    "key": seg_dict.get("key"),
                    "current_value": seg_dict.get("current_value"),
                    "previous_value": seg_dict.get("previous_value"),
                    "delta": seg_dict.get("delta"),
                    "replication_potential": seg_dict.get("replication_potential"),
                })
        if trimmed_benchmarks:
            trimmed_kt["benchmark_segments"] = _limit(trimmed_benchmarks, 3)
        if trimmed_kt:
            trimmed["kt_is_is_not"] = trimmed_kt

    return trimmed if trimmed else ctx
def _safe01(v: Any) -> Optional[float]:
    """Clamp to [0,1] if numeric; return None if not parseable."""
    try:
        if v is None:
            return None
        f = float(v)
        # reject NaN or infinities
        if f != f or f == float('inf') or f == float('-inf'):
            return None
        return max(0.0, min(1.0, f))
    except Exception:
        return None


def _parse_key_assumptions(raw: Any) -> List[SolutionAssumption]:
    """Coerce a per-option key_assumptions list (Phase 15 Stage B) into
    SolutionAssumption instances. Accepts dicts (preferred LLM output) or
    plain strings (defensive fallback), matching StrategySnapshot's legacy
    coercion so both paths tolerate the same degraded input."""
    if not isinstance(raw, list):
        return []

    # The prompt asks for `confidence: high|moderate|low`, but "Medium" appears
    # all over the same prompt for risk and investment levels, so the model
    # reaches for it here too. Coerce the near-misses rather than losing the
    # field — or, before the salvage path below existed, the whole assumption.
    _CONF_SYNONYMS = {
        "medium": "moderate", "med": "moderate", "mid": "moderate",
        "very high": "high", "very low": "low", "none": None, "unknown": None,
    }

    def _normalise(item: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(item)
        item.setdefault("validated_by", "human_confirmation")
        conf = item.get("confidence")
        if isinstance(conf, str):
            key = conf.strip().lower()
            item["confidence"] = _CONF_SYNONYMS.get(key, key) if key in _CONF_SYNONYMS else key
        return item

    out: List[SolutionAssumption] = []
    for item in raw:
        try:
            if isinstance(item, dict):
                out.append(SolutionAssumption(**_normalise(item)))
            elif isinstance(item, str) and item.strip():
                out.append(SolutionAssumption(assumption=item, validated_by="human_confirmation"))
        except Exception as e:
            # Salvage rather than drop. The assumption TEXT is the load-bearing
            # part — it is what VA later grades and what gets pre-registered at
            # approval. Losing it because an optional metadata field came back
            # malformed is a silent, permanent data loss, and this except used
            # to do exactly that with no log line. Retry with the core fields.
            if isinstance(item, dict) and str(item.get("assumption") or "").strip():
                try:
                    out.append(SolutionAssumption(
                        assumption=str(item["assumption"]).strip(),
                        validated_by="human_confirmation",
                    ))
                    logger.info(
                        "[SF] key_assumption metadata rejected (%s) — kept assumption text, dropped metadata: %r",
                        e, {k: v for k, v in item.items() if k != "assumption"},
                    )
                    continue
                except Exception:
                    pass
            logger.info("[SF] key_assumption discarded entirely (unparseable): %s", e)
    return out


def _token_usage_event(ledger: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarise a run's LLM token spend as a single audit event.

    Returns a list so callers can concatenate it unconditionally — an empty
    ledger contributes nothing rather than an event claiming zero cost, which
    would be indistinguishable from a run that genuinely made no LLM calls.

    Per-call rows are kept alongside the totals because the interesting question
    is usually not "what did this cost" but "which stage grew". Output tokens are
    broken out separately since they dominate spend and are what a truncating
    synthesis burns before returning a stub worth nothing.
    """
    if not ledger:
        return []
    _in = sum(r.get("input_tokens") or 0 for r in ledger)
    _out = sum(r.get("output_tokens") or 0 for r in ledger)
    return [{
        "event": "token_usage",
        "calls": len(ledger),
        "input_tokens": _in,
        "output_tokens": _out,
        "total_tokens": _in + _out,
        "by_call": ledger,
    }]


def _parse_impact_estimate(raw: Any) -> Optional[ImpactEstimate]:
    """Coerce the impact_estimate dict into the typed model. Field shape is
    unchanged from the existing prompt JSON — this only adds validation."""
    if not isinstance(raw, dict):
        return None
    try:
        rr = raw.get("recovery_range")
        recovery_range = RecoveryRange(**rr) if isinstance(rr, dict) else None
        # Only accept the two known values. An unrecognised string becomes None
        # ("unstated") rather than being passed through, because a scope nobody
        # can interpret is more dangerous than an absent one: downstream treats
        # None as unverified, but would treat a junk value as a real claim.
        _scope = raw.get("scope")
        if _scope not in ("enterprise", "segment"):
            _scope = None
        return ImpactEstimate(
            metric=raw.get("metric"),
            unit=raw.get("unit"),
            recovery_range=recovery_range,
            basis=raw.get("basis"),
            scope=_scope,
            scope_label=raw.get("scope_label"),
        )
    except Exception:
        return None


def _parse_decision_ask(raw: Any) -> Optional[DecisionAsk]:
    if not isinstance(raw, dict):
        return None
    try:
        return DecisionAsk(**raw)
    except Exception as e:
        logger.warning(f"[SF] decision_ask failed validation, dropping: {e}")
        return None


def _lookup_kpi_scoped(kpi_ref: Optional[str], client_id: Optional[str], logger_: logging.Logger) -> Optional[Any]:
    """Resolve a KPI by id OR display name with strict tenant isolation.

    Phase 15 Stage D needs a real kpi_id (not a display name) to query
    kpi_relationships/assumptions. Reuses the exact tenant-safe pattern from
    A9_Deep_Analysis_Agent._lookup_kpi_scoped (fix commit 5925de7,
    2026-07-13): multiple tenants share KPI ids under the composite PK
    (client_id, id) — e.g. gross_margin_pct exists for lubricants, apex_
    lubricants, and hess. A same-id record from another tenant is NEVER an
    acceptable fallback. Returns None on a scoped miss rather than silently
    resolving cross-tenant.
    """
    if not kpi_ref:
        return None
    try:
        from src.registry.factory import RegistryFactory
        provider = RegistryFactory().get_provider("kpi")
        if not provider:
            return None
        ref = kpi_ref.strip()
        ref_lower = ref.lower()
        candidates = [
            k for k in provider.get_all()
            if getattr(k, "id", None) == ref
            or (getattr(k, "name", "") or "").lower().strip() == ref_lower
        ]
        if client_id:
            scoped = [k for k in candidates if getattr(k, "client_id", None) == client_id]
            if scoped:
                return scoped[0]
            if candidates:
                logger_.error(
                    f"[SF] KPI '{ref}' not found for client '{client_id}' — "
                    f"{len(candidates)} same-id record(s) exist for other tenants; "
                    f"refusing cross-tenant fallback"
                )
            return None
        return candidates[0] if candidates else None
    except Exception as e:
        logger_.debug(f"[SF] _lookup_kpi_scoped('{kpi_ref}', client_id={client_id}) failed: {e}")
        return None


_PROVENANCE_CAVEAT = {
    "template": "UNCONFIRMED industry prior — do not assert as fact; caveat explicitly or ignore",
    "confirmed": "confirmed by the client — usable with attribution",
    "hitl_proposed": "extracted from usage, not yet confirmed — treat cautiously",
    "va_validated": "outcome-tested — describe as 'consistent with' evidence, NEVER 'proved'",
}


def _build_causal_context_section(relationships: List[Any], constraints: List[Any]) -> str:
    """Format the causal chain + active constraints for the synthesis prompt,
    with provenance-aware caveating baked into the text itself (Phase 15
    Stage D). Returns "" when there's nothing to inject — an empty graph
    must never fabricate content, per theory_layer_design.md design
    principle 3 (no invented defaults)."""
    if not relationships and not constraints:
        return ""

    lines: List[str] = []
    if relationships:
        lines.append("## CAUSAL CONTEXT (known relationships for this KPI)")
        lines.append(
            "Each relationship below is provenance-tagged. Respect the caveat for each one — "
            "an unconfirmed prior is not a fact, and a validated relationship is evidence, not proof."
        )
        for r in relationships:
            caveat = _PROVENANCE_CAVEAT.get(getattr(r, "provenance", "template"), "")
            parts = [f"{r.kpi_id} <-> {r.related_kpi_id} ({r.relationship_type}, {r.conflict_direction})"]
            if getattr(r, "mechanism", None):
                parts.append(f"mechanism: {r.mechanism}")
            if getattr(r, "lag_periods", None) is not None:
                parts.append(f"lag: ~{r.lag_periods} months")
            if getattr(r, "causal_rung", None):
                parts.append(f"rung: {r.causal_rung}")
            parts.append(f"provenance: {r.provenance} ({caveat})")
            if getattr(r, "confidence", None):
                parts.append(f"confidence: {r.confidence}")
            lines.append("- " + " | ".join(parts))
        lines.append("")

    if constraints:
        lines.append("## KNOWN CONSTRAINTS — do not propose options that violate these")
        for c in constraints:
            lines.append(f"- {c.text} (source: {c.source})")
        lines.append("")

    return "\n".join(lines) + "\n"


def _parse_immediate_actions(raw: Any) -> List[ImmediateAction]:
    if not isinstance(raw, list):
        return []
    out: List[ImmediateAction] = []
    for item in raw:
        if isinstance(item, dict):
            try:
                out.append(ImmediateAction(**item))
            except Exception:
                continue
    return out


class A9_Solution_Finder_Agent(SolutionFinderProtocol):
    """Solution Finder Agent MVP implementation (skeleton)."""

    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> "A9_Solution_Finder_Agent":
        inst = cls(config or {})
        await inst.connect()
        return inst

    def __init__(self, config: Dict[str, Any]):
        self.name = "A9_Solution_Finder_Agent"
        self.version = "0.1.0"
        self.config = A9_Solution_Finder_Agent_Config(**(config or {}))
        self.logger = logging.getLogger(self.__class__.__name__)
        self.deep_analysis_agent = None
        self.llm_service_agent = None
        self.orchestrator = None

    async def connect(self, orchestrator=None) -> bool:
        try:
            self.orchestrator = orchestrator
            if orchestrator is not None:
                try:
                    self.deep_analysis_agent = await orchestrator.get_agent("A9_Deep_Analysis_Agent")
                except Exception:
                    self.deep_analysis_agent = None
                try:
                    # Get LLM Service Agent (uses cached instance from registry)
                    self.llm_service_agent = await orchestrator.get_agent("A9_LLM_Service_Agent")
                except Exception:
                    self.llm_service_agent = None
            self.logger.info("Solution Finder Agent connected")
            return True
        except Exception as e:
            self.logger.warning(f"Solution Finder Agent connect error: {e}")
            return False

    async def recommend_actions(self, request: SolutionFinderRequest) -> SolutionFinderResponse:
        req_id = request.request_id
        prefs = request.preferences or {}
        try:
            audit_log: List[Dict[str, Any]] = []

            # Per-run token ledger. Usage was already captured by ClaudeService and
            # written to a log line, which in this deployment goes to a detached
            # console window nobody reads — so there was no way to answer "what did
            # that debate cost" from the payload, or to notice a stage quietly
            # doubling in size. Every LLM call SF makes records here, and the totals
            # land in the audit log alongside the result they paid for.
            _token_ledger: List[Dict[str, Any]] = []

            def _record_usage(label: str, resp: Any) -> None:
                """Pull usage off an LLM response. Never raises — cost accounting
                must not be able to break solution generation."""
                try:
                    u = getattr(resp, "usage", None) or {}
                    if not isinstance(u, dict):
                        u = getattr(u, "__dict__", {}) or {}
                    _in = u.get("prompt_tokens")
                    _out = u.get("completion_tokens")
                    if _in is None and _out is None:
                        return
                    _token_ledger.append({
                        "call": label,
                        "model": getattr(resp, "model_used", None),
                        "input_tokens": _in,
                        "output_tokens": _out,
                    })
                except Exception:
                    pass

            # Decide path: LLM persona debate vs heuristic fallback
            # Try LLM when explicitly enabled OR orchestrator is present (safe fallback on failure)
            use_llm = bool(self.config.enable_llm_debate or (self.orchestrator is not None))
            options: List[SolutionOption] = []
            rationale = ""
            
            # Initialize briefing variables
            problem_reframe: Optional[Dict[str, Any]] = None
            unresolved_tensions_list: List[UnresolvedTension] = []
            blind_spots_list: List[str] = []
            next_steps_list: List[str] = []
            cross_review: Optional[Dict[str, Any]] = None
            stage_1_hypotheses_final: Dict[str, Any] = {}
            ma_response: Optional[Dict[str, Any]] = None
            # Phase 15 Stage B
            decision_ask: Optional[DecisionAsk] = None
            immediate_actions_list: List[ImmediateAction] = []

            # FORCE LLM for debugging/MVP
            use_llm = True 
            
            # Fallback: Attempt to acquire LLM service if missing
            if use_llm and not self.orchestrator and not self.llm_service_agent:
                try:
                    from src.agents.new.a9_orchestrator_agent import AgentRegistry
                    self.llm_service_agent = await AgentRegistry.get_agent("A9_LLM_Service_Agent")
                except Exception:
                    pass

            if use_llm:
                try:
                    # Build compact debate prompt content using provided context
                    da_ctx = request.deep_analysis_output or {}
                    da_summary = _extract_deep_analysis_summary(da_ctx)

                    # Detect analysis_mode — HITL-resolved mode in prefs wins over DA plan's
                    # "mixed" auto-detection. prefs carries the principal's explicit choice
                    # ("problem" or "opportunity") after the mixed-mode resolution gate.
                    _da_plan_dict = None
                    try:
                        _raw_plan = da_ctx.get("plan") if isinstance(da_ctx, dict) else None
                        _da_plan_dict = _model_to_dict(_raw_plan)
                    except Exception:
                        pass
                    _prefs_mode = prefs.get("analysis_mode") if isinstance(prefs, dict) else None
                    _plan_mode = _da_plan_dict.get("analysis_mode") if isinstance(_da_plan_dict, dict) else None
                    # Resolved binary modes ("problem"/"opportunity") from the principal override
                    # the DA plan's "mixed" classification. Only fall through to the plan when
                    # prefs carries no resolved mode.
                    analysis_mode: str = (
                        (_prefs_mode if _prefs_mode in ("problem", "opportunity") else None)
                        or _plan_mode
                        or "problem"
                    )
                    is_opportunity = analysis_mode == "opportunity"

                    # Derive a robust problem statement
                    ps_raw = (getattr(request, "problem_statement", None) or "").strip()
                    ps = ps_raw
                    
                    # FORCE KPI from summary if available, even if ps_raw is missing
                    target_kpi = da_summary.get("kpi_name") or "Business Metric"

                    # Hoist change_points — used both inside and outside `if not ps:` block
                    change_points = da_summary.get("top_change_points", [])

                    if not ps:
                        # Construct robust problem statement from DA summary
                        kpi = da_summary.get("kpi_name")
                        
                        ps_parts = []
                        
                        # Part 1: KPI and Delta (Quantitative)
                        if kpi:
                            if change_points:
                                # Use the first (biggest) change point to quantify
                                cp = change_points[0]
                                delta = cp.get("delta")
                                key = cp.get("key")
                                dim = cp.get("dimension")
                                val = cp.get("current_value")
                                
                                # Format nicely if numeric
                                try:
                                    delta_val = float(delta)
                                    delta_str = f"{delta_val:,.2f}"
                                    if is_opportunity:
                                        direction = "is outperforming" if delta_val > 0 else "shows opportunity"
                                    else:
                                        direction = "dropped" if delta_val < 0 else "increased"
                                    delta_abs = f"{abs(delta_val):,.2f}"
                                except Exception:
                                    delta_str = str(delta)
                                    direction = "opportunity detected" if is_opportunity else "changed"
                                    delta_abs = str(delta)

                                try:
                                    val_str = f"{float(val):,.2f}"
                                except Exception:
                                    val_str = str(val)

                                if is_opportunity:
                                    ps_parts.append(f"{kpi} {direction} (Leading segment current level: {val_str}, advantage: {delta_abs}). [ANALYSIS_MODE: OPPORTUNITY]")
                                    if dim and key:
                                        ps_parts.append(f"The leading IS segment is '{key}' within the {dim} dimension — the goal is to replicate its outperformance.")
                                else:
                                    ps_parts.append(f"{kpi} {direction} by {delta_abs} (Current Level: {val_str}). [KPI_DIRECTION: {direction.upper()}]")
                                    if dim and key:
                                        ps_parts.append(f"This deviation is primarily driven by '{key}' within the {dim} segment.")
                            else:
                                ps_parts.append(f"{kpi} is showing significant anomalous behavior deviating from historical trends.")
                        
                        # Part 2: Timeframe
                        tf = da_summary.get("timeframe")
                        if tf:
                             ps_parts.append(f"Analysis period: {tf}.")
                        
                        # Part 3: Signals
                        signals = da_summary.get("where_signals", [])
                        if signals:
                             ps_parts.append(f"Contributing factors identified: {', '.join(signals[:2])}.")

                        if ps_parts:
                            ps = " ".join(ps_parts)
                        else:
                            ps = "Anomaly detected in business metrics requiring strategic intervention."
                            
                        # Prefer SCQA summary if available as it's more narrative context
                        try:
                            scqa = None
                            if hasattr(da_ctx, "scqa_summary"):
                                scqa = getattr(da_ctx, "scqa_summary")
                            elif isinstance(da_ctx, dict):
                                scqa = da_ctx.get("scqa_summary")
                            
                            if scqa:
                                ps = f"{ps} \n\nAdditional Context: {str(scqa)}"
                        except Exception:
                            pass
                    if not ps:
                        # Fallback to KPI name from plan if available
                        try:
                            plan = None
                            if hasattr(da_ctx, "plan"):
                                plan = getattr(da_ctx, "plan", None)
                            elif isinstance(da_ctx, dict):
                                plan = da_ctx.get("plan")
                            kpi_name = None
                            if plan is not None:
                                if isinstance(plan, dict):
                                    kpi_name = plan.get("kpi_name")
                                else:
                                    kpi_name = getattr(plan, "kpi_name", None)
                            if kpi_name:
                                ps = f"KPI: {kpi_name} — generate actionable solution options."
                        except Exception:
                            pass
                    if not ps:
                        ps = "Problem statement not provided"

                    # CRITICAL: Use situation_context.description as the PRIMARY problem statement
                    # It contains the OVERALL KPI direction (e.g., "decreased by 27.2%") which is
                    # more accurate than segment-level change_points that may show mixed directions.
                    try:
                        # First try request-level situation_context, then fall back to deep_analysis_output.situation_context
                        sctx = getattr(request, "situation_context", None)
                        if not sctx and isinstance(da_ctx, dict):
                            sctx = da_ctx.get("situation_context")
                        sctx_desc = sctx.get("description") if isinstance(sctx, dict) else getattr(sctx, "description", None)
                        sctx_kpi = sctx.get("kpi_name") if isinstance(sctx, dict) else getattr(sctx, "kpi_name", None)
                        
                        if isinstance(sctx_desc, str) and sctx_desc.strip():
                            overall_ps = sctx_desc.strip()
                            if is_opportunity:
                                ps = f"[ANALYSIS_MODE: OPPORTUNITY] {overall_ps}"
                                if change_points:
                                    ps += (
                                        f"\n\nOPPORTUNITY FRAMING: The IS segment is the outperforming leader."
                                        " Solutions must ask 'how do we replicate/scale this success to the IS NOT (lagging) segments?'"
                                        " Do NOT frame solutions as fixing a problem."
                                    )
                            else:
                                overall_direction = (
                                    "DECREASED" if "decreased" in overall_ps.lower() or "dropped" in overall_ps.lower()
                                    else "INCREASED" if "increased" in overall_ps.lower()
                                    else "CHANGED"
                                )
                                ps = f"[OVERALL KPI DIRECTION: {overall_direction}] {overall_ps}"
                                if change_points:
                                    ps += (
                                        f"\n\nNOTE: While the OVERALL {sctx_kpi or 'KPI'} has {overall_direction.lower()},"
                                        " individual segments show mixed performance. Some segments may have increased while others decreased."
                                        f" The Problem Reframe 'situation' field MUST reflect the OVERALL {overall_direction} direction,"
                                        " not individual segment increases."
                                    )
                        elif sctx_kpi:
                            ps = f"KPI: {sctx_kpi} — generate actionable solution options."
                    except Exception:
                        pass
                    # Resolve Personas (Hybrid Council vs Legacy)
                    consulting_personas: List[ConsultingPersona] = []
                    # Check if Hybrid Council is enabled via config or request preferences
                    using_hybrid_council = getattr(self.config, "enable_hybrid_council", False)
                    
                    req_personas = []
                    req_preset = None
                    try:
                        req_personas = prefs.get("consulting_personas", [])
                        req_preset = prefs.get("council_preset")
                        self.logger.info(f"Preferences - consulting_personas: {req_personas}, council_preset: {req_preset}")
                        if req_personas or req_preset:
                            using_hybrid_council = True
                    except Exception as e:
                        self.logger.warning(f"Error extracting preferences: {e}")

                    if using_hybrid_council:
                        # 1. Request-level override (Personas)
                        if req_personas:
                            self.logger.info(f"Using request-level personas: {req_personas}")
                            for pid in req_personas:
                                p = get_consulting_persona(str(pid))
                                if p: 
                                    consulting_personas.append(p)
                                    self.logger.info(f"  Added persona: {pid} -> {p.name}")
                                else:
                                    self.logger.warning(f"  Persona not found: {pid}")
                        
                        # 2. Request-level override (Preset)
                        elif req_preset:
                            preset = get_council_preset(str(req_preset))
                            if preset:
                                for pid in preset.personas:
                                    p = get_consulting_persona(pid)
                                    if p: consulting_personas.append(p)
                        
                        # 3. Config-level (Personas)
                        elif getattr(self.config, "consulting_personas", None):
                            for pid in self.config.consulting_personas:
                                p = get_consulting_persona(pid)
                                if p: consulting_personas.append(p)

                        # 4. Config-level (Preset)
                        elif getattr(self.config, "council_preset", None):
                            preset = get_council_preset(self.config.council_preset)
                            if preset:
                                for pid in preset.personas:
                                    p = get_consulting_persona(pid)
                                    if p: consulting_personas.append(p)
                        
                        # 5. Principal Decision Style (NEW - Principal-Driven Approach)
                        else:
                            decision_style = None
                            role = None
                            try:
                                pc = getattr(request, "principal_context", None)
                                if pc:
                                    if isinstance(pc, dict):
                                        decision_style = pc.get("decision_style")
                                        role = pc.get("role")
                                    else:
                                        decision_style = getattr(pc, "decision_style", None)
                                        role = getattr(pc, "role", None)
                            except Exception:
                                pass
                            
                            # Priority: decision_style > role affinity
                            if decision_style and decision_style.lower() in DECISION_STYLE_TO_PERSONA:
                                consulting_personas = get_personas_for_decision_style(decision_style)
                                self.logger.info(f"Using decision_style '{decision_style}' for persona selection")
                            elif role:
                                consulting_personas = get_personas_for_principal(role)
                                self.logger.info(f"Using role '{role}' for persona selection (no decision_style)")
                        
                        # 6. Absolute Fallback (MBB)
                        if not consulting_personas:
                            preset = get_council_preset("mbb_council")
                            if preset:
                                for pid in preset.personas:
                                    p = get_consulting_persona(pid)
                                    if p: consulting_personas.append(p)
                            self.logger.info("Using default MBB council (no decision_style or role)")

                    # Initialize persona_ids to ensure scope availability
                    persona_ids = []
                    
                    # Build Context Strings
                    self.logger.info(f"Final consulting_personas count: {len(consulting_personas)}")
                    self.logger.info(f"Final consulting_personas IDs: {[p.id for p in consulting_personas]}")
                    if consulting_personas:
                        persona_names = ", ".join([p.name for p in consulting_personas])
                        persona_ids = [p.id for p in consulting_personas]
                        persona_details = "\n\n".join([p.to_prompt_context() for p in consulting_personas])
                        
                        # Build dynamic framework descriptions based on actual personas
                        framework_lines = []
                        for p in consulting_personas:
                            framework_lines.append(f"- {p.name}: {p.methodology_summary if hasattr(p, 'methodology_summary') and p.methodology_summary else 'Apply signature frameworks and expertise'}")
                        frameworks_text = "\n".join(framework_lines)
                        
                        role_section = (
                            "## ROLE\n"
                            f"You are the Chair of a Strategy Council composed of: {persona_names}.\n"
                            "Your goal is to synthesize their distinct methodologies into a cohesive executive briefing.\n"
                        )
                        council_section = (
                            "## CONSULTING COUNCIL PROFILES\n"
                            f"{persona_details}\n"
                        )
                        task_instruction = (
                            "Stage 1 persona hypotheses are already captured in INPUT DATA as 'stage_1_persona_hypotheses'.\n"
                            "Each persona has independently proposed one intervention. Your tasks:\n\n"
                            "**STAGE 2 - CROSS-REVIEW:**\n"
                            "Each firm reviews the other firms' Stage 1 proposed_options and provides:\n"
                            "- Critiques: What blind spots or execution risks does the other firm's approach miss?\n"
                            "- Endorsements: What aspects of the other firm's approach are strong?\n"
                            "Be specific — reference the actual option titles from stage_1_persona_hypotheses.\n\n"
                            "**STAGE 3 - SYNTHESIS:**\n"
                            "Use each persona's 'proposed_option' from stage_1_persona_hypotheses as the basis for your 3 output options.\n"
                            "Expand each proposal with: full perspectives (arguments_for, arguments_against, key_questions),\n"
                            "prerequisites, implementation_triggers, and complete impact_estimate with a calibrated recovery_range.\n"
                            "Firm-specific frameworks for reference:\n"
                            f"{frameworks_text}\n"
                        )
                        output_instruction = (
                            "## OUTPUT FORMAT (STRICT JSON)\n"
                            "The 'cross_review' field MUST contain each firm's Stage 2 critiques and endorsements.\n"
                            "Each critique must have 'target' (option id or firm name) and 'concern' (specific issue).\n"
                            "Each endorsement must have 'target' and 'reason' (why they support it).\n"
                            "Do NOT include a 'stage_1_hypotheses' field — those are already captured separately.\n"
                        )
                    else:
                        # Legacy / Generic Persona Path
                        personas_override: List[str] = []
                        try:
                            cand = prefs.get("personas") if isinstance(prefs, dict) else None
                            if isinstance(cand, list):
                                personas_override = [str(p) for p in cand if p]
                        except Exception:
                            personas_override = []
                        personas_list = personas_override or (self.config.expert_personas or [])
                        persona_names = ", ".join(personas_list)
                        persona_ids = personas_list  # Ensure persona_ids is defined for the prompt construction
                        
                        role_section = (
                            "## ROLE\n"
                            "You are a decision analyst preparing a structured briefing for executive stakeholders.\n"
                        )
                        council_section = ""
                        task_instruction = (
                            "Given the problem context, data analysis, and PRINCIPAL INPUT (priorities/constraints), generate a DECISION BRIEFING with:\n"
                            "1. Problem reframing (ensure shared understanding)\n"
                            "2. 2-3 concrete solution options with evidence-based analysis\n"
                            "3. For EACH option: strongest arguments FOR and AGAINST from multiple perspectives\n"
                            "4. Unresolved tensions requiring human judgment\n"
                            "5. Implementation considerations and decision triggers\n"
                        )
                        output_instruction = "## OUTPUT FORMAT (STRICT JSON)\n"

                    if is_opportunity:
                        _accuracy_req = (
                            "- CRITICAL ACCURACY REQUIREMENT (OPPORTUNITY MODE):\n"
                            "  * ANALYSIS_MODE is OPPORTUNITY — do NOT frame solutions as 'fixing a problem'.\n"
                            "  * The IS segment is the outperforming leader; IS NOT segments are replication targets.\n"
                            "  * The Problem Reframe 'situation' MUST describe the outperformance opportunity, not a decline.\n"
                            "  * The 'complication' should describe the replication gap: why IS NOT segments lag behind IS.\n"
                            "  * The 'question' should ask: How do we scale the IS segment's success to IS NOT segments?\n"
                            "  * All 3 solution options must address replication/scaling of the outperforming practices.\n\n"
                        )
                    else:
                        _accuracy_req = (
                            "- CRITICAL ACCURACY REQUIREMENT:\n"
                            "  * The 'problem_statement' field contains the OVERALL KPI direction (e.g., 'decreased by 27.2%').\n"
                            "  * The Problem Reframe 'situation' field MUST reflect this OVERALL direction.\n"
                            "  * The Deep Analysis shows MIXED performance: some segments improved, others degraded.\n"
                            "  * The 'situation' should state the NET/OVERALL effect (from problem_statement).\n"
                            "  * The 'complication' should acknowledge the mixed segment performance.\n"
                            "  * Solution options should address BOTH: fixing degraded segments AND leveraging successful ones.\n\n"
                        )

                    debate_spec = (
                        f"{role_section}\n"
                        f"{council_section}\n"
                        "## TASK\n"
                        f"{task_instruction}\n"
                        "## CONSTRAINTS\n"
                        "- Do NOT synthesize a single recommendation or consensus\n"
                        "- Do NOT simulate how real stakeholders would vote\n"
                        "- DO surface trade-offs, assumptions, and blind spots\n"
                        "- Each perspective must cite its reasoning basis\n"
                        "- MUST respect Principal Input constraints/vetoes if provided\n"
                        f"- MUST populate cross_review with SPECIFIC critiques and endorsements from each consulting firm ({persona_names}). Each firm should critique at least one option and endorse at least one option with concrete reasoning.\n"
                        "- CRITICAL: The Deep Analysis is COMPLETE. Do NOT suggest 'more data gathering' or 'implementing analytics' as a primary solution. Focus on OPERATIONAL INTERVENTIONS to address the identified drivers.\n"
                        f"- CONTEXT: The analysis focuses on '{target_kpi}'. Ensure the Problem Reframe explicitly mentions this KPI.\n"
                        "- QUANTIFIED IMPACT REQUIREMENT: For each option, populate 'impact_estimate' using the actual numbers from the SITUATION METRICS section:\n"
                        "  * 'metric' = the KPI name (from SITUATION METRICS kpi_name field)\n"
                        "  * 'unit' = the KPI unit (from SITUATION METRICS unit field, e.g. '%' or '$')\n"
                        "  * 'recovery_range' = {\"low\": <number>, \"high\": <number>} expressed in the KPI's own units — NOT as a generic percentage of improvement. If unit is '%', express as percentage points (e.g. 1.2 to 2.8). If unit is '$', express as dollar amounts (e.g. 2400000 to 4800000).\n"
                        # SCOPE ELICITATION IS DEFERRED — see ImpactEstimate.scope.
                        # Asking for scope/scope_label here is correct in principle but
                        # pushes the synthesis JSON past its output budget: the response
                        # already runs ~25,600 characters (~20k tokens of dense JSON) and
                        # truncates mid-object, parsing to {"raw_response": ...} and
                        # silently yielding the heuristic stub. Reproduced 3/3 with the
                        # instruction present, 0/1 without. Raising max_tokens to 28000
                        # did not help — claude-sonnet-5 returned status="error".
                        #
                        # The model field, parser, and VA guard still ship: with scope
                        # absent the guard treats every bound as UNVERIFIED, which is the
                        # safe reading and the property that actually protects VA. Re-add
                        # this line once the synthesis output budget is resolved, and
                        # re-verify with the live harness rather than the unit suite —
                        # nothing in tests/unit exercises a real synthesis call.
                        "  * 'basis' = one sentence grounding the estimate in the actual change_points magnitude and the option's mechanism (e.g. 'Supplier consolidation delivering 3-5% unit cost reduction on the $X COGS base identified in the where_is analysis'). If the figure sizes a single segment rather than the enterprise KPI, say so explicitly.\n"
                        "  * Calibrate the range against the current_value and comparison_value from SITUATION METRICS — your estimate should be directionally proportional to the observed variance.\n"
                        "- NUMERIC DIFFERENTIATION REQUIREMENT: Each option's expected_impact, cost, risk, AND recovery_range MUST differ from the others. "
                        "Map each option's cost_signal from stage_1_persona_hypotheses.proposed_option: Low→0.25, Medium→0.50, High→0.80. "
                        "Map risk_signal similarly. recovery_range MUST be non-zero — anchor from Stage 1 impact_estimates in stage_1_persona_hypotheses. "
                        "Do NOT output 0.0 for any numeric field.\n"
                        "- SCOPING REQUIREMENT: Use 'where_is_not' and 'what_is_not' from deep_analysis_summary to explicitly scope each option — name which segments already perform well (no intervention needed) and which are the target. This prevents boiling-the-ocean recommendations.\n"
                        "- CROSS-BASIS SCOPING (when present): If deep_analysis_summary has 'confirmed_problem_segments', prioritise those — they are adverse on BOTH comparison bases (vs prior period AND vs plan), so they are the genuine, most-defensible problem. If it has 'basis_specific_segments', treat them as probable comparison-timing artifacts (adverse on only one basis, e.g. down vs last year but on-plan) — do NOT build primary options around them.\n"
                        "- INTERNAL BENCHMARK FEASIBILITY: If benchmark_segments (internal_benchmark type) are present in deep_analysis_summary or kt_is_is_not, at least one option MUST address replication: how the outperforming segment's practices can be scaled to underperforming areas. Name the benchmark segment explicitly and quantify the replication upside using its delta.\n"
                        "- OPTION DIVERSITY REQUIREMENT: Generate EXACTLY 3 options with meaningfully different primary mechanisms — do NOT collapse them into a single 'Strategic Realignment'. Example structure: (1) an immediate operational intervention (0-90 days, lower cost, higher reversibility), (2) a structural fix targeting the root cause dimension (3-12 months), (3) a strategic portfolio or pricing play (12+ months, higher investment). Each option must be independently actionable and have a distinct title reflecting the specific lever.\n"
                        "- CONSISTENCY CHECK (mandatory before writing opt_2/opt_3): Before recommending mix shift toward a product category or customer segment, verify from the where_is data that the TARGET category has BETTER margin performance than the PROBLEM category. If the target segment is ALSO underperforming in the data, you MUST explicitly acknowledge this in the option description AND provide a resolution path (e.g., 'Step 1 is to restore that segment's margins via [mechanism], then accelerate shift'). Never recommend moving volume toward a segment with worse margins than the one being abandoned without resolving the contradiction.\n"
                        "- ASSUMPTION HONESTY REQUIREMENT: populate ALL of `grounded`, `confidence`, `provenance` on every key_assumption. These carry downstream to Value Assurance, which grades whether each assumption held, so a mislabelled one corrupts the record permanently.\n"
                        "  * `grounded`: true ONLY when the assumption is directly supported by a specific fact present in the INPUT DATA — a named change_point, benchmark segment, market signal, or causal relationship. If you are inferring it from domain knowledge or general reasoning, it is FALSE. An ungrounded assumption is NOT a flaw; it is the normal case, and most assumptions in a typical option are ungrounded. Marking an inferred assumption as grounded is far worse than admitting it was inferred.\n"
                        "  * `provenance`: name the OBSERVATION that would confirm or falsify this — something checkable later, e.g. 'base oil cost exceeds $85 for two consecutive periods'. When grounded=true, cite the specific input fact instead. Never write 'proved' or 'proven'; the strongest permitted phrasing is 'consistent with'.\n"
                        "  * `confidence`: high|moderate|low — confidence that the assumption HOLDS, which is independent of `grounded`. A grounded assumption can be low confidence (thin or noisy data); an inferred one can be high confidence (strong domain prior).\n"
                        "  * Do NOT list fewer assumptions in order to appear more certain. Naming an assumption is the honest act; omitting one is the failure.\n"
                        f"{_accuracy_req}"
                        f"{output_instruction}"
                        "IMPORTANT — fill in this JSON exactly as shown. Do NOT include a stage_1_hypotheses field.\n"
                        "{\n"
                        "  \"problem_reframe\": {\n"
                        "    \"situation\": \"...\",\n"
                        "    \"complication\": \"...\",\n"
                        "    \"question\": \"...\",\n"
                        "    \"key_assumptions\": [\"...\"]\n"
                        "  },\n"
                        "  \"options\": [\n"
                        "    {\n"
                        "      \"id\": \"opt_1\",\n"
                        "      \"title\": \"...\",\n"
                        "      \"description\": \"...\",\n"
                        "      \"expected_impact\": 0.75,\n"
                        "      \"cost\": 0.40,\n"
                        "      \"risk\": 0.35,\n"
                        "      \"impact_estimate\": {\n"
                        "        \"metric\": \"<KPI name from SITUATION METRICS>\",\n"
                        "        \"unit\": \"<unit from SITUATION METRICS, e.g. % or $>\",\n"
                        "        \"recovery_range\": {\"low\": <S1_low_estimate>, \"high\": <S1_high_estimate>},\n"
                        "        \"basis\": \"<one sentence: mechanism + data grounding>\"\n"
                        "      },\n"
                        "      \"rationale\": \"...\",\n"
                        "      \"time_to_value\": \"...\",\n"
                        "      \"reversibility\": \"high|medium|low\",\n"
                        "      \"perspectives\": [\n"
                        "        {\n"
                        "          \"lens\": \"Financial\",\n"
                        "          \"arguments_for\": [\"<complete sentence describing a specific benefit, e.g. 'Directly targets the highest-impact cost driver identified in the analysis'>\"],\n"
                        "          \"arguments_against\": [\"<complete sentence describing a specific risk or limitation, e.g. 'Requires competitor pricing data not currently available'>\"],\n"
                        "          \"key_questions\": [\"<actionable question for the decision maker>\"]\n"
                        "        }\n"
                        "      ],\n"
                        "      \"implementation_triggers\": [\"...\"],\n"
                        "      \"prerequisites\": [\"...\"],\n"
                        "      \"key_assumptions\": [\n"
                        "        {\"assumption\": \"<what this option bets on>\", \"validated_by\": \"sa_assessment|ma_query|human_confirmation\", \"grounded\": false, \"confidence\": \"high|moderate|low\", \"provenance\": \"<what observation would confirm or falsify this>\"}\n"
                        "      ],\n"
                        "      \"flagged_side_effects\": []\n"
                        "    },\n"
                        "    {\n"
                        "      \"id\": \"opt_2\",\n"
                        "      \"title\": \"...\",\n"
                        "      \"description\": \"...\",\n"
                        "      \"expected_impact\": 0.55,\n"
                        "      \"cost\": 0.60,\n"
                        "      \"risk\": 0.55,\n"
                        "      \"impact_estimate\": {\n"
                        "        \"metric\": \"...\",\n"
                        "        \"unit\": \"...\",\n"
                        "        \"recovery_range\": {\"low\": <S1_low_estimate>, \"high\": <S1_high_estimate>},\n"
                        "        \"basis\": \"...\"\n"
                        "      },\n"
                        "      \"rationale\": \"...\",\n"
                        "      \"time_to_value\": \"...\",\n"
                        "      \"reversibility\": \"high|medium|low\",\n"
                        "      \"perspectives\": [\n"
                        "        {\n"
                        "          \"lens\": \"Financial\",\n"
                        "          \"arguments_for\": [\"<complete sentence describing a specific benefit, e.g. 'Directly targets the highest-impact cost driver identified in the analysis'>\"],\n"
                        "          \"arguments_against\": [\"<complete sentence describing a specific risk or limitation, e.g. 'Requires competitor pricing data not currently available'>\"],\n"
                        "          \"key_questions\": [\"<actionable question for the decision maker>\"]\n"
                        "        }\n"
                        "      ],\n"
                        "      \"implementation_triggers\": [\"...\"],\n"
                        "      \"prerequisites\": [\"...\"],\n"
                        "      \"key_assumptions\": [\n"
                        "        {\"assumption\": \"<what this option bets on>\", \"validated_by\": \"sa_assessment|ma_query|human_confirmation\", \"grounded\": false, \"confidence\": \"high|moderate|low\", \"provenance\": \"<what observation would confirm or falsify this>\"}\n"
                        "      ],\n"
                        "      \"flagged_side_effects\": []\n"
                        "    },\n"
                        "    {\n"
                        "      \"id\": \"opt_3\",\n"
                        "      \"title\": \"...\",\n"
                        "      \"description\": \"...\",\n"
                        "      \"expected_impact\": 0.38,\n"
                        "      \"cost\": 0.80,\n"
                        "      \"risk\": 0.70,\n"
                        "      \"impact_estimate\": {\n"
                        "        \"metric\": \"...\",\n"
                        "        \"unit\": \"...\",\n"
                        "        \"recovery_range\": {\"low\": <S1_low_estimate>, \"high\": <S1_high_estimate>},\n"
                        "        \"basis\": \"...\"\n"
                        "      },\n"
                        "      \"rationale\": \"...\",\n"
                        "      \"time_to_value\": \"...\",\n"
                        "      \"reversibility\": \"high|medium|low\",\n"
                        "      \"perspectives\": [\n"
                        "        {\n"
                        "          \"lens\": \"Financial\",\n"
                        "          \"arguments_for\": [\"<complete sentence describing a specific benefit, e.g. 'Directly targets the highest-impact cost driver identified in the analysis'>\"],\n"
                        "          \"arguments_against\": [\"<complete sentence describing a specific risk or limitation, e.g. 'Requires competitor pricing data not currently available'>\"],\n"
                        "          \"key_questions\": [\"<actionable question for the decision maker>\"]\n"
                        "        }\n"
                        "      ],\n"
                        "      \"implementation_triggers\": [\"...\"],\n"
                        "      \"prerequisites\": [\"...\"],\n"
                        "      \"key_assumptions\": [\n"
                        "        {\"assumption\": \"<what this option bets on>\", \"validated_by\": \"sa_assessment|ma_query|human_confirmation\", \"grounded\": false, \"confidence\": \"high|moderate|low\", \"provenance\": \"<what observation would confirm or falsify this>\"}\n"
                        "      ],\n"
                        "      \"flagged_side_effects\": []\n"
                        "    }\n"
                        "  ],\n"
                        "  \"recommendation\": {\"id\": \"opt_1\", \"title\": \"...\"},\n"
                        "  \"recommendation_rationale\": \"<A 2-3 sentence paragraph explaining WHY this specific option is the right first move — ground it in specific named entities, values, and mechanisms from the analysis data (e.g., 'Rock On Bikes' specific margin delta, the cost driver identified in where_is). Do NOT use generic language like 'Options generated via Decision Briefing analysis' or 'Based on our analysis.' Cite the specific driver and the specific option mechanism.>\",\n"
                        "  \"unresolved_tensions\": [\n"
                        "    {\n"
                        "      \"tension\": \"...\",\n"
                        "      \"options_affected\": [\"opt_1\", \"opt_2\"],\n"
                        "      \"requires\": \"<Specific operational action to resolve this tension — NOT meta-labels like 'human judgment' or 'more data'. Format: 'Role title does what specific task by when'. Use ROLE TITLES only — do NOT use personal names (e.g., use 'CFO' or 'VP Sales' not a person's name). E.g.: 'Finance team to complete SKU-level cost-to-serve analysis before National Auto Parts Chain A negotiation begins (target: Week 2)'>\"\n"
                        "    }\n"
                        "  ],\n"
                        "  \"blind_spots\": [\"...\"],\n"
                        "  \"next_steps\": [\n"
                        "    // REQUIREMENT: Minimum 4 items. Each item MUST follow this format:\n"
                        "    // \"<Action verb> + <specific responsible role or team> + <specific deliverable> + <by when or gate condition>\"\n"
                        "    // GOOD: \"CFO to commission SKU-level cost-to-serve analysis from Finance team before negotiating with [customer] (by end of Week 1)\"\n"
                        "    // BAD: \"Review options and decide\" — too vague, no owner, no timeline\n"
                        "    // Each step must be independently actionable with a named owner.\n"
                        "    \"<action verb> + <role> + <specific deliverable> + <by when>\",\n"
                        "    \"...\"\n"
                        "  ],\n"
                        "  \"decision_ask\": {\n"
                        "    \"decision_text\": \"<the ONE decision the executive is being asked to make, <=25 words, no hedge words like 'consider' or 'might'>\",\n"
                        "    \"decision_owner\": \"<role title, e.g. 'CFO'>\",\n"
                        "    \"deadline\": \"<e.g. 'by end of Week 1'>\",\n"
                        "    \"approval_type\": \"<e.g. 'budget approval', 'go/no-go'>\"\n"
                        "  },\n"
                        "  \"immediate_actions\": [\n"
                        "    {\"action_text\": \"<specific first task>\", \"owner\": \"<role title>\", \"due_by_days\": <integer>, \"why_it_matters\": \"<one sentence>\"}\n"
                        "  ],\n"
                        "  \"cross_review\": {\n"
                        + "".join([
                            f'    "{pid}": {{\n'
                            f'      "critiques": [{{"target": "opt_1", "concern": "Specific critique from {pid} lens"}}],\n'
                            f'      "endorsements": [{{"target": "opt_2", "reason": "Why {pid} supports this option"}}]\n'
                            f'    }}{chr(44) if i < len(persona_ids) - 1 else ""}\n'
                            for i, pid in enumerate(persona_ids)
                        ])
                        + "  }\n"
                        "}\n"
                        f"\nCRITICAL: The options array MUST have EXACTLY 3 items (opt_1, opt_2, opt_3). The cross_review MUST use EXACTLY these persona IDs as keys: {persona_ids}. Do NOT include a stage_1_hypotheses field.\n"
                    )
                    self.logger.info(f"Cross-review will use persona_ids: {persona_ids}")
                    # Optional user-supplied context to guide the debate
                    try:
                        user_ctx = prefs.get("user_context") if isinstance(prefs, dict) else None
                    except Exception:
                        user_ctx = None

                    # Extract Principal Input (from request model or preferences dict fallback)
                    principal_input = getattr(request, "principal_input", None)
                    if not principal_input and isinstance(prefs, dict):
                        pi_dict = prefs.get("principal_input")
                        if isinstance(pi_dict, dict):
                            # Pass as raw dict to content
                            principal_input = pi_dict

                    # Extract Problem Refinement results (from MBB-style chat)
                    refinement_result = None
                    if isinstance(prefs, dict):
                        refinement_result = prefs.get("refinement_result")
                        self.logger.info(f"[SF] Refinement result received: {refinement_result is not None}")
                        if refinement_result:
                            self.logger.info(f"[SF] Refinement keys: {list(refinement_result.keys()) if isinstance(refinement_result, dict) else 'not a dict'}")

                    trimmed_da = _trim_deep_analysis_context(da_ctx)
                    # da_summary already extracted above

                    # Lightweight dataset recap for the personas to ground recommendations
                    dataset_recap_lines: List[str] = []
                    kpi_lbl = da_summary.get("kpi_name") or (sctx_kpi if 'sctx_kpi' in locals() else None)
                    if kpi_lbl:
                        dataset_recap_lines.append(f"KPI analyzed: {kpi_lbl}")
                    if da_summary.get("timeframe"):
                        comp_tf = da_summary.get("comparison_timeframe")
                        tf_line = f"Timeframe: {da_summary['timeframe']}"
                        if comp_tf:
                            tf_line += f" vs {comp_tf}"
                        dataset_recap_lines.append(tf_line)
                    if da_summary.get("key_highlights"):
                        for highlight in da_summary["key_highlights"][:3]:
                            dataset_recap_lines.append(f"Evidence: {highlight}")
                    if da_summary.get("where_signals"):
                        dataset_recap_lines.append("CONFIRMED ROOT CAUSES: " + "; ".join(da_summary["where_signals"][:3]))
                    if da_summary.get("top_change_points"):
                        formatted_cps = [
                            _format_driver_entry(cp) for cp in da_summary["top_change_points"][:3]
                            if _format_driver_entry(cp)
                        ]
                        if formatted_cps:
                            dataset_recap_lines.append("Change points: " + "; ".join(formatted_cps))
                    
                    # Add market conflict warning when external signals contradict DA conclusion
                    _s2_conflict = da_ctx.get("market_conflict") if isinstance(da_ctx, dict) else None
                    if _s2_conflict and _s2_conflict.get("detected") and _s2_conflict.get("summary"):
                        dataset_recap_lines.append(f"MARKET SIGNAL CONFLICT: {_s2_conflict['summary']}")

                    # Add Problem Refinement context from MBB-style chat
                    if refinement_result:
                        if refinement_result.get("external_context"):
                            ctx_items = refinement_result["external_context"][:3]
                            if ctx_items:
                                # Phase 15 Stage C label fix: this is the principal's own
                                # statements captured during refinement chat, not their profile.
                                dataset_recap_lines.append("PRINCIPAL-PROVIDED CONTEXT (from refinement): " + "; ".join(ctx_items))
                        if refinement_result.get("constraints"):
                            constraint_items = refinement_result["constraints"][:3]
                            if constraint_items:
                                dataset_recap_lines.append("CONSTRAINTS: " + "; ".join(constraint_items))
                        if refinement_result.get("exclusions"):
                            excl_items = [e.get("value", str(e)) if isinstance(e, dict) else str(e) for e in refinement_result["exclusions"][:3]]
                            if excl_items:
                                dataset_recap_lines.append("EXCLUSIONS: " + "; ".join(excl_items))
                        if refinement_result.get("validated_hypotheses"):
                            validated = refinement_result["validated_hypotheses"][:3]
                            if validated:
                                dataset_recap_lines.append("VALIDATED BY PRINCIPAL: " + "; ".join(validated))
                        if refinement_result.get("invalidated_hypotheses"):
                            invalidated = refinement_result["invalidated_hypotheses"][:3]
                            if invalidated:
                                dataset_recap_lines.append("RULED OUT BY PRINCIPAL: " + "; ".join(invalidated))
                        if refinement_result.get("refined_problem_statement"):
                            dataset_recap_lines.append(f"REFINED PROBLEM: {refinement_result['refined_problem_statement']}")
                    
                    dataset_recap = dataset_recap_lines if dataset_recap_lines else None

                    # Fallback Business Context — load from Supabase registry via client_id
                    bc = getattr(request, "business_context", None)
                    if not bc:
                        try:
                            from src.registry.factory import RegistryFactory as _RF
                            from src.registry.business_context.business_context_provider import SupabaseBusinessContextProvider

                            # Resolve client_id: prefer da_summary or request, fall back to KPI name scan
                            _client_id = (
                                (da_summary.get("client_id") if da_summary else None)
                                or getattr(request, "client_id", None)
                            )
                            if not _client_id:
                                self.logger.warning("[SF] client_id not resolved — skipping business context load to prevent cross-tenant contamination")

                            if _client_id:
                                _bc_provider = SupabaseBusinessContextProvider()
                                _bc_model = await _bc_provider.get_context(_client_id)
                                if _bc_model:
                                    bc = _bc_model.model_dump(exclude_none=True)
                                    self.logger.info(f"[SF] Business context loaded from Supabase: client_id={_client_id}")
                                else:
                                    self.logger.warning(f"[SF] No business context in Supabase for client_id={_client_id}")
                        except Exception as e:
                            self.logger.warning(f"Failed to load business context from Supabase: {e}")

                        # Phase 15 Stage C / strict tenancy (llm_prompt_redesign_da_sf.md §3.2):
                        # a missing business-context record must produce an explicit
                        # "no business context available" line, never invented generic
                        # defaults presented as if they were this client's real context.
                        if not bc:
                            bc = {
                                "note": "No business context available for this client — "
                                        "do not assume generic industry norms; ground recommendations "
                                        "only in the KPI data and analysis signals provided."
                            }

                        try:
                            request.business_context = bc
                        except:
                            pass

                    # Use trimmed DA context to preserve output tokens for generating 3 distinct options.
                    # da_summary + dataset_recap already carry the key quantitative signals;
                    # full context risks exhausting the LLM's output budget on summarisation.
                    full_da_context = _model_to_dict(trimmed_da)

                    # Extract decision maker context for personalized recommendation framing.
                    # Phase 15 Stage C (llm_prompt_redesign_da_sf.md §3.2): the full principal
                    # block, injected at BOTH Stage 1 and synthesis — not just synthesis as before.
                    # time_frame wires PrincipalProfile.time_frame, previously "framed but not
                    # wired" anywhere in the runtime (see project_principal_lens_weighting memory).
                    decision_maker = None
                    try:
                        pc = getattr(request, "principal_context", None)
                        if pc:
                            pc_dict = pc if isinstance(pc, dict) else _model_to_dict(pc)
                            if isinstance(pc_dict, dict):
                                _tf = pc_dict.get("time_frame")
                                _tf_dict = _tf if isinstance(_tf, dict) else _model_to_dict(_tf) if _tf else None
                                # accountability_scope: no dedicated field exists on PrincipalProfile
                                # today — business_processes/kpis are the real, existing proxy.
                                # decision_authority has no source field at all; omitted rather than
                                # fabricated (design principle: no invented defaults).
                                _accountability = [
                                    *(pc_dict.get("business_processes") or []),
                                    *(pc_dict.get("kpis") or []),
                                ]
                                decision_maker = {k: v for k, v in {
                                    "name": pc_dict.get("name") or pc_dict.get("principal_name"),
                                    "role": pc_dict.get("role") or pc_dict.get("title"),
                                    "decision_style": pc_dict.get("decision_style"),
                                    # PrincipalContext.communication_style — sourced from the registry's
                                    # real communication.detail_level field (high/medium/low). Unlike role-
                                    # title keyword matching, this is genuinely wired per-principal.
                                    "communication_style": pc_dict.get("communication_style"),
                                    "priorities": pc_dict.get("current_focus") or pc_dict.get("priorities"),
                                    "time_frame": (_tf_dict.get("default_period") if isinstance(_tf_dict, dict) else None),
                                    "accountability_scope": _accountability[:5] or None,
                                    "decision_authority": pc_dict.get("decision_authority"),
                                }.items() if v}
                    except Exception:
                        decision_maker = None

                    # Phase 15 Stage D (llm_prompt_redesign_da_sf.md / theory_layer_design.md
                    # §5.2): grounding + constraint input contract. Default OFF
                    # (enable_causal_grounding) — the READ path here is safe and non-fatal
                    # (degrades to no context if the schema isn't migrated, tables are
                    # empty, or client_id/kpi_id can't be resolved), but consuming this
                    # content in real recommendations is still gated on tenant-isolation
                    # tests + a pilot with real SF usage. Reuses A9_Deep_Analysis_Agent's
                    # tenant-safe _lookup_kpi_scoped pattern (fix commit 5925de7) — a
                    # same-id KPI from another tenant is never an acceptable fallback.
                    #
                    # Fetched HERE (before Stage 1 runs), not just before synthesis — a
                    # persona forming a hypothesis with no knowledge of a known-impossible
                    # constraint or an already-established causal mechanism produces a
                    # hypothesis synthesis then has to silently override or contradict.
                    # Constraints are worth preventing at the source, not patching after.
                    _cg_relationships: List[Any] = []
                    _cg_constraints: List[Any] = []
                    if getattr(self.config, "enable_causal_grounding", False):
                        try:
                            _cg_client_id = (
                                (da_summary.get("client_id") if da_summary else None)
                                or getattr(request, "client_id", None)
                            )
                            _cg_kpi_ref = da_summary.get("kpi_name") if da_summary else None
                            _cg_kpi = _lookup_kpi_scoped(_cg_kpi_ref, _cg_client_id, self.logger)
                            if _cg_client_id and _cg_kpi is not None:
                                _cg_kpi_id = getattr(_cg_kpi, "id", None)
                                from src.registry.providers.kpi_relationship_provider import KPIRelationshipProvider
                                from src.registry.providers.assumption_provider import AssumptionProvider

                                _cg_relationships = await KPIRelationshipProvider().get_relationships_for_kpi(
                                    _cg_kpi_id, _cg_client_id
                                )
                                _cg_constraints = await AssumptionProvider().get_active_constraints(
                                    _cg_client_id, scope=_cg_kpi_id
                                )
                            elif _cg_client_id and _cg_kpi_ref:
                                self.logger.info(
                                    f"[SF] Causal grounding: KPI '{_cg_kpi_ref}' not resolvable for "
                                    f"client '{_cg_client_id}' — proceeding without causal context"
                                )
                        except Exception as e:
                            # Non-fatal by design: missing migration, empty tables, or a
                            # cold registry pool must never break solution generation.
                            self.logger.info(f"[SF] Causal grounding unavailable (non-fatal): {e}")

                    # Extract situation metadata for urgency calibration (severity, unit, threshold)
                    situation_metadata = None
                    try:
                        sctx = getattr(request, "situation_context", None)
                        if sctx:
                            sctx_dict = sctx if isinstance(sctx, dict) else _model_to_dict(sctx)
                            if isinstance(sctx_dict, dict):
                                _kv = sctx_dict.get("kpi_value") or {}
                                if not isinstance(_kv, dict):
                                    _kv = _model_to_dict(_kv) or {}
                                situation_metadata = {k: v for k, v in {
                                    "severity": str(sctx_dict.get("severity") or ""),
                                    "kpi_name": sctx_dict.get("kpi_name"),
                                    "current_value": _kv.get("value"),
                                    "comparison_value": _kv.get("comparison_value"),
                                    "unit": _kv.get("unit"),
                                    "threshold": sctx_dict.get("threshold") or sctx_dict.get("threshold_value"),
                                }.items() if v is not None and v != ""}
                    except Exception:
                        situation_metadata = None

                    # ---- STAGE 1: Parallel per-persona hypothesis generation ----
                    # Each persona independently proposes one hypothesis + one option with quantified impact.
                    # Running in parallel cuts total latency to ~1 LLM call duration.
                    # Skip for subsequent debate stages (cross_review/synthesis) — Stage 1 already done.
                    import json as _json_s1
                    _debate_stage = prefs.get("debate_stage") if isinstance(prefs, dict) else None
                    # Skip Stage 1 Haiku calls for stages that already have prior hypotheses.
                    # 'hypothesis' stage also skips Stage 1 when prior_stage1_hypotheses is provided
                    # (used when stage1_only pre-call already collected them for fast card reveal).
                    _skip_stage1 = (
                        _debate_stage in ("cross_review", "synthesis")
                        or (
                            _debate_stage == "hypothesis"
                            and isinstance(prefs, dict)
                            and isinstance(prefs.get("prior_stage1_hypotheses"), dict)
                        )
                    )
                    stage_1_hyps_dict: Dict[str, Any] = {}
                    # Restore Stage 1 hypotheses for any stage that skips the parallel Haiku calls
                    if _skip_stage1 and isinstance(prefs, dict):
                        _prior_s1 = prefs.get("prior_stage1_hypotheses")
                        if isinstance(_prior_s1, dict):
                            stage_1_hyps_dict = _prior_s1
                            self.logger.info(f"[SF] Restored {len(stage_1_hyps_dict)} Stage 1 hypotheses from prior call")
                    _skip_synthesis_llm = False  # Set True for stage1_only after Stage 1 completes
                    if consulting_personas and not _skip_stage1:
                        # In mixed mode the IS list carries both problem and opportunity items.
                        # Filter where_signals and where_is_not by segment_type so Stage 1
                        # personas see only the segments relevant to the resolved mode — preventing
                        # the LLM from oscillating between "scale winners" and "fix losers" framing
                        # across runs on identical data.
                        _raw_where_signals = da_summary.get("where_signals", [])
                        _raw_where_is_not  = da_summary.get("where_is_not", [])
                        if is_opportunity and _raw_where_signals:
                            _opp_signals  = [s for s in _raw_where_signals
                                             if not isinstance(s, dict) or s.get("segment_type") != "problem"]
                            _prob_signals  = [s for s in _raw_where_signals
                                             if isinstance(s, dict) and s.get("segment_type") == "problem"]
                            # Opportunity mode: IS = leaders, IS NOT = laggards (replication targets)
                            _where_signals_s1  = (_opp_signals  or _raw_where_signals)[:3]
                            _where_is_not_s1   = (_prob_signals or _raw_where_is_not)[:3]
                        else:
                            _where_signals_s1 = _raw_where_signals[:3]
                            _where_is_not_s1  = _raw_where_is_not[:3]

                        da_compact_s1 = {
                            "kpi_name": da_summary.get("kpi_name"),
                            "analysis_mode": analysis_mode,
                            "top_change_points": da_summary.get("top_change_points", [])[:3],
                            "where_signals": _where_signals_s1,
                            "where_is_not": _where_is_not_s1,
                            "what_is_not": da_summary.get("what_is_not", [])[:3],
                        }
                        if da_summary.get("benchmark_segments"):
                            da_compact_s1["internal_benchmarks"] = da_summary["benchmark_segments"]
                        # Inject market conflict so personas factor in external headwinds/tailwinds
                        _s1_conflict = da_ctx.get("market_conflict") if isinstance(da_ctx, dict) else None
                        if _s1_conflict and _s1_conflict.get("detected") and _s1_conflict.get("summary"):
                            da_compact_s1["market_signal_conflict"] = _s1_conflict["summary"]
                        bc_compact_s1: Dict[str, Any] = {}
                        if isinstance(bc, dict):
                            bc_compact_s1 = {k: v for k, v in {
                                "name": bc.get("name"),
                                "industry": bc.get("industry"),
                                "operational_context": bc.get("operational_context"),
                            }.items() if v}

                        # Build compact principal constraints for Stage 1 from Problem Refinement dialogue
                        refinement_compact_s1: Dict[str, Any] = {}
                        if refinement_result:
                            excl = [
                                e.get("value", str(e)) if isinstance(e, dict) else str(e)
                                for e in refinement_result.get("exclusions", [])[:5]
                            ]
                            if excl:
                                refinement_compact_s1["do_not_propose"] = excl
                            if refinement_result.get("constraints"):
                                refinement_compact_s1["constraints"] = refinement_result["constraints"][:5]
                            if refinement_result.get("validated_hypotheses"):
                                refinement_compact_s1["confirmed_causes"] = refinement_result["validated_hypotheses"][:3]
                            if refinement_result.get("invalidated_hypotheses"):
                                refinement_compact_s1["ruled_out_causes"] = refinement_result["invalidated_hypotheses"][:3]
                            if refinement_result.get("external_context"):
                                refinement_compact_s1["principal_context"] = refinement_result["external_context"][:3]

                        # Phase 15 Stage D: accreted constraints (kpi_relationships/assumptions,
                        # fetched above BEFORE Stage 1 runs) merge into the SAME field the LLM
                        # is already instructed to respect ("Respect any do_not_propose items
                        # and constraints from PRINCIPAL CONSTRAINTS" in the RULES below) —
                        # reusing the existing mechanism rather than inventing a second one a
                        # persona would have to separately learn to honor. Deliberately a
                        # sibling of the refinement_result block above, not nested inside it —
                        # accreted constraints are independent of whether refinement chat ran.
                        if _cg_constraints:
                            _cg_constraint_texts = [c.text for c in _cg_constraints][:5]
                            refinement_compact_s1["constraints"] = (
                                refinement_compact_s1.get("constraints", []) + _cg_constraint_texts
                            )[:5]

                        # Use refined problem statement in Stage 1 if principal provided one
                        ps_s1 = ps
                        if refinement_result and refinement_result.get("refined_problem_statement"):
                            ps_s1 = f"{ps}\nRefined focus: {refinement_result['refined_problem_statement']}"

                        async def _run_stage1(p: ConsultingPersona) -> Optional[Dict]:
                            try:
                                persona_profile = p.to_prompt_context() if hasattr(p, "to_prompt_context") else f"{p.name}"
                                s1_schema = (
                                    '{\n'
                                    f'  "persona_id": "{p.id}",\n'
                                    '  "framework": "<signature diagnostic framework name>",\n'
                                    '  "hypothesis": "<root cause hypothesis citing specific data>",\n'
                                    '  "key_evidence": ["<data point 1>", "<data point 2>", "<data point 3>"],\n'
                                    '  "recommended_focus": "<entity name only — e.g. \'High Mileage Engine Oil\' or \'Retail Products Division\'>",\n'
                                    '  "conviction": "High|Medium|Low",\n'
                                    '  "proposed_option": {\n'
                                    '    "title": "<action-oriented title reflecting your mechanism>",\n'
                                    '    "description": "<2-3 sentences: what, how, why now>",\n'
                                    '    "mechanism": "<how this directly addresses the identified driver>",\n'
                                    '    "time_horizon": "0-90 days|3-12 months|12+ months",\n'
                                    '    "impact_estimate": {\n'
                                    '      "metric": "<KPI name from SITUATION METRICS section>",\n'
                                    '      "unit": "<unit from SITUATION METRICS section>",\n'
                                    '      "recovery_range": {"low": <estimated_low_number>, "high": <estimated_high_number>},\n'
                                    '      "basis": "<mechanism + magnitude from change_points>"\n'
                                    '    },\n'
                                    '    "cost_signal": "High|Medium|Low",\n'
                                    '    "risk_signal": "High|Medium|Low"\n'
                                    '  }\n'
                                    '}'
                                )
                                principal_constraints_section = ""
                                if refinement_compact_s1:
                                    principal_constraints_section = (
                                        "## PRINCIPAL CONSTRAINTS\n"
                                        f"{_json_s1.dumps(refinement_compact_s1, indent=2)}\n\n"
                                    )
                                # Phase 15 Stage C (llm_prompt_redesign_da_sf.md §3.2): principal
                                # block injected at BOTH stages, paired with a consumption
                                # instruction — data without direction is tokens wasted.
                                decision_maker_section = ""
                                if decision_maker:
                                    _dm_role = decision_maker.get("role") or "the decision maker"
                                    _dm_pri = decision_maker.get("priorities")
                                    _dm_pri_str = ", ".join(_dm_pri) if isinstance(_dm_pri, list) else (_dm_pri or "not specified")
                                    _dm_horizon = decision_maker.get("time_frame") or "not specified"
                                    decision_maker_section = (
                                        "## DECISION MAKER\n"
                                        f"{_json_s1.dumps(decision_maker, indent=2)}\n"
                                        f"You are advising the {_dm_role} directly. Weight your hypothesis and option "
                                        f"toward their stated priorities ({_dm_pri_str}) and planning horizon ({_dm_horizon}). "
                                        "Conviction should reflect what evidence would move *this* decision maker.\n\n"
                                    )
                                # Phase 15 Stage D: causal-chain grounding at Stage 1, not just
                                # synthesis — a persona forming its hypothesis from scratch each
                                # time, unaware of an already-established mechanism/lag for this
                                # KPI, either re-derives what's already known or contradicts it.
                                # Constraints are handled separately above (merged into
                                # refinement_compact_s1["constraints"], the existing mechanism);
                                # this is the mechanism/lag/provenance grounding only.
                                causal_context_section_s1 = (
                                    _build_causal_context_section(_cg_relationships, [])
                                    if _cg_relationships else ""
                                )
                                if is_opportunity:
                                    _s1_task = (
                                        f"As {p.name}, apply your replication/scaling methodology to:\n"
                                        "1. Form ONE specific hypothesis about WHY the IS (leading) segment is outperforming\n"
                                        "2. Propose ONE actionable strategy to replicate/scale the IS segment's outperformance to the IS NOT (lagging) segments\n"
                                        "3. Estimate the replication uplift using the KPI unit from SITUATION METRICS — recovery_range = potential uplift in lagging segments (MUST be non-zero)\n"
                                        "4. Provide 3 specific data points as evidence from the analysis signals\n"
                                        + (
                                            "5. Name the IS segment (internal_benchmark) explicitly and quantify the replication potential using its delta.\n"
                                            if da_compact_s1.get("internal_benchmarks") else ""
                                        )
                                        + "RULES: recommended_focus = the IS (leading) segment entity name only. "
                                        "recovery_range low/high = estimated replication uplift in lagging segments (NEVER 0.0). "
                                        "Frame hypothesis as 'outperformance driver', not 'root cause of problem'. "
                                        "Respect any do_not_propose items from PRINCIPAL CONSTRAINTS.\n\n"
                                    )
                                else:
                                    _s1_task = (
                                        f"As {p.name}, apply your methodology to:\n"
                                        "1. Form ONE specific hypothesis about the primary driver of this KPI situation\n"
                                        "2. Propose ONE actionable intervention with a distinct mechanism\n"
                                        "3. Estimate the recovery/uplift impact using the KPI unit from the SITUATION METRICS section above — recovery_range MUST be non-zero numbers proportional to the observed variance\n"
                                        "4. Provide 3 specific data points as evidence from the analysis signals\n"
                                        + (
                                            "5. If internal_benchmarks are present in KEY ANALYSIS SIGNALS, consider replication strategies — "
                                            "how can the outperforming segment's practices be scaled to underperforming areas?\n"
                                            if da_compact_s1.get("internal_benchmarks") else ""
                                        )
                                        + "RULES: recommended_focus = entity name only, NO field prefixes (e.g. 'High Mileage Engine Oil', NOT 'product_name: High Mileage Engine Oil'). "
                                        "recovery_range low/high = actual numeric estimates (NEVER 0.0). cost_signal and risk_signal must reflect your mechanism's complexity. "
                                        "Respect any do_not_propose items and constraints from PRINCIPAL CONSTRAINTS — do not propose excluded options.\n\n"
                                    )
                                s1_prompt = (
                                    f"## ROLE\nYou are a {p.name} consultant.\n\n"
                                    f"## PERSONA\n{persona_profile}\n\n"
                                    f"## PROBLEM\n{ps_s1}\n\n"
                                    "## KEY ANALYSIS SIGNALS\n"
                                    f"{_json_s1.dumps(da_compact_s1, indent=2)}\n\n"
                                    "## BUSINESS CONTEXT\n"
                                    f"{_json_s1.dumps(bc_compact_s1, indent=2)}\n\n"
                                    "## SITUATION METRICS\n"
                                    f"{_json_s1.dumps(situation_metadata or {}, indent=2)}\n\n"
                                    f"{decision_maker_section}"
                                    f"{causal_context_section_s1}"
                                    f"{principal_constraints_section}"
                                    "## YOUR TASK\n"
                                    f"{_s1_task}"
                                    f"## OUTPUT (JSON only, no markdown):\n{s1_schema}"
                                )
                                s1_req = A9_LLM_AnalysisRequest(
                                    request_id=f"{req_id}_s1_{p.id}",
                                    principal_id=getattr(request, "principal_id", "system"),
                                    content=s1_prompt,
                                    analysis_type="custom",
                                    context="",
                                    # Light model for focused single-persona call (overridable via CLAUDE_MODEL_STAGE1)
                                    model=get_claude_model_for_task(ClaudeTaskType.STAGE1_PERSONA),
                                    # temperature=0 ensures identical inputs always produce the same
                                    # hypothesis — prevents mode drift across repeated runs on the same DA data
                                    temperature=0.0,
                                )
                                if self.orchestrator is not None:
                                    s1_resp = await self.orchestrator.execute_agent_method(
                                        "A9_LLM_Service_Agent", "analyze", {"request": s1_req}
                                    )
                                else:
                                    s1_resp = await self.llm_service_agent.analyze(s1_req)  # type: ignore
                                # Recorded before the status check so a FAILED persona
                                # still shows its cost — a call that errors after
                                # generating tokens is billed just the same.
                                _record_usage(f"stage1_{p.id}", s1_resp)
                                _s1_status = getattr(s1_resp, "status", "error")
                                s1_result = getattr(s1_resp, "analysis", None) if _s1_status == "success" else None
                                if isinstance(s1_result, dict):
                                    return s1_result
                                # Both remaining paths previously fell through to a
                                # bare `return None` with NO log line, so a persona
                                # dropping out of the council was invisible — the only
                                # trace was a shorter list in "Stage 1 complete: [...]",
                                # which is easy to miss and impossible to diagnose after
                                # the fact. Observed 2026-08-02: 2 of 3 personas vanished
                                # with nothing logged anywhere.
                                self.logger.warning(
                                    "[SF] Stage 1 produced no usable hypothesis for %s: status=%s, analysis_type=%s, error=%s",
                                    p.id, _s1_status, type(getattr(s1_resp, "analysis", None)).__name__,
                                    getattr(s1_resp, "error", None) or getattr(s1_resp, "error_message", None),
                                )
                            except Exception as _s1e:
                                self.logger.warning(f"[SF] Stage 1 call failed for {p.id}: {_s1e}")
                            return None

                        s1_raw = await asyncio.gather(*[_run_stage1(p) for p in consulting_personas])
                        # Key results by POSITION, not by the LLM echoing its own identity.
                        # gather() preserves input order, so persona attribution is already
                        # known with certainty. The previous loop keyed on _r["persona_id"]
                        # and silently discarded any result where the model omitted or
                        # renamed that field — observed live 2026-08-04: mckinsey's call
                        # succeeded (status=success, valid dict, tokens billed) and the
                        # council quietly proceeded with 2 of 3 firms, no log, no error.
                        # Trusting a generated field for attribution when the caller
                        # already holds ground truth was the defect.
                        _dropped_personas: List[str] = []
                        for p, _r in zip(consulting_personas, s1_raw):
                            if not isinstance(_r, dict):
                                _dropped_personas.append(p.id)  # per-call warning already logged in _run_stage1
                                continue
                            _echoed = _r.get("persona_id")
                            if _echoed and _echoed != p.id:
                                # Attribution stands with the caller; the echo is merely wrong.
                                self.logger.warning(
                                    "[SF] Stage 1 result for %s self-identified as %r — keeping positional attribution",
                                    p.id, _echoed,
                                )
                            stage_1_hyps_dict[p.id] = {
                                "framework": _r.get("framework"),
                                "hypothesis": _r.get("hypothesis"),
                                "key_evidence": _r.get("key_evidence", []),
                                "recommended_focus": _r.get("recommended_focus"),
                                "conviction": _r.get("conviction"),
                                "proposed_option": _r.get("proposed_option"),
                            }
                        audit_log.append({
                            "event": "stage1_calls_complete",
                            "personas": list(stage_1_hyps_dict.keys()),
                            # A shrunken council must be visible in the payload, not
                            # only inferable from a shorter list.
                            "dropped_personas": _dropped_personas,
                        })
                        if _dropped_personas:
                            self.logger.warning(
                                "[SF] Council reduced: %d of %d personas produced no usable hypothesis: %s",
                                len(_dropped_personas), len(consulting_personas), _dropped_personas,
                            )
                        self.logger.info(f"[SF] Stage 1 complete: {list(stage_1_hyps_dict.keys())}")
                        # stage1_only: return Stage 1 results immediately — skip synthesis Sonnet call.
                        # The frontend shows firm cards as soon as this returns, then fires the
                        # 'hypothesis' stage call (Sonnet-only, using prior_stage1_hypotheses).
                        if _debate_stage == "stage1_only":
                            _skip_synthesis_llm = True
                            stage_1_hypotheses_final = stage_1_hyps_dict
                            for _idx, (_pid, _hyp) in enumerate(stage_1_hyps_dict.items()):
                                _po = _hyp.get("proposed_option") or {}
                                options.append(SolutionOption(
                                    id=_po.get("id") or f"opt_{_idx + 1}",
                                    title=str(_po.get("title") or f"Hypothesis ({_pid})"),
                                    description=_po.get("description"),
                                    expected_impact=0.6, cost=0.4, risk=0.3,
                                ))
                            self.logger.info(f"[SF] stage1_only: {len(options)} Stage 1 options captured, synthesis LLM skipped")

                    # Phase 15 Stage E: critic pass (generate -> critique-against-theory ->
                    # synthesize). Runs HERE — after Stage 1 completes (needs real proposals
                    # to critique) and before synthesis (feeds findings in so synthesis can
                    # address them at the source, not patch them after the fact — same
                    # principle as the Stage D constraint-timing fix). Gated on BOTH
                    # enable_critic_pass and enable_causal_grounding — a critic with no
                    # causal graph has nothing to critique against. Skipped entirely in
                    # stage1_only mode (_skip_synthesis_llm) since there's no synthesis call
                    # to feed findings into.
                    critic_findings: List[Dict[str, Any]] = []
                    if (
                        not _skip_synthesis_llm
                        and getattr(self.config, "enable_critic_pass", False)
                        and getattr(self.config, "enable_causal_grounding", False)
                        and stage_1_hyps_dict
                        and (_cg_relationships or _cg_constraints)
                    ):
                        try:
                            _critic_causal_section = _build_causal_context_section(_cg_relationships, _cg_constraints)
                            _critic_proposals = []
                            for _pid, _hyp in stage_1_hyps_dict.items():
                                _po = _hyp.get("proposed_option") or {}
                                _critic_proposals.append({
                                    "persona_id": _pid,
                                    "title": _po.get("title") if isinstance(_po, dict) else None,
                                    "mechanism": _po.get("mechanism") if isinstance(_po, dict) else None,
                                    "recommended_focus": _hyp.get("recommended_focus"),
                                })
                            _critic_prompt = (
                                "## ROLE\n"
                                "You are a skeptical reviewer checking proposed interventions against a "
                                "verified causal model of this business, before they reach an executive.\n\n"
                                "## PROPOSED OPTIONS (from persona hypotheses)\n"
                                f"{_json_s1.dumps(_critic_proposals, indent=2)}\n\n"
                                f"{_critic_causal_section}"
                                "## YOUR TASK\n"
                                "For each proposed option, check ONLY against the causal context and "
                                "constraints above:\n"
                                "1. Does pursuing this option's mechanism plausibly affect another KPI shown "
                                "in the causal chain, in a way that could work against a stated priority or "
                                "create an unintended consequence?\n"
                                "2. Does this option conflict with any KNOWN CONSTRAINT listed above?\n"
                                "Flag a finding ONLY when it is grounded in the causal context or constraints "
                                "provided above — do NOT invent generic risks with no basis in that data. If "
                                "an option has no genuine concern, do not include it in your findings.\n\n"
                                "## OUTPUT (JSON only, no markdown)\n"
                                "{\"findings\": [{\"persona_id\": \"...\", \"concern\": \"<specific, grounded "
                                "concern>\", \"affected_kpi\": \"<kpi id or null>\", \"severity\": "
                                "\"low|moderate|high\"}]}"
                            )
                            _critic_req = A9_LLM_AnalysisRequest(
                                request_id=f"{req_id}_critic",
                                principal_id=getattr(request, "principal_id", None),
                                content=_critic_prompt,
                                analysis_type="custom",
                                context="",
                                # "Best model spent here" per the design intent — routes to the
                                # same Sonnet 5 default as REASONING/SYNTHESIS (11O-C keeps Fable
                                # deferred to the offline path, not this interactive one).
                                model=get_claude_model_for_task(ClaudeTaskType.CRITIC),
                                max_tokens=2000,
                            )
                            if self.orchestrator is not None:
                                _critic_resp = await self.orchestrator.execute_agent_method(
                                    "A9_LLM_Service_Agent", "analyze", {"request": _critic_req}
                                )
                            else:
                                _critic_resp = await self.llm_service_agent.analyze(_critic_req)  # type: ignore
                            _record_usage("critic_pass", _critic_resp)
                            if getattr(_critic_resp, "status", "error") == "success":
                                _critic_analysis = getattr(_critic_resp, "analysis", None)
                                if isinstance(_critic_analysis, dict):
                                    critic_findings = [
                                        f for f in (_critic_analysis.get("findings") or [])
                                        if isinstance(f, dict) and f.get("concern")
                                    ]
                            if critic_findings:
                                audit_log.append({"event": "critic_pass_findings", "count": len(critic_findings)})
                                self.logger.info(f"[SF] Critic pass: {len(critic_findings)} grounded finding(s)")
                        except Exception as e:
                            # Non-fatal by design: a critic-call failure must never break
                            # solution generation — same discipline as Stage D's causal fetch.
                            self.logger.info(f"[SF] Critic pass unavailable (non-fatal): {e}")
                            critic_findings = []

                    # ---- STAGE 2: Synthesis call ----
                    # Separate the data payload from the instructions
                    # The debate_spec contains critical constraints that must be in the prompt prefix
                    # When Stage 1 hypotheses exist, skip full DA context — the summary
                    # carries all key signals and the personas already processed the full context.
                    # This saves ~8-12K tokens per synthesis call (major latency reduction).
                    _include_full_da = not stage_1_hyps_dict
                    data_payload = {
                        "problem_statement": ps,
                        "situation_metadata": situation_metadata,
                        "decision_maker": decision_maker,
                        "business_context": _model_to_dict(bc) if bc else None,
                        **({"deep_analysis_context": full_da_context} if _include_full_da else {}),
                        "deep_analysis_summary": da_summary,
                        "dataset_recap": dataset_recap,
                        "user_context": user_ctx,
                        "principal_input": _model_to_dict(principal_input) if principal_input else None,
                        # Stage 1 results: each persona's hypothesis + proposed_option for synthesis
                        "stage_1_persona_hypotheses": stage_1_hyps_dict if stage_1_hyps_dict else None,
                    }
                    import json as _json
                    data_json = _json.dumps(data_payload, indent=2)

                    # Extract actual Stage 1 recovery_range values to inject as explicit anchors.
                    # The <S1_low_estimate> placeholders in debate_spec are unreliable — LLMs often
                    # output 0 when they have to locate the values themselves in a large JSON blob.
                    # Injecting them as named constants guarantees non-zero synthesis output.
                    recovery_anchors_section = ""
                    if stage_1_hyps_dict:
                        _opt_ids = ["opt_1", "opt_2", "opt_3"]
                        _anchor_lines: List[str] = []
                        for _i, (_pid, _hyp) in enumerate(list(stage_1_hyps_dict.items())[:3]):
                            _po = _hyp.get("proposed_option") or {}
                            _ie = _po.get("impact_estimate") or {} if isinstance(_po, dict) else {}
                            _rr = _ie.get("recovery_range") or {} if isinstance(_ie, dict) else {}
                            _low = _rr.get("low") if isinstance(_rr, dict) else None
                            _high = _rr.get("high") if isinstance(_rr, dict) else None
                            if _low is not None and _high is not None and (_low != 0 or _high != 0):
                                _anchor_lines.append(
                                    f"  {_opt_ids[_i]} (from {_pid}): "
                                    f'recovery_range = {{"low": {_low}, "high": {_high}}}'
                                )
                        if _anchor_lines:
                            recovery_anchors_section = (
                                "## RECOVERY RANGE ANCHORS\n"
                                "Use these EXACT numeric values for impact_estimate.recovery_range in your JSON output.\n"
                                "Do NOT substitute 0 or null — these are the Stage 1 quantified estimates:\n"
                                + "\n".join(_anchor_lines) + "\n"
                                + "CRITICAL COMPLIANCE CHECK: If ANY anchor value above appears as 0.0 or if you cannot find the anchor values, DO NOT output 0.0. Instead, derive a directionally appropriate estimate:\n"
                                + "- For an immediate operational fix (0-90 days): estimate recovery as 30-50% of the observed variance magnitude\n"
                                + "- For a structural fix (3-12 months): estimate 40-70% of the observed variance magnitude\n"
                                + "- For a strategic portfolio shift (12+ months): estimate 20-40% of the observed variance magnitude\n"
                                + "Zero is never an acceptable recovery_range value. A partial estimate is always better than 0.\n\n"
                            )

                    # Phase 15 Stage C (llm_prompt_redesign_da_sf.md §3.2): decision_maker was
                    # previously placed into data_payload with no instruction consuming it —
                    # "data without direction is tokens wasted". This section is the paired
                    # instruction (exact wording per the design doc) plus Phase 13 Cat 4
                    # principal-adaptive framing. M1 (pre-mortem): role adaptation controls
                    # entry point and depth only — the conclusion is identical for every role,
                    # stated explicitly below rather than left implicit.
                    decision_maker_synthesis_section = ""
                    if decision_maker:
                        _dm_role = decision_maker.get("role") or "the decision maker"
                        # communication_style (registry: communication.detail_level) is the real,
                        # per-principal signal for depth — not a role-title keyword guess (see
                        # DEVELOPMENT_PLAN.md Phase 15 Stage C notes: the earlier "cfo"/"ceo"/...
                        # substring match was a brittle, non-generalizing proxy for this).
                        _dm_detail = str(decision_maker.get("communication_style") or "medium").lower()
                        if _dm_detail == "low":
                            _depth_instruction = "Lead with the decision, 5-8 bullets, business-risk language — this reader delegates diagnostic depth."
                        elif _dm_detail == "high":
                            _depth_instruction = "Include diagnostic depth and implementation-level detail — this reader executes, not just decides."
                        else:
                            _depth_instruction = "Balance decision-first framing with enough diagnostic detail to support follow-up questions."
                        decision_maker_synthesis_section = (
                            "## DECISION MAKER — CONSUMPTION INSTRUCTIONS\n"
                            f"Rank options and frame `time_to_value` against {_dm_role}'s planning horizon "
                            f"(decision_maker.time_frame). Lead `recommendation_rationale` with their top stated "
                            f"priority (decision_maker.priorities). Flag any option exceeding their decision "
                            f"authority as requiring escalation in that option's `prerequisites`.\n"
                            f"Role-adaptive presentation for {_dm_role}: {_depth_instruction} "
                            "This changes ENTRY POINT AND DEPTH ONLY — every principal must reach the identical "
                            "recommendation and options from the same underlying facts; never let role adaptation "
                            "change the conclusion.\n\n"
                        )

                    # Phase 15 Stage D: causal chain + constraints for synthesis. Uses the
                    # SAME fetch already done above (before Stage 1 ran) — not re-queried
                    # here. Synthesis needs its own explicit view because the legacy/
                    # non-hybrid-council path generates directly with no Stage 1 at all.
                    causal_context_section = _build_causal_context_section(_cg_relationships, _cg_constraints)

                    # Phase 15 Stage E: feed critic findings into synthesis so they get
                    # addressed at generation time, not bolted on afterward. Findings map
                    # to the ORIGINATING persona, not yet to a final opt_N id (synthesis
                    # assigns those) — so synthesis is instructed to match by mechanism/
                    # persona and populate flagged_side_effects on the corresponding option.
                    critic_findings_section = ""
                    if critic_findings:
                        _cf_lines = ["## CRITIC FINDINGS (theory-grounded review — address these, do not silently drop them)"]
                        for _f in critic_findings:
                            _cf_line = f"- From {_f.get('persona_id', 'a persona')}'s proposal: {_f.get('concern', '')}"
                            if _f.get("affected_kpi"):
                                _cf_line += f" (affects: {_f['affected_kpi']})"
                            if _f.get("severity"):
                                _cf_line += f" [severity: {_f['severity']}]"
                            _cf_lines.append(_cf_line)
                        _cf_lines.append(
                            "For the final option expanded from a flagged persona's proposal, populate "
                            "that option's 'flagged_side_effects' field with the concern (in the "
                            "executive's language, not verbatim) and address it in the rationale or "
                            "prerequisites. Do not silently drop a flagged concern.\n"
                        )
                        critic_findings_section = "\n".join(_cf_lines) + "\n\n"

                    # Build the full prompt with debate_spec as the instruction prefix
                    # This ensures the LLM sees the constraints BEFORE the data
                    full_prompt = (
                        f"{debate_spec}\n\n"
                        f"{decision_maker_synthesis_section}"
                        f"{causal_context_section}"
                        f"{critic_findings_section}"
                        f"## INPUT DATA\n{data_json}\n\n"
                        f"{recovery_anchors_section}"
                        f"## YOUR RESPONSE (JSON ONLY):"
                    )

                    # Phase 15 Stage A: forced tool-use structured output — opt-in only.
                    # Default False until the live A/B compliance run (M2/M5) confirms
                    # quality parity vs the current hand-tuned prompt (see
                    # DEVELOPMENT_PLAN.md Phase 15, A9_Solution_Finder_Agent_Config).
                    _structured_kwargs: Dict[str, Any] = {}
                    if getattr(self.config, "use_structured_output", False):
                        _structured_kwargs["response_schema"] = SFSynthesisSchema.model_json_schema()
                        _structured_kwargs["tool_name"] = "emit_sf_synthesis"

                    analysis_req = A9_LLM_AnalysisRequest(
                        request_id=req_id,
                        principal_id=getattr(request, "principal_id", None),
                        timestamp=getattr(request, "timestamp", None),
                        principal_context=getattr(request, "principal_context", None),
                        situation_context=getattr(request, "situation_context", None),
                        business_context=getattr(request, "business_context", None),
                        content=full_prompt,  # Full prompt with instructions + data
                        analysis_type="custom",
                        context="",  # Empty context since debate_spec is now in content
                        # Full-power model for synthesis/cross-review (overridable via CLAUDE_MODEL_SYNTHESIS)
                        model=get_claude_model_for_task(ClaudeTaskType.SYNTHESIS),
                        # Synthesis JSON for complex datasets can exceed 10000 tokens — use full budget.
                        # Bumped from 16384 (Phase 11O's "thin headroom" watch item, DEVELOPMENT_PLAN.md
                        # line ~1358) after a live Phase 15 Stage D/E test reproduced the predicted
                        # truncation: causal-grounding + critic-pass content pushed synthesis past
                        # 16384 output tokens, producing a parsed dict with no "options" key and
                        # silently falling back to the hardcoded heuristic stub.
                        #
                        # 32000, now that claude_service streams.
                        #
                        # 20000 was a hard wall imposed by the SDK, not the model: it
                        # REJECTS non-streaming requests whose max_tokens implies a
                        # >10-minute generation (24000/32000/64000 all refused). Synthesis
                        # generated right at that wall — measured at exactly 20000 output
                        # tokens — and truncated mid-object, parsing to
                        # {"raw_response": ...} and returning the heuristic stub under
                        # status="success". Verified after the streaming change: 32000 and
                        # 64000 are now accepted.
                        #
                        # This is headroom, not a target. Billing is on tokens GENERATED,
                        # not the ceiling, so a larger number costs nothing unless the model
                        # actually writes more. What it buys is that a verbose run finishes
                        # instead of silently degrading to two generic options.
                        #
                        # The stochastic truncation this fixes was never prompt-size driven
                        # (it recurred with debate_spec back at baseline, on a LONGER body),
                        # so watch heuristic_stub_fallback rather than prompt length if it
                        # ever returns.
                        max_tokens=32000,
                        **_structured_kwargs,
                    )

                    # Record the analysis request components in audit for UI/debug
                    try:
                        def _to_obj(x):
                            try:
                                if hasattr(x, "model_dump"):
                                    return x.model_dump()
                                if hasattr(x, "__dict__"):
                                    return dict(x.__dict__)
                            except Exception:
                                return x
                            return x
                        audit_log.append({
                            "event": "llm_debate_analysis_req",
                            "principal_context": _to_obj(getattr(analysis_req, "principal_context", None)),
                            "situation_context": _to_obj(getattr(analysis_req, "situation_context", None)),
                            "business_context": _to_obj(getattr(analysis_req, "business_context", None)),
                            # Log the data payload for readability
                            "data_payload": data_payload,
                            "debate_spec_length": len(debate_spec),
                        })
                    except Exception:
                        pass

                    # Prefer orchestrator routing per LLM PRD; fallback to direct agent if missing
                    # stage1_only skips the synthesis LLM — Stage 1 Haiku results are sufficient
                    if _skip_synthesis_llm:
                        llm_resp = None
                    elif self.orchestrator is not None:
                        llm_resp = await self.orchestrator.execute_agent_method(
                            "A9_LLM_Service_Agent", "analyze", {"request": analysis_req}
                        )
                    else:
                        if not self.llm_service_agent:
                             raise Exception("A9_LLM_Service_Agent could not be acquired via Orchestrator or Registry.")
                        llm_resp = await self.llm_service_agent.analyze(analysis_req)  # type: ignore

                    # Extract options and rationale safely
                    llm_ok = getattr(llm_resp, "status", "error") == "success"
                    model_used = getattr(llm_resp, "model_used", None)
                    _record_usage("synthesis", llm_resp)
                    audit_log.append({
                        "event": "llm_debate_completed",
                        "status": getattr(llm_resp, "status", None),
                        "model_used": model_used,
                        # Carry the error text. status="error" alone says a call was
                        # rejected but not why, and the reason only reached the
                        # backend's console — invisible to anyone reading the payload
                        # afterwards, which cost a full live run to rediscover.
                        #
                        # The field is error_message. `error` is A9AgentBaseResponse's
                        # classmethod CONSTRUCTOR, so getattr(resp, "error") returns a
                        # bound method and str() of it yields
                        # "<bound method A9AgentBaseResponse.error ...>" — a live run
                        # was spent capturing exactly that instead of the message.
                        "error": (str(getattr(llm_resp, "error_message", None))[:400]
                                  if not llm_ok else None),
                    })

                    parsed = getattr(llm_resp, "analysis", None) if llm_ok else None
                    _has_options = isinstance(parsed, dict) and bool(parsed.get('options'))
                    self.logger.info(f"[SF] LLM response status: {getattr(llm_resp, 'status', 'unknown')}, parsed type: {type(parsed)}, has options: {_has_options}")
                    if not llm_ok:
                        self.logger.error(f"[SF] LLM call failed: {getattr(llm_resp, 'error', 'unknown error')}")
                    # Fallback if non-JSON returned
                    if isinstance(parsed, dict) and parsed.get("options"):
                        for idx, o in enumerate(parsed.get("options", []) or []):
                            try:
                                # Construct perspectives
                                pers_list = []
                                for p_dict in o.get("perspectives", []):
                                    try:
                                        pers_list.append(PerspectiveAnalysis(**p_dict))
                                    except:
                                        # Fallback for partial data
                                        pers_list.append(PerspectiveAnalysis(lens=p_dict.get("lens", "Unknown"), arguments_for=p_dict.get("arguments_for", [])))

                                options.append(
                                    SolutionOption(
                                        id=str(o.get("id") or f"opt{idx+1}"),
                                        title=str(o.get("title") or f"Option {idx+1}"),
                                        description=o.get("description"),
                                        expected_impact=_safe01(o.get("expected_impact")),
                                        cost=_safe01(o.get("cost")),
                                        risk=_safe01(o.get("risk")),
                                        rationale=o.get("rationale"),
                                        # New Fields
                                        time_to_value=o.get("time_to_value"),
                                        reversibility=o.get("reversibility"),
                                        perspectives=pers_list,
                                        implementation_triggers=o.get("implementation_triggers", []),
                                        prerequisites=o.get("prerequisites", []),
                                        impact_estimate=_parse_impact_estimate(o.get("impact_estimate")),
                                        # Phase 15 Stage B: per-option "bets on" assumptions
                                        key_assumptions=_parse_key_assumptions(o.get("key_assumptions")),
                                        # Phase 15 Stage E: critic-pass side effects, if any
                                        flagged_side_effects=[
                                            str(s) for s in (o.get("flagged_side_effects") or []) if s
                                        ],
                                    )
                                )
                            except Exception:
                                continue

                        # Phase 15 Stage B: top-level decision ask + immediate actions
                        decision_ask = _parse_decision_ask(parsed.get("decision_ask"))
                        immediate_actions_list = _parse_immediate_actions(parsed.get("immediate_actions"))

                        # Extract other top-level fields
                        problem_reframe = parsed.get("problem_reframe")
                        if not problem_reframe and da_summary.get("scqa_summary"):
                             # Fallback: Construct reframe from SCQA
                             problem_reframe = {
                                 "situation": da_summary.get("kpi_name") + " analysis",
                                 "complication": da_summary.get("scqa_summary", "Anomaly detected"),
                                 "question": "How to mitigate risk?",
                                 "key_assumptions": ["Data is accurate"]
                             }
                        
                        unresolved_tensions_list = []
                        for t in parsed.get("unresolved_tensions", []):
                            try:
                                unresolved_tensions_list.append(UnresolvedTension(**t))
                            except: 
                                pass

                        blind_spots_list = parsed.get("blind_spots", [])
                        next_steps_list = parsed.get("next_steps", [])
                        cross_review = parsed.get("cross_review")

                        # Use Stage 1 results as authoritative stage_1_hypotheses (dedicated calls = better quality)
                        # Strip proposed_option from the display dict (it's been expanded into the full options)
                        if stage_1_hyps_dict:
                            stage_1_hypotheses_final = {
                                pid: {k: v for k, v in hyp.items() if k != "proposed_option"}
                                for pid, hyp in stage_1_hyps_dict.items()
                            }
                        else:
                            # Fallback: synthesis LLM may not have generated this (removed from schema)
                            stage_1_hypotheses_final = parsed.get("stage_1_hypotheses") or {}

                        # Use LLM-generated rationale if available
                        rationale = parsed.get("recommendation_rationale") or "Options generated via Decision Briefing analysis."

                        # Add briefing dump to audit log
                        audit_log.append({
                            "event": "decision_briefing_generated",
                            "problem_reframe": problem_reframe,
                            "unresolved_tensions": [t.model_dump() for t in unresolved_tensions_list],
                            "blind_spots": blind_spots_list
                        })

                    # Market signals flow in from DA → Problem Refinement → external_context
                    # (MA call removed — no longer duplicated here)
                    ma_response = None

                except Exception as le:
                    # LLM path failed; fall back to heuristic. Full traceback (not just
                    # str(le)) — this fallback previously gave no way to distinguish a
                    # transient LLM/parse hiccup from a real code defect after the fact.
                    import traceback as _tb_debug
                    self.logger.info(f"LLM debate path failed, falling back to heuristic: {le}\n{_tb_debug.format_exc()}")
                    audit_log.append({"event": "llm_debate_error", "error": str(le)})

            # Heuristic fallback or augmentation if LLM didn't yield options
            if not options:
                # LOUD. This branch has now silently degraded a live run twice: once
                # when synthesis exceeded 16384 output tokens, and again after that
                # was bumped to 20000. Both times the response parsed into a dict
                # with no "options" key, raised nothing, and the generic stub
                # ("Tighten spend controls" / "Optimize pricing") was returned with
                # status="success" — indistinguishable from a real recommendation
                # until someone read the titles.
                #
                # An exception here would take the WHOLE workflow down for what may
                # be a transient truncation, so this stays non-fatal — but it must
                # never again be silent. Record what the LLM actually returned so a
                # truncation is separable from a genuinely empty response after the
                # fact, without needing to reproduce it live.
                # `parsed` is bound inside the LLM try-block, so it may be unbound
                # entirely if that block raised before reaching it. Resolve both it
                # and its type defensively — a diagnostic that itself raises would
                # re-hide exactly what it exists to expose.
                try:
                    _p = parsed  # noqa: F821 - may be unbound; guarded
                except NameError:
                    _p = None
                    _parsed_type = "unset"
                else:
                    _parsed_type = type(_p).__name__
                _parsed_keys = sorted(_p.keys()) if isinstance(_p, dict) else None
                _had_llm_error = any(a.get("event") == "llm_debate_error" for a in audit_log)
                self.logger.error(
                    "[SF] LLM produced NO options — returning the generic heuristic stub. "
                    "llm_raised=%s parsed_type=%s parsed_keys=%s. A dict lacking 'options' "
                    "points at max_tokens truncation of the synthesis JSON.",
                    _had_llm_error, _parsed_type, _parsed_keys,
                )
                # parsed_keys == ["raw_response"] means the response never parsed as
                # JSON at all. Record its length and tail: a long body ending
                # mid-token is truncation (raise max_tokens), whereas a short body or
                # one ending cleanly points at the model prefacing its JSON with
                # prose — different bugs, previously indistinguishable without
                # reproducing a 13-minute live run.
                _raw = _p.get("raw_response") if isinstance(_p, dict) else None
                _raw_info = None
                if isinstance(_raw, str):
                    _raw_info = {"len": len(_raw), "head": _raw[:120], "tail": _raw[-160:]}
                audit_log.append({
                    "event": "heuristic_stub_fallback",
                    "reason": "llm_yielded_no_options",
                    "llm_raised": _had_llm_error,
                    "parsed_keys": _parsed_keys,
                    "raw_response_info": _raw_info,
                })
                # Preserve Stage 1 hypotheses so progressive reveal still works even in fallback
                if stage_1_hyps_dict and not stage_1_hypotheses_final:
                    stage_1_hypotheses_final = stage_1_hyps_dict
                options = [
                    SolutionOption(id="opt1", title="Tighten spend controls", expected_impact=0.6, cost=0.3, risk=0.3),
                    SolutionOption(id="opt2", title="Optimize pricing", expected_impact=0.7, cost=0.5, risk=0.4),
                ]
                if not rationale:
                    rationale = "MVP heuristic ranking by weighted impact/cost/risk."
                
                # Ensure problem_reframe is populated even in fallback
                if not problem_reframe:
                     # Attempt to get SCQA from request context if available
                     scqa = "Anomaly detected requiring intervention"
                     da_ctx = request.deep_analysis_output or {}
                     if isinstance(da_ctx, dict):
                         scqa = da_ctx.get("scqa_summary") or scqa
                     elif hasattr(da_ctx, "scqa_summary"):
                         scqa = getattr(da_ctx, "scqa_summary") or scqa
                         
                     problem_reframe = {
                         "situation": "SYSTEM FAILURE - FALLBACK MODE",
                         "complication": "The AI reasoning engine is unavailable or encountered an error.",
                         "question": "What are the immediate mitigation steps (heuristic)?",
                         "key_assumptions": ["Standard operating procedures apply"]
                     }

            criteria = request.evaluation_criteria or [
                TradeOffCriterion(name="impact", weight=self.config.weight_impact),
                TradeOffCriterion(name="cost", weight=self.config.weight_cost),
                TradeOffCriterion(name="risk", weight=self.config.weight_risk),
            ]
            ranked = self._rank_options(options, criteria)
            recommendation = ranked[0] if ranked else None

            # Normalize nested models to plain dict payloads to avoid cross-module identity issues
            try:
                criteria_payload = [
                    (c.model_dump() if hasattr(c, "model_dump") else {"name": getattr(c, "name", None), "weight": getattr(c, "weight", None)})
                    for c in (criteria or [])
                ]
            except Exception:
                criteria_payload = [
                    {"name": "impact", "weight": float(self.config.weight_impact)},
                    {"name": "cost", "weight": float(self.config.weight_cost)},
                    {"name": "risk", "weight": float(self.config.weight_risk)},
                ]
            try:
                options_payload = [
                    (o.model_dump() if hasattr(o, "model_dump") else {
                        "id": getattr(o, "id", None),
                        "title": getattr(o, "title", None),
                        "description": getattr(o, "description", None),
                        "expected_impact": getattr(o, "expected_impact", None),
                        "cost": getattr(o, "cost", None),
                        "risk": getattr(o, "risk", None),
                        "rationale": getattr(o, "rationale", None),
                    })
                    for o in (ranked or [])
                ]
            except Exception:
                options_payload = []
            try:
                recommendation_payload = recommendation.model_dump() if (recommendation is not None and hasattr(recommendation, "model_dump")) else (recommendation if isinstance(recommendation, dict) else None)
            except Exception:
                recommendation_payload = None
            matrix_payload = {"criteria": criteria_payload, "options": options_payload}

            # Build framing_context for Principal-driven transparency (per PRD guardrails)
            framing_context_payload = None
            try:
                decision_style = None
                pc = getattr(request, "principal_context", None)
                if pc:
                    if isinstance(pc, dict):
                        decision_style = pc.get("decision_style")
                    else:
                        decision_style = getattr(pc, "decision_style", None)
                
                if decision_style or consulting_personas:
                    framing_context_payload = {
                        "decision_style": decision_style or "default",
                        "personas_used": [p.id for p in consulting_personas] if consulting_personas else ["mckinsey", "bcg", "bain"],
                        "presentation_note": f"Solutions presented per your {decision_style or 'default'} decision style preferences.",
                        "disclaimer": "Consulting perspectives are analytical frameworks, not colleague opinions.",
                        "alternative_views_available": ["analytical", "visionary", "pragmatic"],
                    }
            except Exception:
                pass

            # Single HITL event required per PRD
            return SolutionFinderResponse.success(
                request_id=req_id,
                options_ranked=options_payload,
                tradeoff_matrix=matrix_payload,
                recommendation=recommendation_payload,
                recommendation_rationale=rationale,
                human_action_required=True,
                human_action_type="approval",
                human_action_context={
                    "summary": "Review ranked options and approve or select an alternative.",
                },
                audit_log=(
                    [{"event": "ranked_options", "count": len(options_payload)}]
                    + audit_log
                    + _token_usage_event(_token_ledger)
                ),
                # Enhanced Decision Briefing Fields
                problem_reframe=problem_reframe,
                unresolved_tensions=unresolved_tensions_list,
                blind_spots=blind_spots_list,
                next_steps=next_steps_list,
                cross_review=cross_review,
                # Multi-call Stage 1 per-persona hypotheses
                stage_1_hypotheses=stage_1_hypotheses_final if stage_1_hypotheses_final else None,
                # Principal-Driven Framing Context
                framing_context=framing_context_payload,
                # Market Intelligence enrichment (None when MA agent unavailable or skipped)
                market_intelligence=ma_response,
                # Phase 15 Stage B
                decision_ask=decision_ask,
                immediate_actions=immediate_actions_list,
            )
        except Exception as e:
            return SolutionFinderResponse.error(request_id=req_id, error_message=str(e))

    async def evaluate_options(self, request: SolutionFinderRequest) -> SolutionFinderResponse:
        req_id = request.request_id
        try:
            options = request.extra.get("options", []) if request.extra else []
            # Convert dicts to model instances if necessary
            normalized: List[SolutionOption] = []
            for o in options:
                if isinstance(o, SolutionOption):
                    normalized.append(o)
                elif isinstance(o, dict):
                    normalized.append(SolutionOption(**o))
            criteria = request.evaluation_criteria or [
                TradeOffCriterion(name="impact", weight=self.config.weight_impact),
                TradeOffCriterion(name="cost", weight=self.config.weight_cost),
                TradeOffCriterion(name="risk", weight=self.config.weight_risk),
            ]
            ranked = self._rank_options(normalized, criteria)
            matrix = TradeOffMatrix(criteria=criteria, options=ranked)
            recommendation = ranked[0] if ranked else None
            return SolutionFinderResponse.success(
                request_id=req_id,
                options_ranked=ranked,
                tradeoff_matrix=matrix,
                recommendation=recommendation,
                recommendation_rationale="Heuristic ranking applied.",
                human_action_required=True,
                human_action_type="approval",
                human_action_context={"summary": "Approve or override the recommended option."},
            )
        except Exception as e:
            return SolutionFinderResponse.error(request_id=req_id, error_message=str(e))

    def _get_industry_from_context(self, request: SolutionFinderRequest) -> Optional[str]:
        """
        Extract an industry label from the request context.

        Priority:
          1. ``request.business_context`` dict/object with an ``industry`` key.
          2. KPI name keyword matching (lubricant → 'lubricants', bike/bicycle → 'bicycles').
          3. Returns None so the MA agent uses its own default.
        """
        try:
            bc = getattr(request, "business_context", None)
            if bc:
                if isinstance(bc, dict):
                    industry = bc.get("industry")
                else:
                    industry = getattr(bc, "industry", None)
                if isinstance(industry, str) and industry.strip():
                    return industry.strip()
        except Exception:
            pass

        # Keyword fallback from KPI name
        try:
            kpi_name = ""
            da_ctx = request.deep_analysis_output or {}
            da_summary = _extract_deep_analysis_summary(da_ctx)
            kpi_name = (da_summary.get("kpi_name") or "").lower()
            if not kpi_name:
                ps = (getattr(request, "problem_statement", None) or "").lower()
                kpi_name = ps
            if "lubricant" in kpi_name:
                return "lubricants"
            if "bike" in kpi_name or "bicycle" in kpi_name:
                return "bicycles"
        except Exception:
            pass

        return None

    def _rank_options(self, options: List[SolutionOption], criteria: List[TradeOffCriterion]) -> List[SolutionOption]:
        # Simple weighted score: impact positive, cost and risk negative
        def score(o: SolutionOption) -> float:
            imp = o.expected_impact or 0.0
            cost = o.cost or 0.0
            risk = o.risk or 0.0
            w = {c.name: c.weight for c in criteria}
            return (w.get("impact", 0.0) * imp) - (w.get("cost", 0.0) * cost) - (w.get("risk", 0.0) * risk)

        return sorted(options, key=score, reverse=True)


async def create_solution_finder_agent(config: Dict[str, Any] = None) -> A9_Solution_Finder_Agent:
    return await A9_Solution_Finder_Agent.create(config or {})
