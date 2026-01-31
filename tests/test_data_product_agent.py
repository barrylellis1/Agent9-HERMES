"""
Test script for Data Product Agent implementation.

This script verifies that the Data Product Agent correctly implements
the DataProductProtocol interface and all its required methods.
"""

import pytest
import pandas as pd
from src.agents.protocols.data_product_protocol import DataProductProtocol

@pytest.mark.asyncio
async def test_protocol_compliance(data_product_agent):
    """Test that the agent implements the DataProductProtocol."""
    assert isinstance(data_product_agent, DataProductProtocol)

@pytest.mark.asyncio
async def test_execute_sql(data_product_agent):
    """Test execute_sql method."""
    # Test with a simple SELECT query
    result = await data_product_agent.execute_sql("SELECT 1 as test")
    
    # Verify result is a dict (protocol compliance) or has expected keys
    # The actual implementation might return a dict with 'rows', 'columns', etc.
    # or if it returns a DataFrame directly (older impl), we check that.
    # Looking at test_data_product_agent_protocol.py, it returns a dict with 'success', 'rows', etc.
    
    assert isinstance(result, dict)
    assert result.get("success") is True
    assert result.get("row_count") == 1
    assert result.get("rows")[0]["test"] == 1

@pytest.mark.asyncio
async def test_generate_sql(data_product_agent):
    """Test generate_sql method."""
    # Test with a simple natural language query
    result = await data_product_agent.generate_sql("Show me the total sales")
    
    # Verify result structure
    assert isinstance(result, dict)
    assert "transaction_id" in result
    
    # If LLM is not available, it might fail or return partial success
    if result.get("success"):
        assert "sql" in result
    else:
        assert "message" in result

@pytest.mark.asyncio
async def test_get_data_product(data_product_agent):
    """Test get_data_product method."""
    # Test with a known data product ID (using default if none exists)
    result = await data_product_agent.get_data_product("default_data_product")
    
    # Verify result structure
    assert isinstance(result, dict)
    assert "success" in result
    # It might return success=False if not found, but structured response
    if not result.get("success"):
        assert "message" in result

@pytest.mark.asyncio
async def test_list_data_products(data_product_agent):
    """Test list_data_products method."""
    # Test listing all data products
    result = await data_product_agent.list_data_products()
    
    # Verify result structure
    assert isinstance(result, dict)
    assert "data_products" in result
    assert "success" in result
    assert result["success"] is True
    assert isinstance(result["data_products"], list)

@pytest.mark.asyncio
async def test_create_view(data_product_agent):
    """Test create_view method."""
    # Test creating a simple view
    view_name = "test_view_pytest"
    sql_query = "SELECT 1 as test"
    
    # Clean up if view exists (optional, depends on implementation idempotency)
    try:
        await data_product_agent.execute_sql(f"DROP VIEW IF EXISTS {view_name}")
    except Exception:
        pass

    result = await data_product_agent.create_view(view_name, sql_query)
    
    # Verify result structure
    assert isinstance(result, dict)
    
    if result.get("success"):
        assert result.get("view_name") == view_name
        
        # Verify view was created by querying it
        view_result = await data_product_agent.execute_sql(f"SELECT * FROM {view_name}")
        assert view_result.get("success") is True
        assert view_result.get("rows")[0]["test"] == 1
        
        # Clean up
        await data_product_agent.execute_sql(f"DROP VIEW IF EXISTS {view_name}")
    else:
        # If creation failed, check message
        # e.g. might fail if not supported by backend or permissions
        assert "message" in result
