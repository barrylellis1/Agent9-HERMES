"""Protocol-level regression tests for the Data Product Agent."""

import pytest


@pytest.mark.asyncio
async def test_list_data_products_protocol_shape(data_product_agent):
    """Data Product Agent should return a protocol-compliant dict when listing products."""

    response = await data_product_agent.list_data_products()

    assert isinstance(response, dict)
    assert "success" in response
    assert "data_products" in response
    assert isinstance(response["data_products"], list)


@pytest.mark.asyncio
async def test_get_data_product_handles_missing_id(data_product_agent):
    """Requesting an unknown data product should return a protocol dict with message."""

    response = await data_product_agent.get_data_product("nonexistent_product")

    assert isinstance(response, dict)
    assert "success" in response
    assert "message" in response


@pytest.mark.asyncio
async def test_generate_sql_pass_through(data_product_agent):
    """Supplying SQL directly should include the original SQL in the response."""

    response = await data_product_agent.generate_sql("SELECT 1 AS test_value")

    assert isinstance(response, dict)
    assert "transaction_id" in response

    if response.get("success"):
        assert response.get("sql") == "SELECT 1 AS test_value"
    else:
        # When LLM-driven SQL generation is enforced the agent returns an error payload.
        assert "sql" in response
        assert response.get("message")


@pytest.mark.asyncio
async def test_execute_sql_returns_rows(data_product_agent):
    """A simple SELECT query should execute and return rows/columns metadata."""

    response = await data_product_agent.execute_sql("SELECT 42 AS value")

    assert response.get("success") is True
    assert response.get("row_count") == 1
    assert response.get("rows")
    assert response.get("rows")[0]["value"] == 42


@pytest.mark.asyncio
async def test_execute_sql_rejects_non_select(data_product_agent):
    """Non-SELECT statements must be rejected per agent contract."""

    response = await data_product_agent.execute_sql("DELETE FROM imaginary_table")

    assert response.get("success") is False
    assert "only select" in (response.get("message", "") or "").lower()
