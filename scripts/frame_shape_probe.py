"""Probe the decision-quality frame link across problem shapes AND framing choices.

WHY THIS EXISTS
---------------
Frame fails 11 of 13 scored runs, but every option came from one KPI and one
Deep Analysis result. Two explanations fit that equally well: "the system never
widens the frame" vs "this problem has one right frame". Objective 2 in
"Crossing the Reliability Threshold" needs a labelled comparison to tell them
apart.

The framing gate (DA_ENABLE_FRAMING_GATE) already asks the principal to choose
an objective before synthesis: confirm_stated, an offered alternative, or
other. The principal's choice is the human label. This probe drives that gate
through the real refinement endpoint, then runs SF with the chosen framing.

IMPORTANT -- WHAT THE LABELS ARE
--------------------------------
Every choice this script makes is SCRIPTED, not a human judgement:
  - arm "confirm":     always accept the stated objective (a rubber stamp)
  - arm "alternative": always take the first causal alternative offered
Each run's output records choice_source="scripted". Scripted choices can show
whether SF honours an explicit frame; they cannot show what a real principal
would pick. Real labels only come from real principals at the UI gate.

USAGE
-----
    .venv/Scripts/python scripts/frame_shape_probe.py
Payloads are written to the scratchpad directory for offline re-scoring.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

import httpx

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))
from orchestrate_reliability_demo import CLIENT_ID, PRINCIPAL_ID, _poll  # noqa: E402

from src.analysis.decision_quality import score_run  # noqa: E402

BASE = "http://127.0.0.1:8000/api/v1"
OUT_DIR = "C:/Users/Blell/AppData/Local/Temp/claude/c--Users-Blell-Agent9-HERMES/91ac6211-f2d4-4fb9-921f-01ed30f61d8e/scratchpad/frame_probe_v2"
SHAPES = ["net_revenue", "premium_mix_pct"]
ARMS = ["confirm", "alternative"]


def _refine_body(kpi_id: str, da_exec: Dict[str, Any], turn: int, framing_decision: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "principal_id": PRINCIPAL_ID,
        "deep_analysis_output": {
            "plan": {"kpi_name": kpi_id, "client_id": CLIENT_ID},
            "execution": da_exec,
        },
        "principal_context": {"principal_id": PRINCIPAL_ID, "role": "Chief Financial Officer", "client_id": CLIENT_ID},
        "conversation_history": [],
        "user_message": None,
        "current_topic": None,
        "turn_count": turn,
        "topics_completed": [],
        "turns_on_current_topic": 0,
        "prior_constraint_items": [],
        "prior_exclusions": [],
    }
    if framing_decision is not None:
        body["framing_decision"] = framing_decision
    return body


def _scripted_decision(arm: str, prompt: Dict[str, Any]) -> Dict[str, Any]:
    stated = prompt["stated_objective_text"]
    if arm == "confirm":
        return {
            "choice": "confirm_stated",
            "chosen_objective_text": stated,
            "falsification_criterion": "SCRIPTED: the stated KPI recovers within one quarter of the recommended action.",
        }
    alts = prompt.get("alternatives") or []
    if not alts:
        raise RuntimeError("no alternatives offered; alternative arm cannot run")
    alt = alts[0]
    return {
        "choice": "alternative",
        "chosen_kpi_id": alt["kpi_id"],
        "chosen_objective_text": f"Recovering {alt.get('kpi_name') or alt['kpi_id']}",
        "falsification_criterion": "SCRIPTED: the chosen driver moves the stated KPI within one quarter.",
    }


def one_run(client: httpx.Client, kpi_id: str, arm: str) -> Dict[str, Any]:
    sa = client.post("/workflows/situations/run", json={"principal_id": PRINCIPAL_ID, "client_id": CLIENT_ID})
    sa.raise_for_status()
    sits = _poll(client, f"/workflows/situations/{sa.json()['data']['request_id']}/status", "SA")["result"]["situations"]["situations"]
    match = next((s for s in sits if s.get("kpi_id") == kpi_id), None)
    if match is None:
        return {"kpi_id": kpi_id, "arm": arm, "error": "no situation"}

    da = client.post("/workflows/deep-analysis/run", json={
        "principal_id": PRINCIPAL_ID, "situation_id": match["situation_id"],
        "scope": {"kpi_id": kpi_id, "timeframe": "current_quarter"},
        "include_supporting_evidence": True, "client_id": CLIENT_ID,
    })
    da.raise_for_status()
    da_result = _poll(client, f"/workflows/deep-analysis/{da.json()['data']['request_id']}/status", "DA")["result"]
    da_exec = da_result["execution"]
    if da_exec.get("status") != "success":
        return {"kpi_id": kpi_id, "arm": arm, "error": "DA failed"}

    gate = client.post("/workflows/deep-analysis/refine", json=_refine_body(kpi_id, da_exec, 0, None), timeout=240.0)
    gate.raise_for_status()
    prompt = gate.json()["data"].get("framing_prompt")
    if not prompt:
        return {"kpi_id": kpi_id, "arm": arm, "error": "framing gate produced no prompt"}

    decision = _scripted_decision(arm, prompt)
    submit = client.post("/workflows/deep-analysis/refine", json=_refine_body(kpi_id, da_exec, 1, decision), timeout=240.0)
    submit.raise_for_status()
    refined = submit.json()["data"]

    sf = client.post("/workflows/solutions/run", json={
        "principal_id": PRINCIPAL_ID,
        "situation_id": match["situation_id"],
        "deep_analysis_output": da_exec,
        "refinement_result": {
            "framing_decision": refined.get("framing_decision") or decision,
            "framing_record": refined.get("framing_record"),
            "refined_problem_statement": refined.get("refined_problem_statement"),
        },
        "client_id": CLIENT_ID,
    })
    sf.raise_for_status()
    solutions = _poll(client, f"/workflows/solutions/{sf.json()['data']['request_id']}/status", "SF")["result"]["solutions"]

    os.makedirs(OUT_DIR, exist_ok=True)
    tag = f"{kpi_id}_{arm}"
    with open(f"{OUT_DIR}/{tag}.json", "w", encoding="utf-8") as f:
        json.dump({"kpi_id": kpi_id, "arm": arm, "choice_source": "scripted",
                   "decision": decision, "solutions": solutions, "da_execution": da_exec}, f)

    frame = score_run(solutions, da_result=da_exec, run_id=tag).l1_frame
    return {
        "kpi_id": kpi_id, "arm": arm, "choice_source": "scripted",
        "chosen_objective": decision["chosen_objective_text"],
        "frame_passed": frame.passed, "frame_evidence": frame.evidence,
        "option_titles": [o.get("title") for o in (solutions.get("options_ranked") or [])],
    }


def main() -> int:
    results: List[Dict[str, Any]] = []
    with httpx.Client(base_url=BASE, timeout=60.0) as client:
        for kpi_id in SHAPES:
            for arm in ARMS:
                print(f"--- {kpi_id} / {arm} (scripted) ---", flush=True)
                try:
                    r = one_run(client, kpi_id, arm)
                except Exception as exc:  # noqa: BLE001
                    r = {"kpi_id": kpi_id, "arm": arm, "error": str(exc)}
                results.append(r)
                print(json.dumps(r, indent=2), flush=True)

    print("\n========== FRAME BY SHAPE x ARM (all scripted) ==========", flush=True)
    for kpi_id in SHAPES:
        for arm in ARMS:
            row = [r for r in results if r["kpi_id"] == kpi_id and r["arm"] == arm and "frame_passed" in r]
            passes = sum(1 for r in row if r["frame_passed"])
            print(f"  {kpi_id} / {arm}: frame passed {passes}/{len(row)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
