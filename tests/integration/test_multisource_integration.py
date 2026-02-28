import pytest
import pytest_asyncio
import asyncio
import logging
from typing import Dict, Any, List
from unittest.mock import MagicMock, AsyncMock

import sys
import os
sys.path.append(os.getcwd())

from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, AgentRegistry
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.models.situation_awareness_models import (
    SituationDetectionRequest,
    SituationDetectionResponse,
    PrincipalContext,
    PrincipalRole,
    TimeFrame,
    ComparisonType,
    KPIDefinition
)
from src.registry.models.data_product import DataProduct

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_multisource_situation_detection():
    """
    Integration test to verify Situation Awareness across multiple data sources (FI + Sales).

    This test:
    1. Initializes Orchestrator and Agents.
    2. Registers mock Data Products (one FI/DuckDB, one Sales/BigQuery).
    3. Registers mock KPIs for both domains.
    4. Mocks Data Product Agent's SQL execution to simulate multi-source returns.
    5. Triggers Situation Detection and verifies KPIs from both sources are processed.
    """
    logger.info("Starting Multi-Source Situation Detection Test")

    # Save registry state so we can restore it after the test.
    # This prevents the mocked DP agent from leaking into subsequent tests.
    _saved_agents = dict(AgentRegistry._agents)
    _saved_factories = dict(AgentRegistry._agent_factories)
    _saved_deps = dict(AgentRegistry._agent_dependencies)
    _saved_status = dict(AgentRegistry._agent_initialization_status)

    try:
        # 1. Initialize Orchestrator
        orchestrator = await A9_Orchestrator_Agent.create()

        # 2. Setup Data Product Agent (Mocked internals to avoid real DB connections for this integration test)
        dp_agent = await A9_Data_Product_Agent.create({"bypass_mcp": True})

        # Mock execute_sql to return synthetic data based on the query/KPI
        async def mock_execute_sql(sql_query, parameters=None, principal_context=None):
            logger.info(f"Mock Executing SQL: {sql_query}")

            # Simulate FI data (DuckDB)
            if "gross_revenue" in sql_query.lower() or "fi_star_schema" in sql_query.lower():
                return {
                    "success": True,
                    "status": "success",
                    "columns": ["value"],
                    "rows": [{"value": 1500000.0}],
                    "data": [{"value": 1500000.0}]
                }

            # Simulate Sales data (BigQuery)
            elif "total_sales_volume" in sql_query.lower() or "sales_orders" in sql_query.lower():
                return {
                    "success": True,
                    "status": "success",
                    "columns": ["value"],
                    "rows": [{"value": 5000}],
                    "data": [{"value": 5000}]
                }

            return {"success": False, "message": "Unknown query in mock"}

        dp_agent.execute_sql = AsyncMock(side_effect=mock_execute_sql)

        # Mock generate_sql_for_kpi to return simple SQL
        async def mock_generate_sql(kpi_definition, **kwargs):
            kpi_name = kpi_definition.name.lower().replace(" ", "_")
            if "revenue" in kpi_name:
                sql = "SELECT SUM(amount) as value FROM fi_star_schema.transactions"
            else:
                sql = "SELECT COUNT(*) as value FROM `project.dataset.sales_orders`"
            return {
                "success": True,
                "sql": sql,
                "kpi_name": kpi_definition.name
            }

        dp_agent.generate_sql_for_kpi = AsyncMock(side_effect=mock_generate_sql)

        # Register DP Agent
        await orchestrator.register_agent("A9_Data_Product_Agent", dp_agent)

        # 3. Setup Situation Awareness Agent
        # We create it via factory to ensure it sets up dependencies
        from src.agents.new.a9_situation_awareness_agent import create_situation_awareness_agent
        sa_agent = create_situation_awareness_agent({"target_domains": ["Finance", "Sales"]})
        await sa_agent.connect(orchestrator)

        # Inject Mock KPIs into SA Agent's registry directly for test stability
        # (Bypassing complex registry loading for this specific integration test)
        sa_agent.kpi_registry = {
            "Gross Revenue": KPIDefinition(
                name="Gross Revenue",
                id="gross_revenue",
                domain="Finance",
                description="Total revenue",
                data_product_id="fi_star_schema",
                thresholds={"critical": 1000000.0, "warning": 1200000.0}, # Example thresholds
                positive_trend_is_good=True
            ),
            "Total Sales Volume": KPIDefinition(
                name="Total Sales Volume",
                id="total_sales_volume",
                domain="Sales",
                description="Number of orders",
                data_product_id="sales_orders_bq",
                thresholds={"critical": 1000.0},
                positive_trend_is_good=True
            )
        }

        # Mock get_relevant_kpis to return our injected KPIs
        sa_agent._get_relevant_kpis = MagicMock(return_value=sa_agent.kpi_registry)

        # Mock _get_kpi_value to allow us to test the flow without full comparisons
        # This simulates the logic inside _get_kpi_value calling DPA
        async def mock_get_kpi_value(kpi_def, timeframe, *args, **kwargs):
            # Call generate/execute on DPA to ensure those paths are covered
            gen = await dp_agent.generate_sql_for_kpi(kpi_def)
            exec_res = await dp_agent.execute_sql(gen["sql"])
            val = exec_res["data"][0]["value"]

            from src.agents.models.situation_awareness_models import KPIValue
            return KPIValue(
                kpi_name=kpi_def.name,
                value=val,
                timeframe=TimeFrame.CURRENT_QUARTER,
                comparison_value=val * 0.8, # Mock comparison
                comparison_type=ComparisonType.YEAR_OVER_YEAR
            )

        sa_agent._get_kpi_value = AsyncMock(side_effect=mock_get_kpi_value)

        await orchestrator.register_agent("A9_Situation_Awareness_Agent", sa_agent)

        # 4. Execute Situation Detection Request
        req = SituationDetectionRequest(
            request_id="test_multisource_001",
            principal_context=PrincipalContext(
                principal_id="cfo_user",
                role="CFO",
                business_processes=["Finance", "Sales"],
                default_filters={},
                decision_style="analytical",
                communication_style="concise",
                preferred_timeframes=[TimeFrame.CURRENT_QUARTER]
            ),
            business_processes=["Finance", "Sales"],
            timeframe=TimeFrame.CURRENT_QUARTER
        )

        logger.info("Triggering orchestration...")
        response_dict = await orchestrator.orchestrate_situation_detection(req)

        # 5. Verify Results
        assert response_dict["status"] == "success"

        # Verify DPA was called for both KPIs
        # It might be called more than 2 times if sample SQL is generated
        assert dp_agent.generate_sql_for_kpi.call_count >= 2
        assert dp_agent.execute_sql.call_count >= 2

        # Check calls arguments to ensure both domains were hit
        calls = dp_agent.generate_sql_for_kpi.call_args_list
        logger.info(f"generate_sql_for_kpi calls: {calls}")

        kpi_names_called = []
        for c in calls:
            # Check positional args
            if len(c[0]) > 0:
                kpi = c[0][0]
                if hasattr(kpi, 'name'):
                    kpi_names_called.append(kpi.name)
            # Check kwargs
            elif 'kpi_definition' in c[1]:
                kpi = c[1]['kpi_definition']
                if hasattr(kpi, 'name'):
                    kpi_names_called.append(kpi.name)

        assert "Gross Revenue" in kpi_names_called
        assert "Total Sales Volume" in kpi_names_called

        logger.info("✅ Multi-Source Integration Verification Successful")

    finally:
        # Restore original AgentRegistry state to prevent mock leakage into other tests
        AgentRegistry._agents = _saved_agents
        AgentRegistry._agent_factories = _saved_factories
        AgentRegistry._agent_dependencies = _saved_deps
        AgentRegistry._agent_initialization_status = _saved_status

if __name__ == "__main__":
    asyncio.run(test_multisource_situation_detection())
