"""
Regression test fixtures.

Tests in this directory require the full stack to be running:
  powershell.exe -ExecutionPolicy Bypass -File restart_decision_studio_ui.ps1

Run with:
  .venv/Scripts/pytest tests/regression/ --timeout=180 -v
"""
import pytest
import httpx

BASE_URL = "http://localhost:8000"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "regression: SA/DA golden-file regression tests — require running dev stack",
    )


@pytest.fixture(scope="session")
def api_client():
    """httpx client pointed at the local dev stack. Skips entire session if server is down."""
    try:
        httpx.get(f"{BASE_URL}/docs", timeout=5)
    except Exception:
        pytest.skip(
            "Dev stack not running — start with: "
            "powershell.exe -ExecutionPolicy Bypass -File restart_decision_studio_ui.ps1"
        )
    with httpx.Client(base_url=BASE_URL, timeout=180) as client:
        yield client
