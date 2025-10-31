# arch-allow-direct-agent-construction
"""
Test script for real data-driven situation detection.

This script validates that the Situation Awareness Agent can:
1. Execute real SQL queries via the Data Product MCP Service Agent
2. Process KPI values from actual database results
3. Detect situations based on real data thresholds and comparisons
"""

import pytest
import pytest_asyncio
import sys
import os
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import situation awareness models
from src.agents.models.situation_awareness_models import (
    PrincipalRole, 
    BusinessProcess as BusinessProcessEnum,  # Rename enum to avoid conflicts
    TimeFrame, 
    ComparisonType,
    SituationDetectionRequest,
    SituationSeverity,
    KPIDefinition,
    PrincipalContext,
    Situation
)

# Import BusinessProcess Pydantic model
from src.registry.models.business_process import BusinessProcess

# Import agent and orchestrator
from src.agents.a9_orchestrator_agent import A9_Orchestrator_Agent, AgentRegistry, initialize_agent_registry
from src.agents.a9_situation_awareness_agent import create_situation_awareness_agent
from src.agents.a9_data_product_mcp_service_agent import A9_Data_Product_MCP_Service_Agent
from src.agents.a9_data_governance_agent import A9_Data_Governance_Agent

# Import necessary registry components
from src.registry.bootstrap import RegistryBootstrap
from src.registry.factory import RegistryFactory
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider

