"""
# doc-sync-skip
A9 Deep Analysis Agent (MVP skeleton)
- Implements DeepAnalysisProtocol
- Uses Data Product Agent for deterministic grouped/timeframe comparisons
- Uses A9_LLM_Service for narrative (optional)
"""
# doc-sync-skip
from __future__ import annotations

import logging
import uuid
import os
import re
from typing import Dict, Any, Optional, List, Tuple
import yaml

from src.agents.shared.a9_agent_base_model import A9AgentBaseModel
from src.agents.agent_config_models import A9_Deep_Analysis_Agent_Config
from src.agents.protocols.deep_analysis_protocol import DeepAnalysisProtocol
from src.agents.models.deep_analysis_models import (
    DimensionTotal,
    DeepAnalysisRequest,
    DeepAnalysisPlan,
    DeepAnalysisResponse,
    KTIsIsNot,
    ChangePoint,
    BenchmarkSegment,
    ProblemRefinementInput,
    ProblemRefinementResult,
    RefinementExclusion,
    ExtractedRefinements,
    ConstraintItem,
    constraint_id,
    FramingAlternative,
    PriorFrameRecord,
    FramingPrompt,
    FramingDecision,
    FramingRecord,
)
from src.agents.models.data_governance_models import KPIDataProductMappingRequest
from src.agents.utils.data_quality_filter import DataQualityFilter, filter_anomalies
from src.database.time_filter import TimeFilter


logger = logging.getLogger(__name__)

# Key under which a GROUP BY ROLLUP grand-total row is stashed in a grouped map.
# The NUL byte guarantees it cannot collide with a real dimension value, so a
# segment genuinely named "None" or "Total" is never mistaken for the total.
_ROLLUP_TOTAL_KEY = "\x00__rollup_total__"

_MIXED_MODE_PURITY_THRESHOLD = 0.80  # fraction of top-N items that must be one direction to be "pure"


