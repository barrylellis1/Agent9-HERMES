"""PM-2 A/B: simulated cross-review (baseline) vs theory-guided moderator.

Design controls (per feedback_one_observation_is_not_a_baseline + PM-4):
- ONE DA result and ONE set of Stage 1 hypotheses (temperature-0) captured
  once, reused for every run — the synthesis arm is the only variable.
- Direct API driving, mimicking client.ts's exact request shape, so UI
  flake cannot confound the comparison.
- The arm is a SERVER-side env flag read at agent creation, so runs are
  batched per arm with a backend restart between batches. Each run's
  protocol is confirmed from the payload (moderator_grades vs cross_review),
  not assumed from the env file.

Usage:
  python ab_debate.py capture            # DA + stage1, saved to ab_input.json
  python ab_debate.py run <arm> <n>      # n synthesis runs, arm = moderator|baseline
  python ab_debate.py report             # comparison table from ab_results.jsonl
"""
import json, os, sys, time, uuid
from pathlib import Path

import urllib.request

BASE = "http://localhost:8000/api/v1"
HERE = Path(__file__).parent
INPUT = HERE / "ab_input.json"
RESULTS = HERE / "ab_results.jsonl"
RAW_DIR = HERE / "ab_raw"
RAW_DIR.mkdir(exist_ok=True)
REPO_DIR = r"c:/Users/Blell/Agent9-HERMES"

PRINCIPAL = "cfo_001"
CLIENT = "lubricants"
KPI = "Gross Margin %"
PRINCIPAL_CONTEXT = {"principal_id": PRINCIPAL, "role": "Chief Financial Officer",
                     "name": "CFO", "client_id": CLIENT}


