import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

from src.decision_studio_admin_api import (
    build_onboarding_api_payload,
    get_api_base_url,
    maybe_poll_admin_onboarding_status,
    reset_admin_onboarding_polling_state,
    schedule_admin_onboarding_poll,
    submit_admin_onboarding_via_api,
)


class _DummyRequest:
    def __init__(self, payload: Dict[str, Any]):
        self._payload = payload

    def model_dump(self) -> Dict[str, Any]:
        return dict(self._payload)


class _State(dict):
    """Session-state shim supporting both dict and attribute semantics."""

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as err:  # pragma: no cover - defensive attribute path
            raise AttributeError(item) from err

    def __setattr__(self, key, value):
        self[key] = value


@pytest.mark.parametrize(
    "env,expected",
    [
        ({}, "http://localhost:8000/api/v1"),
        ({"A9_API_BASE_URL": "http://example.com/api"}, "http://example.com/api"),
        ({"A9_API_BASE_URL": "http://example.com/api/"}, "http://example.com/api"),
    ],
)
def test_get_api_base_url(env, expected):
    actual = get_api_base_url(env)
    assert actual == expected


def test_build_onboarding_api_payload_strips_request_id():
    request = _DummyRequest({"request_id": "abc", "data_product_id": "dp"})
    payload = build_onboarding_api_payload(request)
    assert "request_id" not in payload
    assert payload["data_product_id"] == "dp"


@pytest.mark.anyio
async def test_submit_admin_onboarding_via_api_records_request_id(monkeypatch):
    state = _State()
    request = _DummyRequest({"data_product_id": "dp_123"})
    responses = {
        "run": {"data": {"request_id": "req-456", "state": "pending"}},
    }

    class _Client:
        def __init__(self, *_, **__):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url: str, json: Dict[str, Any]):
            assert url.endswith("/run")
            assert json["data_product_id"] == "dp_123"

            class _Response:
                @staticmethod
                def json():
                    return responses["run"]

                @staticmethod
                def raise_for_status():
                    return None

            return _Response()

    await submit_admin_onboarding_via_api(state, request, client_factory=_Client)
    assert state.admin_onboarding_request_id == "req-456"
    assert state.admin_onboarding_status == "pending"
    assert state.admin_onboarding_result is None
    assert state.admin_onboarding_error is None
    assert state.admin_onboarding_next_poll is not None
    assert state.admin_onboarding_poll_in_progress is False


@pytest.mark.anyio
async def test_maybe_poll_admin_onboarding_status_updates_result():
    state = _State(
        admin_onboarding_request_id="req-1",
        admin_onboarding_status="pending",
        admin_onboarding_next_poll=None,
        admin_onboarding_poll_in_progress=False,
    )

    class _Client:
        def __init__(self, *_, **__):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str):
            assert url.endswith("/req-1/status")

            class _Response:
                @staticmethod
                def json():
                    return {
                        "data": {
                            "state": "completed",
                            "result": {"status": "success"},
                        }
                    }

                @staticmethod
                def raise_for_status():
                    return None

            return _Response()

    await maybe_poll_admin_onboarding_status(state, client_factory=_Client)
    assert state.admin_onboarding_status == "completed"
    assert state.admin_onboarding_result == {"status": "success"}
    assert state.admin_onboarding_error is None
    assert state.admin_onboarding_next_poll is None
    assert state.admin_onboarding_poll_in_progress is False


@pytest.mark.anyio
async def test_maybe_poll_admin_onboarding_status_handles_error(caplog):
    state = _State(
        admin_onboarding_request_id="req-1",
        admin_onboarding_status="pending",
        admin_onboarding_next_poll=None,
        admin_onboarding_poll_in_progress=False,
    )
    caplog.set_level("WARNING")

    class _Client:
        def __init__(self, *_, **__):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str):
            raise RuntimeError("boom")

    await maybe_poll_admin_onboarding_status(state, client_factory=_Client)
    assert state.admin_onboarding_status == "failed"
    assert "Status check failed" in state.admin_onboarding_error
    assert state.admin_onboarding_next_poll is None
    assert state.admin_onboarding_poll_in_progress is False
    assert "Admin onboarding status check failed" in caplog.text


@pytest.mark.anyio
async def test_schedule_and_reset_polling_state():
    state = _State()
    schedule_admin_onboarding_poll(state, delay_seconds=0.01)
    assert state.admin_onboarding_next_poll is not None
    assert state.admin_onboarding_poll_in_progress is False

    reset_admin_onboarding_polling_state(state)
    assert state.admin_onboarding_next_poll is None
    assert state.admin_onboarding_poll_in_progress is False