def _classify_benchmark_segments(is_not_items):
    """Classify IS NOT items into control_group vs internal_benchmark (top quartile by absolute delta)."""
    if not is_not_items:
        return []
    deltas = [abs(item.get("delta", 0)) for item in is_not_items]
    threshold = sorted(deltas, reverse=True)[max(0, len(deltas) // 4 - 1)] if deltas else 0

    total_variance = sum(deltas) or 1.0  # avoid division by zero

    import statistics
    mean_delta = statistics.mean(deltas) if deltas else 0.0
    std_delta = statistics.stdev(deltas) if len(deltas) >= 2 else 0.0
    outlier_cutoff = mean_delta + 2 * std_delta

    segments = []
    for item in is_not_items:
        abs_delta = abs(item.get("delta", 0))
        delta = item.get("delta", 0)
        current = float(item.get("current", 0) or 0.0)
        previous = float(item.get("previous", 0) or 0.0)
        delta_pct = ((current - previous) / previous * 100) if previous else None
        effect_size = abs_delta / total_variance
        is_outlier = abs_delta > outlier_cutoff and std_delta > 0
        # Outliers cannot be reliable replication targets — downgrade to control_group
        is_bmark = abs_delta >= threshold and threshold > 0 and not is_outlier
        rep_potential = round(min(1.0, effect_size * 2), 3) if is_bmark else None
        segments.append(BenchmarkSegment(
            dimension=item.get("dimension", ""),
            key=str(item.get("key", "")),
            current_value=current,
            previous_value=previous,
            delta=float(delta),
            delta_pct=delta_pct,
            benchmark_type="internal_benchmark" if is_bmark else "control_group",
            replication_potential=rep_potential,
            effect_size_pct=round(effect_size, 4),
            is_outlier=is_outlier,
        ))
    return segments


# ============================================================================
# Problem Refinement Chat Constants (MBB-Style Principal Engagement)
# ============================================================================

REFINEMENT_TOPIC_SEQUENCE = [
    "hypothesis_validation",  # Validate/invalidate KT findings with principal knowledge
    "scope_boundaries",       # Confirm segments, time periods to include/exclude
    "external_context",       # Capture factors not visible in data
    "constraints",            # Identify levers that are off-limits
    "success_criteria",       # Define what "solved" looks like
]

TOPIC_OBJECTIVES = {
    "hypothesis_validation": "Confirm which KT drivers are real issues vs. known/expected factors",
    "scope_boundaries": "Define what segments, time periods, or dimensions to include or exclude",
    "external_context": "Capture external factors not visible in the data (market changes, supplier issues, etc.)",
    "constraints": "Identify levers that are off-limits or actions that cannot be taken",
    "success_criteria": "Define what 'solved' looks like and how success will be measured",
    "replication_potential": "Assess whether internal benchmark segments can serve as replication templates and what structural barriers exist",
    # Stage I B-1 — problem-shape-routed topics. Each is asked only when the
    # problem's structure makes it the question worth spending a turn on.
    "tradeoff_tolerance": "Establish which KPI the principal is willing to give ground on when two are in tension, and by how much",
    "segment_specific_causation": "Probe why THIS segment specifically, when the variance is concentrated in one place the data has already identified",
    "comparison_baseline": "Establish a contrast the data cannot supply — what this should be compared against when no IS-NOT control group exists",
}

# Topics that must survive sequence truncation. hypothesis_validation anchors the
# interview; constraints and success_criteria are what Solution Finder consumes.
# Losing `constraints` in particular means SF runs with an empty bound set.
PROTECTED_TOPICS = {"hypothesis_validation", "constraints", "success_criteria"}

# Upper bound on how many topics a routed sequence may contain. Matches the
# pre-existing maximum (5 base + replication_potential).
MAX_TOPICS_IN_SEQUENCE = 6

# Turns needed per topic before the tail of the sequence starts getting starved.
# Observed live: topics complete either on a content heuristic (1-2 turns) or on
# MAX_TURNS_PER_TOPIC (3), so 2 is the realistic average.
TURNS_PER_TOPIC_BUDGET = 2


# Last-resort question when a topic has no authored default. Named rather than
# inlined so the three sites that need it cannot drift apart.
_GENERIC_QUESTION = (
    "Please share any additional context that would help refine this analysis.",
    ["Continue", "Skip this topic", "Proceed to solutions"],
)


def effective_turn_budget(topic_sequence: List[str]) -> int:
    """Total turns allowed, scaled to the routed sequence length.

    `PROTECTED_TOPICS` keeps `constraints` and `success_criteria` from being
    TRUNCATED out of the sequence — it does nothing about them never being
    REACHED. With a fixed MAX_TOTAL_TURNS of 10 and a 6-topic sequence at ~2
    turns each, the interview needs ~12 turns and ends two topics short, so
    Solution Finder receives no constraints. That is the same starvation the cap
    was meant to prevent, arriving by a different route.

    Found by a live run (2026-08-11): a `distributed/no-control/market-conflict`
    problem routed to 6 topics and had reached topic 2 of 6 by turn 5.

    MAX_TOTAL_TURNS remains the floor, so the default 5-topic sequence is
    completely unchanged.
    """
    return max(MAX_TOTAL_TURNS, TURNS_PER_TOPIC_BUDGET * len(topic_sequence or []))


# ============================================================================
# Problem Framing Gate Constants (Phase 19)
# ============================================================================

# Human-facing copy for the provenance ladder, shown at the framing gate.
# Deliberately NEW TEXT, not a9_solution_finder_agent.py's _PROVENANCE_CAVEAT
# — that dict is an LLM INSTRUCTION ("respect the caveat", addressed to a
# model that will paraphrase it into a prompt); this is addressed to the
# person deciding the frame and needs to read correctly on its own, with no
# model in between to soften or contextualize it.
_FRAMING_PROVENANCE_CAVEAT = {
    "template": "An unconfirmed industry pattern, not yet checked against this client's own data.",
    "confirmed": "Confirmed by this client directly.",
    "hitl_proposed": "Surfaced from how the system has been used here, not yet confirmed by anyone.",
    "va_validated": "Outcome-tested by Value Assurance on a solution that used this relationship — the strongest evidence available, though still 'consistent with', never 'proved'.",
}

STYLE_GUIDANCE = {
    "analytical": """McKinsey-style: hypothesis-driven, MECE decomposition, statistical confidence.
Use precise, quantitative language. Focus on falsification criteria.""",
    "visionary": """BCG-style: strategic framing, portfolio positioning, competitive dynamics.
Use narrative, forward-looking language. Focus on long-term value creation.""",
    "pragmatic": """Bain-style: action-oriented, quick wins, ownership, timelines.
Use direct language. Focus on implementation feasibility and 90-day impact.""",
}

# Conversation control constants
MAX_TURNS_PER_TOPIC = 3
MAX_TOTAL_TURNS = 10
MIN_TOPICS_REQUIRED = 3

# Council routing rules
COUNCIL_ROUTING = {
    "strategic": {"roles": ["CEO"], "styles": ["visionary"], "keywords": ["market share", "portfolio", "competitive"]},
    "operational": {"roles": ["COO"], "styles": ["pragmatic"], "keywords": ["process", "efficiency", "production"]},
    "financial": {"roles": ["CFO", "Finance Manager"], "styles": ["analytical"], "keywords": ["margin", "cost", "revenue", "profitability"]},
    "technical": {"roles": [], "styles": [], "keywords": ["data", "system", "integration", "IT"]},
    "innovation": {"roles": [], "styles": [], "keywords": ["new", "disrupt", "creative", "unknown"]},
}


class A9_Deep_Analysis_Agent(DeepAnalysisProtocol):
    """Deep Analysis Agent MVP implementation (skeleton)."""

    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> "A9_Deep_Analysis_Agent":
        inst = cls(config or {})
        await inst.connect()
        return inst

    def __init__(self, config: Dict[str, Any]):
        self.name = "A9_Deep_Analysis_Agent"
        self.version = "0.1.0"
        self.config = A9_Deep_Analysis_Agent_Config(**(config or {}))
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_product_agent = None
        self.data_governance_agent = None  # Wired post-bootstrap by runtime._wire_governance_dependencies()
        self.llm_service_agent = None
        # Optional: orchestrator not stored; agents are resolved in connect()

    # --- Helpers -----------------------------------------------------------
    _CONTRACTS_DIR = "src/registry_references/data_product_registry/data_products"
    _FALLBACK_CONTRACT = "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"

    def _contract_path(self) -> str:
        """Return the default (bicycle FI) contract path. Use _contract_path_for_kpi() when a KPI name is known."""
        canonical = self._FALLBACK_CONTRACT
        if os.path.exists(canonical):
            return canonical
        here = os.path.dirname(__file__)
        proj_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
        abs_canonical = os.path.join(proj_root, canonical)
        return abs_canonical if os.path.exists(abs_canonical) else canonical

    def _lookup_kpi_scoped(self, kpi_ref: Optional[str], client_id: Optional[str]):
        """
        Resolve a KPI by id OR display name with strict tenant isolation.

        Multiple tenants legitimately share KPI ids under the composite PK
        (client_id, id) — e.g. gross_margin_pct exists for lubricants (BigQuery),
        apex_lubricants (Snowflake), and hess (SQL Server). When client_id is known,
        only that tenant's record may be returned; a same-id record from another
        tenant is NEVER an acceptable fallback (it carries the wrong data_product_id
        and therefore the wrong backend, SQL dialect, and dimensions).

        Returns None when client_id is provided and no scoped match exists.
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
                    self.logger.error(
                        f"KPI '{ref}' not found for client '{client_id}' — "
                        f"{len(candidates)} same-id record(s) exist for other tenants; "
                        f"refusing cross-tenant fallback"
                    )
                return None
            return candidates[0] if candidates else None
        except Exception as e:
            self.logger.debug(f"_lookup_kpi_scoped('{kpi_ref}', client_id={client_id}) failed: {e}")
            return None

    def _contract_path_for_kpi(self, kpi_name: str = None, client_id: str = None) -> str:
        """
        Resolve the data product contract path for a given KPI id or name.
        Looks up the KPI's data_product_id in the Supabase registry (tenant-scoped)
        and scans the contracts directory for a matching YAML.

        Fallback rules:
        - client_id known but KPI unresolvable → "" (no contract; downstream dim
          fallbacks take over). NEVER the bicycle FI contract — that leaks another
          client's dimension names into the plan.
        - no client_id (legacy single-tenant path) → bicycle FI contract default.
        """
        try:
            if not kpi_name:
                return self._contract_path()
            kpi_def = self._lookup_kpi_scoped(kpi_name, client_id)
            if kpi_def is None and client_id:
                return ""
            data_product_id = getattr(kpi_def, "data_product_id", None) if kpi_def else None

            if data_product_id:
                # Scan contracts directory for a YAML whose metadata.id matches
                import glob as _glob
                contracts_dir = self._CONTRACTS_DIR
                if not os.path.isabs(contracts_dir) and not os.path.exists(contracts_dir):
                    here = os.path.dirname(__file__)
                    contracts_dir = os.path.abspath(os.path.join(here, "..", "..", "..", contracts_dir))
                for fpath in _glob.glob(os.path.join(contracts_dir, "*.yaml")):
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            doc = yaml.safe_load(f) or {}
                        if (doc.get("metadata") or {}).get("id") == data_product_id:
                            return fpath
                    except Exception:
                        continue
                # No contract YAML found for this data product — return empty string so
                # _dims_from_contract returns [] and the KPI registry fallback takes over.
                return ""
        except Exception as e:
            self.logger.debug(f"_contract_path_for_kpi error: {e}")
        return self._contract_path()

    def _dims_from_contract(self, limit: int, kpi_name: str = None, client_id: str = None) -> List[str]:
        """Candidate dimensions in the order the data product contract declares them.

        The contract's `dimension_semantics` order is the client's own statement of
        what matters for this data product, and it is honoured verbatim.

        Until Aug 2026 this re-ranked against a hardcoded `preferred` literal that
        merged bicycle and lubricants field names — so every tenant was investigated
        in an order nobody had chosen for them, and the literal silently overrode
        each client's declared order. For lubricants it forced profit-centre first
        against a contract that declares products first. Deleted; see
        DEVELOPMENT_PLAN.md -> Phase 15 -> Stage I (Part A).

        A client whose contract lists dimensions in ETL or alphabetical order now
        gets that order. That is the correct failure mode: it surfaces as a
        contract-authoring problem instead of being masked by a literal that
        happened to name a few good dimensions for two clients.
        """
        dims: List[str] = []
        try:
            cpath = self._contract_path_for_kpi(kpi_name, client_id=client_id)
            if not os.path.exists(cpath):
                return []
            with open(cpath, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            views = (doc or {}).get("views", [])
            # Use the first view found (contract may have only one view)
            target = None
            for v in views:
                if isinstance(v, dict) and v.get("llm_profile"):
                    target = v
                    break
            if not isinstance(target, dict):
                return []
            llm_profile = target.get("llm_profile", {}) or {}
            all_dims = llm_profile.get("dimension_semantics", []) or []
            def _keep(lbl: str) -> bool:
                s = str(lbl or "").lower()
                ban = ["flag", "hierarchy", "_id", "transaction_date", "transaction date",
                       "version", "fiscal ytd", "fiscal qtd", "fiscal mtd"]
                return bool(lbl) and not any(t in s for t in ban)
            kept = [d for d in all_dims if _keep(str(d))]
            # Declared order, de-duplicated. No re-ranking: see the docstring.
            out: List[str] = list(dict.fromkeys(kept))
            if isinstance(limit, int) and limit > 0:
                out = out[:limit]
            dims = out
        except Exception as e:
            self.logger.debug(f"_dims_from_contract error: {e}")
        return dims

    def _prev_timeframe(self, timeframe: Optional[str]) -> Optional[str]:
        return TimeFilter.previous_period_name(timeframe)

    # ── Phase 11I-D: alert-type-aware comparator selection ──────────────────────
    _TIME_BASED_ALERT_TYPES = {"threshold_breach"}

    @staticmethod
    def _kpi_has_budget_data(kpi_def: Any) -> bool:
        """True when the KPI can be diagnosed against a Budget/Plan basis.

        Checks `plan_version_value` (the field SA/DPA use to derive plan SQL) first,
        then any threshold whose comparison_type is 'budget' or 'plan_variance'. Note
        SA's plan_variance alert uses ComparisonType.PLAN_VARIANCE — a different enum
        member than the narrow 'budget' scan _pick_threshold_spec does — so both must
        be checked here or a plan_variance-only KPI would look budget-less.
        """
        if getattr(kpi_def, "plan_version_value", None):
            return True
        for t in (getattr(kpi_def, "thresholds", None) or []):
            ct = getattr(t, "comparison_type", None) or (t.get("comparison_type") if isinstance(t, dict) else None)
            ct_str = str(getattr(ct, "value", ct)).lower() if ct is not None else ""
            if ct_str in ("budget", "plan_variance"):
                return True
        return False

    @staticmethod
    def _derive_budget_sql(sql_query: Optional[str], plan_version_value: Optional[str]) -> Optional[str]:
        """Substitute the version filter in the actuals SQL to produce budget SQL.

        Mirrors SA's `_derive_plan_sql` exactly (same regex, same quoting styles).
        The DPA's `generate_sql_for_kpi` silently DROPS its `filters` argument, so the
        budget-dimensional pass cannot get a Budget query by passing filters={"Version":
        "Budget"} — both passes would produce the actuals SQL and every segment delta
        would be 0. Instead we pre-substitute the version in the stored sql_query and
        feed the DPA a proxy whose sql_query is already the budget variant. Handles
        double-quoted ("version"), bracket-quoted ([version]), backtick and bare styles.
        Returns None when no version='Actual' filter is present.
        """
        import re as _re
        if not sql_query or not plan_version_value:
            return None
        pattern = r'((?:"version"|\[version\]|`version`|version))\s*=\s*\'Actual\''
        replacement = r'\1' + f" = '{plan_version_value}'"
        result, count = _re.subn(pattern, replacement, sql_query, flags=_re.IGNORECASE)
        if count == 0:
            return None
        return result

    def _budget_variant_kpi(self, kpi_def: Any) -> Optional[Any]:
        """Clone `kpi_def` with its sql_query rewritten to the Budget version, or None
        if no budget SQL can be derived (no plan_version_value / no version filter)."""
        pvv = getattr(kpi_def, "plan_version_value", None) or "Budget"
        budget_sql = self._derive_budget_sql(
            getattr(kpi_def, "sql_query", None) or getattr(kpi_def, "calculation", None),
            pvv,
        )
        if not budget_sql:
            return None

        class _BudgetKpiProxy:
            """KPI-like object carrying the budget-substituted sql_query."""
            def __init__(self, base_kpi: Any, sql_override: str) -> None:
                self.sql_query = sql_override
                self.calculation = sql_override
                self.name = getattr(base_kpi, "name", "budget")
                self.id = getattr(base_kpi, "id", "budget")
                self.metadata = getattr(base_kpi, "metadata", {})
                self.unit = getattr(base_kpi, "unit", None)
                self.data_product_id = getattr(base_kpi, "data_product_id", None)
                self.plan_version_value = getattr(base_kpi, "plan_version_value", None)

        return _BudgetKpiProxy(kpi_def, budget_sql)

    def _resolve_da_comparator(self, plan: Any, kpi_def: Any, registry_comparator: str) -> str:
        """Choose the Is/Is-Not comparison basis: 'previous' (vs prior period) or 'budget'.

        Precedence: explicit drill override > the dominant alert_type's basis >
        today's registry-preference default (`registry_comparator`, unchanged for
        non-situation-originated calls).
        """
        override = getattr(plan, "comparator_override", None)
        if override in ("previous", "budget"):
            return override

        alert_type = getattr(plan, "alert_type", None)
        if alert_type == "plan_variance":
            if self._kpi_has_budget_data(kpi_def):
                return "budget"
            self.logger.warning(
                "[DA] alert_type=plan_variance but KPI '%s' has no resolvable budget data; "
                "falling back to registry comparator '%s'",
                getattr(kpi_def, "id", getattr(plan, "kpi_name", "?")), registry_comparator,
            )
        elif alert_type in self._TIME_BASED_ALERT_TYPES:
            return "previous"

        return registry_comparator

    def _is_matrix_eligible(self, plan: Any, kpi_def: Any, comparator_main: str) -> bool:
        """True when a KPI breached on BOTH cross-sectional bases (previous-period AND
        plan-variance) and budget data is available — so the two can share one Is/Is-Not
        table as a segment × basis matrix. Temporal/relational patterns (projected_breach,
        acceleration, compound) are NOT matrix columns; they stay as narrated annotations.
        """
        merged = set(getattr(plan, "merged_alert_types", None) or [])
        if not ({"threshold_breach", "plan_variance"} <= merged):
            return False
        if comparator_main not in ("previous", "budget"):
            return False
        return self._kpi_has_budget_data(kpi_def)

    @staticmethod
    def _classify_basis_agreement(
        primary_delta: Any,
        secondary_delta: Any,
        trend_positive: bool,
        primary_side: str,
    ) -> Optional[str]:
        """Per-segment cross-basis tier for the matrix. Returns None when the segment
        has no secondary delta (not cross-checked).

        `trend_positive`: True when a higher value is good (revenue); False for costs.
        `primary_side`: 'problem' (row is in where_is) or 'healthy' (where_is_not).
          - problem + secondary adverse  -> 'confirmed'      (bad on both — real problem)
          - problem + secondary favorable -> 'basis_specific' (bad on one basis only — likely artifact)
          - healthy + secondary adverse  -> 'secondary_only'  (missed by the primary basis)
          - healthy + secondary favorable -> 'healthy'        (true control)
        """
        if secondary_delta is None:
            return None
        try:
            sd = float(secondary_delta)
        except (TypeError, ValueError):
            return None
        sec_adverse = (sd < 0) if trend_positive else (sd > 0)
        if primary_side == "problem":
            return "confirmed" if sec_adverse else "basis_specific"
        return "secondary_only" if sec_adverse else "healthy"

    @staticmethod
    def _build_secondary_alert_appendix(
        primary_alert_type: Optional[str],
        merged_alert_types: Optional[List[str]],
        facts: Optional[Dict[str, Any]],
        max_lines: int = 3,
    ) -> str:
        """Bounded, deterministic narration of the alert patterns that also fired for
        this KPI beyond the one being diagnosed. Facts only (SA's scalars) — never a
        second dimensional analysis, never LLM-reasoned. '' when nothing to add.

        This is what keeps the compound case comprehensible: the primary basis gets a
        full Is/Is-Not diagnosis; every other pattern gets a single flag line + a pointer
        to the on-demand drill, rather than a competing narrative.
        """
        if not merged_alert_types or len(merged_alert_types) < 2:
            return ""
        facts = facts or {}
        lines: List[str] = []
        for at in merged_alert_types:
            if at == primary_alert_type:
                continue
            if at == "plan_variance":
                pv = facts.get("plan_value")
                extra = f" (Budget baseline ≈ {pv:,.0f})" if isinstance(pv, (int, float)) else ""
                lines.append(
                    f"also flagged for plan variance vs its Budget baseline{extra} "
                    f"— use 'Diagnose vs Budget' for the dimensional breakdown"
                )
            elif at == "threshold_breach":
                lines.append(
                    "also breaching its prior-period threshold "
                    "— use 'Diagnose vs prior period' for that basis"
                )
            elif at == "projected_breach":
                pu = facts.get("periods_until_breach")
                when = f" in ~{pu} period(s)" if isinstance(pu, int) else ""
                lines.append(f"on a projected-breach trajectory{when}")
            elif at == "acceleration":
                sig = facts.get("acceleration_signal")
                mag = f" ({sig:.1f}× baseline volatility)" if isinstance(sig, (int, float)) else ""
                lines.append(f"showing accelerating deterioration{mag}")
            if len(lines) >= max_lines:
                break
        if not lines:
            return ""
        return " Additional signals for this KPI: " + "; ".join(lines) + "."

    def _build_group_compare_steps(self, dimensions: List[str], timeframe: Optional[str], filters: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build grouped comparison step skeletons for the provided dimensions.
        Keeps the structure consistent with planning in plan_deep_analysis().
        """
        steps: List[Dict[str, Any]] = []
        try:
            try:
                limit = max(0, int(getattr(self.config, "max_dimensions", 5) or 5))
            except Exception:
                limit = 5
            for dim in (dimensions[:limit] if dimensions else []):
                steps.append({
                    "type": "group_compare",
                    "dimension": dim,
                    "timeframe": timeframe,
                    "filters": filters or {},
                    "comparison": "current_vs_previous",
                })
        except Exception:
            # Non-fatal; fallback to empty steps
            return []
        return steps

    def _trend_positive(self, kpi_name: str, kpi_def: Any = None) -> bool:
        """
        Determine if higher values are better for this KPI.
        Uses inverse_logic from KPI registry thresholds if available.
        
        - inverse_logic=False (default): higher is better (revenue) -> trend_positive=True
        - inverse_logic=True: lower is better (cost/expense) -> trend_positive=False
        """
        # Try to get inverse_logic from KPI definition thresholds
        if kpi_def is not None:
            try:
                thresholds = getattr(kpi_def, "thresholds", None)
                if isinstance(thresholds, list) and thresholds:
                    # Use the first threshold's inverse_logic as the default
                    for t in thresholds:
                        inv = None
                        if hasattr(t, "inverse_logic"):
                            inv = getattr(t, "inverse_logic", None)
                        elif isinstance(t, dict):
                            inv = t.get("inverse_logic")
                        if inv is not None:
                            # inverse_logic=True means lower is better, so trend_positive=False
                            return not bool(inv)
            except Exception:
                pass
        
        # Fallback to name-based heuristic
        s = (kpi_name or "").lower()
        return not any(w in s for w in ("expense", "cost", "deduction", "cogs"))

    def _infer_analysis_mode(
        self,
        problem_items: list,
        healthy_items: list,
        caller_hint: str = "problem",
        top_n: int = 5,
    ) -> str:
        """Determine effective analysis mode from segment variance distribution.

        Returns "problem", "opportunity", or "mixed".
        - If ≥80% of top-N items are problem-direction  → "problem"
        - If ≥80% of top-N items are healthy-direction  → "opportunity"
        - Otherwise                                      → "mixed"
        - Falls back to caller_hint when there are no items.
        """
        n_prob = min(len(problem_items), top_n)
        n_heal = min(len(healthy_items), top_n)
        total = n_prob + n_heal
        if total == 0:
            return caller_hint
        # When caller signals an opportunity but no healthy segments are found, this is
        # typically caused by missing per-dimension comparison data (delta = current − 0
        # for all segments). Trust the caller hint rather than silently override with
        # "problem" on incomplete dimensional evidence.
        if caller_hint == "opportunity" and n_heal == 0:
            return "opportunity"
        if n_prob / total >= _MIXED_MODE_PURITY_THRESHOLD:
            return "problem"
        if n_heal / total >= _MIXED_MODE_PURITY_THRESHOLD:
            return "opportunity"
        return "mixed"

    def _select_variance_items(
        self,
        diffs: List[tuple],  # List of (key, current, previous, delta)
        threshold_pct: float = 0.05,  # 5% variance threshold
        min_items: int = 3,
        max_items: int = 10,
        trend_positive: bool = True,  # True if higher is better (revenue), False if lower is better (cost)
    ) -> tuple:
        """
        Hybrid Threshold + Adaptive N approach for selecting variance items.
        
        Returns (where_is_items, where_is_not_items) where:
        - where_is_items: Items with NEGATIVE variance (problem areas - underperforming)
        - where_is_not_items: Items with POSITIVE variance (healthy areas - outperforming)
        
        For trend_positive=True (revenue KPIs): negative delta = problem, positive delta = healthy
        For trend_positive=False (cost KPIs): positive delta = problem, negative delta = healthy
        
        Algorithm:
        1. Separate items by variance direction (problem vs healthy)
        2. Apply threshold to filter significant variances
        3. If threshold returns < min_items, fall back to Top N
        4. Cap at max_items to avoid overwhelming the LLM
        """
        if not diffs:
            return [], []
        
        # Separate by variance direction
        problem_items = []  # Underperforming
        healthy_items = []  # Outperforming

        for item in diffs:
            key, current, previous, delta = item
            # Skip items with no comparison baseline — previous=0/None means no prior-period data.
            # Keeping them would surface artifacts (e.g. Gross Margin 100% for products with no COGS
            # in the prior period) rather than genuine variance signals.
            if not previous:
                continue
            # Calculate percent variance (handle division by zero)
            pct_variance = abs(delta / previous)

            item_with_pct = (key, current, previous, delta, pct_variance)
            
            # Determine if this is a problem or healthy item based on delta direction
            if trend_positive:
                # For revenue: negative delta = problem, positive delta = healthy
                if delta < 0:
                    problem_items.append(item_with_pct)
                else:
                    healthy_items.append(item_with_pct)
            else:
                # For cost: positive delta = problem (cost increased), negative delta = healthy
                if delta > 0:
                    problem_items.append(item_with_pct)
                else:
                    healthy_items.append(item_with_pct)
        
        # Sort problem items by absolute delta (impact) descending
        problem_items.sort(key=lambda t: abs(t[3]), reverse=True)
        # Sort healthy items by delta (best performers first)
        if trend_positive:
            healthy_items.sort(key=lambda t: t[3], reverse=True)  # Highest positive first
        else:
            healthy_items.sort(key=lambda t: t[3])  # Most negative (cost reduction) first
        
        # Apply threshold filter to problem items
        significant_problems = [item for item in problem_items if item[4] >= threshold_pct]
        
        # If threshold didn't find enough problems, use all problem items
        if len(significant_problems) < min_items and problem_items:
            where_is_items = [(k, c, p, d) for k, c, p, d, _ in problem_items[:max_items]]
        else:
            where_is_items = [(k, c, p, d) for k, c, p, d, _ in significant_problems[:max_items]]
        
        # For healthy items, take top performers
        where_is_not_items = [(k, c, p, d) for k, c, p, d, _ in healthy_items[:max_items]]
        
        return where_is_items, where_is_not_items

    async def connect(self, orchestrator=None) -> bool:
        try:
            if orchestrator is not None:
                try:
                    self.data_product_agent = await orchestrator.get_agent("A9_Data_Product_Agent")
                except Exception:
                    self.data_product_agent = None
                # DGA wired post-bootstrap by runtime._wire_governance_dependencies()
                self.data_governance_agent = None
                try:
                    self.llm_service_agent = await orchestrator.get_agent("A9_LLM_Service_Agent")
                except Exception:
                    self.llm_service_agent = None
            self.logger.info("Deep Analysis Agent connected")
            return True
        except Exception as e:
            self.logger.warning(f"Deep Analysis Agent connect error: {e}")
            return False

    async def enumerate_dimensions(self, request: DeepAnalysisRequest) -> DeepAnalysisResponse:
        req_id = request.request_id
        try:
            # MVP: neutral placeholder enumeration. In production, consult glossary/registry.
            dimensions: List[str] = []
            return DeepAnalysisResponse.success(
                request_id=req_id,
                plan=DeepAnalysisPlan(
                    kpi_name=request.kpi_name,
                    timeframe=request.timeframe,
                    filters=request.filters,
                    dimensions=dimensions,
                    steps=[],
                    notes="Enumerated dimensions (placeholder)."
                ),
                dimensions_suggested=dimensions,
                percent_growth_enabled=bool(request.enable_percent_growth),
                timeframe_mapping=None,
                samples=None,
            )
        except Exception as e:
            return DeepAnalysisResponse.error(request_id=req_id, error_message=str(e))

    async def plan_deep_analysis(self, request: DeepAnalysisRequest) -> DeepAnalysisResponse:
        req_id = request.request_id
        try:
            # Prefer dimensions from Data Product Contract YAML
            try:
                # MVP Optimization: Scan more dimensions (15) to find true top drivers, even if we only report 5
                cfg_limit = int(getattr(request, "target_count", self.config.max_dimensions) or self.config.max_dimensions)
                target_count = max(cfg_limit, 15)
            except Exception:
                target_count = 15
            dimensions: List[str] = self._dims_from_contract(limit=target_count, kpi_name=request.kpi_name, client_id=getattr(request, "client_id", None))
            # Which declaration actually decided the investigation. Recorded on the
            # plan so a run can be audited without re-deriving the resolution order.
            dimension_rank_source: str = "contract_semantics" if dimensions else "none"
            try:
                self.logger.info(f"plan_deep_analysis: kpi={request.kpi_name} timeframe={request.timeframe} dims_from_contract={len(dimensions)}")
            except Exception:
                pass
            # Priority 2: KPI registry — registered _DIMS are more authoritative than DGA-inferred view columns
            if not dimensions and request.kpi_name:
                try:
                    _req_client = getattr(request, "client_id", None)
                    # Tenant-scoped id-or-name resolution (matches by KPI id too — the
                    # workflow passes scope.kpi_id in the kpi_name field)
                    k = self._lookup_kpi_scoped(request.kpi_name, _req_client)
                    if k is not None:
                        kpi_dims = getattr(k, "dimensions", None) or []
                        dimensions = [
                            (d.get("field") or d.get("name") if isinstance(d, dict) else
                             getattr(d, "field", None) or getattr(d, "name", None) or str(d))
                            for d in kpi_dims
                            if d
                        ]
                        dimensions = [d for d in dimensions if d]
                        if dimensions:
                            dimension_rank_source = "kpi_registry"
                            self.logger.info(f"plan_deep_analysis: using {len(dimensions)} dims from KPI registry for '{request.kpi_name}' (client={_req_client})")
                except Exception as e:
                    self.logger.debug(f"plan_deep_analysis: KPI registry dim fallback failed: {e}")

            # Priority 3: DGA registry metadata — view-level columns, last resort
            if not dimensions and request.kpi_name:
                if self.data_governance_agent is None:
                    raise RuntimeError(
                        "Data Governance Agent not initialized. "
                        "Ensure _wire_governance_dependencies() was called during startup."
                    )
                mapping_req = KPIDataProductMappingRequest(
                    kpi_names=[request.kpi_name],
                    context={"principal_id": getattr(request, "principal_id", None)}
                )
                mapping_resp = await self.data_governance_agent.map_kpis_to_data_products(mapping_req)
                if mapping_resp and getattr(mapping_resp, "mappings", None):
                    md = mapping_resp.mappings[0].metadata or {}
                    if isinstance(md, dict):
                        dims = md.get("dimensions")
                        if isinstance(dims, list):
                            extracted_dims = []
                            for d in dims:
                                if d:
                                    if isinstance(d, dict):
                                        dim_name = d.get('name') or d.get('field') or str(d)
                                    elif hasattr(d, 'name'):
                                        dim_name = d.name
                                    elif hasattr(d, 'field'):
                                        dim_name = d.field
                                    else:
                                        dim_name = str(d)
                                    extracted_dims.append(dim_name)
                            dimensions = extracted_dims
                            if dimensions:
                                dimension_rank_source = "dga_metadata"

            # Create skeleton steps for grouped/timeframe comparisons (executed by DPA later)
            steps: List[Dict[str, Any]] = self._build_group_compare_steps(dimensions, request.timeframe, request.filters)

            # Build plan (no SQL here; DPA handles execution in execute_deep_analysis)
            plan = DeepAnalysisPlan(
                kpi_name=request.kpi_name,
                client_id=getattr(request, "client_id", None),
                timeframe=request.timeframe,
                filters=request.filters,
                dimensions=dimensions,
                dimensions_considered=list(dimensions),
                dimension_rank_source=dimension_rank_source,
                steps=steps,
                notes="KT core with SCQA/MECE framing (auto-derived dimensions from data product contract).",
                analysis_mode=getattr(request, "analysis_mode", "problem"),
                # 11I-B: propagate alert-type context for SCQA framing
                alert_type=getattr(request, "alert_type", None),
                compound_alert=getattr(request, "compound_alert", False),
                compound_pattern=getattr(request, "compound_pattern", None),
                # 11I-D: comparator selection + bounded secondary-fact narration
                merged_alert_types=getattr(request, "merged_alert_types", None),
                secondary_alert_facts=getattr(request, "secondary_alert_facts", None),
                comparator_override=getattr(request, "comparator_override", None),
            )
            try:
                self.logger.info(f"plan_deep_analysis: selected_dims={len(dimensions)} steps={len(steps)}")
            except Exception:
                pass
            return DeepAnalysisResponse.success(
                request_id=req_id,
                plan=plan,
                dimensions_suggested=plan.dimensions,
                percent_growth_enabled=bool(request.enable_percent_growth),
                timeframe_mapping=None,
            )
        except Exception as e:
            return DeepAnalysisResponse.error(request_id=req_id, error_message=str(e))

    async def execute_deep_analysis(self, plan: DeepAnalysisPlan) -> DeepAnalysisResponse:
        req_id = str(uuid.uuid4())
        try:
            try:
                plan_filters = getattr(plan, 'filters', None)
                self.logger.info(f"execute_deep_analysis: kpi={getattr(plan, 'kpi_name', None)} timeframe={getattr(plan, 'timeframe', None)} dims_in={len(getattr(plan, 'dimensions', []) or [])} filters={plan_filters}")
            except Exception:
                pass
            kt = KTIsIsNot()

            # Did EVERY dimension go through the ratio bridge? Only then are the
            # per-segment deltas revenue-weighted contributions, and only then may a
            # consumer sum them. Counted rather than flagged so a partial run (bridge on
            # one dimension, generic fallback on another) resolves to "not summable"
            # instead of silently claiming additivity.
            #
            # Declared HERE, not inside the DPA branch that populates it: it is read
            # unconditionally at the end of this method, and a definition nested in a
            # conditional would raise NameError on every path where no KPI resolves.
            _bridge_stats = {"levels": 0, "bridged": 0}

            # Per-dimension totals, as the WAREHOUSE computed them (GROUP BY ROLLUP).
            # Never derived by summing members: for a ratio KPI that gives 452.95%
            # where the truth is 29.43%. Declared here, not inside the DPA branch that
            # fills it, because it is read unconditionally at the end of this method.
            _dimension_totals: Dict[str, DimensionTotal] = {}

            # (dimension, key) -> weighted contribution, populated only by the ratio
            # bridge. Declared unconditionally so every consumer can look up without
            # knowing whether the bridge ran; an empty dict yields None everywhere,
            # which renders as "not computed" rather than "contributed nothing".
            _contrib_by_key: Dict[tuple, float] = {}

            def _record_dimension_total(dim: str, cur: Optional[float], prev: Optional[float]) -> None:
                if cur is None and prev is None:
                    return  # source supplied no total — record nothing rather than a zero
                _dimension_totals[str(dim)] = DimensionTotal(
                    current=cur,
                    previous=prev,
                    delta=(cur - prev) if (cur is not None and prev is not None) else None,
                    source="rollup",
                )

            change_points: List[ChangePoint] = []
            queries_executed: int = 0
            when_started: Optional[str] = None
            spec_main: Dict[str, Any] = {"comparison_type": "previous", "inverse_logic": False, "yellow_threshold": 0.0}
            kpi_def = None  # populated below when resolvable; used for unit-aware SCQA framing

            # Dimensions this KPI's not_sliceable_by deny list excludes from analysis
            # (docs/architecture/kpi_semantic_contract.md §4.5) — populated once kpi_def
            # resolves, read unconditionally at the end of this method (same reason
            # _dimension_totals is declared here rather than inside the branch that fills
            # it: a definition nested in a conditional would raise NameError on every path
            # where no KPI resolves).
            _denied_dims: Dict[str, Dict[str, Any]] = {}  # dimension name -> {reason_class, source, note}
            _dimensions_excluded: List[Dict[str, Any]] = []

            # If DP Agent is available, compute where/when by executing grouped queries
            if self.data_product_agent is not None and getattr(plan, "kpi_name", None):
                try:
                    # Load KPI definition from Supabase-backed RegistryFactory (single source of truth).
                    # Tenant-scoped id-or-name resolution — the previous unscoped
                    # rf_provider.get() fallback here resolved same-id KPIs from OTHER
                    # tenants (wrong data product → wrong backend → empty Is/Is-Not).
                    _plan_client_id = getattr(plan, "client_id", None)
                    kpi_def = self._lookup_kpi_scoped(plan.kpi_name, _plan_client_id)
                    if kpi_def is None and not _plan_client_id:
                        # Legacy single-tenant path only: provider-level lookup by bare id/name
                        from src.registry.factory import RegistryFactory
                        rf_provider = RegistryFactory().get_provider("kpi")
                        if rf_provider:
                            kpi_def = rf_provider.get(plan.kpi_name)
                except Exception as e:
                    kpi_def = None
                    self.logger.debug(f"execute_deep_analysis: KPI load failed: {e}")

                if kpi_def is not None:
                    dp_id = getattr(kpi_def, "data_product_id", None)
                    cur_tf = getattr(plan, "timeframe", None)
                    # Default to current_quarter if no timeframe specified
                    if not cur_tf:
                        cur_tf = "current_quarter"
                        try:
                            if hasattr(plan, "timeframe"):
                                plan.timeframe = cur_tf
                        except Exception:
                            pass
                    prev_tf = self._prev_timeframe(cur_tf)

                    # §4.5: index the deny list once, before any dimension list is built,
                    # so both the flat loop and the hierarchical vector path below can
                    # filter against it. Tolerates the KPI model instance carrying either
                    # NotSliceableByEntry objects or plain dicts (defensive — this method
                    # accepts kpi_def from more than one lookup path).
                    for _entry in (getattr(kpi_def, "not_sliceable_by", None) or []):
                        _dim_name = _entry.get("dimension") if isinstance(_entry, dict) else getattr(_entry, "dimension", None)
                        if not _dim_name:
                            continue
                        _reason_class = _entry.get("reason_class") if isinstance(_entry, dict) else getattr(_entry, "reason_class", None)
                        _source = _entry.get("source") if isinstance(_entry, dict) else getattr(_entry, "source", None)
                        _denied_dims[_dim_name] = {
                            "reason_class": _reason_class or "pipeline_gap",
                            "source": _source or "derived",
                        }

                    dims = getattr(plan, "dimensions", []) or []

                    # Fallback: populate dimensions and steps from contract if missing
                    if not dims:
                        dims = self._dims_from_contract(limit=self.config.max_dimensions, kpi_name=getattr(plan, "kpi_name", None), client_id=getattr(plan, "client_id", None))
                        try:
                            # Update the incoming plan so UI shows correct counts
                            if hasattr(plan, "dimensions"):
                                plan.dimensions = dims
                        except Exception:
                            pass

                    # §4.5: exclude denied dimensions BEFORE the max_dimensions cut (applied
                    # later via dims_to_process/unique_dims), not after — a denied slot should
                    # free room for a valid dimension, not just waste a query slot on a cut
                    # already known to be meaningless. Every exclusion is recorded in
                    # _dimensions_excluded, never silent (§4.5's "one rule that must not be
                    # broken" — a deny list that quietly shrinks the investigation is the
                    # preferred-literal defect wearing better clothes).
                    if _denied_dims and dims:
                        _kept_dims = []
                        for _d in dims:
                            if _d in _denied_dims:
                                _dimensions_excluded.append({"dimension": _d, **_denied_dims[_d]})
                            else:
                                _kept_dims.append(_d)
                        if _dimensions_excluded:
                            self.logger.info(
                                f"[SLICEABILITY] Excluded {len(_dimensions_excluded)} denied dimension(s) "
                                f"for {getattr(plan, 'kpi_name', '?')}: {[e['dimension'] for e in _dimensions_excluded]}"
                            )
                        dims = _kept_dims

                    try:
                        steps_attr = getattr(plan, "steps", None)
                    except Exception:
                        steps_attr = None
                    if not steps_attr:
                        try:
                            new_steps = self._build_group_compare_steps(dims, cur_tf, getattr(plan, "filters", None))
                            if hasattr(plan, "steps"):
                                plan.steps = new_steps
                        except Exception:
                            pass

                    def _as_map(exec_obj: Dict[str, Any]) -> Dict[str, float]:
                        try:
                            cols = [str(c) for c in (exec_obj.get("columns") or [])]
                            rows = exec_obj.get("rows") or []
                            if len(cols) < 2:
                                return {}
                            key_idx = 0
                            val_idx = 1 if len(cols) > 1 else 0
                            out: Dict[str, float] = {}
                            for r in rows:
                                try:
                                    if isinstance(r, dict):
                                        key_col = cols[key_idx]
                                        val_col = cols[val_idx]
                                        _raw_key = r.get(key_col)
                                        val_raw = r.get(val_col)
                                        val = float(val_raw) if val_raw is not None else 0.0
                                    else:
                                        _raw_key = r[key_idx]
                                        val = float(r[val_idx]) if r[val_idx] is not None else 0.0
                                    # A NULL dimension is GROUP BY ROLLUP's grand-total row.
                                    # Tested on the raw value, not on str(...) == "None", so a
                                    # segment legitimately named "None" is never mistaken for
                                    # the total. Sentinel contains a NUL byte, which no
                                    # dimension value can.
                                    key = _ROLLUP_TOTAL_KEY if _raw_key is None else str(_raw_key)
                                    out[key] = val
                                except Exception:
                                    continue
                            return out
                        except Exception:
                            return {}

                    def _pop_total(m: Dict[str, float]) -> Optional[float]:
                        """Remove and return the ROLLUP grand-total row from a grouped map.

                        MUST be called on every map before iterating it. The total row
                        has a NULL dimension, so left in place it becomes a phantom
                        segment that outweighs every real one — and would be ranked as
                        the top change point.
                        """
                        if _ROLLUP_TOTAL_KEY in m:
                            return float(m.pop(_ROLLUP_TOTAL_KEY))
                        return None

                    # Helper: read dimension hierarchies from contract (if provided)
                    def _hierarchies_from_contract() -> Dict[str, List[str]]:
                        try:
                            cpath = self._contract_path_for_kpi(getattr(plan, "kpi_name", None), client_id=getattr(plan, "client_id", None))
                            if not os.path.exists(cpath):
                                return {}
                            with open(cpath, "r", encoding="utf-8") as f:
                                doc = yaml.safe_load(f)
                            views = (doc or {}).get("views", [])
                            target = None
                            for v in views:
                                if isinstance(v, dict) and v.get("llm_profile"):
                                    target = v
                                    break
                            if not isinstance(target, dict):
                                return {}
                            llm_profile = target.get("llm_profile", {}) or {}
                            hier = llm_profile.get("dimension_hierarchies") or {}
                            out: Dict[str, List[str]] = {}
                            if isinstance(hier, dict):
                                for k, v in hier.items():
                                    if isinstance(v, list):
                                        out[str(k)] = [str(x) for x in v if x]
                            return out
                        except Exception:
                            return {}

                    # Helper: pick a threshold spec from KPI registry (default to timeframe comparator)
                    def _pick_threshold_spec() -> Dict[str, Any]:
                        # Default mapping from timeframe to comparison type
                        tf = str(cur_tf or "").lower()
                        comp = "mom"
                        if "quarter" in tf:
                            comp = "qoq"
                        elif "year" in tf:
                            comp = "yoy"
                        # Extract from KPI registry if available
                        spec = {"comparison_type": comp, "inverse_logic": False, "yellow_threshold": 0.0}
                        try:
                            thrs = getattr(kpi_def, "thresholds", None)
                            if isinstance(thrs, list) and thrs:
                                # Match timeframe-derived comparison FIRST (yoy/qoq/mom),
                                # fall back to budget only if no timeframe match found.
                                # This keeps SA→DA alignment: SA detects YoY breach → DA drills YoY.
                                chosen = None
                                for t in thrs:
                                    try:
                                        ct = getattr(t, "comparison_type", None) or (t.get("comparison_type") if isinstance(t, dict) else None)
                                        ct_str = str(getattr(ct, "value", ct)).lower() if ct is not None else ""
                                        if ct_str == comp:
                                            chosen = (ct_str, t)
                                            break
                                    except Exception:
                                        continue
                                # Fallback: use budget threshold if no timeframe match
                                if chosen is None:
                                    for t in thrs:
                                        try:
                                            ct = getattr(t, "comparison_type", None) or (t.get("comparison_type") if isinstance(t, dict) else None)
                                            ct_str = str(getattr(ct, "value", ct)).lower() if ct is not None else ""
                                            if ct_str == "budget":
                                                chosen = (ct_str, t)
                                                break
                                        except Exception:
                                            continue
                                # Apply chosen threshold settings
                                if chosen is not None:
                                    comp, t = chosen
                                    spec["comparison_type"] = comp
                                    try:
                                        inv = getattr(t, "inverse_logic", False) if not isinstance(t, dict) else bool(t.get("inverse_logic", False))
                                        yt = getattr(t, "yellow_threshold", None) if not isinstance(t, dict) else t.get("yellow_threshold")
                                        spec["inverse_logic"] = bool(inv)
                                        if yt is not None:
                                            spec["yellow_threshold"] = float(yt)
                                    except Exception:
                                        pass
                                # If budget is explicitly requested later we will compute dynamically
                        except Exception:
                            pass
                        return spec

                    # Helper: compute grouped maps for a level using DP Agent
                    async def _maps_for_level(level_label: str, comparator: str) -> List[Dict[str, Any]]:
                        groups: List[Dict[str, Any]] = []
                        _bridge_stats["levels"] += 1

                        # --- Bridge analysis path for ratio KPIs ---
                        # Activated when kpi_def carries kpi_type='ratio' metadata with
                        # bridge_numerator_sql and bridge_denominator_sql fields.
                        # Computes per-segment margin % from separate GP and Revenue queries,
                        # then produces a weighted pp-contribution for each segment.
                        # Falls through to standard path on any failure or budget comparisons.
                        try:
                            _md = getattr(kpi_def, "metadata", None) or {}
                            if isinstance(_md, dict) and _md.get("kpi_type") == "ratio" and comparator != "budget":
                                _num_sql = _md.get("bridge_numerator_sql")
                                _den_sql = _md.get("bridge_denominator_sql")
                                if _num_sql and _den_sql:
                                    if not prev_tf:
                                        raise ValueError("bridge: no prev_tf")

                                    class _SqlProxy:
                                        """Thin KPI-like object carrying a substitute sql_query."""
                                        def __init__(self, base_kpi: Any, sql_override: str) -> None:
                                            self.sql_query = sql_override
                                            self.calculation = sql_override
                                            self.name = getattr(base_kpi, "name", "bridge")
                                            self.id = getattr(base_kpi, "id", "bridge")
                                            self.metadata = getattr(base_kpi, "metadata", {})
                                            self.unit = getattr(base_kpi, "unit", None)
                                            self.data_product_id = getattr(base_kpi, "data_product_id", None)

                                    _num_proxy = _SqlProxy(kpi_def, _num_sql)
                                    _den_proxy = _SqlProxy(kpi_def, _den_sql)
                                    _base_f = getattr(plan, "filters", None)

                                    _gen_nc = await self.data_product_agent.generate_sql_for_kpi(
                                        _num_proxy, timeframe=cur_tf, filters=_base_f, breakdown=True, override_group_by=[level_label])
                                    _gen_np = await self.data_product_agent.generate_sql_for_kpi(
                                        _num_proxy, timeframe=cur_tf, filters=_base_f, breakdown=True, override_group_by=[level_label], comparison_period=True)
                                    _gen_dc = await self.data_product_agent.generate_sql_for_kpi(
                                        _den_proxy, timeframe=cur_tf, filters=_base_f, breakdown=True, override_group_by=[level_label])
                                    _gen_dp = await self.data_product_agent.generate_sql_for_kpi(
                                        _den_proxy, timeframe=cur_tf, filters=_base_f, breakdown=True, override_group_by=[level_label], comparison_period=True)

                                    if not all(g.get("success") for g in [_gen_nc, _gen_np, _gen_dc, _gen_dp]):
                                        raise ValueError("bridge: SQL generation failed for one or more components")

                                    _m_nc = _as_map(await self.data_product_agent.execute_sql(_gen_nc["sql"], data_product_id=dp_id))
                                    _m_np = _as_map(await self.data_product_agent.execute_sql(_gen_np["sql"], data_product_id=dp_id))
                                    _m_dc = _as_map(await self.data_product_agent.execute_sql(_gen_dc["sql"], data_product_id=dp_id))
                                    _m_dp = _as_map(await self.data_product_agent.execute_sql(_gen_dp["sql"], data_product_id=dp_id))

                                    _total_den_cur = sum(_m_dc.values()) or 1.0

                                    for _k in set(_m_dc) | set(_m_dp):
                                        _num_c = float(_m_nc.get(_k, 0.0))
                                        _den_c = float(_m_dc.get(_k, 0.0))
                                        _num_p = float(_m_np.get(_k, 0.0))
                                        _den_p = float(_m_dp.get(_k, 0.0))

                                        _gm_c = (_num_c / _den_c * 100.0) if _den_c != 0.0 else 0.0
                                        _gm_p = (_num_p / _den_p * 100.0) if _den_p != 0.0 else 0.0
                                        _rate  = _gm_c - _gm_p

                                        _rev_share = _den_c / _total_den_cur
                                        _contrib   = _rev_share * _rate

                                        _ratio_i = (_rate / abs(_gm_p)) if _gm_p != 0.0 else (0.0 if _rate == 0.0 else (1.0 if _rate > 0.0 else -1.0))

                                        groups.append({
                                            "dimension":    level_label,
                                            "key":          _k,
                                            "current":      round(_gm_c, 4),
                                            "previous":     round(_gm_p, 4),
                                            # `delta` is this segment's OWN rate change, always.
                                            # It used to carry `_contrib` here and the raw change
                                            # on the generic path — one field, two meanings ~8x
                                            # apart, selected by whether a KPI happened to declare
                                            # bridge metadata. change_points feed Solution Finder,
                                            # so that made a config flag silently change what the
                                            # personas reasoned about.
                                            "delta":        round(_rate, 4),
                                            # The weighted contribution keeps its own field. This
                                            # one IS additive across segments; `delta` is not.
                                            "contribution_pp": round(_contrib, 4),
                                            "ratio":        _ratio_i,
                                        })
                                        _contrib_by_key[(level_label, _k)] = round(_contrib, 4)
                                    _bridge_stats["bridged"] += 1
                                    return groups
                        except Exception as _bridge_exc:
                            self.logger.debug(f"[bridge] skipped for {level_label}: {_bridge_exc}")
                            groups = []
                        # --- End bridge analysis path ---

                        try:
                            # Current map
                            gen_cur = await self.data_product_agent.generate_sql_for_kpi(
                                kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[level_label],
                                include_total=True,
                            )
                            if not gen_cur.get("success"):
                                return []
                            cur_exec = await self.data_product_agent.execute_sql(gen_cur.get("sql"), data_product_id=dp_id)
                            m_cur = _as_map(cur_exec)
                            _tot_cur = _pop_total(m_cur)

                            if comparator == "budget":
                                # Budget map: same timeframe, version filter rewritten to Budget.
                                # NOTE: filters={"Version":"Budget"} does NOT work — the DPA drops
                                # its `filters` argument, so both queries would be identical and
                                # every segment delta would be 0. We instead feed a proxy whose
                                # sql_query is already version-substituted (mirrors SA's plan SQL).
                                _base_f = getattr(plan, "filters", None)
                                _bud_kpi = self._budget_variant_kpi(kpi_def)
                                if _bud_kpi is None:
                                    return []
                                gen_act = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=_base_f, breakdown=True, override_group_by=[level_label],
                                    include_total=True,
                                )
                                gen_bud = await self.data_product_agent.generate_sql_for_kpi(
                                    _bud_kpi, timeframe=cur_tf, filters=_base_f, breakdown=True, override_group_by=[level_label],
                                    include_total=True,
                                )
                                if not (gen_act.get("success") and gen_bud.get("success")):
                                    return []
                                act_exec = await self.data_product_agent.execute_sql(gen_act.get("sql"), data_product_id=dp_id)
                                bud_exec = await self.data_product_agent.execute_sql(gen_bud.get("sql"), data_product_id=dp_id)
                                m_act = _as_map(act_exec)
                                m_bud = _as_map(bud_exec)
                                _tot_cur = _pop_total(m_act)
                                _tot_prev = _pop_total(m_bud)
                                _record_dimension_total(level_label, _tot_cur, _tot_prev)
                                keys = set(m_act.keys()) | set(m_bud.keys())
                                for k in keys:
                                    c = float(m_act.get(k, 0.0))
                                    b = float(m_bud.get(k, 0.0))
                                    d = c - b
                                    # ratio vs budget
                                    if b == 0.0:
                                        r = 0.0 if c == 0.0 else (1.0 if c > 0.0 else -1.0)
                                    else:
                                        r = d / abs(b)
                                    groups.append({"dimension": level_label, "key": k, "current": c, "previous": b, "delta": d, "ratio": r})
                                return groups
                            else:
                                # Previous timeframe comparator
                                if not prev_tf:
                                    return []
                                gen_prev = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[level_label], comparison_period=True, include_total=True
                                )
                                if not gen_prev.get("success"):
                                    return []
                                prev_exec = await self.data_product_agent.execute_sql(gen_prev.get("sql"), data_product_id=dp_id)
                                m_prev = _as_map(prev_exec)
                                _tot_prev = _pop_total(m_prev)
                                _record_dimension_total(level_label, _tot_cur, _tot_prev)
                                keys = set(m_cur.keys()) | set(m_prev.keys())
                                for k in keys:
                                    c = float(m_cur.get(k, 0.0))
                                    p = float(m_prev.get(k, 0.0))
                                    d = c - p
                                    # ratio vs previous
                                    if p == 0.0:
                                        r = 0.0 if c == 0.0 else (1.0 if c > 0.0 else -1.0)
                                    else:
                                        r = d / abs(p)
                                    groups.append({"dimension": level_label, "key": k, "current": c, "previous": p, "delta": d, "ratio": r})
                                return groups
                        except Exception:
                            return []

                    # Helper: classify groups against threshold spec
                    def _classify(groups: List[Dict[str, Any]], spec: Dict[str, Any]) -> (List[Dict[str, Any]], List[Dict[str, Any]]):
                        breaches: List[Dict[str, Any]] = []
                        within: List[Dict[str, Any]] = []
                        inv = bool(spec.get("inverse_logic", False))
                        yb = spec.get("yellow_threshold")
                        try:
                            yb = float(0.0 if yb is None else yb)
                        except Exception:
                            yb = 0.0
                        for g in groups:
                            r = float(g.get("ratio", 0.0))
                            is_breach = (r > yb) if inv else (r < yb)
                            if is_breach:
                                breaches.append(g)
                            else:
                                within.append(g)
                        return breaches, within

                    def _format_where_entry(dimension: Any, key: Any, delta: Any, current: Any, previous: Any, note: Optional[str] = None, segment_type: Optional[str] = None, contribution_pp: Any = None) -> Dict[str, Any]:
                        try:
                            delta_val = float(delta if delta is not None else 0.0)
                        except Exception:
                            delta_val = 0.0
                        dim_label = str(dimension) if dimension is not None else "(dimension)"
                        key_label = str(key) if key is not None else "All"
                        text_parts = [f"{dim_label}: {key_label} (Δ {delta_val:+,.2f})"]
                        if note:
                            text_parts.append(str(note))
                        entry = {
                            "dimension": dimension,
                            "key": key,
                            "delta": delta,
                            "current": current,
                            "previous": previous,
                            "text": " — ".join(text_parts),
                        }
                        if note is not None:
                            entry["note"] = note
                        if segment_type is not None:
                            entry["segment_type"] = segment_type
                        # Only present for ratio KPIs with bridge SQL configured. Absent
                        # means "not computed" — never rendered as zero, which would read
                        # as "this segment contributed nothing".
                        if contribution_pp is not None:
                            entry["contribution_pp"] = contribution_pp
                        return entry

                    def _format_when_entry(bucket: Any, delta: Any, current: Any, previous: Any, note: Optional[str] = None) -> Dict[str, Any]:
                        try:
                            delta_val = float(delta if delta is not None else 0.0)
                        except Exception:
                            delta_val = 0.0
                        bucket_label = str(bucket) if bucket is not None else "(bucket)"
                        text_parts = [f"{bucket_label} (Δ {delta_val:+,.2f})"]
                        if note:
                            text_parts.append(str(note))
                        entry = {
                            "bucket": bucket,
                            "delta": delta,
                            "current": current,
                            "previous": previous,
                            "text": " — ".join(text_parts),
                        }
                        if note is not None:
                            entry["note"] = note
                        return entry

                    def _extract_scalar(exec_obj: Dict[str, Any]) -> float:
                        try:
                            rows = exec_obj.get("rows") or []
                            if not rows:
                                return 0.0
                            first = rows[0]
                            if isinstance(first, dict):
                                for val in first.values():
                                    try:
                                        return float(val)
                                    except Exception:
                                        continue
                                return 0.0
                            for item in first:
                                try:
                                    return float(item)
                                except Exception:
                                    continue
                            return 0.0
                        except Exception:
                            return 0.0

                    async def _compute_overall_summary(comparator: str) -> Optional[Dict[str, float]]:
                        try:
                            base_filters = getattr(plan, "filters", None) or {}
                            if comparator == "budget":
                                # version-substituted proxy — see _budget_variant_kpi (DPA drops filters)
                                _bud_kpi_tot = self._budget_variant_kpi(kpi_def)
                                if _bud_kpi_tot is None:
                                    return None
                                gen_act_tot = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=base_filters
                                )
                                gen_bud_tot = await self.data_product_agent.generate_sql_for_kpi(
                                    _bud_kpi_tot, timeframe=cur_tf, filters=base_filters
                                )
                                if not (gen_act_tot.get("success") and gen_bud_tot.get("success")):
                                    return None
                                act_exec_tot = await self.data_product_agent.execute_sql(gen_act_tot.get("sql"), data_product_id=dp_id)
                                bud_exec_tot = await self.data_product_agent.execute_sql(gen_bud_tot.get("sql"), data_product_id=dp_id)
                                current_total = _extract_scalar(act_exec_tot)
                                baseline_total = _extract_scalar(bud_exec_tot)
                            else:
                                if not prev_tf:
                                    return None
                                gen_cur_tot = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=base_filters
                                )
                                # comparison_period=True on the CURRENT timeframe, not a
                                # separate prev_tf token.
                                #
                                # prev_tf for year_to_date is "last_year", which resolves to
                                # the FULL prior year — while every dimensional query in this
                                # method uses cur_tf + comparison_period=True, i.e. prior
                                # YEAR-TO-DATE. That put two comparison bases in one payload,
                                # both labelled year-over-year: the headline read "29.94 vs
                                # last_year 32.63 (-8.2%)" while the segments and
                                # dimension_totals were computed against 34.43 (-13.1%).
                                #
                                # A live production briefing surfaced it: the model noticed the
                                # two baselines, could not choose between them, and wrote a
                                # next step asking the CFO to "reconcile the two reported
                                # baselines into a single authoritative figure" — escalating
                                # our inconsistency to the reader as a finding.
                                gen_prev_tot = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=base_filters,
                                    comparison_period=True,
                                )
                                if not (gen_cur_tot.get("success") and gen_prev_tot.get("success")):
                                    return None
                                cur_exec_tot = await self.data_product_agent.execute_sql(gen_cur_tot.get("sql"), data_product_id=dp_id)
                                prev_exec_tot = await self.data_product_agent.execute_sql(gen_prev_tot.get("sql"), data_product_id=dp_id)
                                current_total = _extract_scalar(cur_exec_tot)
                                baseline_total = _extract_scalar(prev_exec_tot)

                            delta_val = current_total - baseline_total
                            if baseline_total == 0.0:
                                delta_pct = 0.0 if abs(delta_val) < 1e-9 else (1.0 if delta_val > 0 else -1.0)
                            else:
                                delta_pct = delta_val / abs(baseline_total)
                            return {
                                "current": current_total,
                                "baseline": baseline_total,
                                "delta": delta_val,
                                "delta_pct": delta_pct,
                            }
                        except Exception:
                            return None

                    # Accumulators for post-loop mode inference (populated by both hierarchical and flat paths)
                    _all_problem_items: list = []
                    _all_healthy_items: list = []

                    # Primary path: hierarchical drill per vector if hierarchies present
                    hmap = _hierarchies_from_contract()
                    used_hierarchical = False
                    # Set by whichever path runs; surfaced on the response.
                    dimensions_analyzed: List[str] = []
                    spec_main = _pick_threshold_spec()
                    # 11I-D: comparator basis precedence — explicit drill override > alert-type-driven > registry default.
                    _registry_comparator = "budget" if str(spec_main.get("comparison_type", "")).lower() == "budget" else "previous"
                    comparator_main = self._resolve_da_comparator(plan, kpi_def, _registry_comparator)
                    # Keep spec_main.comparison_type consistent with the resolved basis so downstream
                    # threshold classification and SCQA labeling agree with the data actually fetched.
                    if comparator_main == "budget" and str(spec_main.get("comparison_type", "")).lower() != "budget":
                        spec_main = dict(spec_main); spec_main["comparison_type"] = "budget"
                    elif comparator_main == "previous" and str(spec_main.get("comparison_type", "")).lower() == "budget":
                        _tf_reconcile = str(cur_tf or "").lower()
                        spec_main = dict(spec_main)
                        spec_main["comparison_type"] = "qoq" if "quarter" in _tf_reconcile else ("yoy" if "year" in _tf_reconcile else "mom")
                    overall_summary = await _compute_overall_summary(comparator_main) if self.data_product_agent else None
                    if hmap:
                        used_hierarchical = True
                        spec = spec_main
                        comparator = comparator_main
                        # Declared vector order. Previously re-ranked against a
                        # ["customer","product","profit_center"] literal — inert only
                        # because no live contract happens to name a vector that way,
                        # and a trap for the first one that does. Same defect as the
                        # deleted `preferred` list in _dims_from_contract.
                        vector_order = list(hmap.keys())
                        dimensions_analyzed = [
                            lvl for vec in vector_order for lvl in (hmap.get(vec) or [])
                            if lvl not in _denied_dims
                        ]
                        for vec in vector_order:
                            levels = hmap.get(vec, []) or []
                            for lvl in levels:
                                # §4.5 — same deny-list exclusion as the flat path below,
                                # applied here too so the hierarchical vector path isn't a
                                # silent gap in the same protection.
                                if lvl in _denied_dims:
                                    _dimensions_excluded.append({"dimension": lvl, **_denied_dims[lvl]})
                                    continue
                                grp = await _maps_for_level(lvl, comparator)
                                if not grp:
                                    continue
                                breaches, within = _classify(grp, spec)
                                try:
                                    ratios = [float(g.get("ratio", 0.0)) for g in grp]
                                    labels = ["<-20%", "-20% to -10%", "-10% to 0%", "0% to 10%", "10% to 20%", ">20%"]
                                    edges = [-1e9, -0.2, -0.1, 0.0, 0.1, 0.2, 1e9]
                                    counts = [0, 0, 0, 0, 0, 0]
                                    for r in ratios:
                                        if r < edges[1]:
                                            counts[0] += 1
                                        elif r < edges[2]:
                                            counts[1] += 1
                                        elif r < edges[3]:
                                            counts[2] += 1
                                        elif r < edges[4]:
                                            counts[3] += 1
                                        elif r < edges[5]:
                                            counts[4] += 1
                                        else:
                                            counts[5] += 1
                                    rs = sorted(ratios)
                                    n = len(rs)
                                    if n > 0:
                                        if n % 2 == 1:
                                            med = rs[n // 2]
                                        else:
                                            med = (rs[n // 2 - 1] + rs[n // 2]) / 2.0
                                    else:
                                        med = 0.0
                                    inv = bool(spec.get("inverse_logic", False))
                                    try:
                                        yb_raw = spec.get("yellow_threshold")
                                        yb_val = float(0.0 if yb_raw is None else yb_raw)
                                    except Exception:
                                        yb_val = 0.0
                                    try:
                                        if inv:
                                            breach_count = sum(1 for g in grp if float(g.get("ratio", 0.0)) > yb_val)
                                        else:
                                            breach_count = sum(1 for g in grp if float(g.get("ratio", 0.0)) < yb_val)
                                    except Exception:
                                        breach_count = 0
                                    entry = {
                                        "dimension": lvl,
                                        "vector": vec,
                                        "comparator": comparator,
                                        "threshold": yb_val,
                                        "inverse_logic": inv,
                                        "total_keys": n,
                                        "breach_count": breach_count,
                                        "within_count": max(0, n - breach_count),
                                        "histogram": [{"bin": labels[i], "count": counts[i]} for i in range(len(labels))],
                                        "min_ratio": (rs[0] if n else 0.0),
                                        "median_ratio": med,
                                        "max_ratio": (rs[-1] if n else 0.0),
                                    }
                                    kt.extent_is.append(entry)
                                except Exception:
                                    pass
                                if breaches:
                                    for b in breaches:
                                        entry_b = _format_where_entry(b.get("dimension"), b.get("key"), b.get("delta"), b.get("current"), b.get("previous"), contribution_pp=b.get("contribution_pp"))
                                        kt.where_is.append(entry_b)
                                        change_points.append(ChangePoint(dimension=b.get("dimension"), key=b.get("key"), current_value=b.get("current"), previous_value=b.get("previous"), delta=b.get("delta"), contribution_pp=b.get("contribution_pp")))
                                    for w in within:
                                        entry_w = _format_where_entry(w.get("dimension"), w.get("key"), w.get("delta"), w.get("current"), w.get("previous"), note="Within threshold")
                                        kt.where_is_not.append(entry_w)
                                    break  # stop drilling this vector at first breach level
                                else:
                                    # All within threshold at this level
                                    kt.where_is_not.append(_format_where_entry(lvl, "All", 0.0, None, None, note="All within threshold"))
                                    # Continue to next finer level
                                    continue
                            # proceed to next vector

                        # If hierarchical drill found no breaches, allow legacy fallback path
                        if used_hierarchical and not change_points:
                            used_hierarchical = False

                    # WHERE (dimension values with greatest variance) - Hybrid Threshold + Adaptive N approach
                    if not used_hierarchical:
                        spec_fb = dict(spec_main) if isinstance(spec_main, dict) else _pick_threshold_spec()
                        comp_fb = comparator_main
                        # Deduplicate dimensions to avoid duplicate entries in IS/IS-NOT lists
                        unique_dims = list(dict.fromkeys(dims))
                        self.logger.info(f"[DEDUP] Processing {len(unique_dims)} unique dimensions (from {len(dims)} total): {unique_dims[:5]}...")
                        # Track already-added (dimension, key) pairs to prevent duplicates
                        added_where_is_keys: set = set()
                        added_where_is_not_keys: set = set()
                        dims_to_process = unique_dims[: max(1, min(len(unique_dims), self.config.max_dimensions))]
                        # Which dimensions were ACTUALLY analyzed. Without this a run
                        # reports N dimensions suggested, analyses max_dimensions of
                        # them, and records nowhere which ones.
                        dimensions_analyzed = list(dims_to_process)
                        self.logger.info(f"[LOOP] Will process {len(dims_to_process)} dimensions: {dims_to_process}")
                        for dim_idx, dim in enumerate(dims_to_process):
                            self.logger.info(f"[LOOP] Processing dimension {dim_idx+1}/{len(dims_to_process)}: {dim}")
                            # Snapshot of the cumulative list BEFORE this dimension's own pass, so the
                            # fallback gate below can ask "did THIS dimension add anything" instead of
                            # "is the whole multi-dimension list still empty" — the latter silently
                            # skips every dimension after the first once any prior dimension succeeds
                            # (confirmed live: comparator=budget forces every dim through the fallback
                            # branch, so after dim 1 populates kt.where_is, `if not kt.where_is` is
                            # permanently False and dims 2..N contribute nothing — 2026-08-16).
                            _where_is_count_before_dim = len(kt.where_is)
                            try:
                                # Fetch ALL data for this dimension to apply hybrid threshold selection
                                # This gives us richer context for the LLM vs fixed Top 3/Bottom 3
                                # Budget comparator: skip period-over-period TopN (delta_prev is vs prior period,
                                # not vs budget) — fall through to the dual-query budget path below.
                                if comp_fb == "budget":
                                    all_req = {"success": False}
                                else:
                                    all_req = await self.data_product_agent.generate_sql_for_kpi(
                                        kpi_def,
                                        timeframe=cur_tf,
                                        filters=getattr(plan, "filters", None),
                                        breakdown=True,
                                        override_group_by=[dim],
                                        topn={"type": "top", "n": 50, "metric": "delta_prev"}  # Fetch more for threshold analysis
                                    )
                                if all_req.get("success"):
                                    all_exec = await self.data_product_agent.execute_sql(all_req.get("sql"), data_product_id=dp_id)
                                    queries_executed += 1
                                    rows = all_exec.get("rows") or []
                                    cols = [str(c) for c in (all_exec.get("columns") or [])]
                                    # Determine column names or fallback positions
                                    key_col = cols[0] if cols else None
                                    c_col = "current_value" if "current_value" in cols else (cols[1] if len(cols) > 1 else None)
                                    p_col = "previous_value" if "previous_value" in cols else (cols[2] if len(cols) > 2 else None)
                                    d_col = "delta_prev" if "delta_prev" in cols else (cols[3] if len(cols) > 3 else None)
                                    
                                    # Parse all rows into diffs list
                                    diffs_topn = []
                                    _diff_dropped = 0  # segments lost to coercion — never silently
                                    for r in rows:
                                        try:
                                            if isinstance(r, dict):
                                                key = str(r.get(key_col)) if key_col else None
                                                c_raw = r.get(c_col) if isinstance(c_col, str) else (None if c_col is None else list(r.values())[1])
                                                p_raw = r.get(p_col) if isinstance(p_col, str) else (None if p_col is None else list(r.values())[2])
                                                d_raw = r.get(d_col) if isinstance(d_col, str) else (None if d_col is None else list(r.values())[3])
                                                c = float(c_raw) if c_raw is not None else 0.0
                                                p = float(p_raw) if p_raw is not None else 0.0
                                                d = float(d_raw) if d_raw is not None else (c - p)
                                            else:
                                                key = str(r[0])
                                                c = float(r[1]) if r[1] is not None else 0.0
                                                p = float(r[2]) if r[2] is not None else 0.0
                                                d = float(r[3]) if r[3] is not None else (c - p)
                                            if key:
                                                diffs_topn.append((key, c, p, d))
                                        except Exception:
                                            # Count, do not just skip. A row that fails
                                            # coercion silently removes a SEGMENT from
                                            # diffs_topn, which feeds top-N selection ->
                                            # change_points -> the whole Is/Is-Not
                                            # analysis. A real driver could disappear
                                            # from the diagnosis with no signal at all.
                                            _diff_dropped += 1
                                            continue
                                    if _diff_dropped:
                                        self.logger.warning(
                                            "[DA] %s: %d segment row(s) unparseable and excluded from "
                                            "diffs_topn — Is/Is-Not is computed on the remainder",
                                            plan.kpi_name, _diff_dropped,
                                        )

                                    # Apply Hybrid Threshold + Adaptive N selection
                                    # Determine trend direction from KPI registry (inverse_logic)
                                    kpi_trend_positive = self._trend_positive(plan.kpi_name, kpi_def)
                                    where_is_items, where_is_not_items = self._select_variance_items(
                                        diffs_topn,
                                        threshold_pct=0.05,  # 5% variance threshold
                                        min_items=3,
                                        max_items=10,
                                        trend_positive=kpi_trend_positive
                                    )

                                    # Extend accumulators for post-loop mode inference
                                    _all_problem_items.extend(where_is_items)
                                    _all_healthy_items.extend(where_is_not_items)

                                    added_keys_topn = set()
                                    self.logger.info(f"[DEDUP] Dim={dim}: {len(where_is_items)} problem items, {len(where_is_not_items)} healthy items, existing keys={len(added_where_is_keys)}")
                                    for key, c, p, d in where_is_items:
                                        dedup_key = (dim, key)
                                        if dedup_key not in added_where_is_keys:
                                            _contrib = _contrib_by_key.get((dim, key))
                                            entry_top = _format_where_entry(dim, key, d, c, p, segment_type="problem", contribution_pp=_contrib)
                                            kt.where_is.append(entry_top)
                                            change_points.append(ChangePoint(dimension=dim, key=key, current_value=c, previous_value=p, delta=d, contribution_pp=_contrib))
                                            added_keys_topn.add(key)
                                            added_where_is_keys.add(dedup_key)
                                        else:
                                            self.logger.warning(f"[DEDUP] Skipping duplicate: {dedup_key}")

                                    for key, c, p, d in where_is_not_items:
                                        dedup_key = (dim, key)
                                        if key not in added_keys_topn and dedup_key not in added_where_is_not_keys:
                                            entry_bot = _format_where_entry(dim, key, d, c, p, note="Outperforming", segment_type="opportunity")
                                            kt.where_is_not.append(entry_bot)
                                            added_where_is_not_keys.add(dedup_key)
                                
                                # Fallback: dual-query method if the TopN path failed to populate
                                # THIS dimension (not "is the whole cumulative list still empty").
                                if len(kt.where_is) == _where_is_count_before_dim:
                                    m_cur: Dict[str, float] = {}
                                    m_prev: Dict[str, float] = {}
                                    _fb_success = False
                                    if comp_fb == "budget":
                                        # Actual-vs-budget needs a version-substituted proxy KPI, not
                                        # a second time window — mirrors the pattern already proven in
                                        # _maps_for_level / _record_dimension_total (search
                                        # _budget_variant_kpi elsewhere in this file). TopN has no
                                        # "vs budget" query shape (see the comment above this loop),
                                        # so THIS is budget's only path to segment-level deltas — it
                                        # was silently running actual-vs-PRIOR-PERIOD here instead,
                                        # mislabeled as budget throughout the response and UI
                                        # (confirmed live: identical output to the "previous"
                                        # comparator run for the same KPI/timeframe) — fixed 2026-08-16.
                                        _bud_kpi_fb = self._budget_variant_kpi(kpi_def)
                                        if _bud_kpi_fb is not None:
                                            gen_cur = await self.data_product_agent.generate_sql_for_kpi(
                                                kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim]
                                            )
                                            gen_bud = await self.data_product_agent.generate_sql_for_kpi(
                                                _bud_kpi_fb, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim]
                                            )
                                            if gen_cur.get("success") and gen_bud.get("success"):
                                                cur_exec = await self.data_product_agent.execute_sql(gen_cur.get("sql"), data_product_id=dp_id)
                                                bud_exec = await self.data_product_agent.execute_sql(gen_bud.get("sql"), data_product_id=dp_id)
                                                queries_executed += 2
                                                m_cur = _as_map(cur_exec)
                                                m_prev = _as_map(bud_exec)
                                                _fb_success = True
                                    else:
                                        gen_cur = await self.data_product_agent.generate_sql_for_kpi(
                                            kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim]
                                        )
                                        if gen_cur.get("success"):
                                            cur_exec = await self.data_product_agent.execute_sql(gen_cur.get("sql"), data_product_id=dp_id)
                                            queries_executed += 1
                                            m_cur = _as_map(cur_exec)
                                            _fb_success = True
                                            if prev_tf:
                                                gen_prev = await self.data_product_agent.generate_sql_for_kpi(
                                                    kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim], comparison_period=True
                                                )
                                                if gen_prev.get("success"):
                                                    prev_exec = await self.data_product_agent.execute_sql(gen_prev.get("sql"), data_product_id=dp_id)
                                                    queries_executed += 1
                                                    m_prev = _as_map(prev_exec)
                                    if _fb_success:
                                        # Compute deltas per group
                                        keys = set(m_cur.keys()) | set(m_prev.keys())
                                        diffs = []
                                        for k in keys:
                                            c = m_cur.get(k, 0.0)
                                            p = m_prev.get(k, 0.0)
                                            diff = c - p
                                            diffs.append((k, c, p, diff))
                                        
                                        # Use Hybrid Threshold + Adaptive N approach
                                        kpi_trend_positive = self._trend_positive(plan.kpi_name, kpi_def)
                                        where_is_items, where_is_not_items = self._select_variance_items(
                                            diffs,
                                            threshold_pct=0.05,  # 5% variance threshold
                                            min_items=3,
                                            max_items=10,
                                            trend_positive=kpi_trend_positive
                                        )

                                        # Extend accumulators for post-loop mode inference
                                        _all_problem_items.extend(where_is_items)
                                        _all_healthy_items.extend(where_is_not_items)

                                        added_keys_fallback = set()
                                        for k, c, p, d in where_is_items:
                                            dedup_key = (dim, k)
                                            if dedup_key not in added_where_is_keys:
                                                entry_diff = _format_where_entry(dim, k, d, c, p, segment_type="problem")
                                                kt.where_is.append(entry_diff)
                                                change_points.append(ChangePoint(dimension=dim, key=k, current_value=c, previous_value=p, delta=d))
                                                added_keys_fallback.add(k)
                                                added_where_is_keys.add(dedup_key)

                                        for k, c, p, d in where_is_not_items:
                                            dedup_key = (dim, k)
                                            if k not in added_keys_fallback and dedup_key not in added_where_is_not_keys:
                                                entry_low = _format_where_entry(dim, k, d, c, p, note="Outperforming", segment_type="opportunity")
                                                kt.where_is_not.append(entry_low)
                                                added_where_is_not_keys.add(dedup_key)
                                # Always compute and attach distribution summary for this dimension
                                try:
                                    ratios: List[float] = []
                                    m_act_h: Dict[str, float] = {}
                                    m_bud_h: Dict[str, float] = {}
                                    m_cur_h: Dict[str, float] = {}
                                    m_prev_h: Dict[str, float] = {}
                                    if comp_fb == "budget":
                                        base_filters = getattr(plan, "filters", None) or {}
                                        # version-substituted proxy — see _budget_variant_kpi (DPA drops filters)
                                        _bud_kpi_h = self._budget_variant_kpi(kpi_def)
                                        gen_act_h = await self.data_product_agent.generate_sql_for_kpi(
                                            kpi_def, timeframe=cur_tf, filters=base_filters, breakdown=True, override_group_by=[dim]
                                        )
                                        gen_bud_h = await self.data_product_agent.generate_sql_for_kpi(
                                            _bud_kpi_h, timeframe=cur_tf, filters=base_filters, breakdown=True, override_group_by=[dim]
                                        ) if _bud_kpi_h is not None else {"success": False}
                                        if gen_act_h.get("success") and gen_bud_h.get("success"):
                                            act_exec_h = await self.data_product_agent.execute_sql(gen_act_h.get("sql"), data_product_id=dp_id)
                                            bud_exec_h = await self.data_product_agent.execute_sql(gen_bud_h.get("sql"), data_product_id=dp_id)
                                            m_act_h = _as_map(act_exec_h)
                                            m_bud_h = _as_map(bud_exec_h)
                                            keys_h = set(m_act_h.keys()) | set(m_bud_h.keys())
                                            for k in keys_h:
                                                c = float(m_act_h.get(k, 0.0)); b = float(m_bud_h.get(k, 0.0))
                                                if b == 0.0:
                                                    r = 0.0 if c == 0.0 else (1.0 if c > 0.0 else -1.0)
                                                else:
                                                    r = (c - b) / abs(b)
                                                ratios.append(r)
                                    else:
                                        if prev_tf:
                                            gen_cur_h = await self.data_product_agent.generate_sql_for_kpi(
                                                kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim]
                                            )
                                            gen_prev_h = await self.data_product_agent.generate_sql_for_kpi(
                                                kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim], comparison_period=True
                                            )
                                            if gen_cur_h.get("success") and gen_prev_h.get("success"):
                                                cur_exec_h = await self.data_product_agent.execute_sql(gen_cur_h.get("sql"), data_product_id=dp_id)
                                                prev_exec_h = await self.data_product_agent.execute_sql(gen_prev_h.get("sql"), data_product_id=dp_id)
                                                m_cur_h = _as_map(cur_exec_h)
                                                m_prev_h = _as_map(prev_exec_h)
                                                keys_h = set(m_cur_h.keys()) | set(m_prev_h.keys())
                                                for k in keys_h:
                                                    c = float(m_cur_h.get(k, 0.0)); p = float(m_prev_h.get(k, 0.0))
                                                    if p == 0.0:
                                                        r = 0.0 if c == 0.0 else (1.0 if c > 0.0 else -1.0)
                                                    else:
                                                        r = (c - p) / abs(p)
                                                    ratios.append(r)
                                    if ratios:
                                        labels = ["<-20%", "-20% to -10%", "-10% to 0%", "0% to 10%", "10% to 20%", ">20%"]
                                        edges = [-1e9, -0.2, -0.1, 0.0, 0.1, 0.2, 1e9]
                                        counts = [0, 0, 0, 0, 0, 0]
                                        for r in ratios:
                                            if r < edges[1]: counts[0] += 1
                                            elif r < edges[2]: counts[1] += 1
                                            elif r < edges[3]: counts[2] += 1
                                            elif r < edges[4]: counts[3] += 1
                                            elif r < edges[5]: counts[4] += 1
                                            else: counts[5] += 1
                                        rs = sorted(ratios)
                                        n = len(rs)
                                        if n % 2 == 1:
                                            med = rs[n // 2]
                                        else:
                                            med = (rs[n // 2 - 1] + rs[n // 2]) / 2.0 if n else 0.0
                                        inv_fb = bool(spec_fb.get("inverse_logic", False))
                                        try:
                                            yb_raw_fb = spec_fb.get("yellow_threshold"); yb_val_fb = float(0.0 if yb_raw_fb is None else yb_raw_fb)
                                        except Exception:
                                            yb_val_fb = 0.0
                                        try:
                                            if inv_fb:
                                                breach_cnt_fb = sum(1 for r in ratios if r > yb_val_fb)
                                            else:
                                                breach_cnt_fb = sum(1 for r in ratios if r < yb_val_fb)
                                        except Exception:
                                            breach_cnt_fb = 0
                                        entry_fb = {
                                            "dimension": dim,
                                            "vector": "dimension",
                                            "comparator": comp_fb,
                                            "threshold": yb_val_fb,
                                            "inverse_logic": inv_fb,
                                            "total_keys": n,
                                            "breach_count": breach_cnt_fb,
                                            "within_count": max(0, n - breach_cnt_fb),
                                            "histogram": [{"bin": labels[i], "count": counts[i]} for i in range(len(labels))],
                                            "min_ratio": (rs[0] if n else 0.0),
                                            "median_ratio": med,
                                            "max_ratio": (rs[-1] if n else 0.0),
                                        }
                                        kt.extent_is.append(entry_fb)

                                        # NOTE: Distribution summary diffs are now handled by the main TopN/fallback paths above
                                        # with proper deduplication. This block is intentionally removed to prevent duplicates.
                                except Exception:
                                    pass
                            except Exception as de:
                                self.logger.debug(f"where-is computation failed for {dim}: {de}")

                    # --- Post-loop: self-determine effective analysis mode from segment variance ---
                    _caller_hint = getattr(plan, "analysis_mode", "problem")
                    _effective_mode = self._infer_analysis_mode(
                        _all_problem_items,
                        _all_healthy_items,
                        caller_hint=_caller_hint,
                        top_n=5,
                    )
                    plan.analysis_mode = _effective_mode
                    self.logger.info(
                        "[DA] Effective analysis_mode=%s (caller hint=%s, problem_items=%d, healthy_items=%d)",
                        _effective_mode,
                        _caller_hint,
                        len(_all_problem_items),
                        len(_all_healthy_items),
                    )

                    # Post-loop IS/IS NOT reshuffling based on effective mode
                    if _effective_mode == "opportunity" and kt.where_is_not:
                        # Only swap when IS NOT has items to promote; if IS NOT is empty
                        # (no comparison data per dimension), items already sit in where_is
                        # and are rendered as "leading segments" by the opportunity-mode UI.
                        kt.where_is, kt.where_is_not = kt.where_is_not, kt.where_is
                    elif _effective_mode == "mixed":
                        # Merge both problem and opportunity into where_is; IS NOT = empty
                        kt.where_is = kt.where_is + kt.where_is_not
                        kt.where_is_not = []
                        kt.where_is.sort(key=lambda item: abs(item.get("delta") or 0), reverse=True)
                    # "problem" mode: no reshuffling needed
                    # --- End post-loop mode inference ---

                    # ── Phase 11I-D: segment matrix — join the secondary cross-sectional basis ──
                    # When the KPI breached on BOTH previous-period and plan-variance, run the
                    # dimensional grouping a second time for the other basis (reusing _maps_for_level,
                    # which is already comparator-parameterized) and join each segment's secondary
                    # delta + cross-basis tier onto the primary table's rows. One shared-frame table,
                    # no second KT table, no LLM cross-table fusion. Degrades to primary-only on any error.
                    comparator_secondary: Optional[str] = None
                    matrix_ran = False
                    try:
                        if self._is_matrix_eligible(plan, kpi_def, comparator_main) and self.data_product_agent:
                            comparator_secondary = "budget" if comparator_main == "previous" else "previous"
                            _trend_pos = self._trend_positive(plan.kpi_name, kpi_def)
                            _primary_dims: List[Any] = []
                            for _row in (kt.where_is or []) + (kt.where_is_not or []):
                                _dm = _row.get("dimension")
                                if _dm is not None and _dm not in _primary_dims:
                                    _primary_dims.append(_dm)
                            _sec_delta: Dict[tuple, Any] = {}
                            for _dm in _primary_dims[: max(1, self.config.max_dimensions)]:
                                for _g in (await _maps_for_level(_dm, comparator_secondary) or []):
                                    _gk = _g.get("key")
                                    if _gk is not None:
                                        _sec_delta[(str(_dm), str(_gk))] = _g.get("delta")
                            if _sec_delta:
                                for _row in (kt.where_is or []):
                                    _sd = _sec_delta.get((str(_row.get("dimension")), str(_row.get("key"))))
                                    _row["secondary_delta"] = _sd
                                    _row["basis_agreement"] = self._classify_basis_agreement(
                                        _row.get("delta"), _sd, _trend_pos, "problem")
                                for _row in (kt.where_is_not or []):
                                    _sd = _sec_delta.get((str(_row.get("dimension")), str(_row.get("key"))))
                                    _row["secondary_delta"] = _sd
                                    _row["basis_agreement"] = self._classify_basis_agreement(
                                        _row.get("delta"), _sd, _trend_pos, "healthy")
                                matrix_ran = True
                    except Exception as _mx_exc:
                        self.logger.warning("[DA] segment matrix secondary pass failed, degrading to primary-only: %s", _mx_exc)
                        comparator_secondary = None
                        matrix_ran = False
                    # --- End segment matrix ---

                    # WHEN (time buckets with greatest variance)
                    # Resolve time dimension column from data product contract — no hardcoding
                    time_bucket: Optional[str] = None
                    time_bucket_label: str = ""
                    if dp_id:
                        try:
                            from src.registry.factory import RegistryFactory
                            _dp_provider = RegistryFactory().get_provider("data_product")
                            _dp_obj = _dp_provider.get(dp_id) if _dp_provider else None
                            if _dp_obj and getattr(_dp_obj, "time_dimensions", None):
                                _primary_td = next(
                                    (td for td in _dp_obj.time_dimensions if getattr(td, "primary", True)),
                                    _dp_obj.time_dimensions[0],
                                )
                                time_bucket = _primary_td.display_expr or _primary_td.column
                                time_bucket_label = getattr(_primary_td, "label", None) or time_bucket
                        except Exception as _td_err:
                            self.logger.debug("[DA] time_dimension lookup failed for dp_id=%s: %s", dp_id, _td_err)
                    if not time_bucket:
                        self.logger.info("[DA] No time_dimension configured for dp_id=%s — skipping WHEN analysis", dp_id)
                    if time_bucket:
                        try:
                            # Prefer Top/Bottom N with delta_prev for time buckets
                            t_top = await self.data_product_agent.generate_sql_for_kpi(
                                kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[time_bucket], topn={"type": "top", "n": 3, "metric": "delta_prev"}
                            )
                            if t_top.get("success"):
                                t_top_exec = await self.data_product_agent.execute_sql(t_top.get("sql"), data_product_id=dp_id)
                                queries_executed += 1
                                rows_t = t_top_exec.get("rows") or []
                                cols_t = [str(c) for c in (t_top_exec.get("columns") or [])]
                                b_col = cols_t[0] if cols_t else None
                                c_col = "current_value" if "current_value" in cols_t else (cols_t[1] if len(cols_t) > 1 else None)
                                p_col = "previous_value" if "previous_value" in cols_t else (cols_t[2] if len(cols_t) > 2 else None)
                                d_col = "delta_prev" if "delta_prev" in cols_t else (cols_t[3] if len(cols_t) > 3 else None)
                                for r in rows_t:
                                    try:
                                        if isinstance(r, dict):
                                            b = str(r.get(b_col)) if b_col else None
                                            c_raw = r.get(c_col) if isinstance(c_col, str) else (None if c_col is None else list(r.values())[1])
                                            p_raw = r.get(p_col) if isinstance(p_col, str) else (None if p_col is None else list(r.values())[2])
                                            d_raw = r.get(d_col) if isinstance(d_col, str) else (None if d_col is None else list(r.values())[3])
                                            c = float(c_raw) if c_raw is not None else 0.0
                                            p = float(p_raw) if p_raw is not None else 0.0
                                            d = float(d_raw) if d_raw is not None else (c - p)
                                        else:
                                            b = str(r[0]); c = float(r[1] or 0.0); p = float(r[2] or 0.0); d = float((r[3] if r[3] is not None else c - p))
                                        kt.when_is.append(_format_when_entry(b, d, c, p))
                                    except Exception:
                                        continue
                            t_bot = await self.data_product_agent.generate_sql_for_kpi(
                                kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[time_bucket], topn={"type": "bottom", "n": 3, "metric": "delta_prev"}
                            )
                            if t_bot.get("success"):
                                t_bot_exec = await self.data_product_agent.execute_sql(t_bot.get("sql"), data_product_id=dp_id)
                                queries_executed += 1
                                rows_tb = t_bot_exec.get("rows") or []
                                cols_tb = [str(c) for c in (t_bot_exec.get("columns") or [])]
                                b_col_b = cols_tb[0] if cols_tb else None
                                c_col_b = "current_value" if "current_value" in cols_tb else (cols_tb[1] if len(cols_tb) > 1 else None)
                                p_col_b = "previous_value" if "previous_value" in cols_tb else (cols_tb[2] if len(cols_tb) > 2 else None)
                                d_col_b = "delta_prev" if "delta_prev" in cols_tb else (cols_tb[3] if len(cols_tb) > 3 else None)
                                for r in rows_tb:
                                    try:
                                        if isinstance(r, dict):
                                            b = str(r.get(b_col_b)) if b_col_b else None
                                            c_raw = r.get(c_col_b) if isinstance(c_col_b, str) else (None if c_col_b is None else list(r.values())[1])
                                            p_raw = r.get(p_col_b) if isinstance(p_col_b, str) else (None if p_col_b is None else list(r.values())[2])
                                            d_raw = r.get(d_col_b) if isinstance(d_col_b, str) else (None if d_col_b is None else list(r.values())[3])
                                            c = float(c_raw) if c_raw is not None else 0.0
                                            p = float(p_raw) if p_raw is not None else 0.0
                                            d = float(d_raw) if d_raw is not None else (c - p)
                                        else:
                                            b = str(r[0]); c = float(r[1] or 0.0); p = float(r[2] or 0.0); d = float((r[3] if r[3] is not None else c - p))
                                        kt.when_is_not.append(_format_when_entry(b, d, c, p, note="Within threshold"))
                                    except Exception:
                                        continue
                            # Fallback if needed (dual-query path)
                            if not kt.when_is:
                                gen_cur_t = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[time_bucket]
                                )
                                if gen_cur_t.get("success"):
                                    cur_exec_t = await self.data_product_agent.execute_sql(gen_cur_t.get("sql"), data_product_id=dp_id)
                                    queries_executed += 1
                                    m_cur_t = _as_map(cur_exec_t)
                                else:
                                    m_cur_t = {}
                                m_prev_t: Dict[str, float] = {}
                                if prev_tf:
                                    gen_prev_t = await self.data_product_agent.generate_sql_for_kpi(
                                        kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[time_bucket], comparison_period=True
                                    )
                                    if gen_prev_t.get("success"):
                                        prev_exec_t = await self.data_product_agent.execute_sql(gen_prev_t.get("sql"), data_product_id=dp_id)
                                        queries_executed += 1
                                        m_prev_t = _as_map(prev_exec_t)
                                keys_t = set(m_cur_t.keys()) | set(m_prev_t.keys())
                                diffs_t = []
                                for k in keys_t:
                                    c = m_cur_t.get(k, 0.0)
                                    p = m_prev_t.get(k, 0.0)
                                    d = c - p
                                    diffs_t.append((k, c, p, d))
                                diffs_t.sort(key=lambda t: abs(t[3]), reverse=True)
                                for k, c, p, d in diffs_t[:3]:
                                    kt.when_is.append(_format_when_entry(k, d, c, p))
                                diffs_t_low = sorted(diffs_t, key=lambda t: abs(t[3]))
                                for k, c, p, d in diffs_t_low[:3]:
                                    kt.when_is_not.append(_format_when_entry(k, d, c, p, note="Within threshold"))
                        except Exception as te:
                            self.logger.debug(f"when-is computation failed: {te}")

                    # Fallback: populate dimensions and steps from contract if missing
                    if not getattr(plan, "dimensions", None):
                        # Use contract dims; if still empty and hierarchies exist, seed from top-level hierarchy labels
                        dims_from_contract = self._dims_from_contract(limit=self.config.max_dimensions, kpi_name=getattr(plan, "kpi_name", None), client_id=getattr(plan, "client_id", None))
                        if dims_from_contract:
                            plan.dimensions = dims_from_contract
                        elif hmap:
                            try:
                                top_level_dims: List[str] = []
                                for vec, levels in (hmap.items() if isinstance(hmap, dict) else []):
                                    if isinstance(levels, list) and levels:
                                        top_level_dims.append(str(levels[0]))
                                if top_level_dims:
                                    plan.dimensions = top_level_dims
                            except Exception:
                                pass
                    if not getattr(plan, "steps", None):
                        # Build steps from plan.dimensions (now possibly seeded from hierarchies)
                        plan.steps = self._build_group_compare_steps(plan.dimensions, getattr(plan, "timeframe", None), getattr(plan, "filters", None))

                    # Extent (queries planned)
                    try:
                        steps = getattr(plan, "steps", []) or []
                        planned = queries_executed if queries_executed > 0 else len(steps)
                        kt.extent_is.append({"queries_planned": planned})
                    except Exception:
                        pass
                    try:
                        self.logger.info(f"execute_deep_analysis: dims_after_planning={len(getattr(plan, 'dimensions', []) or [])} steps={len(getattr(plan, 'steps', []) or [])} queries_executed={queries_executed}")
                    except Exception:
                        pass

                    # Compose KT What/What Not narratives based on results
                    try:
                        # The label must describe what was actually measured. It said
                        # "last_year" while the figure is now the prior YEAR-TO-DATE
                        # window — a label naming a different period than the number
                        # is how the wrong baseline stayed invisible in the first place.
                        comparator_label = (
                            "Budget" if comparator_main == "budget"
                            else (f"prior {cur_tf}" if cur_tf else "prior period")
                        )
                        new_what_is: List[str] = []
                        new_what_is_not: List[str] = []
                        if overall_summary:
                            delta_pct = overall_summary.get("delta_pct", 0.0)
                            new_what_is.append(
                                f"{plan.kpi_name} is {overall_summary.get('current', 0.0):,.2f} vs {comparator_label} {overall_summary.get('baseline', 0.0):,.2f} (Δ {overall_summary.get('delta', 0.0):+,.2f}, {delta_pct:+.1%})."
                            )
                        if cur_tf:
                            new_what_is.append(f"Issue observed during {cur_tf} compared against {comparator_label}.")
                        
                        # MVP Optimization: Sort and truncate global change_points to top 5 by impact
                        if change_points:
                            change_points.sort(key=lambda cp: abs(getattr(cp, "delta", 0.0) or 0.0), reverse=True)
                            change_points = change_points[:5]
                            
                        top_cp = None
                        if change_points:
                            top_cp = max(change_points, key=lambda cp: abs(getattr(cp, "delta", 0.0) or 0.0))
                        if top_cp and getattr(top_cp, "dimension", None) is not None:
                            try:
                                dim_name = getattr(top_cp, "dimension", "Dimension")
                                key_name = getattr(top_cp, "key", "(unknown)")
                                delta_val = float(getattr(top_cp, "delta", 0.0) or 0.0)
                                new_what_is.append(
                                    f"Largest variance in {dim_name}: {key_name} (Δ {delta_val:+,.2f})."
                                )
                            except Exception:
                                pass
                        if not change_points:
                            new_what_is.append("No discrete change points breached thresholds; variance is below detection limits.")

                        def _pick_stable(entries: List[Any]) -> Optional[str]:
                            try:
                                candidates: List[tuple] = []
                                for row in entries or []:
                                    if isinstance(row, dict):
                                        if row.get("note"):
                                            candidates.append((0.0, row.get("note")))
                                        else:
                                            delta_raw = row.get("delta")
                                            try:
                                                delta_val = float(delta_raw)
                                            except Exception:
                                                delta_val = 0.0
                                            label_parts = []
                                            if row.get("dimension"):
                                                label_parts.append(str(row.get("dimension")))
                                            if row.get("key") is not None:
                                                label_parts.append(str(row.get("key")))
                                            if row.get("text"):
                                                label = str(row.get("text"))
                                            else:
                                                label = " - ".join(label_parts) if label_parts else "Stable segment"
                                            candidates.append((abs(delta_val), label))
                                    else:
                                        candidates.append((0.0, str(row)))
                                if not candidates:
                                    return None
                                candidates.sort(key=lambda t: t[0])
                                return candidates[0][1]
                            except Exception:
                                return None

                        stable_dim = _pick_stable(getattr(kt, "where_is_not", []))
                        if stable_dim:
                            new_what_is_not.append(f"Stable across segments: {stable_dim}")

                        stable_time = _pick_stable(getattr(kt, "when_is_not", []))
                        if stable_time:
                            new_what_is_not.append(f"Unaffected timeframe buckets: {stable_time}")

                        if not getattr(plan, "filters", None):
                            new_what_is_not.append("No additional filters applied; other business areas appear unaffected.")
                        else:
                            new_what_is.append("Analysis scoped by applied filters, limiting impact to selected context.")

                        if not new_what_is_not and getattr(kt, "where_is_not", None):
                            new_what_is_not.append("Non-breaching segments remain within expected thresholds.")

                        if not new_what_is:
                            new_what_is.append("Variance details unavailable; review data inputs.")
                        if not new_what_is_not:
                            new_what_is_not.append("No clear contrasting conditions identified.")

                        kt.what_is = [{"text": msg} for msg in new_what_is]
                        kt.what_is_not = [{"text": msg} for msg in new_what_is_not]
                    except Exception:
                        pass

                    # Derive 'when_started' as earliest bucket where the change moved in the adverse direction
                    when_started: Optional[str] = None
                    try:
                        # Determine adverse direction based on KPI registry (inverse_logic)
                        adverse_if = (lambda d: d < 0.0) if self._trend_positive(getattr(plan, "kpi_name", "") or "", kpi_def) else (lambda d: d > 0.0)
                        cand: List[str] = []
                        for lst in [getattr(kt, "when_is", []) or [], getattr(kt, "when_is_not", []) or []]:
                            for row in lst:
                                try:
                                    b = row.get("bucket") if isinstance(row, dict) else None
                                    d_raw = row.get("delta") if isinstance(row, dict) else None
                                    d = float(d_raw) if d_raw is not None else 0.0
                                    if b and adverse_if(d):
                                        cand.append(str(b))
                                except Exception:
                                    continue
                        if not cand:
                            for row in (getattr(kt, "when_is", []) or []):
                                try:
                                    b = row.get("bucket") if isinstance(row, dict) else None
                                    if b:
                                        cand.append(str(b))
                                except Exception:
                                    continue

                        def _bucket_key(s: str):
                            try:
                                m = re.match(r"^(\d{4})[-/](\d{2})$", s)
                                if m:
                                    return (int(m.group(1)), int(m.group(2)))
                                m2 = re.match(r"^(\d{4})$", s)
                                if m2:
                                    return (int(m2.group(1)), 0)
                            except Exception:
                                pass
                            return (s,)

                        if cand:
                            cand_sorted = sorted(set(cand), key=_bucket_key)
                            if cand_sorted:
                                when_started = str(cand_sorted[0])
                    except Exception:
                        when_started = None

            scqa_summary = await self._safe_generate_scqa_summary(
                plan=plan,
                kt=kt,
                change_points=change_points,
                spec=spec_main,
                principal_id=getattr(plan, "principal_id", "system"),
                analysis_mode=getattr(plan, "analysis_mode", "problem"),
                alert_type=getattr(plan, "alert_type", None),
                compound_pattern=getattr(plan, "compound_pattern", None),
                matrix_ran=matrix_ran,
                comparator_secondary=comparator_secondary,
                kpi_unit=getattr(kpi_def, "unit", None),
            )
            # 11I-D: append bounded secondary-fact flags for the alert types that are NOT columns in
            # the matrix (temporal/relational: projected_breach, acceleration, compound). When the
            # matrix ran, threshold_breach + plan_variance are the two matrix columns and are narrated
            # by the SCQA itself, so exclude them from the appendix to avoid double-narration.
            try:
                _merged_for_appendix = getattr(plan, "merged_alert_types", None)
                if matrix_ran and _merged_for_appendix:
                    _merged_for_appendix = [a for a in _merged_for_appendix if a not in ("threshold_breach", "plan_variance")]
                _appendix = self._build_secondary_alert_appendix(
                    getattr(plan, "alert_type", None),
                    _merged_for_appendix,
                    getattr(plan, "secondary_alert_facts", None),
                )
                if _appendix:
                    scqa_summary = f"{scqa_summary}{_appendix}"
            except Exception:
                pass
            # Ensure plan has non-empty counters for UI summary even if DP path didn't run
            try:
                if not getattr(plan, "dimensions", None):
                    plan.dimensions = self._dims_from_contract(limit=self.config.max_dimensions, kpi_name=getattr(plan, "kpi_name", None), client_id=getattr(plan, "client_id", None))
                if not getattr(plan, "steps", None):
                    plan.steps = self._build_group_compare_steps(
                        getattr(plan, "dimensions", []) or [],
                        getattr(plan, "timeframe", None),
                        getattr(plan, "filters", None),
                    )
            except Exception:
                pass
            
            # Prepare timeframe mapping safely
            cur_tf_val = getattr(plan, "timeframe", None)
            prev_tf_val = self._prev_timeframe(cur_tf_val)
            tf_mapping = None
            if cur_tf_val:
                # For ACTUALS the comparison is always the SAME timeframe shifted back
                # one period — YTD vs prior YTD, Q3 vs prior-year Q3 — so durations
                # match and the delta is meaningful. Labelling it with a different
                # token ("last_year") described a full prior year while the query
                # measured prior year-to-date, which is how the two-baseline bug hid.
                tf_mapping = {
                    "current": str(cur_tf_val),
                    "previous": f"prior {cur_tf_val}",
                }

            # Use DataQualityFilter utility to handle data anomalies
            dq_filter = DataQualityFilter()
            
            # Process where_is and where_is_not lists
            self.logger.info(f"[PRE-FILTER] where_is has {len(kt.where_is)} items, keys: {[i.get('key') for i in kt.where_is[:10]]}")
            kt.where_is, dq_issues_is = dq_filter.filter_and_dedupe(kt.where_is)
            kt.where_is_not, dq_issues_is_not = dq_filter.filter_and_dedupe(kt.where_is_not)
            self.logger.info(f"[POST-FILTER] where_is has {len(kt.where_is)} items, dq_issues_is has {len(dq_issues_is)} items")

            # Classify benchmark segments.
            # Source depends on effective mode:
            #   problem    → IS NOT = healthy/outperforming
            #   opportunity → IS = leading/outperforming (already reshuffled above)
            #   mixed       → IS items tagged segment_type="opportunity" are the blueprints
            _effective_mode_final = getattr(plan, "analysis_mode", "problem")
            if _effective_mode_final == "opportunity":
                _benchmark_source = kt.where_is
            elif _effective_mode_final == "mixed":
                _benchmark_source = [item for item in kt.where_is if isinstance(item, dict) and item.get("segment_type") == "opportunity"]
            else:
                _benchmark_source = kt.where_is_not
            if _benchmark_source:
                kt.benchmark_segments = _classify_benchmark_segments(_benchmark_source)
                self.logger.info(
                    "[BENCHMARK] Classified %d items (mode=%s): %d internal_benchmark, %d control_group",
                    len(kt.benchmark_segments),
                    _effective_mode_final,
                    sum(1 for s in kt.benchmark_segments if s.benchmark_type == "internal_benchmark"),
                    sum(1 for s in kt.benchmark_segments if s.benchmark_type == "control_group"),
                )
            
            # Create data quality alert if anomalies found
            all_dq_issues = dq_issues_is + dq_issues_is_not
            dq_alert = dq_filter.create_data_quality_alert(all_dq_issues, context="Deep Analysis")
            if dq_alert:
                kt.extent_is.append(dq_alert)
                self.logger.warning(f"[DATA_QUALITY] {len(all_dq_issues)} items moved to data quality alerts")
            
            # ── Overall movement, asked of the warehouse ────────────────────────
            # The dimension breakdowns cover the SAME rows under the same filters, so
            # the overall figure is identical for every dimension — one scalar pair,
            # not per-dimension work.
            #
            # This runs regardless of which dimensional path executed. A live run
            # proved that necessary: the ROLLUP wiring on `_maps_for_level` was inert
            # because this KPI takes the topn/CTE path instead, which ends in
            # ORDER BY ... LIMIT and cannot carry a ROLLUP row. `bridge=0/0
            # dimension_totals=0` in the logs, on an otherwise successful analysis.
            #
            # Two ungrouped queries using the KPI's own registered expression. No
            # arithmetic here beyond the subtraction of two values the warehouse
            # computed — deriving the total from the member rows is the bug this
            # replaced (452.95% against a true 29.43%).
            if not _dimension_totals and self.data_product_agent is not None and kpi_def is not None:
                try:
                    _dims_present = {
                        str(i.get("dimension")) for i in kt.where_is + kt.where_is_not
                        if isinstance(i, dict) and i.get("dimension")
                    }
                    if _dims_present:
                        async def _scalar(comparison: bool):
                            g = await self.data_product_agent.generate_sql_for_kpi(
                                kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None),
                                breakdown=False, comparison_period=comparison,
                            )
                            if not g.get("success"):
                                return None
                            ex = await self.data_product_agent.execute_sql(g.get("sql"), data_product_id=dp_id)
                            rows = (ex or {}).get("rows") or []
                            if not rows:
                                return None
                            r = rows[0]
                            v = list(r.values())[0] if isinstance(r, dict) else r[0]
                            return float(v) if v is not None else None

                        _ov_cur = await _scalar(False)
                        _ov_prev = await _scalar(True) if prev_tf else None
                        if _ov_cur is not None or _ov_prev is not None:
                            _ov = DimensionTotal(
                                current=_ov_cur, previous=_ov_prev,
                                delta=(_ov_cur - _ov_prev) if (_ov_cur is not None and _ov_prev is not None) else None,
                                # Two ungrouped queries, not a ROLLUP row — label it
                                # accurately. Provenance that overstates how a number
                                # was obtained is the failure mode this whole area of
                                # work exists to remove.
                                source="scalar_query",
                            )
                            for _d in _dims_present:
                                _dimension_totals[_d] = _ov
                            self.logger.info(
                                f"[TOTAL] overall {plan.kpi_name}: current={_ov_cur} previous={_ov_prev} "
                                f"delta={_ov.delta} applied to {len(_dims_present)} dimension(s)"
                            )
                except Exception as _tot_exc:
                    # Non-fatal: an absent total renders as no total, which is the
                    # honest outcome. It must never fall back to summing members.
                    self.logger.warning(f"[TOTAL] overall figure unavailable: {_tot_exc}")

            kt.dimension_totals = _dimension_totals

            # Cross-check: where the ratio bridge ran, the WEIGHTED contributions should
            # land on the warehouse-computed total. Two independent computations of the
            # same quantity — SUM(gp)/SUM(rev) in SQL versus sum(rev_share * rate) in
            # Python — so a divergence means one of them is wrong. Logged rather than
            # raised: the total is authoritative and already correct on its own, and a
            # bad decomposition must not take down an otherwise-good analysis.
            for _dim, _tot in _dimension_totals.items():
                if _tot.delta is None:
                    continue
                _contribs = [
                    cp.contribution_pp for cp in change_points
                    if cp.dimension == _dim and cp.contribution_pp is not None
                ]
                if not _contribs:
                    continue
                _sum_c = sum(_contribs)
                # Members shown are top-N, so the sum is a subset of the whole and can
                # only be checked for OVERSHOOT — exceeding the total it decomposes.
                if abs(_sum_c) > abs(_tot.delta) * 1.15 + 0.01:
                    self.logger.warning(
                        f"[ROLLUP-CHECK] {_dim}: contributions sum to {_sum_c:.3f} but the "
                        f"warehouse total moved {_tot.delta:.3f} — decomposition overshoots "
                        f"the quantity it decomposes"
                    )

            self.logger.info(
                f"[FINAL] where_is={len(kt.where_is)} items, where_is_not={len(kt.where_is_not)} items, "
                f"dq_issues={len(all_dq_issues)} after filtering, "
                f"bridge={_bridge_stats['bridged']}/{_bridge_stats['levels']} "
                f"dimension_totals={len(_dimension_totals)}"
            )

            return DeepAnalysisResponse.success(
                request_id=req_id,
                plan=plan,
                scqa_summary=scqa_summary,
                kt_is_is_not=kt,
                change_points=change_points,
                percent_growth_enabled=False,
                timeframe_mapping=tf_mapping,
                when_started=when_started,
                dimensions_suggested=getattr(plan, "dimensions", []),
                dimensions_analyzed=dimensions_analyzed,
                dimensions_excluded=_dimensions_excluded,
                analysis_mode=getattr(plan, "analysis_mode", "problem"),
                mixed_framing=(_effective_mode_final == "mixed"),
                # 11I-D: surface which alert basis was diagnosed so SF/PIB can label it and the
                # frontend can offer the on-demand 'diagnose vs the other basis' drill.
                alert_type=getattr(plan, "alert_type", None),
                comparator=comparator_main,
                merged_alert_types=getattr(plan, "merged_alert_types", None),
                comparator_secondary=comparator_secondary,
                matrix_ran=matrix_ran,
            )
        except Exception as e:
            import traceback as _tb
            self.logger.error("[DA] execute_deep_analysis TRACEBACK:\n%s", _tb.format_exc())
            return DeepAnalysisResponse.error(request_id=req_id, error_message=str(e))

    # ========================================================================
    # Problem Refinement Chat (MBB-Style Principal Engagement)
    # ========================================================================

    async def refine_analysis(
        self,
        input_model: ProblemRefinementInput,
        context: Optional[Dict[str, Any]] = None
    ) -> ProblemRefinementResult:
        """
        Interactive problem refinement chat using hybrid approach:
        - Deterministic topic sequence (what to cover)
        - LLM-driven question generation (how to ask)
        
        This method is called iteratively for each turn of the conversation.
        """
        try:
            # Extract inputs
            da_output = input_model.deep_analysis_output
            principal_ctx = input_model.principal_context
            history = input_model.conversation_history or []
            user_message = input_model.user_message
            turn_count = input_model.turn_count
            
            # Get decision style (default to analytical)
            decision_style = principal_ctx.get("decision_style", "analytical").lower()
            if decision_style not in STYLE_GUIDANCE:
                decision_style = "analytical"
            
            # Get principal role and ID
            principal_role = principal_ctx.get("role", "")
            principal_id = principal_ctx.get("principal_id", "system")

            # Route the topic sequence off the problem's measured structure
            topic_sequence, problem_profile, routing_rules = self._get_topic_sequence(da_output)
            profile_cell = problem_profile.cell_key() if problem_profile is not None else None
            if routing_rules:
                self.logger.info(
                    f"[REFINE] profile={profile_cell} routed_sequence={topic_sequence} rules={routing_rules}"
                )

            # Determine current topic. topics_completed is round-tripped by the
            # client (see the note where _extract_completed_topics was removed) —
            # never re-derived from prose.
            current_topic = input_model.current_topic
            topics_completed = list(input_model.topics_completed or [])

            if not current_topic:
                # First turn - start with first topic
                current_topic = topic_sequence[0]
            
            # Check for early exit commands
            if user_message and self._is_early_exit(user_message):
                # Accumulate refinements before finalizing
                accumulated = self._accumulate_refinements(
                    history, input_model.prior_constraint_items, input_model.prior_exclusions
                )
                return self._create_final_result(
                    da_output, principal_ctx, history, topics_completed, turn_count, accumulated,
                    profile_cell=profile_cell, topic_sequence=topic_sequence, routing_rules=routing_rules,
                )
            
            # Check for skip command
            topic_skipped = False
            if user_message and self._is_skip_command(user_message):
                topic_skipped = True
                topics_completed.append(current_topic)
                current_topic = self._get_next_topic(current_topic, topics_completed, topic_sequence)

            # Check max turns — budget scales with the routed sequence length so a
            # longer sequence cannot starve the topics Solution Finder consumes.
            _turn_budget = effective_turn_budget(topic_sequence)
            if turn_count >= _turn_budget:
                self.logger.info(
                    f"Max turns ({_turn_budget} for {len(topic_sequence)} topics) reached, finalizing refinement"
                )
                accumulated = self._accumulate_refinements(
                    history, input_model.prior_constraint_items, input_model.prior_exclusions
                )
                return self._create_final_result(
                    da_output, principal_ctx, history, topics_completed, turn_count, accumulated,
                    profile_cell=profile_cell, topic_sequence=topic_sequence, routing_rules=routing_rules,
                )

            # If all topics completed, finalize
            if current_topic is None or len(topics_completed) >= len(topic_sequence):
                accumulated = self._accumulate_refinements(
                    history, input_model.prior_constraint_items, input_model.prior_exclusions
                )
                return self._create_final_result(
                    da_output, principal_ctx, history, topics_completed, turn_count, accumulated,
                    profile_cell=profile_cell, topic_sequence=topic_sequence, routing_rules=routing_rules,
                )
            
            # Build KT summary for LLM context
            kt_summary = self._build_kt_summary(da_output)
            
            # Accumulate refinements from previous turns
            accumulated = self._accumulate_refinements(
                history, input_model.prior_constraint_items, input_model.prior_exclusions
            )

            # On turn 0, seed external_context with MA signals if provided
            if turn_count == 0 and input_model.initial_external_context:
                accumulated = self._merge_refinements(
                    accumulated,
                    ExtractedRefinements(external_context=list(input_model.initial_external_context))
                )
                # Auto-skip external_context topic — MA signals already provide this.
                # R4: EXCEPT when the profile reports a market conflict. A detected
                # disagreement between the market signal and the internal data is
                # precisely the case where the seeded text is insufficient — it is
                # the reason to ask, not a substitute for asking.
                _market_conflict = bool(problem_profile is not None and problem_profile.market_conflict)
                if _market_conflict:
                    routing_rules.append("R4:market_conflict -> keep external_context (no turn-0 auto-skip)")
                elif "external_context" not in topics_completed:
                    topics_completed.append("external_context")

            # If user provided a message, extract refinements from it
            extracted = ExtractedRefinements()
            if user_message and not topic_skipped:
                extracted = await self._extract_refinements_from_response(
                    user_message, current_topic, da_output, decision_style, principal_id
                )
                self.logger.info(f"[DA] Extracted refinements: ext_ctx={len(extracted.external_context)}, constraints={len(extracted.constraints)}, validated={len(extracted.validated_hypotheses)}")
                # Merge extracted into accumulated. Constraints from the interview
                # are stamped `source="refinement"` with the turn that produced them.
                accumulated = self._merge_refinements(
                    accumulated, extracted, source="refinement", turn_index=turn_count
                )
            
            # Check if topic is complete (via LLM or heuristics)
            topic_complete = False
            if user_message and not topic_skipped:
                topic_complete = await self._check_topic_complete(
                    current_topic, history, user_message, extracted,
                    turns_on_current_topic=input_model.turns_on_current_topic,
                )
            
            # Advance topic if complete
            if topic_complete:
                topics_completed.append(current_topic)
                current_topic = self._get_next_topic(current_topic, topics_completed, topic_sequence)
                
                # If no more topics, finalize
                if current_topic is None:
                    return self._create_final_result(
                        da_output, principal_ctx, history, topics_completed, turn_count,
                        accumulated,
                        profile_cell=profile_cell, topic_sequence=topic_sequence, routing_rules=routing_rules,
                    )
            
            # Generate next question via LLM
            agent_message, suggested_responses = await self._generate_refinement_question(
                current_topic=current_topic,
                decision_style=decision_style,
                kt_summary=kt_summary,
                history=history,
                user_message=user_message,
                accumulated=accumulated,
                principal_role=principal_role,
                principal_id=principal_id,
                da_output=da_output,
            )
            
            # Update conversation history
            new_history = list(history)
            if user_message:
                new_history.append({"role": "user", "content": user_message})
            new_history.append({"role": "assistant", "content": agent_message})
            
            return ProblemRefinementResult(
                agent_message=agent_message,
                suggested_responses=suggested_responses,
                exclusions=accumulated.exclusions,
                external_context=accumulated.external_context,
                constraints=accumulated.constraints,
                validated_hypotheses=accumulated.validated_hypotheses,
                invalidated_hypotheses=accumulated.invalidated_hypotheses,
                replication_constraints=accumulated.replication_constraints,
                current_topic=current_topic,
                topic_complete=topic_complete,
                topics_completed=topics_completed,
                ready_for_solutions=False,
                refined_problem_statement=None,
                recommended_council_type=None,
                council_routing_rationale=None,
                turn_count=turn_count + 1,
                conversation_history=new_history,
                constraint_items=accumulated.constraint_items,
                problem_profile_cell=profile_cell,
                topic_sequence=topic_sequence,
                topic_routing_rules_applied=routing_rules,
            )
            
        except Exception as e:
            self.logger.error(f"Error in refine_analysis: {e}")
            # Return a graceful error response
            return ProblemRefinementResult(
                agent_message=f"I encountered an issue processing your response. Let's continue - {str(e)[:100]}",
                suggested_responses=["Let's continue", "Skip this topic", "Proceed to solutions"],
                exclusions=[],
                external_context=[],
                constraints=[],
                validated_hypotheses=[],
                invalidated_hypotheses=[],
                current_topic=input_model.current_topic or REFINEMENT_TOPIC_SEQUENCE[0],
                topic_complete=False,
                topics_completed=[],
                ready_for_solutions=False,
                turn_count=input_model.turn_count + 1,
                conversation_history=input_model.conversation_history or [],
            )

    def _is_early_exit(self, message: str) -> bool:
        """Check if user wants to exit refinement early."""
        exit_phrases = [
            "proceed to solutions", "skip to solutions", "go to solutions",
            "done", "finish", "that's all", "let's move on", "ready for solutions"
        ]
        msg_lower = message.lower().strip()
        return any(phrase in msg_lower for phrase in exit_phrases)

    def _is_skip_command(self, message: str) -> bool:
        """Check if user wants to skip current topic."""
        skip_phrases = ["skip", "not applicable", "n/a", "next topic", "move on"]
        msg_lower = message.lower().strip()
        return any(phrase in msg_lower for phrase in skip_phrases)

    def _get_next_topic(self, current: str, completed: List[str], topic_sequence: List[str] = None) -> Optional[str]:
        """Get the next topic in sequence that hasn't been completed."""
        seq = topic_sequence or REFINEMENT_TOPIC_SEQUENCE
        try:
            current_idx = seq.index(current)
            for topic in seq[current_idx + 1:]:
                if topic not in completed:
                    return topic
        except ValueError:
            pass
        # Check if any earlier topics were skipped
        for topic in seq:
            if topic not in completed:
                return topic
        return None

    # REMOVED (Stage I B-1): `_extract_completed_topics(history)`.
    #
    # It scanned assistant messages for the literal substrings "moving to
    # {topic}" / "completed {topic}" — phrases nothing in the codebase
    # deterministically emits, so in practice it returned [] on every turn. It
    # also iterated the STATIC REFINEMENT_TOPIC_SEQUENCE, so it could never
    # recognise `replication_potential`, nor any of the problem-shape-routed
    # topics added by B-1.
    #
    # `topics_completed` is now round-tripped through the client, which already
    # held it (ProblemRefinementChat state) and simply never sent it back. The
    # server stays stateless. Recovering state by pattern-matching an LLM's prose
    # was the defect; asking the caller for the state it already has is the fix.

    @staticmethod
    def _format_kt_delta(delta: Any, unit: Optional[str]) -> str:
        """Render a KT driver delta in the KPI's OWN unit.

        A literal `$` used to be hardcoded into this block, so a percentage KPI
        rendered as currency: `gross_margin_pct` falling 7.14 percentage points
        printed as `$-7` in the context EVERY Solution Finder persona reads.

        Two separate defects, both material:

        * **Wrong unit.** `pp` presented as dollars. A principal who catches it
          stops trusting the system; one who does not is misinformed.
        * **Lost precision.** `:,.0f` collapsed the top two drivers (-7.14 and
          -6.61) onto the same `$-7`, destroying the ranking this block exists
          to convey.

        A delta of a percentage is percentage POINTS, never percent — a margin
        going 34.43% -> 29.94% moved 4.49pp, not 4.49%.
        """
        try:
            d = float(delta)
        except (TypeError, ValueError):
            return "n/a"
        u = (unit or "").strip().lower()
        if u in ("%", "pct", "percent", "percentage"):
            return f"{d:+,.2f}pp"
        if u in ("$", "usd"):
            return f"-${abs(d):,.0f}" if d < 0 else f"${d:,.0f}"
        return f"{d:+,.2f}{(' ' + unit.strip()) if unit else ''}"

    def _build_kt_summary(self, da_output: Dict[str, Any]) -> str:
        """Build a concise summary of KT IS/IS-NOT findings for LLM context."""
        summary_parts = []
        
        # Handle nested structure - execution may be inside da_output
        execution = da_output.get("execution", da_output)
        
        # Get KT data from execution
        kt = execution.get("kt_is_is_not", {})
        scqa = execution.get("scqa_summary", "")
        
        # Also get situation context if available
        situation = da_output.get("situation_context", {})
        if situation:
            kpi_name = situation.get("kpi_name", "")
            description = situation.get("description", "")
            if kpi_name:
                summary_parts.append(f"KPI: {kpi_name}")
            if description:
                summary_parts.append(f"Situation: {description}")
        
        if scqa:
            summary_parts.append(f"Summary: {scqa[:500]}")
        
        # Resolve the KPI's declared unit once. The deltas below are meaningless
        # without it, and guessing is what produced `$-7` for percentage points.
        plan = da_output.get("plan") or {}
        kpi_ref = plan.get("kpi_name") or (situation or {}).get("kpi_name")
        client_id = plan.get("client_id") or (situation or {}).get("client_id")
        kpi_unit = None
        if kpi_ref:
            kpi_rec = self._lookup_kpi_scoped(kpi_ref, client_id)
            kpi_unit = getattr(kpi_rec, "unit", None) if kpi_rec else None

        # Where IS (top drivers)
        where_is = kt.get("where_is", [])
        if where_is:
            top_drivers = where_is[:5]
            driver_strs = []
            for d in top_drivers:
                key = d.get("key", "Unknown")
                line = f"- {key}: {self._format_kt_delta(d.get('delta'), kpi_unit)}"
                # `percent_of_total` is NOT computed on the flat dimension path —
                # the key is absent from every entry. `.get(key, 0)` therefore
                # defaulted it and printed "(0.0% of variance)" against every
                # driver, telling each persona that the top driver explains none
                # of the problem. Omit the clause rather than assert a false zero.
                pct = d.get("percent_of_total")
                if isinstance(pct, (int, float)) and not isinstance(pct, bool):
                    line += f" ({pct:.1f}% of variance)"
                driver_strs.append(line)
            summary_parts.append("Top Drivers (WHERE IS):\n" + "\n".join(driver_strs))
        
        # Where IS NOT (stable segments)
        where_is_not = kt.get("where_is_not", [])
        if where_is_not:
            stable = where_is_not[:3]
            stable_strs = [f"- {s.get('key', 'Unknown')}" for s in stable]
            summary_parts.append("Stable Segments (WHERE IS NOT):\n" + "\n".join(stable_strs))
        
        # When started
        when_started = execution.get("when_started")
        if when_started:
            summary_parts.append(f"Issue started: {when_started}")
        
        return "\n\n".join(summary_parts) if summary_parts else "No KT analysis data available."

    async def _build_framing_prompt(
        self, da_output: Dict[str, Any], principal_ctx: Dict[str, Any]
    ) -> Optional[FramingPrompt]:
        """Build the mandatory framing gate's prompt (Phase 19), unwired —
        nothing calls this yet (Slice 2 of the implementation plan).

        Two evidence sources, shown together, never conflated (Decision #12):
        - the internal causal graph, 1-2 hops, UNFILTERED BY DIRECTION (the
          schema is undirected — see KPIRelationship's own docstring)
        - a Market Analysis conflict, when one was actually detected — MA's
          call timing is unchanged (still fires once, after DA's Is/Is-Not +
          change points exist, in workflows.py); what changes is that its
          output now feeds DA's own framing construction rather than only
          reaching Problem Refinement's external_context seed and SF's prompt.

        Returns None on ANY failure — no client_id, no resolvable KPI, a cold
        registry pool, a missing migration, a provider exception. ONE outer
        try/except around the whole body, deliberately — same posture as SF's
        existing causal-grounding block (a9_solution_finder_agent.py, the
        `if enable_causal_grounding:` block), which pre-initializes empty
        results and lets a single try/except cover the entire gather. Never
        partially fabricates a prompt; the caller must treat None as "the
        gate has nothing to show on this turn", not as an error to surface
        to the principal — a transient failure here means the gate simply
        doesn't render this turn, not that the interview breaks.
        """
        try:
            execution = da_output.get("execution", da_output)
            plan = da_output.get("plan") or {}
            situation = da_output.get("situation_context", {}) or {}
            kpi_ref = plan.get("kpi_name") or situation.get("kpi_name")
            client_id = plan.get("client_id") or situation.get("client_id")
            if not kpi_ref or not client_id:
                self.logger.info(
                    "[FRAMING] cannot build framing prompt — kpi_ref=%s client_id=%s", kpi_ref, client_id
                )
                return None

            kpi_rec = self._lookup_kpi_scoped(kpi_ref, client_id)
            if kpi_rec is None:
                self.logger.info(f"[FRAMING] KPI '{kpi_ref}' not resolvable for client '{client_id}'")
                return None
            kpi_id = getattr(kpi_rec, "id", None)
            kpi_name = getattr(kpi_rec, "name", None) or kpi_ref
            owner_role = getattr(kpi_rec, "owner_role", None)
            if not kpi_id:
                return None

            viewer_role = (principal_ctx or {}).get("role")
            viewer_is_owner = None
            if owner_role and viewer_role:
                viewer_is_owner = str(owner_role).strip().lower() == str(viewer_role).strip().lower()

            from src.registry.providers.kpi_relationship_provider import KPIRelationshipProvider
            from src.registry.providers.assumption_provider import AssumptionProvider

            alternatives: List[FramingAlternative] = []

            # --- Causal-graph alternatives: zero filtering, shortest-hop de-duplicated ---
            # No local try/except — a provider exception here (e.g. an
            # unmigrated schema) propagates to the outer catch and the whole
            # method returns None. Deliberate: see the docstring above.
            neighbourhood = await KPIRelationshipProvider().get_causal_neighbourhood(
                kpi_id, client_id, max_hops=2
            )

            # Replay the same visited-set walk get_causal_neighbourhood used
            # internally (its return shape doesn't expose which endpoint was
            # "new" at each hop) to identify, per edge, the neighbour KPI it
            # introduced. An edge connecting two already-visited nodes (a
            # cross-link) introduces no new candidate objective and is
            # skipped for THIS purpose — it doesn't stop being real evidence,
            # it's just not a distinct alternative.
            _visited = {kpi_id}
            for edge, hop in neighbourhood:
                neighbour = None
                if edge.kpi_id not in _visited:
                    neighbour = edge.kpi_id
                elif edge.related_kpi_id not in _visited:
                    neighbour = edge.related_kpi_id
                if neighbour is None:
                    continue
                _visited.add(neighbour)

                neighbour_rec = self._lookup_kpi_scoped(neighbour, client_id)
                neighbour_name = getattr(neighbour_rec, "name", None) or neighbour
                mechanism = getattr(edge, "mechanism", None)
                provenance = getattr(edge, "provenance", None) or "template"
                evidence_caveats: List[str] = []
                if not mechanism:
                    evidence_caveats.append(
                        "No causal mechanism recorded for this relationship — direction and pathway are not established."
                    )
                hop_word = "hop" if hop == 1 else "hops"
                alternatives.append(FramingAlternative(
                    source="causal_graph",
                    kpi_id=neighbour,
                    objective_text=(
                        f"Addressing {neighbour_name} instead of {kpi_name} directly — "
                        f"connected {hop} {hop_word} away in the causal graph"
                    ),
                    hops=hop,
                    relationship_type=getattr(edge, "relationship_type", None),
                    conflict_direction=getattr(edge, "conflict_direction", None),
                    lag_periods=getattr(edge, "lag_periods", None),
                    causal_rung=getattr(edge, "causal_rung", None),
                    confidence=getattr(edge, "confidence", None),
                    mechanism=mechanism,
                    direction_confirmed=False,
                    provenance=provenance,
                    provenance_caveat=_FRAMING_PROVENANCE_CAVEAT.get(provenance, ""),
                    evidence_caveats=evidence_caveats,
                ))

            # --- Market-signal alternative (Decision #12) ---
            # da_output carries `market_conflict` at the TOP level (sibling to
            # "plan"/"execution", not nested under "execution") — confirmed
            # against workflows.py's result_payload construction, the same
            # shape _build_kt_summary already reads "plan"/"situation_context"
            # from. Malformed or absent input produces zero alternatives here,
            # never a fabricated one — matches the empty-graph discipline above.
            market_conflict = da_output.get("market_conflict")
            if isinstance(market_conflict, dict) and market_conflict.get("detected") is True:
                summary_text = market_conflict.get("summary")
                if isinstance(summary_text, str) and summary_text.strip():
                    raw_confidence = market_conflict.get("confidence")
                    confidence_str = None
                    if isinstance(raw_confidence, (int, float)) and not isinstance(raw_confidence, bool):
                        confidence_str = f"{raw_confidence:.0%}"
                    alternatives.append(FramingAlternative(
                        source="market_signal",
                        kpi_id=None,
                        objective_text=summary_text.strip(),
                        hops=None,
                        confidence=confidence_str,
                        mechanism=None,
                        direction_confirmed=False,
                        evidence_caveats=[
                            "Independently generated by Market Analysis before comparison to this "
                            "KPI's conclusion — an external signal, not a causal claim about this KPI."
                        ],
                    ))
                else:
                    self.logger.info("[FRAMING] market_conflict.detected=True but summary missing/blank — skipping")

            # --- Active constraints (existing register entries for this KPI) ---
            # No local try/except — same reasoning as the causal graph above.
            active_constraints: List[ConstraintItem] = []
            _constraint_assumptions = await AssumptionProvider().get_active_constraints(client_id, scope=kpi_id)
            for a in (_constraint_assumptions or []):
                active_constraints.append(ConstraintItem(
                    id=constraint_id(a.text),
                    text=a.text,
                    source="assumption_register",
                ))

            # --- Prior frame, if one exists — never pre-ticked (Decision #5) ---
            prior_frame: Optional[PriorFrameRecord] = None
            _prior = await AssumptionProvider().get_active_framing(client_id, kpi_id)
            if _prior is not None:
                prior_frame = PriorFrameRecord(
                    id=_prior.id,
                    choice=_prior.framing_choice or "confirm_stated",
                    chosen_objective_text=_prior.text,
                    falsification_criterion=_prior.falsification_criterion,
                    decided_by_role=_prior.decided_by_role,
                    decided_by_is_owner=_prior.decided_by_is_owner,
                    decided_at=_prior.created_at,
                )

            stated_objective_text = f"Recovering {kpi_name}"
            question = (
                f"Is recovering {kpi_name} the right objective here, or does the evidence below "
                f"point to a different one?"
            )

            return FramingPrompt(
                kpi_id=kpi_id,
                kpi_name=kpi_name,
                stated_objective_text=stated_objective_text,
                question=question,
                alternatives=alternatives,
                active_constraints=active_constraints,
                owner_role=owner_role,
                viewer_role=viewer_role,
                viewer_is_owner=viewer_is_owner,
                prior_frame=prior_frame,
                requires_falsification_criterion=True,
            )
        except Exception as e:
            self.logger.info(f"[FRAMING] framing prompt unavailable (non-fatal): {e}")
            return None

    def _has_internal_benchmarks(self, da_output: Dict[str, Any]) -> bool:
        """True when DA classified at least one IS-NOT segment as a replication target."""
        execution = da_output.get("execution", da_output)
        kt = execution.get("kt_is_is_not", {})
        if not isinstance(kt, dict):
            kt = {}
        benchmark_segments = kt.get("benchmark_segments", []) or []
        return any(
            (s.get("benchmark_type") if isinstance(s, dict) else getattr(s, "benchmark_type", None)) == "internal_benchmark"
            for s in benchmark_segments
        )

    def _get_topic_sequence(self, da_output: Dict[str, Any]) -> Tuple[List[str], Optional[Any], List[str]]:
        """Route the interview topics off the problem's measured structure.

        Returns `(sequence, profile, rules_applied)`.

        WHY THIS EXISTS
        ---------------
        The interview ran a FIXED five-topic sequence regardless of what the
        analysis had already established. A concentrated single-segment problem
        and a diffuse enterprise one got the same five questions in the same
        order — so turns were spent asking what the data had already answered,
        and the questions that only a human could answer were never reached.

        `src/analysis/problem_profile.py` already classifies the structural
        facets deterministically and was consumed by nothing on any production
        path. This is its first live use. No LLM: the ROUTING is deterministic;
        only the wording of each question is generated.

        Every rule is justified by what the facet makes redundant or necessary,
        never by taste. `constraints` and `success_criteria` are never dropped —
        they are what Solution Finder consumes.
        """
        from src.analysis.problem_profile import classify

        base = list(REFINEMENT_TOPIC_SEQUENCE)
        if self._has_internal_benchmarks(da_output):
            base.append("replication_potential")

        try:
            profile = classify(da_output)
        except Exception as e:
            # A routing failure must never cost the principal their interview.
            self.logger.warning(f"[REFINE] problem_profile.classify failed, using base sequence: {e}")
            return base, None, []

        rules: List[str] = []
        seq = list(base)

        # --- R2 / R2': what concentration says about scope -------------------
        # A dominance ratio >= 2.0 means one segment is carrying the variance and
        # the data has ALREADY answered "which segments are in scope". Asking it
        # spends a turn to be told what we told them. Ask the question the
        # concentration raises instead: why THIS one.
        if profile.concentration == "concentrated":
            if "scope_boundaries" in seq:
                seq.remove("scope_boundaries")
            rules.append("R2:concentrated -> drop scope_boundaries, add segment_specific_causation")
        elif profile.concentration == "distributed":
            # Diffuse variance: scope genuinely IS the first question.
            if "scope_boundaries" in seq:
                seq.remove("scope_boundaries")
                seq.insert(0, "scope_boundaries")
                rules.append("R2':distributed -> scope_boundaries leads")

        # --- early-slot inserts, in fixed priority order ---------------------
        # All three want the position right after hypothesis_validation. The
        # order between them is fixed so the sequence is reproducible: the
        # cross-KPI tension is the most urgent framing question, then where to
        # look, then what to compare against.
        early: List[str] = []
        if profile.compound_alert:
            early.append("tradeoff_tolerance")
            rules.append("R1:compound_alert -> add tradeoff_tolerance")
        if profile.concentration == "concentrated":
            early.append("segment_specific_causation")
        if not profile.has_control_group:
            # KT diagnosis leans on contrast. An empty IS-NOT set means "why here
            # and not there" cannot be answered from the data at all — so the
            # contrast has to come from the principal or the interview produces
            # nothing diagnostic.
            early.append("comparison_baseline")
            rules.append("R3:no_control_group -> add comparison_baseline")

        if early:
            anchor = seq.index("hypothesis_validation") if "hypothesis_validation" in seq else -1
            for offset, topic in enumerate(early):
                if topic not in seq:
                    seq.insert(anchor + 1 + offset, topic)

        # --- R5: replication barriers ARE constraints ------------------------
        if profile.mode == "opportunity" and "replication_potential" in seq and "constraints" in seq:
            if seq.index("replication_potential") > seq.index("constraints"):
                seq.remove("replication_potential")
                seq.insert(seq.index("constraints"), "replication_potential")
                rules.append("R5:opportunity -> replication_potential before constraints")

        # --- cap, protecting what SF consumes --------------------------------
        if len(seq) > MAX_TOPICS_IN_SEQUENCE:
            trimmed = list(seq)
            for topic in reversed(seq):
                if len(trimmed) <= MAX_TOPICS_IN_SEQUENCE:
                    break
                if topic not in PROTECTED_TOPICS:
                    trimmed.remove(topic)
            rules.append(f"CAP:{len(seq)}->{len(trimmed)} (protected: {sorted(PROTECTED_TOPICS)})")
            seq = trimmed

        return seq, profile, rules

    def _build_benchmark_summary(self, da_output: Dict[str, Any]) -> str:
        """Build a summary of internal benchmark segments for the replication_potential topic."""
        execution = da_output.get("execution", da_output)
        kt = execution.get("kt_is_is_not", {})
        if not isinstance(kt, dict):
            return ""
        benchmark_segments = kt.get("benchmark_segments", [])
        internal = []
        for s in (benchmark_segments or []):
            seg = s if isinstance(s, dict) else (s.model_dump() if hasattr(s, "model_dump") else {})
            if seg.get("benchmark_type") == "internal_benchmark":
                internal.append(seg)
        if not internal:
            return ""
        lines = ["Internal Benchmark Segments (Replication Targets):"]
        for seg in internal[:5]:
            key = seg.get("key", "Unknown")
            delta = seg.get("delta", 0)
            rep = seg.get("replication_potential")
            rep_str = f" | replication potential: {rep:.0%}" if rep is not None else ""
            try:
                lines.append(f"- {seg.get('dimension', '')} = {key}: delta {delta:+,.0f}{rep_str}")
            except Exception:
                lines.append(f"- {seg.get('dimension', '')} = {key}: delta {delta}{rep_str}")
        return "\n".join(lines)

    def _accumulate_refinements(
        self,
        history: List[Dict[str, str]],
        prior_constraint_items: Optional[List[ConstraintItem]] = None,
        prior_exclusions: Optional[List[RefinementExclusion]] = None,
    ) -> ExtractedRefinements:
        """Rebuild accumulated refinements from prior turns.

        WHAT THIS USED TO DO, AND WHY IT WAS WRONG
        ------------------------------------------
        It replayed every user message through `_simple_extraction(msg,
        "general")` — the KEYWORD extractor — discarding the structured output
        the LLM had already produced on those turns and re-deriving it by
        substring matching. Two consequences:

          * `exclusions` were lost permanently. The "general" branch never
            populates them, so an exclusion captured on turn 2 did not exist by
            turn 3, and the principal's "leave International out of this" was
            silently dropped from the problem statement.
          * Provenance could not survive. A keyword match has no idea which
            persona's extractor surfaced an item, so per-persona constraint sets
            were impossible to build on top of it.

        Now the client echoes back the typed state it already holds, and the
        keyword replay is the fallback for callers that do not send it. The
        endpoint stays stateless — we ask the caller for state it has, rather
        than reconstructing it from prose.
        """
        accumulated = ExtractedRefinements(
            constraints=[c.text for c in (prior_constraint_items or [])],
            constraint_items=list(prior_constraint_items or []),
            exclusions=list(prior_exclusions or []),
        )

        if prior_constraint_items or prior_exclusions:
            # Caller supplied typed state; do not re-derive it heuristically.
            return accumulated

        for msg in history:
            if msg.get("role") == "user":
                user_text = msg.get("content", "")
                extracted = self._simple_extraction(user_text, "general")
                accumulated = self._merge_refinements(accumulated, extracted)

        return accumulated

    def _merge_refinements(
        self,
        accumulated: ExtractedRefinements,
        extracted: ExtractedRefinements,
        source: str = "refinement",
        turn_index: Optional[int] = None,
        discovered_by: Optional[List[str]] = None,
    ) -> ExtractedRefinements:
        """Merge newly extracted refinements into accumulated.

        Constraint texts arriving without a typed item get one minted here, so
        `constraint_items` stays a complete mirror of `constraints` no matter
        which extraction path produced them. Merging is by `ConstraintItem.id`:
        a constraint restated on a later turn unions its `discovered_by` rather
        than appearing twice.
        """
        merged_items: Dict[str, ConstraintItem] = {c.id: c for c in accumulated.constraint_items}

        for item in extracted.constraint_items:
            existing = merged_items.get(item.id)
            if existing is None:
                merged_items[item.id] = item
            else:
                existing.discovered_by = sorted(set(existing.discovered_by) | set(item.discovered_by))

        for text in extracted.constraints:
            cid = constraint_id(text)
            if cid in merged_items:
                if discovered_by:
                    merged_items[cid].discovered_by = sorted(
                        set(merged_items[cid].discovered_by) | set(discovered_by)
                    )
                continue
            merged_items[cid] = ConstraintItem(
                id=cid,
                text=text,
                source=source,
                discovered_by=list(discovered_by or []),
                turn_index=turn_index,
            )

        return ExtractedRefinements(
            exclusions=accumulated.exclusions + extracted.exclusions,
            external_context=accumulated.external_context + extracted.external_context,
            constraints=[c.text for c in merged_items.values()],
            validated_hypotheses=accumulated.validated_hypotheses + extracted.validated_hypotheses,
            invalidated_hypotheses=accumulated.invalidated_hypotheses + extracted.invalidated_hypotheses,
            replication_constraints=accumulated.replication_constraints + extracted.replication_constraints,
            constraint_items=list(merged_items.values()),
        )

    async def _extract_refinements_from_response(
        self,
        user_message: str,
        current_topic: str,
        da_output: Dict[str, Any],
        decision_style: str,
        principal_id: str = "system",
    ) -> ExtractedRefinements:
        """Use LLM to extract structured refinements from user's response."""
        if not self.llm_service_agent:
            # Fallback: simple keyword extraction
            return self._simple_extraction(user_message, current_topic)
        
        try:
            from src.agents.new.a9_llm_service_agent import A9_LLM_Request
            from src.llm_services.claude_service import get_claude_model_for_task, ClaudeTaskType

            extraction_prompt = f"""Extract structured refinements from the user's response.

User's response: "{user_message}"
Current topic: {current_topic}

Extract any of the following that are mentioned:
1. EXCLUSIONS: Segments, dimensions, or time periods to exclude (format: dimension|value|reason)
2. EXTERNAL_CONTEXT: External factors mentioned (market changes, supplier issues, etc.)
3. CONSTRAINTS: Actions or levers that are off-limits
4. VALIDATED: Hypotheses or drivers the user confirmed as real issues
5. INVALIDATED: Hypotheses or drivers the user said are known/expected/not relevant
6. REPLICATION_CONSTRAINTS: Structural barriers preventing replication of benchmark segments (capacity, contracts, timing, resources) — extract only when current_topic is 'replication_potential'

Respond in JSON format:
{{
  "exclusions": [{{"dimension": "...", "value": "...", "reason": "..."}}],
  "external_context": ["..."],
  "constraints": ["..."],
  "validated_hypotheses": ["..."],
  "invalidated_hypotheses": ["..."],
  "replication_constraints": ["..."]
}}

If nothing relevant is found for a category, use an empty list."""

            request = A9_LLM_Request(
                request_id=str(uuid.uuid4()),
                principal_id=principal_id,
                prompt=extraction_prompt,
                operation="generate",
                temperature=0.1,  # Low temperature for structured extraction
                # Haiku: pure JSON classification — no reasoning needed (overridable via CLAUDE_MODEL_NLP)
                model=get_claude_model_for_task(ClaudeTaskType.NLP_PARSING),
            )
            
            response = await self.llm_service_agent.generate(request)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON from response
            import json
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return ExtractedRefinements(
                    exclusions=[
                        RefinementExclusion(**e) for e in data.get("exclusions", [])
                    ],
                    external_context=data.get("external_context", []),
                    constraints=data.get("constraints", []),
                    validated_hypotheses=data.get("validated_hypotheses", []),
                    invalidated_hypotheses=data.get("invalidated_hypotheses", []),
                    replication_constraints=data.get("replication_constraints", []),
                )
        except Exception as e:
            self.logger.warning(f"LLM extraction failed, using simple extraction: {e}")
        
        return self._simple_extraction(user_message, current_topic)

    async def _safe_generate_scqa_summary(self, **kwargs) -> Optional[str]:
        """Call `_generate_scqa_summary`; on any exception, return None rather
        than a fabricated frame.

        Extracted from `execute_deep_analysis()` (2026-08-17) so this specific
        behavior — absence on failure, never a hardcoded question — is unit
        testable on its own. Nothing in this test suite drives
        `execute_deep_analysis()` end to end (it is an ~850-line orchestration
        method), so the try/except living inline there was, in practice,
        untestable; a regression could only ever have been caught live.

        DO NOT REINSTATE A FALLBACK QUESTION HERE.

        This used to emit:
          "... Question: Which segments drive the change?"

        SCQA is a framing device — its Q *is* the frame — so that line asserted
        a dimensional-attribution frame as a CONSTANT whenever generation
        failed, and every downstream stage (the council, the moderator, HITL)
        then answered it faithfully. A frame with no author is the exact defect
        `problem_framing_design.md` exists to close, and this was its worst
        instance: not merely unexamined, but hardcoded on the error path where
        nobody would look.

        Absence is the honest output. Downstream already treats a missing
        scqa_summary as missing; a fabricated one is indistinguishable from a
        real one to every consumer.
        """
        try:
            return await self._generate_scqa_summary(**kwargs)
        except Exception as _scqa_err:
            self.logger.warning("[DA] SCQA generation failed: %s", _scqa_err)
            return None

    async def _generate_scqa_summary(
        self,
        plan: "DeepAnalysisPlan",
        kt: "KTIsIsNot",
        change_points: List["ChangePoint"],
        spec: Optional[Dict[str, Any]],
        principal_id: str,
        analysis_mode: str = "problem",
        alert_type: Optional[str] = None,
        compound_pattern: Optional[str] = None,
        matrix_ran: bool = False,
        comparator_secondary: Optional[str] = None,
        kpi_unit: Optional[str] = None,
    ) -> str:
        """Generate a Situation-Complication-Question-Answer narrative via LLM.

        Falls back to a deterministic summary if the LLM call fails. When `matrix_ran`,
        the narrative reads ACROSS the segment × basis matrix (one enriched table) — leading
        with `confirmed` segments (adverse on both bases), flagging `basis_specific` ones as
        probable comparison artifacts, and surfacing any `secondary_only` segments — rather
        than diagnosing a single basis.
        """
        import json as _json

        def _basis_label(c: Optional[str]) -> str:
            return "Budget/Plan" if c == "budget" else "prior period"

        # Percentage-point deltas need a "pp" suffix, not the bare "%" unit (which
        # reads as a percentage of the delta itself, not percentage points) or a
        # dollar sign (matches the fix already applied on the frontend for the
        # same class of bug — see decision-studio-ui DeepFocusView.tsx formatDelta).
        _delta_unit = "pp" if kpi_unit == "%" else (kpi_unit or "")
        def _fmt_delta(v: float) -> str:
            return f"{v:.1f}{_delta_unit}" if _delta_unit else f"{v:.1f}"

        # Matrix tier buckets (only meaningful when matrix_ran) — segment keys per cross-basis tier.
        _rows_all = [r for r in ((getattr(kt, "where_is", []) or []) + (getattr(kt, "where_is_not", []) or [])) if isinstance(r, dict)]
        _confirmed = [r.get("key", "") for r in _rows_all if r.get("basis_agreement") == "confirmed"][:5]
        _basis_specific = [r.get("key", "") for r in _rows_all if r.get("basis_agreement") == "basis_specific"][:5]
        _secondary_only = [r.get("key", "") for r in _rows_all if r.get("basis_agreement") == "secondary_only"][:5]

        # Build compact context strings from available data
        # DA agent populates where_is/where_is_not (dimensional segments), not what_is/what_is_not
        is_items = [r.get("key", "") for r in (getattr(kt, "where_is", []) or []) if isinstance(r, dict)][:5]
        is_not_items = [r.get("key", "") for r in (getattr(kt, "where_is_not", []) or []) if isinstance(r, dict)][:5]
        top_cps = [
            f"{cp.dimension}={cp.key} ({cp.delta:+.1f})" if cp.delta is not None else f"{cp.dimension}={cp.key}"
            for cp in (change_points or [])[:4]
            if cp.dimension and cp.key
        ]
        comparator = (spec or {}).get("comparison_type", "prior period")
        inv = (spec or {}).get("inverse_logic", False)
        # For problem mode: direction describes the adverse condition ("under" for revenue, "over" for cost).
        # For opportunity mode: direction is inverted — the KPI is doing better than expected.
        if analysis_mode == "opportunity":
            direction = "under" if inv else "over"
        else:
            direction = "over" if inv else "under"

        # Deterministic fallback (used when LLM unavailable or fails)
        def _fallback() -> str:
            is_str = ", ".join(is_items) if is_items else "leading segments"
            is_not_str = ", ".join(is_not_items) if is_not_items else "remaining segments"
            cp_str = "; ".join(top_cps) if top_cps else "key contributors identified"
            # Matrix branch takes priority — one narrative read ACROSS the two cross-sectional bases.
            if matrix_ran and (_confirmed or _basis_specific):
                _prim = _basis_label(comparator)
                _sec = _basis_label(comparator_secondary)
                _conf_str = ", ".join(_confirmed) if _confirmed else "no segments"
                _bs_str = ", ".join(_basis_specific) if _basis_specific else None
                parts = [
                    f"Situation: {plan.kpi_name} breached on two bases — vs {_prim} and vs {_sec}.",
                    (f"Complication: {_conf_str} are adverse on BOTH bases — the genuine problem to solve."
                     if _confirmed else
                     f"Complication: no segment is adverse on both bases — the breach is basis-specific."),
                ]
                if _bs_str:
                    parts.append(
                        f"Note: {_bs_str} are adverse vs {_prim} but on-track vs {_sec} — likely a comparison-timing artifact, not a root-cause problem."
                    )
                if _secondary_only:
                    parts.append(
                        f"Also: {', '.join(_secondary_only)} look fine vs {_prim} but are adverse vs {_sec} — surfaced only by the second basis."
                    )
                parts.append(
                    f"Question: What actions address the {_conf_str} problem confirmed across both bases?"
                )
                return " ".join(parts)
            if analysis_mode == "opportunity":
                return (
                    f"Situation: {plan.kpi_name} is {direction}-performing vs. {comparator}. "
                    f"Complication: The outperformance is concentrated in {is_str} — creating a replication opportunity in {is_not_str}. "
                    f"Key drivers: {cp_str}. "
                    f"Question: How do we scale the {is_str} performance across {is_not_str}?"
                )
            if analysis_mode == "mixed":
                _where_is_rows = [r for r in (getattr(kt, "where_is", []) or []) if isinstance(r, dict)]
                problem_segs = [r.get("key", "") for r in _where_is_rows if r.get("segment_type") == "problem"][:3]
                opp_segs = [r.get("key", "") for r in _where_is_rows if r.get("segment_type") == "opportunity"][:3]
                net_problem = sum(abs(r.get("delta") or 0) for r in _where_is_rows if r.get("segment_type") == "problem")
                net_opp = sum(abs(r.get("delta") or 0) for r in _where_is_rows if r.get("segment_type") == "opportunity")
                prob_str = ", ".join(problem_segs) if problem_segs else "underperforming segments"
                opp_str = ", ".join(opp_segs) if opp_segs else "outperforming segments"
                # Magnitude-aware ordering — don't default to "fix the problem first"
                # when the opportunity is the materially larger number (same net-delta
                # comparison the Action Center's "Let Agent9 Decide" button already makes).
                if net_opp > net_problem * 3:
                    question = f"Question: How do we scale the {opp_str} performance while keeping {prob_str} from widening further?"
                    answer = (
                        f"Answer: Prioritise scaling the {opp_str} playbook — the opportunity "
                        f"({_fmt_delta(net_opp)} combined) is far larger than the drag from {prob_str} "
                        f"({_fmt_delta(net_problem)} combined), which merits monitoring but not the primary response."
                    )
                elif net_problem > net_opp * 3:
                    question = f"Question: How do we arrest the decline in {prob_str} before addressing the smaller {opp_str} opportunity?"
                    answer = (
                        f"Answer: Prioritise recovery in {prob_str} — the drag ({_fmt_delta(net_problem)} combined) "
                        f"far outweighs the {opp_str} opportunity ({_fmt_delta(net_opp)} combined) this period."
                    )
                else:
                    question = "Question: How do we address the laggards while scaling the leaders simultaneously?"
                    answer = (
                        f"Answer: Prioritise recovery in {prob_str} and replicate the {opp_str} playbook across similar "
                        f"segments — the two are comparable in size ({_fmt_delta(net_problem)} vs {_fmt_delta(net_opp)}) "
                        f"and both merit attention."
                    )
                return (
                    f"Situation: {plan.kpi_name} shows mixed performance vs. the comparison period. "
                    f"Complication: Performance is bifurcated — {prob_str} are dragging results while "
                    f"{opp_str} are outperforming. "
                    f"{question} "
                    f"{answer}"
                )
            # Problem mode — apply alert-type-aware framing
            if compound_pattern:
                complication = (
                    f"Complication: {compound_pattern} — "
                    f"the cross-KPI divergence suggests a structural issue beyond a single segment. "
                    f"Dimensional breakdown: {is_str}."
                )
            elif alert_type == "projected_breach":
                complication = (
                    f"Complication: The trend is on trajectory to breach the threshold in the next period(s) — "
                    f"deterioration is concentrated in {is_str}."
                )
            elif alert_type == "plan_variance":
                complication = (
                    f"Complication: Performance is tracking below plan, with the budget gap driven by {is_str}, "
                    f"while {is_not_str} are on target."
                )
            elif alert_type == "acceleration":
                complication = (
                    f"Complication: The rate of decline is accelerating — the variance in {is_str} "
                    f"is widening period-over-period, not just persisting."
                )
            else:
                complication = (
                    f"Complication: The variance is concentrated in {is_str}, while {is_not_str} are within range."
                )
            # Build situation prefix based on alert_type
            if alert_type == "projected_breach":
                situation_prefix = f"Situation: {plan.kpi_name} is trending toward a threshold breach vs. {comparator}."
            elif alert_type == "plan_variance":
                situation_prefix = f"Situation: {plan.kpi_name} is tracking below plan vs. {comparator}."
            else:
                situation_prefix = f"Situation: {plan.kpi_name} is {direction}-performing vs. {comparator}."
            return (
                f"{situation_prefix} "
                f"{complication} "
                f"Key drivers: {cp_str}. "
                f"Question: What actions can address the identified contributors?"
            )

        try:
            from src.agents.new.a9_llm_service_agent import A9_LLM_Request
            from src.llm_services.claude_service import get_claude_model_for_task, ClaudeTaskType

            if analysis_mode == "opportunity":
                prompt = (
                    f"Write a concise SCQA narrative for a CFO reviewing a GROWTH OPPORTUNITY in "
                    f"'{plan.kpi_name}' ({plan.timeframe or 'current period'}).\n\n"
                    f"Leading segments (IS — the blueprint to replicate): {', '.join(is_items) or 'see change points'}\n"
                    f"Segments with unrealised potential (IS NOT — replication targets): "
                    f"{', '.join(is_not_items) or 'none identified'}\n"
                    f"Largest change-points: {'; '.join(top_cps) or 'none'}\n\n"
                    f"CRITICAL FRAMING RULES:\n"
                    f"- This is an OPPORTUNITY card. The KPI is OUTPERFORMING overall.\n"
                    f"- The IS segments are the SUCCESS STORY. Lead with what they are doing RIGHT.\n"
                    f"- Do NOT use words like 'underperform', 'underperformance', 'decline', 'problem'.\n"
                    f"- The IS NOT segments have UNREALISED POTENTIAL, not a failure.\n"
                    f"- The Question and Answer must be about REPLICATING the IS success, not fixing IS NOT.\n\n"
                    f"Output exactly 4 labelled sentences with no preamble: "
                    f"'Situation:', 'Complication:', 'Question:', 'Answer:'. "
                    f"Be specific and quantitative. No bullet points. No headers."
                )
            elif analysis_mode == "mixed":
                _where_is_rows_p = [r for r in (getattr(kt, "where_is", []) or []) if isinstance(r, dict)]
                problem_segs = [r.get("key", "") for r in _where_is_rows_p if r.get("segment_type") == "problem"][:3]
                opp_segs = [r.get("key", "") for r in _where_is_rows_p if r.get("segment_type") == "opportunity"][:3]
                net_problem = sum(abs(r.get("delta") or 0) for r in _where_is_rows_p if r.get("segment_type") == "problem")
                net_opp = sum(abs(r.get("delta") or 0) for r in _where_is_rows_p if r.get("segment_type") == "opportunity")
                # Don't hardcode "fix laggards first" regardless of size — that produced
                # recommendations focused on a 2.9pp problem while ignoring a 98pp+
                # opportunity sitting right next to it. Let relative magnitude drive
                # which gets primary billing in the Answer.
                if net_opp > net_problem * 3:
                    _magnitude_rule = (
                        f"- The opportunity ({_fmt_delta(net_opp)} combined) is FAR LARGER than the problem "
                        f"({_fmt_delta(net_problem)} combined) — at least 3x. The Answer's PRIMARY recommendation "
                        f"must be to SCALE the opportunity. Mention the laggard as something to monitor/contain "
                        f"in parallel, not as the primary action.\n"
                    )
                elif net_problem > net_opp * 3:
                    _magnitude_rule = (
                        f"- The problem ({_fmt_delta(net_problem)} combined) is FAR LARGER than the opportunity "
                        f"({_fmt_delta(net_opp)} combined) — at least 3x. The Answer's PRIMARY recommendation "
                        f"must be to FIX the laggard. Mention the replication opportunity as a secondary/parallel "
                        f"action, not the primary one.\n"
                    )
                else:
                    _magnitude_rule = (
                        f"- Problem ({_fmt_delta(net_problem)}) and opportunity ({_fmt_delta(net_opp)}) are "
                        f"comparable in size — the Answer should give both recovery and replication roughly "
                        f"equal billing.\n"
                    )
                prompt = (
                    f"Write a concise SCQA narrative for a CFO reviewing MIXED performance in "
                    f"'{plan.kpi_name}' ({plan.timeframe or 'current period'}).\n\n"
                    f"Underperforming segments (need recovery): {', '.join(problem_segs) or 'see change points'} "
                    f"— combined magnitude {_fmt_delta(net_problem)}\n"
                    f"Outperforming segments (replication blueprints): {', '.join(opp_segs) or 'see change points'} "
                    f"— combined magnitude {_fmt_delta(net_opp)}\n"
                    f"Largest change-points: {'; '.join(top_cps) or 'none'}\n\n"
                    f"FRAMING RULES:\n"
                    f"- This is a MIXED situation. Both problems and opportunities exist simultaneously.\n"
                    f"- Complication must name BOTH the drag from laggards AND the opportunity from leaders.\n"
                    f"{_magnitude_rule}"
                    f"- Do not default to 'fix the problem first' when the numbers say otherwise — lead with "
                    f"whichever is materially larger.\n\n"
                    f"Output exactly 4 labelled sentences: 'Situation:', 'Complication:', 'Question:', 'Answer:'. No bullet points."
                )
            else:
                # Build alert-type context for the prompt
                _alert_context = ""
                if matrix_ran and (_confirmed or _basis_specific):
                    _prim_l = _basis_label(comparator)
                    _sec_l = _basis_label(comparator_secondary)
                    _alert_context = (
                        f"\n\nCRITICAL FRAMING — TWO-BASIS SEGMENT MATRIX: This KPI breached vs {_prim_l} AND vs {_sec_l}. "
                        f"Each segment has been cross-classified across both bases:\n"
                        f"- CONFIRMED (adverse on both — the real problem): {', '.join(_confirmed) or 'none'}\n"
                        f"- BASIS-SPECIFIC (adverse on {_prim_l} but on-track vs {_sec_l} — likely a comparison-timing artifact, NOT a root cause): {', '.join(_basis_specific) or 'none'}\n"
                        f"- SECONDARY-ONLY (fine vs {_prim_l} but adverse vs {_sec_l}): {', '.join(_secondary_only) or 'none'}\n"
                        f"The Complication MUST lead with the CONFIRMED segments as the genuine problem, and MUST explicitly "
                        f"note that BASIS-SPECIFIC segments are probably a timing/budget artifact so they are not chased. "
                        f"Do NOT treat a segment that is only adverse on one basis as a confirmed problem."
                    )
                elif compound_pattern:
                    _alert_context = (
                        f"\n\nCRITICAL FRAMING — COMPOUND ALERT: This situation involves a cross-KPI conflict: {compound_pattern}. "
                        f"The Complication MUST lead with this cross-KPI tension before naming dimensional segments. "
                        f"Example Complication: 'Despite revenue growing 8%, gross margin declined 3pp — "
                        f"the divergence suggests a mix shift or pricing compression, not a volume problem.'"
                    )
                elif alert_type == "projected_breach":
                    _alert_context = (
                        f"\n\nCRITICAL FRAMING — PROJECTED BREACH: This KPI has not yet breached its threshold "
                        f"but is on trajectory to do so. The Situation must say 'is trending toward breach' "
                        f"rather than 'has breached'. The Complication must name which dimensional segments are "
                        f"driving the projected deterioration."
                    )
                elif alert_type == "plan_variance":
                    _alert_context = (
                        f"\n\nCRITICAL FRAMING — PLAN VARIANCE: The trigger is a miss vs. the budget/plan baseline, "
                        f"not a threshold breach. The Situation must reference the plan miss (e.g. 'is tracking "
                        f"below plan'). The Complication must identify which segments are responsible for the "
                        f"budget gap."
                    )
                elif alert_type == "acceleration":
                    _alert_context = (
                        f"\n\nCRITICAL FRAMING — ACCELERATION: The rate of deterioration is increasing, not just "
                        f"the level. The Complication must note that the decline is accelerating, not just present."
                    )
                prompt = (
                    f"Write a concise SCQA (Situation-Complication-Question-Answer) narrative for a CFO "
                    f"investigating the KPI '{plan.kpi_name}' ({plan.timeframe or 'current period'}).\n\n"
                    f"Comparator: {comparator} | Direction: {direction}-performing vs target\n"
                    f"Top problem segments (IS): {', '.join(is_items) or 'see change points'}\n"
                    f"Healthy segments (IS NOT): {', '.join(is_not_items) or 'none identified'}\n"
                    f"Largest change-points: {'; '.join(top_cps) or 'none'}"
                    f"{_alert_context}\n\n"
                    f"Output exactly 4 labelled sentences: 'Situation: ...', 'Complication: ...', "
                    f"'Question: ...', 'Answer: ...'. Be specific and quantitative. No bullet points."
                )

            req = A9_LLM_Request(
                request_id=str(uuid.uuid4()),
                principal_id=principal_id,
                prompt=prompt,
                operation="generate",
                temperature=0.3,
                model=get_claude_model_for_task(ClaudeTaskType.NLP_PARSING),
            )
            resp = await self.llm_service_agent.generate(req)
            content = (getattr(resp, "content", "") or "").strip()

            # Strip LLM-added preamble before the SCQA (e.g. "# SCQA Narrative: ...")
            if "Situation:" in content:
                content = content[content.index("Situation:"):].strip()
            # Strip LLM artifact metadata appended after the SCQA (e.g. "---\n**VERIFIED_ACTION:** N/A")
            for _sep in ["\n---", "\n\n---"]:
                if _sep in content:
                    content = content[:content.index(_sep)].strip()
                    break

            # Accept only if it looks like a real SCQA (has all 4 labels and no placeholder brackets)
            if (content and "Situation:" in content and "Complication:" in content
                    and "[" not in content and "MISSING" not in content
                    and "please provide" not in content.lower()
                    and "missing" not in content.lower()):
                # For opportunity mode: reject if the LLM slipped into problem framing
                problem_framing = any(
                    w in content.lower()
                    for w in [
                        "under-performing", "underperforming", "underperformance",
                        "declined", "decreasing", "falling short",
                    ]
                )
                if analysis_mode == "opportunity" and problem_framing:
                    self.logger.info("[DA] SCQA LLM returned problem framing for opportunity mode — using deterministic fallback")
                else:
                    # mixed mode accepts both problem and opportunity language; problem mode has no framing restriction
                    return content
            self.logger.info("[DA] SCQA LLM returned placeholder/incomplete — using deterministic fallback")
        except Exception as _e:
            self.logger.warning("[DA] SCQA LLM call failed, using deterministic fallback: %s", _e)

        return _fallback()

    def _simple_extraction(self, user_message: str, current_topic: str) -> ExtractedRefinements:
        """Simple keyword-based extraction fallback."""
        msg_lower = user_message.lower()
        result = ExtractedRefinements()
        
        # Skip very short responses or skip commands
        if len(user_message) < 10 or "skip" in msg_lower or "proceed" in msg_lower:
            return result
        
        # For "general" topic (used when accumulating from history), use keyword detection
        if current_topic == "general":
            # Detect constraints
            if any(kw in msg_lower for kw in ["can't", "cannot", "won't", "off the table", "not possible", "budget", "timeline"]):
                result.constraints.append(user_message[:300])
            # Detect external context
            elif any(kw in msg_lower for kw in ["supplier", "market", "competitor", "pricing", "change", "external", "economy"]):
                result.external_context.append(user_message[:300])
            # Detect validation
            elif any(kw in msg_lower for kw in ["yes", "correct", "right", "confirms", "align", "understand", "agree"]):
                result.validated_hypotheses.append(user_message[:300])
            # Detect invalidation
            elif any(kw in msg_lower for kw in ["no", "wrong", "incorrect", "known", "expected", "not surprising", "aware"]):
                result.invalidated_hypotheses.append(user_message[:300])
            # Default: treat substantive responses as context
            elif len(user_message) > 30:
                result.external_context.append(user_message[:300])
            return result
        
        # Based on current topic, categorize the response
        if current_topic == "hypothesis_validation":
            # Look for validation/invalidation signals
            if any(kw in msg_lower for kw in ["yes", "correct", "right", "confirms", "align", "understand", "agree"]):
                result.validated_hypotheses.append(user_message[:300])
            elif any(kw in msg_lower for kw in ["no", "wrong", "incorrect", "known", "expected", "not surprising", "aware"]):
                result.invalidated_hypotheses.append(user_message[:300])
            else:
                # Default: treat as context
                result.external_context.append(user_message[:300])
        
        elif current_topic == "external_context":
            # Capture as external context
            result.external_context.append(user_message[:300])
        
        elif current_topic == "scope_boundaries":
            # Look for exclusion signals
            if any(kw in msg_lower for kw in ["exclude", "ignore", "remove", "not include", "focus on"]):
                result.external_context.append(f"Scope: {user_message[:300]}")
            else:
                result.external_context.append(user_message[:300])
        
        elif current_topic == "constraints":
            # Capture as constraints
            result.constraints.append(user_message[:300])
        
        else:
            # Default: external context
            if len(user_message) > 20:
                result.external_context.append(user_message[:300])
        
        return result

    async def _check_topic_complete(
        self,
        current_topic: str,
        history: List[Dict[str, str]],
        user_message: str,
        extracted: ExtractedRefinements,
        turns_on_current_topic: int = 0,
    ) -> bool:
        """Determine if the current topic has been sufficiently covered.

        `turns_on_current_topic` is maintained by the caller and reset whenever
        `current_topic` changes. It previously counted EVERY assistant message in
        the conversation — not messages since the last topic change — so from
        turn 3 onward every topic auto-completed on arrival regardless of what
        the principal had said. Under B-1's routed sequences that would have
        raced the routing: a topic added because the problem's shape demanded it
        would be marked complete before it was ever properly asked.
        """
        # Auto-complete if max turns on THIS topic reached
        if turns_on_current_topic >= MAX_TURNS_PER_TOPIC:
            return True
        
        # Topic-specific completion heuristics
        if current_topic == "hypothesis_validation":
            # Complete if user validated or invalidated at least one hypothesis
            if extracted.validated_hypotheses or extracted.invalidated_hypotheses:
                return True
        
        elif current_topic == "scope_boundaries":
            # Complete if user specified any exclusions
            if extracted.exclusions:
                return True
        
        elif current_topic == "external_context":
            # Complete if user provided context or said "none"
            if extracted.external_context or "none" in user_message.lower() or "no" == user_message.lower().strip():
                return True
        
        elif current_topic == "constraints":
            # Complete if user provided constraints or said "none"
            if extracted.constraints or "none" in user_message.lower() or "no" == user_message.lower().strip():
                return True
        
        elif current_topic == "success_criteria":
            # Complete if user provided any success criteria
            if len(user_message) > 20:  # Assume substantive response
                return True

        elif current_topic == "replication_potential":
            # Complete if user gave any substantive answer (template valid or identified barriers)
            if extracted.replication_constraints or len(user_message) > 20:
                return True

        # --- Stage I B-1 problem-shape-routed topics -------------------------
        elif current_topic == "tradeoff_tolerance":
            # A stated willingness to trade is itself a constraint on the answer set.
            if extracted.constraints or len(user_message) > 20:
                return True

        elif current_topic == "segment_specific_causation":
            # Any causal claim about the segment, confirmed or ruled out.
            if extracted.validated_hypotheses or extracted.invalidated_hypotheses or len(user_message) > 20:
                return True

        elif current_topic == "comparison_baseline":
            # The principal supplying a contrast the data could not.
            if extracted.external_context or len(user_message) > 20:
                return True

        return False

    async def _generate_refinement_question(
        self,
        current_topic: str,
        decision_style: str,
        kt_summary: str,
        history: List[Dict[str, str]],
        user_message: Optional[str],
        accumulated: ExtractedRefinements,
        principal_role: str,
        principal_id: str = "system",
        da_output: Optional[Dict[str, Any]] = None,
    ) -> tuple:
        """Generate the next question using LLM with style guidance."""

        # For replication_potential, enrich kt_summary with benchmark segment details
        if current_topic == "replication_potential" and da_output:
            benchmark_summary = self._build_benchmark_summary(da_output)
            if benchmark_summary:
                kt_summary = kt_summary + "\n\n" + benchmark_summary

        # Build conversation history string
        history_str = ""
        for msg in history[-6:]:  # Last 6 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:300]
            history_str += f"{role.upper()}: {content}\n"

        # Build accumulated refinements string
        acc_str = ""
        if accumulated.exclusions:
            acc_str += f"Exclusions: {[e.value for e in accumulated.exclusions]}\n"
        if accumulated.external_context:
            acc_str += f"External Context: {accumulated.external_context}\n"
        if accumulated.constraints:
            acc_str += f"Constraints: {accumulated.constraints}\n"
        if accumulated.validated_hypotheses:
            acc_str += f"Validated: {accumulated.validated_hypotheses}\n"
        if accumulated.invalidated_hypotheses:
            acc_str += f"Invalidated: {accumulated.invalidated_hypotheses}\n"
        if accumulated.replication_constraints:
            acc_str += f"Replication barriers: {accumulated.replication_constraints}\n"

        # Default questions if LLM unavailable
        default_questions = {
            "hypothesis_validation": (
                "Looking at the analysis findings, do any of these drivers surprise you or seem off based on what you know about the business?",
                ["The findings align with my understanding", "Some of these are known issues", "I'm surprised by these results"]
            ),
            "scope_boundaries": (
                "Are there any segments, time periods, or dimensions we should exclude from this analysis?",
                ["No exclusions needed", "Exclude specific segments", "Focus on a specific time period"]
            ),
            "external_context": (
                "Were there any external factors - market changes, supplier issues, or internal changes - that we should account for?",
                ["No external factors", "Yes, there were market changes", "There were internal process changes"]
            ),
            "constraints": (
                "What levers are off the table? Are there any actions we cannot take?",
                ["No constraints", "Pricing is fixed", "Headcount is frozen"]
            ),
            "success_criteria": (
                "What does 'solved' look like for you? How will we measure success?",
                ["Return to prior performance", "Specific improvement target", "Stabilize the trend"]
            ),
            "replication_potential": (
                "The analysis identified internal segments performing above baseline. Are these a valid replication template, or do structural barriers prevent direct replication?",
                ["Yes, these are a valid template", "There are capacity constraints", "There are contractual barriers", "The timing context was different"]
            ),
            # Stage I B-1 routed topics. Every topic the router can emit needs an
            # entry here, or the no-LLM path degrades it to a generic prompt.
            "tradeoff_tolerance": (
                "Two KPIs are moving against each other here. If you had to give ground on one to protect the other, which one, and how much?",
                ["Protect margin, accept volume loss", "Protect volume, accept margin loss", "Neither can move", "Depends on the segment"]
            ),
            "segment_specific_causation": (
                "The variance is concentrated in one segment rather than spread across the business. What is different about that segment specifically?",
                ["Different customer mix", "Different cost structure", "A one-off event", "Nothing — I'd expect it everywhere"]
            ),
            "comparison_baseline": (
                "There is no comparable segment in the data to contrast against, so the analysis cannot say 'why here and not there'. What should this be measured against?",
                ["Prior year same period", "Budget/plan", "An external benchmark", "A specific peer segment"]
            ),
        }

        if not self.llm_service_agent:
            # Return default question for topic
            return default_questions.get(current_topic, _GENERIC_QUESTION)
        
        try:
            from src.agents.new.a9_llm_service_agent import A9_LLM_Request
            
            system_prompt = f"""You are a senior consultant conducting a problem refinement interview with a business principal.

INTERVIEW STYLE: {STYLE_GUIDANCE.get(decision_style, STYLE_GUIDANCE['analytical'])}

YOUR TASK: Ask ONE question about "{current_topic}"
GOAL: {TOPIC_OBJECTIVES.get(current_topic, '')}

CRITICAL: The Deep Analysis is COMPLETE. We already have the data. Your questions should:
- VALIDATE findings with the principal's business knowledge (not ask for more data)
- Uncover CONTEXT the data cannot show (external factors, organizational constraints)
- Identify what's OFF THE TABLE (constraints, exclusions)
- Confirm or INVALIDATE hypotheses based on principal's expertise

DO NOT ask questions like "What data do you have?" or "Can you provide metrics?" - we already analyzed the data below.

ANALYSIS FINDINGS (ALREADY COMPLETE):
{kt_summary}

{f"CONVERSATION SO FAR:{chr(10)}{history_str}" if history_str else ""}
{f"USER JUST SAID: {user_message}" if user_message else "This is the FIRST question - open DIRECTLY with the specific findings above."}
{f"REFINEMENTS CAPTURED:{chr(10)}{acc_str}" if acc_str else ""}

OUTPUT REQUIREMENTS:
- Generate exactly ONE question (1-2 sentences max)
- Reference specific numbers or segments from the analysis findings above
- Ask about VALIDATION, CONTEXT, or CONSTRAINTS - not more data
- NEVER introduce yourself, greet the principal, or refer to yourself by a name.
  Do not say "I'm <name>" or "This is <name>". You are a step in an analysis, not
  a persona. Open with the finding.
- Return ONLY this JSON format:

{{"question": "Your single question here", "suggested_responses": ["Option 1", "Option 2", "Option 3"]}}"""

            request = A9_LLM_Request(
                request_id=str(uuid.uuid4()),
                principal_id=principal_id,
                prompt="Return ONLY a JSON object with 'question' and 'suggested_responses' keys. No other text.",
                system_prompt=system_prompt,
                operation="generate",
                temperature=0.3,  # Lower temperature for more consistent output
            )
            
            response = await self.llm_service_agent.generate(request)
            content = response.content if hasattr(response, 'content') else str(response)
            
            self.logger.info(f"LLM refinement response: {content[:500]}")
            
            # Parse JSON from response
            import json
            json_match = re.search(r'\{[\s\S]*?\}', content)  # Non-greedy match for first JSON object
            if json_match:
                data = json.loads(json_match.group())
                # .get, not [] — a missing default must never discard a good LLM
                # answer. Indexing here raised KeyError for topics absent from
                # default_questions, and the outer `except Exception` swallowed
                # it and returned the generic fallback, so a successful
                # generation was thrown away by a lookup it did not need.
                # Observed live 2026-08-11 on `comparison_baseline`.
                _fallback = default_questions.get(current_topic, _GENERIC_QUESTION)
                question = data.get("question", _fallback[0])
                
                # Post-process: take only first sentence if multiple questions detected
                if question.count("?") > 1:
                    # Split on question marks and take first complete question
                    parts = question.split("?")
                    question = parts[0].strip() + "?"
                
                return (
                    question,
                    data.get("suggested_responses", _fallback[1])
                )
        except Exception as e:
            self.logger.warning(f"LLM question generation failed: {e}")

        return default_questions.get(current_topic, _GENERIC_QUESTION)

    def _determine_council_type(
        self,
        principal_ctx: Dict[str, Any],
        accumulated: ExtractedRefinements,
        da_output: Dict[str, Any],
    ) -> tuple:
        """Determine recommended Solution Council type based on context."""
        role = principal_ctx.get("role", "")
        style = principal_ctx.get("decision_style", "analytical").lower()
        
        # Combine all text for keyword matching
        all_text = " ".join([
            da_output.get("scqa_summary", ""),
            " ".join(accumulated.external_context),
            " ".join(accumulated.constraints),
            " ".join(accumulated.validated_hypotheses),
        ]).lower()
        
        # Score each council type
        scores = {}
        for council, rules in COUNCIL_ROUTING.items():
            score = 0
            if role in rules["roles"]:
                score += 3
            if style in rules["styles"]:
                score += 2
            for kw in rules["keywords"]:
                if kw.lower() in all_text:
                    score += 1
            scores[council] = score
        
        # Get highest scoring council
        best_council = max(scores, key=scores.get)
        best_score = scores[best_council]
        
        # Build rationale
        rationale_parts = []
        if role:
            rationale_parts.append(f"Principal role: {role}")
        rationale_parts.append(f"Decision style: {style}")
        if best_score > 0:
            rationale_parts.append(f"Matched keywords/rules for {best_council} council")
        
        return best_council, "; ".join(rationale_parts)

    def _recommend_diverse_council(
        self,
        principal_ctx: Dict[str, Any],
        accumulated: ExtractedRefinements,
        da_output: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Recommend a diverse council with one member from each category (MBB, Big4, Tech, Risk)."""
        self.logger.info(f"_recommend_diverse_council called with principal_ctx: {principal_ctx}")
        
        # Partner selection rules by category
        PARTNER_RULES = {
            "mbb": {
                "mckinsey": {
                    "name": "McKinsey & Company",
                    "keywords": ["strategy", "transformation", "portfolio", "cost", "restructuring", "operating model"],
                    "roles": ["CEO", "CFO"],
                },
                "bcg": {
                    "name": "Boston Consulting Group",
                    "keywords": ["growth", "innovation", "digital", "market", "competitive", "portfolio"],
                    "roles": ["CEO", "CMO", "CTO"],
                },
                "bain": {
                    "name": "Bain & Company",
                    "keywords": ["results", "implementation", "customer", "nps", "pe", "operational", "quick wins"],
                    "roles": ["COO", "CEO"],
                },
            },
            "big4": {
                "deloitte": {
                    "name": "Deloitte Consulting",
                    "keywords": ["technology", "operations", "erp", "cloud", "process", "automation"],
                    "roles": ["CTO", "COO"],
                },
                "ey_parthenon": {
                    "name": "EY-Parthenon",
                    "keywords": ["transaction", "ma", "synergy", "deal", "integration", "divestiture"],
                    "roles": ["CFO", "CEO"],
                },
                "kpmg": {
                    "name": "KPMG Advisory",
                    "keywords": ["risk", "compliance", "governance", "regulatory", "esg", "audit", "controls"],
                    "roles": ["CFO", "Finance Manager"],
                },
                "pwc_strategy": {
                    "name": "PwC Strategy&",
                    "keywords": ["capabilities", "operating model", "cost", "fit", "efficiency"],
                    "roles": ["COO", "CFO"],
                },
            },
            "technology": {
                "accenture": {
                    "name": "Accenture",
                    "keywords": ["scale", "ai", "cloud", "digital", "automation", "platform", "data"],
                    "roles": ["CTO", "COO"],
                },
            },
            "risk": {
                "kpmg": {
                    "name": "KPMG Advisory",
                    "keywords": ["risk", "compliance", "governance", "controls", "regulatory"],
                    "roles": ["CFO", "Finance Manager"],
                },
            },
        }
        
        role = principal_ctx.get("role", "")
        
        # Combine all text for keyword matching
        all_text = " ".join([
            da_output.get("scqa_summary", ""),
            " ".join(accumulated.external_context),
            " ".join(accumulated.constraints),
            " ".join(accumulated.validated_hypotheses),
            " ".join(accumulated.invalidated_hypotheses),
        ]).lower()
        
        recommendations = []
        
        for category, partners in PARTNER_RULES.items():
            best_partner = None
            best_score = -1
            best_rationale = ""
            
            for partner_id, info in partners.items():
                score = 0
                matched_keywords = []
                
                # Score by keyword matches
                for kw in info["keywords"]:
                    if kw.lower() in all_text:
                        score += 1
                        matched_keywords.append(kw)
                
                # Bonus for role affinity
                if role in info.get("roles", []):
                    score += 2
                
                if score > best_score:
                    best_score = score
                    best_partner = partner_id
                    if matched_keywords:
                        best_rationale = f"Matched: {', '.join(matched_keywords[:3])}"
                    elif role in info.get("roles", []):
                        best_rationale = f"Aligned with {role} role"
                    else:
                        best_rationale = f"Default {category.upper()} selection"
            
            if best_partner:
                recommendations.append({
                    "category": category,
                    "persona_id": best_partner,
                    "persona_name": PARTNER_RULES[category][best_partner]["name"],
                    "rationale": best_rationale,
                })
        
        return recommendations

    def _create_final_result(
        self,
        da_output: Dict[str, Any],
        principal_ctx: Dict[str, Any],
        history: List[Dict[str, str]],
        topics_completed: List[str],
        turn_count: int,
        accumulated: Optional[ExtractedRefinements] = None,
        profile_cell: Optional[str] = None,
        topic_sequence: Optional[List[str]] = None,
        routing_rules: Optional[List[str]] = None,
    ) -> ProblemRefinementResult:
        """Create the final refinement result with problem statement and council routing.

        The routing fields are carried through to the terminal result too — a
        conversation that ended early is exactly the one where you want to see
        which sequence it was following and how far it got.
        """
        if accumulated is None:
            accumulated = ExtractedRefinements()
        
        # Determine council type
        council_type, council_rationale = self._determine_council_type(
            principal_ctx, accumulated, da_output
        )
        
        # Recommend diverse council (one from each category)
        diverse_council = self._recommend_diverse_council(
            principal_ctx, accumulated, da_output
        )
        self.logger.info(f"Diverse council recommendation: {diverse_council}")
        
        # Build refined problem statement
        scqa = da_output.get("scqa_summary", "")
        problem_parts = [scqa[:500] if scqa else "Analysis complete."]
        
        if accumulated.exclusions:
            excl_str = ", ".join([e.value for e in accumulated.exclusions])
            problem_parts.append(f"Excluding: {excl_str}")
        
        if accumulated.external_context:
            problem_parts.append(f"Context: {'; '.join(accumulated.external_context[:3])}")
        
        if accumulated.constraints:
            problem_parts.append(f"Constraints: {'; '.join(accumulated.constraints[:3])}")
        
        if accumulated.validated_hypotheses:
            problem_parts.append(f"Focus areas: {'; '.join(accumulated.validated_hypotheses[:3])}")
        
        refined_statement = " | ".join(problem_parts)
        
        return ProblemRefinementResult(
            agent_message="Thank you for the context. I have enough information to proceed to solution generation.",
            suggested_responses=[],
            exclusions=accumulated.exclusions,
            external_context=accumulated.external_context,
            constraints=accumulated.constraints,
            validated_hypotheses=accumulated.validated_hypotheses,
            invalidated_hypotheses=accumulated.invalidated_hypotheses,
            replication_constraints=accumulated.replication_constraints,
            current_topic=topics_completed[-1] if topics_completed else "complete",
            topic_complete=True,
            topics_completed=topics_completed,
            ready_for_solutions=True,
            refined_problem_statement=refined_statement,
            recommended_council_type=council_type,
            council_routing_rationale=council_rationale,
            recommended_council_members=diverse_council,
            turn_count=turn_count,
            conversation_history=history,
            constraint_items=accumulated.constraint_items,
            problem_profile_cell=profile_cell,
            topic_sequence=list(topic_sequence or []),
            topic_routing_rules_applied=list(routing_rules or []),
        )


async def create_deep_analysis_agent(config: Dict[str, Any] = None) -> A9_Deep_Analysis_Agent:
    return await A9_Deep_Analysis_Agent.create(config or {})
