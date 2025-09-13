"""
Simple test script for verifying KPI registry integration with Situation Awareness Agent.
This script focuses specifically on testing the KPI loading from the registry.
"""

import os
import sys
import asyncio
import logging
import yaml
import unittest.mock as mock
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the Situation Awareness Agent
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent

# Mock KPI Provider
class MockKPIProvider:
    def __init__(self):
        self.kpis = [
            {
                "id": "fin_revenue",
                "name": "Revenue",
                "description": "Total revenue across all business units",
                "unit": "USD",
                "domain": "Finance",
                "calculation": "SUM(revenue)",
                "source_table": "financial_data",
                "business_processes": ["Sales", "Marketing"],
                "thresholds": {
                    "critical": {"value": 1000000, "comparison": "lt"},
                    "warning": {"value": 1500000, "comparison": "lt"}
                }
            },
            {
                "id": "fin_profit_margin",
                "name": "Profit Margin",
                "description": "Profit margin percentage",
                "unit": "%",
                "domain": "Finance",
                "calculation": "(SUM(revenue) - SUM(costs)) / SUM(revenue) * 100",
                "source_table": "financial_data",
                "business_processes": ["Finance", "Operations"],
                "thresholds": {
                    "critical": {"value": 10, "comparison": "lt"},
                    "warning": {"value": 15, "comparison": "lt"}
                }
            },
            {
                "id": "fin_cash_flow",
                "name": "Cash Flow",
                "description": "Net cash flow",
                "unit": "USD",
                "domain": "Finance",
                "calculation": "SUM(cash_in) - SUM(cash_out)",
                "source_table": "cash_flow_data",
                "business_processes": ["Finance", "Treasury"],
                "thresholds": {
                    "critical": {"value": 0, "comparison": "lt"},
                    "warning": {"value": 100000, "comparison": "lt"}
                }
            }
        ]
    
    def get_all(self):
        return self.kpis

# Mock Registry Factory
class RegistryFactory:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RegistryFactory, cls).__new__(cls)
            cls._instance.providers = {}
            cls._instance.providers["kpi"] = MockKPIProvider()
        return cls._instance
    
    def get_kpi_provider(self):
        return self.providers.get("kpi")
    
    def get_provider(self, provider_type):
        return self.providers.get(provider_type)

async def test_kpi_registry_loading():
    """Test KPI registry loading in the Situation Awareness Agent"""
    logger.info("Starting KPI registry loading test")
    
    # Patch the RegistryFactory import in the Situation Awareness Agent
    import sys
    sys.modules['src.registry.registry_factory'] = type('MockModule', (), {'RegistryFactory': RegistryFactory})
    
    try:
        # Create the Situation Awareness Agent directly
        agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "target_domains": ["Finance"]
        }
        
        logger.info("Creating Situation Awareness Agent...")
        agent = await A9_Situation_Awareness_Agent.create(agent_config)
        
        # Verify KPI registry is loaded
        logger.info(f"KPI Registry loaded: {len(agent.kpi_registry)} KPIs")
        
        # Print the first 5 KPIs for verification
        count = 0
        for kpi_name, kpi_def in agent.kpi_registry.items():
            if count < 5:  # Limit to first 5 KPIs to avoid overwhelming output
                logger.info(f"KPI: {kpi_name} - {kpi_def.get('description', 'No description')}")
                count += 1
        
        # Test the KPI registry loading method directly
        logger.info("Testing _load_kpi_registry method...")
        agent._load_kpi_registry()
        
        logger.info(f"KPI Registry after reload: {len(agent.kpi_registry)} KPIs")
        
        # Verify KPI registry structure
        if agent.kpi_registry:
            # Get a sample KPI
            sample_kpi_name = next(iter(agent.kpi_registry))
            sample_kpi = agent.kpi_registry[sample_kpi_name]
            
            logger.info(f"Sample KPI structure for '{sample_kpi_name}':")
            for key, value in sample_kpi.items():
                logger.info(f"  {key}: {value}")
            
            # Check if the KPI has the required fields
            required_fields = ['name', 'description', 'unit']
            missing_fields = [field for field in required_fields if field not in sample_kpi]
            
            if missing_fields:
                logger.warning(f"Missing required fields in KPI: {missing_fields}")
            else:
                logger.info("All required fields present in KPI")
            
            return True
        else:
            logger.error("KPI Registry is empty")
            return False
            
    except Exception as e:
        logger.error(f"Error in KPI registry loading test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_kpi_registry_loading())
