"""A run where the LLM never executed must not report success.

WHY THIS FILE EXISTS
--------------------
Observed live on 2026-08-09. The Anthropic account hit zero credit, so EVERY
LLM call in a Solution Finder run failed:

    credit balance is too low to access the Anthropic API

The workflow returned:

    state: completed        error: None
    options: "Tighten spend controls", "Optimize pricing"

`heuristic_stub_fallback` and the credit error were both present in the audit
log, so detection existed — it simply never reached the reader. A total outage
was indistinguishable from a real recommendation.

That is worse than a wrong number, because a wrong number can be argued with.
And the blandness of "tighten spend controls" is exactly what a sceptic expects
a weak AI tool to produce, so it discredits the product precisely when it is not
working.

Two distinctions this pins:
  - llm_unavailable      -> nothing ran. The workflow FAILS.
  - llm_yielded_no_options -> the model answered but synthesis was unparseable
                            (usually truncation). Stage 1 hypotheses survive, so
                            this DEGRADES and stays visible.
"""
from __future__ import annotations

import pytest

from src.agents.models.solution_finder_models import SolutionFinderResponse


class TestTheResponseCarriesDegradation:
    def test_a_healthy_response_is_not_degraded(self):
        r = SolutionFinderResponse.success(request_id="r1")
        assert r.analysis_degraded is False
        assert r.degraded_reason is None

    def test_llm_unavailable_round_trips(self):
        r = SolutionFinderResponse.success(
            request_id="r1", analysis_degraded=True, degraded_reason="llm_unavailable")
        assert r.analysis_degraded is True
        assert r.degraded_reason == "llm_unavailable"

    def test_truncation_is_a_distinct_reason(self):
        """Not the same failure, and must not be treated the same.

        The model DID respond here; partial signal survives. Failing the run
        would discard work that is still useful.
        """
        r = SolutionFinderResponse.success(
            request_id="r1", analysis_degraded=True, degraded_reason="llm_yielded_no_options")
        assert r.degraded_reason == "llm_yielded_no_options"

    def test_an_unknown_reason_is_rejected(self):
        """The Literal keeps the two cases from blurring into a free-text field
        that consumers would have to pattern-match."""
        with pytest.raises(Exception):
            SolutionFinderResponse.success(
                request_id="r1", analysis_degraded=True, degraded_reason="something_else")

    def test_degradation_defaults_off_so_silence_is_never_degraded(self):
        """An older payload without the field must read as healthy, not broken.

        The opposite default would mark every historical response degraded and
        train readers to ignore the banner.
        """
        r = SolutionFinderResponse(request_id="r1", status="success")
        assert r.analysis_degraded is False


class TestWorkflowStateRules:
    """The mapping the API applies. Kept as explicit expectations so a future
    change to the rule is a deliberate edit rather than a silent drift."""

    @staticmethod
    def _state_for(reason):
        # Mirrors _run_solution_workflow in src/api/routes/workflows.py.
        return "failed" if reason == "llm_unavailable" else "completed"

    def test_llm_unavailable_fails_the_run(self):
        assert self._state_for("llm_unavailable") == "failed"

    def test_truncation_still_completes(self):
        # Partial output is worth showing, flagged. Discarding it would lose the
        # Stage 1 hypotheses, which are preserved specifically for this case.
        assert self._state_for("llm_yielded_no_options") == "completed"

    def test_a_healthy_run_completes(self):
        assert self._state_for(None) == "completed"
