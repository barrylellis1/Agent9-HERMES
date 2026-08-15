# arch-allow-direct-agent-construction
"""
Problem-shape-routed refinement topics (Stage I B-1).

The refinement interview ran a FIXED five-topic sequence regardless of what the
analysis had already established — so a concentrated single-segment problem and a
diffuse enterprise one got the same five questions in the same order. Turns were
spent asking what the data had already answered, and questions only a human could
answer were never reached.

`src/analysis/problem_profile.py` classified the structural facets deterministically
and was consumed by nothing on any production path. These tests cover its first
live use. The ROUTING is deterministic — no LLM is involved in choosing topics,
only in wording them.

Also covers two latent defects fixed alongside, without which the routing would
have been unobservable or would have raced its own progress:

  * `_extract_completed_topics` scanned assistant prose for "moving to {topic}",
    which nothing emits, and iterated the STATIC sequence so it could never see a
    routed topic. Replaced by a client round-trip.
  * `_check_topic_complete` counted EVERY assistant message rather than messages
    since the last topic change, auto-completing every topic from turn 3 onward.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.new.a9_deep_analysis_agent import (
    MAX_TOPICS_IN_SEQUENCE,
    PROTECTED_TOPICS,
    REFINEMENT_TOPIC_SEQUENCE,
    TOPIC_OBJECTIVES,
    A9_Deep_Analysis_Agent,
)
from src.agents.models.deep_analysis_models import (
    ExtractedRefinements,
    ProblemRefinementInput,
)


def _agent():
    return A9_Deep_Analysis_Agent({})


def _da(
    *,
    change_points=None,
    where_is_not=None,
    analysis_mode="problem",
    compound_alert=False,
    market_conflict=False,
    benchmarks=None,
):
    """Build a DA result shaped the way `problem_profile.classify` reads it."""
    execution = {
        "analysis_mode": analysis_mode,
        "change_points": change_points if change_points is not None else [],
        "kt_is_is_not": {
            "where_is_not": where_is_not if where_is_not is not None else [],
            "benchmark_segments": benchmarks or [],
        },
        "compound_alert": compound_alert,
        "market_conflict": market_conflict,
    }
    return {"plan": {"kpi_name": "gross_margin_pct"}, "execution": execution}


# Two change points 2.58x apart -> "concentrated" (DOMINANCE_THRESHOLD = 2.0)
_CONCENTRATED = [{"delta": -43.24}, {"delta": -16.76}]
# Near-equal -> "distributed"
_DISTRIBUTED = [{"delta": -7.14}, {"delta": -6.61}, {"delta": -5.86}]
_CONTROL_GROUP = [{"key": "Chain B", "delta": 1.2}]


# ---------------------------------------------------------------------------
# The no-op case comes first: routing must not disturb the default
# ---------------------------------------------------------------------------


def test_default_problem_shape_yields_the_historical_sequence():
    """A distributed problem with a control group routes to... almost the base.

    R2' fires (scope_boundaries leads), which is the designed behaviour for
    diffuse variance. The SET of topics must be unchanged.
    """
    agent = _agent()
    seq, profile, rules = agent._get_topic_sequence(
        _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP)
    )

    assert set(seq) == set(REFINEMENT_TOPIC_SEQUENCE), "no topic added or lost"
    assert profile.concentration == "distributed"
    assert profile.has_control_group is True
    assert seq[0] == "scope_boundaries"
    assert [r for r in rules if r.startswith("R2'")]


def test_classification_failure_degrades_to_the_base_sequence():
    """A routing failure must never cost the principal their interview."""
    agent = _agent()
    with patch("src.analysis.problem_profile.classify", side_effect=ValueError("boom")):
        seq, profile, rules = agent._get_topic_sequence(_da())

    assert seq == list(REFINEMENT_TOPIC_SEQUENCE)
    assert profile is None
    assert rules == []


# ---------------------------------------------------------------------------
# Individual rules
# ---------------------------------------------------------------------------


def test_r1_compound_alert_adds_tradeoff_tolerance_early():
    agent = _agent()
    seq, _, rules = agent._get_topic_sequence(
        _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP, compound_alert=True)
    )

    assert "tradeoff_tolerance" in seq
    assert seq.index("tradeoff_tolerance") < seq.index("constraints")
    assert any("R1" in r for r in rules)


def test_r2_concentrated_drops_scope_and_asks_why_this_segment():
    """A dominance ratio >= 2.0 means the data already answered "which segments"."""
    agent = _agent()
    seq, profile, rules = agent._get_topic_sequence(
        _da(change_points=_CONCENTRATED, where_is_not=_CONTROL_GROUP)
    )

    assert profile.concentration == "concentrated"
    assert "scope_boundaries" not in seq, "spent turn asking what the data showed"
    assert "segment_specific_causation" in seq
    assert seq.index("segment_specific_causation") == seq.index("hypothesis_validation") + 1
    assert any("R2:" in r for r in rules)


def test_r3_empty_is_not_set_asks_for_a_baseline():
    """No IS-NOT means "why here and not there" is unanswerable from data."""
    agent = _agent()
    seq, profile, rules = agent._get_topic_sequence(
        _da(change_points=_DISTRIBUTED, where_is_not=[])
    )

    assert profile.has_control_group is False
    assert "comparison_baseline" in seq
    assert any("R3" in r for r in rules)


def test_r5_opportunity_mode_asks_replication_before_constraints():
    """Replication barriers ARE constraints; splitting them wastes a turn."""
    agent = _agent()
    seq, _, rules = agent._get_topic_sequence(
        _da(
            change_points=_DISTRIBUTED,
            where_is_not=_CONTROL_GROUP,
            analysis_mode="opportunity",
            benchmarks=[{"benchmark_type": "internal_benchmark", "key": "Chain B"}],
        )
    )

    assert "replication_potential" in seq
    assert seq.index("replication_potential") < seq.index("constraints")
    assert any("R5" in r for r in rules)


# ---------------------------------------------------------------------------
# Composition and the cap
# ---------------------------------------------------------------------------


def test_two_rules_firing_together_compose_in_fixed_priority_order():
    """Concentrated AND no control group: both inserts land, order is stable."""
    agent = _agent()
    seq, _, _ = agent._get_topic_sequence(
        _da(change_points=_CONCENTRATED, where_is_not=[], compound_alert=True)
    )

    # Fixed priority: tension first, then where to look, then what to compare to.
    assert seq.index("tradeoff_tolerance") < seq.index("segment_specific_causation")
    assert seq.index("segment_specific_causation") < seq.index("comparison_baseline")


def test_cap_is_respected_and_never_drops_what_solution_finder_consumes():
    """The failure this guards: a long sequence starving `constraints`.

    MAX_TOTAL_TURNS is 10; at ~2 turns per topic a 9-topic sequence guarantees
    `constraints` is never reached, and Solution Finder then runs with an empty
    bound set — which is the exact defect Stage I exists to fix.
    """
    agent = _agent()
    seq, _, rules = agent._get_topic_sequence(
        _da(
            change_points=_CONCENTRATED,
            where_is_not=[],
            compound_alert=True,
            analysis_mode="opportunity",
            benchmarks=[{"benchmark_type": "internal_benchmark", "key": "Chain B"}],
        )
    )

    assert len(seq) <= MAX_TOPICS_IN_SEQUENCE
    for protected in PROTECTED_TOPICS:
        assert protected in seq, f"{protected} must survive truncation"
    assert any("CAP" in r for r in rules)


def test_turn_budget_scales_with_sequence_length():
    """The starvation the topic cap does NOT prevent.

    PROTECTED_TOPICS stops `constraints` being truncated out of the sequence. It
    does nothing about it never being reached: at ~2 turns per topic a 6-topic
    sequence needs ~12 turns against a fixed MAX_TOTAL_TURNS of 10, so the
    interview ends two topics short and Solution Finder gets no constraints.

    Found by a live run: a 6-topic routed sequence had reached topic 2 of 6 by
    turn 5.
    """
    from src.agents.new.a9_deep_analysis_agent import MAX_TOTAL_TURNS, effective_turn_budget

    # The default 5-topic sequence is unchanged — MAX_TOTAL_TURNS is a floor.
    assert effective_turn_budget(list(REFINEMENT_TOPIC_SEQUENCE)) == MAX_TOTAL_TURNS

    six = list(REFINEMENT_TOPIC_SEQUENCE) + ["comparison_baseline"]
    assert effective_turn_budget(six) >= 2 * len(six)
    assert effective_turn_budget(six) > MAX_TOTAL_TURNS

    assert effective_turn_budget([]) == MAX_TOTAL_TURNS


@pytest.mark.asyncio
async def test_a_good_llm_question_is_not_discarded_by_a_missing_default():
    """Regression: a successful generation thrown away by a lookup it didn't need.

    The parse branch indexed `default_questions[current_topic]` to build a
    fallback. For a routed topic absent from that dict this raised KeyError,
    which the surrounding `except Exception` swallowed — returning the generic
    "Please share any additional context." and discarding the model's answer.
    Observed live 2026-08-11 on `comparison_baseline`.
    """
    agent = _agent()
    llm = MagicMock()
    llm.analyze = AsyncMock(return_value=MagicMock(
        answer='{"question": "What should this be measured against?", "suggested_responses": ["Budget", "Prior year"]}'
    ))
    agent.llm_service_agent = llm

    for topic in ("comparison_baseline", "tradeoff_tolerance", "segment_specific_causation"):
        question, suggested = await agent._generate_refinement_question(
            current_topic=topic,
            decision_style="analytical",
            kt_summary="KPI: gross_margin_pct",
            history=[],
            user_message=None,
            accumulated=ExtractedRefinements(),
            principal_role="CFO",
        )
        assert "additional context" not in question.lower(), (
            f"{topic}: LLM answer was discarded in favour of the generic fallback"
        )


@pytest.mark.asyncio
async def test_every_routed_topic_has_an_authored_default_question():
    """The no-LLM path must not degrade a routed topic to a generic prompt."""
    agent = _agent()
    agent.llm_service_agent = None

    for topic in ("tradeoff_tolerance", "segment_specific_causation", "comparison_baseline"):
        question, suggested = await agent._generate_refinement_question(
            current_topic=topic,
            decision_style="analytical",
            kt_summary="",
            history=[],
            user_message=None,
            accumulated=ExtractedRefinements(),
            principal_role="CFO",
        )
        assert "additional context" not in question.lower(), f"{topic} has no authored default"
        assert len(suggested) >= 3


@pytest.mark.asyncio
async def test_prompt_forbids_the_agent_naming_itself():
    """Regression: the model was inventing a persona name for itself.

    The turn-0 instruction read "introduce yourself briefly" and never supplied
    an identity, so the model confabulated one — it opened with "I'm Alex" across
    three consecutive live runs (2026-08-11). Two problems: the identity was
    non-deterministic (nothing pinned it across model or prompt changes), and
    "Alex Morgan" is a real principal in scripts/clients/bicycle.py, so the
    assistant was liable to introduce itself using an actual user's name.

    Asserts the prompt, not the model's output: a stochastic generator cannot be
    unit-tested for what it will never say, but the instruction it is given can.
    """
    agent = _agent()
    captured = {}

    async def _capture(request):
        captured["system_prompt"] = request.system_prompt
        return MagicMock(answer='{"question": "Does the decline match a known event?", "suggested_responses": ["Yes", "No", "Partly"]}')

    llm = MagicMock()
    llm.generate = AsyncMock(side_effect=_capture)
    agent.llm_service_agent = llm

    # user_message=None selects the turn-0 branch, where the defect lived.
    await agent._generate_refinement_question(
        current_topic="hypothesis_validation",
        decision_style="analytical",
        kt_summary="KPI: gross_margin_pct  -4.49pp",
        history=[],
        user_message=None,
        accumulated=ExtractedRefinements(),
        principal_role="CFO",
    )

    prompt = captured["system_prompt"]
    # Match the removed INSTRUCTION, not the bare phrase — the prohibition that
    # replaced it necessarily contains "introduce yourself" itself.
    assert "introduce yourself briefly" not in prompt.lower()
    assert "NEVER introduce yourself" in prompt
    assert "open DIRECTLY with the specific findings" in prompt


# ---------------------------------------------------------------------------
# Constraint provenance (Stage I B-2)
# ---------------------------------------------------------------------------


def test_prior_typed_state_is_not_re_derived_heuristically():
    """The `_accumulate_refinements` defect.

    It replayed every prior user message through the KEYWORD extractor, throwing
    away the structured LLM output those turns had produced. `exclusions` were
    lost outright — the "general" branch never populates them — so a principal's
    "leave International out of this" ceased to exist one turn later.
    """
    from src.agents.models.deep_analysis_models import ConstraintItem, RefinementExclusion, constraint_id

    agent = _agent()
    prior = [ConstraintItem(
        id=constraint_id("Union runs through Q3"), text="Union runs through Q3",
        source="refinement", discovered_by=["bain"], turn_index=1,
    )]
    prior_excl = [RefinementExclusion(dimension="channel_name", value="International", reason="reseller")]

    # History full of prose the keyword extractor would happily mine.
    history = [
        {"role": "user", "content": "We cannot change pricing and headcount is frozen for now."},
        {"role": "assistant", "content": "Understood."},
    ]

    acc = agent._accumulate_refinements(history, prior, prior_excl)

    assert [c.id for c in acc.constraint_items] == [prior[0].id]
    assert acc.constraint_items[0].discovered_by == ["bain"], "provenance survived the round-trip"
    assert acc.exclusions == prior_excl, "exclusions are no longer lost between turns"


def test_keyword_replay_remains_the_fallback_when_no_typed_state_is_sent():
    """An older client that sends nothing must still get the old behaviour."""
    agent = _agent()
    history = [{"role": "user", "content": "We cannot change pricing, it is a hard constraint for us."}]

    acc = agent._accumulate_refinements(history, [], [])
    assert acc.constraints, "fallback extraction should still run for legacy callers"


def test_restating_a_constraint_merges_provenance_rather_than_duplicating():
    from src.agents.models.deep_analysis_models import ConstraintItem, ExtractedRefinements, constraint_id

    agent = _agent()
    text = "Union runs through Q3"
    acc = ExtractedRefinements(
        constraints=[text],
        constraint_items=[ConstraintItem(id=constraint_id(text), text=text,
                                         source="refinement", discovered_by=["bain"])],
    )
    incoming = ExtractedRefinements(
        constraint_items=[ConstraintItem(id=constraint_id("  union RUNS through q3 "),
                                         text=text, source="refinement", discovered_by=["mckinsey"])]
    )

    merged = agent._merge_refinements(acc, incoming)

    assert len(merged.constraint_items) == 1, "same constraint restated must not appear twice"
    assert merged.constraint_items[0].discovered_by == ["bain", "mckinsey"]


def test_bare_constraint_strings_get_typed_items_minted():
    """constraint_items must mirror constraints regardless of extraction path."""
    from src.agents.models.deep_analysis_models import ExtractedRefinements

    agent = _agent()
    merged = agent._merge_refinements(
        ExtractedRefinements(),
        ExtractedRefinements(constraints=["Pricing is frozen"]),
        source="refinement", turn_index=2,
    )

    assert len(merged.constraint_items) == 1
    assert merged.constraint_items[0].text == "Pricing is frozen"
    assert merged.constraint_items[0].source == "refinement"
    assert merged.constraint_items[0].turn_index == 2
    assert merged.constraints == ["Pricing is frozen"], "flat list stays in sync for existing consumers"


def test_every_routed_topic_has_an_objective():
    """A topic with no objective produces an empty LLM instruction."""
    agent = _agent()
    seen = set()
    for cps, isnot, compound, mode in [
        (_CONCENTRATED, [], True, "problem"),
        (_DISTRIBUTED, _CONTROL_GROUP, False, "opportunity"),
        ([], [], False, "problem"),
    ]:
        seq, _, _ = agent._get_topic_sequence(
            _da(change_points=cps, where_is_not=isnot, compound_alert=compound,
                analysis_mode=mode,
                benchmarks=[{"benchmark_type": "internal_benchmark", "key": "X"}])
        )
        seen.update(seq)

    for topic in seen:
        assert TOPIC_OBJECTIVES.get(topic), f"topic '{topic}' has no objective text"


# ---------------------------------------------------------------------------
# The two latent defects
# ---------------------------------------------------------------------------


def test_extract_completed_topics_is_gone():
    """Recovering state by pattern-matching an LLM's prose was the defect.

    It searched for "moving to {topic}" / "completed {topic}" — phrases nothing
    emits — and iterated the static sequence, so it could never recognise a
    routed topic even if the phrases had appeared.
    """
    assert not hasattr(A9_Deep_Analysis_Agent, "_extract_completed_topics")


@pytest.mark.asyncio
async def test_topics_completed_round_trips_from_the_client():
    agent = _agent()
    agent.llm_service_agent = None  # deterministic default question path

    result = await agent.refine_analysis(
        ProblemRefinementInput(
            deep_analysis_output=_da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
            principal_context={"decision_style": "analytical", "role": "CFO"},
            conversation_history=[{"role": "assistant", "content": "q1"}],
            current_topic="external_context",
            turn_count=1,
            topics_completed=["scope_boundaries", "hypothesis_validation"],
        )
    )

    assert "scope_boundaries" in result.topics_completed
    assert "hypothesis_validation" in result.topics_completed


@pytest.mark.asyncio
async def test_a_fresh_topic_does_not_auto_complete_on_a_long_conversation():
    """The regression for the all-messages turn counter.

    Six assistant messages in history, but zero turns on THIS topic. The old
    counter returned True immediately — so a topic added because the problem's
    shape demanded it would be marked complete before it was ever asked.
    """
    agent = _agent()
    long_history = [{"role": "assistant", "content": f"q{i}"} for i in range(6)]

    complete = await agent._check_topic_complete(
        "comparison_baseline", long_history, "hmm", ExtractedRefinements(),
        turns_on_current_topic=0,
    )
    assert complete is False

    # And the per-topic cap still fires once genuinely spent on this topic.
    assert await agent._check_topic_complete(
        "comparison_baseline", long_history, "hmm", ExtractedRefinements(),
        turns_on_current_topic=3,
    ) is True


# ---------------------------------------------------------------------------
# Observability — routing that cannot be seen cannot be reviewed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_result_reports_the_profile_and_the_rules_that_fired():
    agent = _agent()
    agent.llm_service_agent = None

    result = await agent.refine_analysis(
        ProblemRefinementInput(
            deep_analysis_output=_da(change_points=_CONCENTRATED, where_is_not=[]),
            principal_context={"decision_style": "analytical", "role": "CFO"},
            conversation_history=[],
            turn_count=0,
        )
    )

    assert result.problem_profile_cell == "problem/concentrated/no-control/single"
    assert "segment_specific_causation" in result.topic_sequence
    assert "comparison_baseline" in result.topic_sequence
    assert result.topic_routing_rules_applied, "rules that fired must be reported"


@pytest.mark.asyncio
async def test_market_conflict_keeps_external_context_off_the_turn0_autoskip():
    """R4. MA seeds external_context and the topic is normally auto-skipped.

    A detected conflict between the market signal and the internal data is the
    reason to ask, not a substitute for asking.
    """
    agent = _agent()
    agent.llm_service_agent = None

    da = _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP, market_conflict=True)
    result = await agent.refine_analysis(
        ProblemRefinementInput(
            deep_analysis_output=da,
            principal_context={"decision_style": "analytical", "role": "CFO"},
            conversation_history=[],
            turn_count=0,
            initial_external_context=["Market signal: base oil up 18%"],
        )
    )

    assert "external_context" not in result.topics_completed
    assert any("R4" in r for r in result.topic_routing_rules_applied)


@pytest.mark.asyncio
async def test_no_market_conflict_still_autoskips_external_context():
    """The unchanged path — R4 must not fire on an ordinary problem."""
    agent = _agent()
    agent.llm_service_agent = None

    result = await agent.refine_analysis(
        ProblemRefinementInput(
            deep_analysis_output=_da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
            principal_context={"decision_style": "analytical", "role": "CFO"},
            conversation_history=[],
            turn_count=0,
            initial_external_context=["Market signal: base oil up 18%"],
        )
    )

    assert "external_context" in result.topics_completed
