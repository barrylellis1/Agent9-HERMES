"""
Plan-variance E2E pipeline test: SA -> DA (+MA enrichment) -> SF -> HITL approve -> VA.

Proves that a real plan_variance situation (Phase 11I-A) survives the full
pipeline into a VA vs_plan verdict (Phase 11I-C) — the exact wiring built in
this session: workflows.py's HITL approve handler looks up the originating
situation's plan_value via SituationsStore and threads it into
RegisterSolutionRequest.plan_value_at_approval, which VA then uses to compute
vs_plan_verdict at evaluation.

Unlike test_sa_golden.py this is NOT a numeric golden-value regression test —
SF's output is LLM-generated prose and is not deterministic across runs.
Assertions are structural: each stage completes, and the plan_value threads
through correctly end to end.

Requirements:
  - Dev stack running (restart_decision_studio_ui.ps1)
  - Hess client seeded locally with plan_variance thresholds (scripts/clients/hess.py)
  - Real LLM calls: DA (diagnostic question), MA (market signals), SF (3 personas +
    synthesis) all hit Claude/Perplexity for real. This test is slower (~30-90s)
    and costs real API tokens — that's why it's marked @pytest.mark.regression
    and excluded from the fast unit-test loop.

Run:
  .venv/Scripts/pytest tests/regression/test_plan_variance_e2e.py -v --timeout=240
"""
from __future__ import annotations

import httpx
import pytest

from tests.regression._plan_variance_runner import (
    approve_solution,
    evaluate_va_solution,
    find_plan_variance_situation,
    get_va_solution_via_portfolio,
    run_deep_analysis,
    run_solution_finder,
    transition_solution_phase,
)
from tests.regression.conftest import BASE_URL

CLIENT_ID = "hess"
PRINCIPAL_ID = "cfo_001"


@pytest.fixture
def e2e_client(api_client):
    """
    Dedicated client with a longer per-request read timeout than the shared
    session-scoped api_client (180s). SF's multi-call architecture (3 personas
    + synthesis, all real LLM calls) can leave the single-worker event loop
    busy long enough that even a lightweight status-check GET misses a 180s
    per-request timeout. Reuses api_client's skip-if-server-down check.
    """
    with httpx.Client(base_url=BASE_URL, timeout=httpx.Timeout(300.0, connect=10.0)) as client:
        yield client


@pytest.mark.regression
def test_plan_variance_full_pipeline(e2e_client) -> None:
    """
    Drive a real plan_variance situation through SA -> DA -> MA -> SF -> HITL
    approve -> HITL Mark Implementing -> HITL Go Live -> VA evaluate, and
    verify the plan/budget baseline is captured and reflected in VA's verdict.

    The phase-transition steps are not optional plumbing to skip past — they
    are exactly what the real Portfolio.tsx "Mark Implementing" / "Go Live"
    buttons call, and Go Live is what resets actual_trend to a fresh
    measurement baseline in production.
    """
    api_client = e2e_client
    # ── Step 1: SA — find a real plan_variance situation ──────────────────
    situation = find_plan_variance_situation(api_client, CLIENT_ID, PRINCIPAL_ID)
    assert situation.get("alert_type") == "plan_variance"
    assert situation.get("plan_value") is not None, (
        "SA plan_variance situation must carry plan_value — if this is None, "
        "the 11I-A plan_variance detection block is broken."
    )
    kpi_name = situation.get("kpi_name") or situation.get("kpi_id")
    current_actual = (situation.get("kpi_value") or {}).get("value")
    assert current_actual is not None

    # ── Step 2: DA — deep analysis on the plan_variance KPI (+ MA enrichment inline) ──
    da_result = run_deep_analysis(api_client, PRINCIPAL_ID, situation, CLIENT_ID)
    assert da_result.get("execution") is not None, "DA execution result missing"
    # MA enrichment is inline within the DA route handler — its presence in the
    # result (even as an empty list, e.g. no live market signals for this
    # industry/session) proves the MA agent call path executed without error.
    assert "market_signals" in da_result, "MA enrichment step did not run — market_signals key missing"

    # ── Step 3: SF — solution options from DA's output ─────────────────────
    sf_result = run_solution_finder(api_client, PRINCIPAL_ID, situation, da_result, CLIENT_ID)
    options = sf_result["options"]
    assert len(options) > 0
    chosen_option = options[0]
    assert chosen_option.get("id")

    # ── Step 4: HITL approve — triggers VA register_solution ──────────────
    approve_entry = approve_solution(api_client, sf_result["request_id"], chosen_option["id"])
    va_solution_id = approve_entry.get("va_solution_id")
    assert va_solution_id, f"HITL approval did not register a VA solution: {approve_entry}"

    # ── Step 5: VA — confirm the plan baseline threaded through at registration ──
    solution = get_va_solution_via_portfolio(api_client, PRINCIPAL_ID, CLIENT_ID, va_solution_id)
    assert solution.get("plan_value_at_approval") is not None, (
        f"VA solution {va_solution_id} has no plan_value_at_approval — the "
        f"workflows.py situation-lookup wiring (SituationsStore.get_situation -> "
        f"full_payload['plan_value']) did not carry the budget baseline through "
        f"from the originating plan_variance situation for KPI '{kpi_name}'."
    )

    # ── Step 6: HITL "Mark Implementing" — APPROVED -> IMPLEMENTING ────────
    impl_resp = transition_solution_phase(api_client, va_solution_id, "IMPLEMENTING", PRINCIPAL_ID)
    assert impl_resp.get("phase") == "IMPLEMENTING"

    # ── Step 7: HITL "Go Live" — IMPLEMENTING -> LIVE ──────────────────────
    live_resp = transition_solution_phase(api_client, va_solution_id, "LIVE", PRINCIPAL_ID)
    assert live_resp.get("phase") == "LIVE"

    # ── Step 8: VA — evaluate and confirm a real vs_plan verdict (not no_plan_data) ──
    eval_result = evaluate_va_solution(api_client, PRINCIPAL_ID, va_solution_id, current_actual)
    vs_plan_verdict = eval_result["evaluation"].get("vs_plan_verdict")
    assert vs_plan_verdict is not None and vs_plan_verdict != "no_plan_data", (
        f"Expected a real vs_plan_verdict (ahead/on/behind) given plan_value_at_approval="
        f"{solution.get('plan_value_at_approval')}, got '{vs_plan_verdict}'."
    )
