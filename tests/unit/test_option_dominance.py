"""Tests for src.analysis.option_dominance — the deterministic Pareto-dominance
flag for Solution Finder options.

Real case found live 2026-08-24: opt_1 and opt_2 were both modelled at an
identical $3.8M-$5.2M recovery range, but opt_2 took 12+ months (vs opt_1's
0-90 days), cost more (0.60 vs 0.45), and carried more risk (0.55 vs 0.40).
"""
from src.agents.models.solution_finder_models import (
    SolutionOption, ImpactEstimate, RecoveryRange,
)
from src.analysis.option_dominance import (
    find_dominated_options, apply_dominance_flags, as_audit_event,
)


def _opt(id_, low, high, cost, risk, scope="segment", scope_label="Base Oil & Additives"):
    return SolutionOption(
        id=id_,
        title=f"Option {id_}",
        cost=cost,
        risk=risk,
        impact_estimate=ImpactEstimate(
            metric="ebitda", unit="$",
            recovery_range=RecoveryRange(low=low, high=high),
            scope=scope, scope_label=scope_label,
        ),
    )


class TestFindDominatedOptions:
    def test_the_real_live_case(self):
        """opt_1 dominates opt_2: same recovery range, lower cost, lower risk."""
        opt_1 = _opt("opt_1", 3_800_000, 5_200_000, cost=0.45, risk=0.40)
        opt_2 = _opt("opt_2", 3_800_000, 5_200_000, cost=0.60, risk=0.55)
        # A genuine trade-off, not dominated by opt_1: lower floor but a
        # higher ceiling (3.0M vs opt_1's 3.8M floor, 6.5M vs opt_1's 5.2M
        # ceiling) — neither option's recovery range contains the other's.
        opt_3 = _opt("opt_3", 3_000_000, 6_500_000, cost=0.65, risk=0.60)

        findings = find_dominated_options([opt_1, opt_2, opt_3])
        dominated_ids = {f["dominated_id"] for f in findings}
        assert dominated_ids == {"opt_2"}
        assert findings[0]["dominated_by_id"] == "opt_1"

    def test_genuinely_distinct_options_are_not_flagged(self):
        """Higher impact but higher cost/risk too — a real trade-off, not dominance."""
        opt_1 = _opt("opt_1", 3_800_000, 5_200_000, cost=0.45, risk=0.40)
        opt_2 = _opt("opt_2", 4_500_000, 6_000_000, cost=0.60, risk=0.55)
        assert find_dominated_options([opt_1, opt_2]) == []

    def test_identical_options_are_not_flagged_as_dominated(self):
        """Equal on every axis — dominance requires STRICTLY better somewhere."""
        opt_1 = _opt("opt_1", 3_800_000, 5_200_000, cost=0.45, risk=0.40)
        opt_2 = _opt("opt_2", 3_800_000, 5_200_000, cost=0.45, risk=0.40)
        assert find_dominated_options([opt_1, opt_2]) == []

    def test_never_compares_across_different_scope(self):
        """A segment-scoped and an enterprise-scoped range are different units —
        must never be treated as comparable, matching ImpactEstimate's own
        scope-safety discipline."""
        segment = _opt("opt_1", 1_000_000, 2_000_000, cost=0.3, risk=0.3,
                        scope="segment", scope_label="Base Oil & Additives")
        enterprise = _opt("opt_2", 5_000_000, 8_000_000, cost=0.9, risk=0.9,
                           scope="enterprise", scope_label=None)
        assert find_dominated_options([segment, enterprise]) == []

    def test_missing_impact_estimate_skips_gracefully(self):
        bare = SolutionOption(id="opt_1", title="No estimate", cost=0.3, risk=0.3)
        full = _opt("opt_2", 3_800_000, 5_200_000, cost=0.45, risk=0.40)
        assert find_dominated_options([bare, full]) == []

    def test_unstated_scope_is_never_compared(self):
        """scope=None means unverified, per ImpactEstimate's docstring — must
        not be silently treated as comparable to anything, including itself."""
        a = _opt("opt_1", 3_800_000, 5_200_000, cost=0.45, risk=0.40, scope=None)
        b = _opt("opt_2", 3_800_000, 5_200_000, cost=0.60, risk=0.55, scope=None)
        assert find_dominated_options([a, b]) == []


class TestApplyDominanceFlags:
    def test_mutates_dominated_by_in_place(self):
        opt_1 = _opt("opt_1", 3_800_000, 5_200_000, cost=0.45, risk=0.40)
        opt_2 = _opt("opt_2", 3_800_000, 5_200_000, cost=0.60, risk=0.55)
        assert opt_2.dominated_by is None

        apply_dominance_flags([opt_1, opt_2])

        assert opt_2.dominated_by == "opt_1"
        assert opt_1.dominated_by is None  # opt_1 is not dominated by anything

    def test_clean_run_leaves_flags_none(self):
        opt_1 = _opt("opt_1", 3_800_000, 5_200_000, cost=0.45, risk=0.40)
        opt_2 = _opt("opt_2", 4_500_000, 6_000_000, cost=0.60, risk=0.55)
        apply_dominance_flags([opt_1, opt_2])
        assert opt_1.dominated_by is None
        assert opt_2.dominated_by is None


class TestAsAuditEvent:
    def test_absent_when_clean(self):
        assert as_audit_event([]) is None

    def test_present_when_findings_exist(self):
        findings = [{"dominated_id": "opt_2", "dominated_by_id": "opt_1", "reason": "..."}]
        event = as_audit_event(findings)
        assert event["event"] == "dominated_option"
        assert event["findings"] == findings
