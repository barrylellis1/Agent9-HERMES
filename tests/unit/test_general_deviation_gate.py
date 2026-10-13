"""The scope rule is checked, not only requested (src/analysis/general_deviation_gate.py).

Figures are the live lubricants Net Revenue case of 2026-10-13: every segment 16.3%
below plan, and three runs that sized options three different ways.
"""
from __future__ import annotations

from src.agents.new.a9_solution_finder_agent import (
    _GENERAL_DEVIATION_RULE,
    _da_change_points,
    _parse_impact_estimate,
)
from src.analysis.general_deviation_gate import (
    IMPACT_EXCEEDS_SEGMENT_GAP,
    SCOPE_NOT_STATED,
    SEGMENT_NOT_RECOGNISED,
    SEGMENT_WITHOUT_REASON,
    check_impact_scope,
    explain,
    segment_gap,
)

CPS = [
    {"dimension": "customer_region", "key": "North America", "delta": -5735814.94},
    {"dimension": "customer_segment", "key": "Retail Partners", "delta": -3278660.75},
    {"dimension": "profit_center_name", "key": "Retail Products Division", "delta": -3278660.75},
    {"dimension": "product_line", "key": "Engine Oils", "delta": -2740000.0},
    {"dimension": "product_name", "key": "Synthetic Blend Engine Oil", "delta": -892525.0},
    {"dimension": "product_name", "key": "Conventional Engine Oil", "delta": -717256.0},
]


def _ie(**kw):
    base = {"metric": "Net Revenue", "unit": "$", "recovery_range": {"low": 100000.0, "high": 500000.0}}
    base.update(kw)
    return base


class TestSegmentGap:
    def test_one_named_member(self):
        assert segment_gap("Retail Partners pilot cohort", CPS) == 3278660.75

    def test_members_of_one_dimension_are_added(self):
        assert segment_gap("Synthetic Blend Engine Oil and Conventional Engine Oil", CPS) == 892525.0 + 717256.0

    def test_across_dimensions_the_largest_is_taken_not_the_sum(self):
        # the same dollars under two dimensions
        assert segment_gap("Retail Partners customer segment / Retail Products Division", CPS) == 3278660.75

    def test_a_label_naming_nothing_measured_is_none(self):
        assert segment_gap("Top four largest-declining SKUs", CPS) is None
        assert segment_gap(None, CPS) is None and segment_gap("Retail Partners", []) is None

    def test_a_member_name_matches_as_whole_words_only(self):
        cps = [{"dimension": "tier", "key": "Value", "delta": -100.0}]
        assert segment_gap("Value tier pilot", cps) == 100.0
        assert segment_gap("Value-based pricing", cps) == 100.0      # still a whole word
        assert segment_gap("Revalued accounts", cps) is None


class TestCheck:
    def test_an_enterprise_figure_passes(self):
        assert check_impact_scope(_ie(scope="enterprise", scope_label=None), CPS) == []

    def test_an_unstated_scope_is_a_finding(self):
        assert check_impact_scope(_ie(), CPS) == [SCOPE_NOT_STATED]
        assert check_impact_scope(_ie(scope="regional"), CPS) == [SCOPE_NOT_STATED]

    def test_a_declared_pilot_within_its_segment_passes(self):
        ie = _ie(scope="segment", scope_label="Retail Partners", scope_reason="pilot",
                 recovery_range={"low": 655000.0, "high": 1150000.0})
        assert check_impact_scope(ie, CPS) == []

    def test_a_segment_figure_with_no_reason_is_a_finding(self):
        ie = _ie(scope="segment", scope_label="Retail Partners")
        assert check_impact_scope(ie, CPS) == [SEGMENT_WITHOUT_REASON]
        assert check_impact_scope({**ie, "scope_reason": "root_cause"}, CPS) == [SEGMENT_WITHOUT_REASON]

    def test_more_than_the_segments_own_gap_is_a_finding(self):
        ie = _ie(scope="segment", scope_label="Engine Oils", scope_reason="largest_exposure",
                 recovery_range={"low": 1400000.0, "high": 2900000.0})
        assert check_impact_scope(ie, CPS) == [IMPACT_EXCEEDS_SEGMENT_GAP]

    def test_a_segment_the_analysis_did_not_measure_cannot_be_checked(self):
        ie = _ie(scope="segment", scope_label="Top four largest-declining SKUs", scope_reason="largest_exposure")
        assert check_impact_scope(ie, CPS) == [SEGMENT_NOT_RECOGNISED]

    def test_an_option_with_no_estimate_makes_no_sized_claim(self):
        assert check_impact_scope(None, CPS) == []

    def test_every_finding_has_a_plain_explanation(self):
        codes = [SCOPE_NOT_STATED, SEGMENT_WITHOUT_REASON, SEGMENT_NOT_RECOGNISED, IMPACT_EXCEEDS_SEGMENT_GAP]
        assert len(explain(codes)) == 4 and all(" " in e for e in explain(codes))


class TestSolutionFinderWiring:
    def test_the_rule_asks_for_the_reason_as_data(self):
        assert '"scope_reason": "pilot" or "largest_exposure"' in _GENERAL_DEVIATION_RULE

    def test_the_parser_keeps_a_valid_reason_and_drops_any_other(self):
        assert _parse_impact_estimate(_ie(scope="segment", scope_label="X", scope_reason="pilot")).scope_reason == "pilot"
        assert _parse_impact_estimate(_ie(scope="segment", scope_label="X", scope_reason="cause")).scope_reason is None
        assert _parse_impact_estimate(_ie(scope="enterprise")).scope_findings == []

    def test_change_points_are_found_in_either_payload_shape(self):
        assert _da_change_points({"execution": {"change_points": CPS}}) == CPS
        assert _da_change_points({"change_points": CPS}) == CPS
        assert _da_change_points({}) == [] and _da_change_points("text") == []

    def test_the_is_is_not_rows_are_read_too_once_each(self):
        # live: change_points held 5 rows and no products; where_is held all 60 members
        payload = {"execution": {
            "change_points": CPS[:2],
            "kt_is_is_not": {"where_is": [CPS[1], {"dimension": "product_name", "key": "Automatic Transmission Fluid",
                                                    "delta": -720069.23}]},
        }}
        rows = _da_change_points(payload)
        assert [r["key"] for r in rows] == ["North America", "Retail Partners", "Automatic Transmission Fluid"]
        ie = _ie(scope="segment", scope_label="Automatic Transmission Fluid", scope_reason="pilot",
                 recovery_range={"low": 300000.0, "high": 750000.0})
        assert check_impact_scope(ie, rows) == [IMPACT_EXCEEDS_SEGMENT_GAP]
        assert check_impact_scope({**ie, "recovery_range": {"low": 1.0, "high": 700000.0}}, rows) == []
