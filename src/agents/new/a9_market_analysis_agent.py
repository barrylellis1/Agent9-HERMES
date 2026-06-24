"""
A9 Market Analysis Agent

Retrieves external market signals relevant to a KPI anomaly and synthesises them
into an executive-ready narrative using A9_LLM_Service_Agent.

Pipeline:
    1. Build a targeted search query from (kpi_name, industry, kpi_context).
    2. Call PerplexityService to fetch web-search results (signals + citations).
    3. Convert Perplexity citations into MarketSignal objects.
    4. Send signals + kpi_context to A9_LLM_Service_Agent (claude-sonnet-4-6) for synthesis.
    5. Return MarketAnalysisResponse with signals, synthesis, and confidence.

Graceful degradation:
    - If PERPLEXITY_API_KEY is not set the agent skips step 2/3 and synthesises
      from kpi_context alone (LLM-only mode).
    - If the LLM service is unavailable, synthesis falls back to a formatted
      summary of the raw signal text.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
import json
from typing import Any, Dict, List, Optional, Tuple

from src.agents.agent_config_models import A9_Market_Analysis_Agent_Config
from src.agents.models.kpi_template_models import (
    BenchmarkSource,
    CompanyKPIProfile,
    CompanyResearchRequest,
    TemplateKPI,
)
from src.agents.models.market_analysis_models import (
    MarketAnalysisRequest,
    MarketAnalysisResponse,
    MarketSignal,
)
from src.agents.new.a9_llm_service_agent import (
    A9_LLM_AnalysisRequest,
    A9_LLM_AnalysisResponse,
)
from src.llm_services.claude_service import ClaudeTaskType, get_claude_model_for_task
from src.llm_services.perplexity_service import PerplexityService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Synthesis model — use SYNTHESIS task routing so env-var overrides work
# ---------------------------------------------------------------------------
_SYNTHESIS_MODEL = get_claude_model_for_task(ClaudeTaskType.SYNTHESIS)


class A9_Market_Analysis_Agent:
    """
    Market Analysis Agent.

    Discovers external market trends related to a KPI anomaly and synthesises
    them into an executive briefing via the A9_LLM_Service_Agent.

    Registration:
        The AgentBootstrap discovers this class automatically because:
          - class name starts with ``A9_`` and ends with ``_Agent``
          - ``create`` is an async classmethod
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> "A9_Market_Analysis_Agent":
        """
        Factory method — registered with AgentBootstrap.

        Creates the agent, opens the Perplexity HTTP client, and discovers the
        LLM service from AgentRegistry when available.
        """
        inst = cls(config or {})
        await inst.connect()
        return inst

    def __init__(self, config: Dict[str, Any]) -> None:
        self.name = "A9_Market_Analysis_Agent"
        self.version = "0.1.0"
        self.config = A9_Market_Analysis_Agent_Config(**(config or {}))
        self._perplexity: Optional[PerplexityService] = None
        self._llm_service: Optional[Any] = None
        self.orchestrator: Optional[Any] = None

    async def connect(self, orchestrator: Any = None) -> bool:
        """
        Open external connections and discover the LLM service.

        Args:
            orchestrator: Optional A9_Orchestrator_Agent instance. When supplied the
                          agent resolves A9_LLM_Service_Agent through it; otherwise
                          it falls back to a direct AgentRegistry lookup.
        """
        try:
            self.orchestrator = orchestrator

            # Initialise Perplexity client when enabled
            if self.config.enable_perplexity:
                self._perplexity = PerplexityService()
                await self._perplexity.connect()
                logger.info("%s: Perplexity service connected", self.name)

            # Resolve LLM service via orchestrator or direct registry
            if orchestrator is not None:
                try:
                    self._llm_service = await orchestrator.get_agent("A9_LLM_Service_Agent")
                except Exception as exc:
                    logger.warning("%s: LLM service lookup via orchestrator failed: %s", self.name, exc)
            else:
                try:
                    from src.agents.new.a9_orchestrator_agent import AgentRegistry

                    self._llm_service = await AgentRegistry.get_agent("A9_LLM_Service_Agent")
                except Exception as exc:
                    logger.warning(
                        "%s: LLM service lookup via AgentRegistry failed: %s", self.name, exc
                    )

            logger.info("%s: connected (perplexity=%s, llm=%s)",
                        self.name,
                        self._perplexity is not None,
                        self._llm_service is not None)
            return True
        except Exception as exc:
            logger.error("%s: connect error: %s", self.name, exc)
            return False

    async def disconnect(self) -> None:
        """Close Perplexity HTTP client and release resources."""
        if self._perplexity is not None:
            try:
                await self._perplexity.disconnect()
            except Exception as exc:
                logger.warning("%s: error closing Perplexity client: %s", self.name, exc)
        logger.info("%s: disconnected", self.name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_market(self, request: MarketAnalysisRequest) -> MarketAnalysisResponse:
        """
        Core entrypoint.  Runs the full pipeline:
            search → signal parsing → LLM synthesis → response.

        Args:
            request: MarketAnalysisRequest with kpi_name, kpi_context, industry, etc.

        Returns:
            MarketAnalysisResponse with signals, synthesis narrative, and confidence.
        """
        if self.config.log_all_requests:
            logger.info(
                "%s: analyze_market called — session=%s kpi=%s industry=%s",
                self.name, request.session_id, request.kpi_name, request.industry,
            )

        signals: List[MarketSignal] = []
        sources_queried: List[str] = []
        error_msg: Optional[str] = None

        # ------------------------------------------------------------------
        # Step 1 — Perplexity web search (skipped if disabled or key missing)
        # ------------------------------------------------------------------
        raw_answer = ""
        if self.config.enable_perplexity and self._perplexity is not None:
            try:
                query = self._build_search_query(request)
                sources_queried.append("perplexity")
                logger.info("%s: Perplexity query: %s", self.name, query)

                result = await self._perplexity.search(query, max_results=request.max_signals)
                raw_answer = result.get("answer", "")
                citations = result.get("citations", [])

                signals = self._parse_citations(
                    citations=citations,
                    fallback_answer=raw_answer,
                    max_signals=request.max_signals,
                )
                if result.get("error"):
                    error_msg = f"Perplexity search error: {result['error']}"
            except Exception as exc:
                logger.warning("%s: Perplexity search failed: %s", self.name, exc)
                error_msg = str(exc)
        else:
            logger.info(
                "%s: Perplexity skipped (enable_perplexity=%s, client=%s)",
                self.name, self.config.enable_perplexity, self._perplexity is not None,
            )
            # LLM-only fallback: generate structured signals from model knowledge
            if self._llm_service is not None or self.orchestrator is not None:
                signals = await self._llm_generate_signals(request)
                if signals:
                    sources_queried.append("llm_knowledge")
                    logger.info("%s: LLM-generated %d signal(s)", self.name, len(signals))

        # ------------------------------------------------------------------
        # Step 1b — LLM fallback if Perplexity returned no signals
        # ------------------------------------------------------------------
        if not signals and (self._llm_service is not None or self.orchestrator is not None):
            signals = await self._llm_generate_signals(request)
            if signals:
                sources_queried.append("llm_knowledge")
                logger.info("%s: LLM fallback generated %d signal(s)", self.name, len(signals))

        # ------------------------------------------------------------------
        # Step 2 — LLM synthesis (also produces conflict assessment)
        # ------------------------------------------------------------------
        synthesis, conflict = await self._synthesize(request, signals, raw_answer)

        # ------------------------------------------------------------------
        # Step 3 — Confidence score heuristic
        # ------------------------------------------------------------------
        confidence = self._compute_confidence(signals, synthesis)

        return MarketAnalysisResponse(
            session_id=request.session_id,
            kpi_name=request.kpi_name,
            signals=signals,
            synthesis=synthesis,
            conflict=conflict,
            competitor_context=None,  # Reserved for future enrichment
            confidence=confidence,
            sources_queried=sources_queried,
            error=error_msg,
            timestamp=datetime.utcnow().isoformat(),
        )

    # ------------------------------------------------------------------
    # Phase 12A — Company Intelligence KPI Template Generator
    # ------------------------------------------------------------------

    async def research_company_kpi_profile(
        self, request: CompanyResearchRequest
    ) -> CompanyKPIProfile:
        """
        Phase 12A entrypoint — research a company's public footprint and produce
        a benchmark-anchored KPI template profile.

        Pipeline:
            1. Build 4 targeted Perplexity queries (filings, segments, peer
               benchmarks, strategic priorities)
            2. Run all 4 in parallel via asyncio.gather
            3. Synthesise via Sonnet into a structured CompanyKPIProfile
            4. M4 fallback: when Perplexity is unavailable, run LLM-only mode
               and mark `degraded=True`; all benchmark_source values become
               'inferred'

        Returns:
            CompanyKPIProfile — never raises; failures degrade gracefully.
        """
        if self.config.log_all_requests:
            logger.info(
                "%s: research_company_kpi_profile — company=%s industry_hint=%s client=%s",
                self.name,
                request.company_name,
                request.industry_hint,
                request.client_id,
            )

        use_perplexity = (
            self.config.enable_perplexity
            and self._perplexity is not None
            and bool(getattr(self._perplexity, "api_key", ""))
        )

        if not use_perplexity:
            logger.info(
                "%s: Perplexity unavailable — running LLM-only company profile (degraded mode)",
                self.name,
            )
            return await self._llm_only_company_profile(request)

        # Run 4 parallel web searches; collect raw answers + citations
        queries = self._build_company_search_queries(request)
        try:
            raw_results = await asyncio.gather(
                *[self._perplexity.search(q, max_results=5) for q in queries],
                return_exceptions=True,
            )
        except Exception as exc:
            logger.warning("%s: parallel Perplexity searches failed: %s", self.name, exc)
            raw_results = []

        # Filter out exceptions / errored payloads
        clean_results: List[Dict[str, Any]] = [
            r for r in raw_results
            if isinstance(r, dict) and not r.get("error") and r.get("answer")
        ]

        if not clean_results:
            logger.warning(
                "%s: all 4 Perplexity searches returned empty/error — falling back to LLM-only",
                self.name,
            )
            return await self._llm_only_company_profile(request)

        profile = await self._synthesize_company_profile(request, clean_results, queries)
        return profile

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_search_query(self, request: MarketAnalysisRequest) -> str:
        """Compose a search query that scans market conditions independently of the DA conclusion."""
        bc = request.business_context or {}
        da = request.da_structural_context or {}
        industry_part = f" {request.industry}" if request.industry else ""
        subindustry = bc.get("subindustry") or ""
        products = bc.get("products_services") or []
        product_terms = " ".join(products[:2]) if products else ""
        # Include top change-point segment names for specificity (neutral structural fact)
        cp_terms = " ".join((da.get("change_point_segments") or [])[:2])
        specificity = f" {subindustry}" if subindustry else ""
        specificity += f" {product_terms}" if product_terms else ""
        specificity += f" {cp_terms}" if cp_terms else ""
        return (
            f"{request.kpi_name}{industry_part}{specificity} market conditions headwinds tailwinds "
            f"2025 2026 commodity prices competitive dynamics supply chain"
        )

    def _parse_citations(
        self,
        citations: List[Any],
        fallback_answer: str,
        max_signals: int,
    ) -> List[MarketSignal]:
        """
        Convert Perplexity citation objects into MarketSignal models.

        Perplexity citations are plain strings (URLs) or dicts.  We normalise
        both forms.  When fewer than ``max_signals`` citations exist but a
        non-empty answer was returned, we add one synthetic signal derived from
        the answer text.
        """
        signals: List[MarketSignal] = []

        for i, citation in enumerate(citations[:max_signals]):
            if isinstance(citation, str):
                # citation is just a URL
                signals.append(
                    MarketSignal(
                        source="perplexity",
                        title=f"Market signal {i + 1}",
                        summary=fallback_answer[:300] if fallback_answer else "(no summary)",
                        relevance_score=0.7,
                        url=citation,
                    )
                )
            elif isinstance(citation, dict):
                signals.append(
                    MarketSignal(
                        source=citation.get("source", "perplexity"),
                        title=citation.get("title") or f"Market signal {i + 1}",
                        summary=citation.get("snippet") or citation.get("text") or "(no summary)",
                        relevance_score=float(citation.get("relevance_score", 0.7)),
                        published_at=citation.get("published_at"),
                        url=citation.get("url"),
                    )
                )

        # Synthetic signal from the raw answer when no structured citations were returned
        if not signals and fallback_answer.strip():
            signals.append(
                MarketSignal(
                    source="perplexity",
                    title="Market intelligence summary",
                    summary=fallback_answer[:500],
                    relevance_score=0.6,
                )
            )

        return signals

    async def _llm_generate_signals(
        self, request: MarketAnalysisRequest
    ) -> List[MarketSignal]:
        """
        Generate structured MarketSignal objects via LLM when Perplexity is unavailable.

        Asks the LLM to return a JSON array of signals based on its training knowledge
        of the KPI, industry, and known market dynamics.  Returns an empty list on any
        failure so the caller degrades gracefully.
        """
        import json as _json
        import re as _re

        bc = request.business_context or {}
        da = request.da_structural_context or {}
        industry_label = request.industry or bc.get("industry") or "the relevant industry"
        subindustry = bc.get("subindustry") or ""
        products = bc.get("products_services") or []
        regions = bc.get("regions") or []

        # Build enriched context block from registry + DA structural facts
        ctx_lines: list[str] = []
        if subindustry:
            ctx_lines.append(f"Sub-sector: {subindustry}")
        if products:
            ctx_lines.append(f"Core products/services: {', '.join(products[:4])}")
        if regions:
            ctx_lines.append(f"Operating regions: {', '.join(regions[:3])}")
        if da.get("dimensions"):
            ctx_lines.append(f"Business dimensions analyzed: {', '.join(da['dimensions'][:5])}")
        if da.get("active_segments"):
            ctx_lines.append(f"Active market segments: {', '.join(da['active_segments'][:5])}")
        if da.get("change_point_segments"):
            ctx_lines.append(f"Segments with notable activity: {', '.join(da['change_point_segments'][:3])}")
        ctx_block = (
            "\nBusiness context:\n" + "\n".join(f"  - {l}" for l in ctx_lines) + "\n"
            if ctx_lines else ""
        )

        prompt = (
            f"You are a market intelligence analyst with deep expertise in {industry_label}.\n"
            f"{ctx_block}\n"
            f"Produce {request.max_signals} distinct external market signals covering current "
            f"conditions specifically affecting '{request.kpi_name}' in this business.\n\n"
            f"IMPORTANT: Generate an INDEPENDENT, BALANCED scan — do NOT bias signals toward "
            f"confirming any particular internal finding. Include BOTH:\n"
            f"- Headwinds: factors that create cost pressure, demand weakness, margin compression, "
            f"supply disruption, or pricing difficulty\n"
            f"- Tailwinds: factors enabling cost reduction, demand growth, margin expansion, or "
            f"competitive advantage\n\n"
            f"Focus signals on commodity/input prices, competitive dynamics, demand trends, "
            f"regulatory/macro factors, and supply chain conditions specifically relevant to "
            f"the business context above. Be specific to the actual segments and dimensions listed.\n\n"
            f"Return ONLY valid JSON with this exact structure (no other text):\n"
            f'{{"signals": [\n'
            f'  {{"title": "Brief headline", "summary": "1-2 sentence explanation of the signal and its relevance", '
            f'"source": "llm_knowledge", "relevance_score": 0.85}}\n'
            f']}}\n\n'
            f"relevance_score must be a float between 0 and 1. Be specific and quantitative."
        )

        try:
            from src.agents.new.a9_llm_service_agent import A9_LLM_Request

            gen_req = A9_LLM_Request(
                request_id=str(uuid.uuid4()),
                principal_id=request.principal_id or "system",
                prompt=prompt,
                system_prompt="You are a market intelligence analyst. Return only valid JSON, no other text.",
                model=_SYNTHESIS_MODEL,
                operation="generate",
                temperature=0.3,
            )

            if self.orchestrator is not None:
                llm_resp = await self.orchestrator.execute_agent_method(
                    "A9_LLM_Service_Agent", "generate", {"request": gen_req}
                )
            else:
                llm_resp = await self._llm_service.generate(gen_req)

            if getattr(llm_resp, "status", "error") != "success":
                logger.warning("%s: LLM generate returned non-success: %s", self.name, getattr(llm_resp, "status", "?"))
                return []

            raw_text = getattr(llm_resp, "content", "") or ""
            # Strip markdown code fences if present
            raw_text = raw_text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text[raw_text.index("\n") + 1:] if "\n" in raw_text else raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:raw_text.rfind("```")].rstrip()

            # Parse the {"signals": [...]} object
            parsed = _json.loads(raw_text)
            raw_signals = parsed.get("signals", []) if isinstance(parsed, dict) else []

            signals: List[MarketSignal] = []
            for item in raw_signals[:request.max_signals]:
                if not isinstance(item, dict):
                    continue
                try:
                    signals.append(MarketSignal(
                        source=str(item.get("source", "llm_knowledge")),
                        title=str(item.get("title", "Market Signal")),
                        summary=str(item.get("summary", "")),
                        relevance_score=min(1.0, max(0.0, float(item.get("relevance_score", 0.7)))),
                    ))
                except Exception:
                    continue
            return signals

        except Exception as exc:
            logger.warning("%s: LLM signal generation failed: %s", self.name, exc)
            return []

    async def _synthesize(
        self,
        request: MarketAnalysisRequest,
        signals: List[MarketSignal],
        raw_answer: str,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Build the synthesis narrative via A9_LLM_Service_Agent.

        Also performs conflict detection: if analysis_mode is supplied, the LLM
        is asked whether the external signals confirm or contradict the internal
        DA conclusion. Returns (synthesis_text, conflict_dict).

        Falls back to a formatted plain-text summary when the LLM service is
        unavailable, so the caller always receives a usable string.
        """
        bc = request.business_context or {}
        da = request.da_structural_context or {}
        industry_label = request.industry or bc.get("industry") or "the relevant"
        subindustry = bc.get("subindustry") or ""
        products = bc.get("products_services") or []
        bc_detail = ""
        detail_parts = []
        if subindustry:
            detail_parts.append(subindustry)
        if products:
            detail_parts.append(f"products: {', '.join(products[:3])}")
        if da.get("active_segments"):
            detail_parts.append(f"segments: {', '.join(da['active_segments'][:3])}")
        if detail_parts:
            bc_detail = f" ({'; '.join(detail_parts)})"
        formatted_signals = self._format_signals_for_prompt(signals, raw_answer)

        # Build conflict-detection clause when the caller supplied analysis_mode
        analysis_mode = request.analysis_mode
        if analysis_mode:
            mode_label = {
                "opportunity": "an OPPORTUNITY (internal data shows positive trajectory)",
                "problem": "a PROBLEM (internal data shows negative trajectory)",
                "mixed": "a MIXED situation (some segments improving, others declining)",
            }.get(analysis_mode, analysis_mode)
            conflict_clause = (
                f"\n\nCONFLICT DETECTION:\n"
                f"The internal data analysis has classified this as {mode_label}.\n"
                f"Assess whether the external market signals CONFIRM or CONTRADICT that conclusion.\n"
                f"A contradiction means:\n"
                f"  - Internal = opportunity, but signals show headwinds (cost pressure, demand softness, margin compression)\n"
                f"  - Internal = problem, but signals show tailwinds (market growth, demand recovery, pricing power)\n"
            )
            conflict_json_schema = (
                '"conflict": {\n'
                '    "detected": true or false,\n'
                '    "type": "headwind_vs_opportunity" | "tailwind_vs_problem" | null,\n'
                '    "confidence": 0.0 to 1.0,\n'
                '    "summary": "One sentence explaining the conflict, or null if none"\n'
                '  }'
            )
        else:
            conflict_clause = ""
            conflict_json_schema = '"conflict": null'

        prompt = (
            f"You are a market intelligence analyst. Analyse these external market signals about "
            f"'{request.kpi_name}' in the {industry_label}{bc_detail} industry.\n\n"
            f"Internal business context: {request.kpi_context}"
            f"{conflict_clause}\n\n"
            f"Market Signals:\n{formatted_signals}\n\n"
            f"Return a JSON object with exactly this structure:\n"
            f"{{\n"
            f'  "synthesis": "2-3 paragraph executive briefing covering: (1) key external factors '
            f'driving this KPI movement, (2) competitive context and industry benchmarks, '
            f'(3) implications for the business. Be specific and quantitative.",\n'
            f"  {conflict_json_schema}\n"
            f"}}\n\n"
            f"Return only valid JSON. No markdown, no preamble."
        )

        if self._llm_service is None and self.orchestrator is None:
            logger.warning(
                "%s: LLM service unavailable — returning plain-text synthesis fallback", self.name
            )
            return self._plain_text_fallback(request, signals, raw_answer), None

        try:
            analysis_req = A9_LLM_AnalysisRequest(
                request_id=str(uuid.uuid4()),
                principal_id=request.principal_id or "system",
                content=prompt,
                analysis_type="custom",
                context="",
                model=_SYNTHESIS_MODEL,
            )

            # Route through orchestrator when available, otherwise call directly
            if self.orchestrator is not None:
                llm_resp = await self.orchestrator.execute_agent_method(
                    "A9_LLM_Service_Agent", "analyze", {"request": analysis_req}
                )
            else:
                llm_resp = await self._llm_service.analyze(analysis_req)

            if getattr(llm_resp, "status", "error") == "success":
                analysis = getattr(llm_resp, "analysis", {})
                raw_text = ""
                if isinstance(analysis, dict):
                    raw_text = (
                        analysis.get("text")
                        or analysis.get("content")
                        or analysis.get("response")
                        or ""
                    )
                    # If analysis dict itself has "synthesis" key, it may already be parsed
                    if "synthesis" in analysis:
                        return str(analysis["synthesis"]), analysis.get("conflict")
                else:
                    raw_text = str(analysis)

                # Parse the JSON response
                if raw_text:
                    try:
                        parsed = json.loads(raw_text)
                        synthesis_text = parsed.get("synthesis") or raw_text
                        conflict_data = parsed.get("conflict")
                        return str(synthesis_text), conflict_data
                    except (json.JSONDecodeError, ValueError):
                        # LLM returned plain text despite instructions — use as-is
                        return raw_text, None

                return str(analysis), None

            logger.warning(
                "%s: LLM synthesis returned non-success status: %s",
                self.name,
                getattr(llm_resp, "status", "unknown"),
            )
            return self._plain_text_fallback(request, signals, raw_answer), None

        except Exception as exc:
            logger.error("%s: LLM synthesis error: %s", self.name, exc)
            return self._plain_text_fallback(request, signals, raw_answer), None

    def _format_signals_for_prompt(
        self, signals: List[MarketSignal], raw_answer: str
    ) -> str:
        """Format MarketSignal list into a prompt-friendly string."""
        if not signals:
            return raw_answer.strip() if raw_answer.strip() else "(No external signals available)"

        lines: List[str] = []
        for i, sig in enumerate(signals, start=1):
            lines.append(
                f"{i}. [{sig.source.upper()}] {sig.title}\n"
                f"   Summary: {sig.summary}\n"
                f"   Relevance: {sig.relevance_score:.0%}"
                + (f"\n   URL: {sig.url}" if sig.url else "")
            )
        return "\n\n".join(lines)

    def _plain_text_fallback(
        self,
        request: MarketAnalysisRequest,
        signals: List[MarketSignal],
        raw_answer: str,
    ) -> str:
        """Return a human-readable summary without LLM assistance."""
        lines = [
            f"Market analysis for {request.kpi_name}",
            f"Context: {request.kpi_context}",
        ]
        if signals:
            lines.append(f"\n{len(signals)} external signal(s) retrieved:")
            for sig in signals:
                lines.append(f"  - {sig.title}: {sig.summary}")
        elif raw_answer:
            lines.append(f"\nPerplexity summary: {raw_answer[:500]}")
        else:
            lines.append(
                "\nNo external market signals were retrieved. "
                "Consider setting PERPLEXITY_API_KEY for live market data."
            )
        return "\n".join(lines)

    def _compute_confidence(self, signals: List[MarketSignal], synthesis: str) -> float:
        """
        Heuristic confidence score.

        - Base: 0.3 (LLM-only, no signals)
        - Each signal adds 0.1 (capped at 0.5 total signal contribution)
        - Non-empty synthesis adds 0.2
        """
        signal_contribution = min(len(signals) * 0.1, 0.5)
        synthesis_contribution = 0.2 if synthesis and len(synthesis) > 50 else 0.0
        return round(min(0.3 + signal_contribution + synthesis_contribution, 1.0), 2)

    # ------------------------------------------------------------------
    # Phase 12A helpers
    # ------------------------------------------------------------------

    def _build_company_search_queries(
        self, request: CompanyResearchRequest
    ) -> List[str]:
        """Return the 4 parallel Perplexity queries for Phase 12A research."""
        name = request.company_name
        industry_part = ""
        if request.industry_hint:
            industry_part = f" {request.industry_hint}"
        if request.sub_sector:
            industry_part += f" {request.sub_sector}"

        return [
            # 1. Public filings & company-reported KPIs (filing tier)
            f"{name} 10-K annual report key performance indicators metrics 2024 2025",
            # 2. Business segments / operating metrics (filing tier)
            f"{name} business segments operating metrics{industry_part}",
            # 3. Industry peer benchmarks (peer tier — source types only)
            f"{industry_part or name} industry benchmark KPI ranges analyst reports 2024 2025",
            # 4. Strategic priorities from investor communications (filing tier)
            f"{name} CEO investor day strategic priorities financial targets",
        ]

    async def _synthesize_company_profile(
        self,
        request: CompanyResearchRequest,
        search_results: List[Dict[str, Any]],
        queries: List[str],
    ) -> CompanyKPIProfile:
        """
        Synthesise 4 web-search payloads into a structured CompanyKPIProfile via Sonnet.

        Enforces M1 (benchmark_source on every benchmark) and M6 (source TYPES only,
        never specific competitor names or figures presented as fact).
        """
        biz_desc = request.business_description or ""
        sub = request.sub_sector or ""
        industry = request.industry_hint or "the relevant industry"

        # Compact context block — give the LLM each search's answer text
        context_blocks: List[str] = []
        for i, (q, r) in enumerate(zip(queries, search_results), start=1):
            answer = (r.get("answer") or "").strip()
            if not answer:
                continue
            # Trim to keep token budget reasonable
            context_blocks.append(f"SEARCH {i}: {q}\nFINDINGS:\n{answer[:1800]}")
        context_str = "\n\n".join(context_blocks) if context_blocks else "(no web findings)"

        biz_block = ""
        if biz_desc or sub:
            biz_block = f"\nADMIN-PROVIDED CONTEXT:\n"
            if biz_desc:
                biz_block += f"  Description: {biz_desc}\n"
            if sub:
                biz_block += f"  Sub-sector: {sub}\n"

        prompt = (
            f"You are an industry KPI analyst. Research target: {request.company_name}.\n"
            f"Industry hint: {industry}.\n"
            f"{biz_block}\n"
            f"WEB FINDINGS FROM 4 PARALLEL SEARCHES:\n{context_str}\n\n"
            f"TASK: Produce {request.max_kpis} benchmark-anchored KPI templates "
            f"organised across functional domains (Finance, Operations, Sales, "
            f"Supply Chain, etc.). Each KPI must include an industry-relevant "
            f"benchmark range when available.\n\n"
            f"RULES:\n"
            f"1. Every benchmark MUST carry a `benchmark_source` from this set: "
            f"'filing' (company-reported in their own annual report or investor "
            f"materials), 'peer' (range from an industry analyst report covering "
            f"the sector), or 'inferred' (your training knowledge only). When "
            f"unsure, use 'inferred'.\n"
            f"2. NEVER name specific competitor companies or quote specific figures "
            f"as fact. Cite source TYPES only (e.g. 'specialty chemicals analyst "
            f"reports, 2024'). This is a legal/citation guardrail.\n"
            f"3. Prefer concrete KPIs over generic ones (e.g. 'Order-to-Delivery "
            f"Lead Time' beats 'Operational Efficiency').\n"
            f"4. `confidence` reflects how relevant the KPI is to this specific "
            f"company given the findings — not how confident you are it exists.\n\n"
            f"Return ONLY valid JSON matching this exact schema:\n"
            f"{{\n"
            f'  "industry_inferred": "string",\n'
            f'  "is_public": true | false,\n'
            f'  "research_sources": ["Source TYPE 1", "Source TYPE 2", ...],\n'
            f'  "template_kpis": [\n'
            f'    {{\n'
            f'      "name": "Gross Margin",\n'
            f'      "definition": "Revenue minus COGS, as a % of revenue",\n'
            f'      "unit": "%",\n'
            f'      "benchmark_low": 12.0,\n'
            f'      "benchmark_high": 18.0,\n'
            f'      "benchmark_range": "12-18%",\n'
            f'      "benchmark_source": "filing",\n'
            f'      "confidence": 0.85,\n'
            f'      "domain": "Finance",\n'
            f'      "business_process_id": null\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
            f"No markdown, no preamble. Pure JSON."
        )

        parsed = await self._llm_json_call(
            prompt=prompt,
            principal_id=None,
            temperature=0.2,
        )

        if not parsed:
            logger.warning("%s: synthesis returned no parseable JSON — degrading to LLM-only", self.name)
            return await self._llm_only_company_profile(request)

        return self._profile_from_parsed(request, parsed, degraded=False)

    async def _llm_only_company_profile(
        self, request: CompanyResearchRequest
    ) -> CompanyKPIProfile:
        """
        M4 fallback — produce a CompanyKPIProfile from LLM knowledge alone.

        All benchmarks are forced to `benchmark_source='inferred'`. Marks
        `degraded=True` so the UI can surface the degradation notice.
        """
        biz_desc = request.business_description or ""
        sub = request.sub_sector or ""
        industry = request.industry_hint or "the relevant industry"

        biz_block = ""
        if biz_desc or sub:
            biz_block = "\nADMIN-PROVIDED CONTEXT:\n"
            if biz_desc:
                biz_block += f"  Description: {biz_desc}\n"
            if sub:
                biz_block += f"  Sub-sector: {sub}\n"

        prompt = (
            f"You are an industry KPI analyst. Research target: {request.company_name}.\n"
            f"Industry hint: {industry}.\n"
            f"{biz_block}\n"
            f"WEB SEARCH IS UNAVAILABLE — rely on your training knowledge only.\n\n"
            f"TASK: Produce {request.max_kpis} benchmark-anchored KPI templates "
            f"organised across functional domains. Every benchmark_source MUST be "
            f"'inferred' since you have no live source data.\n\n"
            f"RULES:\n"
            f"1. Every benchmark_source MUST be 'inferred'.\n"
            f"2. NEVER name specific competitor companies. Cite source TYPES only.\n"
            f"3. Prefer concrete KPIs over generic ones.\n"
            f"4. confidence should be lower (typically 0.3-0.6) to reflect the "
            f"degraded research mode.\n\n"
            f"Return ONLY valid JSON in this schema:\n"
            f"{{\n"
            f'  "industry_inferred": "string",\n'
            f'  "is_public": false,\n'
            f'  "research_sources": ["LLM training knowledge"],\n'
            f'  "template_kpis": [\n'
            f'    {{\n'
            f'      "name": "Gross Margin",\n'
            f'      "definition": "Revenue minus COGS, as a % of revenue",\n'
            f'      "unit": "%",\n'
            f'      "benchmark_low": 40.0,\n'
            f'      "benchmark_high": 60.0,\n'
            f'      "benchmark_range": "40-60%",\n'
            f'      "benchmark_source": "inferred",\n'
            f'      "confidence": 0.5,\n'
            f'      "domain": "Finance",\n'
            f'      "business_process_id": null\n'
            f'    }}\n'
            f'  ]\n'
            f"}}\n"
            f"No markdown, no preamble."
        )

        parsed = await self._llm_json_call(
            prompt=prompt,
            principal_id=None,
            temperature=0.3,
        )

        if not parsed:
            # Worst case: return an empty-but-valid profile so the UI degrades cleanly
            logger.error(
                "%s: LLM-only profile generation failed — returning empty profile",
                self.name,
            )
            return CompanyKPIProfile(
                company_name=request.company_name,
                industry_inferred=request.industry_hint,
                is_public=False,
                domains=[],
                template_kpis=[],
                research_sources=["LLM training knowledge"],
                degraded=True,
            )

        return self._profile_from_parsed(request, parsed, degraded=True)

    async def _llm_json_call(
        self,
        prompt: str,
        principal_id: Optional[str],
        temperature: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Shared helper: send a prompt to the LLM service, parse JSON response.

        Returns None on any failure (no LLM, non-success status, unparseable JSON).
        """
        if self._llm_service is None and self.orchestrator is None:
            logger.warning("%s: no LLM service available for JSON call", self.name)
            return None

        try:
            from src.agents.new.a9_llm_service_agent import A9_LLM_Request

            req = A9_LLM_Request(
                request_id=str(uuid.uuid4()),
                principal_id=principal_id or "system",
                prompt=prompt,
                system_prompt="Return only valid JSON. No markdown. No preamble.",
                model=_SYNTHESIS_MODEL,
                operation="generate",
                temperature=temperature,
                max_tokens=8192,
            )

            if self.orchestrator is not None:
                resp = await self.orchestrator.execute_agent_method(
                    "A9_LLM_Service_Agent", "generate", {"request": req}
                )
            else:
                resp = await self._llm_service.generate(req)

            if getattr(resp, "status", "error") != "success":
                logger.warning(
                    "%s: LLM call returned non-success: %s",
                    self.name,
                    getattr(resp, "status", "?"),
                )
                return None

            raw = (getattr(resp, "content", "") or "").strip()
            # Strip markdown fences if the model used them anyway
            if raw.startswith("```"):
                raw = raw[raw.index("\n") + 1:] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[: raw.rfind("```")].rstrip()

            return json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("%s: JSON parse failed: %s", self.name, exc)
            return None
        except Exception as exc:
            logger.error("%s: LLM JSON call failed: %s", self.name, exc)
            return None

    def _profile_from_parsed(
        self,
        request: CompanyResearchRequest,
        parsed: Dict[str, Any],
        degraded: bool,
    ) -> CompanyKPIProfile:
        """
        Convert a parsed LLM JSON dict into a typed CompanyKPIProfile.

        Tolerant of missing or malformed fields — drops invalid KPIs rather than
        raising. In degraded mode, forces every benchmark_source to 'inferred'.
        """
        raw_kpis = parsed.get("template_kpis", [])
        if not isinstance(raw_kpis, list):
            raw_kpis = []

        valid_sources = {"filing", "peer", "inferred"}
        template_kpis: List[TemplateKPI] = []

        for item in raw_kpis:
            if not isinstance(item, dict):
                continue
            try:
                # Normalize benchmark_source
                src = item.get("benchmark_source")
                if degraded:
                    src = "inferred"
                elif src not in valid_sources:
                    src = "inferred" if item.get("benchmark_range") else None

                # Derive a display range when only numeric bounds were returned
                low = item.get("benchmark_low")
                high = item.get("benchmark_high")
                rng = item.get("benchmark_range")
                if rng is None and low is not None and high is not None:
                    unit = (item.get("unit") or "").strip()
                    suffix = unit if unit in {"%", "pp"} else ""
                    rng = f"{low}-{high}{suffix}"

                template_kpis.append(
                    TemplateKPI(
                        name=str(item.get("name", "")).strip(),
                        definition=str(item.get("definition", "")).strip(),
                        unit=str(item.get("unit", "")).strip(),
                        benchmark_low=float(low) if low is not None else None,
                        benchmark_high=float(high) if high is not None else None,
                        benchmark_range=rng,
                        benchmark_source=src,  # type: ignore[arg-type]
                        confidence=float(item.get("confidence", 0.5)),
                        domain=str(item.get("domain", "")).strip() or "General",
                        business_process_id=item.get("business_process_id") or None,
                    )
                )
            except (ValueError, TypeError) as exc:
                logger.warning("%s: dropped malformed KPI item: %s (%s)", self.name, exc, item)
                continue

        domains = sorted({k.domain for k in template_kpis if k.domain})

        sources = parsed.get("research_sources", [])
        if not isinstance(sources, list):
            sources = []
        sources = [str(s) for s in sources if s]

        return CompanyKPIProfile(
            company_name=request.company_name,
            industry_inferred=str(parsed.get("industry_inferred") or request.industry_hint or "") or None,
            is_public=bool(parsed.get("is_public", False)),
            domains=domains,
            template_kpis=template_kpis,
            research_sources=sources or (["LLM training knowledge"] if degraded else []),
            degraded=degraded,
        )
