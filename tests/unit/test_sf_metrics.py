"""
Deterministic SF measurement instruments (2026-08-06).

Covers `src/analysis/`: mechanism fingerprinting, groundedness scoring, and
problem-type classification. Every function under test is pure — no LLM, no
network, no database — which is the whole design commitment: a stochastic ruler
cannot measure a stochastic process.

Several tests below are REGRESSION tests for real misclassifications found in
Phase 0 by running the first taxonomy against 13 live SF payloads. They are
marked as such; the strings in them are verbatim from real runs.
"""
from __future__ import annotations

import pytest

from src.analysis.groundedness import (
    PLAUSIBILITY_CEILING,
    DAFacts,
    extract_da_facts,
    score_option,
)
from src.analysis.mechanism import (
    MechanismFingerprint,
    classify_lever,
    fingerprint,
    lever_set,
    modal_share,
    normalize_causal_edge,
)
from src.analysis.problem_profile import classify, profiles_differ


# ---------------------------------------------------------------------------
# Mechanism taxonomy
# ---------------------------------------------------------------------------

class TestLeverTaxonomy:
    """The families were derived from real payloads, not invented — see module docstring."""

    @pytest.mark.parametrize("title,expected", [
        ("Base Oil Cost-Indexing Clause via Accelerated Contract Renewal", "indexation"),
        ("Trigger-Based Base Oil Indexation Clause in Chain A Contract Renewal", "indexation"),
        ("Volume-for-Margin Contract Reset with Walk-Away Economics Assessment", "volume_for_margin"),
        ("Full-Potential Account Economics Reset: Volume-for-Margin Portfolio Realignment", "volume_for_margin"),
        ("Renegotiate Synthetic Blend Pricing Corridor and Trigger COGS Pass-Through", "pricing_corridor"),
        ("Systematize Anchor-Account Renewal Governance and Margin Controls", "governance"),
        ("Enterprise Margin Intelligence Platform with Portfolio-Wide Repricing", "platform"),
        ("Service Centers Cost-to-Serve Audit + Pre-Negotiated Pricing Corridor", "cost_audit"),
    ])
    def test_real_titles_classify_to_expected_family(self, title, expected):
        primary, _ = classify_lever(title)
        assert primary == expected

    # --- REGRESSION: the three Phase 0 misclassifications -------------------
    # First taxonomy matched title+description together and resolved by fixed
    # priority. Long descriptions mention every lever in passing, so incidental
    # prose outvoted each option's actual thesis. Fix: match the TITLE, earliest
    # mention wins. These three cases are why.

    def test_regression_platform_title_not_overridden_by_index_in_description(self):
        primary, _ = classify_lever(
            "Enterprise Margin Intelligence Platform with Portfolio-Wide Repricing",
            "Deploys indexed contracting across anchor accounts with automated margin feeds "
            "and a quarterly cost-index reset tied to base oil benchmarks.",
        )
        assert primary == "platform", "description mentioning 'indexed' must not outvote a platform title"

    def test_regression_governance_title_not_overridden_by_automation_in_description(self):
        primary, _ = classify_lever(
            "Systematize Anchor-Account Renewal Governance and Margin Controls",
            "Introduces automated margin monitoring and an ERP-backed renewal calendar.",
        )
        assert primary == "governance", "description mentioning automation must not outvote a governance title"

    def test_regression_no_index_in_title_means_not_indexation(self):
        primary, _ = classify_lever(
            "Renegotiate Synthetic Blend Pricing Corridor Within Current Price-Lock Boundaries",
            "Sets a COGS-indexed quarterly corridor once the lock expires.",
        )
        assert primary == "pricing_corridor", "the word 'index' never appears in this title"

    # --- Compound titles: position decides, and it must separate these two ---

    def test_compound_titles_separated_by_leading_lever(self):
        platform_led, _ = classify_lever(
            "Enterprise-Wide Margin Intelligence Platform & Indexed Contracting Across Anchor Accounts")
        index_led, _ = classify_lever(
            "Accelerate Chain A Renewal Negotiation with Indexed Pricing + Automated Margin Feed")
        assert platform_led == "platform"
        assert index_led == "indexation"
        assert platform_led != index_led, "a fixed priority order would collapse these two"

    def test_compound_option_records_supporting_levers(self):
        primary, all_levers = classify_lever(
            "Volume-for-Margin Portfolio Reset with Parallel Benchmark Replication")
        assert primary == "volume_for_margin"
        assert all_levers[0] == "volume_for_margin", "primary must lead the list"
        assert "replication" in all_levers

    def test_description_used_only_when_title_names_no_lever(self):
        primary, _ = classify_lever("Project Meridian", "Introduces a base oil indexation clause at renewal.")
        assert primary == "indexation"

    def test_heuristic_stub_titles_detected(self):
        # Hardcoded fallback titles in the agent — exact match, not fuzzy.
        assert classify_lever("Tighten spend controls")[0] == "stub"
        assert classify_lever("Optimize pricing")[0] == "stub"

    def test_empty_input_is_unclassified_not_a_guess(self):
        assert classify_lever(None, None)[0] == "unclassified"
        assert classify_lever("", "")[0] == "unclassified"


