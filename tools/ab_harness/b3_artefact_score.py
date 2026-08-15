"""Phase 0 outcome measure — does a council challenge the NUMBER before diagnosing the BUSINESS?

WHY THIS EXISTS
---------------
Every B-3 arm measured divergence. Divergence is a proxy: a council can diverge
beautifully and elicit worse constraints. This scores the arms on something that
actually matters and that this project has already been burned by.

THE FAILURE BEING SCORED (2026-08-09, real)
-------------------------------------------
COGS was allocated to a single customer while revenue spanned twenty. Gross margin
by customer therefore read -457.71% for one account and exactly 100.00% for the
other nineteen. The enterprise figure was correct throughout, which is why it
survived. SA raised a breach, DA found "concentration", three MBB personas
diagnosed a base-oil pass-through, and the briefing recommended renegotiating a
contract to fix an ETL defect. Every layer behaved correctly on top of a number
that was not real.

The question that catches it challenges HOW COST WAS ASSIGNED TO THE SLICE before
accepting the slice as a business signal. That is the property being scored — and
note it should be asked as STANDARD PRACTICE, not only when someone already
suspects an artefact. All arms below saw the POST-fix (clean) data, so any hit
here is the method asking unprompted.

METHOD
------
Deterministic term matching, then EVERY match is printed for inspection. The
number alone is not the output — a term list cannot tell "resource allocation"
(capital allocation, not an artefact question) from "overhead allocation". Read
the matches; they are the evidence.

Usage:  python tools/ab_harness/b3_artefact_score.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent

# Terms that mark a question as challenging cost ASSIGNMENT / MEASUREMENT rather
# than commercial cause. Deliberately narrow: "cost" and "margin" appear in
# every question in every arm and carry no signal.
ARTEFACT_TERMS = [
    "absorption", "absorb", "under-absorb", "unabsorbed",
    "overhead", "standard cost", "costing", "cost method", "methodology",
    "allocat",            # inspect: capital/resource allocation is NOT this
    "apportion", "assigned", "assignment",
    "ledger", "general ledger", "booked", "accounting",
    "granularity", "same grain", "same level",
]

# Arms, in the order they were run.
ARMS = [
    ("MBB · sonnet-5 · registry profiles",      "b3_results.json"),
    ("MBB · fable-5 · registry profiles",       "b3_results_mbb_claude-fable-5.json"),
    ("diverse council · sonnet-5 · registry",   "b3_results_diverse.json"),
    ("famous four · sonnet-5 · authored",       "b3_results_famous.json"),
    ("20 methods · sonnet-5 · authored",        "b3_discovery_round_results.json"),
    ("20 methods · fable-5 · authored",         "b3_discovery_round_claude-fable-5.json"),
    ("20 methods · fable-5 · NAME ONLY",        "b3_discovery_round_claude-fable-5_bare.json"),
]


def _questions(payload: dict) -> dict:
    """Normalise both harness output shapes to {persona: [question, ...]}."""
    out = {}
    for pid, val in (payload.get("results") or {}).items():
        if isinstance(val, list):                       # b3_question_divergence
            out[pid] = [q.get("question", "") for q in val]
        elif isinstance(val, dict):                     # b3_discovery_round
            out[pid] = [
                val.get("opening", {}).get("question", ""),
                val.get("followup", {}).get("question", ""),
            ]
    return out


# ---------------------------------------------------------------------------
# ADJUDICATION — recorded, not inferred.
#
# The term screen produces CANDIDATES. Whether a candidate genuinely challenges
# cost assignment is a semantic judgement, so it is recorded here explicitly
# rather than encoded as a cleverer regex. Tuning a classifier until it agrees
# with the reader is the same circularity this project keeps catching; keeping
# screen and verdict separate is the `src/analysis` discipline (a check returns
# True / False / None, and not-checked is never pass).
#
# Keyed (arm_file, persona, first 40 chars of question).
# ---------------------------------------------------------------------------
ADJUDICATION = {
    # GENUINE — challenges whether the number is an artefact of cost assignment
    ("b3_discovery_round_results.json", "carnegie", "Were any of these five lines running below"): True,
    ("b3_discovery_round_results.json", "deming", "If all five lines are moving together in t"): True,
    ("b3_discovery_round_claude-fable-5.json", "ohno", "Before we accept these margin numbers as a"): True,
    ("b3_discovery_round_claude-fable-5.json", "ohno", "When you say margin fell, I hear only the a"): True,
    ("b3_discovery_round_claude-fable-5_bare.json", "deming", "If it is a genuine signal beginning in per"): True,
    # PARTIAL — decomposes the blended figure but does not question its validity
    ("b3_discovery_round_results.json", "carnegie", "For each of these five lines, can you give"): False,
    ("b3_discovery_round_claude-fable-5_bare.json", "rockefeller", "Before we talk price, show me the ledger o"): False,
    # FALSE POSITIVE — "absorb" in the commercial sense (we ate the cost increase)
    ("b3_results.json", "bcg", "Have input costs (base oil, additives, pac"): False,
    ("b3_discovery_round_results.json", "sloan", "If it's trade-down rather than pricing, we"): False,
    ("b3_discovery_round_claude-fable-5.json", "rockefeller", "If the base stock and additive suppliers a"): False,
    ("b3_discovery_round_claude-fable-5_bare.json", "bezos", "Before we treat this margin compression as"): False,
    ("b3_discovery_round_claude-fable-5_bare.json", "buffett", "When input costs rose on these oil lines, "): False,
    ("b3_discovery_round_claude-fable-5_bare.json", "rockefeller", "If the whole Value category is bleeding ma"): False,
    ("b3_discovery_round_claude-fable-5_bare.json", "sloan", "Before we treat this as one problem, tell "): False,
    # FALSE POSITIVE — "allocation" meaning capital/resource, not cost assignment
    ("b3_discovery_round_results.json", "christensen", "Pull up the resource allocation history fo"): False,
    ("b3_discovery_round_claude-fable-5.json", "christensen", "If a lower-cost entrant is establishing a "): False,
    # WEAK — names product costing as one of several possibly-broken capabilities,
    # but still frames it as "what is broken in the business", not "is this real"
    ("b3_results_diverse.json", "pwc_strategy", "Which specific capabilities—pricing govern"): False,
}


def _adjudicate(fname: str, pid: str, q: str):
    """True = genuine artefact challenge, False = screened out, None = unreviewed.

    Prefix match rather than exact slice: the recorded keys are hand-written
    excerpts, and an off-by-one silently turned every verdict into `unreviewed`
    (which then read as 0 genuine — a not-checked masquerading as a fail).
    """
    text = q.strip()
    for (f, p, prefix), verdict in ADJUDICATION.items():
        if f == fname and p == pid and text.startswith(prefix):
            return verdict
    return None


def _hits(text: str) -> list:
    low = text.lower()
    return [t for t in ARTEFACT_TERMS if t in low]


def main():
    print("=" * 100)
    print("PHASE 0 — artefact-challenge rate per council")
    print("Does any persona question HOW COST WAS ASSIGNED before diagnosing a commercial cause?")
    print("=" * 100)

    summary = []
    for label, fname in ARMS:
        path = HERE / fname
        if not path.exists():
            print(f"\n[missing] {fname}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        qs = _questions(payload)

        screened, genuine, unreviewed = {}, set(), 0
        for pid, questions in qs.items():
            for q in questions:
                if not _hits(q):
                    continue
                verdict = _adjudicate(fname, pid, q)
                screened.setdefault(pid, []).append((verdict, q))
                if verdict is True:
                    genuine.add(pid)
                elif verdict is None:
                    unreviewed += 1

        n_personas = len(qs)
        summary.append((label, len(screened), len(genuine), n_personas, unreviewed))

        print(f"\n{'=' * 100}")
        print(f"{label}")
        print(f"  screened by terms: {len(screened)}/{n_personas}   "
              f"GENUINE after adjudication: {len(genuine)}/{n_personas}"
              + (f"   UNREVIEWED: {unreviewed}" if unreviewed else ""))
        print("=" * 100)
        if not screened:
            print("  (nothing screened)")
        for pid, items in sorted(screened.items()):
            for verdict, q in items:
                mark = {True: "GENUINE ", False: "screened", None: "UNREVIEWED"}[verdict]
                print(f"  [{mark}] {pid}")
                print(f"      {q.strip()[:300]}")

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"  {'arm':40} {'screened':>9} {'genuine':>8} {'of':>4}  {'rate':>6}")
    for label, n_scr, n_gen, tot, _u in summary:
        print(f"  {label:40} {n_scr:>9} {n_gen:>8} {tot:>4}  {n_gen/tot:>5.0%}")

    tot_scr = sum(s[1] for s in summary)
    tot_gen = sum(s[2] for s in summary)
    print(f"\n  Term screen produced {tot_scr} candidates; {tot_gen} survived adjudication "
          f"({1 - tot_gen / tot_scr:.0%} false-positive rate).")
    print("  The dominant false positive is 'absorb' in the commercial sense — 'we absorbed")
    print("  the cost increase' is not absorption costing. Second is 'allocation' meaning")
    print("  capital or resource allocation rather than cost assignment.")


main()
