"""
MeasurementContext — provenance stamped on every KPI reading (2026-08-08).

WHY
---
`KPIValue.timeframe` records the *token* ("year_to_date"), which is an
instruction, not a fact. SA resolves windows with its own `_bq_get_period_dates`;
the DPA uses the shared `TimeFilter`. They currently agree, and nothing enforced
that they keep agreeing — a divergence would have produced two plausible numbers
with no way to tell which window either covered.

The same blindness produced a second confusion. A clean single-KPI assessment
logged, one second apart:

    Extracted KPI value for Net Revenue:  94,271,804.70
    Extracted KPI value for Net Revenue: 107,769,900.00

Both correct — Actual and Budget, the second from `_fetch_plan_value` re-running
the KPI against the plan version. Nothing on either value recorded WHICH, so the
pair read as the pipeline losing track of numbers.

These tests pin the contract that makes both failures visible rather than silent.
"""
from __future__ import annotations

import pytest

from src.agents.models.situation_awareness_models import (
    ComparisonType,
    KPIValue,
    MeasurementContext,
    TimeFrame,
)


class TestMeasurementContext:
    def test_window_renders_only_when_fully_resolved(self):
        full = MeasurementContext(window_start="2026-01-01", window_end="2026-08-08")
        assert full.window() == "2026-01-01..2026-08-08"
        # A half-resolved window is not a window. Returning a partial string would
        # let an equality check pass on incomplete provenance.
        assert MeasurementContext(window_start="2026-01-01").window() is None
        assert MeasurementContext().window() is None

    def test_label_distinguishes_readings_that_share_a_name(self):
        actual = MeasurementContext(version="Actual", window_start="2026-01-01",
                                    window_end="2026-08-08", source_system="bigquery")
        budget = MeasurementContext(version="Budget", window_start="2026-01-01",
                                    window_end="2026-08-08", source_system="bigquery")
        assert actual.label() != budget.label(), "Actual and Budget must not read identically"
        assert "Actual" in actual.label() and "Budget" in budget.label()

    def test_label_is_honest_when_nothing_is_known(self):
        # Absence must announce itself. A blank or fabricated label would let an
        # unprovenanced number look as trustworthy as a stamped one.
        assert MeasurementContext().label() == "unknown provenance"

    def test_every_field_optional_so_the_addition_is_purely_additive(self):
        MeasurementContext()  # must not raise

    def test_windows_are_comparable_across_agents(self):
        """The point of the whole model: drift becomes a checkable assertion."""
        sa = MeasurementContext(window_start="2026-01-01", window_end="2026-08-08")
        dpa_same = MeasurementContext(window_start="2026-01-01", window_end="2026-08-08")
        dpa_drifted = MeasurementContext(window_start="2025-01-01", window_end="2025-12-31")
        assert sa.window() == dpa_same.window()
        assert sa.window() != dpa_drifted.window()


class TestKPIValueCarriesContext:
    def _kpi(self, **kw):
        base = dict(kpi_name="Net Revenue", value=94_271_804.70,
                    timeframe=TimeFrame.YEAR_TO_DATE)
        base.update(kw)
        return KPIValue(**base)

    def test_context_is_optional_and_absent_by_default(self):
        # Existing callers and fixtures must be unaffected; absence must read as
        # unknown rather than as a match.
        assert self._kpi().context is None

    def test_context_round_trips(self):
        v = self._kpi(context=MeasurementContext(
            window_start="2026-01-01", window_end="2026-08-08", version="Actual",
            source_system="bigquery", data_product_id="dp_lubricants_financials",
            sql_hash="ab12cd34ef56",
        ))
        assert v.context.version == "Actual"
        assert v.context.window() == "2026-01-01..2026-08-08"
        assert v.context.sql_hash == "ab12cd34ef56"

    def test_the_live_confusion_is_now_separable(self):
        """REGRESSION — the two Net Revenue readings that looked like corruption."""
        actual = self._kpi(value=94_271_804.70, context=MeasurementContext(
            version="Actual", window_start="2026-01-01", window_end="2026-08-08",
            sql_hash="aaaaaaaaaaaa"))
        budget = self._kpi(value=107_769_900.00, context=MeasurementContext(
            version="Budget", window_start="2026-01-01", window_end="2026-08-08",
            sql_hash="bbbbbbbbbbbb"))

        assert actual.kpi_name == budget.kpi_name          # same name, as before
        assert actual.value != budget.value                # different numbers, as before
        # ...but now the difference is EXPLAINED rather than mysterious:
        assert actual.context.version != budget.context.version
        assert actual.context.sql_hash != budget.context.sql_hash
        assert actual.context.window() == budget.context.window()  # same period, different version

    def test_model_dump_carries_context_to_downstream_consumers(self):
        # DA/SF/UI receive serialised payloads; provenance must survive the hop or
        # the whole exercise stops at the agent boundary.
        d = self._kpi(context=MeasurementContext(version="Actual",
                                                 window_start="2026-01-01",
                                                 window_end="2026-08-08")).model_dump()
        assert d["context"]["version"] == "Actual"
        assert d["context"]["window_start"] == "2026-01-01"


