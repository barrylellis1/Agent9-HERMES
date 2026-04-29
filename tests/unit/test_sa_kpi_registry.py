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


def _make_agent_with_mock_registry(loop, mock_registry_factory):
    """Create an SA agent with mocked registry, bypassing full orchestrator wiring.

    # arch-lint-skip: This is a unit test that isolates KPI registry loading.
    # Direct instantiation avoids orchestrator overhead; test uses mock registry factory
    # injected via config to validate loading behavior in isolation.
    """
    config = {
        "target_domains": ["Finance"],
        "registry_factory": mock_registry_factory,
    }
    # Instantiate directly (no connect) to avoid orchestrator side-effects
    agent = A9_Situation_Awareness_Agent(config)  # arch-lint-skip
    # Manually load KPIs from the mocked registry
    loop.run_until_complete(agent._load_kpi_registry())
    return agent


class TestSituationAwarenessKPIRegistry(unittest.TestCase):
    """Test KPI registry integration with Situation Awareness Agent."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock registry factory injected via config (no global patch needed)
        self.mock_registry_factory = mock.MagicMock()

        # Create a mock KPI provider
        self.mock_kpi_provider = MockKPIProvider()
        self.mock_registry_factory.get_kpi_provider.return_value = self.mock_kpi_provider
        self.mock_registry_factory.get_provider.return_value = self.mock_kpi_provider

        # Set up async event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test fixtures."""
        self.loop.close()

    def test_load_kpi_registry(self):
        """Test loading KPI registry from Supabase-backed provider."""
        agent = _make_agent_with_mock_registry(self.loop, self.mock_registry_factory)

        # Verify KPI registry is loaded
        self.assertGreater(len(agent.kpi_registry), 0)

        # Verify KPI provider was called
        self.mock_registry_factory.get_kpi_provider.assert_called_once()

    def test_kpi_matches_domains(self):
        """Test KPI domain matching."""
        agent = _make_agent_with_mock_registry(self.loop, self.mock_registry_factory)

        # Test with matching domain
        kpi = {"domain": "Finance", "name": "Revenue"}
        self.assertTrue(agent._kpi_matches_domains(kpi, ["Finance"]))

        # Test with non-matching domain
        kpi = {"domain": "HR", "name": "Employee Count"}
        self.assertFalse(agent._kpi_matches_domains(kpi, ["Finance"]))

        # Test with multiple domains
        kpi = {"domain": "Finance", "name": "Revenue"}
        self.assertTrue(agent._kpi_matches_domains(kpi, ["Finance", "HR"]))

    def test_convert_to_kpi_definition(self):
        """Test converting canonical KPI to internal KPIDefinition."""
        agent = _make_agent_with_mock_registry(self.loop, self.mock_registry_factory)

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

if __name__ == "__main__":
    unittest.main()
