# tests/unit/test_a9_nlp_interface_agent_v2.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.agents.a9_nlp_interface_agent_v2 import A9_NLP_Interface_Agent_V2
from src.agents.utils.exceptions import LLMGenerationError
from src.models.llm_models import LLMRequest, LLMResponse

@pytest.mark.asyncio
async def test_generate_sql_query_success(nlp_agent):
    """Tests successful SQL query generation."""
    base_query = "SELECT SUM(revenue) FROM Sales"
    schema = {"revenue": "DECIMAL", "date": "DATE"}
    expected_sql = "SELECT SUM(revenue) FROM Sales WHERE date > '2023-01-01'"

    # Mock the orchestrator's route_request method
    with patch('src.agents.agent_registry.registry.get_agent') as mock_get_agent:
        mock_orchestrator = AsyncMock()
        mock_orchestrator.route_request.return_value = {"response": expected_sql}
        mock_get_agent.return_value = mock_orchestrator

        result_sql = await nlp_agent.generate_sql_query(base_query, schema)

        assert result_sql == expected_sql
        mock_orchestrator.route_request.assert_called_once()

@pytest.mark.asyncio
async def test_generate_sql_query_llm_failure(nlp_agent, mocker):
    """Tests graceful failure when the LLM service raises an error."""
    base_query = "SELECT SUM(revenue) FROM Sales"
    schema = {"revenue": "DECIMAL", "date": "DATE"}

    # Mock the orchestrator's route_request method to raise the custom exception
    mock_orchestrator = AsyncMock()
    mock_orchestrator.route_request.side_effect = LLMGenerationError("API Quota Exceeded")
    mocker.patch('src.agents.agent_registry.registry.get_agent', return_value=mock_orchestrator)

    # Act
    result_sql = await nlp_agent.generate_sql_query(base_query, schema)

    # Assert
    assert result_sql == ""
    mock_orchestrator.route_request.assert_called_once()
