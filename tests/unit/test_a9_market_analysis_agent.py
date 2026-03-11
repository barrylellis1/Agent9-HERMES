# arch-allow-direct-agent-construction
"""
Unit tests for A9_Market_Analysis_Agent.

Covers the key behavioral contracts — no real LLM or Perplexity calls are made.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.new.a9_market_analysis_agent import A9_Market_Analysis_Agent
from src.agents.models.market_analysis_models import MarketAnalysisRequest, MarketAnalysisResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(**kwargs) -> MarketAnalysisRequest:
    defaults = dict(
        session_id="sess-001",
        kpi_name="Gross Margin",
        kpi_context="Gross Margin dropped 2.3pp in lubricants Q1 2026",
        industry="lubricants",
        max_signals=3,
    )
    defaults.update(kwargs)
    return MarketAnalysisRequest(**defaults)


def _agent_with_mocks(
    *,
    enable_perplexity: bool = False,
    llm_synthesis: str = "Synthesised market briefing.",
    perplexity_result: dict = None,
) -> A9_Market_Analysis_Agent:
    """Build an agent with external dependencies mocked out."""
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": enable_perplexity})

    # Mock LLM service
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status = "success"
    mock_resp.analysis = {"text": llm_synthesis}
    mock_llm.analyze = AsyncMock(return_value=mock_resp)
    agent._llm_service = mock_llm

    # Mock Perplexity service when enabled
    if enable_perplexity and perplexity_result is not None:
        mock_perp = AsyncMock()
        mock_perp.search = AsyncMock(return_value=perplexity_result)
        agent._perplexity = mock_perp

    return agent


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_returns_valid_response():
    """Happy path: always returns a typed MarketAnalysisResponse."""
    agent = _agent_with_mocks()
    resp = await agent.analyze_market(_make_request())

    assert isinstance(resp, MarketAnalysisResponse)
    assert resp.session_id == "sess-001"
    assert resp.kpi_name == "Gross Margin"
    assert resp.synthesis  # non-empty


@pytest.mark.asyncio
async def test_llm_only_mode_has_no_signals():
    """When Perplexity is disabled, no signals and no perplexity source are returned."""
    agent = _agent_with_mocks(enable_perplexity=False)
    resp = await agent.analyze_market(_make_request())

    assert resp.signals == []
    assert "perplexity" not in resp.sources_queried


@pytest.mark.asyncio
async def test_perplexity_signals_populate_response():
    """URL citations from Perplexity are converted to MarketSignal objects."""
    citations = ["https://a.com", "https://b.com"]
    agent = _agent_with_mocks(
        enable_perplexity=True,
        perplexity_result={"answer": "Context.", "citations": citations},
    )
    resp = await agent.analyze_market(_make_request())

    assert len(resp.signals) == 2
    assert "perplexity" in resp.sources_queried


@pytest.mark.asyncio
async def test_max_signals_respected():
    """Agent never returns more signals than requested."""
    citations = [f"https://example.com/{i}" for i in range(10)]
    agent = _agent_with_mocks(
        enable_perplexity=True,
        perplexity_result={"answer": "ctx", "citations": citations},
    )
    resp = await agent.analyze_market(_make_request(max_signals=2))

    assert len(resp.signals) <= 2


@pytest.mark.asyncio
async def test_perplexity_error_does_not_raise():
    """If Perplexity fails, the agent falls back silently and still returns a response."""
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": True})
    mock_perp = AsyncMock()
    mock_perp.search = AsyncMock(side_effect=RuntimeError("network error"))
    agent._perplexity = mock_perp
    agent._llm_service = None  # plain-text fallback

    resp = await agent.analyze_market(_make_request())

    assert isinstance(resp, MarketAnalysisResponse)
    assert resp.signals == []
    assert resp.error  # error recorded


@pytest.mark.asyncio
async def test_no_llm_service_uses_plaintext_fallback():
    """Without an LLM service, the agent returns a plain-text synthesis instead of raising."""
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": False})
    agent._llm_service = None

    resp = await agent.analyze_market(_make_request())

    assert isinstance(resp, MarketAnalysisResponse)
    assert "Gross Margin" in resp.synthesis
