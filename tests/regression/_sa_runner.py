"""
Shared helper: run a SA scan via the API and return normalised results.
Used by both the pytest tests and the update_golden.py capture script.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import httpx

BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 3   # seconds between status polls
POLL_TIMEOUT  = 120 # seconds before giving up


# ── Client definitions ──────────────────────────────────────────────────────

CLIENTS = [
    {
        "client_id":    "lubricants",
        "principal_id": "cfo_001",
        "backend":      "bigquery",
        # Gross Profit = revenue KPI that was previously affected by NaN bug
        # Cost of Goods Sold = inverse_logic cost KPI (exercises NaN path for costs)
        "anchor_kpis":  ["Gross Profit", "Cost of Goods Sold"],
        "warmup":       False,
    },
    {
        "client_id":    "apex_lubricants",
        "principal_id": "cfo_001",
        "backend":      "snowflake",
        # Base Oil & Additives Cost = inverse_logic cost KPI on Snowflake
        # B2B Direct Revenue = revenue KPI on Snowflake
        "anchor_kpis":  ["Base Oil & Additives Cost", "B2B Direct Revenue"],
        "warmup":       False,
    },
    {
        "client_id":    "hess",
        "principal_id": "cfo_001",
        "backend":      "sqlserver",
        # Total Revenue = primary revenue KPI on SQL Server
        # Gross Margin % = derived ratio KPI (exercises CASE/NULLIF SQL path)
        "anchor_kpis":  ["Total Revenue", "Gross Margin %"],
        "warmup":       False,
    },
]

# Fixed window — historical data does not change, so results are deterministic.
TIMEFRAME       = "year_to_date"
COMPARISON_TYPE = "year_over_year"


# ── Core runner ─────────────────────────────────────────────────────────────

def run_sa_scan(
    client: httpx.Client,
    client_id: str,
    principal_id: str,
    timeframe: str = TIMEFRAME,
    comparison_type: str = COMPARISON_TYPE,
) -> Dict[str, Any]:
    """
    POST /workflows/situations/run → poll until complete → return normalised dict:
    {
      "situations":    { kpi_name: {severity, card_type, current_value, comparison_value, percent_change, comparison_type} },
      "opportunities": { kpi_name: {...} },
    }
    Raises RuntimeError on timeout or scan failure.
    """
    payload = {
        "principal_id":   principal_id,
        "client_id":      client_id,
        "timeframe":      timeframe,
        "comparison_type": comparison_type,
    }

    resp = client.post("/api/v1/workflows/situations/run", json=payload)
    resp.raise_for_status()
    request_id = json.loads(resp.content)["data"]["request_id"]

    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        status_resp = client.get(f"/api/v1/workflows/situations/{request_id}/status")
        status_resp.raise_for_status()
        record = json.loads(status_resp.content).get("data", {})
        state  = record.get("state") or record.get("status")

        if state in ("completed", "success"):
            result = record.get("result") or {}
            return _normalise(result)

        if state in ("failed", "error"):
            raise RuntimeError(
                f"SA scan failed for {client_id}: {record.get('error') or record.get('message')}"
            )

    raise RuntimeError(
        f"SA scan for {client_id} did not complete within {POLL_TIMEOUT}s"
    )


def _normalise(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract situations + opportunities and flatten to the fields we compare.
    Each entry is keyed by kpi_name (stable, human-readable identifier).
    """
    out: Dict[str, Dict[str, Any]] = {}

    def _entry(s: Dict[str, Any]) -> Dict[str, Any]:
        kv = s.get("kpi_value") or {}
        return {
            "severity":        s.get("severity"),
            "card_type":       s.get("card_type"),
            "current_value":   _safe(kv.get("value")),
            "comparison_value": _safe(kv.get("comparison_value")),
            "percent_change":  _safe(kv.get("percent_change")),
            "comparison_type": kv.get("comparison_type"),
        }

    # result["situations"] may be a list OR a dict like {"status": "success", "situations": [...]}
    _sit_raw = result.get("situations") or []
    if isinstance(_sit_raw, dict):
        _sit_raw = _sit_raw.get("situations") or []

    _opp_raw = result.get("opportunities") or []
    if isinstance(_opp_raw, dict):
        _opp_raw = _opp_raw.get("opportunities") or []

    situations    = _sit_raw if isinstance(_sit_raw, list) else []
    opportunities = _opp_raw if isinstance(_opp_raw, list) else []

    sit_map: Dict[str, Any] = {}
    for s in situations:
        d = s if isinstance(s, dict) else (s.model_dump() if hasattr(s, "model_dump") else {})
        name = d.get("kpi_name") or d.get("kpi_id") or "unknown"
        sit_map[name] = _entry(d)

    opp_map: Dict[str, Any] = {}
    for o in opportunities:
        d = o if isinstance(o, dict) else (o.model_dump() if hasattr(o, "model_dump") else {})
        name = d.get("kpi_name") or d.get("kpi_id") or "unknown"
        opp_map[name] = _entry(d)

    return {"situations": sit_map, "opportunities": opp_map}


def _safe(v: Any) -> Optional[float]:
    """Return None for NaN/inf, otherwise round to 4dp for stable comparison."""
    if v is None:
        return None
    try:
        f = float(v)
        if f != f or f == float("inf") or f == float("-inf"):  # NaN or inf
            return None
        return round(f, 4)
    except (TypeError, ValueError):
        return None