@pytest.mark.asyncio
async def test_real_data_situation_detection():
    """
    Test real data-driven situation detection with the Situation Awareness Agent.
    
    This test:
    1. Initializes the orchestrator with minimal real agents
    2. Registers needed agent factories with the orchestrator
    3. Creates the Situation Awareness Agent with real dependencies
    4. Executes a situation detection request with real data
    5. Validates that situations are detected based on actual KPI values
    """
    logger.info("Starting real data situation detection test")
    
    # Initialize the orchestrator with minimal configuration
    orchestrator = A9_Orchestrator_Agent({
        "agents_path": "src/agents/new",
        "db_config": {
            "db_type": "duckdb",
            "data_dir": "src/data",
            "db_file": "agent9.db"
        }
    })
    
    # Initialize registry providers using RegistryBootstrap to avoid config schema issues
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    registry_path = os.path.join(base_path, "registry")
    await RegistryBootstrap.initialize({
        "base_path": base_path,
        "registry_path": registry_path
    })
        
    # Initialize agent registry with common agent factories
    # This loads and registers all required agent factories through the standard mechanism
    await initialize_agent_registry()
    
    # Define test config for the situation awareness agent
    situation_agent_config = {
        "contract_path": "src/contracts/fi_star_schema.yaml",
        "target_domains": ["Finance"],  # Focus on Finance domain for MVP
        "principal_profile_path": "src/registry/principal/principal_profiles.yaml",
        "business_glossary_path": "src/registry/data/business_glossary.yaml",
    }
    
    # Define test config for the data product agent
    data_product_agent_config = {
        "db_config": {
            "db_type": "duckdb",
            "data_dir": "src/data",
            "db_file": "agent9.db"
        },
        "contracts_path": "src/contracts",
        "registry_file": "src/registry/data_product/data_product_registry.yaml"
    }
    
    # Define test config for the data governance agent
    data_governance_agent_config = {
        "business_glossary_path": "src/registry/data/business_glossary.yaml",
        "hitl_threshold": 0.7  # Set threshold for HITL escalation
    }
    
    # NOTE: Agent factories are now registered automatically through initialize_agent_registry()
    # This follows the Agent9 Design Standard that prohibits manual agent registration in tests
    # The orchestrator will dynamically discover and register all required agents
    
    # Connect to the orchestrator
    await orchestrator.connect()
    
    try:
        # Create the Situation Awareness Agent
        agent = create_situation_awareness_agent(situation_agent_config)
        
        # Add direct SQL tracking instrumentation
        original_generate_sql = agent._generate_sql_for_kpi
        original_detect_situations = agent.detect_situations
        
        # Track all generated SQL directly
        def sql_tracking_wrapper(*args, **kwargs):
            sql = original_generate_sql(*args, **kwargs)
            print(f"\n===== SQL GENERATED =====\n{sql}\n")
            return sql
        
        # Track situation detection directly
        async def situation_tracking_wrapper(*args, **kwargs):
            print(f"\n===== SITUATION DETECTION STARTED =====\n")
            
            # Add debugging to inspect principal and business processes
            request = args[0] if args else kwargs.get('request')
            if request:
                print(f"Principal context: {request.principal_context}")
                print(f"Business processes: {request.business_processes}")
                print(f"Timeframe: {request.timeframe}")
            
            # Add debugging for KPI registry
            print(f"KPI registry contains {len(agent.kpi_registry)} KPIs")
            if agent.kpi_registry:
                print("KPIs in registry:")
                for i, (kpi_name, kpi_def) in enumerate(list(agent.kpi_registry.items())[:5]):
                    print(f"  {i+1}. {kpi_name} - Business processes: {kpi_def.business_processes}")
            else:
                print("KPI registry is empty!")
            
            response = await original_detect_situations(*args, **kwargs)
            print(f"\n===== SITUATIONS DETECTED: {len(response.situations)} =====\n")
            for i, situation in enumerate(response.situations):
                print(f"Situation {i+1}: {situation.title} (Severity: {situation.severity})")
            return response
        
        # Apply direct instrumentation
        agent._generate_sql_for_kpi = sql_tracking_wrapper
        agent.detect_situations = situation_tracking_wrapper

        # Connect the agent to its dependencies
        connection_success = await agent.connect()
        
        # Debug the KPI registry state after connect (should be populated by the agent itself)
        print("\n===== KPI REGISTRY STATE AFTER CONNECT =====\n")
        print(f"KPI registry has {len(agent.kpi_registry)} KPIs")
        if agent.kpi_registry:
            print("Sample KPIs loaded:")
            for i, (kpi_name, kpi_def) in enumerate(list(agent.kpi_registry.items())[:3]):
                print(f"  {i+1}. {kpi_name} - Business processes: {kpi_def.business_processes}")
        else:
            print("WARNING: KPI registry is empty after agent connect!")
            # This should not happen after our fix to agent.connect()

        # Verify agent is properly initialized
        logger.info("Checking agent initialization state...")
        assert connection_success, "Agent should be connected"
        assert agent.data_product_agent is not None, "Data Product Agent should be available"
        assert agent.data_governance_agent is not None, "Data Governance Agent should be available"
        assert agent.kpi_registry is not None, "KPI registry should be loaded"
        logger.info(f"Agent has loaded {len(agent.kpi_registry)} KPI definitions")
        
        # Get a principal context for testing
        principal_id = "CFO"  # Use CFO profile for testing
        
        # Get the principal profile from the initialized RegistryFactory
        registry_factory = RegistryFactory()
        principal_provider = registry_factory.get_principal_profile_provider()
        principal_profile = principal_provider.get(principal_id) if principal_provider else None
        
        # Normalize principal_profile to dict for downstream .get() access
        if principal_profile is not None:
            try:
                principal_profile = principal_profile.model_dump() if hasattr(principal_profile, 'model_dump') else principal_profile
            except Exception:
                pass
        
        if not principal_profile:
            logger.error(f"Principal profile not found for ID: {principal_id}")
            principal_profile = {
                "role": "CFO",
                "name": "Chief Financial Officer",
                "business_processes": ["Finance: Profitability Analysis", "Finance: Revenue Growth Analysis"]
            }
        
        # Create principal context
        principal_context = PrincipalContext(
            principal_id=principal_id,
            role=PrincipalRole.CFO,
            name=(principal_profile.get("name", "Chief Financial Officer") if isinstance(principal_profile, dict) else getattr(principal_profile, 'name', "Chief Financial Officer")),
            # Use BusinessProcessEnum values directly
            business_processes=[
                BusinessProcessEnum.PROFITABILITY_ANALYSIS,
                BusinessProcessEnum.REVENUE_GROWTH
            ],
            # Add required fields
            default_filters={"business_unit": "all", "region": "global"},
            decision_style="data-driven",
            communication_style="concise",
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
        )
        
        # Create situation detection request
        situation_request = SituationDetectionRequest(
            request_id=f"test-situation-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            principal_context=principal_context,
            business_processes=[BusinessProcessEnum.PROFITABILITY_ANALYSIS, BusinessProcessEnum.REVENUE_GROWTH],
            timeframe=TimeFrame.CURRENT_QUARTER,
            comparison_type=ComparisonType.QUARTER_OVER_QUARTER
        )
        
        # Stats collection variables
        sql_queries = []
        sql_errors = []
        situations_by_severity = {}
        
        # Patch the agent's _get_kpi_value method to capture SQL queries and errors
        original_get_kpi_value = agent._get_kpi_value
        
        async def patched_get_kpi_value(*args, **kwargs):
            try:
                # Call original method
                kpi_value = await original_get_kpi_value(*args, **kwargs)
                
                # Capture SQL queries if successful
                if hasattr(agent, 'last_sql_query') and agent.last_sql_query:
                    sql_queries.append({
                        'kpi': args[0].name if args and hasattr(args[0], 'name') else 'unknown',
                        'query': agent.last_sql_query,
                        'success': True,
                        'result': kpi_value.value if kpi_value else None
                    })
                    
                return kpi_value
            except Exception as e:
                # Capture errors
                if hasattr(agent, 'last_sql_query') and agent.last_sql_query:
                    sql_errors.append({
                        'kpi': args[0].name if args and hasattr(args[0], 'name') else 'unknown',
                        'query': agent.last_sql_query,
                        'error': str(e)
                    })
                raise
        
        # Apply the patch
        agent._get_kpi_value = patched_get_kpi_value
        
        # Add attribute to store last SQL query
        agent.last_sql_query = None
        
        # Patch _generate_sql_for_kpi to capture queries
        original_generate_sql = agent._generate_sql_for_kpi
        
        def patched_generate_sql(*args, **kwargs):
            sql = original_generate_sql(*args, **kwargs)
            agent.last_sql_query = sql
            return sql
        
        agent._generate_sql_for_kpi = patched_generate_sql
        
        # Execute situation detection
        logger.info("Executing situation detection with real data...")
        situation_response = await agent.detect_situations(situation_request)
        
        # Collect statistics on situations by severity
        for situation in situation_response.situations:
            severity = situation.severity
            if severity not in situations_by_severity:
                situations_by_severity[severity] = 0
            situations_by_severity[severity] += 1
        
        # Print SQL query statistics
        print("\n===== SQL Query Statistics =====")
        print(f"Total SQL queries executed: {len(sql_queries)}")
        print(f"SQL query errors: {len(sql_errors)}")
        
        # Print situation statistics
        print("\n===== Situation Statistics =====")
        print(f"Total situations detected: {len(situation_response.situations)}")
        for severity, count in situations_by_severity.items():
            print(f"Severity {severity}: {count} situations")
        
        # Print SQL queries
        print("\n===== SQL Queries Executed =====")
        for i, query_info in enumerate(sql_queries, 1):
            print(f"Query {i} - KPI: {query_info['kpi']}")
            print(f"SQL: {query_info['query']}")
            print(f"Result: {query_info['result']}\n")
        
        # Print SQL errors if any
        if sql_errors:
            print("\n===== SQL Query Errors =====")
            for i, error_info in enumerate(sql_errors, 1):
                print(f"Error {i} - KPI: {error_info['kpi']}")
                print(f"SQL: {error_info['query']}")
                print(f"Error: {error_info['error']}\n")
        
        # Print detail of each situation
        print("\n===== Situations Detected =====")
        for i, situation in enumerate(situation_response.situations, 1):
            print(f"Situation {i}:")
            print(f"  Title: {situation.title}")
            print(f"  Description: {situation.description}")
            print(f"  Severity: {situation.severity}")
            print(f"  KPIs: {', '.join([kpi.name for kpi in situation.kpis])}")
            print()
        
        # Validate response
        assert situation_response is not None, "Situation response should not be None"
        assert situation_response.request_id == situation_request.request_id, "Request ID mismatch"
        
        # Log the detected situations
        logger.info(f"Detected {len(situation_response.situations)} situations")
        for idx, situation in enumerate(situation_response.situations):
            logger.info(f"Situation {idx+1}: {situation.title}")
            logger.info(f"  - Description: {situation.description}")
            logger.info(f"  - Severity: {situation.severity}")
            logger.info(f"  - KPIs: {', '.join([kpi.kpi_name for kpi in situation.kpi_values])}")
            logger.info(f"  - Context: {situation.context}")
            
            # Print the actual KPI values
            for kpi in situation.kpi_values:
                logger.info(f"    * {kpi.kpi_name}: {kpi.value}")
                if kpi.comparison_value is not None:
                    percent_change = (kpi.value - kpi.comparison_value) / abs(kpi.comparison_value) * 100 if kpi.comparison_value != 0 else 0
                    logger.info(f"      Previous: {kpi.comparison_value} ({percent_change:.1f}% change)")
        
        # Test execution of actual SQL query directly
        logger.info("\nTesting direct SQL execution...")
        
        # Get a sample KPI definition using RegistryFactory
        registry = RegistryFactory()
        kpi_provider = registry.get_kpi_provider()
        kpi_definitions = {k.id: k for k in (kpi_provider.get_all() if kpi_provider else [])}
        
        if kpi_definitions:
            # Get the first KPI for testing
            sample_kpi_name = next(iter(kpi_definitions.keys()))
            sample_kpi = kpi_definitions[sample_kpi_name]
            
            logger.info(f"Testing SQL generation for KPI: {sample_kpi_name}")
            
            # Generate SQL for the KPI
            sql_query = agent._generate_sql_for_kpi(
                sample_kpi,
                TimeFrame.CURRENT_QUARTER,
                {}
            )
            
            logger.info(f"Generated SQL: {sql_query}")
            
            # Execute the SQL query via data product agent
            from src.agents.a9_data_product_mcp_service_agent import SQLExecutionRequest
            
            sql_exec_request = SQLExecutionRequest(
                request_id=f"test_sql_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                principal_id="system",
                sql_query=sql_query
            )
            
            sql_exec_response = await agent.data_product_agent.execute_sql(sql_exec_request)
            
            # Log the SQL execution result
            logger.info(f"SQL execution status: {sql_exec_response.status}")
            if sql_exec_response.status == "success":
                logger.info(f"SQL results: {sql_exec_response.results}")
            else:
                logger.error(f"SQL error: {sql_exec_response.error_message}")
                
            # Test KPI value retrieval directly
            logger.info("\nTesting direct KPI value retrieval...")
            kpi_value = await agent._get_kpi_value(
                sample_kpi,
                TimeFrame.CURRENT_QUARTER,
                ComparisonType.QUARTER_OVER_QUARTER,
                {}
            )
            
            if kpi_value:
                logger.info(f"Retrieved KPI value for {kpi_value.kpi_name}: {kpi_value.value}")
                if kpi_value.comparison_value is not None:
                    percent_change = (kpi_value.value - kpi_value.comparison_value) / abs(kpi_value.comparison_value) * 100 if kpi_value.comparison_value != 0 else 0
                    logger.info(f"Comparison value: {kpi_value.comparison_value} ({percent_change:.1f}% change)")
            else:
                logger.warning("KPI value retrieval returned None")
        else:
            logger.warning("No KPI definitions found for testing")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)
        raise
    finally:
        # Disconnect the agent and orchestrator
        if 'agent' in locals():
            await agent.disconnect()
        await orchestrator.disconnect()
    
    logger.info("Real data situation detection test completed")

async def main():
    """Run the test."""
    logger.info("\n====== TESTING REAL DATA SITUATION DETECTION ======\n")
    await test_real_data_situation_detection()
    logger.info("\n====== TEST COMPLETED ======\n")

if __name__ == "__main__":
    asyncio.run(main())
