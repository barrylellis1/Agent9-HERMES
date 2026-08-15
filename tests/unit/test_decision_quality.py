"""
Unit tests for `src.analysis.decision_quality`.

Pure functions — no LLM, no network, no DB. Several of these codify defects the
first version of the scorer actually had, found while scoring the real corpus.
"""
from __future__ import annotations

import pytest

from src.analysis.decision_quality import (
    DEFAULT_CRITERIA_WEIGHTS,
    score_run,
)


def _opt(oid, title, description="", **kw):
    o = {"id": oid, "title": title, "description": description}
    o.update(kw)
    return o


def _run(options, **kw):
    payload = {
        "options_ranked": options,
        "audit_log": kw.pop("audit_log", []),
        "tradeoff_matrix": kw.pop("tradeoff_matrix", None),
        "decision_ask": kw.pop("decision_ask", None),
        "immediate_actions": kw.pop("immediate_actions", []),
        "next_steps": kw.pop("next_steps", []),
        "constraint_exposure": kw.pop("constraint_exposure", None),
        "moderator_grades": kw.pop("moderator_grades", {}),
    }
    payload.update(kw)
    return payload


DEFAULT_MATRIX = {"criteria": [{"name": n, "weight": w} for n, w in DEFAULT_CRITERIA_WEIGHTS]}


# --------------------------------------------------------------------------
# Link 2 — creative alternatives
# --------------------------------------------------------------------------

class TestAlternatives:
    def test_three_options_one_lever_family_is_not_three_alternatives(self):
        """The core DQ link-2 claim: same lever three times is ONE alternative."""
        s = score_run(_run([
            _opt("o1", "Indexed Pricing Clause A"),
            _opt("o2", "Base-Oil Indexation Mechanism B"),
            _opt("o3", "Trigger-Based Indexation C"),
        ]))
        assert s.l2_alternatives.passed is False
        assert s.distinct_lever_families == 1

    def test_two_distinct_families_passes(self):
        s = score_run(_run([
            _opt("o1", "Indexed Pricing Clause"),
            _opt("o2", "Pricing Corridor Renegotiation"),
        ]))
        assert s.l2_alternatives.passed is True

    def test_unclassified_options_do_not_count_as_alternatives(self):
        """REGRESSION. The first version counted `unclassified` as a lever family.

        On the real corpus that turned arm E2 — one classified family plus two
        options the taxonomy could not name — into a confident PASS. Two
        unclassified options may be one lever or two; the taxonomy does not
        cover mix-shift or hedging, so the honest answer is 'undetermined'.
        """
        # These two titles name no lever the taxonomy knows. If a future taxonomy
        # extension covers one of them this test fails LOUDLY rather than
        # silently changing meaning — which is exactly what happened when
        # `mix_shift` and `hedging` were added on 2026-08-15, and is why the
        # guard assertion below exists.
        from src.analysis.mechanism import classify_lever
        unnameable = ["Chain A Renewal Acceleration Programme",
                      "Anchor Account Escalation Pathway"]
        for t in unnameable:
            assert classify_lever(t)[0] == "unclassified", (
                f"fixture {t!r} is no longer unclassified — the taxonomy grew into it. "
                "Pick a new unnameable title; do not weaken the assertion."
            )

        s = score_run(_run([
            _opt("o1", "Pricing Corridor Reset"),
            _opt("o2", unnameable[0]),
            _opt("o3", unnameable[1]),
        ]))
        assert s.unclassified_options == 2
        assert s.l2_alternatives.passed is None, "must not guess when the taxonomy gap decides it"
        assert "UNCLASSIFIED" in s.l2_alternatives.detail

    def test_unclassified_cannot_rescue_a_single_family_run(self):
        """One classified family + zero unclassified is still a clean FAIL."""
        s = score_run(_run([
            _opt("o1", "Indexed Pricing Clause A"),
            _opt("o2", "Indexation Mechanism B"),
        ]))
        assert s.l2_alternatives.passed is False

    def test_no_options_leaves_link_unchecked(self):
        s = score_run(_run([]))
        assert s.l2_alternatives.passed is None


# --------------------------------------------------------------------------
# Link 1 — appropriate frame
# --------------------------------------------------------------------------

