"""Does the DEEP ANALYSIS HANDOVER cause the convergence? (the variable never varied)

THE HYPOTHESIS
--------------
Seven B-3 arms varied roster, model and prompt richness. All seven held ONE thing
constant: every persona received the identical Deep Analysis output — an SCQA
narrative that already names the situation, asserts the complication, and ranks
the drivers. Personas were then asked what to enquire about, starting from a
shared conclusion.

If that framing is what channels everyone down one path, convergence is a
handover problem and is fixable. If it is the problem itself that admits few
useful questions, convergence is irreducible and no council helps.

The earlier write-up asserted the second without testing it. This tests it.

THE ARMS — four levels, each adjacent pair varying ONE thing
------------------------------------------------------------
  A  DIAGNOSIS    _build_kt_summary(): SCQA narrative + "Top Drivers" + IS-NOT,
                  truncated to the top 8 segments.          [= production today]
  D  FRAMED_FULL  the same SCQA narrative, but over ALL ~40 measured segments.
  B  EVIDENCE     all segments, ranked by magnitude, NO narrative.
  C  RAW          all segments, sorted ALPHABETICALLY, no ranking, no narrative.

  A -> D  isolates BREADTH   (both framed; 8 segments vs 40)
  D -> B  isolates NARRATIVE (both full breadth; story vs no story)
  B -> C  isolates RANKING   (both full, unframed; ranked vs alphabetical)

The first cut of this test ran only A/B/C, which confounded framing removal with a
5x increase in segment count — more segments alone plausibly produces more
divergence. D separates them.

Roster, model, effort and prompt style are held at the most differentiated
configuration already measured (20 methods, name-only, sonnet-5, medium) so that
any remaining convergence is attributable to the input rather than the council.

Usage:  python tools/ab_harness/b3_input_framing.py <da-payload.json>
"""
from __future__ import annotations

import json
import os
import random
import re
import statistics
import sys
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

import anthropic  # noqa: E402

from b3_discovery_round import MINDS, TOPIC_VOCAB, _content_words, _jaccard  # noqa: E402

MODEL = "claude-sonnet-5"
EFFORT = "medium"

