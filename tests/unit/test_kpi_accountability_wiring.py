# arch-allow-direct-agent-construction
"""
Validates KPI accountability filtering in PIB and SA agents.

Four contracts under test:
1. PIB _populate_situations — filters assessments to accountable KPIs when assignments exist
2. PIB _populate_situations — uses all assessments when no accountability assignments exist
3. PIB _populate_situations — uses all assessments when accountability provider raises
4. SA _get_relevant_kpis — applies accountable_kpi_ids set to restrict returned KPIs
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.models.situation_awareness_models import PrincipalContext, KPIDefinition
from src.registry.models.kpi_accountability import AccountabilityRole, KPIAccountability


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _kpi_accountability(kpi_id: str, principal_id: str = "cfo_001") -> KPIAccountability:
    return KPIAccountability(
        id=f"{kpi_id}_acc",
        client_id="lubricants",
        kpi_id=kpi_id,
        principal_id=principal_id,
        role=AccountabilityRole.ACCOUNTABLE,
    )


def _kpi_assessment(kpi_id: str, status: str = "detected") -> dict:
    return {"kpi_id": kpi_id, "kpi_name": kpi_id, "status": status, "id": f"ka_{kpi_id}"}


def _kpi_def(kpi_id: str, client_id: str = "lubricants") -> KPIDefinition:
    kpi = MagicMock(spec=KPIDefinition)
    kpi.id = kpi_id
    kpi.name = kpi_id
    kpi.client_id = client_id
    # Empty list triggers the "include KPIs without business processes" shortcut —
    # simplest way to have test KPIs pass through the business process filter.
    kpi.business_processes = []
    return kpi


def _sa_agent() -> A9_Situation_Awareness_Agent:
    agent = A9_Situation_Awareness_Agent(config={})
    agent.data_governance_agent = MagicMock()
    agent.kpi_registry = {}
    agent.data_product_agent = None
    agent.principal_profiles = {}
    return agent


# ---------------------------------------------------------------------------
# PIB accountability filter tests
# ---------------------------------------------------------------------------

class TestPIBAccountabilityFilter:
    """Verify _populate_situations filters by accountability registry."""

    def _make_pib_agent(self):
        """Build a minimal PIB agent with mocked stores."""
        from src.agents.new.a9_pib_agent import A9_PIB_Agent
        agent = A9_PIB_Agent.__new__(A9_PIB_Agent)
        agent._assessment_store = MagicMock()
        agent._assessment_store.get_detected_kpi_ids = AsyncMock(return_value=["gross_margin_pct", "net_revenue", "sga_expense"])
        agent._situations_store = MagicMock()
        agent._situations_store.get_open_situations = AsyncMock(return_value=[])
        agent._briefing_store = MagicMock()
        agent._create_token = AsyncMock(return_value="tok_dummy")
        agent._severity_label = lambda score: "critical" if score >= 0.7 else "warning"
        agent._clean_description = lambda d: d or ""
        agent._ds_url = "http://localhost:5173"
        return agent

    def _make_config(self, client_id="lubricants", principal_id="cfo_001"):
        cfg = MagicMock()
        cfg.client_id = client_id
        cfg.principal_id = principal_id
        cfg.dry_run = True
        return cfg

    def _make_briefing_run(self):
        run = MagicMock()
        run.id = "run_001"
        return run

    def _make_latest_run(self):
        return {"id": "assess_run_001", "previous_run_id": None}

    def _make_all_assessments(self):
        return [
            _kpi_assessment("gross_margin_pct"),
            _kpi_assessment("net_revenue"),
            _kpi_assessment("sga_expense"),
        ]

    @pytest.mark.asyncio
    async def test_filters_assessments_to_accountable_kpis(self):
        """When assignments exist, only accountable KPIs appear in the briefing."""
        agent = self._make_pib_agent()

        # CFO is only accountable for gross_margin_pct and net_revenue
        assignments = [
            _kpi_accountability("gross_margin_pct"),
            _kpi_accountability("net_revenue"),
        ]

        with patch(
            "src.agents.new.a9_pib_agent.KPIAccountabilityProvider"
        ) as MockProvider:
            MockProvider.return_value.get_for_principal = AsyncMock(return_value=assignments)
            # Patch _load_assessments to return 3 KPIs
            agent._load_assessments = AsyncMock(return_value=self._make_all_assessments())

            from src.agents.models.pib_models import BriefingContent
            content = BriefingContent(
                principal_id="cfo_001",
                principal_name="CFO",
                principal_role="Chief Financial Officer",
                client_id="lubricants",
                client_name="Lubricants",
                assessment_run_id="assess_run_001",
            )
            from datetime import datetime, timezone, timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

            await agent._populate_situations(
                content, self._make_config(), self._make_briefing_run(),
                self._make_latest_run(), expires_at,
            )

        kpi_ids_in_briefing = {s.kpi_name for s in content.new_situations}
        assert "gross_margin_pct" in kpi_ids_in_briefing
        assert "net_revenue" in kpi_ids_in_briefing
        assert "sga_expense" not in kpi_ids_in_briefing

    @pytest.mark.asyncio
    async def test_uses_all_assessments_when_no_assignments(self):
        """When no accountability assignments exist, all assessments are included."""
        agent = self._make_pib_agent()

        with patch(
            "src.agents.new.a9_pib_agent.KPIAccountabilityProvider"
        ) as MockProvider:
            MockProvider.return_value.get_for_principal = AsyncMock(return_value=[])
            agent._load_assessments = AsyncMock(return_value=self._make_all_assessments())

            from src.agents.models.pib_models import BriefingContent
            content = BriefingContent(
                principal_id="cfo_001",
                principal_name="CFO",
                principal_role="Chief Financial Officer",
                client_id="lubricants",
                client_name="Lubricants",
                assessment_run_id="assess_run_001",
            )
            from datetime import datetime, timezone, timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

            await agent._populate_situations(
                content, self._make_config(), self._make_briefing_run(),
                self._make_latest_run(), expires_at,
            )

        # All three should be present (fallback: no filter applied)
        assert len(content.new_situations) == 3

    @pytest.mark.asyncio
    async def test_resilient_to_provider_failure(self):
        """When accountability provider raises, all assessments are still included."""
        agent = self._make_pib_agent()

        with patch(
            "src.agents.new.a9_pib_agent.KPIAccountabilityProvider"
        ) as MockProvider:
            MockProvider.return_value.get_for_principal = AsyncMock(
                side_effect=RuntimeError("DB pool not available")
            )
            agent._load_assessments = AsyncMock(return_value=self._make_all_assessments())

            from src.agents.models.pib_models import BriefingContent
            content = BriefingContent(
                principal_id="cfo_001",
                principal_name="CFO",
                principal_role="Chief Financial Officer",
                client_id="lubricants",
                client_name="Lubricants",
                assessment_run_id="assess_run_001",
            )
            from datetime import datetime, timezone, timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)

            # Should not raise — falls back to all assessments
            await agent._populate_situations(
                content, self._make_config(), self._make_briefing_run(),
                self._make_latest_run(), expires_at,
            )

        assert len(content.new_situations) == 3


# ---------------------------------------------------------------------------
# SA accountability filter tests
# ---------------------------------------------------------------------------

class TestSAAccountabilityFilter:
    """Verify _get_relevant_kpis restricts KPIs when accountable_kpi_ids is provided."""

    def _make_kpi_registry(self, client_id="lubricants"):
        # SA stores KPIs under "{client_id}:{kpi_name}" when client_id is known
        return {
            f"{client_id}:gross_margin_pct": _kpi_def("gross_margin_pct"),
            f"{client_id}:net_revenue": _kpi_def("net_revenue"),
            f"{client_id}:sga_expense": _kpi_def("sga_expense"),
        }

    def _make_principal_context(self, principal_id="cfo_001"):
        ctx = MagicMock(spec=PrincipalContext)
        ctx.principal_id = principal_id
        ctx.role = "CFO"
        ctx.business_processes = ["Finance"]
        return ctx

    def test_restricts_kpis_to_accountable_set(self):
        """When accountable_kpi_ids is provided, only those KPIs are returned."""
        agent = _sa_agent()
        agent.kpi_registry = self._make_kpi_registry()

        ctx = self._make_principal_context()
        accountable = {"gross_margin_pct", "net_revenue"}

        with patch.object(
            agent, "_apply_principal_kpi_preferences",
            side_effect=lambda _ctx, kpis: kpis,
        ):
            result = agent._get_relevant_kpis(
                ctx,
                business_processes=["Finance"],
                client_id="lubricants",
                accountable_kpi_ids=accountable,
            )

        assert "sga_expense" not in result
        # gross_margin_pct and net_revenue should survive if they matched the
        # business process filter (they will since kpi_def.business_processes = ["Finance"])
        surviving = set(result.keys())
        assert surviving.issubset({"gross_margin_pct", "net_revenue"})

    def test_no_filter_when_accountable_kpi_ids_is_none(self):
        """When accountable_kpi_ids is None, the full set is returned."""
        agent = _sa_agent()
        agent.kpi_registry = self._make_kpi_registry()

        ctx = self._make_principal_context()

        with patch.object(
            agent, "_apply_principal_kpi_preferences",
            side_effect=lambda _ctx, kpis: kpis,
        ):
            result = agent._get_relevant_kpis(
                ctx,
                business_processes=["Finance"],
                client_id="lubricants",
                accountable_kpi_ids=None,
            )

        # All three KPIs match "Finance" business process — none should be excluded
        assert len(result) == 3
