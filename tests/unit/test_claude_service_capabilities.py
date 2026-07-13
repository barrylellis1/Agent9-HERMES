"""
Phase 11O-A unit tests — capability-aware request builder in claude_service.py.

Covers:
- Sampling params dropped for model families that reject them (Fable 5, Opus 4.8, Sonnet 5)
- Sampling params preserved for current routing-table models (Sonnet 4.6, Haiku 4.5)
- Unknown model IDs get the conservative profile (no sampling params)
- Fable 5 opts into server-side refusal fallbacks (beta header + fallbacks body)
- A9_LLM_EFFORT applied only where supported
- stop_reason == "refusal" surfaces as an error dict, never as content
"""

import pytest
from unittest.mock import MagicMock, patch

from src.llm_services.claude_service import (
    ClaudeService,
    FABLE_FALLBACK_MODEL,
    build_messages_kwargs,
    get_model_capabilities,
)

_MESSAGES = [{"role": "user", "content": "hello"}]


def _kwargs(model, temperature=0.7, max_tokens=1024):
    return build_messages_kwargs(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system="system prompt",
        messages=_MESSAGES,
    )


def test_temperature_dropped_for_new_generation_models():
    for model in ("claude-fable-5", "claude-opus-4-8", "claude-opus-4-7", "claude-sonnet-5"):
        kw = _kwargs(model)
        assert "temperature" not in kw, f"{model} must not receive temperature (API returns 400)"


def test_temperature_preserved_for_current_models():
    for model in ("claude-sonnet-4-6", "claude-haiku-4-5-20251001"):
        kw = _kwargs(model)
        assert kw["temperature"] == 0.7, f"{model} should keep explicit temperature"


def test_unknown_model_gets_conservative_profile():
    kw = _kwargs("claude-nova-9")
    assert "temperature" not in kw  # omission is always valid; sending may 400
    assert "extra_body" not in kw   # no effort, no fallbacks for unknown families
    caps = get_model_capabilities("claude-nova-9")
    assert caps.accepts_temperature is False


def test_longest_prefix_wins():
    # "claude-sonnet-4-5" and "claude-sonnet-4-6" must not resolve to each other
    assert get_model_capabilities("claude-sonnet-4-6").supports_effort is True
    assert get_model_capabilities("claude-sonnet-4-5-20250929").supports_effort is False
    # dated Haiku ID resolves through its family prefix
    assert get_model_capabilities("claude-haiku-4-5-20251001").accepts_temperature is True


def test_fable_opts_into_server_side_fallbacks():
    kw = _kwargs("claude-fable-5")
    assert kw["extra_headers"]["anthropic-beta"] == "server-side-fallback-2026-06-01"
    assert kw["extra_body"]["fallbacks"] == [{"model": FABLE_FALLBACK_MODEL}]


def test_non_fable_models_do_not_get_fallbacks():
    for model in ("claude-sonnet-4-6", "claude-sonnet-5", "claude-opus-4-8"):
        kw = _kwargs(model)
        assert "extra_headers" not in kw
        assert "fallbacks" not in kw.get("extra_body", {})


def test_effort_env_applied_only_where_supported(monkeypatch):
    monkeypatch.setenv("A9_LLM_EFFORT", "medium")
    kw = _kwargs("claude-sonnet-5")
    assert kw["extra_body"]["output_config"] == {"effort": "medium"}
    # Haiku 4.5 rejects output_config.effort — must not be sent
    kw_haiku = _kwargs("claude-haiku-4-5-20251001")
    assert "output_config" not in kw_haiku.get("extra_body", {})


def test_effort_omitted_when_env_unset(monkeypatch):
    monkeypatch.delenv("A9_LLM_EFFORT", raising=False)
    kw = _kwargs("claude-sonnet-5")
    assert "output_config" not in kw.get("extra_body", {})


def test_max_tokens_clamped_to_model_ceiling():
    kw = _kwargs("claude-haiku-4-5-20251001", max_tokens=200000)
    assert kw["max_tokens"] == 64000


def _make_service(mock_client_cls, message):
    mock_client_cls.return_value.messages.create.return_value = message
    return ClaudeService({"model_name": "claude-fable-5", "api_key": "test-key"})


@pytest.mark.asyncio
async def test_refusal_stop_reason_returns_error_dict():
    refusal = MagicMock()
    refusal.stop_reason = "refusal"
    refusal.model = "claude-fable-5"
    refusal.content = []
    refusal.stop_details = MagicMock(category="cyber")
    with patch("src.llm_services.claude_service.anthropic.Anthropic") as mock_cls:
        service = _make_service(mock_cls, refusal)
        result = await service.generate(prompt="hello")
    assert result["response"] is None
    assert "refusal" in result["error"]
    assert "cyber" in result["error"]


@pytest.mark.asyncio
async def test_text_extraction_skips_non_text_leading_blocks():
    # Fable responses can lead with fallback/thinking blocks — content[0] is not
    # guaranteed to be the text block.
    fallback_block = MagicMock(spec=[])
    fallback_block.type = "fallback"
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "the answer"
    message = MagicMock()
    message.stop_reason = "end_turn"
    message.model = "claude-opus-4-8"  # served by the fallback model
    message.content = [fallback_block, text_block]
    message.usage.input_tokens = 10
    message.usage.output_tokens = 5
    with patch("src.llm_services.claude_service.anthropic.Anthropic") as mock_cls:
        service = _make_service(mock_cls, message)
        result = await service.generate(prompt="hello")
    assert result["response"] == "the answer"
    assert result["model"] == "claude-opus-4-8"  # reports the model that served
