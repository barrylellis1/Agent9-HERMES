"""Re-seeding kpi_relationships must not erase what VA verdicts earned.

onboard_client.py deletes and re-inserts the table per client. A link marked
intervention_tested / va_validated at runtime has to survive that.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from onboard_client import _preserve_earned_link_states  # noqa: E402


def _row(a, b, **kw):
    base = {"client_id": "c1", "kpi_id": a, "related_kpi_id": b, "provenance": "confirmed"}
    base.update(kw)
    return base


TESTED = {"causal_rung": "intervention_tested", "provenance": "va_validated"}


def test_seeded_causal_link_keeps_its_earned_state():
    seed = [_row("premium_mix_pct", "gross_margin_pct", causal_rung="correlational")]
    existing = [_row("premium_mix_pct", "gross_margin_pct", **TESTED)]
    rows, carried, kept = _preserve_earned_link_states(seed, existing)
    assert rows[0]["causal_rung"] == "intervention_tested"
    assert rows[0]["provenance"] == "va_validated"
    assert carried == ["premium_mix_pct<->gross_margin_pct"]
    assert kept == []
    assert seed[0]["causal_rung"] == "correlational", "seed rows must not be mutated"


def test_untested_link_is_seeded_as_written():
    seed = [_row("units_sold", "net_revenue", causal_rung="correlational")]
    existing = [_row("units_sold", "net_revenue", causal_rung="correlational")]
    rows, carried, _ = _preserve_earned_link_states(seed, existing)
    assert rows == seed
    assert carried == []


def test_accounting_identity_never_carries_tested_state():
    seed = [_row("sales_order_count", "net_revenue", basis="accounting_identity")]
    existing = [_row("sales_order_count", "net_revenue", basis="accounting_identity", **TESTED)]
    rows, carried, kept = _preserve_earned_link_states(seed, existing)
    assert rows == seed
    assert carried == [] and kept == []


def test_earned_link_missing_from_seed_is_kept():
    existing = [_row("a", "b", **TESTED)]
    rows, carried, kept = _preserve_earned_link_states([_row("x", "y")], existing)
    assert kept == existing
    assert existing[0] in rows and len(rows) == 2
    assert carried == []


def test_match_ignores_which_side_the_seed_lists_first():
    seed = [_row("gross_margin_pct", "premium_mix_pct")]
    existing = [_row("premium_mix_pct", "gross_margin_pct", **TESTED)]
    rows, carried, kept = _preserve_earned_link_states(seed, existing)
    assert rows[0]["provenance"] == "va_validated"
    assert len(rows) == 1 and kept == []
