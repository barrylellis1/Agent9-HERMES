"""KT driver deltas render in the KPI's own unit (Aug 2026).

THE DEFECT
----------
`_build_kt_summary` hardcoded a `$` and `:,.0f` into the WHERE-IS block:

    driver_strs.append(f"- {key}: ${delta:,.0f} ({pct:.1f}% of variance)")

On lubricants `gross_margin_pct` that produced, in the context EVERY Solution
Finder persona reads:

    - Synthetic Blend Engine Oil: $-7 (0.0% of variance)
    - Conventional Engine Oil: $-7 (0.0% of variance)

Three separate faults in one line:

1. **Wrong unit.** Percentage points presented as dollars.
2. **Lost precision.** -7.14 and -6.61 both collapse to `$-7`, destroying the
   ranking the block exists to convey.
3. **A false zero.** `percent_of_total` is absent from every entry on the flat
   dimension path, so `.get(key, 0)` defaulted it and asserted that each top
   driver explains 0.0% of the variance.

Fault 3 is the worst: it is not a formatting error but a false statement of
fact, delivered to three personas as evidence.
"""

import pytest

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent as DA


# ---------------------------------------------------------------------------
# Unit rendering
# ---------------------------------------------------------------------------


def test_percentage_kpi_renders_as_points_not_dollars():
    """The regression. A margin delta is percentage POINTS."""
    out = DA._format_kt_delta(-7.14, "%")

    assert "$" not in out
    assert out == "-7.14pp"


def test_currency_kpi_still_renders_as_currency():
    assert DA._format_kt_delta(1234567.0, "$") == "$1,234,567"
    assert DA._format_kt_delta(-4200.0, "$") == "-$4,200"


def test_precision_keeps_distinct_drivers_distinct():
    """-7.14 and -6.61 both printed as `$-7` and became indistinguishable."""
    assert DA._format_kt_delta(-7.14, "%") != DA._format_kt_delta(-6.61, "%")


def test_unknown_unit_does_not_invent_one():
    """Guessing a unit is what caused the defect. Stay neutral instead."""
    out = DA._format_kt_delta(-7.14, None)

    assert "$" not in out
    assert "pp" not in out
    assert "-7.14" in out


def test_malformed_delta_does_not_crash_the_context_block():
    assert DA._format_kt_delta(None, "%") == "n/a"
    assert DA._format_kt_delta("not a number", "$") == "n/a"


def test_sign_is_preserved_for_gains():
    assert DA._format_kt_delta(3.2, "%") == "+3.20pp"


# ---------------------------------------------------------------------------
# The false zero
# ---------------------------------------------------------------------------


class _StubKPI:
    def __init__(self, unit):
        self.unit = unit


class _DAStub(DA):
    """Only the tenant-scoped KPI lookup is stubbed; formatting is the real code."""

    def __init__(self, unit="%"):
        self._unit = unit

    def _lookup_kpi_scoped(self, kpi_ref, client_id):
        return _StubKPI(self._unit)


def _da_output(where_is):
    return {
        "plan": {"kpi_name": "gross_margin_pct", "client_id": "lubricants"},
        "execution": {"kt_is_is_not": {"where_is": where_is}},
    }


def test_absent_percent_of_total_is_omitted_not_asserted_as_zero():
    """`percent_of_total` is missing on the flat path; do not print 0.0%."""
    out = _DAStub()._build_kt_summary(
        _da_output([{"key": "Synthetic Blend Engine Oil", "delta": -7.14}])
    )

    assert "0.0% of variance" not in out
    assert "of variance" not in out
    assert "-7.14pp" in out


def test_real_percent_of_total_is_still_reported():
    out = _DAStub()._build_kt_summary(
        _da_output([{"key": "Synthetic Blend", "delta": -7.14, "percent_of_total": 41.3}])
    )

    assert "(41.3% of variance)" in out


def test_zero_is_reported_when_genuinely_measured():
    """A real measured 0.0 must survive — the fix drops ABSENT, not zero."""
    out = _DAStub()._build_kt_summary(
        _da_output([{"key": "Flat Segment", "delta": 0.0, "percent_of_total": 0.0}])
    )

    assert "(0.0% of variance)" in out


def test_the_full_block_no_longer_contains_a_currency_symbol():
    """End-to-end on the shape that produced the reported output."""
    out = _DAStub()._build_kt_summary(
        _da_output([
            {"key": "Synthetic Blend Engine Oil", "delta": -7.14},
            {"key": "Conventional Engine Oil", "delta": -6.61},
        ])
    )

    assert "$" not in out
    assert "-7.14pp" in out and "-6.61pp" in out


def test_unresolvable_kpi_falls_back_to_neutral_rather_than_dollars():
    """A registry miss must not resurrect the `$` default."""

    class _NoKPI(_DAStub):
        def _lookup_kpi_scoped(self, kpi_ref, client_id):
            return None

    out = _NoKPI()._build_kt_summary(
        _da_output([{"key": "Synthetic Blend", "delta": -7.14}])
    )

    assert "$" not in out
    assert "-7.14" in out
