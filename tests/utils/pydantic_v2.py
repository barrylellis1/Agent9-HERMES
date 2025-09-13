"""
Pydantic v2 test utilities for Agent9.

Use these helpers in tests to ensure consistent Pydantic v2 APIs
and to avoid accidental regression to v1 methods.
"""
from __future__ import annotations

from typing import Any, Dict, Type, TypeVar, Generic
from pydantic import BaseModel
from pydantic.type_adapter import TypeAdapter

T = TypeVar("T")
M = TypeVar("M", bound=BaseModel)


def validate_model(model_cls: Type[M], data: Dict[str, Any]) -> M:
    """Validate a dict into a Pydantic v2 model instance using model_validate."""
    return model_cls.model_validate(data)


def dump_model(model: BaseModel, *, by_alias: bool = False) -> Dict[str, Any]:
    """Dump a model to dict using model_dump (v2)."""
    return model.model_dump(by_alias=by_alias)


def dump_model_json(model: BaseModel, *, by_alias: bool = False) -> str:
    """Dump a model to JSON using model_dump_json (v2)."""
    return model.model_dump_json(by_alias=by_alias)


def validate_as(type_hint: Any, value: Any) -> Any:
    """Validate a Python value against a typing hint using TypeAdapter (v2)."""
    adapter = TypeAdapter(type_hint)
    return adapter.validate_python(value)


def safe_copy(model: BaseModel, *, deep: bool = False, update: Dict[str, Any] | None = None) -> BaseModel:
    """Copy a model using model_copy (v2)."""
    return model.model_copy(deep=deep, update=update or {})


__all__ = [
    "validate_model",
    "dump_model",
    "dump_model_json",
    "validate_as",
    "safe_copy",
]
