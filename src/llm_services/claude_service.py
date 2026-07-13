"""
Claude LLM Service for Agent9-HERMES

Provides integration with Claude models via the Anthropic Messages API.
Supports task-based model routing (Haiku for light tasks, Sonnet for complex tasks),
per-call model overrides, and guardrail enforcement.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import yaml
import anthropic
from pydantic import BaseModel, ConfigDict, Field
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Task-type constants and model routing (mirrors openai_service.py pattern)
# ---------------------------------------------------------------------------

class ClaudeTaskType:
    """Task type constants for Claude model selection"""
    SQL_GENERATION = "sql_generation"
    NLP_PARSING = "nlp_parsing"
    REASONING = "reasoning"
    SOLUTION_FINDING = "solution_finding"
    BRIEFING = "briefing"
    STAGE1_PERSONA = "stage1_persona"   # Cheap, focused single-persona call
    SYNTHESIS = "synthesis"             # Complex multi-option synthesis
    GENERAL = "general"


# Default Claude model per task type
# Haiku = cheap/fast for focused tasks; Sonnet = full power for synthesis.
# Sonnet 4.6 → Sonnet 5 (Phase 11O-B, Jul 2026): won the controlled synthesis A/B
# on the Lubricants scenario — better reasoning under contradictory evidence, 32%
# faster, same sticker price. Rollback: CLAUDE_MODEL_SYNTHESIS=claude-sonnet-4-6 etc.
# NOTE: Sonnet 5 rejects non-default sampling params — build_messages_kwargs()
# strips temperature for it (capability map above).
DEFAULT_CLAUDE_TASK_MODELS: Dict[str, str] = {
    ClaudeTaskType.SQL_GENERATION:   "claude-haiku-4-5-20251001",
    ClaudeTaskType.NLP_PARSING:      "claude-haiku-4-5-20251001",
    ClaudeTaskType.REASONING:        "claude-sonnet-5",
    ClaudeTaskType.SOLUTION_FINDING: "claude-sonnet-5",
    ClaudeTaskType.BRIEFING:         "claude-sonnet-5",
    ClaudeTaskType.STAGE1_PERSONA:   "claude-haiku-4-5-20251001",
    ClaudeTaskType.SYNTHESIS:        "claude-sonnet-5",
    ClaudeTaskType.GENERAL:          "claude-sonnet-5",
}

# Environment variable names for task-specific model overrides
CLAUDE_TASK_MODEL_ENV_VARS: Dict[str, str] = {
    ClaudeTaskType.SQL_GENERATION:   "CLAUDE_MODEL_SQL",
    ClaudeTaskType.NLP_PARSING:      "CLAUDE_MODEL_NLP",
    ClaudeTaskType.REASONING:        "CLAUDE_MODEL_REASONING",
    ClaudeTaskType.SOLUTION_FINDING: "CLAUDE_MODEL_SOLUTION",
    ClaudeTaskType.BRIEFING:         "CLAUDE_MODEL_BRIEFING",
    ClaudeTaskType.STAGE1_PERSONA:   "CLAUDE_MODEL_STAGE1",
    ClaudeTaskType.SYNTHESIS:        "CLAUDE_MODEL_SYNTHESIS",
    ClaudeTaskType.GENERAL:          "CLAUDE_MODEL",
}


def get_claude_model_for_task(task_type: str = ClaudeTaskType.GENERAL) -> str:
    """
    Get the appropriate Claude model for a given task type.

    Priority:
    1. Environment variable override for specific task
    2. General CLAUDE_MODEL environment variable
    3. Default model for task type
    """
    env_var = CLAUDE_TASK_MODEL_ENV_VARS.get(task_type)
    if env_var:
        model = os.environ.get(env_var)
        if model:
            return model

    general = os.environ.get("CLAUDE_MODEL")
    if general:
        return general

    return DEFAULT_CLAUDE_TASK_MODELS.get(task_type, DEFAULT_CLAUDE_TASK_MODELS[ClaudeTaskType.GENERAL])


# ---------------------------------------------------------------------------
# Model capability map + request builder (Phase 11O-A)
# ---------------------------------------------------------------------------

class ModelCapabilities(BaseModel):
    """API-surface flags for a Claude model family, used to build valid requests."""
    accepts_temperature: bool = True   # False → temperature/top_p/top_k return 400; omit them
    supports_effort: bool = False      # output_config.effort accepted
    server_fallbacks: bool = False     # opt into server-side refusal fallbacks (Fable 5)
    max_output_tokens: int = 128000


# Keyed by model-ID prefix; the longest matching prefix wins (so
# "claude-sonnet-4-6" beats "claude-sonnet-4-" style overlaps).
# Sonnet 5 / Opus 4.7+ / Fable 5 reject sampling params with a 400.
MODEL_CAPABILITIES: Dict[str, ModelCapabilities] = {
    "claude-haiku-4-5":  ModelCapabilities(max_output_tokens=64000),
    "claude-sonnet-4-5": ModelCapabilities(max_output_tokens=64000),
    "claude-sonnet-4-6": ModelCapabilities(supports_effort=True),
    "claude-opus-4-5":   ModelCapabilities(supports_effort=True, max_output_tokens=64000),
    "claude-opus-4-6":   ModelCapabilities(supports_effort=True),
    "claude-sonnet-5":   ModelCapabilities(accepts_temperature=False, supports_effort=True),
    "claude-opus-4-7":   ModelCapabilities(accepts_temperature=False, supports_effort=True),
    "claude-opus-4-8":   ModelCapabilities(accepts_temperature=False, supports_effort=True),
    "claude-fable-5":    ModelCapabilities(accepts_temperature=False, supports_effort=True,
                                           server_fallbacks=True),
}

# Unknown model IDs get the conservative profile: omitting sampling params is
# always valid, sending them is not. Output ceiling left high — the API gives
# a clear 400 if exceeded, whereas silent clamping would truncate synthesis.
_CONSERVATIVE_CAPABILITIES = ModelCapabilities(accepts_temperature=False)

# Server-side refusal fallback target for Fable 5 (the only supported target at launch)
FABLE_FALLBACK_MODEL = os.environ.get("CLAUDE_FABLE_FALLBACK_MODEL", "claude-opus-4-8")
_FALLBACK_BETA_HEADER = "server-side-fallback-2026-06-01"


def get_model_capabilities(model_id: str) -> ModelCapabilities:
    """Longest-prefix match against MODEL_CAPABILITIES; conservative profile for unknown IDs."""
    best: Optional[str] = None
    for prefix in MODEL_CAPABILITIES:
        if model_id.startswith(prefix) and (best is None or len(prefix) > len(best)):
            best = prefix
    if best is None:
        logger.warning(
            f"Unknown Claude model '{model_id}' — using conservative capabilities (no sampling params)"
        )
        return _CONSERVATIVE_CAPABILITIES
    return MODEL_CAPABILITIES[best]


def build_messages_kwargs(
    model: str,
    max_tokens: int,
    temperature: Optional[float],
    system: str,
    messages: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build kwargs for client.messages.create() that are valid for the target model.

    - Drops temperature for models that reject sampling params (Sonnet 5, Opus 4.7+, Fable 5).
    - Applies output_config.effort when the A9_LLM_EFFORT env var is set and the model supports it
      (unset = API default "high"). Sent via extra_body for SDK-version tolerance.
      (Deliberately NOT named CLAUDE_EFFORT — the Claude Code harness injects that
      name into its shell sessions, which would silently leak into local test runs.)
    - For Fable 5, opts into server-side refusal fallbacks so classifier false-positives
      are re-served by FABLE_FALLBACK_MODEL instead of failing the request.
    - Clamps max_tokens to the model's output ceiling (warns when clamping).
    """
    caps = get_model_capabilities(model)

    _max_tokens = max_tokens
    if max_tokens > caps.max_output_tokens:
        logger.warning(
            f"max_tokens={max_tokens} exceeds {model} output ceiling; clamping to {caps.max_output_tokens}"
        )
        _max_tokens = caps.max_output_tokens

    kwargs: Dict[str, Any] = {
        "model": model,
        "max_tokens": _max_tokens,
        "system": system,
        "messages": messages,
    }

    if caps.accepts_temperature and temperature is not None:
        kwargs["temperature"] = temperature

    extra_body: Dict[str, Any] = {}
    effort = os.environ.get("A9_LLM_EFFORT")
    if effort and caps.supports_effort:
        extra_body["output_config"] = {"effort": effort}
    if caps.server_fallbacks:
        extra_body["fallbacks"] = [{"model": FABLE_FALLBACK_MODEL}]
        kwargs["extra_headers"] = {"anthropic-beta": _FALLBACK_BETA_HEADER}
    if extra_body:
        kwargs["extra_body"] = extra_body

    return kwargs


