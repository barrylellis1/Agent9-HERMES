"""
A9 Deep Analysis Agent (MVP skeleton)
- Implements DeepAnalysisProtocol
- Uses Data Product Agent for deterministic grouped/timeframe comparisons
- Uses A9_LLM_Service for narrative (optional)
"""
from __future__ import annotations

import logging
import uuid
import os
import re
from typing import Dict, Any, Optional, List
import yaml

from src.agents.shared.a9_agent_base_model import A9AgentBaseModel
from src.agents.agent_config_models import A9_Deep_Analysis_Agent_Config
from src.agents.protocols.deep_analysis_protocol import DeepAnalysisProtocol
from src.agents.models.deep_analysis_models import (
    DeepAnalysisRequest,
    DeepAnalysisPlan,
    DeepAnalysisResponse,
    KTIsIsNot,
    ChangePoint,
    ProblemRefinementInput,
    ProblemRefinementResult,
    RefinementExclusion,
    ExtractedRefinements,
)
from src.agents.models.data_governance_models import KPIDataProductMappingRequest
from src.agents.utils.data_quality_filter import DataQualityFilter, filter_anomalies


logger = logging.getLogger(__name__)


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
        self.llm_service_agent = None
        # Optional: orchestrator not stored; agents are resolved in connect()

    # --- Helpers -----------------------------------------------------------
    def _contract_path(self) -> str:
        """
        Resolve contract path from the canonical registry_references location.
        This ensures single source of truth for data product contracts.
        """
        try:
            # Canonical path in registry_references (single source of truth)
            canonical = "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"
            if os.path.exists(canonical):
                return canonical
            
            # Try from project root
            here = os.path.dirname(__file__)
            proj_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
            abs_canonical = os.path.join(proj_root, canonical)
            if os.path.exists(abs_canonical):
                return abs_canonical
            
            # Last resort
            return canonical
        except Exception:
            return "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml"

    def _dims_from_contract(self, limit: int) -> List[str]:
        dims: List[str] = []
        try:
            cpath = self._contract_path()
            if not os.path.exists(cpath):
                return []
            with open(cpath, "r", encoding="utf-8") as f:
                doc = yaml.safe_load(f)
            views = (doc or {}).get("views", [])
            target = None
            for v in views:
                if isinstance(v, dict) and v.get("name") == "FI_Star_View":
                    target = v
                    break
            if not isinstance(target, dict):
                return []
            llm_profile = target.get("llm_profile", {}) or {}
            all_dims = llm_profile.get("dimension_semantics", []) or []
            def _keep(lbl: str) -> bool:
                s = str(lbl or "").lower()
                ban = ["flag", "hierarchy", "id", "transaction date", "version", "fiscal ytd", "fiscal qtd", "fiscal mtd"]
                return bool(lbl) and not any(t in s for t in ban)
            kept = [d for d in all_dims if _keep(str(d))]
            # Preference order
            preferred = ["Profit Center Name", "Customer Type Name", "Customer Name", "Product Name"]
            out: List[str] = [d for d in preferred if d in kept]
            for d in kept:
                if d not in out:
                    out.append(d)
            if isinstance(limit, int) and limit > 0:
                out = out[:limit]
            dims = out
        except Exception as e:
            self.logger.debug(f"_dims_from_contract error: {e}")
        return dims

    def _prev_timeframe(self, timeframe: Optional[str]) -> Optional[str]:
        tf = (str(timeframe or "").strip().lower())
        map_ = {
            "current_quarter": "last_quarter",
            "this_quarter": "last_quarter",
            "current_month": "last_month",
            "this_month": "last_month",
            "current_year": "last_year",
            "this_year": "last_year",
            "quarter_to_date": "quarter_to_date",
            "month_to_date": "month_to_date",
            "year_to_date": "year_to_date",
        }
        return map_.get(tf)

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
            # Calculate percent variance (handle division by zero)
            if previous != 0:
                pct_variance = abs(delta / previous)
            elif current != 0:
                pct_variance = 1.0  # 100% variance if previous was 0 but current isn't
            else:
                pct_variance = 0.0  # Both are 0
            
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
                try:
                    self.data_governance_agent = await orchestrator.get_agent("A9_Data_Governance_Agent")
                except Exception:
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
            dimensions: List[str] = self._dims_from_contract(limit=target_count)
            try:
                self.logger.info(f"plan_deep_analysis: kpi={request.kpi_name} timeframe={request.timeframe} dims_from_contract={len(dimensions)}")
            except Exception:
                pass
            # Fallback to DG metadata if contract not available
            if not dimensions:
                try:
                    if self.data_governance_agent is not None and request.kpi_name:
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
                                    # Extract field name from dimension objects
                                    extracted_dims = []
                                    for d in dims:
                                        if d:
                                            if isinstance(d, dict):
                                                # Use 'name' or 'field' key if available
                                                dim_name = d.get('name') or d.get('field') or str(d)
                                            elif hasattr(d, 'name'):
                                                dim_name = d.name
                                            elif hasattr(d, 'field'):
                                                dim_name = d.field
                                            else:
                                                dim_name = str(d)
                                            extracted_dims.append(dim_name)
                                    dimensions = extracted_dims
                except Exception as e:
                    self.logger.debug(f"plan_deep_analysis: DG fallback failed: {e}")

            # Create skeleton steps for grouped/timeframe comparisons (executed by DPA later)
            steps: List[Dict[str, Any]] = self._build_group_compare_steps(dimensions, request.timeframe, request.filters)

            # Build plan (no SQL here; DPA handles execution in execute_deep_analysis)
            plan = DeepAnalysisPlan(
                kpi_name=request.kpi_name,
                timeframe=request.timeframe,
                filters=request.filters,
                dimensions=dimensions,
                steps=steps,
                notes="KT core with SCQA/MECE framing (auto-derived dimensions from data product contract)."
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

            change_points: List[ChangePoint] = []
            queries_executed: int = 0

            # If DP Agent is available, compute where/when by executing grouped queries
            if self.data_product_agent is not None and getattr(plan, "kpi_name", None):
                try:
                    # Load KPI definition via KPIProvider (DP Agent expects KPI object)
                    from src.registry.providers.kpi_provider import KPIProvider
                    kp = KPIProvider(source_path="src/registry/kpi/kpi_registry.yaml", storage_format="yaml")
                    await kp.load()
                    kpi_def = kp.get(plan.kpi_name)
                except Exception as e:
                    kpi_def = None
                    self.logger.debug(f"execute_deep_analysis: KPI load failed: {e}")

                if kpi_def is not None:
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
                    dims = getattr(plan, "dimensions", []) or []

                    # Fallback: populate dimensions and steps from contract if missing
                    if not dims:
                        dims = self._dims_from_contract(limit=self.config.max_dimensions)
                        try:
                            # Update the incoming plan so UI shows correct counts
                            if hasattr(plan, "dimensions"):
                                plan.dimensions = dims
                        except Exception:
                            pass
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
                                        key = str(r.get(key_col))
                                        val_raw = r.get(val_col)
                                        val = float(val_raw) if val_raw is not None else 0.0
                                    else:
                                        key = str(r[key_idx])
                                        val = float(r[val_idx]) if r[val_idx] is not None else 0.0
                                    out[key] = val
                                except Exception:
                                    continue
                            return out
                        except Exception:
                            return {}

                    # Helper: read dimension hierarchies from contract (if provided)
                    def _hierarchies_from_contract() -> Dict[str, List[str]]:
                        try:
                            cpath = self._contract_path()
                            if not os.path.exists(cpath):
                                return {}
                            with open(cpath, "r", encoding="utf-8") as f:
                                doc = yaml.safe_load(f)
                            views = (doc or {}).get("views", [])
                            target = None
                            for v in views:
                                if isinstance(v, dict) and v.get("name") == "FI_Star_View":
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
                                # Prefer budget thresholds if present
                                chosen = None
                                for t in thrs:
                                    try:
                                        ct = getattr(t, "comparison_type", None) or (t.get("comparison_type") if isinstance(t, dict) else None)
                                        ct_str = str(getattr(ct, "value", ct)).lower() if ct is not None else ""
                                        if ct_str == "budget":
                                            chosen = (ct_str, t)
                                            break
                                    except Exception:
                                        continue
                                # If no budget threshold chosen, try match to timeframe-derived comp
                                if chosen is None:
                                    for t in thrs:
                                        try:
                                            ct = getattr(t, "comparison_type", None) or (t.get("comparison_type") if isinstance(t, dict) else None)
                                            ct_str = str(getattr(ct, "value", ct)).lower() if ct is not None else ""
                                            if ct_str == comp:
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
                        try:
                            # Current map
                            gen_cur = await self.data_product_agent.generate_sql_for_kpi(
                                kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[level_label]
                            )
                            if not gen_cur.get("success"):
                                return []
                            cur_exec = await self.data_product_agent.execute_sql(gen_cur.get("sql"))
                            m_cur = _as_map(cur_exec)

                            if comparator == "budget":
                                # Budget map: same timeframe, Version='Budget'
                                base_filters = getattr(plan, "filters", None) or {}
                                f_act = {**base_filters, "Version": "Actual"}
                                f_bud = {**base_filters, "Version": "Budget"}
                                gen_act = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=f_act, breakdown=True, override_group_by=[level_label]
                                )
                                gen_bud = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=f_bud, breakdown=True, override_group_by=[level_label]
                                )
                                if not (gen_act.get("success") and gen_bud.get("success")):
                                    return []
                                act_exec = await self.data_product_agent.execute_sql(gen_act.get("sql"))
                                bud_exec = await self.data_product_agent.execute_sql(gen_bud.get("sql"))
                                m_act = _as_map(act_exec)
                                m_bud = _as_map(bud_exec)
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
                                    kpi_def, timeframe=prev_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[level_label]
                                )
                                if not gen_prev.get("success"):
                                    return []
                                prev_exec = await self.data_product_agent.execute_sql(gen_prev.get("sql"))
                                m_prev = _as_map(prev_exec)
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

                    def _format_where_entry(dimension: Any, key: Any, delta: Any, current: Any, previous: Any, note: Optional[str] = None) -> Dict[str, Any]:
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
                                f_act = {**base_filters, "Version": "Actual"}
                                f_bud = {**base_filters, "Version": "Budget"}
                                gen_act_tot = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=f_act
                                )
                                gen_bud_tot = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=f_bud
                                )
                                if not (gen_act_tot.get("success") and gen_bud_tot.get("success")):
                                    return None
                                act_exec_tot = await self.data_product_agent.execute_sql(gen_act_tot.get("sql"))
                                bud_exec_tot = await self.data_product_agent.execute_sql(gen_bud_tot.get("sql"))
                                current_total = _extract_scalar(act_exec_tot)
                                baseline_total = _extract_scalar(bud_exec_tot)
                            else:
                                if not prev_tf:
                                    return None
                                gen_cur_tot = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=cur_tf, filters=base_filters
                                )
                                gen_prev_tot = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=prev_tf, filters=base_filters
                                )
                                if not (gen_cur_tot.get("success") and gen_prev_tot.get("success")):
                                    return None
                                cur_exec_tot = await self.data_product_agent.execute_sql(gen_cur_tot.get("sql"))
                                prev_exec_tot = await self.data_product_agent.execute_sql(gen_prev_tot.get("sql"))
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

                    # Primary path: hierarchical drill per vector if hierarchies present
                    hmap = _hierarchies_from_contract()
                    used_hierarchical = False
                    spec_main = _pick_threshold_spec()
                    comparator_main = "budget" if str(spec_main.get("comparison_type", "")).lower() == "budget" else "previous"
                    overall_summary = await _compute_overall_summary(comparator_main) if self.data_product_agent else None
                    if hmap:
                        used_hierarchical = True
                        spec = spec_main
                        comparator = comparator_main
                        # Default vector order
                        vector_order = [k for k in ["customer", "product", "profit_center"] if k in hmap] or list(hmap.keys())
                        for vec in vector_order:
                            levels = hmap.get(vec, []) or []
                            for lvl in levels:
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
                                        entry_b = _format_where_entry(b.get("dimension"), b.get("key"), b.get("delta"), b.get("current"), b.get("previous"))
                                        kt.where_is.append(entry_b)
                                        change_points.append(ChangePoint(dimension=b.get("dimension"), key=b.get("key"), current_value=b.get("current"), previous_value=b.get("previous"), delta=b.get("delta")))
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
                        self.logger.info(f"[LOOP] Will process {len(dims_to_process)} dimensions: {dims_to_process}")
                        for dim_idx, dim in enumerate(dims_to_process):
                            self.logger.info(f"[LOOP] Processing dimension {dim_idx+1}/{len(dims_to_process)}: {dim}")
                            try:
                                # Fetch ALL data for this dimension to apply hybrid threshold selection
                                # This gives us richer context for the LLM vs fixed Top 3/Bottom 3
                                all_req = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def,
                                    timeframe=cur_tf,
                                    filters=getattr(plan, "filters", None),
                                    breakdown=True,
                                    override_group_by=[dim],
                                    topn={"type": "top", "n": 50, "metric": "delta_prev"}  # Fetch more for threshold analysis
                                )
                                if all_req.get("success"):
                                    all_exec = await self.data_product_agent.execute_sql(all_req.get("sql"))
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
                                            continue
                                    
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
                                    
                                    # Add significant variance items to where_is (with deduplication)
                                    added_keys_topn = set()
                                    self.logger.info(f"[DEDUP] Dim={dim}: {len(where_is_items)} IS items, {len(where_is_not_items)} IS-NOT items, existing keys={len(added_where_is_keys)}")
                                    for key, c, p, d in where_is_items:
                                        dedup_key = (dim, key)
                                        if dedup_key not in added_where_is_keys:
                                            entry_top = _format_where_entry(dim, key, d, c, p)
                                            kt.where_is.append(entry_top)
                                            change_points.append(ChangePoint(dimension=dim, key=key, current_value=c, previous_value=p, delta=d))
                                            added_keys_topn.add(key)
                                            added_where_is_keys.add(dedup_key)
                                        else:
                                            self.logger.warning(f"[DEDUP] Skipping duplicate: {dedup_key}")
                                    
                                    # Add healthy items to where_is_not (for contrast, with deduplication)
                                    for key, c, p, d in where_is_not_items:
                                        dedup_key = (dim, key)
                                        if key not in added_keys_topn and dedup_key not in added_where_is_not_keys:
                                            entry_bot = _format_where_entry(dim, key, d, c, p, note="Outperforming")
                                            kt.where_is_not.append(entry_bot)
                                            added_where_is_not_keys.add(dedup_key)
                                
                                # Fallback: dual-query method if TopN path failed to populate
                                if not kt.where_is:
                                    gen_cur = await self.data_product_agent.generate_sql_for_kpi(
                                        kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim]
                                    )
                                    if gen_cur.get("success"):
                                        cur_exec = await self.data_product_agent.execute_sql(gen_cur.get("sql"))
                                        queries_executed += 1
                                        m_cur = _as_map(cur_exec)
                                        m_prev: Dict[str, float] = {}
                                        if prev_tf:
                                            gen_prev = await self.data_product_agent.generate_sql_for_kpi(
                                                kpi_def, timeframe=prev_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim]
                                            )
                                            if gen_prev.get("success"):
                                                prev_exec = await self.data_product_agent.execute_sql(gen_prev.get("sql"))
                                                queries_executed += 1
                                                m_prev = _as_map(prev_exec)
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
                                        
                                        # Add significant variance items to where_is (with deduplication)
                                        added_keys_fallback = set()
                                        for k, c, p, d in where_is_items:
                                            dedup_key = (dim, k)
                                            if dedup_key not in added_where_is_keys:
                                                entry_diff = _format_where_entry(dim, k, d, c, p)
                                                kt.where_is.append(entry_diff)
                                                change_points.append(ChangePoint(dimension=dim, key=k, current_value=c, previous_value=p, delta=d))
                                                added_keys_fallback.add(k)
                                                added_where_is_keys.add(dedup_key)
                                        
                                        # Add healthy items to where_is_not (for contrast, with deduplication)
                                        for k, c, p, d in where_is_not_items:
                                            dedup_key = (dim, k)
                                            if k not in added_keys_fallback and dedup_key not in added_where_is_not_keys:
                                                entry_low = _format_where_entry(dim, k, d, c, p, note="Outperforming")
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
                                        f_act = {**base_filters, "Version": "Actual"}
                                        f_bud = {**base_filters, "Version": "Budget"}
                                        gen_act_h = await self.data_product_agent.generate_sql_for_kpi(
                                            kpi_def, timeframe=cur_tf, filters=f_act, breakdown=True, override_group_by=[dim]
                                        )
                                        gen_bud_h = await self.data_product_agent.generate_sql_for_kpi(
                                            kpi_def, timeframe=cur_tf, filters=f_bud, breakdown=True, override_group_by=[dim]
                                        )
                                        if gen_act_h.get("success") and gen_bud_h.get("success"):
                                            act_exec_h = await self.data_product_agent.execute_sql(gen_act_h.get("sql"))
                                            bud_exec_h = await self.data_product_agent.execute_sql(gen_bud_h.get("sql"))
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
                                                kpi_def, timeframe=prev_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[dim]
                                            )
                                            if gen_cur_h.get("success") and gen_prev_h.get("success"):
                                                cur_exec_h = await self.data_product_agent.execute_sql(gen_cur_h.get("sql"))
                                                prev_exec_h = await self.data_product_agent.execute_sql(gen_prev_h.get("sql"))
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

                    # WHEN (time buckets with greatest variance)
                    time_bucket = "Fiscal Year-Month"
                    try:
                        # Prefer Top/Bottom N with delta_prev for time buckets
                        t_top = await self.data_product_agent.generate_sql_for_kpi(
                            kpi_def, timeframe=cur_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[time_bucket], topn={"type": "top", "n": 3, "metric": "delta_prev"}
                        )
                        if t_top.get("success"):
                            t_top_exec = await self.data_product_agent.execute_sql(t_top.get("sql"))
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
                            t_bot_exec = await self.data_product_agent.execute_sql(t_bot.get("sql"))
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
                                cur_exec_t = await self.data_product_agent.execute_sql(gen_cur_t.get("sql"))
                                queries_executed += 1
                                m_cur_t = _as_map(cur_exec_t)
                            else:
                                m_cur_t = {}
                            m_prev_t: Dict[str, float] = {}
                            if prev_tf:
                                gen_prev_t = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def, timeframe=prev_tf, filters=getattr(plan, "filters", None), breakdown=True, override_group_by=[time_bucket]
                                )
                                if gen_prev_t.get("success"):
                                    prev_exec_t = await self.data_product_agent.execute_sql(gen_prev_t.get("sql"))
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
                        dims_from_contract = self._dims_from_contract(limit=self.config.max_dimensions)
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
                        comparator_label = "Budget" if comparator_main == "budget" else (prev_tf or "previous period")
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

            scqa_summary = (
                f"Situation: Reviewing {plan.kpi_name}. "
                f"Complication: Variance detected? (MVP skeleton). "
                f"Question: Which segments drive change? "
            )
            # Ensure plan has non-empty counters for UI summary even if DP path didn't run
            try:
                if not getattr(plan, "dimensions", None):
                    plan.dimensions = self._dims_from_contract(limit=self.config.max_dimensions)
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
                tf_mapping = {
                    "current": str(cur_tf_val), 
                    "previous": str(prev_tf_val) if prev_tf_val else "previous period"
                }

            # Use DataQualityFilter utility to handle data anomalies
            dq_filter = DataQualityFilter()
            
            # Process where_is and where_is_not lists
            self.logger.info(f"[PRE-FILTER] where_is has {len(kt.where_is)} items, keys: {[i.get('key') for i in kt.where_is[:10]]}")
            kt.where_is, dq_issues_is = dq_filter.filter_and_dedupe(kt.where_is)
            kt.where_is_not, dq_issues_is_not = dq_filter.filter_and_dedupe(kt.where_is_not)
            self.logger.info(f"[POST-FILTER] where_is has {len(kt.where_is)} items, dq_issues_is has {len(dq_issues_is)} items")
            
            # Create data quality alert if anomalies found
            all_dq_issues = dq_issues_is + dq_issues_is_not
            dq_alert = dq_filter.create_data_quality_alert(all_dq_issues, context="Deep Analysis")
            if dq_alert:
                kt.extent_is.append(dq_alert)
                self.logger.warning(f"[DATA_QUALITY] {len(all_dq_issues)} items moved to data quality alerts")
            
            self.logger.info(f"[FINAL] where_is={len(kt.where_is)} items, where_is_not={len(kt.where_is_not)} items, dq_issues={len(all_dq_issues)} after filtering")

            return DeepAnalysisResponse.success(
                request_id=req_id,
                plan=plan,
                scqa_summary=scqa_summary,
                kt_is_is_not=kt,
                change_points=change_points,
                percent_growth_enabled=False,
                timeframe_mapping=tf_mapping,
                when_started=when_started,
                dimensions_suggested=getattr(plan, "dimensions", [])
            )
        except Exception as e:
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
            
            # Determine current topic
            current_topic = input_model.current_topic
            topics_completed = []
            
            # Parse topics_completed from history if not first turn
            if history:
                topics_completed = self._extract_completed_topics(history)
            
            if not current_topic:
                # First turn - start with first topic
                current_topic = REFINEMENT_TOPIC_SEQUENCE[0]
            
            # Check for early exit commands
            if user_message and self._is_early_exit(user_message):
                # Accumulate refinements before finalizing
                accumulated = self._accumulate_refinements(history)
                return self._create_final_result(
                    da_output, principal_ctx, history, topics_completed, turn_count, accumulated
                )
            
            # Check for skip command
            topic_skipped = False
            if user_message and self._is_skip_command(user_message):
                topic_skipped = True
                topics_completed.append(current_topic)
                current_topic = self._get_next_topic(current_topic, topics_completed)
            
            # Check max turns
            if turn_count >= MAX_TOTAL_TURNS:
                self.logger.info(f"Max turns ({MAX_TOTAL_TURNS}) reached, finalizing refinement")
                accumulated = self._accumulate_refinements(history)
                return self._create_final_result(
                    da_output, principal_ctx, history, topics_completed, turn_count, accumulated
                )
            
            # If all topics completed, finalize
            if current_topic is None or len(topics_completed) >= len(REFINEMENT_TOPIC_SEQUENCE):
                accumulated = self._accumulate_refinements(history)
                return self._create_final_result(
                    da_output, principal_ctx, history, topics_completed, turn_count, accumulated
                )
            
            # Build KT summary for LLM context
            kt_summary = self._build_kt_summary(da_output)
            
            # Accumulate refinements from previous turns
            accumulated = self._accumulate_refinements(history)
            
            # If user provided a message, extract refinements from it
            extracted = ExtractedRefinements()
            if user_message and not topic_skipped:
                extracted = await self._extract_refinements_from_response(
                    user_message, current_topic, da_output, decision_style, principal_id
                )
                self.logger.info(f"[DA] Extracted refinements: ext_ctx={len(extracted.external_context)}, constraints={len(extracted.constraints)}, validated={len(extracted.validated_hypotheses)}")
                # Merge extracted into accumulated
                accumulated = self._merge_refinements(accumulated, extracted)
            
            # Check if topic is complete (via LLM or heuristics)
            topic_complete = False
            if user_message and not topic_skipped:
                topic_complete = await self._check_topic_complete(
                    current_topic, history, user_message, extracted
                )
            
            # Advance topic if complete
            if topic_complete:
                topics_completed.append(current_topic)
                current_topic = self._get_next_topic(current_topic, topics_completed)
                
                # If no more topics, finalize
                if current_topic is None:
                    return self._create_final_result(
                        da_output, principal_ctx, history, topics_completed, turn_count,
                        accumulated
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
                current_topic=current_topic,
                topic_complete=topic_complete,
                topics_completed=topics_completed,
                ready_for_solutions=False,
                refined_problem_statement=None,
                recommended_council_type=None,
                council_routing_rationale=None,
                turn_count=turn_count + 1,
                conversation_history=new_history,
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

    def _get_next_topic(self, current: str, completed: List[str]) -> Optional[str]:
        """Get the next topic in sequence that hasn't been completed."""
        try:
            current_idx = REFINEMENT_TOPIC_SEQUENCE.index(current)
            for topic in REFINEMENT_TOPIC_SEQUENCE[current_idx + 1:]:
                if topic not in completed:
                    return topic
        except ValueError:
            pass
        # Check if any earlier topics were skipped
        for topic in REFINEMENT_TOPIC_SEQUENCE:
            if topic not in completed:
                return topic
        return None

    def _extract_completed_topics(self, history: List[Dict[str, str]]) -> List[str]:
        """Extract which topics have been completed from conversation history."""
        # Simple heuristic: look for topic transitions in assistant messages
        completed = []
        for msg in history:
            if msg.get("role") == "assistant":
                content = msg.get("content", "").lower()
                # Check for topic transition phrases
                for topic in REFINEMENT_TOPIC_SEQUENCE:
                    if f"moving to {topic}" in content or f"completed {topic}" in content:
                        if topic not in completed:
                            completed.append(topic)
        return completed

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
        
        # Where IS (top drivers)
        where_is = kt.get("where_is", [])
        if where_is:
            top_drivers = where_is[:5]
            driver_strs = []
            for d in top_drivers:
                key = d.get("key", "Unknown")
                delta = d.get("delta", 0)
                pct = d.get("percent_of_total", 0)
                driver_strs.append(f"- {key}: ${delta:,.0f} ({pct:.1f}% of variance)")
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

    def _accumulate_refinements(self, history: List[Dict[str, str]]) -> ExtractedRefinements:
        """Accumulate refinements from conversation history by re-extracting from user messages."""
        accumulated = ExtractedRefinements()
        
        # Extract refinements from each user message in history
        for msg in history:
            if msg.get("role") == "user":
                user_text = msg.get("content", "")
                # Use simple extraction (sync) to accumulate from history
                extracted = self._simple_extraction(user_text, "general")
                accumulated = self._merge_refinements(accumulated, extracted)
        
        return accumulated

    def _merge_refinements(
        self, accumulated: ExtractedRefinements, extracted: ExtractedRefinements
    ) -> ExtractedRefinements:
        """Merge newly extracted refinements into accumulated."""
        return ExtractedRefinements(
            exclusions=accumulated.exclusions + extracted.exclusions,
            external_context=accumulated.external_context + extracted.external_context,
            constraints=accumulated.constraints + extracted.constraints,
            validated_hypotheses=accumulated.validated_hypotheses + extracted.validated_hypotheses,
            invalidated_hypotheses=accumulated.invalidated_hypotheses + extracted.invalidated_hypotheses,
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
            from src.agents.a9_llm_service_agent import A9_LLM_Request
            
            extraction_prompt = f"""Extract structured refinements from the user's response.

User's response: "{user_message}"
Current topic: {current_topic}

Extract any of the following that are mentioned:
1. EXCLUSIONS: Segments, dimensions, or time periods to exclude (format: dimension|value|reason)
2. EXTERNAL_CONTEXT: External factors mentioned (market changes, supplier issues, etc.)
3. CONSTRAINTS: Actions or levers that are off-limits
4. VALIDATED: Hypotheses or drivers the user confirmed as real issues
5. INVALIDATED: Hypotheses or drivers the user said are known/expected/not relevant

Respond in JSON format:
{{
  "exclusions": [{{"dimension": "...", "value": "...", "reason": "..."}}],
  "external_context": ["..."],
  "constraints": ["..."],
  "validated_hypotheses": ["..."],
  "invalidated_hypotheses": ["..."]
}}

If nothing relevant is found for a category, use an empty list."""

            request = A9_LLM_Request(
                request_id=str(uuid.uuid4()),
                principal_id=principal_id,
                prompt=extraction_prompt,
                operation="generate",
                temperature=0.1,  # Low temperature for structured extraction
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
                )
        except Exception as e:
            self.logger.warning(f"LLM extraction failed, using simple extraction: {e}")
        
        return self._simple_extraction(user_message, current_topic)

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
    ) -> bool:
        """Determine if the current topic has been sufficiently covered."""
        # Count turns on this topic
        topic_turns = 0
        for msg in history:
            if msg.get("role") == "assistant":
                # Simple heuristic: count assistant messages since last topic change
                topic_turns += 1
        
        # Auto-complete if max turns per topic reached
        if topic_turns >= MAX_TURNS_PER_TOPIC:
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
    ) -> tuple:
        """Generate the next question using LLM with style guidance."""
        
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
        }
        
        if not self.llm_service_agent:
            # Return default question for topic
            return default_questions.get(current_topic, (
                "Please share any additional context that would help refine this analysis.",
                ["Continue", "Skip this topic", "Proceed to solutions"]
            ))
        
        try:
            from src.agents.a9_llm_service_agent import A9_LLM_Request
            
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
{f"USER JUST SAID: {user_message}" if user_message else "This is the FIRST question - introduce yourself briefly and reference the specific findings above."}
{f"REFINEMENTS CAPTURED:{chr(10)}{acc_str}" if acc_str else ""}

OUTPUT REQUIREMENTS:
- Generate exactly ONE question (1-2 sentences max)
- Reference specific numbers or segments from the analysis findings above
- Ask about VALIDATION, CONTEXT, or CONSTRAINTS - not more data
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
                question = data.get("question", default_questions[current_topic][0])
                
                # Post-process: take only first sentence if multiple questions detected
                if question.count("?") > 1:
                    # Split on question marks and take first complete question
                    parts = question.split("?")
                    question = parts[0].strip() + "?"
                
                return (
                    question,
                    data.get("suggested_responses", default_questions[current_topic][1])
                )
        except Exception as e:
            self.logger.warning(f"LLM question generation failed: {e}")
        
        return default_questions.get(current_topic, (
            "Please share any additional context.",
            ["Continue", "Skip", "Proceed to solutions"]
        ))

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
    ) -> ProblemRefinementResult:
        """Create the final refinement result with problem statement and council routing."""
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
        )


async def create_deep_analysis_agent(config: Dict[str, Any] = None) -> A9_Deep_Analysis_Agent:
    return await A9_Deep_Analysis_Agent.create(config or {})