def _post(path, body):
    req = urllib.request.Request(
        f"{BASE}{path}", data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def _get(path):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as r:
        return json.loads(r.read())


def _poll(path, timeout_s=900):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        d = _get(path)["data"]
        if d["state"] == "completed":
            return d["result"], time.time() - t0
        if d["state"] == "failed":
            raise RuntimeError(f"workflow failed: {d.get('error')}")
        time.sleep(5)
    raise TimeoutError(f"{path} not done in {timeout_s}s")


def capture():
    sid = f"ab_{uuid.uuid4().hex[:8]}"
    print(f"[capture] DA run for {KPI} (situation {sid})...")
    r = _post("/workflows/deep-analysis/run", {
        "principal_id": PRINCIPAL, "situation_id": sid,
        "scope": {"kpi_id": KPI, "timeframe": "year_to_date"},
        "include_supporting_evidence": True, "client_id": CLIENT,
    })
    rid = r["data"]["request_id"]
    da_result, secs = _poll(f"/workflows/deep-analysis/{rid}/status")
    print(f"[capture] DA done in {secs:.0f}s")

    prefs = {"consulting_personas": ["mckinsey", "bcg", "bain"],
             "council_preset": "recommended", "analysis_mode": "problem",
             "debate_stage": "stage1_only"}
    print("[capture] stage1_only (temperature-0 hypotheses)...")
    r = _post("/workflows/solutions/run", {
        "principal_id": PRINCIPAL, "deep_analysis_output": da_result,
        "preferences": prefs, "principal_context": PRINCIPAL_CONTEXT,
        "situation_id": sid, "client_id": CLIENT,
    })
    rid = r["data"]["request_id"]
    s1, secs = _poll(f"/workflows/solutions/{rid}/status")
    hyps = (s1.get("solutions") or {}).get("stage_1_hypotheses")
    if not hyps:
        raise RuntimeError("no stage_1_hypotheses captured")
    print(f"[capture] stage1 done in {secs:.0f}s — personas: {list(hyps)}")
    INPUT.write_text(json.dumps({"situation_id": sid, "da_result": da_result,
                                 "hypotheses": hyps}, indent=2), encoding="utf-8")
    print(f"[capture] fixed input written: {INPUT}")


def _metrics(result, arm, run_no, secs):
    sol = result.get("solutions") or {}
    opts = sol.get("options_ranked") or []
    audit = sol.get("audit_log") or result.get("audit_log") or []
    events = {e.get("event") for e in audit if isinstance(e, dict)}
    grades = sol.get("moderator_grades") or {}
    tu = next((e for e in audit if isinstance(e, dict) and e.get("event") == "token_usage"), {})
    rows = tu.get("by_call", [])
    synth_row = next((r for r in rows if r.get("call") in ("moderator", "synthesis")), {})
    scopes = [(o.get("impact_estimate") or {}).get("scope") for o in opts]
    ranges = [((o.get("impact_estimate") or {}).get("recovery_range") or {}) for o in opts]
    return {
        "arm": arm, "run": run_no, "secs": round(secs, 1),
        "n_options": len(opts),
        "titles": [str(o.get("title"))[:45] for o in opts],
        "recommendation": (sol.get("recommendation") or {}).get("title", "")[:45],
        "stub_fallback": "heuristic_stub_fallback" in events,
        "scope_stated": sum(1 for s in scopes if s),
        "scopes": scopes,
        "range_highs": [r.get("high") for r in ranges],
        "has_cross_review": bool(sol.get("cross_review")),
        "has_grades": bool(grades),
        "arithmetic_flags": sum(1 for g in grades.values()
                                if isinstance(g, dict) and g.get("arithmetic_consistency") == "flag"),
        "constraint_fails": sum(1 for g in grades.values()
                                if isinstance(g, dict) and g.get("constraint_survival") == "fail"),
        "standing_findings": sum(1 for g in grades.values() if isinstance(g, dict)
                                 for f in (g.get("critic_findings_response") or [])
                                 if isinstance(f, dict) and f.get("disposition") == "standing"),
        "in_tokens": synth_row.get("input_tokens"),
        "out_tokens": synth_row.get("output_tokens"),
        "budget_pct": (round(100 * synth_row["output_tokens"] / synth_row["max_tokens"], 1)
                       if synth_row.get("max_tokens") and synth_row.get("output_tokens") is not None
                       else None),
    }


def _next_run_index(arm):
    """Continue numbering after existing payloads instead of overwriting them.

    run(arm, n) previously numbered 1..n every invocation, so a second batch
    silently clobbered ab_raw/{arm}_1.json and _2.json from the first. Metrics
    survived in ab_results.jsonl, but the raw payloads - the only place the full
    option text and audit log live - were lost. In an experiment whose whole
    point is comparability, destroying earlier evidence is the one thing the
    harness must not do.
    """
    existing = [int(f.stem.rsplit("_", 1)[1]) for f in RAW_DIR.glob(arm + "_*.json")
                if f.stem.rsplit("_", 1)[1].isdigit()]
    return max(existing, default=0) + 1


def _build_id():
    """Git HEAD, so every run is attributable to the build that produced it.

    Runs from before and after a code change are not interchangeable evidence;
    without this a batch looks homogeneous when it is not.
    """
    import subprocess
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, cwd=REPO_DIR,
                              timeout=10).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def run(arm, n):
    fixed = json.loads(INPUT.read_text(encoding="utf-8"))
    start = _next_run_index(arm)
    build = _build_id()
    print("[" + arm + "] build=" + build + "  numbering runs "
          + str(start) + ".." + str(start + n - 1) + " (existing payloads preserved)", flush=True)
    prefs = {"consulting_personas": ["mckinsey", "bcg", "bain"],
             "council_preset": "recommended", "analysis_mode": "problem",
             "debate_stage": "synthesis",
             "prior_stage1_hypotheses": fixed["hypotheses"]}
    for offset in range(n):
        i = start + offset
        print(f"[{arm} {offset + 1}/{n} -> #{i}] dispatching synthesis...", flush=True)
        t0 = time.time()
        r = _post("/workflows/solutions/run", {
            "principal_id": PRINCIPAL, "deep_analysis_output": fixed["da_result"],
            "preferences": prefs, "principal_context": PRINCIPAL_CONTEXT,
            "situation_id": fixed["situation_id"], "client_id": CLIENT,
        })
        rid = r["data"]["request_id"]
        result, secs = _poll(f"/workflows/solutions/{rid}/status")
        (RAW_DIR / f"{arm}_{i}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        m = _metrics(result, arm, i, secs)
        m["build"] = build
        # Guard: the payload must agree with the arm we THINK the server runs.
        # A STUB has no grades either, so checking has_grades alone reported a
        # false "ARM MISMATCH" on every stub and hid the real cause.
        expected_grades = arm == "moderator"
        if m["stub_fallback"]:
            print("  !! STUB - excluded from arm comparison; see audit_log "
                  "heuristic_stub_fallback / llm_debate_completed for cause", flush=True)
        elif m["has_grades"] != expected_grades:
            m["ARM_MISMATCH"] = True
            print(f"  !! ARM MISMATCH: has_grades={m['has_grades']} for arm={arm} "
                  f"— server flag does not match this batch", flush=True)
        with RESULTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(m) + "\n")
        print(f"  done {secs:.0f}s  scope={m['scope_stated']}/{m['n_options']}  "
              f"stub={m['stub_fallback']}  out_tok={m['out_tokens']}  "
              f"budget={m['budget_pct']}%  rec='{m['recommendation']}'", flush=True)


