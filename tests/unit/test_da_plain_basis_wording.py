"""Segments worse on one comparison and better on the other are described as exactly that
(owner, 2026-10-29).

They were called "likely a comparison-timing artifact" in Deep Analysis's summary, and Solution
Finder was told not to build options around them. On lubricants Net Revenue (a budget-led card)
every segment was ahead of last year but short of budget, so the whole gap to plan was set aside
as a timing effect. The words now state the two comparisons, and Solution Finder treats a gap
with no segment worse on both as the gap on the main comparison.
"""
import pytest

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
from src.agents.new.a9_solution_finder_agent import _extract_deep_analysis_summary
from src.agents.models.deep_analysis_models import DeepAnalysisPlan, KTIsIsNot


def _da():
    da = A9_Deep_Analysis_Agent.__new__(A9_Deep_Analysis_Agent)
    import logging
    da.logger = logging.getLogger("test")
    da.llm_service_agent = None
    da.orchestrator = None
    return da


def _plan():
    return DeepAnalysisPlan(kpi_name="Net Revenue", client_id="lubricants", timeframe="year_to_date")


def _budget_led_kt():
    # Every flagged segment: short of budget, ahead of last year.
    return KTIsIsNot(
        where_is=[
            {"key": "Retail Partners", "delta": -10.9, "secondary_delta": 1.7, "basis_agreement": "basis_specific"},
            {"key": "Distributors", "delta": -6.2, "secondary_delta": 0.9, "basis_agreement": "basis_specific"},
        ],
        where_is_not=[],
    )


def test_facts_describe_both_comparisons_and_never_say_artifact():
    text = _da()._build_situation_complication_facts(
        plan=_plan(), kt=_budget_led_kt(), change_points=[], spec={"comparison_type": "budget"},
        analysis_mode="problem", matrix_ran=True, comparator_secondary="previous",
    )
    assert "worse than Budget/Plan but better than the prior period" in text
    assert "artifact" not in text.lower() and "timing" not in text.lower()


@pytest.mark.asyncio
async def test_scqa_fallback_asks_about_the_gap_when_nothing_is_worse_on_both():
    text = await _da()._generate_scqa_summary(
        plan=_plan(), kt=_budget_led_kt(), change_points=[], spec={"comparison_type": "budget"},
        principal_id="cfo_001", analysis_mode="problem", matrix_ran=True, comparator_secondary="previous",
    )
    assert "artifact" not in text.lower()
    assert "no segments problem" not in text  # the old question read "address the no segments problem"
    assert "Question: What closes the gap to Budget/Plan across the flagged segments?" in text


def test_solution_finder_gets_the_meaning_in_words():
    summary = _extract_deep_analysis_summary({
        "matrix_ran": True, "comparator": "budget", "comparator_secondary": "previous",
        "kt_is_is_not": _budget_led_kt().model_dump(),
    })
    assert summary["basis_specific_segments"] == ["Retail Partners", "Distributors"]
    assert summary["basis_specific_meaning"] == "worse than budget but better than the prior period"


def test_solution_finder_instruction_no_longer_sets_these_segments_aside():
    import inspect
    from src.agents.new import a9_solution_finder_agent as sf
    src = inspect.getsource(sf)
    assert "probable comparison-timing artifacts" not in src
    assert "do NOT build primary options around them" not in src
    assert "gap to plan across the business" in src
