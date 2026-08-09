"""Slice-validity probe — the verdict logic, pinned against the real bad dataset.

WHY THIS FILE EXISTS
--------------------
On 2026-08-09 the Lubricants demo dataset was found to attribute ALL COGS to a
single customer while revenue spanned twenty. Gross margin by customer therefore
read -457% for that account and exactly 100.00% for the other nineteen. Every
layer above behaved correctly on top of it — a breach was raised, a
"concentration" was found, three consulting personas diagnosed a base-oil
pass-through, and the briefing recommended renegotiating a contract to correct
an ETL defect.

Nothing in the system could catch it: every check we had verifies arithmetic
INSIDE the pipeline (does the prose match the measured number, does an impact
claim match the observed delta). None asked whether the slice itself was
meaningful. The enterprise figure was correct throughout, which is exactly why
it survived — the error only appears once you slice.

The dataset has since been corrected, so the bug is no longer reproducible from
live data. `tests/fixtures/lubricants_uneven_granularity_profile.json` is the
frozen pre-fix profile, captured from BigQuery before the overwrite precisely so
this case is not lost.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.check_slice_validity import (
    DEGRADED_BELOW,
    INVALID_BELOW,
    assess,
)

FIXTURE = (Path(__file__).resolve().parents[1]
           / "fixtures" / "lubricants_uneven_granularity_profile.json")


@pytest.fixture(scope="module")
def pre_fix_profile() -> dict:
    with FIXTURE.open(encoding="utf-8") as f:
        return json.load(f)


class TestTheRealDatasetThatFooledEveryOtherCheck:
    """Drives `assess` with the actual counts observed in BigQuery."""

    @pytest.mark.parametrize("dimension", ["customer_name", "channel_name", "customer_segment"])
    def test_collapsed_dimensions_are_invalid(self, pre_fix_profile, dimension):
        cov = pre_fix_profile["dimension_coverage"][dimension]
        assert cov["cogs"] == 1, "fixture drift — this dimension was collapsed to one value"
        assert assess({"Revenue": cov["revenue"], "COGS": cov["cogs"]}) == "INVALID"

    @pytest.mark.parametrize("dimension", ["product_name", "product_line", "profit_center_name"])
    def test_partially_attributed_dimensions_are_not_silently_ok(self, pre_fix_profile, dimension):
        """COGS reached some but not all values here.

        The point is that these must not pass as clean. Whether they read
        degraded or INVALID depends on the threshold; being 'ok' would be wrong.
        """
        cov = pre_fix_profile["dimension_coverage"][dimension]
        assert assess({"Revenue": cov["revenue"], "COGS": cov["cogs"]}) in {"degraded", "INVALID"}

    def test_nineteen_customers_at_exactly_100_percent(self, pre_fix_profile):
        """The tell a human would have spotted, preserved as a fact.

        Nineteen accounts at *exactly* 100.00% is arithmetically impossible in a
        real business and is what a CFO would notice in seconds.
        """
        margins = pre_fix_profile["gross_margin_pct_by_customer"]
        assert sum(1 for v in margins.values() if v == 100.0) == 19
        assert min(margins.values()) < -400, "the single cost-bearing account"


class TestVerdictBoundaries:
    def test_full_coverage_is_ok(self):
        assert assess({"Revenue": 20, "COGS": 20}) == "ok"

    def test_one_missing_value_is_degraded_not_ok(self):
        # 19/20 = 95%. A near-miss must not read clean — partial attribution is
        # the case most likely to be believed.
        assert assess({"Revenue": 20, "COGS": 19}) == "degraded"

    def test_single_value_against_many_is_invalid(self):
        assert assess({"Revenue": 20, "COGS": 1}) == "INVALID"

    def test_component_entirely_absent_is_invalid_not_unknown(self):
        # Zero rows for a component is the most broken case, not the least.
        assert assess({"Revenue": 20, "COGS": 0}) == "INVALID"

    def test_no_data_at_all_is_unknown_never_ok(self):
        """not-checked is never pass — the discipline the rest of Phase 15 uses."""
        assert assess({}) == "unknown"
        assert assess({"Revenue": 0, "COGS": 0}) == "unknown"

    def test_more_than_two_components_uses_the_weakest(self):
        assert assess({"Revenue": 20, "COGS": 20, "Freight": 1}) == "INVALID"

    def test_thresholds_are_ordered(self):
        assert 0 < INVALID_BELOW < DEGRADED_BELOW <= 1.0
