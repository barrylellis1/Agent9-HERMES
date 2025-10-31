"""LLM SQL generation workflow tests with orchestrator-managed agent."""

import importlib
import os
import sys
from types import SimpleNamespace

import pytest


class _StubLLMService:
    """Async stub for the LLM Service Agent."""

    def __init__(self, response: SimpleNamespace):
        self._response = response
        self.requests = []

    async def generate_sql(self, request):  # pragma: no cover - exercised via tests
        self.requests.append(request)
        return self._response


async def _build_agent_with_stub(registry_factory, monkeypatch, tmp_path, llm_service):
    db_path = tmp_path / "llm_stub.duckdb"

    class _FakeOrchestrator:
        def __init__(self, stub):
            self.stub = stub

        async def get_agent(self, name, config=None):  # pragma: no cover - exercised via tests
            if name == "A9_LLM_Service_Agent":
                return self.stub
            return None

        async def register_agent(self, name, agent):  # pragma: no cover - exercised via tests
            return True

    config = {
        "data_directory": str(tmp_path),
        "database": {"type": "duckdb", "path": str(db_path)},
        "registry_factory": registry_factory,
        "bypass_mcp": True,
        "enable_llm_sql": True,
        "force_llm_sql": True,
        "llm_service_agent": llm_service,
        "orchestrator": _FakeOrchestrator(llm_service),
    }
    from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
    agent = await A9_Data_Product_Agent.create(config)
    return agent


@pytest.mark.asyncio
async def test_generate_sql_uses_llm_stub(registry_bootstrap, monkeypatch, tmp_path):
    """Data Product Agent should delegate natural language SQL generation to the LLM stub."""

    monkeypatch.setenv("A9_ENABLE_LLM_SQL", "true")
    monkeypatch.delenv("A9_FORCE_LLM_SQL", raising=False)

    fake_response = SimpleNamespace(
        status="success",
        sql_query="SELECT 1 AS metric_value",
        error_message=None,
        warnings=None,
    )
    stub = _StubLLMService(fake_response)
    agent = await _build_agent_with_stub(registry_bootstrap, monkeypatch, tmp_path, stub)

    try:
        response = await agent.generate_sql("total revenue last quarter", context={"data_product_id": "fi_star_schema"})
    finally:
        await agent.disconnect()

    assert stub.requests, "LLM stub should receive the generation request"
    assert response.get("success") is True
    assert response.get("sql") == "SELECT 1 AS metric_value"
    assert "transaction_id" in response


@pytest.mark.asyncio
async def test_generate_sql_handles_llm_failure(registry_bootstrap, monkeypatch, tmp_path):
    """When the LLM service returns an error the agent should surface a failure payload."""

    monkeypatch.setenv("A9_ENABLE_LLM_SQL", "true")
    monkeypatch.setenv("A9_FORCE_LLM_SQL", "true")

    failing_response = SimpleNamespace(
        status="error",
        sql_query="",
        error_message="LLM unavailable",
        warnings=None,
    )
    stub = _StubLLMService(failing_response)
    agent = await _build_agent_with_stub(registry_bootstrap, monkeypatch, tmp_path, stub)

    try:
        result = await agent.generate_sql("gross margin by product", context={"data_product_id": "fi_star_schema"})
    finally:
        await agent.disconnect()

    assert stub.requests, "LLM stub should be invoked even on failure paths"
    assert result.get("success") is False
    assert "transaction_id" in result
    assert "sql" in result  # agent returns an empty SQL string when force flag is enabled