class TestCausalEdgeNormalization:
    def test_direction_of_phrasing_does_not_create_false_difference(self):
        a = normalize_causal_edge("gross_margin_pct <-> cogs (confirmed, correlational, ~1 month lag)")
        b = normalize_causal_edge("cogs -> gross_margin_pct (base oil pass-through; confirmed)")
        assert a == b == "cogs<->gross_margin_pct"

    @pytest.mark.parametrize("raw,expected", [
        ("ungrounded — rests outside the verified model", "ungrounded"),
        ("insufficient_data", "insufficient_data"),
        (None, None),
        ("no edge mentioned here at all", None),
    ])
    def test_non_edge_values(self, raw, expected):
        assert normalize_causal_edge(raw) == expected


class TestStability:
    def _fp(self, family):
        return MechanismFingerprint(lever_family=family, scope_label="chain a", causal_edge="a<->b")

    def test_modal_share_perfect_and_scattered(self):
        assert modal_share([self._fp("indexation")] * 4)[1] == 1.0
        scattered = [self._fp("indexation"), self._fp("pricing_corridor"),
                     self._fp("indexation"), self._fp("pricing_corridor")]
        assert modal_share(scattered)[1] == 0.5
        assert modal_share([])[1] == 0.0

    def test_all_levers_excluded_from_equality(self):
        """Two runs phrasing the same mechanism with different supporting levers
        must still count as the same decision — otherwise stability is measured
        at prose level, which is the mistake this whole module corrects."""
        a = MechanismFingerprint("indexation", "chain a", "x<->y", all_levers=("indexation", "replication"))
        b = MechanismFingerprint("indexation", "chain a", "x<->y", all_levers=("indexation", "cost_audit"))
        assert a == b
        assert modal_share([a, b])[1] == 1.0

    def test_lever_set_reports_option_space(self):
        fps = [self._fp("indexation"), self._fp("volume_for_margin"), self._fp("indexation")]
        assert lever_set(fps) == {"indexation", "volume_for_margin"}


# ---------------------------------------------------------------------------
# Groundedness
# ---------------------------------------------------------------------------

# Verbatim shape from the live DA result for the Lubricants gross-margin case.
DA_RESULT = {
    "plan": {"kpi_name": "Gross Margin %", "client_id": "lubricants"},
    "execution": {
        "analysis_mode": "mixed",
        "mixed_framing": True,
        "kt_is_is_not": {
            "what_is": [{"text": "Gross Margin % is 32.55 vs last_year 34.22 (Δ -1.67, -4.9%)."}],
            "where_is_not": [],
        },
        "change_points": [
            {"dimension": "customer_name", "key": "National Auto Parts Chain A", "delta": -43.24},
            {"dimension": "product_name", "key": "Synthetic Blend Engine Oil", "delta": -16.76},
            {"dimension": "profit_center_name", "key": "Service Centers Division", "delta": -15.18},
            {"dimension": "product_name", "key": "Full Synthetic Engine Oil", "delta": -12.10},
            {"dimension": "channel_name", "key": "DIY Retail", "delta": -11.57},
        ],
    },
}

PRICE_LOCK = "Cannot raise list prices on Lubricants anchor accounts mid-quarter (contractual price-lock clause)"


