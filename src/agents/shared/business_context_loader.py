"""
Business Context loader utility for Agent9 debate workflows.

Parses a YAML file into A9_PS_BusinessContext and returns the model instance.
Keep YAML short and structured to control prompt length.
"""
from __future__ import annotations

from typing import Optional
import os
import yaml

from .a9_debate_protocol_models import A9_PS_BusinessContext


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
    """Attempt to load business context from a default path or env var.

    Resolution order:
    1) Env var A9_BUSINESS_CONTEXT_YAML
    2) Provided default_path

    Returns None if no file is found/resolvable.
    """
    env_path = os.environ.get("A9_BUSINESS_CONTEXT_YAML", "").strip()
    candidate = env_path or (default_path or "")
    if candidate and os.path.exists(candidate):
        try:
            return load_business_context_from_yaml(candidate)
        except Exception:
            # Caller may handle/log; return None on failure to remain non-intrusive
            return None
    return None
