"""Does widening the EVIDENCE SCOPE move Solution Finder from symptom to cause?

THE HYPOTHESIS
--------------
Solution Finding runs on the dimensional decomposition of one KPI. A dimensional
breakdown answers WHERE a KPI moved, never WHY. The causal graph and the market
signals are the only things that reach the cause — and until 2026-08-14 neither
arrived properly:

  * causal context was fetched single-hop, so on the lubricants graph
    `base_oil_cost -> cogs -> gross_margin_pct` (two hops) was invisible. A margin
    analysis could not see the cause of its own margin problem.
  * `market_signals` was never read by the Solution Finder at all.

THE MEASURE — cause vs symptom, NOT divergence
-----------------------------------------------
Seven prior arms measured divergence and it was the wrong construct. Here the
question is what each option ACTS ON:

  SYMPTOM  reprice Synthetic Blend, defend the Value tier, renegotiate Chain A
           -> acts on WHERE the KPI moved. All the dimensional analysis can say.
  CAUSE    renegotiate base-oil index formulas, hedge feedstock, reformulate to
           cut base-oil share, fix the pass-through lag
           -> acts on WHY. Only the causal chain / market signals can surface it.

Convergence is NOT a failure here. If every persona converges on fixing the
pass-through, the system is working — the opposite reading from arms 1-7.

CIRCULARITY GUARD
-----------------
Arms B and C put base oil IN THE PROMPT, so an option *mentioning* it proves
nothing. Both the segment (from DA) and the cause (from the graph) are in
context; which one the option ACTS ON is a genuine choice. Only the action counts.

ARMS — each step varies exactly one thing
------------------------------------------
  A  max_hops=1, no market signals   (production BEFORE 2026-08-14)
  B  max_hops=2, no market signals   (the traversal change)
  C  max_hops=2, WITH market signals (the MA routing change)

max_hops is read from SF_CAUSAL_MAX_HOPS at agent creation, so A and B need a
backend restart between them. C follows B with no restart (payload change only).

Usage:
    python tools/ab_harness/scope_arm.py <da-payload.json> <arm>     # arm = A|B|C
    python tools/ab_harness/scope_arm.py score                       # score saved arms
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
BASE = "http://localhost:8000/api/v1"

ARMS = {
    # First cut — CONFOUNDED. All three shared a refinement result whose
    # validated_hypotheses read "Base oil costs jumped 18% in Q2 and we could not
    # pass it through": the entire causal story, handed to every arm before the
    # graph was consulted. The traversal had nothing to add that the CFO had not
    # already said, so cause-vs-symptom could not discriminate (3/3 everywhere).
    "A": {"max_hops": 1, "market_signals": False, "refinement": True,
          "label": "hops=1, no MA, +refinement  (CONFOUNDED)"},
    "B": {"max_hops": 2, "market_signals": False, "refinement": True,
          "label": "hops=2, no MA, +refinement  (CONFOUNDED)"},
    "C": {"max_hops": 2, "market_signals": True, "refinement": True,
          "label": "hops=2, +MA, +refinement    (CONFOUNDED)"},
    # Corrected — no interview, so the causal graph is the ONLY possible source
    # of the upstream cause. Also the realistic case: a principal who skips the
    # refinement chat is exactly who the graph exists to serve.
    "A0": {"max_hops": 1, "market_signals": False, "refinement": False,
           "label": "hops=1, no MA, NO refinement (leaked market_conflict)"},
    "B0": {"max_hops": 2, "market_signals": False, "refinement": False,
           "label": "hops=2, no MA, NO refinement (leaked market_conflict)"},
    # Third cut. A0/B0 stripped `market_signals` but not `market_conflict`, whose
    # summary restates them in prose. With both gone the payload contains no
    # mention of base oil, crude or feedstock anywhere — so the causal graph is
    # the last REMOVABLE channel. What remains is the model's own domain
    # knowledge, which cannot be stripped: that is the real test here.
    "A0C": {"max_hops": 1, "market_signals": False, "refinement": False,
            "label": "hops=1, fully stripped (does the MODEL supply base oil?)"},
    "B0C": {"max_hops": 2, "market_signals": False, "refinement": False,
            "label": "hops=2, fully stripped (does the GRAPH supply base oil?)"},
    # ---------------------------------------------------------------------
    # RE-BASELINE (step 0c). Identical config to arm C — the production
    # default — but run AFTER two context defects were fixed:
    #   * DA KT summary rendered percentage points as dollars, collapsing the
    #     top two drivers onto the same "$-7" and asserting "(0.0% of variance)"
    #     against every one of them.
    #   * the causal_context audit read _cg_constraints before the register was
    #     queried, so every earlier run reported constraints: 0.
    # The 18 prior options were all generated over that broken context, so they
    # cannot serve as the comparator for the task-statement test — the fix would
    # ride along as a second variable.
    "C1": {"max_hops": 2, "market_signals": True, "refinement": True,
           "label": "hops=2, +MA, +refinement — RE-BASELINE with units fixed"},
    # Step 1 — task-statement test. Identical config to C1; only
    # SF_STAGE1_ALLOW_FRAME_CHALLENGE differs (env flag, read at agent
    # creation, so this needs its own restart). Compare against C1, not
    # against arms A/B/C/A0/B0/A0C, which all ran over the pre-unit-fix
    # context.
    "D1": {"max_hops": 2, "market_signals": True, "refinement": True,
           "label": "hops=2, +MA, +refinement, FRAME-CHALLENGE=true"},
    "D2": {"max_hops": 2, "market_signals": True, "refinement": True,
           "label": "hops=2, +MA, +refinement, FRAME-CHALLENGE=true (repeat, n=2)"},
    # Step 2 — lens swap. Identical config to C1 (task text unchanged, flag
    # back to default False) — only the roster differs: Commercial /
    # Operational / Structural instead of McKinsey / BCG / Bain. Requires its
    # own `consulting_personas` override in the POST body — see run_arm below.
    "E1": {"max_hops": 2, "market_signals": True, "refinement": True,
           "label": "hops=2, +MA, +refinement, LENS ROSTER (commercial/operational/structural)"},
    "E2": {"max_hops": 2, "market_signals": True, "refinement": True,
           "label": "hops=2, +MA, +refinement, LENS ROSTER (repeat, n=2)"},
}

_LENS_ARMS = {"E1", "E2"}

# Term screen. Produces CANDIDATES only — every hit is printed for adjudication,
# per the Phase 0 lesson where a bare term list ran a 71% false-positive rate.
CAUSE_TERMS = [
    "index", "indexation", "escalator", "pass-through", "pass through", "passthrough",
    "hedge", "hedging", "forward buy", "supplier contract", "procurement", "supply agreement",
    "reformulat", "formulation", "bill of materials", "base oil share", "additive package",
    "vertical integrat", "blender", "feedstock", "input cost contract", "lag",
]
SYMPTOM_TERMS = [
    "reprice", "price increase", "raise price", "list price", "discount", "rebate",
    "mix shift", "product mix", "customer negotiation", "renegotiate with", "account plan",
    "promotion", "shelf", "tier", "segment focus", "sku rationalis", "sku rationaliz",
]


def _post(url, body):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=900) as resp:
        return json.loads(resp.read().decode())


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url), timeout=900) as resp:
        return json.loads(resp.read().decode())


def run_arm(payload_path: Path, arm: str, label: str | None = None):
    """`label` names the output file instead of the arm letter.

    Needed whenever the same harness arm is run more than once with the variable
    living OUTSIDE the request body — e.g. Stage J posture experiments, where the
    roster and payload are identical and only `business_contexts.metadata`
    differs between runs. Without it two such runs both write
    `scope_arm_C.json` and the first is silently lost, which is the overwrite
    this harness already suffered once (see the Stage H A/B harness-hardening
    note in DEVELOPMENT_PLAN.md).
    """
    cfg = ARMS[arm]
    raw = json.loads(payload_path.read_text(encoding="utf-8"))
    da = raw.get("result", raw)

    if not cfg["market_signals"]:
        da = dict(da)
        da.pop("market_signals", None)
        # `market_conflict.summary` restates the signals in prose — "base oil supply
        # tightness, crude volatility, EV-driven demand softness" — so popping only
        # `market_signals` leaves the cause in the payload under a second key. This
        # silently confounded arms A0/B0 on their first run. Strip both.
        da.pop("market_conflict", None)

    refinement = None
    if cfg["refinement"]:
        with open(HERE / "refine_probe_result.json", encoding="utf-8") as f:
            refinement = json.load(f)

    roster = ["commercial", "operational", "structural"] if arm in _LENS_ARMS else ["mckinsey", "bcg", "bain"]
    body = {
        "principal_id": "cfo_001",
        "client_id": "lubricants",
        "deep_analysis_output": da,
        "refinement_result": refinement,
        "preferences": {
            "consulting_personas": roster,
            "council_preset": "recommended",
            "analysis_mode": "problem",
        },
    }

    print(f"ARM {arm}: {cfg['label']}")
    print(f"  roster                  : {roster}")
    print(f"  market_signals in payload: {'market_signals' in da}")
    print(f"  refinement_result       : {refinement is not None}")
    print(f"  (SF_CAUSAL_MAX_HOPS must be {cfg['max_hops']} on the running backend)")

    t0 = time.time()
    rid = (_post(f"{BASE}/workflows/solutions/run", body).get("data") or {}).get("request_id")
    print(f"  request_id={rid}")
    while True:
        time.sleep(5)
        d = _get(f"{BASE}/workflows/solutions/{rid}/status").get("data") or {}
        if d.get("state") in ("completed", "failed", "error"):
            break
        if time.time() - t0 > 900:
            print("  TIMEOUT"); return
    out = HERE / f"scope_arm_{label or arm}.json"
    if out.exists():
        # Never clobber a saved payload — the corpus IS the evidence.
        raise SystemExit(f"  REFUSING to overwrite {out.name} — pass a fresh label")
    out.write_text(json.dumps(d, indent=2, default=str), encoding="utf-8")
    sol = (d.get("result") or {}).get("solutions") or {}
    print(f"  state={d.get('state')} in {time.time()-t0:.0f}s, "
          f"{len(sol.get('options_ranked') or [])} options -> {out.name}")


def _text_of(opt: dict) -> str:
    parts = [str(opt.get(k, "")) for k in
             ("title", "description", "rationale", "implementation_approach", "mechanism")]
    for k in ("immediate_actions", "prerequisites", "next_steps"):
        v = opt.get(k)
        if isinstance(v, list):
            parts.extend(str(x) for x in v)
    return " ".join(parts)


def score(arms=("A", "B", "C")):
    print("=" * 96)
    print("CAUSE vs SYMPTOM — what does each option ACT ON?")
    print("Mentioning base oil is not evidence (it is in the prompt for B/C). Only the action counts.")
    print("=" * 96)
    summary = []
    for arm in arms:
        p = HERE / f"scope_arm_{arm}.json"
        if not p.exists():
            print(f"\n[{arm}] not run")
            continue
        sol = (json.loads(p.read_text(encoding="utf-8")).get("result") or {}).get("solutions") or {}
        opts = sol.get("options_ranked") or []
        print(f"\n{'=' * 96}\nARM {arm} — {ARMS[arm]['label']}   ({len(opts)} options)\n{'=' * 96}")
        n_cause = n_symptom = 0
        for o in opts:
            blob = _text_of(o).lower()
            c = sorted({t for t in CAUSE_TERMS if t in blob})
            s = sorted({t for t in SYMPTOM_TERMS if t in blob})
            n_cause += bool(c)
            n_symptom += bool(s)
            print(f"\n  TITLE: {str(o.get('title',''))[:110]}")
            print(f"    cause-terms  : {c or '-'}")
            print(f"    symptom-terms: {s or '-'}")
            print(f"    {str(o.get('description',''))[:260]}")
        summary.append((arm, n_cause, n_symptom, len(opts)))

    print("\n" + "=" * 96)
    print(f"  {'arm':6} {'cause':>7} {'symptom':>9} {'options':>9}")
    for arm, c, s, n in summary:
        print(f"  {arm:6} {c:>7} {s:>9} {n:>9}")
    print("\n  Counts are CANDIDATES from a term screen. Read the options above and")
    print("  adjudicate — Phase 0's screen ran 71% false positives on a similar task.")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "score":
        score()
        return
    # optional 3rd arg: output label, for repeat runs of one arm where the
    # variable lives outside the request body (see run_arm docstring)
    run_arm(Path(sys.argv[1]), sys.argv[2].upper(),
            sys.argv[3] if len(sys.argv) > 3 else None)


if __name__ == "__main__":
    main()
