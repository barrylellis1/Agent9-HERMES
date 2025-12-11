"""Reusable helpers for Decision Studio admin onboarding workflow API calls."""

from __future__ import annotations

import os
import time
from typing import Any, Callable, Dict, Mapping, Optional

import httpx


DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1"
DEFAULT_ONBOARDING_POLL_INTERVAL_SECONDS = 2.0
TERMINAL_WORKFLOW_STATES = {"completed", "failed"}


def get_api_base_url(env: Optional[Mapping[str, str]] = None) -> str:
    """Resolve the base URL for workflow API requests."""

    env = env or os.environ
    raw = (env.get("A9_API_BASE_URL") or DEFAULT_API_BASE_URL).strip()
    return raw.rstrip("/") if raw else DEFAULT_API_BASE_URL


def is_terminal_admin_onboarding_state(state: Optional[str]) -> bool:
    """Return True when the workflow state is terminal."""

    return state in TERMINAL_WORKFLOW_STATES


def build_onboarding_api_payload(request_model: Any) -> Dict[str, Any]:
    """Convert the workflow request model to a payload accepted by the API."""

    payload = request_model.model_dump()
    payload.pop("request_id", None)
    return payload


def schedule_admin_onboarding_poll(
    state: Any,
    delay_seconds: float = DEFAULT_ONBOARDING_POLL_INTERVAL_SECONDS,
) -> None:
    """Schedule the next poll attempt for the admin onboarding workflow."""

    _set_state_value(state, "admin_onboarding_next_poll", time.monotonic() + delay_seconds)
    _set_state_value(state, "admin_onboarding_poll_in_progress", False)


def reset_admin_onboarding_polling_state(state: Any) -> None:
    """Reset polling flags for the admin onboarding workflow."""

    _set_state_value(state, "admin_onboarding_next_poll", None)
    _set_state_value(state, "admin_onboarding_poll_in_progress", False)


async def submit_admin_onboarding_via_api(
    state: Any,
    request_model: Any,
    *,
    base_url: Optional[str] = None,
    client_factory: Optional[Callable[..., httpx.AsyncClient]] = None,
) -> bool:
    """Submit the onboarding workflow through the API and prime polling."""

    base_url = base_url or get_api_base_url()
    run_url = f"{base_url}/workflows/data-product-onboarding/run"
    payload = build_onboarding_api_payload(request_model)

    client_factory = client_factory or httpx.AsyncClient

    async with client_factory(timeout=30.0) as client:
        response = await client.post(run_url, json=payload)
        response.raise_for_status()

    envelope = response.json()  # httpx Response.json(), not Pydantic  # pydantic-lint: allow
    data = envelope.get("data") or {}
    request_id = data.get("request_id")
    if not request_id:
        raise ValueError("Workflow response missing request_id")

    _set_state_value(state, "admin_onboarding_request_id", request_id)
    _set_state_value(state, "admin_onboarding_status", data.get("state", "pending"))
    _set_state_value(state, "admin_onboarding_error", None)
    _set_state_value(state, "admin_onboarding_result", None)

    schedule_admin_onboarding_poll(state)
    return True


async def maybe_poll_admin_onboarding_status(
    state: Any,
    *,
    base_url: Optional[str] = None,
    client_factory: Optional[Callable[..., httpx.AsyncClient]] = None,
) -> None:
    """Poll the workflow status endpoint when a request is in-flight."""

    request_id = _get_state_value(state, "admin_onboarding_request_id")
    if not request_id:
        return

    current_status = _get_state_value(state, "admin_onboarding_status")
    if is_terminal_admin_onboarding_state(current_status):
        reset_admin_onboarding_polling_state(state)
        return

    next_poll_at = _get_state_value(state, "admin_onboarding_next_poll")
    if next_poll_at is not None and time.monotonic() < next_poll_at:
        return

    if _get_state_value(state, "admin_onboarding_poll_in_progress"):
        return

    base_url = base_url or get_api_base_url()
    status_url = f"{base_url}/workflows/data-product-onboarding/{request_id}/status"
    client_factory = client_factory or httpx.AsyncClient

    _set_state_value(state, "admin_onboarding_poll_in_progress", True)
    try:
        async with client_factory(timeout=30.0) as client:
            response = await client.get(status_url)
            response.raise_for_status()
        envelope = response.json()  # httpx Response.json(), not Pydantic  # pydantic-lint: allow
        data = envelope.get("data") or {}
        new_state = data.get("state", current_status)
        _set_state_value(state, "admin_onboarding_status", new_state)

        error_message = data.get("error")
        _set_state_value(state, "admin_onboarding_error", error_message)

        result_payload = data.get("result")
        if result_payload is not None:
            _set_state_value(state, "admin_onboarding_result", result_payload)

        if is_terminal_admin_onboarding_state(new_state):
            reset_admin_onboarding_polling_state(state)
        else:
            schedule_admin_onboarding_poll(state)
    except Exception as exc:  # pragma: no cover - defensive logging path
        import logging

        logging.warning("Admin onboarding status check failed: %s", exc)
        _set_state_value(state, "admin_onboarding_error", f"Status check failed: {exc}")
        _set_state_value(state, "admin_onboarding_status", "failed")
        reset_admin_onboarding_polling_state(state)
    finally:
        _set_state_value(state, "admin_onboarding_poll_in_progress", False)


def _set_state_value(state: Any, key: str, value: Any) -> None:
    """Set a value on the provided session state (dict or attribute-based)."""

    try:
        state[key] = value
    except Exception:
        pass
    try:
        setattr(state, key, value)
    except Exception:
        pass


def _get_state_value(state: Any, key: str, default: Any = None) -> Any:
    """Retrieve a value from the provided session state (dict or attribute-based)."""

    try:
        return state.get(key, default)  # type: ignore[attr-defined]
    except Exception:
        pass
    return getattr(state, key, default)