class TestFrame:
    def test_full_potential_rhetoric_does_not_pass_the_frame_link(self):
        """REGRESSION. `volume_for_margin` was treated as an automatic structural
        signal; its `full[-\\s]potential` pattern then matched Bain vocabulary on
        an ordinary recovery plan (real arm A). Mechanism taxonomy classifies
        MECHANISM, never FRAME.
        """
        s = score_run(_run([
            _opt("o1", "Full Potential Margin Recovery: Accelerated Renewal & Cost Reserve"),
            _opt("o2", "Indexed Pricing Clause"),
        ]))
        assert s.l1_frame.passed is False

    def test_genuine_portfolio_exit_language_fires_the_screen(self):
        s = score_run(_run([
            _opt("o1", "SKU Rationalization", "Discontinue underperforming SKUs and delist."),
            _opt("o2", "Indexed Pricing Clause"),
        ]))
        assert s.l1_frame.passed is True
        assert s.l1_frame.evidence

    def test_frame_link_is_marked_advisory(self):
        """It is a term screen for a semantic property; §5 measured a 71% FPR on
        exactly this shape of instrument. It must never present as a verdict."""
        s = score_run(_run([_opt("o1", "Indexed Pricing Clause")]))
        assert s.l1_frame.advisory is True
        assert s.l4_tradeoffs.advisory is True


# --------------------------------------------------------------------------
# Link 4 — clear values and tradeoffs
# --------------------------------------------------------------------------

class TestTradeoffs:
    def test_config_default_weight_vector_fails_the_link(self):
        """REGRESSION. A presence check passes on the agent's own config
        constant, because `request.evaluation_criteria or [defaults]` renders a
        fully-populated weighted matrix when nobody supplied any values. All 11
        real arms carry exactly this vector.
        """
        s = score_run(_run([_opt("o1", "X")], tradeoff_matrix=DEFAULT_MATRIX))
        assert s.criteria_defaulted is True
        assert s.l4_tradeoffs.passed is False
        assert "DEFAULT" in s.l4_tradeoffs.detail.upper()

    def test_principal_specific_weights_pass(self):
        matrix = {"criteria": [{"name": "impact", "weight": 0.7},
                               {"name": "risk", "weight": 0.3}]}
        s = score_run(_run([_opt("o1", "X")], tradeoff_matrix=matrix))
        assert s.criteria_defaulted is False
        assert s.l4_tradeoffs.passed is True

    def test_unweighted_criteria_fail(self):
        matrix = {"criteria": [{"name": "impact"}, {"name": "risk"}]}
        s = score_run(_run([_opt("o1", "X")], tradeoff_matrix=matrix))
        assert s.l4_tradeoffs.passed is False

    def test_absent_matrix_is_not_checked(self):
        s = score_run(_run([_opt("o1", "X")]))
        assert s.l4_tradeoffs.passed is None


# --------------------------------------------------------------------------
# Link 6 — commitment to action
# --------------------------------------------------------------------------

class TestCommitment:
    def test_requires_text_owner_and_actions(self):
        s = score_run(_run(
            [_opt("o1", "X")],
            decision_ask={"decision_text": "Approve hedge", "decision_owner": "CFO"},
            immediate_actions=[{"action_text": "do the thing"}],
        ))
        assert s.l6_commitment.passed is True

    def test_decision_ask_without_owner_fails(self):
        s = score_run(_run(
            [_opt("o1", "X")],
            decision_ask={"decision_text": "Approve hedge"},
            immediate_actions=[{"action_text": "do the thing"}],
        ))
        assert s.l6_commitment.passed is False


# --------------------------------------------------------------------------
# Chain semantics
# --------------------------------------------------------------------------

class TestChain:
    def test_not_checked_is_excluded_from_both_numerator_and_denominator(self):
        s = score_run(_run([_opt("o1", "Indexed Pricing Clause")]))
        assert s.l5_reasoning.passed is None  # no DA facts supplied
        assert s.checked == sum(1 for l in s.links() if l.passed is not None)
        assert s.passed <= s.checked

    def test_one_failed_link_caps_the_chain(self):
        s = score_run(_run([
            _opt("o1", "Indexed Pricing A"), _opt("o2", "Indexation B"),
        ]))
        assert s.l2_alternatives.passed is False
        assert s.chain_verdict is False
        assert "alternatives" in s.weakest_links

    def test_unscored_decision_is_not_a_passing_one(self):
        s = score_run(_run([]))
        if s.checked == 0:
            assert s.chain_verdict is None

    def test_stub_run_fails_information(self):
        s = score_run(_run(
            [_opt("o1", "Tighten spend controls")],
            audit_log=[{"event": "heuristic_stub_fallback"}],
        ))
        assert s.l3_information.passed is False

    def test_option_that_never_saw_a_constraint_fails_information(self):
        s = score_run(_run(
            [_opt("o1", "Indexed Pricing Clause")],
            constraint_exposure={"union_size": 2, "by_option": {
                "o1": {"constraints_seen": ["c1"], "constraints_unseen": ["c2"]}}},
        ))
        assert s.l3_information.passed is False
        assert "never saw" in s.l3_information.detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
