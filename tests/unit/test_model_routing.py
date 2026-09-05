"""
Unit tests for `src.llm_services.model_routing`.

The routing layer exists so call sites name the *kind of work* rather than a
vendor's model ID. The single most important property is negative: converting
every call site must not change which model Anthropic serves, because Anthropic
is the configured production provider and this refactor is meant to enable a
model comparison, not to perform one by accident.
"""

import os

import pytest

from src.llm_services.claude_service import get_claude_model_for_task
from src.llm_services.model_routing import (
    ALL_TASK_TYPES,
    TaskType,
    provider_of,
    resolve_model,
)
from src.llm_services.openai_service import get_model_for_task


class TestAnthropicUnchanged:
    """The production path must resolve exactly what it resolved before."""

    @pytest.mark.parametrize("task", ALL_TASK_TYPES)
    def test_matches_claude_routing_table_exactly(self, task):
        assert resolve_model("anthropic", task) == get_claude_model_for_task(task)

    def test_default_provider_is_anthropic(self):
        # An unset/unknown provider must not silently route to OpenAI.
        assert resolve_model(None, TaskType.SYNTHESIS).startswith("claude-")
        assert resolve_model("", TaskType.SYNTHESIS).startswith("claude-")
        assert resolve_model("something-else", TaskType.SYNTHESIS).startswith("claude-")

    def test_case_insensitive_provider(self):
        assert resolve_model("Anthropic", TaskType.GENERAL) == resolve_model(
            "anthropic", TaskType.GENERAL
        )
        assert resolve_model("OpenAI", TaskType.GENERAL) == resolve_model(
            "openai", TaskType.GENERAL
        )


class TestProviderParity:
    @pytest.mark.parametrize("task", ALL_TASK_TYPES)
    def test_every_task_type_resolves_on_both_providers(self, task):
        # A task type that only one provider knows would silently fall back to
        # that provider's GENERAL model, quietly changing the comparison.
        assert resolve_model("anthropic", task).startswith("claude-")
        assert resolve_model("openai", task).startswith("gpt-")

    @pytest.mark.parametrize("task", ALL_TASK_TYPES)
    def test_openai_table_covers_task_type_explicitly(self, task):
        from src.llm_services.openai_service import DEFAULT_TASK_MODELS

        assert task in DEFAULT_TASK_MODELS, f"{task} would fall through to GENERAL"

    def test_cheap_and_full_power_tiers_agree_across_providers(self):
        # Both providers must put the same tasks on the cheap tier, or a
        # comparison measures the routing choice rather than the models.
        cheap = {TaskType.SQL_GENERATION, TaskType.NLP_PARSING, TaskType.STAGE1_PERSONA}
        for task in cheap:
            assert resolve_model("anthropic", task) == resolve_model(
                "anthropic", TaskType.NLP_PARSING
            )
            assert resolve_model("openai", task) == resolve_model(
                "openai", TaskType.NLP_PARSING
            )


class TestEnvOverrides:
    def test_claude_per_task_override(self, monkeypatch):
        monkeypatch.setenv("CLAUDE_MODEL_SYNTHESIS", "claude-opus-4-8")
        assert resolve_model("anthropic", TaskType.SYNTHESIS) == "claude-opus-4-8"

    def test_openai_per_task_override(self, monkeypatch):
        monkeypatch.setenv("OPENAI_MODEL_SYNTHESIS", "gpt-6-astra")
        assert resolve_model("openai", TaskType.SYNTHESIS) == "gpt-6-astra"

    def test_override_is_provider_scoped(self, monkeypatch):
        # An OpenAI override must not leak into Anthropic resolution.
        monkeypatch.setenv("OPENAI_MODEL_SYNTHESIS", "gpt-6-astra")
        assert resolve_model("anthropic", TaskType.SYNTHESIS).startswith("claude-")


class TestUnknownTaskType:
    def test_falls_back_to_general_with_a_warning(self, caplog):
        with caplog.at_level("WARNING"):
            got = resolve_model("anthropic", "not_a_real_task")
        assert got == resolve_model("anthropic", TaskType.GENERAL)
        assert "not_a_real_task" in caplog.text

    def test_none_resolves_to_general(self):
        assert resolve_model("anthropic", None) == resolve_model(
            "anthropic", TaskType.GENERAL
        )


