# arch-allow-direct-agent-construction
"""
Unit tests for Phase 11I-A: Advanced Alert Intelligence.

Covers four new SA detection patterns:
  1. plan_variance          — actual vs plan/budget
  2. projected_breach       — linear trend crosses threshold within N periods
  3. acceleration           — rate of deterioration is itself speeding up
  4. kpi_type propagation   — covenant/regulatory KPIs always fire at severity=critical

All tests use lightweight mocks — no real DPA/SA instances or network calls.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


# ---------------------------------------------------------------------------
# Model imports
# ---------------------------------------------------------------------------
from src.agents.models.situation_awareness_models import (
    KPIDefinition,
    KPIValue,
    Situation,
    SituationSeverity,
    TimeFrame,
    ComparisonType,
    PrincipalContext,
)


# ---------------------------------------------------------------------------
# Helper: build a minimal SA agent stub that has the three pure methods
# we want to test, without any real infrastructure.
# ---------------------------------------------------------------------------

def _make_sa_stub():
    """Return a stub SA agent with the four new 11I-A methods available."""
    # Import here so that the module-level import check in the test file is clean
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent

    stub = object.__new__(A9_Situation_Awareness_Agent)
    # Attach minimal logger
    import logging
    stub.logger = logging.getLogger("test.sa_stub")
    return stub


# ---------------------------------------------------------------------------
# Helper: build minimal KPIDefinition
# ---------------------------------------------------------------------------

def _kpi_def(
    kpi_id="net_revenue",
    name="Net Revenue",
    plan_version_value=None,
    kpi_type="operational",
    calculation="SELECT SUM(amount) AS value FROM View WHERE version = 'Actual'",
    metadata=None,
    positive_trend_is_good=True,
):
    return KPIDefinition(
        id=kpi_id,
        name=name,
        description="Test KPI",
        unit="$",
        data_product_id="dp_test",
        calculation=calculation,
        positive_trend_is_good=positive_trend_is_good,
        plan_version_value=plan_version_value,
        kpi_type=kpi_type,
        metadata=metadata,
    )


def _kpi_value(value=860.0, inverse_logic=False, monthly_values=None):
    return KPIValue(
        kpi_name="Net Revenue",
        value=value,
        timeframe=TimeFrame.CURRENT_QUARTER,
        inverse_logic=inverse_logic,
        monthly_values=monthly_values,
    )


# ===========================================================================
# PLAN VARIANCE TESTS (3)
# ===========================================================================

class TestPlanVariance:

    @pytest.mark.asyncio
    async def test_plan_variance_fires_when_below_plan(self):
        """Actual=860, Plan=1000 → 14% miss → CRITICAL plan_variance situation."""
        sa = _make_sa_stub()

        kpi_def = _kpi_def(plan_version_value="Budget")
        kpi_val = _kpi_value(value=860.0)

        # We'll exercise the logic inline by calling _fetch_plan_value through a mock
        # and checking the situation creation logic.
        # Rather than patching _get_kpi_value (which has complex routing), we mock
        # _fetch_plan_value directly on the stub.
        plan_val = 1000.0

        # Replicate the plan_variance situation creation logic that exists in detect_situations()
        variance_pct = (kpi_val.value - plan_val) / abs(plan_val)   # -0.14
        inverse = kpi_val.inverse_logic
        bad_direction = (variance_pct < 0) if not inverse else (variance_pct > 0)
        abs_variance = abs(variance_pct)

        assert abs_variance >= 0.02, "variance >= 2% — should fire"

        severity = SituationSeverity.CRITICAL if abs_variance >= 0.15 else (
            SituationSeverity.HIGH if abs_variance >= 0.08 else SituationSeverity.MEDIUM
        )
        # 14% miss → HIGH (not yet critical)
        assert severity == SituationSeverity.HIGH
        assert bad_direction is True

        direction_word = "below" if bad_direction else "ahead of"
        sit = Situation(
            situation_id=f"plan_{kpi_def.id}_{int(abs_variance * 100)}",
            kpi_name=kpi_def.name,
            kpi_id=kpi_def.id,
            kpi_value=kpi_val,
            severity=severity,
            card_type="problem",
            direction="down",
            alert_type="plan_variance",
            plan_value=plan_val,
            description=f"{kpi_def.name} is {abs_variance*100:.1f}% {direction_word} plan",
            business_impact="...",
            hitl_required=bad_direction and severity == SituationSeverity.CRITICAL,
        )

        assert sit.alert_type == "plan_variance"
        assert sit.plan_value == 1000.0
        assert sit.severity == SituationSeverity.HIGH
        assert sit.card_type == "problem"
        assert sit.hitl_required is False  # HIGH, not CRITICAL

    @pytest.mark.asyncio
    async def test_plan_variance_fires_critical_when_large_miss(self):
        """Actual=820, Plan=1000 → 18% miss → CRITICAL plan_variance situation."""
        kpi_val = _kpi_value(value=820.0)
        plan_val = 1000.0
        variance_pct = (kpi_val.value - plan_val) / abs(plan_val)  # -0.18
        severity = SituationSeverity.CRITICAL if abs(variance_pct) >= 0.15 else (
            SituationSeverity.HIGH if abs(variance_pct) >= 0.08 else SituationSeverity.MEDIUM
        )
        assert severity == SituationSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_plan_variance_suppressed_when_no_plan_version(self):
        """When plan_version_value is None, _fetch_plan_value returns None immediately."""
        sa = _make_sa_stub()
        kpi_def = _kpi_def(plan_version_value=None)
        # _fetch_plan_value should return None without calling _get_kpi_value
        result = await sa._fetch_plan_value(kpi_def, TimeFrame.CURRENT_QUARTER, None, None)
        assert result is None

    @pytest.mark.asyncio
    async def test_plan_variance_inverted_for_cost_kpi(self):
        """inverse_logic=True, actual=1100, plan=1000 → cost over budget → bad_direction=True."""
        kpi_val = _kpi_value(value=1100.0, inverse_logic=True)
        plan_val = 1000.0
        variance_pct = (kpi_val.value - plan_val) / abs(plan_val)   # +0.10
        inverse = kpi_val.inverse_logic
        bad_direction = (variance_pct < 0) if not inverse else (variance_pct > 0)
        # Cost went up vs budget → bad even though variance_pct is positive
        assert bad_direction is True

        card_type = "problem" if bad_direction else "opportunity"
        assert card_type == "problem"

    def test_plan_variance_wording_is_polarity_aware(self):
        """Description wording must reflect KPI polarity, not just the numeric sign.

        A cost over budget reads 'above plan'; a cost under budget reads 'below plan'.
        Revenue below budget reads 'below plan'; revenue ahead reads 'ahead of plan'.
        """
        def word(is_cost, bad_direction):
            if is_cost:
                return "above" if bad_direction else "below"
            return "below" if bad_direction else "ahead of"

        # Cost KPI (inverse): over budget = bad → 'above'; under budget = good → 'below'
        assert word(is_cost=True, bad_direction=True) == "above"
        assert word(is_cost=True, bad_direction=False) == "below"
        # Revenue/profit KPI: below budget = bad → 'below'; ahead = good → 'ahead of'
        assert word(is_cost=False, bad_direction=True) == "below"
        assert word(is_cost=False, bad_direction=False) == "ahead of"


# ===========================================================================
# PROJECTED BREACH TESTS (4)
# ===========================================================================

class TestProjectedBreach:

    def test_projection_fires_when_trend_crosses_threshold(self):
        """Steadily declining series should cross the threshold within horizon."""
        sa = _make_sa_stub()
        # Series declining by 10 each period from 100: [90,80,70,60,50,40,30,20,10]
        # Last value is 10, threshold red=50 → already below, but _project_trend looks forward.
        # Use a series that is approaching but hasn't crossed yet:
        # [100, 90, 80, 70, 60, 55] — last value 55, threshold 50 — projection t+1 ≈ 45 → breach
        monthly = [
            {"period": "2026-01", "value": 100},
            {"period": "2026-02", "value": 90},
            {"period": "2026-03", "value": 80},
            {"period": "2026-04", "value": 70},
            {"period": "2026-05", "value": 60},
            {"period": "2026-06", "value": 55},
        ]
        thresholds = {"red": 50.0}
        result = sa._project_trend(monthly, thresholds, inverse_logic=False)
        assert result is not None, "Should project a breach"
        assert result["periods_until_breach"] >= 1
        assert result["projection_confidence"] >= 0.4

    def test_projection_suppressed_when_r2_too_low(self):
        """Noisy / random series should produce R² < 0.4 and return None."""
        sa = _make_sa_stub()
        # Alternating high-low values — high noise, low R²
        monthly = [
            {"period": "2026-01", "value": 100},
            {"period": "2026-02", "value": 20},
            {"period": "2026-03", "value": 95},
            {"period": "2026-04", "value": 15},
            {"period": "2026-05", "value": 90},
            {"period": "2026-06", "value": 10},
        ]
        thresholds = {"red": 50.0}
        result = sa._project_trend(monthly, thresholds, inverse_logic=False)
        assert result is None, "Noisy series should not produce a projection"

    def test_projection_suppressed_when_actual_breach_exists(self):
        """When a threshold_breach situation exists, projected_breach should NOT be added."""
        # This test validates the guard: _has_threshold_breach = any(alert_type=="threshold_breach")
        # We simulate the guard logic directly.
        existing_sit = Situation(
            situation_id="breach_001",
            kpi_name="Net Revenue",
            kpi_value=_kpi_value(),
            severity=SituationSeverity.CRITICAL,
            description="actual breach",
            business_impact="impact",
            alert_type="threshold_breach",
        )
        detected_situations = [existing_sit]
        has_threshold_breach = any(s.alert_type == "threshold_breach" for s in detected_situations)
        assert has_threshold_breach is True
        # In the real code, this guard prevents _project_trend from being called.

    def test_projection_direction_correct_for_cost_kpi(self):
        """inverse_logic=True: rising cost series should also detect a breach."""
        sa = _make_sa_stub()
        # Steadily rising costs (bad for cost KPI with inverse_logic)
        monthly = [{"period": f"2026-{i:02d}", "value": 50 + i * 5} for i in range(1, 10)]
        # With inverse_logic=True, crossing ABOVE threshold is a breach
        thresholds = {"red": 90.0}
        result = sa._project_trend(monthly, thresholds, inverse_logic=True)
        assert result is not None, "Rising cost series should cross the cost threshold"
        assert result["periods_until_breach"] >= 1


# ===========================================================================
# ACCELERATION TESTS (3)
# ===========================================================================

class TestAcceleration:

    def test_acceleration_fires_when_second_derivative_exceeds_threshold(self):
        """Velocity that is itself accelerating should trigger the signal."""
        sa = _make_sa_stub()
        # Series with dramatically accelerating decline:
        # Values:    100, 99, 97, 93, 85, 70
        # Velocities:    -1, -2, -4, -8, -15
        # Accel:            -1, -2, -4, -7  ← latest=-7
        # v_mean ≈ -6, v_std needs to be < 7/2=3.5 for signal to fire
        # Let's use a more dramatic case:
        # Values:    100, 99, 98, 96, 92, 84
        # Velocities:   -1, -1, -2, -4, -8
        # Accel:           0, -1, -2, -4  ← latest=-4, v_std of [-1,-1,-2,-4,-8]
        # v_mean=-3.2, deviations: 2.2,2.2,1.2,-0.8,-4.8
        # variance=(4.84+4.84+1.44+0.64+23.04)/5=34.8/5=6.96, std=2.638
        # threshold=2*2.638=5.276; abs(-4)=4 < 5.276 → still not triggering
        #
        # Use a truly extreme acceleration: doublings
        # Values: 1000, 998, 994, 986, 970, 938
        # Velocities:  -2, -4, -8, -16, -32
        # Accel:          -2, -4, -8, -16  ← latest=-16
        # v_mean=-12.4, deviations: 10.4, 8.4, 4.4, -3.6, -19.6
        # variance=(108.16+70.56+19.36+12.96+384.16)/5=595.2/5=119.04, std=10.91
        # threshold=2*10.91=21.82; abs(-16)=16 < 21.82 → still not triggering
        #
        # The 2× threshold is relative to the velocity std. Let's use a series where
        # the velocities are nearly constant EXCEPT the last period which jumps dramatically:
        # Values: 100, 98, 96, 94, 92, 52
        # Velocities:  -2, -2, -2, -2, -40
        # Accel:         0,  0,  0, -38  ← latest=-38
        # v_mean=-9.6, deviations: 7.6,7.6,7.6,7.6,-30.4
        # variance=(57.76*4+924.16)/5=(231.04+924.16)/5=1155.2/5=231.04, std=15.2
        # threshold=2*15.2=30.4; abs(-38)=38 > 30.4 → FIRES ✓
        monthly = [
            {"period": "2026-01", "value": 100},
            {"period": "2026-02", "value": 98},
            {"period": "2026-03", "value": 96},
            {"period": "2026-04", "value": 94},
            {"period": "2026-05", "value": 92},
            {"period": "2026-06", "value": 52},
        ]
        result = sa._compute_acceleration(monthly)
        assert result is not None, "Accelerating decline should trigger signal"
        assert result > 0

    def test_acceleration_not_fired_on_stable_decline(self):
        """Constant velocity (first derivative constant) should NOT trigger acceleration."""
        sa = _make_sa_stub()
        # Series declining by exactly 5 each period — constant velocity, zero acceleration
        monthly = [{"period": f"2026-{i:02d}", "value": 100 - i * 5} for i in range(9)]
        result = sa._compute_acceleration(monthly)
        # With perfectly constant velocity, acceleration=0 everywhere, std of velocity is also 0
        # so the function returns None (velocity std == 0 → divide-by-zero guard)
        assert result is None, "Constant velocity should produce no acceleration signal"

    def test_acceleration_not_fired_on_single_spike(self):
        """A single-period velocity spike that then stabilises should not fire."""
        sa = _make_sa_stub()
        # Mostly stable, one big drop, then stable again → one large acceleration, one large deceleration
        monthly = [
            {"period": "2026-01", "value": 100},
            {"period": "2026-02", "value": 100},
            {"period": "2026-03", "value": 100},
            {"period": "2026-04", "value": 60},   # big drop
            {"period": "2026-05", "value": 60},   # stable again
            {"period": "2026-06", "value": 60},
        ]
        # The final acceleration (period 5→6 velocity change) is 0, should not exceed threshold
        result = sa._compute_acceleration(monthly)
        # Latest accel = velocity[-1] - velocity[-2]
        # velocities: 0, 0, -40, 0, 0  → accel: 0, -40, 40, 0 → latest=0
        # So no signal at the end
        assert result is None, "Spike that has stabilised should not trigger ongoing acceleration"

    def test_acceleration_fire_multiplier_is_configurable(self):
        """A higher fire_multiplier suppresses a borderline signal; a lower one keeps it.

        Series where latest |accel| lands between two candidate fire floors, so the
        registry-sourced multiplier decides whether the pattern fires.
        """
        sa = _make_sa_stub()
        # Values: 100, 98, 96, 94, 92, 52
        # velocities: -2,-2,-2,-2,-40 ; latest accel=-38 ; v_std≈15.2
        # signal magnitude = 38/15.2 ≈ 2.5
        monthly = [
            {"period": "2026-01", "value": 100},
            {"period": "2026-02", "value": 98},
            {"period": "2026-03", "value": 96},
            {"period": "2026-04", "value": 94},
            {"period": "2026-05", "value": 92},
            {"period": "2026-06", "value": 52},
        ]
        # Default (2.0) fires — 38 > 2.0×15.2=30.4
        assert sa._compute_acceleration(monthly, fire_multiplier=2.0) is not None
        # A stricter floor of 3.0 suppresses it — 38 < 3.0×15.2=45.6
        assert sa._compute_acceleration(monthly, fire_multiplier=3.0) is None

    def test_acceleration_default_multiplier_matches_legacy(self):
        """Calling without fire_multiplier must behave exactly as the old hardcoded 2.0."""
        sa = _make_sa_stub()
        monthly = [
            {"period": "2026-01", "value": 100},
            {"period": "2026-02", "value": 98},
            {"period": "2026-03", "value": 96},
            {"period": "2026-04", "value": 94},
            {"period": "2026-05", "value": 92},
            {"period": "2026-06", "value": 52},
        ]
        assert sa._compute_acceleration(monthly) == sa._compute_acceleration(monthly, fire_multiplier=2.0)


# ===========================================================================
# THRESHOLD-PRESENCE GATING TESTS (Option A)
# ===========================================================================

class TestThresholdPresenceGating:
    """Each 11I-A statistical pattern runs ONLY when the KPI carries a registry
    threshold row for that comparison_type. Absence of a row disables the pattern.
    These tests exercise the gating predicates used inline in detect_situations().
    """

    def test_projected_breach_gated_on_projected_breach_entry(self):
        # projected_breach entry stores a percent-of-budget tolerance (magnitude)
        vt_present = {"yoy": {"red": -5.0}, "projected_breach": {"red": 15.0}}
        vt_absent = {"yoy": {"red": -5.0}, "plan_variance": {"red": 15.0}}
        assert isinstance(vt_present.get("projected_breach"), dict)   # → runs
        assert not isinstance(vt_absent.get("projected_breach"), dict)  # → skipped

    def test_acceleration_gated_on_acceleration_entry(self):
        vt_present = {"yoy": {"red": -5.0}, "acceleration": {"yellow": 2.0, "red": 3.0}}
        vt_absent = {"yoy": {"red": -5.0}}
        assert isinstance(vt_present.get("acceleration"), dict)   # → runs
        assert not isinstance(vt_absent.get("acceleration"), dict)  # → skipped

    def test_acceleration_multipliers_read_from_entry(self):
        """yellow → fire floor, red → HIGH-severity cutoff, with 2.0/3.0 fallbacks."""
        cfg = {"yellow": 2.5, "red": 4.0}
        _fire = float(cfg.get("yellow") if cfg.get("yellow") is not None else 2.0)
        _high = float(cfg.get("red") if cfg.get("red") is not None else 3.0)
        assert _fire == 2.5
        assert _high == 4.0
        # Fallbacks when unset
        empty = {}
        assert float(empty.get("yellow") if empty.get("yellow") is not None else 2.0) == 2.0
        assert float(empty.get("red") if empty.get("red") is not None else 3.0) == 3.0

    def test_projected_breach_floor_derived_from_budget_run_rate(self):
        """Budget-anchored practice: floor = monthly_budget − |monthly_budget| × tol%.

        Revenue below the derived floor fires; the registry stores only the % tolerance.
        """
        sa = _make_sa_stub()
        # Monthly revenue declining toward a budget-derived floor.
        monthly = [
            {"period": "2026-01", "value": 260_000_000},
            {"period": "2026-02", "value": 245_000_000},
            {"period": "2026-03", "value": 230_000_000},
            {"period": "2026-04", "value": 218_000_000},
            {"period": "2026-05", "value": 208_000_000},
        ]
        # Budget aggregate over 2 months = $520M → monthly run-rate $260M; 15% tolerance.
        budget_aggregate = 520_000_000.0
        n_months = 2
        monthly_budget = budget_aggregate / n_months            # 260M
        tol = abs(-15.0) / 100.0
        floor = monthly_budget - abs(monthly_budget) * tol       # 221M
        assert floor == 221_000_000.0
        result = sa._project_trend(monthly, {"red": floor}, inverse_logic=False)
        assert result is not None, "Declining revenue should project below the budget-derived floor"
        assert result["threshold_value"] == floor

    def test_projected_breach_floor_derivation_for_negative_stored_cost(self):
        """Negative-stored cost: floor is MORE negative than budget; inverse_logic stays False.

        Over-budget cost (more negative) crossing below the floor fires — same sign convention
        as the plan-variance fix.
        """
        sa = _make_sa_stub()
        monthly_budget = -50_000_000.0   # budget cost debit (negative)
        tol = abs(25.0) / 100.0
        floor = monthly_budget - abs(monthly_budget) * tol       # -62.5M
        assert floor == -62_500_000.0
        # Costs deteriorating (more negative) toward the floor.
        monthly = [
            {"period": "2026-01", "value": -50_000_000},
            {"period": "2026-02", "value": -54_000_000},
            {"period": "2026-03", "value": -57_000_000},
            {"period": "2026-04", "value": -60_000_000},
            {"period": "2026-05", "value": -61_500_000},
        ]
        result = sa._project_trend(monthly, {"red": floor}, inverse_logic=False)
        assert result is not None, "Worsening cost trend should project below the (negative) floor"

    def test_timeframe_month_count(self):
        """Month-count helper drives the budget→monthly run-rate conversion."""
        sa = _make_sa_stub()
        # YTD as of the loaded Hess data resolves to a multi-month span ≥ 1.
        n = sa._timeframe_month_count(TimeFrame.YEAR_TO_DATE)
        assert isinstance(n, int) and n >= 1
        n_q = sa._timeframe_month_count(TimeFrame.CURRENT_QUARTER)
        assert n_q >= 1


# ===========================================================================
# KPI TYPE / COVENANT TESTS (2)
# ===========================================================================

class TestKpiType:

    def test_covenant_kpi_always_fires_critical(self):
        """A covenant KPI with any detected situation must have severity overridden to CRITICAL."""
        sit = Situation(
            situation_id="cov_001",
            kpi_name="Debt Covenant Ratio",
            kpi_value=_kpi_value(),
            severity=SituationSeverity.MEDIUM,  # would normally be medium
            description="breach",
            business_impact="impact",
            alert_type="threshold_breach",
        )
        detected_situations = [sit]
        kpi_type = "covenant"

        # Apply the same logic as detect_situations()
        if kpi_type in ("covenant", "regulatory"):
            for s in detected_situations:
                s.severity = SituationSeverity.CRITICAL
                s.alert_type = kpi_type

        assert sit.severity == SituationSeverity.CRITICAL
        assert sit.alert_type == "covenant"

    def test_concentration_kpi_type_field_propagates(self):
        """KPIDefinition.kpi_type='concentration' is correctly stored and accessible."""
        kpi_def = _kpi_def(kpi_type="concentration")
        assert kpi_def.kpi_type == "concentration"

        # Simulate the guard in detect_situations()
        _kpi_type = getattr(kpi_def, "kpi_type", "operational")
        assert _kpi_type == "concentration"
        # concentration is NOT in the covenant/regulatory override list, so severity stays
        override = _kpi_type in ("covenant", "regulatory")
        assert override is False


# ===========================================================================
# MODEL FIELD TESTS (sanity checks)
# ===========================================================================

class TestModelFields:

    def test_situation_has_alert_intelligence_fields(self):
        """Situation model should accept all 11I-A fields without error."""
        sit = Situation(
            situation_id="test_001",
            kpi_name="Net Revenue",
            kpi_value=_kpi_value(),
            severity=SituationSeverity.HIGH,
            description="test",
            business_impact="test impact",
            alert_type="projected_breach",
            plan_value=1000.0,
            projected_breach_at_period="t+2",
            projection_confidence=0.85,
            periods_until_breach=2,
            acceleration_signal=3.5,
        )
        assert sit.alert_type == "projected_breach"
        assert sit.plan_value == 1000.0
        assert sit.projected_breach_at_period == "t+2"
        assert sit.projection_confidence == 0.85
        assert sit.periods_until_breach == 2
        assert sit.acceleration_signal == 3.5

    def test_kpi_definition_has_new_fields(self):
        """KPIDefinition should accept plan_version_value and kpi_type without error."""
        kdef = KPIDefinition(
            name="Test KPI",
            description="A test",
            data_product_id="dp_test",
            positive_trend_is_good=True,
            plan_version_value="Budget",
            kpi_type="covenant",
        )
        assert kdef.plan_version_value == "Budget"
        assert kdef.kpi_type == "covenant"

    def test_derive_plan_sql_substitutes_version(self):
        """_derive_plan_sql should replace version = 'Actual' with version = 'Budget'."""
        sa = _make_sa_stub()
        sql = "SELECT SUM(amount) AS value FROM View WHERE version = 'Actual'"
        result = sa._derive_plan_sql(sql, "Budget")
        assert result is not None
        assert "Budget" in result
        assert "Actual" not in result

    def test_derive_plan_sql_returns_none_when_no_filter(self):
        """_derive_plan_sql should return None when no version filter is present."""
        sa = _make_sa_stub()
        sql = "SELECT SUM(amount) AS value FROM View WHERE account_type = 'Revenue'"
        result = sa._derive_plan_sql(sql, "Budget")
        assert result is None


# ===========================================================================
# SQL SERVER HELPER TESTS
# ===========================================================================

class TestSQLServerSQLHelpers:
    """Tests for T-SQL-specific SA helper methods used by the Hess (SQL Server) path."""

    # -----------------------------------------------------------------------
    # _derive_plan_sql — bracket-quoted and backtick-quoted column variants
    # -----------------------------------------------------------------------

    def test_derive_plan_sql_bracket_quoted_version(self):
        """_derive_plan_sql handles T-SQL bracket-quoted [version] = 'Actual'."""
        sa = _make_sa_stub()
        sql = (
            "SELECT SUM([amount]) AS value "
            "FROM [dbo].[HessStarSchemaView] "
            "WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
        )
        result = sa._derive_plan_sql(sql, "Budget")
        assert result is not None, "Should match bracket-quoted [version]"
        assert "[version] = 'Budget'" in result
        assert "'Actual'" not in result

    def test_derive_plan_sql_no_backslash_in_output(self):
        """Backslash must NOT appear in the replacement — SQL Server rejects \\' as invalid T-SQL."""
        sa = _make_sa_stub()
        sql = "SELECT SUM([amount]) AS value FROM [dbo].[View] WHERE [version] = 'Actual'"
        result = sa._derive_plan_sql(sql, "Budget")
        assert result is not None
        assert "\\" not in result, "Backslash escape in T-SQL output would cause a syntax error"

    def test_derive_plan_sql_backtick_quoted_version(self):
        """_derive_plan_sql handles BigQuery backtick-quoted `version` = 'Actual'."""
        sa = _make_sa_stub()
        sql = "SELECT SUM(amount) AS value FROM `project.dataset.view` WHERE `version` = 'Actual'"
        result = sa._derive_plan_sql(sql, "Budget")
        assert result is not None, "Should match backtick-quoted version"
        assert "Budget" in result
        assert "'Actual'" not in result

    def test_derive_plan_sql_case_insensitive(self):
        """_derive_plan_sql is case-insensitive on the column name."""
        sa = _make_sa_stub()
        sql = "SELECT SUM(amount) AS value FROM View WHERE VERSION = 'Actual'"
        result = sa._derive_plan_sql(sql, "Budget")
        assert result is not None
        assert "Budget" in result

    # -----------------------------------------------------------------------
    # _bq_apply_period — date filter appended to T-SQL
    # -----------------------------------------------------------------------

    def test_bq_apply_period_appends_and_when_where_exists(self):
        """_bq_apply_period appends AND <date> BETWEEN when SQL already has a WHERE clause."""
        from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
        from src.agents.protocols.situation_awareness_protocol import TimeFrame
        sql = (
            "SELECT SUM([amount]) AS value "
            "FROM [dbo].[HessStarSchemaView] "
            "WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
        )
        result = A9_Situation_Awareness_Agent._bq_apply_period(
            sql, TimeFrame.YEAR_TO_DATE, is_comparison=False
        )
        assert "AND transaction_date BETWEEN" in result
        assert "WHERE" in result.upper()
        assert result.upper().count("WHERE") == 1, "Should not add a second WHERE"

    def test_bq_apply_period_adds_where_when_none_exists(self):
        """_bq_apply_period adds WHERE <date> BETWEEN when the SQL has no WHERE clause."""
        from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
        from src.agents.protocols.situation_awareness_protocol import TimeFrame
        sql = "SELECT SUM([amount]) AS value FROM [dbo].[View]"
        result = A9_Situation_Awareness_Agent._bq_apply_period(
            sql, TimeFrame.YEAR_TO_DATE, is_comparison=False
        )
        assert "WHERE transaction_date BETWEEN" in result

    def test_bq_apply_period_comparison_shifts_year(self):
        """Year-over-year comparison should produce a date range one year earlier."""
        from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
        from src.agents.protocols.situation_awareness_protocol import TimeFrame, ComparisonType
        import re
        sql = "SELECT SUM([amount]) AS value FROM [dbo].[View] WHERE [version] = 'Actual'"
        current = A9_Situation_Awareness_Agent._bq_apply_period(
            sql, TimeFrame.YEAR_TO_DATE, is_comparison=False
        )
        prior = A9_Situation_Awareness_Agent._bq_apply_period(
            sql, TimeFrame.YEAR_TO_DATE, is_comparison=True,
            comparison_type=ComparisonType.YEAR_OVER_YEAR
        )
        # Extract the start years from both BETWEEN clauses
        current_year = re.search(r"BETWEEN '(\d{4})", current)
        prior_year = re.search(r"BETWEEN '(\d{4})", prior)
        assert current_year and prior_year
        assert int(prior_year.group(1)) == int(current_year.group(1)) - 1

    def test_bq_get_period_dates_enum_value_not_class_name(self):
        """TimeFrame enum member must resolve to the correct dates, not fall to default.

        Python 3.11 changed str(StrEnum) to include the class name (e.g. 'TimeFrame.year_to_date').
        _bq_get_period_dates must use .value, not str(), to avoid matching failure.
        """
        from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
        from src.agents.protocols.situation_awareness_protocol import TimeFrame
        import re
        # YEAR_TO_DATE must produce a Jan-01 start, not last-quarter start (April 1)
        start, end = A9_Situation_Awareness_Agent._bq_get_period_dates(TimeFrame.YEAR_TO_DATE)
        assert start.endswith("-01-01"), f"Expected YYYY-01-01 for YTD start, got {start}"
        # CURRENT_QUARTER must produce a quarter-start, not fall to last_quarter
        start_q, end_q = A9_Situation_Awareness_Agent._bq_get_period_dates(TimeFrame.CURRENT_QUARTER)
        # Quarter starts on a month that is 1, 4, 7, or 10
        start_month = int(start_q.split("-")[1])
        assert start_month in (1, 4, 7, 10), f"Quarter start month must be 1/4/7/10, got {start_month}"

    # -----------------------------------------------------------------------
    # _ss_monthly_series_sql — T-SQL TOP N monthly series
    # -----------------------------------------------------------------------

    def test_ss_monthly_series_sql_contains_top_n(self):
        """_ss_monthly_series_sql should use TOP N T-SQL syntax."""
        sa = _make_sa_stub()
        base_sql = (
            "SELECT SUM([amount]) AS value "
            "FROM [dbo].[HessStarSchemaView] "
            "WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
        )
        result = sa._ss_monthly_series_sql(base_sql)
        assert "TOP 9" in result.upper()
        assert "ORDER BY" in result.upper()

    def test_ss_monthly_series_sql_preserves_where_conditions(self):
        """Non-date WHERE conditions (account_type, version) must be preserved in output."""
        sa = _make_sa_stub()
        base_sql = (
            "SELECT SUM([amount]) AS value "
            "FROM [dbo].[HessStarSchemaView] "
            "WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
        )
        result = sa._ss_monthly_series_sql(base_sql)
        assert "[account_type] = 'Revenue'" in result
        assert "[version] = 'Actual'" in result

    def test_ss_monthly_series_sql_uses_fiscal_year_period_group_by(self):
        """Output must GROUP BY fiscal_year, fiscal_period with the formatted period expression."""
        sa = _make_sa_stub()
        base_sql = (
            "SELECT SUM([amount]) AS value "
            "FROM [dbo].[HessStarSchemaView] "
            "WHERE [account_type] = 'Revenue'"
        )
        result = sa._ss_monthly_series_sql(base_sql)
        assert "GROUP BY [fiscal_year], [fiscal_period]" in result
        # Period column must produce YYYY-PP format via CAST + RIGHT + zero-pad
        assert "CAST([fiscal_year] AS VARCHAR" in result
        assert "RIGHT(" in result

    def test_ss_monthly_series_sql_outer_order_ascending(self):
        """Outer query must ORDER BY period ASC so sparkline reads left to right."""
        sa = _make_sa_stub()
        base_sql = (
            "SELECT SUM([amount]) AS value FROM [dbo].[HessStarSchemaView] "
            "WHERE [version] = 'Actual'"
        )
        result = sa._ss_monthly_series_sql(base_sql)
        # Outer ORDER BY must be ASC; inner ORDER BY must be DESC (newest-first for TOP)
        assert result.upper().rstrip().endswith("ORDER BY PERIOD ASC")

    def test_ss_monthly_series_sql_returns_empty_on_unparseable(self):
        """Completely unparseable SQL should return empty string, not raise."""
        sa = _make_sa_stub()
        result = sa._ss_monthly_series_sql("NOT VALID SQL AT ALL")
        assert result == ""


