"""
Business Context loader utility for Agent9 debate workflows.

Parses a YAML file into A9_PS_BusinessContext and returns the model instance.
Keep YAML short and structured to control prompt length.

Supports both YAML and Supabase backends via environment variables:
- BUSINESS_CONTEXT_BACKEND: "yaml" or "supabase" (default: yaml)
- A9_BUSINESS_CONTEXT: context ID for Supabase (e.g., demo_bicycle, demo_lubricants)
- A9_BUSINESS_CONTEXT_YAML: path to YAML file (legacy, for YAML backend)
"""
from __future__ import annotations

from typing import Optional
import os
import yaml
import logging
import asyncio

from .a9_debate_protocol_models import A9_PS_BusinessContext

logger = logging.getLogger(__name__)


def load_business_context_from_yaml(file_path: str) -> A9_PS_BusinessContext:
    """Load business context from a YAML file into an A9_PS_BusinessContext model.

    Args:
        file_path: Path to YAML file.

    Returns:
        A9_PS_BusinessContext instance.

    Raises:
        FileNotFoundError: if the YAML file does not exist
        ValueError: if the YAML content is invalid for the model
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Business context YAML not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("Business context YAML must define a mapping at the root")

    return A9_PS_BusinessContext(**data)


def try_load_business_context(default_path: Optional[str] = None) -> Optional[A9_PS_BusinessContext]:
    """Attempt to load business context from Supabase or YAML.

    Resolution order:
    1) If BUSINESS_CONTEXT_BACKEND=supabase: Load from Supabase using A9_BUSINESS_CONTEXT env var
    2) Env var A9_BUSINESS_CONTEXT_YAML (path to YAML file)
    3) Provided default_path

    Returns None if no context is found/resolvable.
    """
    backend = os.getenv("BUSINESS_CONTEXT_BACKEND", "yaml").lower()
    
    # Try Supabase backend first if configured
    if backend == "supabase":
        context_id = os.getenv("A9_BUSINESS_CONTEXT", "").strip()
        if context_id:
            try:
                from src.registry.business_context.business_context_provider import get_business_context
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    context = loop.run_until_complete(get_business_context(context_id))
                    if context:
                        logger.info(f"Loaded business context '{context_id}' from Supabase")
                        return context
                finally:
                    loop.close()
            except Exception as e:
                logger.warning(f"Failed to load from Supabase: {e}, falling back to YAML")
    
    # Fallback to YAML
    env_path = os.environ.get("A9_BUSINESS_CONTEXT_YAML", "").strip()
    candidate = env_path or (default_path or "")
    if candidate and os.path.exists(candidate):
        try:
            context = load_business_context_from_yaml(candidate)
            logger.info(f"Loaded business context from YAML: {candidate}")
            return context
        except Exception as e:
            logger.warning(f"Failed to load from YAML: {e}")
            return None
    
    return None