class TestProviderOf:
    @pytest.mark.parametrize(
        "model,expected",
        [
            ("claude-sonnet-5", "anthropic"),
            ("claude-haiku-4-5-20251001", "anthropic"),
            ("gpt-6-astra", "openai"),
            ("gpt-5.6-terra", "openai"),
            ("gpt-4-turbo", "openai"),
            ("llama-3", None),
            ("", None),
            (None, None),
        ],
    )
    def test_detects_provider(self, model, expected):
        assert provider_of(model) == expected


class TestCallSitesUseTaskTypes:
    """Guards the refactor itself: a call site regressing to a hardcoded Claude
    model ID would silently pin that call to Anthropic on every provider."""

    CALLERS = [
        "src/agents/new/a9_solution_finder_agent.py",
        "src/agents/new/a9_situation_awareness_agent.py",
        "src/agents/new/a9_deep_analysis_agent.py",
        "src/agents/new/a9_market_analysis_agent.py",
        "src/agents/new/a9_value_assurance_agent.py",
        "src/api/routes/workflows.py",
    ]

    @pytest.mark.parametrize("path", CALLERS)
    def test_no_caller_resolves_claude_models_directly(self, path):
        src = open(path, encoding="utf-8").read()
        assert "get_claude_model_for_task" not in src, (
            f"{path} resolves a Claude model ID directly; pass task_type instead"
        )

    @pytest.mark.parametrize("path", CALLERS)
    def test_no_caller_hardcodes_a_model_id(self, path):
        src = open(path, encoding="utf-8").read()
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue  # comments may legitimately name models
            assert 'model="claude-' not in stripped and "model='claude-" not in stripped, (
                f"{path} hardcodes a Claude model ID: {stripped[:80]}"
            )


class TestProviderKeyPairing:
    """`api_key_env_var` defaults from the LLM_PROVIDER env var, which can only
    describe one provider. Constructing both in a single process — exactly what a
    model bake-off does — paired the OpenAI provider with ANTHROPIC_API_KEY and
    sent an `sk-ant-...` key to OpenAI (401 invalid_api_key, observed live)."""

    def test_explicit_provider_selects_its_own_key(self, monkeypatch):
        from src.agents.agent_config_models import A9_LLM_Service_Agent_Config

        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        assert A9_LLM_Service_Agent_Config(provider="openai").api_key_env_var == "OPENAI_API_KEY"  # arch-allow-agent-ctor — config model, not an agent
        assert A9_LLM_Service_Agent_Config(provider="anthropic").api_key_env_var == "ANTHROPIC_API_KEY"  # arch-allow-agent-ctor — config model, not an agent

        monkeypatch.setenv("LLM_PROVIDER", "openai")
        assert A9_LLM_Service_Agent_Config(provider="anthropic").api_key_env_var == "ANTHROPIC_API_KEY"  # arch-allow-agent-ctor — config model, not an agent
        assert A9_LLM_Service_Agent_Config(provider="openai").api_key_env_var == "OPENAI_API_KEY"  # arch-allow-agent-ctor — config model, not an agent

    def test_explicit_key_env_var_still_wins(self, monkeypatch):
        from src.agents.agent_config_models import A9_LLM_Service_Agent_Config

        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        cfg = A9_LLM_Service_Agent_Config(provider="openai", api_key_env_var="OPENAI_SOL_KEY")  # arch-allow-agent-ctor — config model, not an agent
        assert cfg.api_key_env_var == "OPENAI_SOL_KEY"

    def test_env_only_construction_unchanged(self, monkeypatch):
        from src.agents.agent_config_models import A9_LLM_Service_Agent_Config

        monkeypatch.setenv("LLM_PROVIDER", "openai")
        cfg = A9_LLM_Service_Agent_Config()  # arch-allow-agent-ctor — config model, not an agent
        assert (cfg.provider, cfg.api_key_env_var) == ("openai", "OPENAI_API_KEY")
