"""Phase 26 step 2: period settings, when a reading may raise a card, and the threshold rename.

src/analysis/period_settings.py, period_comparisons.canonical(), the registry's threshold row,
the two agents' row matching, and the client seed files.
"""
from __future__ import annotations

import importlib
from datetime import date

import pytest

from src.analysis.period_comparisons import COMPARISONS, canonical, spans
from src.analysis.period_settings import (
    DEFAULT_CARD_COMPARISONS, DEFAULT_READING, PeriodSettings, card_decision, has_card_evidence,
    settings_for,
)
from src.registry.models.kpi import KPI, ComparisonType, KPIEvaluationStatus, KPIThreshold

TODAY = date(2026, 10, 15)


class TestOldNames:
    @pytest.mark.parametrize("old, new", [
        ("yoy", "ytd_vs_pytd"), ("YOY", "ytd_vs_pytd"), ("year_over_year", "ytd_vs_pytd"),
        ("qoq", "quarter_vs_prev_quarter"), ("quarter_over_quarter", "quarter_vs_prev_quarter"),
        ("mom", "month_vs_prev_month"), (ComparisonType.YOY, "ytd_vs_pytd"),
    ])
    def test_an_old_name_reads_as_the_comparison_it_has_always_meant(self, old, new):
        assert canonical(old) == new

    @pytest.mark.parametrize("name", ["budget", "plan_variance", "projected_breach", "acceleration", "target"])
    def test_plan_and_alert_names_are_left_alone(self, name):
        assert canonical(name) == name

    def test_the_ten_are_already_canonical(self):
        assert all(canonical(c) == c for c in COMPARISONS)


class TestDefaults:
    def test_the_owners_view_is_the_default(self):
        s = settings_for(None)
        assert s.reading == DEFAULT_READING == "ytd_vs_pytd"
        assert tuple(s.card_comparisons) == DEFAULT_CARD_COMPARISONS
        assert not any(c.startswith(("month", "mtd")) for c in s.card_comparisons)  # month level no
        assert not any(c.startswith(("quarter", "qtd")) for c in s.card_comparisons)  # quarter: opt in
        assert s.min_card_months == 2  # more than one month of evidence

    def test_a_data_product_with_no_settings_takes_the_defaults(self):
        assert settings_for({"source_system": "bigquery"}) == PeriodSettings()


class TestLayering:
    DP = {"period_settings": {"card_comparisons": ["ytd_vs_pytd", "quarter_vs_py_quarter"], "min_card_months": 3}}

    def test_the_data_product_sets_its_own(self):
        s = settings_for(self.DP)
        assert s.card_comparisons == ["ytd_vs_pytd", "quarter_vs_py_quarter"]
        assert s.min_card_months == 3
        assert s.reading == "ytd_vs_pytd"

    def test_a_kpi_overrides_only_the_reading(self):
        s = settings_for(self.DP, {"period_comparison": "qtd_vs_py_qtd", "line": "top"})
        assert s.reading == "qtd_vs_py_qtd"
        assert s.min_card_months == 3

    def test_old_names_are_accepted_in_settings(self):
        s = settings_for({"period_settings": {"reading": "yoy", "card_comparisons": ["yoy", "ytd_vs_pytd"]}})
        assert s.reading == "ytd_vs_pytd" and s.card_comparisons == ["ytd_vs_pytd"]


class TestMistakesAreSeen:
    def test_an_unknown_comparison_is_refused(self):
        with pytest.raises(ValueError, match="not a period comparison"):
            settings_for({"period_settings": {"reading": "rolling_90_days"}})

    def test_a_plan_name_is_not_a_period_comparison(self):
        with pytest.raises(ValueError):
            settings_for({"period_settings": {"card_comparisons": ["budget"]}})

    def test_month_cards_with_a_higher_floor_would_never_fire(self):
        with pytest.raises(ValueError, match="hold one month"):
            settings_for({"period_settings": {"card_comparisons": ["month_vs_py_month"]}})
        s = settings_for({"period_settings": {"card_comparisons": ["month_vs_py_month"], "min_card_months": 1}})
        assert s.card_comparisons == ["month_vs_py_month"]

    def test_month_to_date_is_refused_for_period_keyed_data(self):
        dp = {"period_settings": {"reading": "mtd_vs_py_mtd", "min_card_months": 1}}
        assert settings_for(dp, period_keyed=False).reading == "mtd_vs_py_mtd"
        with pytest.raises(ValueError, match="month to date"):
            settings_for(dp, period_keyed=True)

    def test_the_floor_is_bounded(self):
        with pytest.raises(ValueError):
            settings_for({"period_settings": {"min_card_months": 0}})


