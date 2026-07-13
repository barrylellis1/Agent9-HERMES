# arch-allow-direct-agent-construction
"""
Phase 11I-D: DA alert-type-aware comparator selection + bounded secondary-fact
narration + response propagation.

Covers:
  1. _resolve_da_comparator — override > alert-type-driven > registry default
  2. _kpi_has_budget_data — plan_version_value / budget / plan_variance threshold
  3. _build_secondary_alert_appendix — bounded flags, cap, no second diagnosis
  4. DeepAnalysisResponse round-trips with the new alert_type/comparator/merged fields
  5. New request/plan fields carry through plan construction
"""
from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
from src.agents.models.deep_analysis_models import (
    DeepAnalysisRequest,
    DeepAnalysisPlan,
    DeepAnalysisResponse,
    KTIsIsNot,
)


def _agent() -> A9_Deep_Analysis_Agent:
    return A9_Deep_Analysis_Agent({})


def _kpi(plan_version_value=None, thresholds=None):
    return SimpleNamespace(
        id="total_revenue",
        plan_version_value=plan_version_value,
        thresholds=thresholds or [],
    )


def _plan(alert_type=None, comparator_override=None, merged_alert_types=None):
    return SimpleNamespace(
        kpi_name="Total Revenue",
        alert_type=alert_type,
        comparator_override=comparator_override,
        merged_alert_types=merged_alert_types,
    )


# ---------------------------------------------------------------------------
# 1. _kpi_has_budget_data
# ---------------------------------------------------------------------------

class TestKpiHasBudgetData:
    def test_plan_version_value_set(self):
        assert A9_Deep_Analysis_Agent._kpi_has_budget_data(_kpi(plan_version_value="Budget")) is True

    def test_budget_threshold(self):
        thr = [{"comparison_type": "budget"}]
        assert A9_Deep_Analysis_Agent._kpi_has_budget_data(_kpi(thresholds=thr)) is True

    def test_plan_variance_threshold(self):
        # plan_variance is a DIFFERENT enum member than 'budget' — must still count.
        thr = [{"comparison_type": "plan_variance"}]
        assert A9_Deep_Analysis_Agent._kpi_has_budget_data(_kpi(thresholds=thr)) is True

    def test_no_budget_data(self):
        thr = [{"comparison_type": "yoy"}, {"comparison_type": "qoq"}]
        assert A9_Deep_Analysis_Agent._kpi_has_budget_data(_kpi(thresholds=thr)) is False


# ---------------------------------------------------------------------------
# 1b. _derive_budget_sql / _budget_variant_kpi — version substitution
#     (fixes the $0 secondary column: DPA drops its `filters` arg, so the
#      budget dimensional pass must pre-substitute version in the stored SQL)
# ---------------------------------------------------------------------------

class TestDeriveBudgetSql:
    def test_bracket_quoted_sqlserver(self):
        ss = "SELECT SUM([amount]) AS value FROM [dbo].[V] WHERE [version] = 'Actual'"
        out = A9_Deep_Analysis_Agent._derive_budget_sql(ss, "Budget")
        assert "[version] = 'Budget'" in out
        assert "Actual" not in out

    def test_bare_column_bigquery(self):
        bq = "SELECT SUM(amount) FROM `x.y.z` WHERE account_type = 'Revenue' AND version = 'Actual'"
        out = A9_Deep_Analysis_Agent._derive_budget_sql(bq, "Budget")
        assert "version = 'Budget'" in out
        assert "account_type = 'Revenue'" in out  # untouched

    def test_custom_plan_version_value(self):
        out = A9_Deep_Analysis_Agent._derive_budget_sql("WHERE version = 'Actual'", "Plan")
        assert "version = 'Plan'" in out

    def test_no_version_filter_returns_none(self):
        assert A9_Deep_Analysis_Agent._derive_budget_sql("SELECT 1", "Budget") is None

    def test_empty_inputs_return_none(self):
        assert A9_Deep_Analysis_Agent._derive_budget_sql("", "Budget") is None
        assert A9_Deep_Analysis_Agent._derive_budget_sql("WHERE version='Actual'", "") is None

    def test_no_backslash_escaping_in_output(self):
        # re.sub must not emit \' (SQL Server rejects it) — regression guard.
        out = A9_Deep_Analysis_Agent._derive_budget_sql("WHERE [version] = 'Actual'", "Budget")
        assert "\\'" not in out