def _option(**kw):
    base = {"id": "opt_1", "title": "t", "description": "d", "rationale": "r", "prerequisites": []}
    base.update(kw)
    return base


class TestDAFactExtraction:
    def test_enterprise_delta_parsed_from_narrative(self):
        facts = extract_da_facts(DA_RESULT)
        assert facts.enterprise_delta == pytest.approx(1.67)

    def test_segment_deltas_indexed_by_name(self):
        facts = extract_da_facts(DA_RESULT)
        assert facts.segment_delta_for("National Auto Parts Chain A") == pytest.approx(43.24)

    def test_partial_and_compound_labels_resolve(self):
        facts = extract_da_facts(DA_RESULT)
        assert facts.segment_delta_for("Chain A") is None or facts.segment_delta_for("Chain A") > 0
        # Compound scope: bounded by the LARGEST named segment, never their sum —
        # summing segment pp deltas is the error this module exists to flag.
        compound = facts.segment_delta_for(
            "National Auto Parts Chain A & Synthetic Blend Engine Oil")
        assert compound == pytest.approx(43.24)

    def test_unparseable_headline_degrades_to_none_not_zero(self):
        broken = {"execution": {"kt_is_is_not": {"what_is": [{"text": "no delta here"}]}}}
        assert extract_da_facts(broken).enterprise_delta is None


class TestGroundednessChecks:
    def setup_method(self):
        self.facts = extract_da_facts(DA_RESULT)

    def test_g1_scope_unstated_fails(self):
        s = score_option(_option(impact_estimate={"recovery_range": {"low": 1, "high": 2}}), self.facts)
        assert s.g1_scope_stated is False
        assert any("unstated" in r for r in s.reasons)

    def test_g2_enterprise_claim_naming_a_segment_is_contradictory(self):
        s = score_option(_option(impact_estimate={
            "scope": "enterprise", "scope_label": "National Auto Parts Chain A",
            "recovery_range": {"low": 1.0, "high": 1.5}}), self.facts)
        assert s.g2_scope_consistent is False

    def test_g3_plausible_segment_claim_passes(self):
        # 28.3pp against Chain A's observed 43.24pp move -> ratio 0.65
        s = score_option(_option(impact_estimate={
            "scope": "segment", "scope_label": "National Auto Parts Chain A",
            "recovery_range": {"low": 18.5, "high": 28.3}}), self.facts)
        assert s.g3_arithmetic_plausible is True
        assert s.impact_ratio == pytest.approx(0.65, abs=0.01)
        assert s.cross_segment_summation is False

    def test_g3_catches_the_live_enterprise_summation_case(self):
        """REGRESSION — the exact option the moderator graded arithmetic=pass.

        "Structural Margin Governance & Best-Practice Replication Program",
        26-47pp, scope=enterprise, on a KPI whose enterprise move was -1.67pp.
        Built by summing unweighted segment deltas (43.24+16.76+15.18=75.18)
        across segments with different revenue weights.
        """
        s = score_option(_option(impact_estimate={
            "scope": "enterprise", "scope_label": None,
            "recovery_range": {"low": 26.0, "high": 47.0}}), self.facts)
        assert s.g3_arithmetic_plausible is False
        assert s.impact_ratio == pytest.approx(28.14, abs=0.05)
        assert s.cross_segment_summation is True, "must name the summation methodology explicitly"
        assert any("unweighted segment deltas" in r for r in s.reasons)

    def test_g3_ceiling_allows_full_recovery_plus_headroom(self):
        facts = DAFacts(enterprise_delta=10.0)
        at_ceiling = score_option(_option(impact_estimate={
            "scope": "enterprise", "recovery_range": {"high": 10.0 * PLAUSIBILITY_CEILING}}), facts)
        beyond = score_option(_option(impact_estimate={
            "scope": "enterprise", "recovery_range": {"high": 10.0 * PLAUSIBILITY_CEILING + 0.1}}), facts)
        assert at_ceiling.g3_arithmetic_plausible is True
        assert beyond.g3_arithmetic_plausible is False

    def test_g4_known_and_unknown_edges(self):
        opt = _option(impact_estimate={"scope": "segment", "scope_label": "x"})
        known = score_option(opt, self.facts, moderator_grade={"causal_grounding": "cogs -> gross_margin_pct"},
                             known_causal_edges={"cogs<->gross_margin_pct"})
        unknown = score_option(opt, self.facts, moderator_grade={"causal_grounding": "foo -> bar"},
                               known_causal_edges={"cogs<->gross_margin_pct"})
        ungrounded = score_option(opt, self.facts, moderator_grade={"causal_grounding": "ungrounded"},
                                  known_causal_edges={"cogs<->gross_margin_pct"})
        assert known.g4_causal_edge_known is True
        assert unknown.g4_causal_edge_known is False
        assert ungrounded.g4_causal_edge_known is False

    def test_g5_addressed_vs_unaddressed_constraint(self):
        addressed = score_option(_option(
            description="Defers all repricing on anchor accounts until the contractual "
                        "price-lock clause expires at renewal; no mid-quarter list price change."),
            self.facts, active_constraints=[PRICE_LOCK])
        silent = score_option(_option(description="Rebalance product mix toward higher margin SKUs."),
                              self.facts, active_constraints=[PRICE_LOCK])
        assert addressed.g5_constraints_addressed is True
        assert silent.g5_constraints_addressed is False

    def test_g6_stub_run(self):
        s = score_option(_option(), self.facts, is_stub_run=True)
        assert s.g6_not_stub is False


