"""
SA golden-file regression tests.

Verifies that the numeric outputs of the SA pipeline (current_value,
comparison_value, percent_change, severity) stay stable across code changes,
for each production data backend: BigQuery (lubricants), Snowflake (apex_lubricants),
SQL Server (hess).

Requirements:
  - Dev stack running  (restart_decision_studio_ui.ps1)
  - Golden files exist (tests/regression/golden/<client_id>.json)
    → generate with: python tests/regression/update_golden.py

Run:
  .venv/Scripts/pytest tests/regression/test_sa_golden.py -v --timeout=180
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import time

import pytest

from tests.regression._sa_runner import CLIENTS, run_sa_scan

GOLDEN_DIR = Path(__file__).parent / "golden"

# Tolerance for floating-point comparisons (±0.1 %)
TOLERANCE_PCT = 0.1


# ── Helpers ─────────────────────────────────────────────────────────────────

def _load_golden(client_id: str) -> Dict[str, Any]:
    path = GOLDEN_DIR / f"{client_id}.json"
    if not path.exists():
        pytest.skip(
            f"No golden file for '{client_id}'. "
            f"Run: python tests/regression/update_golden.py --client {client_id}"
        )
    return json.loads(path.read_text())


def _within_tolerance(actual: Optional[float], expected: Optional[float], label: str) -> None:
    """Assert that actual ≈ expected within TOLERANCE_PCT (relative)."""
    if expected is None and actual is None:
        return
    if expected is None:
        pytest.fail(f"{label}: golden is None but got {actual}")
    if actual is None:
        pytest.fail(f"{label}: expected {expected} but got None (possible NaN/null regression)")

    if expected == 0.0:
        # For zero-expected values use absolute tolerance
        assert abs(actual - expected) < 0.01, (
            f"{label}: expected ≈ 0 but got {actual}"
        )
        return

    rel_diff_pct = abs((actual - expected) / expected) * 100
    assert rel_diff_pct <= TOLERANCE_PCT, (
        f"{label}: {actual} differs from golden {expected} by {rel_diff_pct:.4f}% "
        f"(tolerance {TOLERANCE_PCT}%)"
    )


def _compare_situation(kpi_name: str, actual: Dict[str, Any], expected: Dict[str, Any]) -> None:
    """Compare one situation dict against its golden counterpart."""
    assert actual["severity"] == expected["severity"], (
        f"{kpi_name}: severity changed from {expected['severity']} → {actual['severity']}"
    )
    assert actual["card_type"] == expected["card_type"], (
        f"{kpi_name}: card_type changed from {expected['card_type']} → {actual['card_type']}"
    )
    _within_tolerance(actual["percent_change"],  expected["percent_change"],  f"{kpi_name}.percent_change")
    _within_tolerance(actual["current_value"],   expected["current_value"],   f"{kpi_name}.current_value")
    _within_tolerance(actual["comparison_value"], expected["comparison_value"], f"{kpi_name}.comparison_value")


# ── Parametrised test ────────────────────────────────────────────────────────

@pytest.mark.parametrize("cfg", CLIENTS, ids=[c["client_id"] for c in CLIENTS])
@pytest.mark.regression
def test_sa_golden(cfg: Dict[str, Any], api_client) -> None:
    """
    For each client:
    1. Run a live SA scan against the dev data source.
    2. Assert the resulting situations match the golden baseline.
    3. Assert anchor KPIs are present in results (situations or opportunities).
    """
    client_id = cfg["client_id"]
    golden    = _load_golden(client_id)

    # ── Warmup scan (Snowflake only) ───────────────────────────────────────
    # Snowflake warehouses auto-suspend after ~60s of inactivity. The first
    # query after suspension triggers a resume that takes 30–60s, during which
    # the SA agent's KPI queries fail silently and return 0 situations.
    # Running a throwaway scan wakes the warehouse; we then wait for it to be
    # fully live before the real assertion scan.
    if cfg.get("warmup"):
        run_sa_scan(api_client, cfg["client_id"], cfg["principal_id"])
        wait = cfg.get("warmup_wait", 40)
        time.sleep(wait)

    # ── Run live scan ──────────────────────────────────────────────────────
    live = run_sa_scan(api_client, cfg["client_id"], cfg["principal_id"])

    live_sit = live["situations"]
    live_opp = live["opportunities"]
    gold_sit = golden["situations"]
    gold_opp = golden["opportunities"]

    # ── 1. Same set of detected situations ────────────────────────────────
    live_sit_names = set(live_sit.keys())
    gold_sit_names = set(gold_sit.keys())

    missing  = gold_sit_names - live_sit_names
    new_ones = live_sit_names - gold_sit_names

    assert not missing, (
        f"[{client_id}] Situations no longer detected (regression): {sorted(missing)}\n"
        f"If this is expected, re-run update_golden.py --client {client_id}"
    )
    assert not new_ones, (
        f"[{client_id}] New situations appeared (unexpected): {sorted(new_ones)}\n"
        f"If this is expected, re-run update_golden.py --client {client_id}"
    )

    # ── 2. Per-situation numeric and label checks ─────────────────────────
    for kpi_name in gold_sit_names:
        _compare_situation(kpi_name, live_sit[kpi_name], gold_sit[kpi_name])

    # ── 3. Same set of opportunities ──────────────────────────────────────
    live_opp_names = set(live_opp.keys())
    gold_opp_names = set(gold_opp.keys())

    missing_opp  = gold_opp_names - live_opp_names
    new_opp      = live_opp_names - gold_opp_names

    assert not missing_opp, (
        f"[{client_id}] Opportunities no longer detected: {sorted(missing_opp)}"
    )
    assert not new_opp, (
        f"[{client_id}] New opportunities appeared: {sorted(new_opp)}"
    )

    for kpi_name in gold_opp_names:
        _compare_situation(kpi_name, live_opp[kpi_name], gold_opp[kpi_name])

    # ── 4. Anchor KPIs must appear (situation or opportunity) ─────────────
    all_live_names = live_sit_names | live_opp_names
    for anchor in cfg["anchor_kpis"]:
        assert anchor in all_live_names, (
            f"[{client_id}] Anchor KPI '{anchor}' missing from both situations and "
            f"opportunities — possible NaN/null regression in value computation.\n"
            f"Detected: {sorted(all_live_names)}"
        )