class TestBudgetVariantKpi:
    def test_builds_proxy_with_substituted_sql(self):
        kpi = SimpleNamespace(
            id="rev", name="Revenue", plan_version_value="Budget",
            sql_query="SELECT SUM(amount) FROM t WHERE version = 'Actual'",
            metadata={}, unit="USD", data_product_id="dp1",
        )
        proxy = _agent()._budget_variant_kpi(kpi)
        assert proxy is not None
        assert "version = 'Budget'" in proxy.sql_query
        assert proxy.data_product_id == "dp1"  # routing preserved
        assert proxy.id == "rev"

    def test_defaults_plan_version_to_budget(self):
        kpi = SimpleNamespace(
            id="rev", name="Revenue", plan_version_value=None,
            sql_query="SELECT 1 FROM t WHERE version = 'Actual'",
            metadata={}, unit=None, data_product_id=None,
        )
        proxy = _agent()._budget_variant_kpi(kpi)
        assert proxy is not None
        assert "version = 'Budget'" in proxy.sql_query

    def test_none_when_no_version_filter(self):
        kpi = SimpleNamespace(
            id="rev", name="Revenue", plan_version_value="Budget",
            sql_query="SELECT 1 FROM t", metadata={}, unit=None, data_product_id=None,
        )
        assert _agent()._budget_variant_kpi(kpi) is None


# ---------------------------------------------------------------------------
# 2. _resolve_da_comparator — precedence
# ---------------------------------------------------------------------------

class TestResolveComparator:
    def setup_method(self):
        self.da = _agent()

    def test_override_wins_budget(self):
        plan = _plan(alert_type="threshold_breach", comparator_override="budget")
        assert self.da._resolve_da_comparator(plan, _kpi(), "previous") == "budget"

    def test_override_wins_previous(self):
        plan = _plan(alert_type="plan_variance", comparator_override="previous")
        assert self.da._resolve_da_comparator(plan, _kpi(plan_version_value="Budget"), "budget") == "previous"

    def test_plan_variance_with_budget_data_selects_budget(self):
        plan = _plan(alert_type="plan_variance")
        assert self.da._resolve_da_comparator(plan, _kpi(plan_version_value="Budget"), "previous") == "budget"

    def test_plan_variance_without_budget_data_falls_to_registry(self):
        plan = _plan(alert_type="plan_variance")
        # No plan data → cannot run budget basis → registry default, with a warning
        assert self.da._resolve_da_comparator(plan, _kpi(), "previous") == "previous"

    def test_threshold_breach_selects_previous(self):
        plan = _plan(alert_type="threshold_breach")
        # Even if the registry default would have been budget, a time-based alert forces previous.
        assert self.da._resolve_da_comparator(plan, _kpi(plan_version_value="Budget"), "budget") == "previous"

    def test_no_alert_type_uses_registry_default(self):
        plan = _plan(alert_type=None)
        assert self.da._resolve_da_comparator(plan, _kpi(), "budget") == "budget"
        assert self.da._resolve_da_comparator(plan, _kpi(), "previous") == "previous"

    def test_projected_breach_alert_does_not_force_budget(self):
        # projected_breach/acceleration are trend signals, not comparator bases — registry default stands.
        plan = _plan(alert_type="projected_breach")
        assert self.da._resolve_da_comparator(plan, _kpi(plan_version_value="Budget"), "previous") == "previous"


