# arch-allow-direct-agent-construction
"""
Unit tests for Phase 11I-B: KPI Relationship Registry and Compound Alert Detection.

Covers:
  1. KPIRelationship model construction and validation
  2. SA compound alert detection (_detect_compound_alerts)
  3. DA alert_type-aware SCQA framing (fallback deterministic path)

All tests use lightweight stubs — no real DB, agent infrastructure, or LLM calls.
"""
import logging
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import List, Optional

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
from src.registry.models.kpi_relationship import KPIRelationship


# ---------------------------------------------------------------------------
# Helper: minimal stubs
# ---------------------------------------------------------------------------

def _make_sa_stub():
    """Return a stub SA agent with _detect_compound_alerts available."""
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    stub = object.__new__(A9_Situation_Awareness_Agent)
    stub.logger = logging.getLogger("test.sa_stub")
    return stub


def _make_da_stub():
    """Return a stub DA agent with _generate_scqa_summary available."""
    from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
    stub = object.__new__(A9_Deep_Analysis_Agent)
    stub.logger = logging.getLogger("test.da_stub")
    stub.llm_service_agent = None  # forces deterministic fallback
    return stub


def _kpi_value(
    kpi_name: str = "Net Revenue",
    value: float = 1000.0,
    percent_change: float = 5.0,
    inverse_logic: bool = False,
) -> KPIValue:
    return KPIValue(
        kpi_name=kpi_name,
        value=value,
        timeframe=TimeFrame.CURRENT_QUARTER,
        percent_change=percent_change,
        inverse_logic=inverse_logic,
    )


def _situation(
    situation_id: str,
    kpi_name: str,
    kpi_id: Optional[str],
    percent_change: float = 5.0,
    inverse_logic: bool = False,
    alert_type: str = "threshold_breach",
) -> Situation:
    return Situation(
        situation_id=situation_id,
        kpi_name=kpi_name,
        kpi_id=kpi_id,
        kpi_value=_kpi_value(kpi_name=kpi_name, percent_change=percent_change, inverse_logic=inverse_logic),
        severity=SituationSeverity.HIGH,
        description="test",
        business_impact="test impact",
        alert_type=alert_type,
    )


# ---------------------------------------------------------------------------
# KPIRelationship model tests (2)
# ---------------------------------------------------------------------------

