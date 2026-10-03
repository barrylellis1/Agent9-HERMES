"""_flush_sf_audit_log() -- SF's own narrative audit_log, finally persisted
(docs/architecture/audit_event_system_design.md's original pilot scope,
built 2026-10-02 after driving a full SA->DA->MA->SF run showed only one of
six reliability signals reaching the log at all -- the other half of that
gap was SF's own events, never wired to the sink despite the design note's
original motivating example being exactly this: "a real run on 2026-08-22
emitted six genuinely useful operational events and threw all of them away."

Flushed once from the accumulated list at each response-construction site,
not from each of the ~13 append call sites scattered through
a9_solution_finder_agent.py -- these tests cover the flush function directly
(no live DB: AuditService.log is patched, same convention as every other
reliability-signal test this session).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.agents.new.a9_solution_finder_agent import _flush_sf_audit_log


@pytest.mark.asyncio
async def test_noop_when_client_id_missing():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
        await _flush_sf_audit_log(None, "req-1", [{"event": "token_usage", "calls": 3}])
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_noop_when_events_empty():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
        await _flush_sf_audit_log("lubricants", "req-1", [])
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_event_type_is_namespaced_sf_dot():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
        await _flush_sf_audit_log("lubricants", "req-1", [{"event": "causal_context", "edges": 6}])
    kwargs = spy.call_args.kwargs
    assert kwargs["event_type"] == "sf.causal_context"
    assert kwargs["client_id"] == "lubricants"
    assert kwargs["request_id"] == "req-1"
    assert kwargs["source_agent"] == "A9_Solution_Finder_Agent"


def test_payload_excludes_the_event_key_itself():
    """The event name lives in event_type, not duplicated inside payload."""
    import asyncio

    async def _run():
        with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
            await _flush_sf_audit_log(
                "lubricants", "req-1",
                [{"event": "token_usage", "calls": 3, "total_tokens": 1500}],
            )
        return spy.call_args.kwargs["payload"]

    payload = asyncio.run(_run())
    assert payload == {"calls": 3, "total_tokens": 1500}
    assert "event" not in payload


@pytest.mark.asyncio
async def test_outcome_is_always_none_narrative_events_have_no_verdict():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
        await _flush_sf_audit_log("lubricants", "req-1", [{"event": "ranked_options", "count": 3}])
    assert "outcome" not in spy.call_args.kwargs  # AuditService.log defaults outcome=None


@pytest.mark.asyncio
async def test_severity_elevated_for_known_problem_events():
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
        await _flush_sf_audit_log("lubricants", "req-1", [
            {"event": "llm_debate_error", "error": "timeout"},
            {"event": "heuristic_stub_fallback", "reason": "token ceiling"},
            {"event": "impact_scope_contradiction", "detail": "..."},
            {"event": "token_usage", "calls": 1},  # ordinary narration
        ])
    severities = {c.kwargs["event_type"]: c.kwargs["severity"] for c in spy.call_args_list}
    assert severities["sf.llm_debate_error"] == "error"
    assert severities["sf.heuristic_stub_fallback"] == "warning"
    assert severities["sf.impact_scope_contradiction"] == "warning"
    assert severities["sf.token_usage"] == "info"


@pytest.mark.asyncio
async def test_all_events_flushed_even_with_duplicate_names():
    """A real run's audit_log can carry the same event name more than once
    (e.g. multiple impact_estimate_computed entries, one per option) -- every
    entry must be flushed, not deduplicated by event name."""
    events = [{"event": "impact_estimate_computed", "option": "opt_1"},
              {"event": "impact_estimate_computed", "option": "opt_2"}]
    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=AsyncMock()) as spy:
        await _flush_sf_audit_log("lubricants", "req-1", events)
    assert spy.await_count == 2


@pytest.mark.asyncio
async def test_a_failed_write_never_raises_and_does_not_block_the_others():
    """AuditService.log() already never raises by its own contract -- this
    confirms the flush has a defensive second layer (return_exceptions=True)
    rather than depending solely on that contract, since this call sits
    directly in the response path for SF's main return value. A future
    violation of AuditService.log's own guarantee must degrade to a dropped
    event here, never to a broken SF response a principal is waiting on."""
    calls = []

    async def _flaky(**kwargs):
        calls.append(kwargs["event_type"])
        if kwargs["event_type"] == "sf.llm_debate_error":
            raise RuntimeError("simulated contract violation")
        return True

    with patch("src.agents.new.a9_solution_finder_agent.AuditService.log", new=_flaky):
        await _flush_sf_audit_log("lubricants", "req-1", [
            {"event": "llm_debate_error"}, {"event": "token_usage"},
        ])  # must not raise

    assert set(calls) == {"sf.llm_debate_error", "sf.token_usage"}
