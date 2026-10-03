"""_flush_sf_decision_quality() -- the four non-advisory Decision Quality
links (information, alternatives, reasoning, commitment) persisted to
audit_events, per user's explicit "option 2" choice (2026-10-03): L1 (frame)
and L4 (tradeoffs) stay OUT of the log entirely, because `decision_quality.py`
marks both `advisory=True` after `persona_council_experiments.md` Sec 5
measured a 71% false-positive rate scoring a semantic property from a term
screen -- turning that screen into a logged pass/fail verdict would be
exactly what the module's own docstring warns against.

These tests cover the flush function directly, reusing `score_run()`'s real
scoring logic (no live DB: AuditService.log is patched, same convention as
every other reliability-signal test this session).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.new.a9_solution_finder_agent import _flush_sf_decision_quality

_OPTIONS = [
    {"id": "a", "title": "Accelerate renewal cadence", "description": "renewal timing lever"},
    {"id": "b", "title": "Reprice base oil contracts", "description": "pricing lever"},
]

_BASE_SOLUTIONS = {
    "options_ranked": _OPTIONS,
    "audit_log": [],
    "constraint_exposure": {},
    "tradeoff_matrix": {},
    "moderator_grades": {},
    "decision_ask": {},
    "immediate_actions": [],
    "next_steps": [],
}


@pytest.mark.asyncio
async def test_noop_when_client_id_missing():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
        await _flush_sf_decision_quality(None, "req-1", _BASE_SOLUTIONS, None)
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_emits_exactly_four_events_never_frame_or_tradeoffs():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", _BASE_SOLUTIONS, None)

    assert spy.await_count == 4
    resource_ids = {c.kwargs["resource_id"] for c in spy.call_args_list}
    assert resource_ids == {"information", "alternatives", "reasoning", "commitment"}
    assert "frame" not in resource_ids
    assert "tradeoffs" not in resource_ids


@pytest.mark.asyncio
async def test_event_type_and_fields():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", _BASE_SOLUTIONS, None)

    for c in spy.call_args_list:
        kwargs = c.kwargs
        assert kwargs["event_type"] == "reliability.decision_quality"
        assert kwargs["client_id"] == "lubricants"
        assert kwargs["request_id"] == "req-1"
        assert kwargs["source_agent"] == "A9_Solution_Finder_Agent"
        assert kwargs["resource_type"] == "dq_link"
        assert kwargs["outcome"] in ("pass", "fail", "abstain")
        assert "detail" in kwargs["payload"]
        assert "evidence" in kwargs["payload"]


@pytest.mark.asyncio
async def test_two_distinct_lever_families_is_alternatives_pass():
    solutions = dict(_BASE_SOLUTIONS, options_ranked=[
        {"id": "a", "title": "Reprice base oil contracts", "description": "pricing lever"},
        {"id": "b", "title": "Governance council for margin controls", "description": "oversight lever"},
    ])
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", solutions, None)

    alt = next(c.kwargs for c in spy.call_args_list if c.kwargs["resource_id"] == "alternatives")
    assert alt["outcome"] == "pass"
    assert alt["severity"] == "info"


@pytest.mark.asyncio
async def test_single_lever_family_is_alternatives_fail_with_warning_severity():
    solutions = dict(_BASE_SOLUTIONS, options_ranked=[
        {"id": "a", "title": "Reprice base oil contracts A", "description": "pricing lever"},
        {"id": "b", "title": "Reprice synthetic blend contracts B", "description": "pricing lever"},
    ])
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", solutions, None)

    alt = next(c.kwargs for c in spy.call_args_list if c.kwargs["resource_id"] == "alternatives")
    assert alt["outcome"] == "fail"
    assert alt["severity"] == "warning"


@pytest.mark.asyncio
async def test_no_options_is_alternatives_abstain_not_fail():
    solutions = dict(_BASE_SOLUTIONS, options_ranked=[])
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", solutions, None)

    alt = next(c.kwargs for c in spy.call_args_list if c.kwargs["resource_id"] == "alternatives")
    assert alt["outcome"] == "abstain"


@pytest.mark.asyncio
async def test_no_decision_ask_no_owner_is_commitment_fail():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", _BASE_SOLUTIONS, None)

    commitment = next(c.kwargs for c in spy.call_args_list if c.kwargs["resource_id"] == "commitment")
    assert commitment["outcome"] == "fail"


@pytest.mark.asyncio
async def test_full_decision_ask_is_commitment_pass():
    solutions = dict(
        _BASE_SOLUTIONS,
        decision_ask={"decision_text": "Approve base-oil reprice", "decision_owner": "CFO"},
        immediate_actions=[{"action": "notify procurement"}],
    )
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", solutions, None)

    commitment = next(c.kwargs for c in spy.call_args_list if c.kwargs["resource_id"] == "commitment")
    assert commitment["outcome"] == "pass"


@pytest.mark.asyncio
async def test_no_da_result_degrades_reasoning_to_abstain_not_fail():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", _BASE_SOLUTIONS, None)

    reasoning = next(c.kwargs for c in spy.call_args_list if c.kwargs["resource_id"] == "reasoning")
    assert reasoning["outcome"] == "abstain"


@pytest.mark.asyncio
async def test_scoring_exception_is_swallowed_not_raised():
    """score_run() is defensive by convention elsewhere in this session, but
    a malformed `solutions` payload must never break the SF response path
    this flush sits in -- same posture as AuditService.log's own contract."""
    with patch(
        "src.analysis.decision_quality.score_run", side_effect=RuntimeError("boom")
    ), patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", _BASE_SOLUTIONS, None)
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_a_failed_write_does_not_raise_or_block_the_others():
    with patch(
        "src.agents.new.a9_solution_finder_agent.AuditService.log",
        new=AsyncMock(side_effect=[RuntimeError("db down"), True, True, True]),
    ) as spy:
        await _flush_sf_decision_quality("lubricants", "req-1", _BASE_SOLUTIONS, None)
    assert spy.await_count == 4
