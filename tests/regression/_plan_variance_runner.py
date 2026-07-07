"""
Shared helpers: drive the SA -> DA (+MA enrichment) -> SF -> HITL approve -> VA
pipeline via the live API, for the plan_variance E2E test.

Mirrors the polling/normalisation conventions in _sa_runner.py but drives the
full downstream chain rather than just the SA scan.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import httpx

POLL_INTERVAL = 3    # seconds between status polls
POLL_TIMEOUT = 180   # seconds — SF's multi-call architecture (3 personas + synthesis) is the slow step


def _poll(client: httpx.Client, status_url: str, label: str) -> Dict[str, Any]:
    """Poll a workflow status endpoint until completed/failed. Returns the record dict."""
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        resp = client.get(status_url)
        resp.raise_for_status()
        record = json.loads(resp.content).get("data", {})
        state = record.get("state") or record.get("status")
        if state in ("completed", "success"):
            return record
        if state in ("failed", "error"):
            raise RuntimeError(f"{label} failed: {record.get('error') or record.get('message')}")
    raise RuntimeError(f"{label} did not complete within {POLL_TIMEOUT}s")


def find_plan_variance_situation(
    client: httpx.Client,
    client_id: str,
    principal_id: str,
    timeframe: str = "year_to_date",
    comparison_type: str = "year_over_year",
) -> Dict[str, Any]:
    """
    Run a live SA scan and return the first situation with alert_type == 'plan_variance'.

    Raises RuntimeError if no plan_variance situation is detected — that's a real
    regression signal (11I-A plan variance detection or the client's budget seed
    data is broken), not something this test should silently skip past.
    """
    payload = {
        "principal_id": principal_id,
        "client_id": client_id,
        "timeframe": timeframe,
        "comparison_type": comparison_type,
    }
    resp = client.post("/api/v1/workflows/situations/run", json=payload)
    resp.raise_for_status()
    request_id = json.loads(resp.content)["data"]["request_id"]

    record = _poll(client, f"/api/v1/workflows/situations/{request_id}/status", "SA scan")
    result = record.get("result") or {}
    sit_raw = result.get("situations") or []
    if isinstance(sit_raw, dict):
        sit_raw = sit_raw.get("situations") or []

    plan_variance_sits = [s for s in sit_raw if isinstance(s, dict) and s.get("alert_type") == "plan_variance"]
    if not plan_variance_sits:
        all_types = sorted({s.get("alert_type") for s in sit_raw if isinstance(s, dict)})
        raise RuntimeError(
            f"No plan_variance situation detected for {client_id}/{principal_id}. "
            f"alert_types present: {all_types}"
        )
    # Prefer the largest-magnitude variance — most deterministic, least likely to
    # flip severity band across runs due to minor data drift.
    plan_variance_sits.sort(key=lambda s: abs((s.get("kpi_value") or {}).get("percent_change") or 0), reverse=True)
    return plan_variance_sits[0]


def run_deep_analysis(
    client: httpx.Client,
    principal_id: str,
    situation: Dict[str, Any],
    client_id: str,
    timeframe: str = "year_to_date",
) -> Dict[str, Any]:
    """POST /deep-analysis/run for the given situation's KPI, poll to completion, return result dict."""
    kpi_id = situation.get("kpi_id") or situation.get("kpi_name")
    payload = {
        "principal_id": principal_id,
        "situation_id": situation.get("situation_id"),
        "scope": {"kpi_id": kpi_id, "timeframe": timeframe},
        "client_id": client_id,
    }
    resp = client.post("/api/v1/workflows/deep-analysis/run", json=payload)
    resp.raise_for_status()
    request_id = json.loads(resp.content)["data"]["request_id"]

    record = _poll(client, f"/api/v1/workflows/deep-analysis/{request_id}/status", "Deep Analysis")
    return record.get("result") or {}


