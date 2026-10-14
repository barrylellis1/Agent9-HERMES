# arch-allow-direct-agent-construction
"""A scan reports the KPIs it could not read.

Found live 2026-10-13: Apex's Snowflake key was missing, every KPI failed to read, and the
dashboard showed "0 cards", the same as a business with nothing to flag.
"""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.agents.models.situation_awareness_models import SituationDetectionResponse


def test_the_response_carries_the_unread_list_and_defaults_to_empty():
    assert "kpis_unread" in SituationDetectionResponse.model_fields
    r = SituationDetectionResponse(request_id="r", status="success", situations=[])
    assert r.kpis_unread == []


@pytest.mark.asyncio
async def test_the_orchestrator_carries_the_unread_list_and_count_through():
    from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
    from src.agents.models.situation_awareness_models import SituationDetectionResponse
    orch = A9_Orchestrator_Agent.__new__(A9_Orchestrator_Agent)
    orch.logger = __import__("logging").getLogger("t")
    sa_resp = SituationDetectionResponse(request_id="r", status="success", situations=[],
                                         kpi_evaluated_count=0, kpis_unread=["Net Revenue", "EBITDA"])
    orch.get_agent = AsyncMock(return_value=object())
    orch.execute_agent_method = AsyncMock(return_value=sa_resp)
    req = SimpleNamespace(request_id="r", principal_context=None, client_id="apex_lubricants")
    try:
        out = await orch.orchestrate_situation_detection(req)
    except Exception as exc:  # pragma: no cover - surfaced as a clear failure
        pytest.fail(f"orchestrate_situation_detection raised: {exc}")
    assert out["status"] == "success"
    assert out["kpi_evaluated_count"] == 0 and out["kpis_unread"] == ["Net Revenue", "EBITDA"]
