# arch-allow-direct-agent-construction
"""Market research reuses answers for 24 hours and Deep Analysis asks for one paragraph (2026-10-30).

A repeat analysis of the same card asked the same two model questions again (~20-35 s). Answers
are kept for 24 hours, keyed by the exact prompt and the client. The DA summary is one paragraph:
the screen shows one small paragraph, and the 2-3 paragraph briefing was most of the time.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from src.agents.new import a9_market_analysis_agent as ma_mod
from src.agents.new.a9_market_analysis_agent import A9_Market_Analysis_Agent
from src.agents.models.market_analysis_models import MarketAnalysisRequest


def _request(**kwargs) -> MarketAnalysisRequest:
    defaults = dict(
        session_id="s", request_id="r", client_id="lubricants", kpi_name="Gross Margin %",
        kpi_context="Gross margin fell 4.5 points year on year", industry="Lubricants",
        max_signals=3, analysis_mode="problem",
    )
    defaults.update(kwargs)
    return MarketAnalysisRequest(**defaults)


def _agent():
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": False})
    llm = AsyncMock()
    signals = {"signals": [{"title": "Base oil up", "summary": "Group II prices rose.", "relevance_score": 0.8}]}
    llm.generate = AsyncMock(return_value=type("G", (), {"status": "success", "content": json.dumps(signals)})())
    synthesis = {"synthesis": "Input costs rose.", "conflict": {"detected": False, "type": None, "confidence": 0.7, "summary": None}}
    llm.analyze = AsyncMock(return_value=type("A", (), {"status": "success", "analysis": synthesis})())
    agent._llm_service = llm
    return agent, llm


@pytest.mark.asyncio
async def test_a_repeat_analysis_reuses_both_answers():
    agent, llm = _agent()
    first = await agent.analyze_market(_request())
    second = await agent.analyze_market(_request(session_id="s2", request_id="r2"))
    assert llm.generate.await_count == 1 and llm.analyze.await_count == 1
    assert second.synthesis == first.synthesis == "Input costs rose."
    assert [s.title for s in second.signals] == [s.title for s in first.signals]
    assert second.conflict == first.conflict


@pytest.mark.asyncio
async def test_another_client_never_gets_a_reused_answer():
    agent, llm = _agent()
    await agent.analyze_market(_request(client_id="lubricants"))
    await agent.analyze_market(_request(client_id="apex_lubricants"))
    assert llm.generate.await_count == 2 and llm.analyze.await_count == 2


@pytest.mark.asyncio
async def test_a_different_analysis_asks_the_summary_again_but_reuses_the_signals():
    agent, llm = _agent()
    await agent.analyze_market(_request(kpi_context="Gross margin fell 4.5 points"))
    await agent.analyze_market(_request(kpi_context="Gross margin fell 6.0 points"))
    assert llm.generate.await_count == 1  # the signals never see the analysis
    assert llm.analyze.await_count == 2


@pytest.mark.asyncio
async def test_answers_older_than_24_hours_are_asked_again(monkeypatch):
    agent, llm = _agent()
    await agent.analyze_market(_request())
    monkeypatch.setattr(ma_mod, "_REUSE_SECONDS", -1)
    await agent.analyze_market(_request())
    assert llm.generate.await_count == 2 and llm.analyze.await_count == 2


@pytest.mark.asyncio
async def test_a_failed_answer_is_not_kept():
    agent, llm = _agent()
    llm.analyze = AsyncMock(return_value=type("A", (), {"status": "error", "analysis": {}})())
    await agent.analyze_market(_request())
    await agent.analyze_market(_request())
    assert llm.analyze.await_count == 2  # the fallback text is never reused


@pytest.mark.asyncio
async def test_a_reused_answer_is_a_copy():
    agent, _ = _agent()
    first = await agent.analyze_market(_request())
    first.signals[0].title = "changed by a caller"
    second = await agent.analyze_market(_request())
    assert second.signals[0].title == "Base oil up"


@pytest.mark.asyncio
async def test_deep_analysis_asks_for_one_paragraph_and_others_keep_the_briefing():
    agent, llm = _agent()
    await agent.analyze_market(_request(synthesis_length="paragraph"))
    await agent.analyze_market(_request(client_id="other"))  # default: briefing
    paragraph_prompt = llm.analyze.await_args_list[0].args[0].content
    briefing_prompt = llm.analyze.await_args_list[1].args[0].content
    assert "about 100 words" in paragraph_prompt and "2-3 paragraph" not in paragraph_prompt
    assert "2-3 paragraph" in briefing_prompt


def test_the_deep_analysis_route_asks_for_one_paragraph():
    import inspect
    from src.api.routes import workflows

    assert 'synthesis_length="paragraph"' in inspect.getsource(workflows)


@pytest.mark.asyncio
async def test_an_empty_web_search_is_not_kept():
    agent, _ = _agent()
    agent.config.enable_perplexity = True
    search = AsyncMock(return_value={"answer": "", "citations": []})  # e.g. no key set
    agent._perplexity = type("P", (), {"search": search})()
    await agent.analyze_market(_request())
    await agent.analyze_market(_request())
    assert search.await_count == 2


@pytest.mark.asyncio
async def test_a_web_search_that_found_something_is_kept():
    agent, _ = _agent()
    agent.config.enable_perplexity = True
    search = AsyncMock(return_value={"answer": "Base oil rose.", "citations": [{"url": "https://x.test", "title": "t"}]})
    agent._perplexity = type("P", (), {"search": search})()
    await agent.analyze_market(_request())
    await agent.analyze_market(_request())
    assert search.await_count == 1
