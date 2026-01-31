import pytest
import asyncio
import logging
import sys
import os
from typing import Dict, Any
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.models.situation_awareness_models import (
    SituationDetectionRequest, 
    SituationDetectionResponse, 
    Situation, 
    SituationSeverity,
    KPIValue,
    TimeFrame,
    PrincipalContext
)
from src.agents.models.deep_analysis_models import (
    DeepAnalysisRequest,
    DeepAnalysisResponse,
    DeepAnalysisPlan,
    ChangePoint
)
from src.agents.models.solution_finder_models import (
    SolutionFinderRequest,
    SolutionFinderResponse,
    SolutionOption
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_e2e_workflow_chain():
    """
    End-to-End Integration Test simulating the full workflow:
    Situation Awareness -> Deep Analysis -> Solution Finder
    via the Orchestrator.
    """
    logger.info("Starting E2E Workflow Chain Test")
    
    # 1. Initialize Orchestrator
    orchestrator = await A9_Orchestrator_Agent.create()
    
    # --- MOCKING AGENTS ---
    
    # Mock SA Agent
    mock_sa = AsyncMock()
    mock_situation = Situation(
        situation_id="sit_e2e_001",
        kpi_name="Gross Margin",
        kpi_value=KPIValue(
            kpi_name="Gross Margin",
            value=0.25,
            timeframe=TimeFrame.CURRENT_QUARTER,
            dimensions={"Region": "North America"}
        ),
        severity=SituationSeverity.HIGH,
        description="Gross Margin dropped by 10% in North America vs previous quarter.",
        business_impact="Profitability risk"
    )
    mock_sa_response = SituationDetectionResponse(
        request_id="req_sa_e2e",
        status="success",
        situations=[mock_situation]
    )
    mock_sa.detect_situations.return_value = mock_sa_response
    await orchestrator.register_agent("A9_Situation_Awareness_Agent", mock_sa)
    
    # Mock DA Agent
    mock_da = AsyncMock()
    mock_da_plan = DeepAnalysisPlan(kpi_name="Gross Margin", dimensions=["Region", "Product"])
    
    # DA Plan Response
    mock_da.plan_deep_analysis.return_value = DeepAnalysisResponse(
        request_id="req_da_plan_e2e",
        status="success",
        plan=mock_da_plan
    )
    
    # DA Execute Response
    mock_da_exec_response = DeepAnalysisResponse(
        request_id="req_da_exec_e2e",
        status="success",
        plan=mock_da_plan,
        scqa_summary="Gross Margin dropped due to increased raw material costs in North America.",
        change_points=[
            ChangePoint(
                dimension="Region", 
                key="North America", 
                current_value=0.25, 
                previous_value=0.35, 
                delta=-0.10
            )
        ]
    )
    mock_da.execute_deep_analysis.return_value = mock_da_exec_response
    await orchestrator.register_agent("A9_Deep_Analysis_Agent", mock_da)
    
    # Mock SF Agent
    mock_sf = AsyncMock()
    mock_sf_response = SolutionFinderResponse(
        request_id="req_sf_e2e",
        status="success",
        options_ranked=[
            SolutionOption(
                id="opt_1",
                title="Renegotiate Supplier Contracts",
                description="Reduce COGS by renegotiating with NA suppliers.",
                expected_impact=0.05
            )
        ]
    )
    mock_sf.recommend_actions.return_value = mock_sf_response
    await orchestrator.register_agent("A9_Solution_Finder_Agent", mock_sf)
    
    # --- EXECUTION ---
    
    # Step 1: Situation Awareness
    logger.info("Step 1: Executing Situation Awareness")
    sa_req = SituationDetectionRequest(
        request_id="req_sa_e2e",
        principal_context=PrincipalContext(
            role="CFO",
            principal_id="user_e2e",
            business_processes=[],
            default_filters={},
            decision_style="analytical",
            communication_style="concise",
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER]
        ),
        business_processes=[],
        timeframe=TimeFrame.CURRENT_QUARTER
    )
    
    sa_result = await orchestrator.orchestrate_situation_detection(sa_req)
    assert sa_result["status"] == "success"
    assert len(sa_result["situations"]) == 1
    situation = sa_result["situations"][0]
    
    # Step 2: Deep Analysis (triggered from Situation)
    logger.info(f"Step 2: Executing Deep Analysis for {situation.kpi_name}")
    
    da_req = DeepAnalysisRequest(
        request_id="req_da_e2e",
        principal_id="user_e2e",
        kpi_name=situation.kpi_name,
        timeframe=situation.kpi_value.timeframe.value,
        filters=situation.kpi_value.dimensions
    )
    
    da_result = await orchestrator.orchestrate_deep_analysis(da_req)
    assert da_result.status == "success"
    assert da_result.scqa_summary is not None
    
    # Step 3: Solution Finder (triggered from Analysis)
    logger.info("Step 3: Executing Solution Finder")
    
    sf_req = SolutionFinderRequest(
        request_id="req_sf_e2e",
        principal_id="user_e2e",
        problem_statement=da_result.scqa_summary,
        deep_analysis_output=da_result.model_dump(),
        constraints={"budget": "low"}
    )
    
    sf_result = await orchestrator.orchestrate_solution_finding(sf_req)
    assert sf_result.status == "success"
    assert len(sf_result.options_ranked) > 0
    assert sf_result.options_ranked[0].title == "Renegotiate Supplier Contracts"
    
    logger.info("✅ End-to-End Workflow Verification Successful")

if __name__ == "__main__":
    asyncio.run(test_e2e_workflow_chain())