def report():
    rows = [json.loads(l) for l in RESULTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    for arm in ("baseline", "moderator"):
        sub = [r for r in rows if r["arm"] == arm]
        if not sub:
            print(f"\n== {arm}: no runs =="); continue
        print(f"\n== {arm} ({len(sub)} runs) ==")
        for r in sub:
            flags = f" arith_flags={r['arithmetic_flags']} standing={r['standing_findings']}" if r["has_grades"] else ""
            mismatch = " ARM_MISMATCH!" if r.get("ARM_MISMATCH") else ""
            print(f"  #{r['run']} {r['secs']:>6.0f}s  scope {r['scope_stated']}/{r['n_options']}  "
                  f"stub={str(r['stub_fallback'])[0]}  out={r['out_tokens']}  "
                  f"budget={r['budget_pct']}%  rec='{r['recommendation']}'{flags}{mismatch}")
        def avg(k):
            vals = [r[k] for r in sub if isinstance(r.get(k), (int, float))]
            return sum(vals) / len(vals) if vals else None
        recs = {r["recommendation"] for r in sub}
        print(f"  avg: {avg('secs'):.0f}s, out={avg('out_tokens'):.0f} tok, "
              f"scope={avg('scope_stated'):.1f}/3, stubs={sum(r['stub_fallback'] for r in sub)}, "
              f"distinct recommendations={len(recs)}")





# ---------------------------------------------------------------------------
# Diverse-council extension: DA's Problem Refinement recommends the council
# (one partner per category via keyword+role matching), SF debates with it.
# Never exercised before 2026-08-04.
# ---------------------------------------------------------------------------

DIVERSE_INPUT = HERE / "diverse_input.json"

# Realistic CFO refinement answers for the lubricants gross-margin case, each
# grounded in facts already established in the data / theory layer. They also
# deliberately spread across the recommender's categories (cost/contracts,
# technology/data, risk/controls) so the diversity mechanism has real text to
# match on — the point is to exercise the path, not to trick it.
REFINEMENT_ANSWERS = [
    "The biggest driver is base oil cost inflation flowing through supplier "
    "contracts. Chain A's contract has a mid-quarter price-lock clause, so any "
    "repricing has to wait for the renewal window.",
    "Exclude headcount reductions — we committed to no layoffs this year. Also "
    "exclude exiting the Chain A relationship entirely; they are a strategic anchor.",
    "Our ERP margin reporting lags by about a month and the rebate accruals are "
    "manual spreadsheets, so we partly fly blind on realized margin. Better "
    "automation and data quality would help us see this sooner.",
    "Contract compliance matters: any indexing clause has to survive audit and "
    "procurement governance review on both sides.",
]


def capture_diverse():
    fixed = json.loads(INPUT.read_text(encoding="utf-8"))
    da_result = fixed["da_result"]
    pctx = dict(PRINCIPAL_CONTEXT)
    history: list = []
    turn = 0
    topic = None
    result = None
    print("[diverse] driving refinement chat...")
    # The interviewer never volunteers to stop: it finalizes only when
    # turn_count reaches MAX_TOTAL_TURNS (10) or every topic is completed.
    # After the scripted answers run out, "skip" advances topics (the
    # documented skip command) so completion arrives by topic exhaustion
    # rather than by silently running out the clock.
    for i in range(13):
        body = {
            "principal_id": PRINCIPAL, "deep_analysis_output": da_result,
            "principal_context": pctx, "conversation_history": history,
            "user_message": REFINEMENT_ANSWERS[turn - 1] if 0 < turn <= len(REFINEMENT_ANSWERS)
                            else ("skip" if turn > 0 else None),
            "current_topic": topic, "turn_count": turn,
        }
        r = _post("/workflows/deep-analysis/refine", body)
        result = r["data"]
        agent_msg = str(result.get("agent_message", ""))[:110]
        print(f"  turn {turn}: topic={result.get('current_topic')} ready={result.get('ready_for_solutions')} | {agent_msg}")
        history = result.get("conversation_history") or history
        topic = result.get("current_topic")
        turn = result.get("turn_count", turn + 1)
        if result.get("ready_for_solutions"):
            break
    council = result.get("recommended_council_members") or []
    print(f"[diverse] recommended council: {[(m.get('id') or m.get('persona_id')) for m in council]}")
    print(f"[diverse] council type: {result.get('recommended_council_type')} | rationale: {str(result.get('council_routing_rationale'))[:160]}")
    ids = []
    for m in council:
        pid = m.get("id") or m.get("persona_id")
        if pid and pid not in ids:
            ids.append(pid)
    if len(ids) < 3:
        raise RuntimeError(f"diverse council too small to debate: {ids}")

    prefs = {"consulting_personas": ids, "analysis_mode": "problem",
             "debate_stage": "stage1_only", "refinement_result": result}
    print(f"[diverse] stage1_only with {len(ids)} personas: {ids}")
    r = _post("/workflows/solutions/run", {
        "principal_id": PRINCIPAL, "deep_analysis_output": da_result,
        "preferences": prefs, "principal_context": pctx,
        "situation_id": fixed["situation_id"], "client_id": CLIENT,
    })
    rid = r["data"]["request_id"]
    s1, secs = _poll(f"/workflows/solutions/{rid}/status")
    hyps = (s1.get("solutions") or {}).get("stage_1_hypotheses")
    if not hyps:
        raise RuntimeError("no stage_1_hypotheses from diverse council")
    print(f"[diverse] stage1 done in {secs:.0f}s — hypotheses from: {list(hyps)}")
    DIVERSE_INPUT.write_text(json.dumps({
        "situation_id": fixed["situation_id"], "da_result": da_result,
        "council_ids": ids, "refinement_result": result, "hypotheses": hyps,
    }, indent=2), encoding="utf-8")
    print(f"[diverse] input written: {DIVERSE_INPUT}")


def run_diverse(n):
    fixed = json.loads(DIVERSE_INPUT.read_text(encoding="utf-8"))
    prefs = {"consulting_personas": fixed["council_ids"], "analysis_mode": "problem",
             "debate_stage": "synthesis",
             "prior_stage1_hypotheses": fixed["hypotheses"],
             "refinement_result": fixed["refinement_result"]}
    for i in range(1, n + 1):
        print(f"[diverse {i}/{n}] synthesis with council {fixed['council_ids']}...", flush=True)
        r = _post("/workflows/solutions/run", {
            "principal_id": PRINCIPAL, "deep_analysis_output": fixed["da_result"],
            "preferences": prefs, "principal_context": PRINCIPAL_CONTEXT,
            "situation_id": fixed["situation_id"], "client_id": CLIENT,
        })
        rid = r["data"]["request_id"]
        result, secs = _poll(f"/workflows/solutions/{rid}/status")
        (RAW_DIR / f"diverse_{i}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        m = _metrics(result, "diverse", i, secs)
        with RESULTS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(m) + "\n")
        print(f"  done {secs:.0f}s  scope={m['scope_stated']}/{m['n_options']}  "
              f"stub={m['stub_fallback']}  out_tok={m['out_tokens']}  budget={m['budget_pct']}%  "
              f"rec='{m['recommendation']}'", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "capture":
        capture()
    elif cmd == "run":
        run(sys.argv[2], int(sys.argv[3]))
    elif cmd == "capture_diverse":
        capture_diverse()
    elif cmd == "run_diverse":
        run_diverse(int(sys.argv[2]))
    elif cmd == "report":
        report()
