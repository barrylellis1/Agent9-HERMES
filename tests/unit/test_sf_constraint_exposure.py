# arch-allow-direct-agent-construction
"""
Constraint provenance and deterministic exposure reporting (Stage I B-2).

Three defects and one safety net, all independent of whether per-persona
constraint splitting is ever built:

  * `(refinement + register)[:5]` let five interview constraints crowd the
    assumption register out entirely — and the register is the Stage H
    moderator's whole grading denominator, so a talkative interview could
    silently disarm adjudication. Nothing asserted it.
  * `_accumulate_refinements` replayed prior turns through the KEYWORD
    extractor, discarding structured LLM output and losing `exclusions`
    permanently.
  * The HITL approval surface read "Review ranked options and approve" with no
    qualification, implying a constraint review had happened even when
    `enable_theory_moderator` was off and nothing had checked anything.

The exposure report is computed in Python on every run precisely because the
moderator is optional. It reports WHO SAW WHAT — never whether an option
violates a constraint, which is a semantic judgement no regex makes honestly.
"""

import pytest

from src.agents.models.deep_analysis_models import ConstraintItem, constraint_id
from src.agents.new.a9_solution_finder_agent import (
    _MAX_REFINEMENT_CONSTRAINTS_S1,
    _MAX_REGISTER_CONSTRAINTS_S1,
    build_constraint_hitl_context,
    compute_constraint_exposure,
)

PERSONAS = ["mckinsey", "bcg", "bain"]


def _ci(text, source="refinement", discovered_by=None):
    return ConstraintItem(
        id=constraint_id(text), text=text, source=source,
        discovered_by=list(discovered_by or []),
    )


# ---------------------------------------------------------------------------
# constraint_id — the dedup key
# ---------------------------------------------------------------------------


def test_constraint_id_is_stable_across_whitespace_and_case():
    a = constraint_id("The union agreement runs through Q3")
    b = constraint_id("  the   UNION agreement runs through Q3 ")
    assert a == b


def test_constraint_id_separates_genuinely_different_constraints():
    assert constraint_id("Pricing is frozen") != constraint_id("Headcount is frozen")


# ---------------------------------------------------------------------------
# The truncation defect
# ---------------------------------------------------------------------------


def test_register_and_refinement_have_separate_budgets():
    """The regression for `(refinement + register)[:5]`.

    Five refinement constraints used to consume the entire cap, leaving the
    moderator grading against a register of zero — while still reporting a
    constraint count, so the disarming was invisible.
    """
    refinement = [f"refinement constraint {i}" for i in range(6)]
    register = ["union agreement runs through Q3", "anchor account price freeze"]

    merged = refinement[:_MAX_REFINEMENT_CONSTRAINTS_S1] + register[:_MAX_REGISTER_CONSTRAINTS_S1]

    for r in register:
        assert r in merged, "register constraint crowded out by the interview"
    assert len(merged) > _MAX_REFINEMENT_CONSTRAINTS_S1, "a single outer cap has been reintroduced"


# ---------------------------------------------------------------------------
# Exposure
# ---------------------------------------------------------------------------


def test_no_split_means_no_exposure_gap():
    """Today's behaviour: all personas get the flat union, so nothing is unseen.

    Reporting a gap here would be a false alarm — the gap opens only when
    constraint sets are actually split (B-4).
    """
    items = [_ci("Pricing is frozen"), _ci("Union runs through Q3", source="assumption_register")]
    exposure = compute_constraint_exposure(constraint_items=items, persona_ids=PERSONAS)

    assert exposure["union_size"] == 2
    for pid in PERSONAS:
        assert exposure["by_persona"][pid]["unseen"] == []
        assert len(exposure["by_persona"][pid]["seen"]) == 2


