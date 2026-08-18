# arch-allow-direct-agent-construction
"""
Regression test: DA's SCQA generation failure returns None, never a fabricated frame.

`_safe_generate_scqa_summary` was extracted from `execute_deep_analysis()`
(2026-08-17) specifically so this could be tested in isolation. Nothing in this
suite drives `execute_deep_analysis()` end to end — it is an ~850-line
orchestration method — so before the extraction this behavior was only ever
verifiable live, and the bug it guards against shipped for months undetected
that way.

THE BUG THIS GUARDS AGAINST
----------------------------
The branch used to catch any exception from `_generate_scqa_summary` (an LLM
call) and substitute:

    "Situation: Reviewing {kpi}. Complication: Variance detected vs target.
     Question: Which segments drive the change?"

SCQA is a framing device — its Q *is* the frame — so that fabricated a
dimensional-attribution frame as a CONSTANT on the failure path, and every
downstream stage (the council, the moderator, HITL) answered it faithfully
with nobody ever having asked it. See `docs/architecture/problem_framing_design.md`.

NOT covered here: `_generate_scqa_summary`'s OWN internal deterministic
fallback (used when the LLM call inside it merely fails, not when the whole
method raises) is a *different*, legitimate mechanism — it reconstructs a
narrative from real, measured change_points/kt data rather than fabricating
one. That path is exercised by `test_11i_compound_alerts.py` and
`test_da_sf_va_opportunity_mode.py`. This file tests only the outer
catch-all — the one that used to fabricate content with no data behind it
at all.
"""
import logging

import pytest

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent


def _make_da_stub() -> A9_Deep_Analysis_Agent:
    """Same lightweight construction pattern as test_11i_compound_alerts.py —
    no orchestrator, DPA, or LLM infrastructure needed for this method."""
    stub = object.__new__(A9_Deep_Analysis_Agent)
    stub.logger = logging.getLogger("test.da_stub")
    return stub


class TestSafeGenerateScqaSummary:
    @pytest.mark.asyncio
    async def test_exception_returns_none_not_fabricated_text(self, monkeypatch):
        """The regression case: _generate_scqa_summary raises -> result is None."""
        da = _make_da_stub()

        async def _boom(**kwargs):
            raise RuntimeError("simulated LLM/SCQA generation failure")

        monkeypatch.setattr(da, "_generate_scqa_summary", _boom)

        result = await da._safe_generate_scqa_summary(
            plan=None, kt=None, change_points=[], spec=None,
            principal_id="test_principal",
        )

        assert result is None
        # The specific string this bug produced must never reappear here.
        # A future "helpful" re-fix that adds ANY hardcoded question text would
        # be exactly the regression this test exists to catch.
        assert result != "Which segments drive the change?"

    @pytest.mark.asyncio
    async def test_success_path_passes_through_unchanged(self, monkeypatch):
        """Sanity check the wrapper doesn't mangle a genuine result — the fix
        must change ONLY the failure path."""
        da = _make_da_stub()

        real_summary = "Situation: Gross Margin % declined 7.14pp. Complication: concentrated in Synthetic Blend Engine Oil. Question: Is the objective margin recovery, or reducing base-oil exposure?"

        async def _real(**kwargs):
            return real_summary

        monkeypatch.setattr(da, "_generate_scqa_summary", _real)

        result = await da._safe_generate_scqa_summary(
            plan=None, kt=None, change_points=[], spec=None,
            principal_id="test_principal",
        )

        assert result == real_summary

    @pytest.mark.asyncio
    async def test_exception_is_logged_not_swallowed_silently(self, monkeypatch, caplog):
        """Absence must still be OBSERVABLE in logs — silent-and-untraceable is
        a different failure mode than fabricated-and-misleading, but still a
        failure mode. The warning is what lets a real outage be distinguished
        from a KPI that genuinely has nothing to report."""
        da = _make_da_stub()

        async def _boom(**kwargs):
            raise ValueError("upstream KT data malformed")

        monkeypatch.setattr(da, "_generate_scqa_summary", _boom)

        with caplog.at_level(logging.WARNING, logger="test.da_stub"):
            await da._safe_generate_scqa_summary(plan=None, kt=None, change_points=[], spec=None)

        assert any("SCQA generation failed" in r.message for r in caplog.records)
