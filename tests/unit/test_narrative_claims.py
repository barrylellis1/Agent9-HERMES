"""
Deterministic validation of LLM narrative in SF output (2026-08-08).

The groundedness scorer checks each option's impact_estimate. It never looked at
the PROSE — which leads page one of the Executive Briefing, above the fold.

Two real errors from one live run, both in `problem_reframe`, both past every
guard that existed at the time. They are the regression fixtures below.

Tuning note: the first cue implementation was a bare match on "headline", which
produced 4 false positives out of 6 findings on the real payload — all from one
sentence enumerating segments *beneath* the headline. Flags that cry wolf get
ignored, which is worse than no flags, so several tests here exist specifically
to pin the absence of those false positives.
"""
from __future__ import annotations

import pytest

from src.analysis.narrative_claims import (
    HEADLINE_TOLERANCE,
    check_narrative,
    check_stated_sums,
    extract_narrative_fields,
)

# Verbatim from the live payload.
REAL_SITUATION = (
    "Year-to-date Gross Margin % has dropped sharply, with the headline KPI move "
    "recorded as a -43.24 point deterioration to a current level of -445.01, driven "
    "overwhelmingly by a single customer relationship, National Auto Parts Chain A."
)
REAL_COMPLICATION = (
    "Performance beneath that headline number is mixed, not uniform: three segments — "
    "National Auto Parts Chain A (-43.24pp), Synthetic Blend Engine Oil (-16.76pp), and "
    "Service Centers Division (-15.18pp) — are collectively dragging margin down by "
    "140.4pp of combined drag, while International Division shows no material upside."
)
TRUE_HEADLINE = 30.29     # Gross Margin %, from the typed KPIValue
TRUE_DELTA = -6.10


class TestRealErrors:
    """The two defects that reached a briefing."""

    def test_catches_segment_presented_as_headline(self):
        res = check_narrative({"situation": REAL_SITUATION},
                              headline_value=TRUE_HEADLINE, headline_delta=TRUE_DELTA)
        kinds = [f.kind for f in res.findings]
        assert "headline_substitution" in kinds
        f = next(f for f in res.findings if f.kind == "headline_substitution")
        assert f.claimed == pytest.approx(-43.24)   # Chain A's delta
        assert not res.ok

    def test_catches_sum_that_does_not_match_its_own_components(self):
        # 43.24 + 16.76 + 15.18 = 75.18, prose claims 140.4 (1.9x).
        findings = check_stated_sums(REAL_COMPLICATION, "complication")
        assert len(findings) == 1
        assert findings[0].claimed == pytest.approx(140.4)
        assert findings[0].expected == pytest.approx(75.18, abs=0.01)
        assert "1.9x" in findings[0].detail

    def test_full_payload_yields_exactly_the_two_real_errors(self):
        """No false positives on the real text — the whole point of the tuning."""
        res = check_narrative(
            {"problem_reframe.situation": REAL_SITUATION,
             "problem_reframe.complication": REAL_COMPLICATION},
            headline_value=TRUE_HEADLINE, headline_delta=TRUE_DELTA,
        )
        assert len(res.findings) == 2, [str(f) for f in res.findings]
        assert {f.kind for f in res.findings} == {"headline_substitution", "sum_mismatch"}


class TestNoFalsePositives:
    """Each pins a specific way the first implementation cried wolf."""

    def test_segments_beneath_the_headline_are_not_headline_claims(self):
        # THE false positive: a sentence discussing what sits UNDER the headline.
        findings = check_narrative({"c": REAL_COMPLICATION},
                                   headline_value=TRUE_HEADLINE, headline_delta=TRUE_DELTA).findings
        assert not [f for f in findings if f.kind == "headline_substitution"]

    def test_plain_segment_statements_are_never_flagged(self):
        text = "National Auto Parts Chain A fell 43.24pp and DIY Retail fell 16.76pp."
        res = check_narrative({"s": text}, headline_value=TRUE_HEADLINE, headline_delta=TRUE_DELTA)
        assert res.ok

    def test_a_correct_headline_claim_passes(self):
        text = "The headline KPI is 30.29%, down from the prior period."
        res = check_narrative({"s": text}, headline_value=TRUE_HEADLINE, headline_delta=TRUE_DELTA)
        assert res.ok

    def test_headline_within_tolerance_passes(self):
        text = f"The headline KPI is {TRUE_HEADLINE * (1 + HEADLINE_TOLERANCE * 0.5):.2f}%."
        assert check_narrative({"s": text}, headline_value=TRUE_HEADLINE).ok

    def test_claim_matching_the_delta_rather_than_the_level_passes(self):
        # Prose legitimately quotes either the level or the movement.
        text = "The headline KPI move was -6.1 points."
        assert check_narrative({"s": text}, headline_value=TRUE_HEADLINE, headline_delta=TRUE_DELTA).ok

    def test_distant_numbers_are_not_attributed_to_the_headline(self):
        # A later clause about something else must not be read as the claim.
        text = ("The headline KPI is 30.29%, and separately the team reviewed a backlog "
                "of 412 open items across the portfolio during the same period overall.")
        assert check_narrative({"s": text}, headline_value=TRUE_HEADLINE).ok

    def test_correct_sum_passes(self):
        text = "Segments fell 10.0pp, 5.0pp and 5.0pp, collectively 20.0pp of combined drag."
        assert not check_stated_sums(text, "s")

    def test_sum_within_tolerance_passes(self):
        text = "Segments fell 10.0pp and 10.0pp, collectively 20.5pp of combined drag."
        assert not check_stated_sums(text, "s")

    def test_single_component_is_not_a_sum_claim(self):
        # Nothing to add up — reporting this would be noise.
        text = "Chain A fell 43.24pp, a total decline of 43.24pp."
        assert not check_stated_sums(text, "s")

    def test_bare_integers_are_ignored(self):
        # Years, counts and ordinals carry no unit and would generate pure noise.
        text = "In 2026 the headline KPI is 30.29%, across 3 divisions and 12 accounts."
        assert check_narrative({"s": text}, headline_value=TRUE_HEADLINE).ok


