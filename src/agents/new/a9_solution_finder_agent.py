"""
A9 Solution Finder Agent (MVP with optional LLM debate)
- Implements SolutionFinderProtocol
- Generates/evaluates solution options, builds trade-off matrix
- Emits a single HITL event per cycle (per PRD)
- Optional: persona debate via A9_LLM_Service_Agent when enabled in config
"""
from __future__ import annotations

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
)
from src.agents.a9_llm_service_agent import (
    A9_LLM_AnalysisRequest,
    A9_LLM_AnalysisResponse,
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

    summary: Dict[str, Any] = {}
    plan = _model_to_dict(ctx.get("plan"))
    timeframe_map = _model_to_dict(ctx.get("timeframe_mapping"))

    def _first_str(value: Any) -> Optional[str]:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    kpi_name = None
    if isinstance(plan, dict):
        kpi_name = plan.get("kpi_name")
    if not kpi_name:
        kpi_name = ctx.get("kpi_name")
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

    scqa = _first_str(ctx.get("scqa_summary"))
    if scqa:
        summary["scqa_summary"] = scqa

    if isinstance(plan, dict):
        dims = plan.get("dimensions")
        if isinstance(dims, list) and dims:
            summary["dimension_focus"] = _limit([str(d) for d in dims if d], 6)

    change_points_raw = ctx.get("change_points") or []
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

    kt = _model_to_dict(ctx.get("kt_is_is_not"))
    if isinstance(kt, dict):
        summary["what_is_highlights"] = _collect_text_entries(kt.get("what_is"))
        summary["where_signals"] = _collect_text_entries(kt.get("where_is"))
        summary["when_signals"] = _collect_text_entries(kt.get("when_is"))

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
        try:
            audit_log: List[Dict[str, Any]] = []

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

            # FORCE LLM for debugging/MVP
            use_llm = True 
            
            # Fallback: Attempt to acquire LLM service if missing
            if use_llm and not self.orchestrator and not self.llm_service_agent:
                try:
                    print("DEBUG: Dependencies missing, attempting AgentRegistry lookup...")
                    from src.agents.new.a9_orchestrator_agent import AgentRegistry
                    self.llm_service_agent = await AgentRegistry.get_agent("A9_LLM_Service_Agent")
                    print(f"DEBUG: Acquired LLM Service via Registry: {self.llm_service_agent is not None}")
                except Exception as e:
                    print(f"DEBUG: Registry lookup failed: {e}")

            if use_llm:
                try:
                    print(f"DEBUG: Attempting LLM Debate. Orchestrator: {self.orchestrator is not None}, LLM Agent: {self.llm_service_agent is not None}")
                    # Build compact debate prompt content using provided context
                    da_ctx = request.deep_analysis_output or {}
                    da_summary = _extract_deep_analysis_summary(da_ctx)
                    print(f"DEBUG: da_summary keys: {list(da_summary.keys())}")
                    print(f"DEBUG: KPI in summary: {da_summary.get('kpi_name')}")
                    
                    # Derive a robust problem statement
                    ps_raw = (getattr(request, "problem_statement", None) or "").strip()
                    ps = ps_raw
                    
                    # FORCE KPI from summary if available, even if ps_raw is missing
                    target_kpi = da_summary.get("kpi_name") or "Business Metric"

                    if not ps:
                        # Construct robust problem statement from DA summary
                        kpi = da_summary.get("kpi_name")
                        change_points = da_summary.get("top_change_points", [])
                        
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
                                    direction = "dropped" if delta_val < 0 else "increased"
                                    # Use absolute for narrative
                                    delta_abs = f"{abs(delta_val):,.2f}"
                                except:
                                    delta_str = str(delta)
                                    direction = "changed"
                                    delta_abs = str(delta)
                                
                                try:
                                    val_str = f"{float(val):,.2f}"
                                except:
                                    val_str = str(val)
                                
                                ps_parts.append(f"{kpi} {direction} by {delta_abs} (Current Level: {val_str}).")
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

                    # Align with active situation context to avoid KPI mismatch
                    try:
                        sctx = getattr(request, "situation_context", None)
                        sctx_desc = sctx.get("description") if isinstance(sctx, dict) else getattr(sctx, "description", None)
                        sctx_kpi = sctx.get("kpi_name") if isinstance(sctx, dict) else getattr(sctx, "kpi_name", None)
                        if isinstance(sctx_desc, str) and sctx_desc.strip():
                            ps = sctx_desc.strip()
                        elif (not ps_raw) and sctx_kpi:
                            ps = f"KPI: {sctx_kpi} — generate actionable solution options."
                    except Exception:
                        pass
                    # Allow per-request persona override via preferences
                    try:
                        prefs = getattr(request, "preferences", None) or {}
                    except Exception:
                        prefs = {}
                    personas_override: List[str] = []
                    try:
                        cand = prefs.get("personas") if isinstance(prefs, dict) else None
                        if isinstance(cand, list):
                            personas_override = [str(p) for p in cand if p]
                    except Exception:
                        personas_override = []
                    personas_list = personas_override or (self.config.expert_personas or [])
                    personas = ", ".join(personas_list)

                    debate_spec = (
                        "## ROLE\n"
                        "You are a decision analyst preparing a structured briefing for executive stakeholders.\n\n"
                        "## TASK\n"
                        "Given the problem context, data analysis, and PRINCIPAL INPUT (priorities/constraints), generate a DECISION BRIEFING with:\n"
                        "1. Problem reframing (ensure shared understanding)\n"
                        "2. 2-3 concrete solution options with evidence-based analysis\n"
                        "3. For EACH option: strongest arguments FOR and AGAINST from multiple perspectives\n"
                        "4. Unresolved tensions requiring human judgment\n"
                        "5. Implementation considerations and decision triggers\n\n"
                        "## CONSTRAINTS\n"
                        "- Do NOT synthesize a single recommendation or consensus\n"
                        "- Do NOT simulate how real stakeholders would vote\n"
                        "- DO surface trade-offs, assumptions, and blind spots\n"
                        "- Each perspective must cite its reasoning basis\n"
                        "- MUST respect Principal Input constraints/vetoes if provided\n"
                        "- CRITICAL: The Deep Analysis is COMPLETE. Do NOT suggest 'more data gathering' or 'implementing analytics' as a primary solution. Focus on OPERATIONAL INTERVENTIONS to address the identified drivers.\n"
                        f"- CONTEXT: The analysis focuses on '{target_kpi}'. Ensure the Problem Reframe explicitly mentions this KPI.\n\n"
                        "## OUTPUT FORMAT (STRICT JSON)\n"
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
                        "      \"expected_impact\": 0.0-1.0,\n"
                        "      \"cost\": 0.0-1.0,\n"
                        "      \"risk\": 0.0-1.0,\n"
                        "      \"rationale\": \"...\",\n"
                        "      \"time_to_value\": \"...\",\n"
                        "      \"reversibility\": \"high|medium|low\",\n"
                        "      \"perspectives\": [\n"
                        "        {\n"
                        "          \"lens\": \"Financial\",\n"
                        "          \"arguments_for\": [\"...\"],\n"
                        "          \"arguments_against\": [\"...\"],\n"
                        "          \"key_questions\": [\"...\"]\n"
                        "        }\n"
                        "      ],\n"
                        "      \"implementation_triggers\": [\"...\"],\n"
                        "      \"prerequisites\": [\"...\"]\n"
                        "    }\n"
                        "  ],\n"
                        "  \"unresolved_tensions\": [\n"
                        "    {\n"
                        "      \"tension\": \"...\",\n"
                        "      \"options_affected\": [\"opt_1\", \"opt_2\"],\n"
                        "      \"requires\": \"human judgment|more data|stakeholder input\"\n"
                        "    }\n"
                        "  ],\n"
                        "  \"blind_spots\": [\"...\"],\n"
                        "  \"next_steps\": [\"...\"]\n"
                        "}\n"
                    )
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
                    dataset_recap = dataset_recap_lines if dataset_recap_lines else None

                    # Fallback Business Context from registry if missing (MVP Enhancement)
                    bc = getattr(request, "business_context", None)
                    if not bc:
                         # Attempt to load specific Bicycle Retail context
                         try:
                             import yaml
                             import os
                             # Hardcoded path for MVP, would normally come from a Registry Service
                             ctx_path = r"c:\Users\barry\CascadeProjects\Agent9-HERMES\src\registry_references\business_context\bicycle_retail_context.yaml"
                             if os.path.exists(ctx_path):
                                 with open(ctx_path, "r", encoding="utf-8") as f:
                                     bc = yaml.safe_load(f)
                         except Exception as e:
                             print(f"DEBUG: Failed to load context yaml: {e}")
                             pass
                         
                         if not bc:
                             bc = {
                                 "business_terms": {
                                     "profit_center": "Operational unit responsible for generating revenue and managing costs.",
                                     "customer_type": "Segment classification (Enterprise, SMB, Gov)."
                                 },
                                 "supported_processes": [
                                     "Finance: Profitability Analysis",
                                     "Finance: Expense Management"
                                 ]
                             }
                         
                         try:
                            request.business_context = bc
                         except:
                            pass

                    content = {
                        "problem": ps,
                        "deep_analysis_context": trimmed_da,
                        "deep_analysis_summary": da_summary,
                        "dataset_recap": dataset_recap,
                        "debate_spec": debate_spec,
                        "user_context": user_ctx,
                        "principal_input": _model_to_dict(principal_input) if principal_input else None,
                    }
                    import json as _json
                    analysis_payload = _json.dumps(content)

                    analysis_req = A9_LLM_AnalysisRequest(
                        request_id=req_id,
                        principal_id=getattr(request, "principal_id", None),
                        timestamp=getattr(request, "timestamp", None),
                        principal_context=getattr(request, "principal_context", None),
                        situation_context=getattr(request, "situation_context", None),
                        business_context=getattr(request, "business_context", None),
                        content=analysis_payload,
                        analysis_type="custom",
                        context="Respond ONLY with valid JSON matching the required keys and numeric fields in [0,1].",
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
                            # Use parsed content dict for readability
                            "content": content,
                        })
                    except Exception:
                        pass

                    # Prefer orchestrator routing per LLM PRD; fallback to direct agent if missing
                    if self.orchestrator is not None:
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
                    audit_log.append({
                        "event": "llm_debate_completed",
                        "status": getattr(llm_resp, "status", None),
                        "model_used": model_used,
                    })

                    parsed = getattr(llm_resp, "analysis", None) if llm_ok else None
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
                                        prerequisites=o.get("prerequisites", [])
                                    )
                                )
                            except Exception:
                                continue

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

                        # Fallback rationale
                        rationale = "Options generated via Decision Briefing analysis."

                        # Add briefing dump to audit log
                        audit_log.append({
                            "event": "decision_briefing_generated",
                            "problem_reframe": problem_reframe,
                            "unresolved_tensions": [t.model_dump() for t in unresolved_tensions_list],
                            "blind_spots": blind_spots_list
                        })

                except Exception as le:
                    # LLM path failed; fall back to heuristic
                    print(f"DEBUG: LLM Debate FAILED: {le}")
                    import traceback
                    traceback.print_exc()
                    self.logger.info(f"LLM debate path failed, falling back to heuristic: {le}")
                    audit_log.append({"event": "llm_debate_error", "error": str(le)})

            # Heuristic fallback or augmentation if LLM didn't yield options
            if not options:
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
                audit_log=[{"event": "ranked_options", "count": len(options_payload)}] + audit_log,
                # Enhanced Decision Briefing Fields
                problem_reframe=problem_reframe,
                unresolved_tensions=unresolved_tensions_list,
                blind_spots=blind_spots_list,
                next_steps=next_steps_list,
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