def test_persona_with_a_strict_subset_reports_the_exact_complement():
    seen_by_bain = _ci("Union runs through Q3", discovered_by=["bain"])
    shared = _ci("Pricing is frozen", discovered_by=["mckinsey", "bcg", "bain"])
    exposure = compute_constraint_exposure(
        constraint_items=[seen_by_bain, shared], persona_ids=PERSONAS
    )

    assert exposure["by_persona"]["bain"]["unseen"] == []
    assert exposure["by_persona"]["mckinsey"]["unseen"] == [seen_by_bain.id]
    assert exposure["by_persona"]["bcg"]["unseen"] == [seen_by_bain.id]


def test_register_constraints_reach_every_persona_regardless_of_discovery():
    """Register constraints are not persona-discovered facts.

    Splitting them would degrade the moderator, whose denominator they are.
    """
    reg = _ci("Union runs through Q3", source="assumption_register", discovered_by=["bain"])
    exposure = compute_constraint_exposure(constraint_items=[reg], persona_ids=PERSONAS)

    for pid in PERSONAS:
        assert exposure["by_persona"][pid]["unseen"] == []


def test_option_without_an_originating_persona_is_not_given_a_fabricated_gap():
    """Attribution lands in B-4; until then we cannot know, so we do not guess."""
    items = [_ci("Pricing is frozen", discovered_by=["bain"])]
    exposure = compute_constraint_exposure(
        constraint_items=items, persona_ids=PERSONAS,
        options=[{"id": "opt_1", "title": "Reprice"}],
    )

    assert exposure["by_option"]["opt_1"]["originating_persona"] is None
    assert exposure["by_option"]["opt_1"]["constraints_unseen"] == []


def test_option_exposure_follows_its_originating_persona():
    only_bain = _ci("Union runs through Q3", discovered_by=["bain"])
    exposure = compute_constraint_exposure(
        constraint_items=[only_bain], persona_ids=PERSONAS,
        options=[{"id": "opt_1", "originating_persona": "mckinsey"}],
    )

    assert exposure["by_option"]["opt_1"]["constraints_unseen"] == [only_bain.id]


def test_empty_union_is_not_reported_as_full_coverage():
    exposure = compute_constraint_exposure(constraint_items=[], persona_ids=PERSONAS)
    assert exposure["union_size"] == 0
    for pid in PERSONAS:
        assert exposure["by_persona"][pid]["seen"] == []


# ---------------------------------------------------------------------------
# The HITL surface — the load-bearing string
# ---------------------------------------------------------------------------


def test_moderator_off_says_plainly_that_nothing_was_checked():
    """The most important assertion in this file.

    enable_theory_moderator defaults False. A surface that says only "review and
    approve" implies a check happened when none did — the reader has no way to
    tell an unchecked run from a clean one.
    """
    items = [_ci("Pricing is frozen"), _ci("Union runs through Q3")]
    exposure = compute_constraint_exposure(
        constraint_items=items, persona_ids=PERSONAS, moderator_checked=False
    )
    ctx = build_constraint_hitl_context(exposure, items, "opt_1")

    assert ctx["constraint_check_performed"] is False
    assert "no adjudication pass ran" in ctx["summary"]
    assert "2 constraint(s) were captured" in ctx["summary"]
    assert len(ctx["constraint_union"]) == 2


def test_moderator_on_and_fully_exposed_reports_the_grading():
    items = [_ci("Pricing is frozen")]
    exposure = compute_constraint_exposure(
        constraint_items=items, persona_ids=PERSONAS, moderator_checked=True,
        options=[{"id": "opt_1", "originating_persona": "bain"}],
    )
    ctx = build_constraint_hitl_context(exposure, items, "opt_1")

    assert ctx["constraint_check_performed"] is True
    assert "graded against all 1 captured constraint" in ctx["summary"]
    assert ctx["recommended_option_unseen_constraints"] == []