class TestWhenACardMayBeRaised:
    def test_ytd_in_october_may_raise_a_card(self):
        d = card_decision(spans("ytd_vs_pytd", TODAY, period_keyed=True), PeriodSettings())
        assert d.may_raise and d.reason == ""

    def test_a_comparison_outside_the_card_list_is_context_only(self):
        d = card_decision(spans("quarter_vs_py_quarter", TODAY, period_keyed=True), PeriodSettings())
        assert not d.may_raise
        assert d.reason == "Quarter vs same quarter previous year is shown for context; it does not raise cards here."

    def test_ytd_holding_one_closed_month_does_not(self):
        # a February scan of period-keyed data reads as of 31 January
        d = card_decision(spans("ytd_vs_pytd", date(2026, 2, 20), period_keyed=True), PeriodSettings())
        assert not d.may_raise
        assert d.reason == "YTD vs previous year YTD holds 1 complete month (Jan 2026); a card needs 2."
        assert card_decision(spans("ytd_vs_pytd", date(2026, 3, 2), period_keyed=True), PeriodSettings()).may_raise

    def test_date_keyed_ytd_counts_only_whole_months(self):
        s = PeriodSettings()
        assert not card_decision(spans("ytd_vs_pytd", date(2026, 2, 27), False), s).may_raise  # Jan + part of Feb
        assert card_decision(spans("ytd_vs_pytd", date(2026, 2, 28), False), s).may_raise  # Jan + Feb
        early = card_decision(spans("ytd_vs_pytd", date(2026, 1, 9), False), s)
        assert early.reason.startswith("YTD vs previous year YTD holds no complete month")

    def test_a_threshold_row_can_opt_in_or_out(self):
        s = PeriodSettings()
        quarter = spans("quarter_vs_py_quarter", TODAY, period_keyed=True)
        assert card_decision(quarter, s, raises_card=True).may_raise
        assert not card_decision(spans("ytd_vs_pytd", TODAY, True), s, raises_card=False).may_raise

    def test_opting_in_does_not_skip_the_evidence_floor(self):
        month = spans("month_vs_py_month", TODAY, period_keyed=True)
        d = card_decision(month, PeriodSettings(), raises_card=True)
        assert not d.may_raise and "a card needs 2" in d.reason
        assert card_decision(month, PeriodSettings(min_card_months=1), raises_card=True).may_raise

    def test_a_client_that_moves_on_quarters_turns_them_on(self):
        s = settings_for({"period_settings": {"card_comparisons": ["ytd_vs_pytd", "quarter_vs_py_quarter"]}})
        assert card_decision(spans("quarter_vs_py_quarter", TODAY, True), s).may_raise

    def test_plan_variance_shares_the_evidence_floor(self):
        current = spans("ytd_vs_pytd", date(2026, 2, 20), True).current
        d = has_card_evidence(current, PeriodSettings(), "Actual vs plan")
        assert not d.may_raise and d.reason.startswith("Actual vs plan holds 1 complete month")


class TestThresholdRow:
    def test_the_ten_names_are_accepted(self):
        for c in COMPARISONS:
            assert KPIThreshold(comparison_type=c).comparison_type.value == c

    def test_raises_card_defaults_to_following_the_data_product(self):
        assert KPIThreshold(comparison_type="ytd_vs_pytd").raises_card is None
        assert KPIThreshold(comparison_type="ytd_vs_pytd", raises_card=False).raises_card is False

    def test_evaluate_finds_a_renamed_row_by_its_old_name_and_back(self):
        new = KPI(id="k", name="K", domain="F", data_product_id="d",
                  thresholds=[{"comparison_type": "ytd_vs_pytd", "green_threshold": 5, "yellow_threshold": 0, "red_threshold": -5}])
        old = KPI(id="k", name="K", domain="F", data_product_id="d",
                  thresholds=[{"comparison_type": "yoy", "green_threshold": 5, "yellow_threshold": 0, "red_threshold": -5}])
        assert new.evaluate(3, ComparisonType.YOY) == KPIEvaluationStatus.YELLOW
        assert old.evaluate(3, ComparisonType.YTD_VS_PYTD) == KPIEvaluationStatus.YELLOW
        assert new.evaluate(3, ComparisonType.QOQ) == KPIEvaluationStatus.UNKNOWN