def run_solution_finder(
    client: httpx.Client,
    principal_id: str,
    situation: Dict[str, Any],
    deep_analysis_result: Dict[str, Any],
    client_id: str,
) -> Dict[str, Any]:
    """POST /solutions/run using DA's execution output, poll to completion, return the request_id + options."""
    payload = {
        "principal_id": principal_id,
        "situation_id": situation.get("situation_id"),
        "deep_analysis_output": deep_analysis_result.get("execution"),
        "client_id": client_id,
    }
    resp = client.post("/api/v1/workflows/solutions/run", json=payload)
    resp.raise_for_status()
    request_id = json.loads(resp.content)["data"]["request_id"]

    record = _poll(client, f"/api/v1/workflows/solutions/{request_id}/status", "Solution Finder")
    result = record.get("result") or {}
    solutions = result.get("solutions") or {}
    options = solutions.get("options_ranked") or []
    if not options:
        raise RuntimeError(f"Solution Finder returned no options_ranked for request {request_id}")
    return {"request_id": request_id, "options": options, "market_intelligence": solutions.get("market_intelligence")}


def approve_solution(
    client: httpx.Client,
    request_id: str,
    solution_option_id: str,
) -> Dict[str, Any]:
    """POST the HITL approve action; returns the va_solution_id from the action entry."""
    resp = client.post(
        f"/api/v1/workflows/solutions/{request_id}/actions/approve",
        json={"action": "approve", "payload": {"solution_option_id": solution_option_id}},
    )
    resp.raise_for_status()
    data = json.loads(resp.content)["data"]
    actions = data.get("actions") or []
    approve_entries = [a for a in actions if a.get("action") == "approve"]
    if not approve_entries:
        raise RuntimeError(f"No 'approve' action entry returned for {request_id}: {data}")
    return approve_entries[-1]


def transition_solution_phase(
    client: httpx.Client,
    solution_id: str,
    new_phase: str,
    principal_id: str,
) -> Dict[str, Any]:
    """
    PATCH the VA lifecycle phase — this is exactly what the real UI's
    "Mark Implementing" / "Go Live" buttons on Portfolio.tsx call
    (handlePhaseTransition -> PATCH /solutions/{id}/phase). A true E2E must
    simulate these clicks, not skip straight from approve to evaluate: the
    LIVE transition resets actual_trend to a fresh baseline and is what makes
    TrajectoryChart show the Expected/Actual lines in production.
    """
    resp = client.patch(
        f"/api/v1/value-assurance/solutions/{solution_id}/phase",
        params={"principal_id": principal_id},
        json={"new_phase": new_phase},
    )
    resp.raise_for_status()
    return json.loads(resp.content)


def get_va_solution_via_portfolio(
    client: httpx.Client, principal_id: str, client_id: str, solution_id: str
) -> Dict[str, Any]:
    """
    Fetch a registered solution by scanning the portfolio summary.

    NOTE: the legacy GET /value-assurance/solutions/{id} route reads from a
    module-level dict in value_assurance.py that is never populated by the real
    register_solution flow (which writes to the VA agent singleton's own
    in-memory store via AgentRegistry). That route 404s for anything registered
    through the actual HITL approval path. GET /portfolio/{principal_id} calls
    _get_va_agent() -> AgentRegistry.get_agent(...) -> the real singleton, so it
    sees solutions registered via workflows.py. Use this helper, not the
    single-solution GET, until that legacy route is rewired or removed.
    """
    resp = client.get(
        f"/api/v1/value-assurance/portfolio/{principal_id}",
        params={"client_id": client_id, "include_superseded": True},
    )
    resp.raise_for_status()
    portfolio = json.loads(resp.content)
    for sol in portfolio.get("solutions") or []:
        if sol.get("solution_id") == solution_id:
            return sol
    raise RuntimeError(f"Solution {solution_id} not found in portfolio for {principal_id}/{client_id}")


def evaluate_va_solution(
    client: httpx.Client,
    principal_id: str,
    solution_id: str,
    current_kpi_value: float,
) -> Dict[str, Any]:
    payload = {
        "request_id": f"eval-{solution_id[:12]}",
        "principal_id": principal_id,
        "solution_id": solution_id,
        "current_kpi_value": current_kpi_value,
    }
    resp = client.post(
        f"/api/v1/value-assurance/solutions/{solution_id}/evaluate",
        json=payload,
    )
    resp.raise_for_status()
    return json.loads(resp.content)
