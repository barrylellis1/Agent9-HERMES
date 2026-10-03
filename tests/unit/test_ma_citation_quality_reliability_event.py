# arch-allow-direct-agent-construction
"""reliability.citation_quality -- MA's reliability signal, the one stage of
five with none at all until now (docs/architecture/audit_event_system_design.md,
2026-10-02 scope extension). Confirmed live the same day: driving a full
SA->DA->MA->SF run produced zero MA entries in audit_events, because nothing
emitted one -- not because MA ran clean.

Reuses test_a9_market_analysis_agent.py's fixtures (_make_request,
_agent_with_mocks) rather than re-deriving them. No live DB: AuditService.log
is patched, same convention as every other reliability-signal test.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.new.a9_market_analysis_agent import (
    A9_Market_Analysis_Agent,
    _citation_quality_outcome,
)
from src.agents.models.market_analysis_models import MarketAnalysisRequest, MarketSignal


def _make_request(**kwargs) -> MarketAnalysisRequest:
    defaults = dict(
        session_id="sess-001",
        request_id="deep-analysis-req-001",
        client_id="lubricants",
        kpi_name="Gross Margin",
        kpi_context="Gross Margin dropped 2.3pp in lubricants Q1 2026",
        industry="lubricants",
        max_signals=3,
    )
    defaults.update(kwargs)
    return MarketAnalysisRequest(**defaults)


def _agent_with_mocks(*, enable_perplexity: bool = False, perplexity_result: dict = None):
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": enable_perplexity})
    mock_llm = AsyncMock()
    mock_resp = type("R", (), {"status": "success", "analysis": {"text": "Synthesised."}})()
    mock_llm.analyze = AsyncMock(return_value=mock_resp)
    agent._llm_service = mock_llm
    if enable_perplexity and perplexity_result is not None:
        mock_perp = AsyncMock()
        mock_perp.search = AsyncMock(return_value=perplexity_result)
        agent._perplexity = mock_perp
    return agent


class TestCitationQualityOutcome:
    """The pure decision function -- no agent needed."""

    def test_error_is_fail(self):
        assert _citation_quality_outcome("Perplexity search error: timeout", []) == "fail"

    def test_at_least_one_url_is_pass(self):
        signals = [
            MarketSignal(source="perplexity", title="t", summary="s", relevance_score=0.7, url=None),
            MarketSignal(source="perplexity", title="t", summary="s", relevance_score=0.7, url="https://a.com"),
        ]
        assert _citation_quality_outcome(None, signals) == "pass"

    def test_no_error_no_urls_is_abstain(self):
        signals = [
            MarketSignal(source="llm_knowledge", title="t", summary="s", relevance_score=0.6, url=None),
        ]
        assert _citation_quality_outcome(None, signals) == "abstain"

    def test_no_signals_at_all_is_abstain_not_fail(self):
        assert _citation_quality_outcome(None, []) == "abstain"

    def test_error_wins_even_if_a_url_somehow_exists(self):
        """Shouldn't happen in practice (an errored search sets signals=[]),
        but the error is the more severe fact and must take precedence."""
        signals = [MarketSignal(source="perplexity", title="t", summary="s", relevance_score=0.7, url="https://a.com")]
        assert _citation_quality_outcome("search error", signals) == "fail"


@pytest.mark.asyncio
async def test_real_citations_emit_pass():
    agent = _agent_with_mocks(
        enable_perplexity=True,
        perplexity_result={"answer": "Context.", "citations": ["https://a.com", "https://b.com"]},
    )
    with patch("src.agents.new.a9_market_analysis_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        resp = await agent.analyze_market(_make_request())

    assert len(resp.signals) == 2
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["event_type"] == "reliability.citation_quality"
    assert kwargs["outcome"] == "pass"
    assert kwargs["client_id"] == "lubricants"
    assert kwargs["request_id"] == "deep-analysis-req-001"
    assert kwargs["resource_id"] == "Gross Margin"
    assert kwargs["payload"]["signals_with_url"] == 2


@pytest.mark.asyncio
async def test_missing_request_id_logs_none_not_a_crash():
    """request_id is Optional (only the DA->MA integration call site has it;
    e.g. company-profile's industry-research endpoint does not) -- must
    degrade to request_id=None, never AttributeError on a field that isn't
    there (MarketAnalysisRequest is a plain BaseModel, not A9AgentBaseRequest,
    so it has no request_id unless this model declares one itself)."""
    agent = _agent_with_mocks(
        enable_perplexity=True,
        perplexity_result={"answer": "Context.", "citations": ["https://a.com"]},
    )
    request = _make_request(request_id=None)
    with patch("src.agents.new.a9_market_analysis_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        resp = await agent.analyze_market(request)

    assert resp.synthesis
    spy.assert_awaited_once()
    assert spy.call_args.kwargs["request_id"] is None


@pytest.mark.asyncio
async def test_llm_only_fallback_emits_abstain_not_fail():
    """Perplexity disabled entirely -- the pure LLM-knowledge path. No real
    citation ever existed to check, so this is inconclusive, not a defect."""
    agent = _agent_with_mocks(enable_perplexity=False)
    with patch("src.agents.new.a9_market_analysis_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await agent.analyze_market(_make_request())

    spy.assert_awaited_once()
    assert spy.call_args.kwargs["outcome"] == "abstain"


@pytest.mark.asyncio
async def test_perplexity_error_emits_fail():
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": True})
    mock_perp = AsyncMock()
    mock_perp.search = AsyncMock(side_effect=RuntimeError("network error"))
    agent._perplexity = mock_perp
    agent._llm_service = None

    with patch("src.agents.new.a9_market_analysis_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        resp = await agent.analyze_market(_make_request())

    assert resp.error
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["outcome"] == "fail"
    assert kwargs["severity"] == "warning"


@pytest.mark.asyncio
async def test_no_client_id_skips_emission_entirely():
    """MarketAnalysisRequest.client_id is Optional -- not every caller has one
    yet (company-profile's industry-research endpoint). Must skip, not guess,
    matching every other reliability signal's own missing-client_id posture."""
    agent = _agent_with_mocks(
        enable_perplexity=True,
        perplexity_result={"answer": "Context.", "citations": ["https://a.com"]},
    )
    request = _make_request(client_id=None)
    with patch("src.agents.new.a9_market_analysis_agent.AuditService.log", new=AsyncMock()) as spy:
        await agent.analyze_market(request)

    spy.assert_not_called()


@pytest.mark.asyncio
async def test_audit_failure_never_breaks_the_analysis():
    agent = _agent_with_mocks(
        enable_perplexity=True,
        perplexity_result={"answer": "Context.", "citations": ["https://a.com"]},
    )
    with patch("src.agents.new.a9_market_analysis_agent.AuditService.log", new=AsyncMock(return_value=False)):
        resp = await agent.analyze_market(_make_request())

    assert resp.synthesis
    assert len(resp.signals) == 1
