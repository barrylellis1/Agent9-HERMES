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
    def test_month_cards_need_a_one_month_floor(self):
        month = spans("month_vs_py_month", TODAY, period_keyed=True)
        s1 = PeriodSettings(card_comparisons=["month_vs_py_month"], min_card_months=1)
        assert card_decision(month, s1).may_raise

    def test_ytd_in_october_may_raise_a_card(self):
        d = card_decision(spans("ytd_vs_pytd", TODAY, period_keyed=True), PeriodSettings())
        assert d.may_raise and d.reason == ""

    def test_a_comparison_outside_the_card_list_is_context_only(self):
        d = card_decision(spans("quarter_vs_py_quarter", TODAY, period_keyed=True), PeriodSettings())
        assert not d.may_raise
        assert d.reason == "Quarter vs same quarter previous year is shown for context; it does not raise cards here."

    def test_ytd_holding_one_closed_month_does_not(self):
        # a February scan of period-keyed data reads as of 31 January; the agent then falls back
        # to the last 12 months (TestKindsAndFallback), but a YTD span on its own may not raise a card
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

    def test_a_client_that_moves_on_quarters_turns_them_on(self):
        s = settings_for({"period_settings": {"card_comparisons": ["ytd_vs_pytd", "quarter_vs_py_quarter"]}})
        assert card_decision(spans("quarter_vs_py_quarter", TODAY, True), s).may_raise

    def test_plan_variance_shares_the_evidence_floor(self):
        current = spans("ytd_vs_pytd", date(2026, 2, 20), True).current
        d = has_card_evidence(current, PeriodSettings(), "Actual vs plan")
        assert not d.may_raise and d.reason.startswith("Actual vs plan holds 1 complete month")


class TestKindsAndFallback:
    """Owner rulings 2026-10-17: financial or operational; the February fallback."""

    def test_unmarked_is_financial(self):
        s = settings_for({"period_settings": {}})
        assert (s.kind, s.reading, s.card_comparisons) == ("financial", "ytd_vs_pytd", ["ytd_vs_pytd"])
        assert "year_vs_prev_year" not in s.card_comparisons  # removed from the default (ruling 1)

    def test_operational_reads_the_last_12_months(self):
        s = settings_for({"period_settings": {"kind": "operational"}})
        assert (s.reading, s.card_comparisons) == ("ltm_vs_prior_ltm", ["ltm_vs_prior_ltm"])

    def test_a_product_can_add_quarter_cards(self):
        s = settings_for({"period_settings": {"kind": "financial", "card_comparisons": ["ytd_vs_pytd", "quarter_vs_py_quarter"]}})
        assert s.card_comparisons == ["ytd_vs_pytd", "quarter_vs_py_quarter"]

    def test_an_unknown_kind_is_refused(self):
        with pytest.raises(ValueError):
            settings_for({"period_settings": {"kind": "commercial"}})

    def test_february_falls_back_to_the_last_12_months(self):
        from src.analysis.period_settings import fallback_comparison
        s = PeriodSettings()
        feb = spans("ytd_vs_pytd", date(2026, 2, 20), period_keyed=True)
        assert fallback_comparison(s, "ytd_vs_pytd", feb.current) == "ltm_vs_prior_ltm"
        mar = spans("ytd_vs_pytd", date(2026, 3, 2), period_keyed=True)
        assert fallback_comparison(s, "ytd_vs_pytd", mar.current) is None

    def test_only_a_financial_year_to_date_falls_back(self):
        from src.analysis.period_settings import fallback_comparison
        feb = spans("ytd_vs_pytd", date(2026, 2, 20), period_keyed=True)
        assert fallback_comparison(PeriodSettings(kind="operational"), "ytd_vs_pytd", feb.current) is None
        q = spans("qtd_vs_py_qtd", date(2026, 2, 20), period_keyed=True)
        assert fallback_comparison(PeriodSettings(), "qtd_vs_py_qtd", q.current) is None

    def test_the_fallback_counts_as_the_year_to_date_card(self):
        ltm = spans("ltm_vs_prior_ltm", date(2026, 2, 20), period_keyed=True)
        assert not card_decision(ltm, PeriodSettings()).may_raise            # LTM is not a financial card...
        assert card_decision(ltm, PeriodSettings(), fallback_from="ytd_vs_pytd").may_raise  # ...unless standing in


class TestThresholdRow:
    def test_the_ten_names_are_accepted(self):
        for c in COMPARISONS:
            assert KPIThreshold(comparison_type=c).comparison_type.value == c

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


