"""
Score every saved SF payload against the six Decision Quality links.

Retrospective only — reads `scope_arm_*.json` from disk, makes no API call.
See `docs/architecture/decision_quality_rubric.md` for the rubric, the corpus
limits, and the prediction recorded before this was run.

    py tools/ab_harness/dq_score.py

Arms are stratified pre/post the `_build_kt_summary` unit fix (§7c) because the
pre-fix arms saw percentage-point deltas rendered as dollars in the context every
persona read. Pooling them would blend two different inputs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analysis.decision_quality import score_run  # noqa: E402

HERE = Path(__file__).resolve().parent

# §7c: C1 is the first arm run after both false-zero fixes landed.
POST_FIX = ["C1", "D1", "D2", "E1", "E2"]
PRE_FIX = ["A", "A0", "A0C", "B", "B0", "C"]

ARM_NOTE = {
    "A": "1 hop, refinement on", "B": "2 hops", "C": "2 hops + market signals",
    "A0": "no refinement", "B0": "2 hops, no refinement",
    "A0C": "no refinement, market_conflict stripped",
    "C1": "re-baseline after unit + audit fixes (CONTROL)",
    "D1": "frame-challenge flag on", "D2": "frame-challenge flag on",
    "E1": "lens swap: commercial/operational/structural",
    "E2": "lens swap, replicate",
}

LINKS = ["frame", "alternatives", "information", "tradeoffs", "reasoning", "commitment"]

# ADJUDICATION OF THE LINK-1 SCREEN, recorded as data beside the screen rather
# than folded into a cleverer regex (§5: a term screen for a semantic property
# produced a 71% false-positive rate, so the screen is never the verdict).
#
# Every arm whose screen fired was read in context. Verdict + reason below.
FRAME_ADJUDICATION = {
    "D1": (True, "opt_2 'Immediate SKU Rationalization' genuinely proposes discontinuing "
                 "and delisting SKUs — acts on portfolio composition, not on the price or "
                 "cost of the existing portfolio"),
    "E2": (True, "opt_3 proposes 'SKU exit/de-emphasis' with volume reallocated to other "
                 "formulations — a mix/portfolio move, though paired with price recovery"),
}
# Screens that fired and did NOT survive reading are recorded too, so the
# false-positive rate of this instrument stays visible.
FRAME_REJECTED = {
    "A": "matched `full-potential` on 'Full Potential Margin Recovery: Accelerated Renewal, "
         "Cost Reserve & Base Oil Sourcing Diversification' — Bain vocabulary attached to an "
         "ordinary KPI-recovery plan. Rejected; the auto-pass on lever family was removed.",
}


def load(arm: str):
    p = HERE / f"scope_arm_{arm}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["result"]["solutions"], (d.get("payload") or {}).get("deep_analysis_output")


def mark(v):
    return {True: "PASS", False: "FAIL", None: " -- "}[v]


def report(arms, heading):
    print(f"\n{'=' * 100}\n{heading}\n{'=' * 100}")
    scores = []
    for arm in arms:
        loaded = load(arm)
        if not loaded:
            print(f"  {arm}: MISSING")
            continue
        solutions, da = loaded
        s = score_run(solutions, da_result=da, run_id=arm)
        scores.append(s)
        chain = {True: "HOLDS", False: "CAPPED", None: "UNSCORED"}[s.chain_verdict]
        print(f"\n  {arm:4s} ({ARM_NOTE.get(arm, '')})")
        print(f"       chain={chain:8s} links passed={s.passed}/{s.checked}  "
              f"levers={s.distinct_lever_families} classified"
              f"{f' +{s.unclassified_options} unclassified' if s.unclassified_options else ''}"
              f" of {s.n_options} options")
        for l in s.links():
            flag = " (advisory)" if l.advisory else ""
            print(f"         {mark(l.passed)}  {l.name:13s}{flag:11s} {l.detail[:100]}")
        if s.l1_frame.passed and arm not in FRAME_ADJUDICATION:
            print(f"         ^^ frame screen fired but is UNADJUDICATED — not a pass")
        if arm in FRAME_ADJUDICATION:
            print(f"         >> frame ADJUDICATED GENUINE: {FRAME_ADJUDICATION[arm][1][:150]}")
        if arm in FRAME_REJECTED:
            print(f"         >> frame screen REJECTED on reading: {FRAME_REJECTED[arm][:150]}")
    return scores


def summarise(scores, heading):
    if not scores:
        return
    print(f"\n  --- {heading}: per-link pass rate ---")
    for i, name in enumerate(LINKS):
        vals = [s.links()[i].passed for s in scores]
        checked = [v for v in vals if v is not None]
        rate = f"{sum(1 for v in checked if v)}/{len(checked)}" if checked else "0/0 (never checked)"
        print(f"    {name:13s} {rate}")
    caps = {}
    for s in scores:
        for w in s.weakest_links:
            caps[w] = caps.get(w, 0) + 1
    print(f"    capped by: {caps or 'nothing — no link failed anywhere'}")


if __name__ == "__main__":
    post = report(POST_FIX, "POST-FIX STRATUM (clean context)")
    summarise(post, "post-fix")
    pre = report(PRE_FIX, "PRE-FIX STRATUM (broken _build_kt_summary unit string)")
    summarise(pre, "pre-fix")

    print(f"\n{'=' * 100}\nCOMBINED: {len(post) + len(pre)} runs, "
          f"{sum(s.n_options for s in post + pre)} options\n{'=' * 100}")
    summarise(post + pre, "all arms")
