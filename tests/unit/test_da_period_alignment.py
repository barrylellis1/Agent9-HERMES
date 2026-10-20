"""Deep Analysis analyses the comparison the situation card was read on.

Found live 2026-10-13: the B2B Revenue card said "up 1.8% vs prior year" (2026-10-01..13
against 2025-10-01..13) and Deep Analysis, asked about that card with the same token,
compared the whole quarter with the whole previous quarter and found every segment down.

Phase 26 step 3d (2026-10-16): the card records its named comparison and reference day; the
route hands them to Deep Analysis as a token, and every query resolves it through the same
spans. Without a situation, an old word is read as Situation Awareness reads it.
"""
from __future__ import annotations

from datetime import date

import pytest

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent as DA
from src.agents.new.a9_deep_analysis_agent import _period_words, _situation_period
from src.analysis.period_comparisons import from_request, spans, token
from src.api.routes.workflows import _situation_period_token
from src.database.time_filter import TimeFilter

DATED = {"type": "date", "column": "d"}
FYP = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}


@pytest.mark.parametrize("word", ["current_quarter", "current_month", "current_year", "year_to_date", "last_quarter"])
def test_both_stages_measure_the_same_two_windows(word):
    # the card's reading of the word, and the analysis given the card's token
    r = spans(from_request(word, "year_over_year", False), date.today(), False)
    tok = token(r.comparison, r.reference_day)
    assert TimeFilter.current_condition(DATED, tok, dialect="snowflake") == \
        f"d BETWEEN '{r.current.start}' AND '{r.current.end}'"
    assert TimeFilter.previous_condition(DATED, tok, dialect="snowflake") == \
        f"d BETWEEN '{r.previous.start}' AND '{r.previous.end}'"


def test_hess_the_analysis_stops_where_the_card_did():
    tok = _situation_period_token({"kpi_value": {"context": {
        "period_comparison": "ytd_vs_pytd", "reference_day": "2026-07-31"}}})
    assert tok == "ytd_vs_pytd@2026-07-31"
    assert _situation_period(tok, True) == tok   # the card's token is kept as given
    assert TimeFilter.current_condition(FYP, tok) == "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 7"


@pytest.mark.parametrize("payload", [{}, {"kpi_value": {}}, {"kpi_value": {"context": {"period_comparison": None}}},
                                     {"kpi_value": {"context": {"period_comparison": "rolling_90"}}}])
def test_a_card_without_a_recorded_comparison_gives_no_token(payload):
    assert _situation_period_token(payload) is None


ON = date(2026, 10, 15)


@pytest.mark.parametrize("word, keyed, expected", [
    ("year_to_date", True, "ytd_vs_pytd@2026-09-30"),          # closed months on period-keyed data
    ("current_quarter", False, "qtd_vs_py_qtd@2026-10-15"),    # the quarter so far, as the card reads it
    ("current_month", True, "month_vs_py_month@2026-09-30"),   # closed month on period-keyed data
    ("current_month", False, "mtd_vs_py_mtd@2026-10-15"),
    (None, False, "qtd_vs_py_qtd@2026-10-15"),                 # the route's old default
])
def test_without_a_situation_an_old_word_is_read_as_the_card_reads_it(word, keyed, expected):
    # Always with a reference day (2026-10-20), so labels and sentences can name the period
    assert _situation_period(word, keyed, today=ON) == expected


def test_a_token_without_a_day_is_given_the_data_products_day():
    assert _situation_period("ytd_vs_pytd", True, today=ON) == "ytd_vs_pytd@2026-09-30"
    assert _situation_period("ytd_vs_pytd@2026-07-31", True, today=ON) == "ytd_vs_pytd@2026-07-31"


def test_an_enum_word_is_read_too():
    from src.agents.models.situation_awareness_models import TimeFrame
    assert _situation_period(TimeFrame.CURRENT_QUARTER, today=ON) == "qtd_vs_py_qtd@2026-10-15"


def test_a_kpi_dated_by_delivery_on_a_period_keyed_product_reads_its_closed_months():
    """Fulfilment (declared on delivery date) on the period-keyed Sales product: the product's
    key decides the day, so the analysis reads Jan-Sep, as the card does (decision 7)."""
    tok = _situation_period("year_to_date", True, today=ON)
    assert TimeFilter.current_condition({"type": "date", "column": "delivery_date"}, tok) ==         "`delivery_date` BETWEEN '2026-01-01' AND '2026-09-30'"


def test_text_names_the_period_in_words():
    assert _period_words("ytd_vs_pytd@2026-09-30") == "YTD vs previous year YTD, as of 30 Sep 2026"
    assert _period_words("quarter_vs_py_quarter") == "Quarter vs same quarter previous year"
    assert _period_words(None) == ""


class TestThresholdRowForTheComparison:
    @staticmethod
    def _kpi(rows):
        from src.registry.models.kpi import KPI
        return KPI(id="k", name="K", domain="F", data_product_id="d", thresholds=rows)

    ROW = {"green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True}

    def test_the_ytd_token_finds_the_ytd_row_with_the_same_spec_as_before(self):
        kpi = self._kpi([{"comparison_type": "ytd_vs_pytd", **self.ROW}])
        assert DA._threshold_spec(kpi, "ytd_vs_pytd@2026-09-30") == DA._threshold_spec(kpi, "year_to_date") == \
            {"comparison_type": "yoy", "inverse_logic": True, "yellow_threshold": 5.0}

    def test_a_quarter_token_finds_the_quarter_row_not_the_ytd_one(self):
        kpi = self._kpi([{"comparison_type": "ytd_vs_pytd", **self.ROW, "yellow_threshold": 1.0},
                         {"comparison_type": "quarter_vs_py_quarter", **self.ROW}])
        assert DA._threshold_spec(kpi, "quarter_vs_py_quarter@2026-09-30") == \
            {"comparison_type": "yoy", "inverse_logic": True, "yellow_threshold": 5.0}

    def test_a_sequential_token_keys_on_the_previous_period(self):
        kpi = self._kpi([{"comparison_type": "quarter_vs_prev_quarter", **self.ROW}])
        assert DA._threshold_spec(kpi, "qtd_vs_prev_qtd@2026-09-30")["comparison_type"] == "qoq"
