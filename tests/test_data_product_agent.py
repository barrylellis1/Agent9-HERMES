"""
Test script for Data Product Agent implementation.

This script verifies that the Data Product Agent correctly implements
the DataProductProtocol interface and all its required methods.
"""

import asyncio
import os
import sys
import unittest
import logging
from typing import Dict, Any, List

import pandas as pd

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the agent and protocol
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.protocols.data_product_protocol import DataProductProtocol


class TestDataProductAgent(unittest.TestCase):
    """Test case for Data Product Agent implementation."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        
        # Create event loop for async tests
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)
        
        # Configuration for the agent
        cls.config = {
            "data_directory": "data",
            "log_level": "INFO",
            "database": {
                "type": "duckdb",
                "path": "data/agent9-hermes.duckdb"
            }
        }
        
        # Create agent instance
        try:
            cls.agent = cls.loop.run_until_complete(
                A9_Data_Product_Agent.create(cls.config)
            )
        except Exception as e:
            print(f"Failed to create agent: {str(e)}")
            raise

    @classmethod
    def tearDownClass(cls):
        try:
            if hasattr(cls, 'loop') and cls.loop is not None:
                cls.loop.run_until_complete(cls.agent.disconnect())
                cls.loop.close()
        except Exception:
            pass

    def test_protocol_compliance(self):
        """Test that the agent implements the DataProductProtocol."""
        self.assertIsInstance(self.agent, DataProductProtocol)
        
    def test_execute_sql(self):
        """Test execute_sql method."""
        # Test with a simple SELECT query
        try:
            result = self.loop.run_until_complete(
                self.agent.execute_sql("SELECT 1 as test")
            )
            
            # Verify result is a pandas DataFrame
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 1)
            self.assertEqual(result.iloc[0]['test'], 1)
        except Exception as e:
            self.fail(f"execute_sql failed: {str(e)}")
        
    def test_generate_sql(self):
        """Test generate_sql method."""
        # Test with a simple natural language query
        try:
            result = self.loop.run_until_complete(
                self.agent.generate_sql("Show me the total sales")
            )
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn('sql', result)
            self.assertIn('success', result)
            self.assertTrue(result['success'])
        except Exception as e:
            self.fail(f"generate_sql failed: {str(e)}")
        
    def test_get_data_product(self):
        """Test get_data_product method."""
        # Test with a known data product ID (using default if none exists)
        try:
            result = self.loop.run_until_complete(
                self.agent.get_data_product("default_data_product")
            )
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn('transaction_id', result)
            self.assertIn('success', result)
        except Exception as e:
            self.fail(f"get_data_product failed: {str(e)}")
        
    def test_list_data_products(self):
        """Test list_data_products method."""
        # Test listing all data products
        try:
            result = self.loop.run_until_complete(
                self.agent.list_data_products()
            )
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn('data_products', result)
            self.assertIn('count', result)
            self.assertIn('success', result)
            self.assertTrue(result['success'])
            
            # Verify data_products is a list
            self.assertIsInstance(result['data_products'], list)
        except Exception as e:
            self.fail(f"list_data_products failed: {str(e)}")
        
    def test_create_view(self):
        """Test create_view method."""
        # Test creating a simple view
        view_name = "test_view"
        sql_query = "SELECT 1 as test"
        
        try:
            result = self.loop.run_until_complete(
                self.agent.create_view(view_name, sql_query)
            )
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            self.assertIn('view_name', result)
            self.assertIn('success', result)
            self.assertTrue(result['success'])
            
            # Verify view was created by querying it
            try:
                view_result = self.loop.run_until_complete(
                    self.agent.execute_sql(f"SELECT * FROM {view_name}")
                )
                self.assertEqual(len(view_result), 1)
                self.assertEqual(view_result.iloc[0]['test'], 1)
            except Exception as e:
                self.fail(f"Failed to query created view: {str(e)}")
        except Exception as e:
            self.fail(f"create_view failed: {str(e)}")


if __name__ == '__main__':
    unittest.main()
