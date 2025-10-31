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
)
from src.agents.models.data_governance_models import KPIDataProductMappingRequest


logger = logging.getLogger(__name__)


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
        try:
            here = os.path.dirname(__file__)
            # From src/agents/new -> src
            src_dir = os.path.abspath(os.path.join(here, "..", ".."))
            candidate = os.path.join(src_dir, "contracts", "fi_star_schema.yaml")
            if os.path.exists(candidate):
                return candidate
            # Fallback: from project root -> src/contracts/...
            proj_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
            # here=src/agents/new -> proj_root=src; contract at src/contracts/fi_star_schema.yaml
            alt2 = os.path.join(proj_root, "contracts", "fi_star_schema.yaml")
            if os.path.exists(alt2):
                return alt2
            # Fallback: CWD-based absolute
            cwd_alt = os.path.abspath(os.path.join(os.getcwd(), "src", "contracts", "fi_star_schema.yaml"))
            if os.path.exists(cwd_alt):
                return cwd_alt
            # Last resort: repo-relative string (may still work if cwd = project root)
            return "src/contracts/fi_star_schema.yaml"
        except Exception:
            return "src/contracts/fi_star_schema.yaml"

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

    def _trend_positive(self, kpi_name: str) -> bool:
        s = (kpi_name or "").lower()
        return not any(w in s for w in ("expense", "cost", "deduction"))

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
                target_count = int(getattr(request, "target_count", self.config.max_dimensions) or self.config.max_dimensions)
            except Exception:
                target_count = self.config.max_dimensions
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
                                    dimensions = [str(d) for d in dims if d]
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
                self.logger.info(f"execute_deep_analysis: kpi={getattr(plan, 'kpi_name', None)} timeframe={getattr(plan, 'timeframe', None)} dims_in={len(getattr(plan, 'dimensions', []) or [])}")
            except Exception:
                pass
            kt = KTIsIsNot()
            # What is
            if getattr(plan, "kpi_name", None):
                kt.what_is.append({"kpi_name": plan.kpi_name})
            if getattr(plan, "timeframe", None):
                kt.what_is.append({"timeframe": plan.timeframe})
            kt.what_is.append({"filters_present": bool(getattr(plan, "filters", None))})

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

                    # Primary path: hierarchical drill per vector if hierarchies present
                    hmap = _hierarchies_from_contract()
                    used_hierarchical = False
                    if hmap:
                        used_hierarchical = True
                        spec = _pick_threshold_spec()
                        comparator = "budget" if str(spec.get("comparison_type", "")).lower() == "budget" else "previous"
                        # Default vector order
                        vector_order = [k for k in ["customer", "product", "profit_center"] if k in hmap] or list(hmap.keys())
                        for vec in vector_order:
                            levels = hmap.get(vec, []) or []
                            for lvl in levels:
                                grp = await _maps_for_level(lvl, comparator)
                                if not grp:
                                    continue
                                breaches, within = _classify(grp, spec)
                                if breaches:
                                    for b in breaches:
                                        kt.where_is.append({"dimension": b.get("dimension"), "key": b.get("key"), "delta": b.get("delta"), "current": b.get("current"), "previous": b.get("previous")})
                                        change_points.append(ChangePoint(dimension=b.get("dimension"), key=b.get("key"), current_value=b.get("current"), previous_value=b.get("previous"), delta=b.get("delta")))
                                    for w in within:
                                        kt.where_is_not.append({"dimension": w.get("dimension"), "key": w.get("key"), "delta": w.get("delta"), "current": w.get("current"), "previous": w.get("previous")})
                                    break  # stop drilling this vector at first breach level
                                else:
                                    # All within threshold at this level
                                    kt.where_is.append({"dimension": lvl, "key": "All", "note": "All within threshold"})
                                    # Continue to next finer level
                                    continue
                            # proceed to next vector

                    # WHERE (dimension values with greatest variance) fallback (legacy Top/Bottom N)
                    if not used_hierarchical:
                        for dim in dims[: max(1, min(len(dims), self.config.max_dimensions))]:
                            try:
                                # Prefer single-shot delta ranking via DPA TopN metric
                                top_req = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def,
                                    timeframe=cur_tf,
                                    filters=getattr(plan, "filters", None),
                                    breakdown=True,
                                    override_group_by=[dim],
                                    topn={"type": "top", "n": 3, "metric": "delta_prev"}
                                )
                                if top_req.get("success"):
                                    top_exec = await self.data_product_agent.execute_sql(top_req.get("sql"))
                                    queries_executed += 1
                                    rows = top_exec.get("rows") or []
                                    cols = [str(c) for c in (top_exec.get("columns") or [])]
                                    # Determine column names or fallback positions
                                    key_col = cols[0] if cols else None
                                    c_col = "current_value" if "current_value" in cols else (cols[1] if len(cols) > 1 else None)
                                    p_col = "previous_value" if "previous_value" in cols else (cols[2] if len(cols) > 2 else None)
                                    d_col = "delta_prev" if "delta_prev" in cols else (cols[3] if len(cols) > 3 else None)
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
                                            kt.where_is.append({"dimension": dim, "key": key, "delta": d, "current": c, "previous": p})
                                            change_points.append(ChangePoint(dimension=dim, key=key, current_value=c, previous_value=p, delta=d))
                                        except Exception:
                                            continue
                                # Bottom (least variance) list
                                bot_req = await self.data_product_agent.generate_sql_for_kpi(
                                    kpi_def,
                                    timeframe=cur_tf,
                                    filters=getattr(plan, "filters", None),
                                    breakdown=True,
                                    override_group_by=[dim],
                                    topn={"type": "bottom", "n": 3, "metric": "delta_prev"}
                                )
                                if bot_req.get("success"):
                                    bot_exec = await self.data_product_agent.execute_sql(bot_req.get("sql"))
                                    queries_executed += 1
                                    rows = bot_exec.get("rows") or []
                                    cols_b = [str(c) for c in (bot_exec.get("columns") or [])]
                                    key_col_b = cols_b[0] if cols_b else None
                                    c_col_b = "current_value" if "current_value" in cols_b else (cols_b[1] if len(cols_b) > 1 else None)
                                    p_col_b = "previous_value" if "previous_value" in cols_b else (cols_b[2] if len(cols_b) > 2 else None)
                                    d_col_b = "delta_prev" if "delta_prev" in cols_b else (cols_b[3] if len(cols_b) > 3 else None)
                                    for r in rows:
                                        try:
                                            if isinstance(r, dict):
                                                key = str(r.get(key_col_b)) if key_col_b else None
                                                c_raw = r.get(c_col_b) if isinstance(c_col_b, str) else (None if c_col_b is None else list(r.values())[1])
                                                p_raw = r.get(p_col_b) if isinstance(p_col_b, str) else (None if p_col_b is None else list(r.values())[2])
                                                d_raw = r.get(d_col_b) if isinstance(d_col_b, str) else (None if d_col_b is None else list(r.values())[3])
                                                c = float(c_raw) if c_raw is not None else 0.0
                                                p = float(p_raw) if p_raw is not None else 0.0
                                                d = float(d_raw) if d_raw is not None else (c - p)
                                            else:
                                                key = str(r[0])
                                                c = float(r[1]) if r[1] is not None else 0.0
                                                p = float(r[2]) if r[2] is not None else 0.0
                                                d = float(r[3]) if r[3] is not None else (c - p)
                                            kt.where_is_not.append({"dimension": dim, "key": key, "delta": d, "current": c, "previous": p})
                                        except Exception:
                                            continue
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
                                        # Sort by absolute variance descending
                                        diffs.sort(key=lambda t: abs(t[3]), reverse=True)
                                        for k, c, p, d in diffs[:3]:
                                            kt.where_is.append({"dimension": dim, "key": k, "delta": d, "current": c, "previous": p})
                                            change_points.append(ChangePoint(dimension=dim, key=k, current_value=c, previous_value=p, delta=d))
                                        diffs_sorted_low = sorted(diffs, key=lambda t: abs(t[3]))
                                        for k, c, p, d in diffs_sorted_low[:3]:
                                            kt.where_is_not.append({"dimension": dim, "key": k, "delta": d, "current": c, "previous": p})
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
                                    kt.when_is.append({"bucket": b, "delta": d, "current": c, "previous": p})
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
                                    kt.when_is_not.append({"bucket": b, "delta": d, "current": c, "previous": p})
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
                                kt.when_is.append({"bucket": k, "delta": d, "current": c, "previous": p})
                            diffs_t_low = sorted(diffs_t, key=lambda t: abs(t[3]))
                            for k, c, p, d in diffs_t_low[:3]:
                                kt.when_is_not.append({"bucket": k, "delta": d, "current": c, "previous": p})
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
            return DeepAnalysisResponse.success(
                request_id=req_id,
                plan=plan,
                scqa_summary=scqa_summary,
                kt_is_is_not=kt,
                change_points=change_points,
                percent_growth_enabled=False,
                timeframe_mapping={"current": getattr(plan, "timeframe", None), "previous": self._prev_timeframe(getattr(plan, "timeframe", None))},
                dimensions_suggested=getattr(plan, "dimensions", [])
            )
        except Exception as e:
            return DeepAnalysisResponse.error(request_id=req_id, error_message=str(e))


async def create_deep_analysis_agent(config: Dict[str, Any] = None) -> A9_Deep_Analysis_Agent:
    return await A9_Deep_Analysis_Agent.create(config or {})
