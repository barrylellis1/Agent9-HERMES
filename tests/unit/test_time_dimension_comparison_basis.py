# arch-allow-direct-agent-construction
"""Phase 25 step 2 — per-KPI time dimension selection + declared comparison basis.

A canonical YYYY-MM key (step 1) makes "2026-05" the same STRING on every data
product. It does NOT make it the same ACTIVITY. Verified live against BigQuery
2026-09-18: on `LubricantsSalesStarView`, 55,584 of 61,654 rows (90.2%) fall in
a different month under the delivery basis than under revenue recognition.

So a KPI must be able to say which basis it is measured on, and callers must be
able to read that back before comparing two KPIs or affirming a causal edge
between them.
"""
import logging
from types import SimpleNamespace

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.registry.models.data_product import TimeDimensionSpec


def _td(**kw):
    # Real model, not a stub: the resolver calls model_dump(), and a stub that
    # merely looks right would hide that.
    return TimeDimensionSpec(**kw)


# The real shape of dp_lubricants_sales: three dimensions, three real-world events.
SALES_TDS = [
    _td(type="fiscal_year_period", period_column_type="string",
        label="Fiscal Period (Revenue Recognition)", comparison_basis="revenue_recognition", primary=True),
    _td(column="order_date", label="Order Date", comparison_basis="order_placement"),
    _td(column="delivery_date", label="Delivery Date", comparison_basis="delivery"),
]


def _agent(tds=SALES_TDS):
    agent = object.__new__(A9_Data_Product_Agent)
    agent.logger = logging.getLogger("test.comparison_basis")
    dp = SimpleNamespace(time_dimensions=tds)
    agent.registry_factory = SimpleNamespace(
        get_provider=lambda name: SimpleNamespace(get=lambda _id: dp)
    )
    return agent


def _kpi(**meta):
    return SimpleNamespace(id="k", name="k", data_product_id="dp_lubricants_sales", metadata=meta)


class TestPerKpiTimeDimension:
    def test_no_override_uses_primary(self):
        spec = _agent()._resolve_time_spec("dp_lubricants_sales", _kpi())
        assert spec["type"] == "fiscal_year_period"
        assert spec["comparison_basis"] == "revenue_recognition"

    def test_override_selects_by_label(self):
        spec = _agent()._resolve_time_spec("dp_lubricants_sales", _kpi(time_dimension="Delivery Date"))
        assert spec["column"] == "delivery_date"
        assert spec["comparison_basis"] == "delivery"

    def test_override_selects_by_basis(self):
        spec = _agent()._resolve_time_spec("dp_lubricants_sales", _kpi(time_dimension="order_placement"))
        assert spec["column"] == "order_date"

    def test_label_matching_ignores_case_and_separators(self):
        """'Delivery Date' and 'delivery_date' must select the same entry --
        seeds and KPI metadata are written by different hands."""
        spec = _agent()._resolve_time_spec("dp_lubricants_sales", _kpi(time_dimension="delivery_date"))
        assert spec["column"] == "delivery_date"

    def test_unknown_dimension_warns_and_falls_back_to_primary(self, caplog):
        """A named-but-absent dimension is a registry mismatch, not a
        preference. Falling back silently would leave the KPI on a DIFFERENT
        basis while looking like it honoured the request."""
        with caplog.at_level(logging.WARNING):
            spec = _agent()._resolve_time_spec("dp_lubricants_sales", _kpi(time_dimension="invoice_date"))
        assert spec["comparison_basis"] == "revenue_recognition"  # the primary
        assert any("invoice_date" in r.getMessage() for r in caplog.records), \
            "the mismatch must be logged, not swallowed"

    def test_missing_kpi_argument_is_backward_compatible(self):
        """Pre-existing callers pass only the data product id."""
        spec = _agent()._resolve_time_spec("dp_lubricants_sales")
        assert spec["comparison_basis"] == "revenue_recognition"


class TestResolveComparisonBasis:
    def test_returns_declared_basis(self):
        assert _agent().resolve_comparison_basis("dp_lubricants_sales", _kpi()) == "revenue_recognition"

    def test_returns_overridden_basis(self):
        got = _agent().resolve_comparison_basis("dp_lubricants_sales", _kpi(time_dimension="Delivery Date"))
        assert got == "delivery"

    def test_undeclared_basis_is_empty_not_a_default(self):
        """Empty means UNKNOWN. Step 3 must not treat it as compatible with
        anything -- that would re-admit the bug this field exists to catch."""
        agent = _agent([_td(type="fiscal_year_period", label="Fiscal Period", primary=True)])
        assert agent.resolve_comparison_basis("dp_lubricants_sales", _kpi()) == ""

    def test_bases_differ_across_dimensions_of_one_product(self):
        """The whole point: one product, one set of rows, three answers to
        'what happened in 2026-05'."""
        agent = _agent()
        bases = {
            agent.resolve_comparison_basis("dp", _kpi()),
            agent.resolve_comparison_basis("dp", _kpi(time_dimension="Order Date")),
            agent.resolve_comparison_basis("dp", _kpi(time_dimension="Delivery Date")),
        }
        assert bases == {"revenue_recognition", "order_placement", "delivery"}
