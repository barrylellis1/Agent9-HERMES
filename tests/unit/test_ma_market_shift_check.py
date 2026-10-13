# arch-allow-direct-agent-construction
"""The confirming question for a gap that is everywhere.

When Deep Analysis finds no IS NOT (src/analysis/deviation_scope.py), the cause is
common to the whole business. One candidate is a shift in the market, and Market
Analysis is asked whether its signals support that. The question is asked at
synthesis only: the internal finding never shapes which signals are fetched.
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.agents.models.market_analysis_models import (
    MarketAnalysisRequest,
    MarketAnalysisResponse,
    MarketSignal,
)
from src.agents.new.a9_market_analysis_agent import (
    A9_Market_Analysis_Agent,
    _record_market_shift,
)

GENERAL = (
    "The gap is across the board: all 60 segments checked, in 10 dimensions, are about "
    "16.3% below plan. No segment stands out."
)


def _request(**kwargs) -> MarketAnalysisRequest:
    defaults = dict(
        session_id="sess-001",
        request_id="da-req-001",
        client_id="lubricants",
        kpi_name="Net Revenue",
        kpi_context="Net Revenue is 16.3% below plan",
        industry="lubricants",
        max_signals=3,
    )
    defaults.update(kwargs)
    return MarketAnalysisRequest(**defaults)


def _signal(url=None) -> MarketSignal:
    return MarketSignal(source="perplexity", title="t", summary="s", relevance_score=0.7, url=url)


def _agent(analysis: dict):
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": False})
    llm = AsyncMock()
    llm.analyze = AsyncMock(return_value=type("R", (), {"status": "success", "analysis": analysis})())
    agent._llm_service = llm
    return agent, llm


def _prompt(llm) -> str:
    call = llm.analyze.call_args
    req = call.args[0] if call.args else next(iter(call.kwargs.values()))
    return str(getattr(req, "content", None) or getattr(req, "prompt", None) or req)


class TestRecordMarketShift:
    def test_the_answer_is_kept_with_whether_it_rests_on_a_source(self):
        out: dict = {}
        _record_market_shift(
            out, _request(general_deviation=GENERAL),
            {"market_shift": {"assessment": "Supported", "confidence": 0.7, "summary": " Demand fell 12%. "}},
            [_signal(url="https://example.com/report")],
        )
        assert out["market_shift"] == {
            "assessment": "supported", "confidence": 0.7, "summary": "Demand fell 12%.", "grounded": True,
        }

    def test_without_a_source_url_the_answer_is_marked_ungrounded(self):
        out: dict = {}
        _record_market_shift(out, _request(general_deviation=GENERAL),
                             {"market_shift": {"assessment": "supported", "confidence": 0.9}}, [_signal()])
        assert out["market_shift"]["grounded"] is False and out["market_shift"]["summary"] is None

    def test_an_answer_outside_the_three_values_is_not_a_confirmation(self):
        out: dict = {}
        _record_market_shift(out, _request(general_deviation=GENERAL),
                             {"market_shift": {"assessment": "probably", "confidence": "high"}}, [])
        assert out["market_shift"]["assessment"] == "insufficient"
        assert out["market_shift"]["confidence"] is None

    def test_confidence_is_held_between_zero_and_one(self):
        out: dict = {}
        _record_market_shift(out, _request(general_deviation=GENERAL),
                             {"market_shift": {"assessment": "not_supported", "confidence": 7}}, [])
        assert out["market_shift"]["confidence"] == 1.0

    def test_nothing_is_recorded_when_the_question_was_not_asked(self):
        out: dict = {}
        _record_market_shift(out, _request(), {"market_shift": {"assessment": "supported"}}, [])
        assert out == {}

    def test_no_answer_records_nothing(self):
        out: dict = {}
        _record_market_shift(out, _request(general_deviation=GENERAL), {"synthesis": "x"}, [])
        assert out == {}


class TestSynthesisAsksTheQuestion:
    @pytest.mark.asyncio
    async def test_the_question_and_its_answer_shape_are_in_the_prompt(self):
        agent, llm = _agent({"synthesis": "Market text.", "conflict": None,
                             "market_shift": {"assessment": "insufficient", "confidence": 0.3,
                                              "summary": "The signals do not say."}})
        out: dict = {}
        text, _ = await agent._synthesize(_request(general_deviation=GENERAL), [_signal()], "raw", extras_out=out)
        prompt = _prompt(llm)
        assert "MARKET-SHIFT CHECK" in prompt and "all 60 segments checked" in prompt
        assert '"market_shift"' in prompt and "insufficient" in prompt
        assert "Do NOT infer a market shift from the internal gap itself" in prompt
        assert text == "Market text." and out["market_shift"]["assessment"] == "insufficient"

    @pytest.mark.asyncio
    async def test_a_localised_gap_asks_nothing(self):
        agent, llm = _agent({"synthesis": "Market text.", "conflict": None})
        out: dict = {}
        await agent._synthesize(_request(), [_signal()], "raw", extras_out=out)
        assert "MARKET-SHIFT CHECK" not in _prompt(llm) and "market_shift" not in _prompt(llm)
        assert out == {}


def test_the_response_carries_the_answer_and_the_request_the_finding():
    assert "market_shift" in MarketAnalysisResponse.model_fields
    assert "general_deviation" in MarketAnalysisRequest.model_fields