class TestSituationAwarenessFilesRowsByComparison:
    def test_old_and_new_names_and_the_request_share_one_key(self):
        from src.agents.new.a9_situation_awareness_agent import _threshold_key
        assert _threshold_key("yoy") == _threshold_key("ytd_vs_pytd") == _threshold_key("year_over_year") == "ytd_vs_pytd"
        assert _threshold_key("qoq") == _threshold_key("quarter_over_quarter") == "quarter_vs_prev_quarter"
        assert _threshold_key(ComparisonType.YOY) == "ytd_vs_pytd"

    def test_plan_and_alert_rows_keep_their_keys(self):
        from src.agents.new.a9_situation_awareness_agent import _threshold_key
        assert _threshold_key("budget_vs_actual") == "budget"
        assert _threshold_key("target_vs_actual") == "target"
        for k in ("plan_variance", "projected_breach", "acceleration"):
            assert _threshold_key(k) == k
        assert _threshold_key(None) is None and _threshold_key("") is None


class TestDeepAnalysisPicksTheSameRow:
    @staticmethod
    def _kpi(rows):
        return KPI(id="cogs", name="COGS", domain="F", data_product_id="d", thresholds=rows)

    ROW = {"green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True}

    def test_a_renamed_row_gives_the_spec_its_old_name_gave(self):
        from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent as DA
        new = DA._threshold_spec(self._kpi([{"comparison_type": "ytd_vs_pytd", **self.ROW}]), "year_to_date")
        old = DA._threshold_spec(self._kpi([{"comparison_type": "yoy", **self.ROW}]), "year_to_date")
        assert new == old == {"comparison_type": "yoy", "inverse_logic": True, "yellow_threshold": 5.0}

    def test_it_is_matched_before_a_budget_row(self):
        from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent as DA
        rows = [{"comparison_type": "budget", "yellow_threshold": 2.0},
                {"comparison_type": "ytd_vs_pytd", **self.ROW}]
        assert DA._threshold_spec(self._kpi(rows), "year_to_date")["comparison_type"] == "yoy"

    def test_quarter_rows_match_a_quarter_timeframe(self):
        from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent as DA
        spec = DA._threshold_spec(self._kpi([{"comparison_type": "quarter_vs_prev_quarter", **self.ROW}]), "current_quarter")
        assert spec == {"comparison_type": "qoq", "inverse_logic": True, "yellow_threshold": 5.0}

    def test_with_no_row_for_the_comparison_budget_is_used_then_the_default(self):
        from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent as DA
        budget_only = self._kpi([{"comparison_type": "budget", "yellow_threshold": 2.0}])
        assert DA._threshold_spec(budget_only, "year_to_date")["comparison_type"] == "budget"
        assert DA._threshold_spec(self._kpi([]), "year_to_date") == \
            {"comparison_type": "yoy", "inverse_logic": False, "yellow_threshold": 0.0}


_CLIENTS = ["lubricants", "apex_lubricants", "hess", "bicycle"]


def _data_products(mod):
    return getattr(mod, "DATA_PRODUCTS", None) or [mod.DATA_PRODUCT]


class TestSeedFiles:
    @pytest.mark.parametrize("client", _CLIENTS)
    def test_no_seed_still_writes_an_old_name(self, client):
        mod = importlib.import_module(f"scripts.clients.{client}")
        old = [(k["id"], t["comparison_type"]) for k in mod.KPIS for t in k.get("thresholds") or []
               if str(t.get("comparison_type")).lower() in ("yoy", "qoq", "mom")]
        assert old == []

    @pytest.mark.parametrize("client", _CLIENTS)
    def test_every_threshold_row_loads(self, client):
        mod = importlib.import_module(f"scripts.clients.{client}")
        for k in mod.KPIS:
            for t in k.get("thresholds") or []:
                KPIThreshold(**t)

    @pytest.mark.parametrize("client", _CLIENTS)
    def test_every_data_product_has_valid_settings(self, client):
        mod = importlib.import_module(f"scripts.clients.{client}")
        for dp in _data_products(mod):
            meta = dp.get("metadata") or {}
            keyed = any(td.get("type") in ("fiscal_year_period", "fiscal_year")
                        for td in (dp.get("time_dimensions") or meta.get("time_dimensions") or []))
            settings_for(meta, period_keyed=keyed)
            for k in mod.KPIS:
                if k.get("data_product_id") == dp.get("id"):
                    settings_for(meta, k.get("metadata") or {}, period_keyed=keyed)