_UTTERANCE = {
    "type": "object",
    "properties": {"question": {"type": "string"},
                   "topic": {"type": "string", "enum": TOPIC_VOCAB}},
    "required": ["question", "topic"],
    "additionalProperties": False,
}
_SCHEMA = {
    "type": "object",
    "properties": {"opening": _UTTERANCE, "followup": _UTTERANCE},
    "required": ["opening", "followup"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------------------
# The three inputs
# ---------------------------------------------------------------------------

def _segments(execution: dict) -> list:
    """Every segment DA measured, IS and IS-NOT alike, as (dimension, key, delta)."""
    kt = execution.get("kt_is_is_not") or {}
    rows = []
    for side in ("where_is", "where_is_not"):
        for r in kt.get(side) or []:
            if isinstance(r, dict) and r.get("key") is not None:
                rows.append((r.get("dimension", "?"), str(r.get("key")), r.get("delta")))
    return rows


def build_inputs(da: dict) -> dict:
    from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent

    execution = da.get("execution", da)
    kpi = (da.get("plan") or {}).get("kpi_name") or execution.get("kpi_name") or "the KPI"

    # A — exactly what production hands over today
    a = A9_Deep_Analysis_Agent({})._build_kt_summary(da)

    rows = _segments(execution)

    def _fmt(r):
        d, k, delta = r
        return f"  {d} = {k}: {delta:+.2f}" if isinstance(delta, (int, float)) else f"  {d} = {k}: {delta}"

    # B — same evidence, ranked, no narrative
    ranked = sorted(
        [r for r in rows if isinstance(r[2], (int, float))],
        key=lambda r: -abs(r[2]),
    )
    b = (
        f"KPI: {kpi}\n"
        f"Comparison: year-to-date vs prior year-to-date. Units are percentage points.\n\n"
        f"Segment movements, largest first:\n" + "\n".join(_fmt(r) for r in ranked)
    )

    # C — same evidence, alphabetical, IS/IS-NOT merged, no ranking, no story
    alpha = sorted(rows, key=lambda r: (r[0], r[1]))
    c = (
        f"KPI: {kpi}\n"
        f"Comparison: year-to-date vs prior year-to-date. Units are percentage points.\n\n"
        f"Measured values by segment:\n" + "\n".join(_fmt(r) for r in alpha)
    )

    # D — A's narrative framing, but over the full segment set. Isolates breadth
    # from framing: A truncates to 8 segments, B/C carry ~40.
    narrative = a.split("Top Drivers")[0].rstrip()
    d = (
        f"{narrative}\n\n"
        f"Segment movements, largest first:\n" + "\n".join(_fmt(r) for r in ranked)
    )

    # Ordered so each adjacent pair varies exactly one thing.
    return {"A_diagnosis": a, "D_framed_full": d, "B_evidence": b, "C_raw": c}


# ---------------------------------------------------------------------------

def _ask(client, pid: str, kt: str):
    name = MINDS[pid].split(" — ")[0]
    system = (
        "Reason in the documented style of the business thinker named below, applying "
        "the method and priorities they are known for. Do not roleplay or write in "
        "first person as them — produce the enquiry their method implies.\n\n"
        f"## THE THINKER\n{name}\n\n"
        "## WHAT THE ANALYSIS PRODUCED (do not ask for more of this data)\n"
        f"{kt}\n\n"
        "## YOUR TASK\n"
        "You get ONE opening question to the CFO, and ONE follow-up or comment after it. "
        "That is your entire turn in a discovery round, so spend it on what only this "
        "method would think to ask. Ask what only the executive can answer.\n\n"
        "Tag each with the single best-fitting topic from:\n" + ", ".join(TOPIC_VOCAB)
    )
    # Structured output rather than regex-scraping a JSON block. An earlier run
    # died on arm 3 of 4 when one question contained a character that broke the
    # scrape, discarding 40 completed calls. The schema makes that unrepresentable.
    r = client.messages.create(
        model=MODEL, max_tokens=700,
        output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": _SCHEMA}},
        system=system,
        messages=[{"role": "user", "content": "Return the JSON object."}],
    )
    if r.stop_reason == "refusal":
        raise SystemExit(f"{pid}: refused — discard this arm")
    text = next((b.text for b in r.content if getattr(b, "type", None) == "text"), "")
    return json.loads(text), r.usage.input_tokens, r.usage.output_tokens


def _null(n_personas: int, picks: int = 2, trials: int = 8000):
    rng = random.Random(7)
    means = []
    for _ in range(trials):
        sets = [set(rng.sample(range(len(TOPIC_VOCAB)), picks)) for _ in range(n_personas)]
        means.append(statistics.mean(_jaccard(a, b) for a, b in combinations(sets, 2)))
    means.sort()
    return statistics.mean(means), means[int(0.05 * len(means))], means[int(0.95 * len(means))]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    da = raw.get("result", raw)
    inputs = build_inputs(da)

    print("=" * 90)
    print(f"INPUT FRAMING TEST — {len(MINDS)} methods, name-only, {MODEL}, effort={EFFORT}")
    print("Roster/model/prompt held constant. INPUT FRAMING is the only variable.")
    print("=" * 90)
    for k, v in inputs.items():
        print(f"\n--- {k} ({len(v)} chars) ---\n{v[:420]}{'…' if len(v) > 420 else ''}")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    null_mean, null_p05, null_p95 = _null(len(MINDS))
    summary, all_results = [], {}
    tok_in = tok_out = 0

    for arm, kt in inputs.items():
        results = {}
        for pid in MINDS:
            d, ti, to = _ask(client, pid, kt)
            results[pid] = d
            tok_in += ti
            tok_out += to
        all_results[arm] = results

        topics = {p: {d["opening"].get("topic"), d["followup"].get("topic")} for p, d in results.items()}
        words = {p: _content_words([d["opening"].get("question", ""), d["followup"].get("question", "")])
                 for p, d in results.items()}
        t = statistics.mean(_jaccard(topics[a], topics[b]) for a, b in combinations(topics, 2))
        l = statistics.mean(_jaccard(words[a], words[b]) for a, b in combinations(words, 2))
        terms = len(set().union(*words.values()))
        summary.append((arm, t, l, terms))
        print(f"\n[{arm}]  topic J={t:.3f}   lexical J={l:.3f}   distinct terms={terms}")

    print("\n" + "=" * 90)
    print("RESULT — does removing the diagnosis reduce convergence?")
    print("=" * 90)
    print(f"  random-tagger null: {null_mean:.3f}  (90% {null_p05:.3f}-{null_p95:.3f})\n")
    print(f"  {'arm':16} {'topic J':>9} {'vs null':>10} {'lexical J':>11} {'terms':>7}")
    for arm, t, l, terms in summary:
        rel = "ABOVE (converged)" if t > null_p95 else ("at null" if t >= null_p05 else "BELOW (diverged)")
        print(f"  {arm:16} {t:>9.3f} {rel:>18} {l:>11.3f} {terms:>7}")

    by = {a: t for a, t, _l, _n in summary}
    print("\n  ISOLATED EFFECTS (each pair varies exactly one thing):")
    print(f"    breadth   A -> D : {by['A_diagnosis']:.3f} -> {by['D_framed_full']:.3f}  "
          f"({by['D_framed_full'] - by['A_diagnosis']:+.3f})   8 segments -> 40, both framed")
    print(f"    narrative D -> B : {by['D_framed_full']:.3f} -> {by['B_evidence']:.3f}  "
          f"({by['B_evidence'] - by['D_framed_full']:+.3f})   story removed, breadth held")
    print(f"    ranking   B -> C : {by['B_evidence']:.3f} -> {by['C_raw']:.3f}  "
          f"({by['C_raw'] - by['B_evidence']:+.3f})   rank order removed")
    print(f"    TOTAL     A -> C : {by['A_diagnosis']:.3f} -> {by['C_raw']:.3f}  "
          f"({by['C_raw'] - by['A_diagnosis']:+.3f})")
    print("\n  Falling toward the null = that factor was doing the converging (fixable).")
    print("  Flat = the problem admits few questions regardless (irreducible).")
    print(f"\nCOST: {tok_in} in / {tok_out} out across {len(MINDS) * len(inputs)} {MODEL} calls")

    out = Path(__file__).parent / "b3_input_framing_results.json"
    out.write_text(json.dumps({
        "model": MODEL, "effort": EFFORT, "inputs": inputs, "results": all_results,
        "summary": [{"arm": a, "topic_jaccard": t, "lexical_jaccard": l, "terms": n}
                    for a, t, l, n in summary],
        "null": {"mean": null_mean, "p05": null_p05, "p95": null_p95},
        "tokens_in": tok_in, "tokens_out": tok_out,
    }, indent=2), encoding="utf-8")
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
