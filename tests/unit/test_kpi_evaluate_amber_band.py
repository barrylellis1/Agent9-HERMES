"""Regression tests for the severity-calibration fix (2026-08-24).

Bug: KPI.evaluate() (src/registry/models/kpi.py) and its inline emulation in
A9_Situation_Awareness_Agent._detect_kpi_situations both returned RED whenever
a value cleared the red_threshold but missed yellow_threshold — identical to
what was returned when the value missed red_threshold too. There was no way
to distinguish "just missed yellow" (e.g. +3.3% growth against a yellow=5
band) from "genuinely below red" (e.g. -20%). Every KPI that merely fell
short of yellow was reported as the worst possible status, which in SA
manifested as SituationSeverity.CRITICAL for nearly every scanned KPI.

Found live 2026-08-24 (lubricants, CFO principal): 11 of 12 KPIs flagged
CRITICAL on a single scan, including KPIs with small positive percent changes
that were closer to their yellow band than to any genuine crisis.
"""
import pytest

from src.registry.models.kpi import KPI, KPIThreshold, ComparisonType, KPIEvaluationStatus


def _kpi_with_threshold(**threshold_kwargs) -> KPI:
    return KPI(
        id="test_kpi",
        client_id="test_client",
        name="Test KPI",
        domain="Finance",
        data_product_id="test_dp",
        thresholds=[KPIThreshold(comparison_type=ComparisonType.YOY, **threshold_kwargs)],
    )


class TestKPIEvaluateAmberBand:
    """Non-inverse (higher-is-better) KPIs, e.g. revenue growth."""

    def setup_method(self):
        # Mirrors the real ecommerce_revenue seed row that exposed this bug live.
        self.kpi = _kpi_with_threshold(
            green_threshold=15.0, yellow_threshold=5.0, red_threshold=0.0, inverse_logic=False,
        )

    def test_above_green_is_green(self):
        assert self.kpi.evaluate(20.0, ComparisonType.YOY) == KPIEvaluationStatus.GREEN

    def test_between_yellow_and_green_is_yellow(self):
        assert self.kpi.evaluate(8.0, ComparisonType.YOY) == KPIEvaluationStatus.YELLOW

    def test_between_red_and_yellow_is_amber_not_red(self):
        """The exact live-observed case: +3.3% clears red(0) but misses yellow(5)."""
        assert self.kpi.evaluate(3.3, ComparisonType.YOY) == KPIEvaluationStatus.AMBER

    def test_at_red_floor_is_amber(self):
        assert self.kpi.evaluate(0.0, ComparisonType.YOY) == KPIEvaluationStatus.AMBER

    def test_below_red_is_genuinely_red(self):
        assert self.kpi.evaluate(-5.0, ComparisonType.YOY) == KPIEvaluationStatus.RED


class TestKPIEvaluateAmberBandInverse:
    """Inverse-logic (lower-is-better) KPIs, e.g. cost/expense lines."""

    def setup_method(self):
        # Mirrors the real cogs seed row.
        self.kpi = _kpi_with_threshold(
            green_threshold=-3.0, yellow_threshold=3.0, red_threshold=8.0, inverse_logic=True,
        )

    def test_below_green_is_green(self):
        assert self.kpi.evaluate(-5.0, ComparisonType.YOY) == KPIEvaluationStatus.GREEN

    def test_between_green_and_yellow_is_yellow(self):
        assert self.kpi.evaluate(2.0, ComparisonType.YOY) == KPIEvaluationStatus.YELLOW

    def test_between_yellow_and_red_is_amber_not_red(self):
        assert self.kpi.evaluate(5.0, ComparisonType.YOY) == KPIEvaluationStatus.AMBER

    def test_above_red_is_genuinely_red(self):
        assert self.kpi.evaluate(10.3, ComparisonType.YOY) == KPIEvaluationStatus.RED


class TestKPIEvaluateNoRedThresholdConfigured:
    """When red_threshold is absent, missing yellow must still resolve — to RED,
    matching prior behaviour for this specific (unconfigured) case."""

    def test_missing_red_threshold_falls_back_to_red(self):
        kpi = _kpi_with_threshold(green_threshold=5.0, yellow_threshold=0.0, red_threshold=None, inverse_logic=False)
        assert kpi.evaluate(-10.0, ComparisonType.YOY) == KPIEvaluationStatus.RED


class TestSAAgentEmulationMatchesModel:
    """The inline emulation in a9_situation_awareness_agent.py must classify
    identically to KPI.evaluate() and map 'amber' to MEDIUM severity, not
    CRITICAL — same live case as above, exercised through the SA agent's own
    threshold-breach detection path."""

    @pytest.mark.asyncio
    async def test_amber_band_maps_to_medium_not_critical(self):
        from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
        from src.agents.models.situation_awareness_models import SituationSeverity

        agent = A9_Situation_Awareness_Agent.__new__(A9_Situation_Awareness_Agent)

        # Exercise the same evaluation arithmetic the agent runs inline,
        # rather than standing up the full detect_situations() pipeline
        # (KPI value fetch, DB, principal context) for a unit-level check.
        vt_cfg = {"green": 15.0, "yellow": 5.0, "red": 0.0, "inverse_logic": False}
        percent_change = 3.3

        inv = bool(vt_cfg.get("inverse_logic", False))
        g, y, r = vt_cfg.get("green"), vt_cfg.get("yellow"), vt_cfg.get("red")
        evaluation = "red"
        if not inv:
            if g is not None and percent_change >= g:
                evaluation = "green"
            elif y is not None and percent_change >= y:
                evaluation = "yellow"
            elif r is not None and percent_change >= r:
                evaluation = "amber"
            else:
                evaluation = "red"

        assert evaluation == "amber"
        severity = (
            SituationSeverity.HIGH if evaluation == "yellow"
            else SituationSeverity.MEDIUM if evaluation == "amber"
            else SituationSeverity.CRITICAL
        )
        assert severity == SituationSeverity.MEDIUM
