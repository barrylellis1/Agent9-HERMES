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

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents.agent_config_models import A9_Market_Analysis_Agent_Config
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
        # Step 2 — LLM synthesis
        # ------------------------------------------------------------------
        synthesis = await self._synthesize(request, signals, raw_answer)

        # ------------------------------------------------------------------
        # Step 3 — Confidence score heuristic
        # ------------------------------------------------------------------
        confidence = self._compute_confidence(signals, synthesis)

        return MarketAnalysisResponse(
            session_id=request.session_id,
            kpi_name=request.kpi_name,
            signals=signals,
            synthesis=synthesis,
            competitor_context=None,  # Reserved for future enrichment
            confidence=confidence,
            sources_queried=sources_queried,
            error=error_msg,
            timestamp=datetime.utcnow().isoformat(),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_search_query(self, request: MarketAnalysisRequest) -> str:
        """Compose a targeted search query from the request fields."""
        industry_part = f" {request.industry} industry" if request.industry else ""
        return (
            f"market trends{industry_part} {request.kpi_name} 2025 2026 competitors "
            f"external factors: {request.kpi_context}"
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

        industry_label = request.industry or "the relevant industry"
        prompt = (
            f"You are a market intelligence analyst with deep knowledge of {industry_label}.\n\n"
            f"A business is investigating why '{request.kpi_name}' has changed significantly.\n"
            f"Business context: {request.kpi_context}\n\n"
            f"Generate {request.max_signals} distinct external market signals that could explain "
            f"or provide context for this KPI movement. Draw on your knowledge of recent market "
            f"trends, commodity prices, competitive dynamics, and macroeconomic factors relevant "
            f"to {industry_label}.\n\n"
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
    ) -> str:
        """
        Build the synthesis narrative via A9_LLM_Service_Agent.

        Falls back to a formatted plain-text summary when the LLM service is
        unavailable, so the caller always receives a usable string.
        """
        industry_label = request.industry or "the relevant"
        formatted_signals = self._format_signals_for_prompt(signals, raw_answer)

        prompt = (
            f"You are a market intelligence analyst. Given these external market signals about "
            f"{request.kpi_name} in the {industry_label} industry, synthesise a 2-3 paragraph "
            f"executive briefing on what these signals mean for business performance.\n\n"
            f"KPI Context: {request.kpi_context}\n\n"
            f"Market Signals:\n{formatted_signals}\n\n"
            f"Provide:\n"
            f"1. Key external factors driving this KPI movement\n"
            f"2. Competitive context and industry benchmarks\n"
            f"3. Implications for the business\n\n"
            f"Be specific and quantitative where possible. Do not be vague."
        )

        if self._llm_service is None and self.orchestrator is None:
            logger.warning(
                "%s: LLM service unavailable — returning plain-text synthesis fallback", self.name
            )
            return self._plain_text_fallback(request, signals, raw_answer)

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
                # The LLM service returns analysis as a dict; the raw text lives under various keys.
                if isinstance(analysis, dict):
                    text = (
                        analysis.get("text")
                        or analysis.get("synthesis")
                        or analysis.get("content")
                        or analysis.get("response")
                        or ""
                    )
                    if text:
                        return str(text)
                    # Flatten the entire dict to a string when no known key is present
                    return str(analysis)
                return str(analysis)

            logger.warning(
                "%s: LLM synthesis returned non-success status: %s",
                self.name,
                getattr(llm_resp, "status", "unknown"),
            )
            return self._plain_text_fallback(request, signals, raw_answer)

        except Exception as exc:
            logger.error("%s: LLM synthesis error: %s", self.name, exc)
            return self._plain_text_fallback(request, signals, raw_answer)

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