class TestNotCheckedIsNotPass:
    """The central discipline: a check that could not run must never look like a pass."""

    def test_unsupplied_inputs_yield_none_and_are_excluded_from_score(self):
        s = score_option(_option(impact_estimate={
            "scope": "segment", "scope_label": "National Auto Parts Chain A",
            "recovery_range": {"high": 10.0}}), extract_da_facts(DA_RESULT))
        assert s.g4_causal_edge_known is None   # no registry supplied
        assert s.g5_constraints_addressed is None
        assert s.g6_not_stub is None
        assert s.checked == 3, "only the three checkable items count toward the denominator"
        assert s.score == 1.0

    def test_missing_da_baseline_does_not_silently_pass_arithmetic(self):
        s = score_option(_option(impact_estimate={
            "scope": "enterprise", "recovery_range": {"high": 999.0}}), DAFacts())
        assert s.g3_arithmetic_plausible is None, "no baseline means not-checked, never pass"


# ---------------------------------------------------------------------------
# Problem profile
# ---------------------------------------------------------------------------

class TestProblemProfile:
    def test_live_lubricants_case(self):
        p = classify(DA_RESULT)
        assert p.mode == "mixed"
        assert p.mixed_framing is True
        assert p.concentration == "concentrated"
        assert p.dominance_ratio == pytest.approx(2.58, abs=0.01)  # 43.24 / 16.76
        assert p.has_control_group is False                        # empty IS-NOT set
        assert p.cell_key() == "mixed/concentrated/no-control/single"

    def test_distributed_when_no_segment_dominates(self):
        da = {"plan": {"kpi_name": "K"}, "execution": {"change_points": [
            {"key": "a", "delta": -10.0}, {"key": "b", "delta": -9.0}, {"key": "c", "delta": -8.5}]}}
        p = classify(da)
        assert p.concentration == "distributed"
        assert p.dominance_ratio == pytest.approx(1.11, abs=0.01)

    def test_control_group_detected_when_is_not_populated(self):
        da = {"execution": {"kt_is_is_not": {"where_is_not": [{"key": "healthy segment"}]},
                            "change_points": []}}
        assert classify(da).has_control_group is True

    def test_cross_kpi_not_checked_without_registry(self):
        assert classify(DA_RESULT).cross_kpi is None
        assert classify(DA_RESULT, kpi_has_relationships=True).cross_kpi is True

    def test_profiles_differ_identifies_structural_difference(self):
        a = classify(DA_RESULT)
        b = classify({"execution": {"analysis_mode": "opportunity",
                                    "kt_is_is_not": {"where_is_not": [{"k": 1}]},
                                    "change_points": [{"key": "x", "delta": -5.0},
                                                      {"key": "y", "delta": -4.8}]}})
        diff = profiles_differ(a, b)
        assert {"mode", "concentration", "has_control_group"} <= diff