# ---------------------------------------------------------------------------
# Config and service models
# ---------------------------------------------------------------------------

class BehaviorRule(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    description: str = ""
    pattern: str = ""
    required: bool = False


class GuardrailConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    system_prompt: str
    prohibited_patterns: List[Dict[str, str]] = []
    required_behaviors: List[BehaviorRule] = []


class PromptTemplate(BaseModel):
    model_config = ConfigDict(extra="allow")
    template_id: str
    description: str
    content: str


class ClaudeServiceConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    model_name: str = Field(
        default_factory=lambda: get_claude_model_for_task(ClaudeTaskType.GENERAL),
        description="Default Claude model. Overridden per-call via model parameter."
    )
    task_type: str = ClaudeTaskType.GENERAL
    api_key_env_var: str = "ANTHROPIC_API_KEY"
    max_tokens: int = 4096
    temperature: float = 0.7
    guardrails_path: str = "docs/cascade_guardrails.yaml"
    prompt_templates_path: str = "docs/cascade_prompt_templates.md"
    system_prompt_override: Optional[str] = None


# ---------------------------------------------------------------------------
# ClaudeService
# ---------------------------------------------------------------------------

class ClaudeService:
    """
    Service for interacting with Claude models via the Anthropic Messages API.

    Features:
    - Modern Messages API (client.messages.create)
    - Per-call model override (enables Haiku for Stage 1, Sonnet for synthesis)
    - Task-type based model routing with env var overrides
    - Guardrail system prompt enforcement
    """

    def __init__(self, config: Union[ClaudeServiceConfig, Dict[str, Any]]):
        if isinstance(config, dict):
            self.config = ClaudeServiceConfig(**config)
        else:
            self.config = config

        # Resolve API key
        api_key = getattr(self.config, "api_key", None)
        if not api_key:
            api_key = os.environ.get(self.config.api_key_env_var)
        if not api_key:
            load_dotenv(override=True)
            api_key = os.environ.get(self.config.api_key_env_var)
        if not api_key:
            raise ValueError(
                f"Anthropic API key not found — checked config and env var '{self.config.api_key_env_var}'"
            )

        masked = api_key[:8] + "***" + api_key[-4:]
        logger.info(f"Initializing Claude client (key: {masked})")

        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info(f"Anthropic SDK version: {anthropic.__version__}")

        self.guardrails = self._load_guardrails()
        self.prompt_templates = self._load_prompt_templates()

        logger.info(f"ClaudeService ready — default model: {self.config.model_name}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_guardrails(self) -> GuardrailConfig:
        try:
            with open(self.config.guardrails_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            system_prompt = (
                data.get("system_prompts", {})
                    .get("claude_sonnet_thinking", {})
                    .get("content", "")
            )
            prohibited = data.get("prohibited_patterns", [])
            behaviors: List[BehaviorRule] = []
            for bid, bdata in data.get("behaviors", {}).items():
                behaviors.append(BehaviorRule(
                    id=str(bid),
                    description=str(bdata.get("description", "")),
                    pattern=str(bdata.get("pattern", "")),
                    required=bool(bdata.get("required", False)),
                ))
            return GuardrailConfig(
                system_prompt=system_prompt,
                prohibited_patterns=prohibited,
                required_behaviors=behaviors,
            )
        except Exception as e:
            logger.warning(f"Could not load guardrails ({e}); using default system prompt")
            return GuardrailConfig(
                system_prompt="You are Cascade, an AI assistant following Agent9 standards."
            )

    def _load_prompt_templates(self) -> Dict[str, PromptTemplate]:
        templates: Dict[str, PromptTemplate] = {}
        try:
            with open(self.config.prompt_templates_path, "r", encoding="utf-8") as f:
                content = f.read()
            import re
            for title, body in re.findall(r"### ([^\n]+)\n```\n(.*?)\n```", content, re.DOTALL):
                tid = title.strip().lower().replace(" ", "_")
                templates[tid] = PromptTemplate(
                    template_id=tid,
                    description=title.strip(),
                    content=body.strip(),
                )
        except Exception as e:
            logger.warning(f"Could not load prompt templates ({e})")
        return templates

    def get_system_prompt(self) -> str:
        return self.config.system_prompt_override or self.guardrails.system_prompt

    def get_prompt_template(self, template_id: str) -> Optional[str]:
        t = self.prompt_templates.get(template_id.lower().replace(" ", "_"))
        return t.content if t else None

    def format_prompt_template(self, template_id: str, **kwargs) -> Optional[str]:
        content = self.get_prompt_template(template_id)
        if not content:
            return None
        try:
            return content.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable in template '{template_id}': {e}")
            return None

    # ------------------------------------------------------------------
    # Core generation (Messages API)
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response from Claude using the Messages API.

        Args:
            prompt:        User message content.
            system_prompt: Override system prompt (defaults to guardrails prompt).
            max_tokens:    Override max tokens.
            temperature:   Override temperature.
            model:         Override model (e.g. 'claude-haiku-4-5-20251001' for Stage 1 calls).
        """
        try:
            _system = system_prompt or self.get_system_prompt()
            _max_tokens = max_tokens or self.config.max_tokens
            _temperature = temperature if temperature is not None else self.config.temperature
            _model = model or self.config.model_name

            request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            logger.info(f"[ClaudeService] {request_id} → model={_model}, max_tokens={_max_tokens}")

            message = self.client.messages.create(
                **build_messages_kwargs(
                    model=_model,
                    max_tokens=_max_tokens,
                    temperature=_temperature,
                    system=_system,
                    messages=[{"role": "user", "content": prompt}],
                )
            )

            # Safety classifiers (Fable 5) can decline with HTTP 200 + stop_reason="refusal".
            # With server-side fallbacks enabled this only surfaces if the whole chain refused.
            if getattr(message, "stop_reason", None) == "refusal":
                details = getattr(message, "stop_details", None)
                category = getattr(details, "category", None) if details else None
                logger.warning(f"[ClaudeService] {request_id} ✗ refused (category={category})")
                return {
                    "request_id": request_id,
                    "error": f"Model declined the request (stop_reason=refusal, category={category})",
                    "model": getattr(message, "model", _model),
                    "response": None,
                    "timestamp": datetime.now().isoformat(),
                }

            # First text block — content may lead with non-text blocks (thinking,
            # fallback markers) on newer models, so don't assume content[0] is text.
            response_text = next(
                (b.text for b in (message.content or []) if getattr(b, "type", None) == "text"),
                "",
            )
            usage = {
                "prompt_tokens": message.usage.input_tokens,
                "completion_tokens": message.usage.output_tokens,
                "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
            }

            logger.info(
                f"[ClaudeService] {request_id} ✓ — "
                f"in={usage['prompt_tokens']} out={usage['completion_tokens']} tokens"
            )
            return {
                "request_id": request_id,
                # message.model reports the model that actually served the response
                # (differs from _model when a Fable refusal fell back to Opus)
                "model": getattr(message, "model", _model) or _model,
                "response": response_text,
                "usage": usage,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"[ClaudeService] generation error: {e}")
            return {
                "request_id": f"err_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "error": str(e),
                "model": model or self.config.model_name,
                "response": None,
                "timestamp": datetime.now().isoformat(),
            }

    def generate_with_template(
        self,
        template_id: str,
        template_vars: Dict[str, Any],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate using a prompt template (sync wrapper — runs via asyncio.run internally)."""
        formatted = self.format_prompt_template(template_id, **template_vars)
        if not formatted:
            return {
                "error": f"Template '{template_id}' not found or formatting error",
                "response": None,
                "timestamp": datetime.now().isoformat(),
            }
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.generate(
                prompt=formatted,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
            )
        )


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def create_claude_service(config: Union[Dict[str, Any], ClaudeServiceConfig]) -> ClaudeService:
    """Create a ClaudeService instance from a config dict or ClaudeServiceConfig."""
    try:
        service = ClaudeService(config)
        logger.info("ClaudeService created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create ClaudeService: {e}")
        raise


def create_claude_service_for_task(task_type: str, **config_overrides) -> ClaudeService:
    """Create a ClaudeService pre-configured for a specific task type."""
    model = get_claude_model_for_task(task_type)
    task_defaults = {
        ClaudeTaskType.SQL_GENERATION:   {"temperature": 0.1, "max_tokens": 2048},
        ClaudeTaskType.NLP_PARSING:      {"temperature": 0.1, "max_tokens": 1024},
        ClaudeTaskType.REASONING:        {"temperature": 0.7, "max_tokens": 8192},
        ClaudeTaskType.SOLUTION_FINDING: {"temperature": 0.7, "max_tokens": 8192},
        ClaudeTaskType.BRIEFING:         {"temperature": 0.5, "max_tokens": 4096},
        ClaudeTaskType.STAGE1_PERSONA:   {"temperature": 0.7, "max_tokens": 4096},
        ClaudeTaskType.SYNTHESIS:        {"temperature": 0.7, "max_tokens": 8192},
        ClaudeTaskType.GENERAL:          {"temperature": 0.7, "max_tokens": 4096},
    }
    config = {
        "model_name": model,
        "task_type": task_type,
        **task_defaults.get(task_type, task_defaults[ClaudeTaskType.GENERAL]),
        **config_overrides,
    }
    logger.info(f"Creating ClaudeService for task '{task_type}' with model '{model}'")
    return create_claude_service(config)
