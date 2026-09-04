"""
Provider-neutral task → model routing.

Agent call sites used to resolve a *Claude* model ID directly
(`get_claude_model_for_task(ClaudeTaskType.SYNTHESIS)`) and pass the resulting
string as `A9_LLM_Request.model`. That hardcodes provider vocabulary into every
caller: flipping `LLM_PROVIDER=openai` sent literal "claude-sonnet-5" to
OpenAI's API, and the only way to run the same pipeline on another provider was
to edit each call site.

A caller knows what *kind of work* it needs — a cheap focused persona call, a
full-power synthesis — but has no business knowing which vendor's model serves
that today. So callers now pass `task_type` and this module resolves it for
whichever provider is configured.

Task types are the union of both providers' vocabularies (Claude's is the
superset in practice). Each provider keeps its own routing table and env-var
overrides; this is a dispatcher, not a second source of truth.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TaskType:
    """Canonical, provider-neutral task types.

    Values match `ClaudeTaskType` and `openai_service.TaskType` so a string from
    either is accepted unchanged.
    """

    SQL_GENERATION = "sql_generation"
    NLP_PARSING = "nlp_parsing"
    REASONING = "reasoning"
    SOLUTION_FINDING = "solution_finding"
    BRIEFING = "briefing"
    STAGE1_PERSONA = "stage1_persona"
    SYNTHESIS = "synthesis"
    CRITIC = "critic"
    GENERAL = "general"


ALL_TASK_TYPES = (
    TaskType.SQL_GENERATION,
    TaskType.NLP_PARSING,
    TaskType.REASONING,
    TaskType.SOLUTION_FINDING,
    TaskType.BRIEFING,
    TaskType.STAGE1_PERSONA,
    TaskType.SYNTHESIS,
    TaskType.CRITIC,
    TaskType.GENERAL,
)


def resolve_model(provider: str, task_type: Optional[str] = None) -> str:
    """Resolve the model serving `task_type` on `provider`.

    Delegates to the provider's own routing table so per-task env-var overrides
    (CLAUDE_MODEL_SYNTHESIS, OPENAI_MODEL_SYNTHESIS, …) keep working untouched.
    """
    task = task_type or TaskType.GENERAL
    if task not in ALL_TASK_TYPES:
        logger.warning(
            f"Unknown task_type {task!r}; falling back to {TaskType.GENERAL!r}. "
            f"Known: {ALL_TASK_TYPES}"
        )
        task = TaskType.GENERAL

    name = (provider or "anthropic").lower()
    if name == "openai":
        from src.llm_services.openai_service import get_model_for_task

        return get_model_for_task(task)

    # Anthropic is the default provider; an unrecognised name resolving here
    # rather than raising matches the agent's own behaviour of treating
    # anthropic as the fallback.
    from src.llm_services.claude_service import get_claude_model_for_task

    return get_claude_model_for_task(task)


def provider_of(model_name: str) -> Optional[str]:
    """Best-effort provider for a model ID, or None if unrecognised.

    Used to detect a cross-provider model ID arriving from a call site that has
    not yet been converted to task types.
    """
    m = str(model_name or "")
    if m.startswith("claude-"):
        return "anthropic"
    if m.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    return None
