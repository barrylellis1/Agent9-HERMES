"""
A9_LLM_Service_Agent.analyze() — the FAILURE branch (2026-08-09).

WHY THIS FILE EXISTS
--------------------
A one-word bug shipped and reached a live run:

    self.logger.error(...)   # this class has no self.logger; line 40 defines
                             # a MODULE-level `logger`

It sat on the parse-failure path. When a response failed to parse, the
diagnostic line itself raised AttributeError, the exception propagated out of
analyze(), the call returned status="error", and Solution Finder fell through
to its heuristic stub — presenting "Tighten spend controls" to a user and
DESTROYING the very error the line was added to capture.

It shipped despite 891 passing tests because every one of them exercised
`parse_llm_json` **as a pure function**. Nothing exercised the agent's error
branch. A guard that has never been executed is not a guard.

So these tests drive `analyze()` itself, with the LLM stubbed, and assert the
failure path behaves — not just the happy path.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.new.a9_llm_service_agent import (
    A9_LLM_AnalysisRequest,
    A9_LLM_Service_Agent,
)


def _request(request_id: str = "req_parse_fail") -> A9_LLM_AnalysisRequest:
    # The compliance regex matches any A9_-prefixed symbol and cannot tell an
    # agent from its request model; building a Pydantic request directly is the
    # intended pattern. Token must sit on the violating line itself.
    return A9_LLM_AnalysisRequest(  # arch-allow-agent-ctor — request model, not an agent
        request_id=request_id, principal_id="cfo_001",
        content="analyse this", analysis_type="custom", context="",
    )


async def _agent(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    return await A9_LLM_Service_Agent.create({"provider": "anthropic"})


def _generate_returning(content: str):
    """Stub the underlying generate() so analyze() sees a successful call whose
    CONTENT is what we control — that is where parsing happens."""
    return AsyncMock(return_value=SimpleNamespace(
        status="success", content=content, model_used="claude-sonnet-5",
        usage={"prompt_tokens": 10, "completion_tokens": 20}, error_message=None,
    ))


class TestParseFailureBranch:
    @pytest.mark.asyncio
    async def test_unparseable_response_does_not_raise(self, monkeypatch):
        """REGRESSION: the diagnostic line crashed here and took the run with it."""
        agent = await _agent(monkeypatch)
        # Unquoted range — invalid JSON, and beyond what repair should attempt.
        bad = '{"options": [{"id": "opt_1", "impact": 18.5-26.3}]}'
        with patch.object(agent, "generate", _generate_returning(bad)):
            resp = await agent.analyze(_request())
        assert resp.status == "success", "a parse failure must degrade, not error the call"
        assert isinstance(resp.analysis, dict)

    @pytest.mark.asyncio
    async def test_failure_preserves_the_diagnostic(self, monkeypatch):
        agent = await _agent(monkeypatch)
        bad = '{"options": [{"id": "opt_1", "impact": 18.5-26.3}]}'
        with patch.object(agent, "generate", _generate_returning(bad)):
            resp = await agent.analyze(_request())
        assert "raw_response" in resp.analysis
        pe = resp.analysis.get("_parse_error")
        assert pe, "the decode error must survive — losing it cost a day of forensics"
        assert "msg" in pe and "pos" in pe and "context" in pe
        assert resp.confidence == 0.5

    @pytest.mark.asyncio
    async def test_logging_on_the_failure_path_is_actually_executed(self, monkeypatch):
        """Directly pins the bug: the logger call must not raise.

        Patching the module logger proves the line RUNS, rather than inferring it
        from the absence of an exception elsewhere.
        """
        agent = await _agent(monkeypatch)
        with patch("src.agents.new.a9_llm_service_agent.logger") as mock_log, \
             patch.object(agent, "generate", _generate_returning("not json at all")):
            resp = await agent.analyze(_request())
        assert mock_log.error.called, "the failure path must log"
        assert resp.status == "success"

    @pytest.mark.asyncio
    async def test_agent_has_no_self_logger(self, monkeypatch):
        """The specific mistake, asserted so it cannot silently return.

        If a future change adds self.logger this test fails loudly and can be
        deleted deliberately — better than the attribute quietly reappearing and
        masking whether call sites are correct.
        """
        agent = await _agent(monkeypatch)
        assert not hasattr(agent, "logger"), \
            "this class logs via the module-level `logger`; call sites must not use self.logger"


class TestHappyPathStillWorks:
    @pytest.mark.asyncio
    async def test_valid_json_parses(self, monkeypatch):
        agent = await _agent(monkeypatch)
        with patch.object(agent, "generate", _generate_returning('{"options": [{"id": "opt_1"}]}')):
            resp = await agent.analyze(_request())
        assert resp.status == "success"
        assert resp.analysis["options"][0]["id"] == "opt_1"
        assert "_parse_error" not in resp.analysis

    @pytest.mark.asyncio
    async def test_fenced_json_parses(self, monkeypatch):
        agent = await _agent(monkeypatch)
        fenced = '```json\n{"options": [{"id": "opt_2"}]}\n```'
        with patch.object(agent, "generate", _generate_returning(fenced)):
            resp = await agent.analyze(_request())
        assert resp.analysis["options"][0]["id"] == "opt_2"

    @pytest.mark.asyncio
    async def test_repaired_json_is_marked(self, monkeypatch):
        agent = await _agent(monkeypatch)
        with patch.object(agent, "generate", _generate_returning('Here you go: {"options": []}')):
            resp = await agent.analyze(_request())
        assert resp.analysis.get("_parse_repair") == "outermost_object"

    @pytest.mark.asyncio
    async def test_upstream_error_still_returns_error(self, monkeypatch):
        # A genuine generation failure must NOT be dressed up as success.
        agent = await _agent(monkeypatch)
        failed = AsyncMock(return_value=SimpleNamespace(
            status="error", content=None, model_used=None, usage={},
            error_message="credit balance too low"))
        with patch.object(agent, "generate", failed):
            resp = await agent.analyze(_request())
        assert resp.status == "error"
        assert "credit" in (resp.error_message or "")