class TestSABuildsContext:
    """The builder is defensive by contract: provenance must never break measurement."""

    def _sa_cls(self):
        from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
        return A9_Situation_Awareness_Agent

    def _build(self, sa, **kw):
        args = dict(timeframe=TimeFrame.YEAR_TO_DATE, comparison_type=None,
                    merged_filters={"Fiscal Year": ["2026"]}, source_system="bigquery",
                    data_product_id="dp_x", base_sql="SELECT SUM(amount) FROM t",
                    kpi_definition=type("K", (), {"plan_version_value": None})())
        args.update(kw)
        return sa._build_measurement_context(sa, **args) if isinstance(sa, type) else sa._build_measurement_context(**args)

    def test_resolves_a_real_window_not_the_token(self):
        ctx = self._build(self._sa_cls())
        assert ctx is not None
        assert ctx.window() is not None, "must resolve 'year_to_date' to actual dates"
        assert ctx.window_start.count("-") == 2

    def test_defaults_to_actual_and_hashes_the_sql(self):
        ctx = self._build(self._sa_cls())
        assert ctx.version == "Actual"
        assert ctx.sql_hash and len(ctx.sql_hash) == 12

    def test_detects_the_plan_version_from_the_substituted_sql(self):
        # The KPI NAME is unchanged when _fetch_plan_value rewrites the calculation,
        # so the substituted version value in the SQL is the only reliable marker.
        kpi = type("K", (), {"plan_version_value": "Budget"})()
        ctx = self._build(self._sa_cls(), kpi_definition=kpi,
                          base_sql="SELECT SUM(amount) FROM t WHERE version = 'Budget'")
        assert ctx.version == "Budget"

    def test_plan_version_declared_but_not_in_sql_is_still_actual(self):
        # A KPI that merely HAS a plan version is not a plan reading.
        kpi = type("K", (), {"plan_version_value": "Budget"})()
        ctx = self._build(self._sa_cls(), kpi_definition=kpi,
                          base_sql="SELECT SUM(amount) FROM t WHERE version = 'Actual'")
        assert ctx.version == "Actual"

    def test_different_sql_yields_different_hash(self):
        a = self._build(self._sa_cls(), base_sql="SELECT 1")
        b = self._build(self._sa_cls(), base_sql="SELECT 2")
        assert a.sql_hash != b.sql_hash

    def test_never_raises_on_bad_input(self):
        # Provenance is bookkeeping; it must not be able to fail a measurement.
        ctx = self._build(self._sa_cls(), timeframe=None, kpi_definition=None, base_sql=None)
        assert ctx is None or isinstance(ctx, MeasurementContext)


class TestComparisonBasis:
    """Not every KPI comparison is current-vs-prior.

    REGRESSION. The first implementation asked `_bq_get_period_dates` for a
    comparison window regardless of type. That helper only understands PERIODS
    and falls back to "last month" for anything else, so three of six
    ComparisonTypes were stamped with 2025-12-01..2025-12-31 — a real-looking
    range that means nothing for a plan variance or a peer benchmark.

    A fabricated window is worse than an absent one: something downstream can
    compare against it and "confirm" agreement that was never checked.

    The pipeline also has comparisons with no window at all:
      projected_breach — a forecast against a budget-derived floor
                         (floor = monthly_budget - |monthly_budget| x tol),
                         carrying a horizon in periods_until_breach
      acceleration     — 2nd derivative over >=4 monthly points, i.e. a series
    """

    def _ctx(self, comparison_type):
        from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent as SA
        return SA._build_measurement_context(
            SA, timeframe=TimeFrame.YEAR_TO_DATE, comparison_type=comparison_type,
            merged_filters={}, source_system="bigquery", data_product_id="dp",
            base_sql="SELECT 1", kpi_definition=type("K", (), {"plan_version_value": None})(),
        )

    @pytest.mark.parametrize("ct", [
        ComparisonType.YEAR_OVER_YEAR,
        ComparisonType.QUARTER_OVER_QUARTER,
        ComparisonType.MONTH_OVER_MONTH,
    ])
    def test_temporal_comparisons_stamp_a_prior_window(self, ct):
        c = self._ctx(ct)
        assert c.comparison_basis == "temporal"
        assert c.comparison_window_start and c.comparison_window_end
        assert c.comparison_window_start < c.window_start, "prior window must precede the current one"

    @pytest.mark.parametrize("ct", [ComparisonType.BUDGET_VS_ACTUAL, ComparisonType.TARGET_VS_ACTUAL])
    def test_plan_variance_compares_the_SAME_window(self, ct):
        # A plan variance is Actual vs Budget over the same period. Stamping a
        # prior period (the old behaviour: last December) was simply wrong.
        c = self._ctx(ct)
        assert c.comparison_basis == "version"
        assert (c.comparison_window_start, c.comparison_window_end) == (c.window_start, c.window_end)

    def test_benchmark_has_no_comparison_window(self):
        # A peer cohort is not a time shift. None is the honest answer.
        c = self._ctx(ComparisonType.BENCHMARK)
        assert c.comparison_basis == "peer"
        assert c.comparison_window_start is None and c.comparison_window_end is None

    def test_no_comparison_type_stamps_no_basis(self):
        c = self._ctx(None)
        assert c.comparison_basis is None
        assert c.comparison_window_start is None

    def test_current_window_is_always_stamped(self):
        # Whatever the basis, the measured period itself is always known.
        for ct in [None, ComparisonType.BUDGET_VS_ACTUAL, ComparisonType.BENCHMARK]:
            assert self._ctx(ct).window() is not None

    def test_window_equality_is_only_meaningful_within_a_basis(self):
        """The assertion this model exists to enable must not compare apples to
        oranges: a plan variance and a YoY both have windows, but comparing them
        across bases would flag a difference that is correct by definition."""
        yoy = self._ctx(ComparisonType.YEAR_OVER_YEAR)
        plan = self._ctx(ComparisonType.BUDGET_VS_ACTUAL)
        assert yoy.comparison_basis != plan.comparison_basis
        assert yoy.comparison_window_start != plan.comparison_window_start
        # Same measured period though — that IS comparable across agents.
        assert yoy.window() == plan.window()