class TestBehaviourContract:
    def test_no_findings_produces_no_audit_event(self):
        # An event asserting "no problems" is indistinguishable from a check that
        # never ran — same discipline as the token ledger and groundedness scorer.
        res = check_narrative({"s": "All within tolerance."}, headline_value=30.29)
        assert res.ok and res.as_audit_event() is None

    def test_findings_produce_a_structured_audit_event(self):
        res = check_narrative({"s": REAL_SITUATION}, headline_value=TRUE_HEADLINE)
        ev = res.as_audit_event()
        assert ev["event"] == "narrative_claim_mismatch"
        assert ev["count"] >= 1
        assert ev["findings"][0]["kind"] == "headline_substitution"
        assert "excerpt" in ev["findings"][0]

    def test_no_headline_supplied_means_not_checked_not_pass(self):
        # Without a baseline the check cannot run; it must not silently approve.
        res = check_narrative({"s": REAL_SITUATION})
        assert not [f for f in res.findings if f.kind == "headline_substitution"]
        assert "s" in res.checked_fields  # the field was seen, the check just had no basis

    def test_never_raises_on_junk_input(self):
        for bad in ({}, {"s": None}, {"s": ""}, {"s": 12345}, None):
            check_narrative(bad, headline_value=30.29)  # must not raise

    def test_dollar_magnitudes_are_scaled(self):
        text = "The headline KPI is $34.1M."
        res = check_narrative({"s": text}, headline_value=34_100_000)
        assert res.ok, [str(f) for f in res.findings]

    def test_extracts_the_prose_an_executive_reads(self):
        fields = extract_narrative_fields({
            "problem_reframe": {"situation": "s", "complication": "c", "question": "q"},
            "recommendation_rationale": "r",
            "options_ranked": [],
        })
        assert set(fields) == {"problem_reframe.situation", "problem_reframe.complication",
                               "problem_reframe.question", "recommendation_rationale"}

    def test_empty_and_non_string_fields_are_skipped(self):
        fields = extract_narrative_fields({"problem_reframe": {"situation": "", "complication": None}})
        assert fields == {}


class TestReversedTransitionDirection:
    """"A -> B" written backwards, alongside a correctly-signed delta.

    A live production briefing stated, twice:

        "enterprise headline Gross Margin % move (-2.69 points, 29.94%->32.63%)"

    which reads as RISING from 29.94 to 32.63 while labelled -2.69 points. Every
    existing check passed: each number was individually correct and the sums
    balanced. Only the ORDER of the endpoints was wrong, and nothing compared the
    direction they imply against the direction claimed beside them.
    """

    def test_catches_the_production_sentence(self):
        from src.analysis.narrative_claims import check_transition_direction
        text = ("The enterprise headline Gross Margin % move (-2.69 points, "
                "29.94%->32.63%) is smaller than the Engine Oils-specific decline.")
        f = check_transition_direction(text, "risk_register")
        assert len(f) == 1
        assert f[0].kind == "direction_mismatch"
        assert "reversed" in f[0].detail

    def test_silent_on_a_correctly_ordered_fall(self):
        from src.analysis.narrative_claims import check_transition_direction
        assert check_transition_direction(
            "Gross Margin % fell from 32.63% to 29.94%, a -2.69 point move.", "x") == []

    def test_silent_on_a_genuine_rise(self):
        from src.analysis.narrative_claims import check_transition_direction
        assert check_transition_direction(
            "Margin improved from 29.94% to 32.63%, a +2.69 point move.", "x") == []

    def test_needs_both_signals_in_one_sentence(self):
        """Narrow on purpose.

        Prose that merely mentions two figures, with no signed move beside them,
        is not evidence of anything. A check that cries wolf gets ignored — the
        lesson from tuning the headline cue after four false positives in six.
        """
        from src.analysis.narrative_claims import check_transition_direction
        assert check_transition_direction("Margin went from 32.63% to 29.94%.", "x") == []
        assert check_transition_direction("The move was -2.69 points.", "x") == []

    def test_arrow_and_prose_forms_both_parse(self):
        from src.analysis.narrative_claims import check_transition_direction
        for t in ("move (-2.69 points, 29.94% -> 32.63%) noted",
                  "move (-2.69 points, from 29.94% to 32.63%) noted"):
            assert check_transition_direction(t, "x"), f"missed: {t}"

    def test_identical_endpoints_are_not_a_direction(self):
        from src.analysis.narrative_claims import check_transition_direction
        assert check_transition_direction("flat from 29.94% to 29.94%, a -0.0 point move", "x") == []

    def test_runs_inside_check_narrative(self):
        """A checker that is written but never wired is not a checker — the
        exact gap that let the Stage H moderator panel ship unexecuted."""
        from src.analysis.narrative_claims import check_narrative
        res = check_narrative({"f": "move (-2.69 points, 29.94%->32.63%) observed"})
        assert any(x.kind == "direction_mismatch" for x in res.findings)


