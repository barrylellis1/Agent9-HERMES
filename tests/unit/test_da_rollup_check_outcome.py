"""_rollup_check_outcome() -- the three-way decision behind
reliability.rollup_check (docs/architecture/audit_event_system_design.md).

Extracted 2026-10-02 after a live run showed the original fail-only design's
blind spot: a KPI whose ratio bridge never engages for ANY dimension
(confirmed live as "bridge=0/0" in [FINAL] log output) produced the exact
same silence in audit_events as a KPI that ran and reconciled perfectly --
both were simply absent. These tests pin the three outcomes apart, matching
test_decomposition_analysis.py's TestTreeReconciliationIsComputable
convention for the sibling "is this even computable" question elsewhere in
the reliability panel.
"""
from __future__ import annotations

from src.agents.new.a9_deep_analysis_agent import _rollup_check_outcome


def test_no_warehouse_total_is_abstain():
    outcome, sum_c = _rollup_check_outcome(None, [10.0, 5.0])
    assert outcome == "abstain"
    assert sum_c is None


def test_no_contributions_is_abstain_not_pass():
    """The live incident this function exists to fix: bridge=0/0 means the
    ratio bridge never engaged for this KPI -- contributions is empty even
    though a warehouse delta exists. Must not read as "reconciled"."""
    outcome, sum_c = _rollup_check_outcome(-3.97, [])
    assert outcome == "abstain"
    assert sum_c is None


def test_reconciling_contributions_is_pass():
    outcome, sum_c = _rollup_check_outcome(-5.0, [-2.0, -2.9])
    assert outcome == "pass"
    assert sum_c == -4.9


def test_overshooting_contributions_is_fail():
    # Members are top-N (a subset), so only overshoot is checkable --
    # the live incident this check exists for: -53pp summed against a
    # true -5pp enterprise move.
    outcome, sum_c = _rollup_check_outcome(-5.0, [-30.0, -23.0])
    assert outcome == "fail"
    assert sum_c == -53.0


def test_exactly_at_tolerance_boundary_passes():
    # tolerance=1.15, floor=0.01 -> allowed = |delta|*1.15 + 0.01
    # delta=-5.0 -> allowed = 5.75 + 0.01 = 5.76; sum exactly at the edge passes
    outcome, _ = _rollup_check_outcome(-5.0, [-5.76])
    assert outcome == "pass"


def test_just_past_tolerance_boundary_fails():
    outcome, _ = _rollup_check_outcome(-5.0, [-5.77])
    assert outcome == "fail"


def test_undershoot_is_pass_not_fail():
    """Members are top-N, so the sum is a SUBSET of the whole by design --
    undershooting is expected and must never be flagged."""
    outcome, sum_c = _rollup_check_outcome(-10.0, [-1.0])
    assert outcome == "pass"
    assert sum_c == -1.0