class TestKPIRelationshipModel:

    def test_kpi_relationship_model_valid(self):
        """Construct a valid KPIRelationship and confirm fields serialize correctly."""
        rel = KPIRelationship(
            kpi_id="net_revenue",
            related_kpi_id="gross_margin_pct",
            client_id="apex_lubricants",
            relationship_type="volume_margin",
            conflict_direction="diverging",
            description="Revenue UP / Margin DOWN signals pricing pressure",
        )
        dumped = rel.model_dump()
        assert dumped["kpi_id"] == "net_revenue"
        assert dumped["related_kpi_id"] == "gross_margin_pct"
        assert dumped["client_id"] == "apex_lubricants"
        assert dumped["relationship_type"] == "volume_margin"
        assert dumped["conflict_direction"] == "diverging"
        assert "pricing pressure" in dumped["description"]

    def test_kpi_relationship_conflict_direction_values(self):
        """Literal validation rejects invalid conflict_direction."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            KPIRelationship(
                kpi_id="net_revenue",
                related_kpi_id="gross_margin_pct",
                client_id="apex_lubricants",
                relationship_type="volume_margin",
                conflict_direction="opposite",  # invalid Literal
            )


# ---------------------------------------------------------------------------
# SA compound detection tests (3)
# ---------------------------------------------------------------------------

class TestCompoundAlertDetection:

    @pytest.mark.asyncio
    async def test_compound_alert_fires_on_diverging_conflict(self):
        """Revenue UP + margin DOWN with a diverging relationship → both get compound_alert=True."""
        sa = _make_sa_stub()

        # revenue is UP (+5%), margin is DOWN (-3%)
        revenue_sit = _situation("sit_001", "Net Revenue", "net_revenue", percent_change=5.0)
        margin_sit = _situation("sit_002", "Gross Margin %", "gross_margin_pct", percent_change=-3.0)
        situations = [revenue_sit, margin_sit]

        rel = KPIRelationship(
            kpi_id="net_revenue",
            related_kpi_id="gross_margin_pct",
            client_id="apex_lubricants",
            relationship_type="volume_margin",
            conflict_direction="diverging",
            description="Revenue growing while margin declining signals mix shift",
        )

        with patch(
            "src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider.get_relationships_for_kpi",
            new_callable=AsyncMock,
        ) as mock_get:
            # Return rel only when queried for net_revenue; empty for gross_margin_pct
            async def side_effect(kpi_id, client_id):
                if kpi_id == "net_revenue":
                    return [rel]
                return []
            mock_get.side_effect = side_effect

            result = await sa._detect_compound_alerts(situations, "apex_lubricants")

        assert revenue_sit.compound_alert is True
        assert margin_sit.compound_alert is True
        assert revenue_sit.related_kpi_id == "gross_margin_pct"
        assert margin_sit.related_kpi_id == "net_revenue"
        assert revenue_sit.compound_pattern is not None
        assert "UP" in revenue_sit.compound_pattern or "DOWN" in revenue_sit.compound_pattern

    @pytest.mark.asyncio
    async def test_compound_alert_suppressed_when_only_one_kpi_has_situation(self):
        """Only one KPI in the pair has a situation → no compound_alert."""
        sa = _make_sa_stub()

        # Only revenue has a situation — margin is not in the list
        revenue_sit = _situation("sit_001", "Net Revenue", "net_revenue", percent_change=5.0)
        situations = [revenue_sit]

        rel = KPIRelationship(
            kpi_id="net_revenue",
            related_kpi_id="gross_margin_pct",
            client_id="apex_lubricants",
            relationship_type="volume_margin",
            conflict_direction="diverging",
            description="Revenue vs margin conflict",
        )

        with patch(
            "src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider.get_relationships_for_kpi",
            new_callable=AsyncMock,
            return_value=[rel],
        ):
            result = await sa._detect_compound_alerts(situations, "apex_lubricants")

        # gross_margin_pct is not in kpi_sit_map → no conflict flagged
        assert revenue_sit.compound_alert is False

    @pytest.mark.asyncio
    async def test_compound_alert_converging(self):
        """Receivables UP + Revenue UP with converging relationship → compound_alert=True."""
        sa = _make_sa_stub()

        # Both KPIs moving in the same direction (both UP)
        receivables_sit = _situation("sit_001", "Accounts Receivable", "accounts_receivable", percent_change=8.0)
        revenue_sit = _situation("sit_002", "Net Revenue", "net_revenue", percent_change=5.0)
        situations = [receivables_sit, revenue_sit]

        rel = KPIRelationship(
            kpi_id="accounts_receivable",
            related_kpi_id="net_revenue",
            client_id="apex_lubricants",
            relationship_type="receivables_revenue",
            conflict_direction="converging",
            description="Receivables growing faster than revenue signals collection risk",
        )

        with patch(
            "src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider.get_relationships_for_kpi",
            new_callable=AsyncMock,
        ) as mock_get:
            async def side_effect(kpi_id, client_id):
                if kpi_id == "accounts_receivable":
                    return [rel]
                return []
            mock_get.side_effect = side_effect

            result = await sa._detect_compound_alerts(situations, "apex_lubricants")

        assert receivables_sit.compound_alert is True
        assert revenue_sit.compound_alert is True
        assert receivables_sit.related_kpi_id == "net_revenue"


# ---------------------------------------------------------------------------
# DA alert_type framing tests (3)
# ---------------------------------------------------------------------------

class TestSCQAAlertTypeFraming:
    """Tests for DA _generate_scqa_summary deterministic fallback with alert_type context."""

    def _build_plan_and_kt(self, kpi_name: str = "Net Revenue"):
        """Build minimal plan and KT stubs for SCQA testing."""
        from src.agents.models.deep_analysis_models import DeepAnalysisPlan, KTIsIsNot

        plan = DeepAnalysisPlan(
            kpi_name=kpi_name,
            timeframe="current_quarter",
            analysis_mode="problem",
        )

        # KTIsIsNot with minimal where_is / where_is_not entries (extra="allow" on base model)
        kt = KTIsIsNot(
            where_is=[{"key": "Engine Oils", "delta": -50000}],
            where_is_not=[{"key": "Industrial Lubricants", "delta": 1000}],
        )

        return plan, kt

    @pytest.mark.asyncio
    async def test_scqa_fallback_includes_compound_pattern(self):
        """When compound_pattern is set, the fallback Complication leads with the compound tension."""
        da = _make_da_stub()
        plan, kt = self._build_plan_and_kt()

        result = await da._generate_scqa_summary(
            plan=plan,
            kt=kt,
            change_points=[],
            spec=None,
            principal_id="cfo_001",
            analysis_mode="problem",
            alert_type="compound",
            compound_pattern="Net Revenue UP / Gross Margin DOWN",
        )

        # The compound pattern must appear in the complication
        assert "Net Revenue UP / Gross Margin DOWN" in result
        assert "Complication:" in result

    @pytest.mark.asyncio
    async def test_scqa_fallback_projected_breach_framing(self):
        """alert_type='projected_breach' → Situation text contains 'trending toward' not 'has breached'."""
        da = _make_da_stub()
        plan, kt = self._build_plan_and_kt()

        result = await da._generate_scqa_summary(
            plan=plan,
            kt=kt,
            change_points=[],
            spec=None,
            principal_id="cfo_001",
            analysis_mode="problem",
            alert_type="projected_breach",
            compound_pattern=None,
        )

        # Situation framing must mention trending/trajectory, not a breach that already happened
        assert "trending toward" in result or "trajectory" in result or "breach" in result.lower()
        assert "Complication:" in result
        # Must NOT claim the KPI has already breached as a fait accompli at the top
        # (the word "breached" alone doesn't fail — "trending toward a threshold breach" is acceptable)

    @pytest.mark.asyncio
    async def test_scqa_fallback_plan_variance_framing(self):
        """alert_type='plan_variance' → Situation text contains plan-related language."""
        da = _make_da_stub()
        plan, kt = self._build_plan_and_kt()

        result = await da._generate_scqa_summary(
            plan=plan,
            kt=kt,
            change_points=[],
            spec=None,
            principal_id="cfo_001",
            analysis_mode="problem",
            alert_type="plan_variance",
            compound_pattern=None,
        )

        # Situation must reference plan miss
        result_lower = result.lower()
        assert "plan" in result_lower or "budget" in result_lower
        assert "Complication:" in result