class TestAdditiveClaim:
    """Phase 17 T1/T2: a THIRD error class, methodological rather than
    arithmetic -- a 'combined Npp' sentence about a KPI declared
    additive_across_dimensions=false is invalid regardless of whether the
    cited numbers actually add up (that's check_stated_sums's job)."""

    def _kpi(self, **overrides):
        from src.registry.models.kpi import KPI
        base = dict(
            id="gross_margin_pct", client_id="lubricants", name="Gross Margin %",
            domain="Finance", data_product_id="dp_lubricants_financials",
            additive_across_dimensions=False,
        )
        base.update(overrides)
        return KPI(**base)

    def test_flags_a_combined_sentence_even_when_arithmetic_is_correct(self):
        """The real gap check_stated_sums cannot close: 43.24+16.76+15.18
        really does equal 75.18 here (unlike the REAL_COMPLICATION fixture
        above, which is also wrong arithmetically) -- so check_stated_sums
        alone would pass this sentence, yet summing gross_margin_pct's
        segments is still invalid on principle."""
        from src.analysis.narrative_claims import check_additive_claim, check_stated_sums
        text = ("Three segments are collectively dragging margin down by 75.18pp "
                "of combined drag (43.24pp + 16.76pp + 15.18pp).")
        assert check_stated_sums(text, "f") == []  # arithmetic checks out
        findings = check_additive_claim(text, "f", self._kpi())
        assert findings, "must flag even though the arithmetic is self-consistent"
        assert findings[0].kind == "non_additive_summation"

    def test_no_op_when_kpi_is_none(self):
        from src.analysis.narrative_claims import check_additive_claim
        text = "Segments are collectively dragging margin down by 75.18pp of combined drag."
        assert check_additive_claim(text, "f", None) == []

    def test_no_op_when_additivity_undeclared(self):
        """None (not yet declared) must never be treated as either additive or not."""
        from src.analysis.narrative_claims import check_additive_claim
        kpi = self._kpi(additive_across_dimensions=None)
        text = "Segments are collectively dragging margin down by 75.18pp of combined drag."
        assert check_additive_claim(text, "f", kpi) == []

    def test_no_op_when_kpi_is_declared_additive(self):
        """e.g. net_revenue -- summing segment dollars IS valid."""
        from src.analysis.narrative_claims import check_additive_claim
        kpi = self._kpi(id="net_revenue", additive_across_dimensions=True)
        text = "Three regions collectively contributed $75.18M of combined revenue."
        assert check_additive_claim(text, "f", kpi) == []

    def test_no_sum_cue_present_yields_no_finding(self):
        from src.analysis.narrative_claims import check_additive_claim
        text = "Gross Margin % declined 6.10 points year over year."
        assert check_additive_claim(text, "f", self._kpi()) == []

    def test_runs_inside_check_narrative_with_kpi_param(self):
        from src.analysis.narrative_claims import check_narrative
        res = check_narrative(
            {"f": "Segments are collectively dragging margin down by 75.18pp of combined drag."},
            kpi=self._kpi(),
        )
        assert any(x.kind == "non_additive_summation" for x in res.findings)

    def test_check_narrative_default_kpi_none_is_backward_compatible(self):
        """Every existing call site (kpi not yet threaded through) must see
        zero behavior change -- kpi defaults to None."""
        from src.analysis.narrative_claims import check_narrative
        res = check_narrative({"f": "Segments are collectively dragging margin down by 75.18pp of combined drag."})
        assert not any(x.kind == "non_additive_summation" for x in res.findings)
