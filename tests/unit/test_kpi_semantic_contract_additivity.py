"""Regression/coverage tests for the §3 additivity fields on the KPI model
(2026-08-30, Phase 17 T1 -- docs/architecture/kpi_semantic_contract.md §3).

additive_across_dimensions must default to None, NEVER True: assuming
additive-by-default would silently re-authorise the exact defect this
contract exists to close (§6 "Honest limitations", and the live Aug 6 bug
documented in src/analysis/groundedness.py).
"""
from src.registry.models.kpi import KPI


def _kpi(**overrides) -> KPI:
    base = dict(
        id="test_kpi", client_id="test_client", name="Test", domain="Finance",
        data_product_id="dp_test",
    )
    base.update(overrides)
    return KPI(**base)


class TestAdditivityDefaults:
    def test_additive_across_dimensions_defaults_to_none_not_true(self):
        """The one non-negotiable default in this whole field set."""
        kpi = _kpi()
        assert kpi.additive_across_dimensions is None

    def test_all_seven_fields_default_to_none(self):
        kpi = _kpi()
        assert kpi.unit_class is None
        assert kpi.additive_across_dimensions is None
        assert kpi.aggregation_method is None
        assert kpi.weight_column is None
        assert kpi.sign_convention is None
        assert kpi.inverse_logic is None
        assert kpi.scope_eligible is None

    def test_legacy_shape_with_no_semantic_contract_keys_still_constructs(self):
        """Every pre-existing KPI record (no §3 keys at all) must load cleanly."""
        legacy_shape = {
            "id": "cogs", "client_id": "lubricants", "name": "Cost of Goods Sold",
            "domain": "Finance", "data_product_id": "dp_lubricants_financials",
        }
        kpi = KPI(**legacy_shape)
        assert kpi.additive_across_dimensions is None


class TestAdditivityExplicitValues:
    def test_additive_kpi_declares_true(self):
        kpi = _kpi(additive_across_dimensions=True, aggregation_method="sum")
        assert kpi.additive_across_dimensions is True

    def test_non_additive_kpi_declares_false_with_weighted_avg(self):
        kpi = _kpi(
            id="gross_margin_pct", additive_across_dimensions=False,
            aggregation_method="weighted_avg", weight_column="net_revenue",
        )
        assert kpi.additive_across_dimensions is False
        assert kpi.aggregation_method == "weighted_avg"
        assert kpi.weight_column == "net_revenue"

    def test_scope_eligible_accepts_all_three_values(self):
        for v in ("enterprise", "segment", "both"):
            assert _kpi(scope_eligible=v).scope_eligible == v

    def test_sign_convention_is_distinct_from_data_product_measure_semantics(self):
        """KPI-level sign_convention -- a different field, a different grain,
        from DataProduct.measure_semantics (data-product-level, Phase 16 step 2,
        already live). Both may legitimately exist without colliding."""
        kpi = _kpi(id="cogs", sign_convention="negative_stored", inverse_logic=True)
        assert kpi.sign_convention == "negative_stored"
        assert kpi.inverse_logic is True


class TestNotSliceableByUnaffected:
    """Guard: adding §3 must not disturb §4 (not_sliceable_by), a different,
    already-built axis -- docs/architecture/kpi_semantic_contract.md §4.1."""

    def test_not_sliceable_by_still_defaults_to_empty_list(self):
        kpi = _kpi()
        assert kpi.not_sliceable_by == []

    def test_both_axes_can_be_declared_independently_on_the_same_kpi(self):
        kpi = _kpi(
            additive_across_dimensions=False,
            not_sliceable_by=[{"dimension": "customer_name", "reason_class": "pipeline_gap", "source": "derived"}],
        )
        assert kpi.additive_across_dimensions is False
        assert kpi.not_sliceable_by[0].dimension == "customer_name"
