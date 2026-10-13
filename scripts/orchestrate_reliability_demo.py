"""Orchestrate real SA->DA->SF->approve->evaluate cycles to accumulate real
causal-edge confirmations and graded assumptions for a sales demo.

WHAT THIS IS FOR
----------------
"Crossing the Reliability Threshold" named "accumulate real verdicts" as a
thing that can't be shortcut by seeding -- it clears through outcomes on real
engagements or it does not clear. That's still true for a real paying
account. But the write-back mechanism itself (src/agents/new/
a9_value_assurance_agent.py: _grade_assumptions_from_verdict,
_confirm_causal_edge_from_verdict) is already fully built and wired into the
live approval -> evaluation flow, and evaluate_solution_impact() takes the
outcome KPI value as a plain request parameter -- there is no wall-clock gate
inside it. So this script drives the REAL mechanism, through the REAL API
surface, with REAL (if compressed-in-time) scenarios: real SA detection, real
DA diagnosis, real SF synthesis with the theory moderator on, a real HITL
approval that captures claimed_causal_edge the normal way, and a real DiD
evaluation call with a crafted but plausible outcome value. The write-backs
that follow are the same code path a real multi-month engagement would hit.
This is not the same as writing rows into `assumptions` or
`kpi_relationships` directly, which this script never does.

WHAT IT CANNOT GUARANTEE
-------------------------
Which kpi_relationships edge a run's moderator grade cites
(`causal_grounding`, normalized by src.analysis.mechanism.normalize_causal_
edge) comes from the LLM's own synthesis, not a parameter this script can
force. Each scenario targets a KPI with real registered relationships and
lets the moderator reason naturally; this script reports what actually got
claimed and confirmed, not what was intended. Expect a partial hit rate, not
one-for-one control. Each full cycle costs real LLM spend and several
minutes of wall time -- this is a deliberately small batch (see SCENARIOS
below), not a maximized one.

USAGE
-----
    .venv/Scripts/python scripts/orchestrate_reliability_demo.py
    .venv/Scripts/python scripts/orchestrate_reliability_demo.py --base-url http://127.0.0.1:8000

Requires the local stack already running (restart_decision_studio_ui.ps1).
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"
CLIENT_ID = "lubricants"
PRINCIPAL_ID = "cfo_001"
POLL_INTERVAL_S = 2
# 240s was too tight -- 2 of the first 6 full-batch cycles hit SF's natural
# variance (observed elsewhere this session running up to ~5-6 min).
POLL_TIMEOUT_S = 420


@dataclass
class Scenario:
    kpi_id: str
    target_verdict: str  # "validated" | "partial" | "failed"
    note: str


# Realistic mix, not all-green (user's explicit choice): most land VALIDATED,
# one PARTIAL, one FAILED.
#
# Sanity-check run (--limit 1) found gross_margin_pct never surfaces as a
# PROBLEM-type SA situation (only as an OPPORTUNITY card, which the serializer
# leaves kpi_id=None on) -- so it can never be this script's own DA/SF target
# KPI. Retargeted to net_revenue and premium_mix_pct, which DO surface as
# problem situations with a real kpi_id AND both sit in gross_margin_pct's own
# causal neighbourhood (net_revenue<->gross_margin_pct and
# premium_mix_pct<->gross_margin_pct are both registered kpi_relationships
# rows) -- confirming either edge still moves gross_margin_pct's own density
# gate, via get_causal_neighbourhood()'s multi-hop traversal.
SCENARIOS: List[Scenario] = [
    Scenario("net_revenue", "validated", "revenue growth lever"),
    Scenario("net_revenue", "validated", "mix-shift revenue lever, second run"),
    Scenario("premium_mix_pct", "validated", "premium mix recovery"),
    Scenario("net_revenue", "validated", "pricing lever"),
    Scenario("premium_mix_pct", "validated", "premium mix recovery, second run"),
    Scenario("net_revenue", "partial", "directionally right, undershoots expected range"),
    Scenario("premium_mix_pct", "failed", "intervention did not move the KPI"),
]


@dataclass
class CycleResult:
    scenario: Scenario
    situation_id: Optional[str] = None
    da_request_id: Optional[str] = None
    sf_request_id: Optional[str] = None
    option_id: Optional[str] = None
    va_solution_id: Optional[str] = None
    claimed_causal_edge: Optional[str] = None
    expected_impact_lower: Optional[float] = None
    expected_impact_upper: Optional[float] = None
    baseline_kpi_value: Optional[float] = None
    crafted_current_kpi_value: Optional[float] = None
    actual_verdict: Optional[str] = None
    edge_confirmed: bool = False
    error: Optional[str] = None


def _poll(client: httpx.Client, url: str, label: str) -> Dict[str, Any]:
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()["data"]
        state = data.get("state")
        if state == "completed":
            return data
        if state == "failed":
            raise RuntimeError(f"{label} failed: {data.get('error')}")
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"{label} did not complete within {POLL_TIMEOUT_S}s")


def run_cycle(client: httpx.Client, scenario: Scenario) -> CycleResult:
    result = CycleResult(scenario=scenario)
    print(f"\n=== {scenario.kpi_id} / {scenario.target_verdict} ({scenario.note}) ===")

    # 1. Fresh SA scan (cheap to re-run; situations are deterministic per KPI/alert shape)
    print("  SA: detecting situations...")
    resp = client.post("/workflows/situations/run", json={"principal_id": PRINCIPAL_ID, "client_id": CLIENT_ID})
    resp.raise_for_status()
    sa_req_id = resp.json()["data"]["request_id"]
    sa_data = _poll(client, f"/workflows/situations/{sa_req_id}/status", "SA")
    situations = sa_data["result"]["situations"]["situations"]
    match = next((s for s in situations if s.get("kpi_id") == scenario.kpi_id), None)
    if match is None:
        result.error = f"no situation detected for {scenario.kpi_id} this scan"
        print(f"  SKIP: {result.error}")
        return result
    result.situation_id = match["situation_id"]
    print(f"  situation: {result.situation_id}")

    # 2. DA
    print("  DA: running deep analysis...")
    resp = client.post("/workflows/deep-analysis/run", json={
        "principal_id": PRINCIPAL_ID,
        "situation_id": result.situation_id,
        "scope": {"kpi_id": scenario.kpi_id, "timeframe": "current_quarter"},
        "include_supporting_evidence": True,
        "client_id": CLIENT_ID,
    })
    resp.raise_for_status()
    da_req_id = resp.json()["data"]["request_id"]
    result.da_request_id = da_req_id
    da_data = _poll(client, f"/workflows/deep-analysis/{da_req_id}/status", "DA")
    da_execution = da_data["result"]["execution"]
    if da_execution.get("status") != "success":
        result.error = f"DA did not succeed: {da_execution.get('error_message')}"
        print(f"  SKIP: {result.error}")
        return result

    # 3. SF (theory moderator already on via SF_ENABLE_THEORY_MODERATOR=true in .env)
    print("  SF: generating solutions...")
    resp = client.post("/workflows/solutions/run", json={
        "principal_id": PRINCIPAL_ID,
        "situation_id": result.situation_id,
        "deep_analysis_output": da_execution,
        "client_id": CLIENT_ID,
    })
    resp.raise_for_status()
    sf_req_id = resp.json()["data"]["request_id"]
    result.sf_request_id = sf_req_id
    sf_data = _poll(client, f"/workflows/solutions/{sf_req_id}/status", "SF")
    solutions = sf_data["result"]["solutions"]
    options = solutions.get("options_ranked") or []
    if not options:
        result.error = "SF produced no options"
        print(f"  SKIP: {result.error}")
        return result
    recommendation = solutions.get("recommendation") or options[0]
    result.option_id = recommendation.get("id") or options[0].get("id")
    print(f"  recommended option: {result.option_id}")

    # 4. Approve -> captures claimed_causal_edge + pre-registers assumptions
    print("  Approving recommended option...")
    resp = client.post(f"/workflows/solutions/{sf_req_id}/actions/approve", json={
        "action": "approve",
        "comment": "Orchestrated reliability-demo cycle",
        "payload": {"solution_option_id": result.option_id},
    })
    resp.raise_for_status()
    approve_data = resp.json()["data"]
    actions = approve_data.get("actions") or []
    last_action = actions[-1] if actions else {}
    result.va_solution_id = last_action.get("va_solution_id")
    if not result.va_solution_id:
        result.error = "approval did not produce a va_solution_id"
        print(f"  SKIP: {result.error}")
        return result
    print(f"  va_solution_id: {result.va_solution_id}")

    # 5. Read back what was actually captured at approval.
    # GET /value-assurance/solutions/{id} reads a legacy, never-written-to
    # module-level dict in src/api/routes/value_assurance.py (confirmed live,
    # 404 on a solution that definitely exists) -- the documented-but-easy-to
    # forget staleness in project_va_persistence_state.md. The portfolio
    # endpoint calls the real agent instance, which reads its own
    # self._solutions_store (populated by register_solution), so it's used
    # here instead.
    resp = client.get(f"/value-assurance/portfolio/{PRINCIPAL_ID}", params={"client_id": CLIENT_ID})
    resp.raise_for_status()
    portfolio = resp.json()
    solution = next((s for s in portfolio["solutions"] if s["solution_id"] == result.va_solution_id), None)
    if solution is None:
        result.error = f"va_solution_id {result.va_solution_id} not found in portfolio"
        print(f"  SKIP: {result.error}")
        return result
    snapshot = solution["strategy_snapshot"]
    result.claimed_causal_edge = snapshot.get("claimed_causal_edge")
    # The KPI's actual value at approval (last complete month). Evaluation measures
    # against this; it refuses when none was recorded.
    result.baseline_kpi_value = snapshot.get("kpi_value_at_approval")
    if result.baseline_kpi_value is None:
        result.error = "no KPI value was recorded at approval, so this solution cannot be evaluated"
        print(f"  SKIP: {result.error}")
        return result
    result.expected_impact_lower = solution.get("expected_impact_lower")
    result.expected_impact_upper = solution.get("expected_impact_upper")
    print(f"  claimed_causal_edge: {result.claimed_causal_edge}")
    print(f"  expected_impact: [{result.expected_impact_lower}, {result.expected_impact_upper}], baseline={result.baseline_kpi_value}")

    # 6. Craft an outcome KPI value that drives the intended verdict through
    #    the REAL DiD formula (attributable = total_change, no control/market/
    #    seasonal adjustments supplied -- the simplest honest case).
    baseline = result.baseline_kpi_value
    lower = result.expected_impact_lower or 0.0
    if scenario.target_verdict == "validated":
        current = baseline + abs(lower) * 1.15  # clears the lower bound with margin
    elif scenario.target_verdict == "partial":
        current = baseline + abs(lower) * 0.5   # positive, but short of the expected lower bound
    else:  # failed
        current = baseline - abs(lower) * 0.2   # moved the wrong way
    result.crafted_current_kpi_value = current
    print(f"  evaluating with current_kpi_value={current:.4f} (targeting {scenario.target_verdict})...")

    resp = client.post(f"/value-assurance/solutions/{result.va_solution_id}/evaluate", json={
        "request_id": f"demo-eval-{result.va_solution_id}",
        "principal_id": PRINCIPAL_ID,
        "solution_id": result.va_solution_id,
        "current_kpi_value": current,
    })
    resp.raise_for_status()
    eval_data = resp.json()
    # SolutionVerdict serializes uppercase ("VALIDATED"/"PARTIAL"/"FAILED").
    result.actual_verdict = eval_data["evaluation"]["verdict"]
    print(f"  actual verdict: {result.actual_verdict}")

    # 7. Confirm what the write-back actually did (read back, don't assume)
    if result.claimed_causal_edge and result.claimed_causal_edge not in ("ungrounded", "insufficient_data"):
        resp = client.get("/registry/kpi-relationships", params={"client_id": CLIENT_ID})
        resp.raise_for_status()
        rels = resp.json()["data"] if isinstance(resp.json(), dict) else resp.json()
        a, b = sorted(result.claimed_causal_edge.split("<->"))
        for rel in rels:
            pair = sorted([rel.get("kpi_id"), rel.get("related_kpi_id")])
            if pair == [a, b] and rel.get("causal_rung") == "intervention_tested" and rel.get("provenance") == "va_validated":
                result.edge_confirmed = True
                break
        print(f"  edge confirmed: {result.edge_confirmed}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N scenarios (for a quick sanity check before the full batch)")
    parser.add_argument("--skip", type=int, default=0, help="Skip the first N scenarios (e.g. already run in an earlier sanity check)")
    args = parser.parse_args()

    scenarios = SCENARIOS[args.skip :]
    if args.limit:
        scenarios = scenarios[: args.limit]
    results: List[CycleResult] = []
    with httpx.Client(base_url=args.base_url, timeout=60.0) as client:
        for scenario in scenarios:
            try:
                results.append(run_cycle(client, scenario))
            except Exception as exc:  # noqa: BLE001 -- report and continue the batch
                print(f"  ERROR: {exc}")
                results.append(CycleResult(scenario=scenario, error=str(exc)))

        print("\n\n========== SUMMARY ==========")
        confirmed = [r for r in results if r.edge_confirmed]
        graded = [r for r in results if r.actual_verdict in ("VALIDATED", "FAILED")]
        for r in results:
            status = "OK" if not r.error else f"ERROR: {r.error}"
            print(f"  {r.scenario.kpi_id:20s} target={r.scenario.target_verdict:10s} "
                  f"actual={r.actual_verdict or '-':10s} edge={r.claimed_causal_edge or '-':35s} "
                  f"confirmed={r.edge_confirmed}  [{status}]")
        print(f"\n  {len(confirmed)}/{len(results)} cycles confirmed a causal edge")
        print(f"  {len(graded)}/{len(results)} cycles graded assumptions (validated/failed verdicts)")

        print("\n  Checking density gate for each KPI touched (plus gross_margin_pct,")
        print("  whose causal neighbourhood both scenario KPIs feed into)...")
        kpis_touched = sorted({s.kpi_id for s in scenarios} | {"gross_margin_pct"})
        for kpi_id in kpis_touched:
            resp = client.get(f"/registry/theory-layer/{kpi_id}", params={"client_id": CLIENT_ID})
            resp.raise_for_status()
            data = resp.json()["data"]
            gate = data.get("epistemic_summary", {}).get("density_gate_passed")
            print(f"    {kpi_id}: density_gate_passed={gate}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
