# arch-allow-direct-agent-construction
"""A call site can ask the model to think less, for that call only (2026-10-31).

Effort was a single process-wide switch (A9_LLM_EFFORT). Market research's two calls spent
most of their output on thinking, so they now ask for low effort through
A9_LLM_Request.reasoning_effort, which reaches Anthropic's output_config.effort.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from src.llm_services.claude_service import build_messages_kwargs

_MESSAGES = [{"role": "user", "content": "hello"}]


def _kwargs(model="claude-sonnet-5", effort=None):
    return build_messages_kwargs(
        model=model, max_tokens=1024, temperature=None, system="s", messages=_MESSAGES, effort=effort,
    )


def test_a_call_can_ask_for_low_effort(monkeypatch):
    monkeypatch.delenv("A9_LLM_EFFORT", raising=False)
    assert _kwargs(effort="low")["extra_body"]["output_config"] == {"effort": "low"}


def test_the_call_wins_over_the_process_setting(monkeypatch):
    monkeypatch.setenv("A9_LLM_EFFORT", "high")
    assert _kwargs(effort="low")["extra_body"]["output_config"] == {"effort": "low"}
    assert _kwargs()["extra_body"]["output_config"] == {"effort": "high"}


def test_no_effort_means_the_provider_default(monkeypatch):
    monkeypatch.delenv("A9_LLM_EFFORT", raising=False)
    assert "extra_body" not in _kwargs()


def test_an_unknown_effort_is_ignored_not_sent(monkeypatch):
    monkeypatch.delenv("A9_LLM_EFFORT", raising=False)
    assert "extra_body" not in _kwargs(effort="xhigh")  # OpenAI-only level


def test_a_model_without_effort_never_gets_it(monkeypatch):
    monkeypatch.delenv("A9_LLM_EFFORT", raising=False)
    assert "extra_body" not in _kwargs(model="claude-haiku-4-5-20251001", effort="low")


async def _llm_agent(monkeypatch):
    from src.agents.new.a9_llm_service_agent import A9_LLM_Service_Agent

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    return await A9_LLM_Service_Agent.create({"provider": "anthropic"})


def _reply():
    return {"request_id": "x", "model": "claude-sonnet-5", "response": json.dumps({"a": 1}),
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}


@pytest.mark.asyncio
async def test_analyze_sends_the_effort_to_the_claude_service(monkeypatch):
    from src.agents.new.a9_llm_service_agent import A9_LLM_AnalysisRequest

    agent = await _llm_agent(monkeypatch)
    agent.llm_service.generate = AsyncMock(return_value=_reply())
    req = A9_LLM_AnalysisRequest(  # arch-allow-agent-ctor — request model, not an agent
        request_id="r", principal_id="p", content="x", analysis_type="custom", reasoning_effort="low",
    )
    resp = await agent.analyze(req)
    assert resp.status == "success"
    assert agent.llm_service.generate.await_args.kwargs["effort"] == "low"


@pytest.mark.asyncio
async def test_no_effort_sends_no_effort_argument(monkeypatch):
    from src.agents.new.a9_llm_service_agent import A9_LLM_Request

    agent = await _llm_agent(monkeypatch)
    agent.llm_service.generate = AsyncMock(return_value=_reply())
    await agent.generate(A9_LLM_Request(  # arch-allow-agent-ctor — request model, not an agent
        request_id="r", principal_id="p", prompt="x"))
    assert "effort" not in agent.llm_service.generate.await_args.kwargs


@pytest.mark.asyncio
async def test_market_signals_and_summary_ask_for_low_effort():
    from src.agents.new.a9_market_analysis_agent import A9_Market_Analysis_Agent
    from src.agents.models.market_analysis_models import MarketAnalysisRequest

    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": False})
    llm = AsyncMock()
    signals = {"signals": [{"title": "Base oil up", "summary": "Prices rose.", "relevance_score": 0.8}]}
    llm.generate = AsyncMock(return_value=type("G", (), {"status": "success", "content": json.dumps(signals)})())
    llm.analyze = AsyncMock(return_value=type("A", (), {"status": "success", "analysis": {
        "synthesis": "Costs rose.", "conflict": {"detected": False, "type": None, "confidence": 0.7, "summary": None}}})())
    agent._llm_service = llm
    await agent.analyze_market(MarketAnalysisRequest(
        session_id="s", client_id="lubricants", kpi_name="Gross Margin %", kpi_context="fell 4.5 points",
        max_signals=3, analysis_mode="problem",
    ))
    assert llm.generate.await_args.args[0].reasoning_effort == "low"
    assert llm.analyze.await_args.args[0].reasoning_effort == "low"