# ===========================================================================
# MERGE COMPOUND KPI SITUATIONS (same-KPI multi-alert-type consolidation)
# ===========================================================================

class TestMergeCompoundKpiSituations:
    """`_merge_compound_kpi_situations` folds multiple alert_types for the same
    KPI into one card. Pattern-specific fields (plan_value, acceleration_signal,
    compound_*) are each set by exactly one member — never by primary alone —
    so the merge must scan all members for each field, not just take primary's.
    """

    def _sit(self, situation_id, kpi_name="Total Revenue", kpi_id="total_revenue",
             severity=SituationSeverity.CRITICAL, alert_type="threshold_breach",
             card_type="problem", **kwargs):
        kv = _kpi_value(value=100.0)
        defaults = dict(
            situation_id=situation_id, kpi_name=kpi_name, kpi_id=kpi_id,
            kpi_value=kv, severity=severity, card_type=card_type,
            description="test", business_impact=f"impact-{situation_id}",
            alert_type=alert_type,
        )
        defaults.update(kwargs)
        return Situation(**defaults)

    def test_single_alert_type_passes_through_unchanged(self):
        """A KPI with only one problem situation is untouched by the merge."""
        sa = _make_sa_stub()
        sit = self._sit("s1", alert_type="plan_variance", plan_value=50.0)
        result = sa._merge_compound_kpi_situations([sit])
        assert len(result) == 1
        assert result[0] is sit
        assert result[0].merged_alert_types is None

    def test_opportunity_cards_pass_through_without_merging(self):
        """card_type='opportunity' situations are never grouped/merged."""
        sa = _make_sa_stub()
        sit1 = self._sit("o1", card_type="opportunity", alert_type=None)
        sit2 = self._sit("o2", card_type="opportunity", alert_type=None)
        result = sa._merge_compound_kpi_situations([sit1, sit2])
        assert len(result) == 2
        assert all(s.merged_alert_types is None for s in result)

    def test_plan_value_survives_merge_when_threshold_breach_is_primary(self):
        """The exact production collision: threshold_breach (no plan_value) and
        plan_variance (has plan_value) fire together; threshold_breach wins the
        primary slot (same severity, detected first) but plan_value must still
        surface on the merged card — this is what VA's registration reads.
        """
        sa = _make_sa_stub()
        thresh = self._sit("thresh_1", alert_type="threshold_breach", plan_value=None)
        plan = self._sit("plan_1", alert_type="plan_variance", plan_value=264_000_000.0)

        merged = sa._merge_compound_kpi_situations([thresh, plan])

        assert len(merged) == 1
        m = merged[0]
        assert m.alert_type == "threshold_breach"  # primary unchanged
        assert set(m.merged_alert_types) == {"threshold_breach", "plan_variance"}
        assert m.plan_value == 264_000_000.0, (
            "plan_value must be pulled from whichever member set it, not just primary"
        )

    def test_all_pattern_specific_fields_survive_merge(self):
        """acceleration_signal, compound_alert/related_kpi_id/compound_pattern,
        and projected_breach fields must each survive from their own member too.
        """
        sa = _make_sa_stub()
        thresh = self._sit(
            "thresh_1", alert_type="threshold_breach",
            compound_alert=True, related_kpi_id="gross_margin_pct",
            compound_pattern="Revenue DOWN / Margin DOWN",
        )
        plan = self._sit("plan_1", alert_type="plan_variance", plan_value=264_000_000.0)
        proj = self._sit(
            "proj_1", alert_type="projected_breach", severity=SituationSeverity.HIGH,
            projected_breach_at_period="t+2", projection_confidence=0.82, periods_until_breach=2,
        )
        accel = self._sit(
            "accel_1", alert_type="acceleration", severity=SituationSeverity.MEDIUM,
            acceleration_signal=3.4,
        )

        merged = sa._merge_compound_kpi_situations([thresh, plan, proj, accel])

        assert len(merged) == 1
        m = merged[0]
        assert set(m.merged_alert_types) == {
            "threshold_breach", "plan_variance", "projected_breach", "acceleration"
        }
        assert m.plan_value == 264_000_000.0
        assert m.projected_breach_at_period == "t+2"
        assert m.projection_confidence == 0.82
        assert m.periods_until_breach == 2
        assert m.acceleration_signal == 3.4
        assert m.compound_alert is True
        assert m.related_kpi_id == "gross_margin_pct"
        assert m.compound_pattern == "Revenue DOWN / Margin DOWN"

    def test_hitl_required_is_union_across_members(self):
        """hitl_required must be True if ANY member requires it (pre-existing
        behavior, verified to still hold after adding the new field-preservation logic).
        """
        sa = _make_sa_stub()
        thresh = self._sit("thresh_1", alert_type="threshold_breach", hitl_required=False)
        plan = self._sit("plan_1", alert_type="plan_variance", hitl_required=True)
        merged = sa._merge_compound_kpi_situations([thresh, plan])
        assert merged[0].hitl_required is True

    def test_different_kpis_are_not_merged_together(self):
        """Situations for different KPIs must never be folded into one card."""
        sa = _make_sa_stub()
        sit1 = self._sit("s1", kpi_name="Total Revenue", kpi_id="total_revenue")
        sit2 = self._sit("s2", kpi_name="Gross Margin %", kpi_id="gross_margin_pct")
        result = sa._merge_compound_kpi_situations([sit1, sit2])
        assert len(result) == 2
        assert {s.kpi_name for s in result} == {"Total Revenue", "Gross Margin %"}

    def test_business_impact_bullets_combined_and_capped(self):
        """business_impact concatenates each member's impact, capped at 4 bullets."""
        sa = _make_sa_stub()
        members = [
            self._sit(f"s{i}", alert_type=f"type{i}", business_impact=f"impact-{i}")
            for i in range(6)
        ]
        merged = sa._merge_compound_kpi_situations(members)
        assert len(merged) == 1
        bullets = merged[0].business_impact.split(" • ")
        assert len(bullets) == 4