# ---------------------------------------------------------------------------
# 3. _build_secondary_alert_appendix
# ---------------------------------------------------------------------------

class TestSecondaryAppendix:
    def test_single_alert_no_appendix(self):
        out = A9_Deep_Analysis_Agent._build_secondary_alert_appendix(
            "threshold_breach", ["threshold_breach"], {"plan_value": 100.0}
        )
        assert out == ""

    def test_none_merged_no_appendix(self):
        assert A9_Deep_Analysis_Agent._build_secondary_alert_appendix("threshold_breach", None, {}) == ""

    def test_excludes_primary_includes_others(self):
        out = A9_Deep_Analysis_Agent._build_secondary_alert_appendix(
            "threshold_breach",
            ["threshold_breach", "plan_variance", "acceleration"],
            {"plan_value": 264_000_000.0, "acceleration_signal": 3.4},
        )
        # primary (threshold_breach) not repeated; both others flagged
        assert "plan variance" in out.lower()
        assert "accelerating" in out.lower()
        assert "264,000,000" in out
        assert "3.4" in out
        # no second diagnosis / IS-IS-NOT structure leaked in
        assert "Complication:" not in out

    def test_budget_primary_flags_threshold_breach(self):
        out = A9_Deep_Analysis_Agent._build_secondary_alert_appendix(
            "plan_variance", ["plan_variance", "threshold_breach"], {"plan_value": 100.0}
        )
        assert "prior-period threshold" in out.lower()
        assert "plan variance" not in out.lower()  # primary excluded

    def test_caps_at_three_lines(self):
        out = A9_Deep_Analysis_Agent._build_secondary_alert_appendix(
            "threshold_breach",
            ["threshold_breach", "plan_variance", "projected_breach", "acceleration", "compound"],
            {"plan_value": 1.0, "periods_until_breach": 2, "acceleration_signal": 2.0},
        )
        # Semicolon-joined; at most 3 flag clauses.
        assert out.count(";") <= 2


# ---------------------------------------------------------------------------
# 4. Model round-trips + plan propagation
# ---------------------------------------------------------------------------

class TestModels:
    def test_response_carries_new_fields(self):
        resp = DeepAnalysisResponse.success(
            request_id="r1",
            kt_is_is_not=KTIsIsNot(),
            alert_type="plan_variance",
            comparator="budget",
            merged_alert_types=["threshold_breach", "plan_variance"],
        )
        d = resp.model_dump()
        assert d["alert_type"] == "plan_variance"
        assert d["comparator"] == "budget"
        assert d["merged_alert_types"] == ["threshold_breach", "plan_variance"]

    def test_response_backward_compatible_without_new_fields(self):
        resp = DeepAnalysisResponse.success(request_id="r2", kt_is_is_not=KTIsIsNot())
        d = resp.model_dump()
        assert d["alert_type"] is None
        assert d["comparator"] is None

    def test_request_and_plan_carry_new_fields(self):
        req = DeepAnalysisRequest(
            request_id="r3",
            principal_id="cfo_001",
            kpi_name="Total Revenue",
            alert_type="plan_variance",
            merged_alert_types=["threshold_breach", "plan_variance"],
            secondary_alert_facts={"plan_value": 100.0},
            comparator_override="budget",
        )
        assert req.merged_alert_types == ["threshold_breach", "plan_variance"]
        assert req.secondary_alert_facts == {"plan_value": 100.0}
        assert req.comparator_override == "budget"

        plan = DeepAnalysisPlan(
            kpi_name="Total Revenue",
            merged_alert_types=req.merged_alert_types,
            secondary_alert_facts=req.secondary_alert_facts,
            comparator_override=req.comparator_override,
        )
        assert plan.comparator_override == "budget"


# ---------------------------------------------------------------------------
# 5. Segment matrix (Phase 11I-D matrix): eligibility, classification tiers, response
# ---------------------------------------------------------------------------

