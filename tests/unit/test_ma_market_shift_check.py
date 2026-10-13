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
    UNANSWERED_MARKET_SHIFT_SUMMARY,
    UNSOURCED_MARKET_SHIFT_SUMMARY,
    _parse_synthesis_reply,
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

    def test_without_a_source_the_answer_is_insufficient_whatever_the_model_said(self):
        for said in ("supported", "not_supported"):
            out: dict = {}
            _record_market_shift(out, _request(general_deviation=GENERAL),
                                 {"market_shift": {"assessment": said, "confidence": 0.9, "summary": "Recalled."}},
                                 [_signal()])
            shift = out["market_shift"]
            assert shift["assessment"] == "insufficient" and shift["grounded"] is False
            assert shift["confidence"] is None and shift["summary"] == UNSOURCED_MARKET_SHIFT_SUMMARY
            assert shift["unsourced_assessment"] == said and shift["unsourced_summary"] == "Recalled."

    def test_with_a_source_the_answer_stands_and_nothing_unsourced_is_kept(self):
        out: dict = {}
        _record_market_shift(out, _request(general_deviation=GENERAL),
                             {"market_shift": {"assessment": "not_supported", "confidence": 0.6, "summary": "Steady."}},
                             [_signal(url="https://example.com/r")])
        assert out["market_shift"]["assessment"] == "not_supported"
        assert "unsourced_assessment" not in out["market_shift"]

    def test_an_answer_outside_the_three_values_is_not_a_confirmation(self):
        out: dict = {}
        _record_market_shift(out, _request(general_deviation=GENERAL),
                             {"market_shift": {"assessment": "probably", "confidence": "high"}},
                             [_signal(url="https://example.com/r")])
        assert out["market_shift"]["assessment"] == "insufficient"
        assert out["market_shift"]["confidence"] is None

    def test_confidence_is_held_between_zero_and_one(self):
        out: dict = {}
        _record_market_shift(out, _request(general_deviation=GENERAL),
                             {"market_shift": {"assessment": "not_supported", "confidence": 7}},
                             [_signal(url="https://example.com/r")])
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


class TestReadingTheReply:
    """Found live 2026-10-13: two JSON objects in one reply lost the answer and put a
    Python dict repr on screen as the market briefing."""

    TWO = (
        '{\n  "synthesis": "First attempt."\n}\n'
        'Note: JSON schema requires specific top-level fields; see below for compliant object.\n\n'
        '{\n  "synthesis": "Second attempt.",\n  "conflict": null,\n'
        '  "market_shift": {"assessment": "not_supported", "confidence": 0.55, "summary": "Segment-specific pressures."}\n}'
    )

    def test_the_last_object_with_a_synthesis_is_used(self):
        parsed = _parse_synthesis_reply(self.TWO)
        assert parsed["synthesis"] == "Second attempt."
        assert parsed["market_shift"]["assessment"] == "not_supported"

    def test_a_fenced_or_prefaced_object_is_still_read(self):
        parsed = _parse_synthesis_reply('Here you go:\n```json\n{"synthesis": "Text {with braces}."}\n```')
        assert parsed["synthesis"] == "Text {with braces}."

    def test_no_object_is_none(self):
        assert _parse_synthesis_reply("plain words") is None and _parse_synthesis_reply("") is None
        assert _parse_synthesis_reply('{"other": 1}') is None

    @pytest.mark.asyncio
    async def test_an_unparsed_reply_from_the_llm_service_is_recovered(self):
        agent, _ = _agent({"raw_response": self.TWO, "_parse_error": {"error": "json_decode_failed"}})
        out: dict = {}
        text, conflict = await agent._synthesize(_request(general_deviation=GENERAL), [_signal()], "raw", extras_out=out)
        assert text == "Second attempt." and conflict is None
        assert out["market_shift"]["unsourced_assessment"] == "not_supported"
        assert out["market_shift"]["assessment"] == "insufficient" and out["market_shift"]["grounded"] is False

    @pytest.mark.asyncio
    async def test_an_unreadable_reply_never_reaches_the_reader_as_a_payload(self):
        agent, _ = _agent({"raw_response": '{"synthesis": "cut off', "_parse_error": {"error": "x"}})
        text, _c = await agent._synthesize(_request(), [_signal()], "raw")
        assert "raw_response" not in text and "_parse_error" not in text
        assert text.startswith("Market analysis for Net Revenue")

    @pytest.mark.asyncio
    async def test_plain_prose_is_still_used_as_is(self):
        agent, _ = _agent({"text": "Synthesised."})
        text, _c = await agent._synthesize(_request(), [_signal()], "raw")
        assert text == "Synthesised."


class TestAskedButNotAnswered:
    @pytest.mark.asyncio
    async def test_a_reply_without_the_answer_is_recorded_as_unanswered(self):
        agent, _ = _agent({"synthesis": "Market text.", "conflict": None})
        resp = await agent.analyze_market(_request(general_deviation=GENERAL))
        assert resp.market_shift["assessment"] == "insufficient" and resp.market_shift["unanswered"] is True
        assert resp.market_shift["summary"] == UNANSWERED_MARKET_SHIFT_SUMMARY

    @pytest.mark.asyncio
    async def test_when_the_question_was_not_asked_there_is_still_nothing(self):
        agent, _ = _agent({"synthesis": "Market text.", "conflict": None})
        resp = await agent.analyze_market(_request())
        assert resp.market_shift is None
