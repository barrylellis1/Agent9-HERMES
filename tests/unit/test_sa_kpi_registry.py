"""
Unit test for KPI registry integration with Situation Awareness Agent.

This test focuses on testing the KPI registry integration with the
Situation Awareness Agent, specifically the KPI loading and conversion methods.
"""

import os
import sys
import unittest
import asyncio
import logging
from typing import Dict, Any
from unittest import mock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the mock agents
from tests.mocks.mock_agents import MockKPIProvider, MockRegistryFactory

# Import the agent
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent

class TestSituationAwarenessKPIRegistry(unittest.TestCase):
    """Test KPI registry integration with Situation Awareness Agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock registry factory
        self.registry_factory_patcher = mock.patch('src.registry.factory.RegistryFactory')
        self.mock_registry_factory_class = self.registry_factory_patcher.start()
        self.mock_registry_factory = mock.MagicMock()
        self.mock_registry_factory_class.return_value = self.mock_registry_factory
        
        # Create a mock KPI provider
        self.mock_kpi_provider = MockKPIProvider()
        self.mock_registry_factory.get_kpi_provider.return_value = self.mock_kpi_provider
        self.mock_registry_factory.get_provider.return_value = self.mock_kpi_provider
        
        # Set up async event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop the registry factory patcher
        self.registry_factory_patcher.stop()
        
        # Close the event loop
        self.loop.close()
    
    def test_load_kpi_registry(self):
        """Test loading KPI registry."""
        # Create the Situation Awareness Agent
        agent = self.loop.run_until_complete(A9_Situation_Awareness_Agent.create({
            "contract_path": "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml",
            "target_domains": ["Finance"]
        }))
        
        # Verify KPI registry is loaded
        self.assertGreater(len(agent.kpi_registry), 0)
        
        # Verify KPI provider was called
        self.mock_registry_factory.get_kpi_provider.assert_called_once()
        
        # Clean up
        self.loop.run_until_complete(agent.disconnect())
    
    def test_kpi_matches_domains(self):
        """Test KPI domain matching."""
        # Create the Situation Awareness Agent
        agent = self.loop.run_until_complete(A9_Situation_Awareness_Agent.create({
            "contract_path": "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml",
            "target_domains": ["Finance"]
        }))
        
        # Test with matching domain
        kpi = {"domain": "Finance", "name": "Revenue"}
        self.assertTrue(agent._kpi_matches_domains(kpi, ["Finance"]))
        
        # Test with non-matching domain
        kpi = {"domain": "HR", "name": "Employee Count"}
        self.assertFalse(agent._kpi_matches_domains(kpi, ["Finance"]))
        
        # Test with multiple domains
        kpi = {"domain": "Finance", "name": "Revenue"}
        self.assertTrue(agent._kpi_matches_domains(kpi, ["Finance", "HR"]))
        
        # Clean up
        self.loop.run_until_complete(agent.disconnect())
    
    def test_convert_to_kpi_definition(self):
        """Test converting canonical KPI to internal KPIDefinition."""
        # Create the Situation Awareness Agent
        agent = self.loop.run_until_complete(A9_Situation_Awareness_Agent.create({
            "contract_path": "src/registry_references/data_product_registry/data_products/fi_star_schema.yaml",
            "target_domains": ["Finance"]
        }))
        
        # Test with valid KPI
        canonical_kpi = {
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
        }
        
        kpi_def = agent._convert_to_kpi_definition(canonical_kpi)
        
        # Verify conversion
        self.assertIsNotNone(kpi_def)
        self.assertEqual(kpi_def.name, "Revenue")
        self.assertEqual(kpi_def.description, "Total revenue across all business units")
        self.assertEqual(kpi_def.unit, "USD")
        
        # Test with invalid KPI (missing required fields)
        invalid_kpi = {
            "id": "invalid_kpi",
            "domain": "Finance"
        }
        
        kpi_def = agent._convert_to_kpi_definition(invalid_kpi)
        
        # Verify conversion fails gracefully
        self.assertIsNone(kpi_def)
        
        # Clean up
        self.loop.run_until_complete(agent.disconnect())

if __name__ == "__main__":
    unittest.main()