class TestMatrixEligibility:
    def setup_method(self):
        self.da = _agent()

    def test_eligible_when_both_bases_and_budget_data(self):
        plan = _plan(merged_alert_types=["threshold_breach", "plan_variance"])
        assert self.da._is_matrix_eligible(plan, _kpi(plan_version_value="Budget"), "previous") is True

    def test_ineligible_single_alert(self):
        plan = _plan(merged_alert_types=["threshold_breach"])
        assert self.da._is_matrix_eligible(plan, _kpi(plan_version_value="Budget"), "previous") is False

    def test_ineligible_no_plan_variance(self):
        plan = _plan(merged_alert_types=["threshold_breach", "acceleration"])
        assert self.da._is_matrix_eligible(plan, _kpi(plan_version_value="Budget"), "previous") is False

    def test_ineligible_no_budget_data(self):
        plan = _plan(merged_alert_types=["threshold_breach", "plan_variance"])
        assert self.da._is_matrix_eligible(plan, _kpi(), "previous") is False

    def test_eligible_symmetric_when_primary_is_budget(self):
        # plan_variance-dominant KPI (primary=budget) is still matrix-eligible; secondary=previous.
        plan = _plan(merged_alert_types=["threshold_breach", "plan_variance"])
        assert self.da._is_matrix_eligible(plan, _kpi(plan_version_value="Budget"), "budget") is True


class TestBasisAgreement:
    def test_confirmed_both_adverse_revenue(self):
        assert A9_Deep_Analysis_Agent._classify_basis_agreement(-10, -5, True, "problem") == "confirmed"

    def test_basis_specific_adverse_primary_only(self):
        # down vs primary, favorable vs secondary → likely artifact
        assert A9_Deep_Analysis_Agent._classify_basis_agreement(-10, 5, True, "problem") == "basis_specific"

    def test_secondary_only_healthy_primary_adverse_secondary(self):
        assert A9_Deep_Analysis_Agent._classify_basis_agreement(10, -5, True, "healthy") == "secondary_only"

    def test_healthy_both_favorable(self):
        assert A9_Deep_Analysis_Agent._classify_basis_agreement(10, 5, True, "healthy") == "healthy"

    def test_none_when_no_secondary(self):
        assert A9_Deep_Analysis_Agent._classify_basis_agreement(-10, None, True, "problem") is None

    def test_cost_kpi_inverse_logic_confirmed(self):
        # inverse (cost): adverse = delta > 0; both positive → confirmed
        assert A9_Deep_Analysis_Agent._classify_basis_agreement(10, 5, False, "problem") == "confirmed"

    def test_cost_kpi_basis_specific(self):
        # cost: adverse primary (+), favorable secondary (-) → basis_specific
        assert A9_Deep_Analysis_Agent._classify_basis_agreement(10, -5, False, "problem") == "basis_specific"


class TestMatrixResponseModel:
    def test_response_matrix_fields_roundtrip(self):
        resp = DeepAnalysisResponse.success(
            request_id="rm1",
            kt_is_is_not=KTIsIsNot(where_is=[{"dimension": "region", "key": "Gulf", "delta": -10, "secondary_delta": -8, "basis_agreement": "confirmed"}]),
            comparator="previous",
            comparator_secondary="budget",
            matrix_ran=True,
        )
        d = resp.model_dump()
        assert d["matrix_ran"] is True
        assert d["comparator_secondary"] == "budget"
        row = d["kt_is_is_not"]["where_is"][0]
        assert row["secondary_delta"] == -8
        assert row["basis_agreement"] == "confirmed"

    def test_response_matrix_defaults_off(self):
        resp = DeepAnalysisResponse.success(request_id="rm2", kt_is_is_not=KTIsIsNot())
        d = resp.model_dump()
        assert d["matrix_ran"] is False
        assert d["comparator_secondary"] is None
