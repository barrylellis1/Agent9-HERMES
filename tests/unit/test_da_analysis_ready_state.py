"""The analysis is stored as soon as it is done; market research follows (owner, 2026-10-23).

Measured: market research is 19-27 s of a 22-32 s analysis run. The route now stores the analysis
in state "analysis_ready" (market research "pending") so the screen can show it, then completes
with market research "ready", or "unavailable" when it failed. A caller that only waits for
"completed" sees exactly what it saw before.
"""
import asyncio
from types import SimpleNamespace

import pytest

from src.agents.models.deep_analysis_models import DeepAnalysisResponse
from src.api.routes import workflows as wf

PRINCIPAL = {"principal_id": "cfo_001", "role": "CFO", "business_processes": ["finance"], "default_filters": {},
             "decision_style": "analytical", "communication_style": "concise", "preferred_timeframes": ["year_to_date"]}


class Orchestrator:
    def __init__(self, market_fails=False):
        self.release_market = asyncio.Event()
        self.market_started = asyncio.Event()
        self.market_fails = market_fails

    async def execute_agent_method(self, agent, method, args):
        if agent == "A9_Principal_Context_Agent":
            return {"context": PRINCIPAL}
        if agent == "A9_Market_Analysis_Agent":
            self.market_started.set()
            await self.release_market.wait()
            if self.market_fails:
                raise RuntimeError("market research failed")
            return SimpleNamespace(signals=[], conflict=None, market_shift=None, synthesis="Base oil prices eased.",
                                   confidence=0.6, sources_queried=[])
        raise AssertionError(f"unexpected call {agent}.{method}")

    async def orchestrate_deep_analysis(self, request):
        return DeepAnalysisResponse(request_id="da-1", status="success", dimensions_analyzed=["Region"])


async def _start(orch):
    rid = wf._generate_request_id("deep_analysis")
    req = wf.DeepAnalysisWorkflowRequest(principal_id="cfo_001", scope={"kpi_id": "net_revenue"})
    await wf._create_record(rid, "deep_analysis", req.model_dump())
    task = asyncio.create_task(wf._run_deep_analysis_workflow(rid, SimpleNamespace(get_orchestrator=lambda: orch), req))
    await asyncio.wait_for(orch.market_started.wait(), 5)
    return rid, task


@pytest.mark.asyncio
async def test_the_analysis_is_stored_before_market_research_finishes():
    orch = Orchestrator()
    rid, task = await _start(orch)
    rec = (await wf._get_record(rid)).to_dict()
    assert rec["state"] == "analysis_ready"
    assert rec["result"]["execution"]["dimensions_analyzed"] == ["Region"]
    assert rec["result"]["market_status"] == "pending" and rec["result"]["market_signals"] is None

    orch.release_market.set()
    await asyncio.wait_for(task, 5)
    rec = (await wf._get_record(rid)).to_dict()
    assert rec["state"] == "completed"
    assert rec["result"]["market_status"] == "ready"
    assert rec["result"]["market_synthesis"]["summary"] == "Base oil prices eased."
    assert rec["result"]["execution"]["dimensions_analyzed"] == ["Region"]


@pytest.mark.asyncio
async def test_failed_market_research_completes_as_unavailable():
    orch = Orchestrator(market_fails=True)
    rid, task = await _start(orch)
    orch.release_market.set()
    await asyncio.wait_for(task, 5)
    rec = (await wf._get_record(rid)).to_dict()
    assert rec["state"] == "completed" and rec["result"]["market_status"] == "unavailable"
