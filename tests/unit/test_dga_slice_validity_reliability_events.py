# arch-allow-direct-agent-construction
"""check_slice_validity() now emits reliability.slice_validity audit events
(docs/architecture/audit_event_system_design.md, 2026-10-02 scope extension)
-- the third pilot signal, after DA's [ROLLUP-CHECK] and SA's
detection-confidence gate.

Reuses the fixtures from test_dga_slice_validity.py (same KPI, same
_fake_dpa shape) rather than re-deriving them -- only the AuditService
assertions are new here. No live DB: AuditService.log is patched to a spy,
same convention as test_enterprise_assessment_reliability_events.py.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
from src.agents.models.data_governance_models import SliceValidityCheckRequest
from src.registry.models.kpi import KPI, KPIDimension

_MARGIN_SQL = (
    "SELECT ROUND(100.0 * SUM(CASE WHEN account_type IN ('Revenue', 'COGS') "
    "THEN amount ELSE 0 END), 2) AS value FROM `agent9-465818.LubricantsBusiness."
    "LubricantsStarSchemaView` WHERE version = 'Actual'"
)


def _kpi(**overrides) -> KPI:
    defaults = dict(
        id="gross_margin_pct",
        client_id="lubricants",
        name="Gross Margin %",
        domain="Finance",
        data_product_id="lubricants_financial_analytics",
        view_name="LubricantsStarSchemaView",
        sql_query=_MARGIN_SQL,
        dimensions=[KPIDimension(name="Customer", field="customer_name")],
    )
    defaults.update(overrides)
    return KPI(**defaults)


def _dga(*, kpi, dpa) -> A9_Data_Governance_Agent:
    agent = A9_Data_Governance_Agent(config={})
    agent.kpi_provider = MagicMock()
    agent.kpi_provider.get.return_value = kpi
    agent.kpi_provider.upsert = AsyncMock()
    agent.data_product_provider = MagicMock()
    agent.data_product_provider.get.return_value = None
    agent.data_product_agent = dpa
    return agent


def _request(**overrides) -> SliceValidityCheckRequest:
    defaults = dict(kpi_id="gross_margin_pct", client_id="lubricants", dimensions=["customer_name"])
    defaults.update(overrides)
    return SliceValidityCheckRequest(**defaults)


def _fake_dpa(counts: dict) -> MagicMock:
    """Cross-component only -- no completeness fixture, so that check is
    silently skipped and the single cross_component verdict is unambiguous
    to assert against (test_dga_slice_validity.py's _fake_dpa, trimmed)."""
    dpa = MagicMock()

    async def _execute_sql(sql, data_product_id=None, **kw):
        if "COUNT(*) AS total_rows" in sql:
            return {"success": False, "message": "no completeness fixture"}
        if "COUNT(DISTINCT customer_name)" in sql:
            return {"success": True, "rows": [{"component": c, "n": n} for c, n in counts.items()]}
        return {"success": False, "message": f"no fixture for query: {sql}"}

    dpa.execute_sql = AsyncMock(side_effect=_execute_sql)
    return dpa


@pytest.mark.asyncio
async def test_matching_coverage_emits_pass():
    agent = _dga(kpi=_kpi(), dpa=_fake_dpa({"Revenue": 10, "COGS": 10}))  # ratio 1.0 -> ok
    with patch("src.agents.new.a9_data_governance_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        resp = await agent.check_slice_validity(_request())

    assert resp.status == "success"
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["event_type"] == "reliability.slice_validity"
    assert kwargs["outcome"] == "pass"
    assert kwargs["client_id"] == "lubricants"
    assert kwargs["resource_id"] == "gross_margin_pct:customer_name"
    assert kwargs["payload"]["check_type"] == "cross_component"
    assert "reason_class" not in kwargs["payload"]


@pytest.mark.asyncio
async def test_badly_skewed_coverage_emits_fail_with_reason_class():
    agent = _dga(kpi=_kpi(), dpa=_fake_dpa({"Revenue": 20, "COGS": 1}))  # ratio 0.05 -> INVALID
    with patch("src.agents.new.a9_data_governance_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        resp = await agent.check_slice_validity(_request())

    assert resp.status == "success"
    assert resp.not_sliceable_by and resp.not_sliceable_by[0].dimension == "customer_name"
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["outcome"] == "fail"
    assert kwargs["severity"] == "warning"
    assert kwargs["payload"]["reason_class"] == "pipeline_gap"


@pytest.mark.asyncio
async def test_mild_skew_emits_abstain_not_fail():
    agent = _dga(kpi=_kpi(), dpa=_fake_dpa({"Revenue": 10, "COGS": 5}))  # ratio 0.5 -> degraded
    with patch("src.agents.new.a9_data_governance_agent.AuditService.log", new=AsyncMock(return_value=True)) as spy:
        resp = await agent.check_slice_validity(_request())

    assert resp.status == "success"
    # degraded does not deny the dimension -- not_sliceable_by only collects INVALID.
    assert resp.not_sliceable_by == []
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["outcome"] == "abstain"  # inconclusive, not a confirmed defect


@pytest.mark.asyncio
async def test_audit_failure_never_breaks_the_check():
    agent = _dga(kpi=_kpi(), dpa=_fake_dpa({"Revenue": 10, "COGS": 10}))
    with patch("src.agents.new.a9_data_governance_agent.AuditService.log", new=AsyncMock(return_value=False)):
        resp = await agent.check_slice_validity(_request())

    assert resp.status == "success"