def test_moderator_on_with_unseen_constraints_names_the_shortfall():
    only_bain = _ci("Union runs through Q3", discovered_by=["bain"])
    shared = _ci("Pricing is frozen", discovered_by=PERSONAS)
    items = [only_bain, shared]
    exposure = compute_constraint_exposure(
        constraint_items=items, persona_ids=PERSONAS, moderator_checked=True,
        options=[{"id": "opt_1", "originating_persona": "mckinsey"}],
    )
    ctx = build_constraint_hitl_context(exposure, items, "opt_1")

    assert ctx["recommended_option_unseen_constraints"] == [only_bain.id]
    assert "without knowledge of 1 of the 2" in ctx["summary"]


def test_no_constraints_at_all_is_stated_rather_than_implied():
    exposure = compute_constraint_exposure(constraint_items=[], persona_ids=PERSONAS)
    ctx = build_constraint_hitl_context(exposure, [], None)
    assert "No constraints were captured" in ctx["summary"]


def test_top_level_refinement_result_is_actually_wired():
    """Regression: a documented request field that was silently ignored.

    `SolutionWorkflowRequest.refinement_result` has existed and been documented
    as the way to pass refinement output, but Solution Finder only ever reads
    `preferences["refinement_result"]` — so a caller using the documented field
    got no constraints, no exclusions, and no error. Found by a live run
    (2026-08-12) where the constraint union contained the register constraint
    and not the principal's own.

    Same failure class as the never-wired `use_structured_output` flag: the
    field existed, typechecked, and did nothing.
    """
    import inspect

    from src.api.routes import workflows as wf

    src = inspect.getsource(wf)
    assert 'request.refinement_result' in src, (
        "SolutionWorkflowRequest.refinement_result is declared but never read — "
        "callers using the documented field get no refinement context"
    )
    # And SF must still read it from preferences, which is where the UI puts it.
    from src.agents.new import a9_solution_finder_agent as sf_mod
    assert 'prefs.get("refinement_result")' in inspect.getsource(sf_mod)


def test_exposure_accepts_plain_dicts_as_well_as_models():
    """The union is assembled from two sources with different runtime shapes."""
    exposure = compute_constraint_exposure(
        constraint_items=[
            {"id": "c_1", "text": "a", "source": "refinement", "discovered_by": ["bain"]},
            {"id": "c_2", "text": "b", "source": "assumption_register"},
        ],
        persona_ids=["bain", "bcg"],
    )
    assert exposure["union_size"] == 2
    assert exposure["by_persona"]["bcg"]["unseen"] == ["c_1"]
    assert "c_2" in exposure["by_persona"]["bcg"]["seen"]


def test_causal_audit_counts_constraints_after_they_are_fetched():
    """The audit event must report the register, not the empty list it starts as.

    THE DEFECT
    ----------
    The `causal_context` audit append sat ABOVE the constraint fetch:

        _cg_constraints: List[Any] = []          # line ~1798
        ...
        audit_log.append({... "constraints": len(_cg_constraints or []) ...})
        _cg_constraints = await AssumptionProvider().get_active_constraints(...)

    so `constraints` was measured while still bound to the initial empty list and
    every run reported `constraints: 0` regardless of what the register held. The
    lubricants register in fact contains an active constraint scoped to
    gross_margin_pct, and it WAS reaching Stage 1 the whole time — only the
    instrument was blind.

    This is the same defect shape as the DA KT summary's "(0.0% of variance)":
    a measurement asserting zero when it simply had not looked yet. A false zero
    from an audit log is worse than a missing field, because it reads as a
    verified finding and was used to gate real design decisions.
    """
    import inspect

    from src.agents.new import a9_solution_finder_agent as sf_mod

    src = inspect.getsource(sf_mod)
    fetch = src.find("await AssumptionProvider().get_active_constraints")
    audit = src.find('"event": "causal_context"')

    assert fetch != -1, "constraint fetch not found"
    assert audit != -1, "causal_context audit event not found"
    assert fetch < audit, (
        "the causal_context audit event reads _cg_constraints before the register "
        "is queried, so it reports a false zero on every run"
    )