class TestTheOfflineAssessmentReadsEachKpisSetting:
    """run_enterprise_assessment: each KPI on its data product's reading (Phase 26 step 3e)."""

    @staticmethod
    def _factory(dp):
        from types import SimpleNamespace
        provider = SimpleNamespace(get=lambda dp_id: dp if dp_id == "dp" else None)
        return SimpleNamespace(get_provider=lambda name: provider if name == "data_product" else None)

    @staticmethod
    def _dp(settings=None, keyed=True):
        from types import SimpleNamespace
        td = {"type": "fiscal_year_period", "year_column": "fy", "period_column": "fp"} if keyed else {"type": "date", "column": "d"}
        meta = {"period_settings": settings} if settings else {}
        return SimpleNamespace(metadata=meta, time_dimensions=[td])

    def test_the_default_is_what_every_assessment_has_read(self):
        from types import SimpleNamespace
        from run_enterprise_assessment import _period_comparison_for_kpi
        kpi = SimpleNamespace(id="k", data_product_id="dp", metadata={})
        assert _period_comparison_for_kpi(kpi, self._factory(self._dp())) == "ytd_vs_pytd"

    def test_the_data_product_decides(self):
        from types import SimpleNamespace
        from run_enterprise_assessment import _period_comparison_for_kpi
        assert _period_comparison_for_kpi(SimpleNamespace(id="k", data_product_id="dp", metadata={}),
                                          self._factory(self._dp({"kind": "operational"}))) == "ltm_vs_prior_ltm"
        dp = self._dp({"reading": "quarter_vs_py_quarter"})
        # no per-KPI exceptions (ruling 3): a KPI's own metadata no longer overrides the product
        kpi = SimpleNamespace(id="k", data_product_id="dp", metadata={"period_comparison": "year_vs_prev_year"})
        assert _period_comparison_for_kpi(kpi, self._factory(dp)) == "quarter_vs_py_quarter"

    def test_an_invalid_setting_is_logged_and_the_default_read(self, caplog):
        from types import SimpleNamespace
        from run_enterprise_assessment import _period_comparison_for_kpi
        kpi = SimpleNamespace(id="k", data_product_id="dp", metadata={})
        bad = self._dp({"reading": "mtd_vs_py_mtd", "min_card_months": 1}, keyed=True)
        assert _period_comparison_for_kpi(kpi, self._factory(bad)) == "ytd_vs_pytd"
        assert "could not be read" in caplog.text

    def test_monitoring_profile_no_longer_claims_a_comparison_period(self):
        from src.registry.models.kpi import KPIMonitoringProfile
        assert "comparison_period" not in KPIMonitoringProfile.model_fields


class TestSeeds:
    """Phase 26 step 3f(4): every seeded data product declares its kind (owner build choice 1), and
    each KPI's period target matches its data product's kind (decision 9)."""

    @staticmethod
    def _seed(client):
        import importlib.util
        spec = importlib.util.spec_from_file_location(f"seed_{client}", f"scripts/clients/{client}.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    def test_every_data_product_declares_its_kind(self):
        kinds = {}
        for client in ("lubricants", "apex_lubricants", "hess", "bicycle"):
            m = self._seed(client)
            for dp in getattr(m, "DATA_PRODUCTS", None) or [m.DATA_PRODUCT]:
                kinds[dp["id"]] = settings_for(dp["metadata"]).kind
                assert "kind" in dp["metadata"]["period_settings"], dp["id"]
        assert kinds["dp_lubricants_sales"] == kinds["dp_lubricants_orders"] == "operational"
        assert {k for d, k in kinds.items() if d not in ("dp_lubricants_sales", "dp_lubricants_orders")} == {"financial"}

    def test_each_kpi_is_judged_on_its_products_reading(self):
        for client in ("lubricants", "apex_lubricants", "hess"):
            m = self._seed(client)
            reading = {dp["id"]: settings_for(dp["metadata"]).reading
                       for dp in getattr(m, "DATA_PRODUCTS", None) or [m.DATA_PRODUCT]}
            for k in m.KPIS:
                period_rows = [t["comparison_type"] for t in k.get("thresholds") or []
                               if t["comparison_type"] in ("ytd_vs_pytd", "ltm_vs_prior_ltm")]
                assert period_rows in ([], [reading[k["data_product_id"]]]), (client, k["id"], period_rows)
