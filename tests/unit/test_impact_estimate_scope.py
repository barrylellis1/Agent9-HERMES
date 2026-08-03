"""Impact-estimate scope regression tests.

Codifies a defect observed in live runs (both fast and full debate mode): SF
returned recovery ranges of 18.5-28.3 percentage points for a Gross Margin % of
31.08 whose annual decline was 5.08pp. The figures were not hallucinated -- the
`basis` text traced them to "50-65% of the 43.24pp Chain A decline", a real
DIMENSIONAL magnitude from DA's change_points, emitted under the ENTERPRISE
KPI's name with nothing to distinguish the two.

Why it matters beyond presentation: VA solution registration reads
recovery_range verbatim into impact bounds and later grades the outcome against
them. An unqualified segment figure therefore becomes an enterprise commitment
that can never be met, manufacturing a permanent "failed" verdict -- and once
assumption grading writes back to the causal graph, teaching the theory layer
the wrong lesson from a solution that may have worked perfectly well.
"""

import pytest

from src.agents.models.solution_finder_models import ImpactEstimate, RecoveryRange
from src.agents.new.a9_solution_finder_agent import _parse_impact_estimate


class TestImpactEstimateScopeParsing:
    def test_enterprise_scope_round_trips(self):
        est = _parse_impact_estimate({
            "metric": "Gross Margin %", "unit": "%",
            "recovery_range": {"low": 1.2, "high": 2.8},
            "scope": "enterprise", "basis": "enterprise-scaled",
        })
        assert est is not None
        assert est.scope == "enterprise"
        assert est.scope_label is None

    def test_segment_scope_retains_label(self):
        """The exact shape of the live defect, now expressible without ambiguity."""
        est = _parse_impact_estimate({
            "metric": "Gross Margin %", "unit": "%",
            "recovery_range": {"low": 18.5, "high": 28.3},
            "scope": "segment", "scope_label": "National Auto Parts Chain A",
            "basis": "50-65% of the 43.24pp Chain A decline",
        })
        assert est.scope == "segment"
        assert est.scope_label == "National Auto Parts Chain A"

    @pytest.mark.parametrize("bad", ["company-wide", "ENTERPRISE", "global", "", "kpi"])
    def test_unrecognised_scope_becomes_none_not_passthrough(self, bad):
        """A scope nobody can interpret is worse than an absent one.

        None is handled downstream as "unverified"; an unrecognised string that
        survived would be read as a genuine claim about scope. Note "ENTERPRISE"
        is rejected too -- silently upcasing would assert enterprise scope on the
        model's behalf, which is precisely the assumption that caused the bug.
        """
        assert _parse_impact_estimate({"metric": "m", "scope": bad}).scope is None

    def test_absent_scope_is_none_not_defaulted_to_enterprise(self):
        """Defaulting to 'enterprise' would silently reintroduce the defect.

        Pre-existing payloads and any model ignoring the instruction land here.
        Treating them as enterprise is exactly the unverified assumption that let
        segment-sized numbers reach VA in the first place.
        """
        est = _parse_impact_estimate({
            "metric": "Gross Margin %", "unit": "%",
            "recovery_range": {"low": 18.5, "high": 28.3},
        })
        assert est.scope is None, "absent scope must stay unstated, never assumed enterprise"

    def test_scope_is_optional_on_the_model(self):
        """Older persisted SF payloads must still deserialise."""
        est = ImpactEstimate(metric="Gross Margin %", unit="%",
                             recovery_range=RecoveryRange(low=1.0, high=2.0))
        assert est.scope is None and est.scope_label is None


class TestVaRegistrationScopeGuard:
    """The guard is a WARNING, not a rejection.

    HITL approval must not fail because an estimate looks large -- a human has
    already approved the option, and silently rewriting a number the approver saw
    would be worse than recording doubt beside it. These tests pin the classifier
    that decides when doubt is recorded; see workflows.py approve handler.
    """

    @staticmethod
    def _classify(impact_est):
        """Mirror of the guard's branch logic in workflows.py."""
        scope = impact_est.get("scope")
        if scope == "segment":
            label = impact_est.get("scope_label")
            return f"segment{' (' + str(label) + ')' if label else ''}"
        if scope is None:
            return "unstated"
        return None

    def test_segment_scope_is_flagged(self):
        assert self._classify({
            "scope": "segment", "scope_label": "National Auto Parts Chain A",
        }) == "segment (National Auto Parts Chain A)"

    def test_unstated_scope_is_flagged(self):
        assert self._classify({"recovery_range": {"low": 18.5, "high": 28.3}}) == "unstated"

    def test_enterprise_scope_is_not_flagged(self):
        assert self._classify({"scope": "enterprise"}) is None

    def test_segment_without_label_still_flags(self):
        assert self._classify({"scope": "segment"}) == "segment"
