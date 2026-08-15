"""Phase 15 Stage I B-3 — the ~$0.50 gate.

THE QUESTION
------------
Stage I's premise is that three MBB personas produce "one analysis in three
costumes" because every point at which they could diverge has been removed
before they are invoked. B-4 would fix that by giving each persona its own
questions in the refinement interview and its own constraint set.

Before building it: **would they actually ask different questions?**

If all three converge on the same questions, a shared question queue buys
nothing, Stage I closes at B-2, and "the frameworks do not diverge even on what
they would ask" is a real finding obtained for pocket change.

SCOPE NOTE
----------
The dev plan's original gate also asked which DATA CUTS each persona wanted.
That half is moot: personas share one Deep Analysis evidence base by decision
(see DEVELOPMENT_PLAN Stage I / plan Part B) — three personas reasoning off
three different evidence bases would weaken G3, since the moderator cannot check
arithmetic against data it never saw.

MEASUREMENT
-----------
No LLM judge — a stochastic ruler cannot measure a stochastic process. Two
deterministic comparisons:

  1. topic-set Jaccard  — each persona tags its own questions from OUR fixed
     topic vocabulary. Self-tagging is structured output, not adjudication.
  2. lexical Jaccard    — content-word overlap of the question text itself.
     Crude, but it does not depend on the model's self-tagging at all.

GATE: proceed to B-4 only if BOTH mean pairwise Jaccards are <= 0.7 AND the
divergence is directional on inspection rather than noise.

WHY A DIRECT API CALL
---------------------
There is no endpoint for "propose refinement questions" — that is the thing B-4
would build, so probing it through the app is circular. The no-direct-LLM-import
rule governs agent files (`src/agents/`); this is a tools/ experiment script.
Persona profiles and the KT summary are loaded from the real registry and a real
DA payload so the probe is representative rather than invented.

Usage:
    python tools/ab_harness/b3_question_divergence.py <path-to-da-payload.json>
"""
from __future__ import annotations

import json
import os
import re
import sys
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

import anthropic  # noqa: E402

MODEL = "claude-sonnet-5"  # matches CLAUDE_MODEL_REASONING, what refinement actually uses
MBB_PERSONAS = ["mckinsey", "bcg", "bain"]
N_QUESTIONS = 6

# The real vocabulary the interview routes over (a9_deep_analysis_agent.py).
TOPIC_VOCAB = [
    "hypothesis_validation", "scope_boundaries", "external_context",
    "constraints", "success_criteria", "replication_potential",
    "tradeoff_tolerance", "segment_specific_causation", "comparison_baseline",
]

_STOP = set("""
a an the and or but if is are was were be been being of to in on at for with by from as that this
these those it its we you they i do does did what which who whom how why when where should would
could can may might will shall about into over under than then there their our your his her not no
any all some each per vs versus given does do
""".split())


# Control arm: operators with sharply opposed philosophies, written in the same
# shape as ConsultingPersona.to_prompt_context() — including known biases, which
# is what keeps a persona honest rather than hagiographic. If personas THIS far
# apart still converge, the convergence is structural (one problem, one shared
# evidence base) rather than a defect in the consulting persona definitions.
FAMOUS_PROFILES = {
    "buffett": """Specialty: Capital allocation and durable competitive advantage
Methodology: Judge the business, not the quarter. Test for pricing power first — a business that cannot raise
  price without losing volume has no moat, and a margin problem there is structural, not operational.
  Frameworks: owner earnings, return on incremental invested capital, circle of competence, moat durability.
Perspective: Strengths — separates price from value; ruthless about businesses that consume capital and return
  little; will say a business is simply not a good one. Known biases — skeptical of technology-led fixes;
  reaches for raising price before cutting cost; averse to capital-hungry remedies; may write off a fixable
  operating problem as a permanently poor business.
Output Style: Plain language, homely analogies, blunt. Short. Avoids jargon entirely.""",

    "bezos": """Specialty: Customer-backwards reasoning and long-run free cash flow per share
Methodology: Work backwards from the customer, then find the controllable INPUT metrics that drive the output
  metric — margin is an output; nobody can act on it directly. Distinguish one-way doors (decide slowly) from
  two-way doors (decide fast). Frameworks: working backwards, input vs output metrics, Day 1, disagree and commit.
Perspective: Strengths — refuses to accept an aggregate number as actionable; converts a margin problem into the
  handful of inputs that produce it. Known biases — tolerant of thin margin if it buys share or scale; inclined to
  treat margin defense as short-term thinking; prefers building a new mechanism to repairing an existing one.
Output Style: Narrative memo prose, full sentences, no bullet points. Precise and unhurried.""",

    "musk": """Specialty: First-principles cost engineering and vertical integration
Methodology: Reduce the product to its raw material cost floor and ask why the actual cost differs — the ratio of
  the two is the only number that matters. Question every requirement, including who set it and whether they were
  right. Frameworks: the algorithm (question requirements, delete, simplify, accelerate, automate), idiot index.
Perspective: Strengths — attacks the cost structure itself rather than negotiating the price; finds the
  theoretical floor and treats everything above it as a defect. Known biases — treats contractual and
  organizational constraints as requirements to be challenged rather than facts; over-favors bringing work
  in-house; timelines are optimistic.
Output Style: Terse, numeric, blunt to the point of rudeness. No preamble.""",

    "ohno": """Specialty: Waste elimination and root-cause diagnosis at the place the work happens
Methodology: Go and see for yourself — a number in a report is not a cause. Ask why five times; the first answer
  is a symptom. Cost is reduced by removing waste from the process, never by raising price or cutting people.
  Frameworks: 5 Whys, the seven wastes (muda), just-in-time, jidoka (stop the line on a defect).
Perspective: Strengths — refuses to accept an aggregate or an average as an explanation; insists on the specific
  operation where value stops being added. Known biases — distrusts any diagnosis made away from the workplace,
  including this one; may reject data-only analysis as fundamentally insufficient; horizon is patient and
  incremental where the situation may demand speed.
Output Style: Asks rather than asserts. Socratic and very terse. Answers a question with a better question.""",
}
FAMOUS_PERSONAS = list(FAMOUS_PROFILES)


def _resolve_diverse_council(da_payload: dict) -> list:
    """Ask DA for the council it would actually recommend for this problem.

    Uses the real `_recommend_diverse_council` rather than a hardcoded list, so
    the probe tests the council the system ships (`council_preset:
    "recommended"`) rather than one invented for the experiment.
    """
    from src.agents.models.deep_analysis_models import ExtractedRefinements
    from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent

    agent = A9_Deep_Analysis_Agent({})
    execution = da_payload.get("execution", da_payload)
    return agent._recommend_diverse_council(
        {"role": "CFO", "principal_id": "cfo_001", "decision_style": "analytical"},
        ExtractedRefinements(),
        execution,
    )


def _persona_profiles(persona_ids: list) -> dict:
    """Real profiles from the registry, including each firm's known biases."""
    from src.registry.consulting_personas.consulting_persona_provider import (
        ConsultingPersonaProvider,
    )

    provider = ConsultingPersonaProvider()
    out = {}
    for pid in persona_ids:
        p = provider.get_persona(pid)
        if p is None:
            raise SystemExit(f"persona '{pid}' not found in registry")
        out[pid] = p.to_prompt_context() if hasattr(p, "to_prompt_context") else str(p)
    return out


def _kt_summary(da_payload: dict) -> str:
    """Rebuild the same context the refinement agent gets."""
    from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent

    agent = A9_Deep_Analysis_Agent({})
    return agent._build_kt_summary(da_payload)


_FAMOUS_ROLE = {
    "buffett": "Warren Buffett", "bezos": "Jeff Bezos",
    "musk": "Elon Musk", "ohno": "Taiichi Ohno",
}


def _ask(client, persona_id: str, profile: str, kt: str, famous: bool = False) -> list:
    if famous:
        # Reason in this person's documented style — not an impersonation, and
        # the answers stand or fall as questions, not as claims about anyone.
        role = (
            f"Reason in the documented style of {_FAMOUS_ROLE[persona_id]}, applying the "
            "method and priorities described below. Do not roleplay or write in first "
            "person as them; produce the questions their method implies."
        )
        header = "## THE METHOD YOU ARE APPLYING"
        whose = "this method"
    else:
        role = f"You are a {persona_id.upper()} consultant."
        header = "## YOUR FIRM'S PROFILE"
        whose = "your firm's methodology"

    system = (
        f"{role}\n\n"
        f"{header}\n{profile}\n\n"
        "## THE ANALYSIS (already complete — do not ask for more data)\n"
        f"{kt}\n\n"
        "## YOUR TASK\n"
        f"Before proposing any solution, you get to interview the CFO. Propose the "
        f"{N_QUESTIONS} questions {whose} says matter most for bounding this problem. "
        "Ask what only the executive can answer; the data above is already known.\n\n"
        "Tag each question with the single best-fitting topic from this list:\n"
        + ", ".join(TOPIC_VOCAB) + "\n\n"
        '## OUTPUT (JSON only)\n'
        '{"questions": [{"question": "<one question>", "topic": "<topic from the list>"}]}'
    )
    # No `temperature` — it is rejected with a 400 on claude-sonnet-5 (removed,
    # not deprecated-but-tolerated). `effort` is the replacement control.
    kwargs = dict(
        model=MODEL, max_tokens=1500,
        output_config={"effort": "medium"},
        system=system,
        messages=[{"role": "user", "content": "Return ONLY the JSON object."}],
    )
    if MODEL.startswith("claude-fable"):
        r = client.beta.messages.create(
            betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs
        )
    else:
        r = client.messages.create(**kwargs)
    if r.stop_reason == "refusal":
        cat = getattr(getattr(r, "stop_details", None), "category", None)
        raise SystemExit(f"{persona_id}: refused (category={cat!r}) — discard this arm")
    # Never index content[0] blindly: thinking is ON BY DEFAULT on claude-sonnet-5
    # with display="omitted", so the first block is often an empty ThinkingBlock.
    text = next((b.text for b in r.content if getattr(b, "type", None) == "text"), "")
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise SystemExit(f"{persona_id}: no JSON in response:\n{text[:400]}")
    data = json.loads(m.group())
    return data.get("questions", []), r.usage.input_tokens, r.usage.output_tokens


def _random_tagger_baseline(n_personas: int, trials: int = 20000):
    """What mean pairwise Jaccard does a RANDOM tagger produce?

    Choosing N_QUESTIONS topics from a fixed vocabulary guarantees overlap by
    arithmetic alone — for 6 picks from 9 topics the null sits at ~0.51, so any
    fixed "low Jaccard = divergence" threshold below that is measuring nothing.
    Returns (mean, p05, p95).
    """
    import random
    import statistics

    rng = random.Random(7)  # fixed seed: the null must not move between runs
    means = []
    for _ in range(trials):
        sets = [set(rng.sample(range(len(TOPIC_VOCAB)), N_QUESTIONS)) for _ in range(n_personas)]
        means.append(statistics.mean(_jaccard(a, b) for a, b in combinations(sets, 2)))
    means.sort()
    return statistics.mean(means), means[int(0.05 * len(means))], means[int(0.95 * len(means))]


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _content_words(questions: list) -> set:
    words = set()
    for q in questions:
        for w in re.findall(r"[a-z]+", str(q.get("question", "")).lower()):
            if w not in _STOP and len(w) > 2:
                words.add(w)
    return words


def main():
    global MODEL
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    payload_path = Path(sys.argv[1])
    raw = json.loads(payload_path.read_text(encoding="utf-8"))
    da = raw.get("result", raw)
    council_mode = sys.argv[2] if len(sys.argv) > 2 else "diverse"
    if len(sys.argv) > 3:
        MODEL = sys.argv[3]
    print(f"MODEL={MODEL}  (effort held at medium)\n")

    # --- resolve the council under test -----------------------------------
    if council_mode == "mbb":
        personas = list(MBB_PERSONAS)
        print(f"COUNCIL: MBB (hardcoded) -> {personas}\n")
    elif council_mode == "famous":
        personas = list(FAMOUS_PERSONAS)
        print("=" * 78)
        print("COUNCIL: famous operators (control arm — not registry personas)")
        print("=" * 78)
        for p in personas:
            print(f"  {p:10} {FAMOUS_PROFILES[p].splitlines()[0]}")
        print()
    else:
        recs = _resolve_diverse_council(da)
        print("=" * 78)
        print("COUNCIL: diverse, resolved by DA's own _recommend_diverse_council")
        print("=" * 78)
        for r in recs:
            print(f"  {r['category']:12} {r['persona_id']:16} {r['persona_name']:26} {r.get('rationale','')}")
        personas = [r["persona_id"] for r in recs]
        dupes = [p for p in set(personas) if personas.count(p) > 1]
        if dupes:
            print(f"\n  !! DUPLICATE SEAT(S): {dupes} — a firm holds more than one seat;")
            print("     the council is smaller than its slot count suggests.")
        personas = list(dict.fromkeys(personas))  # de-dup for the probe itself
        print(f"\n  distinct personas probed: {personas}\n")

    kt = _kt_summary(da)
    print("=" * 78)
    print("KT SUMMARY GIVEN TO EVERY PERSONA (identical input)")
    print("=" * 78)
    print(kt[:1200])
    print()

    profiles = dict(FAMOUS_PROFILES) if council_mode == "famous" else _persona_profiles(personas)
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    results, tok_in, tok_out = {}, 0, 0
    for pid in personas:
        qs, ti, to = _ask(client, pid, profiles[pid], kt, famous=(council_mode == "famous"))
        results[pid] = qs
        tok_in += ti
        tok_out += to
        print("=" * 78)
        print(f"{pid.upper()}  ({len(qs)} questions)")
        print("=" * 78)
        for q in qs:
            print(f"  [{q.get('topic','?'):28}] {q.get('question','')}")
        print()

    # --- deterministic comparison -----------------------------------------
    topic_sets = {p: {q.get("topic") for q in qs} for p, qs in results.items()}
    word_sets = {p: _content_words(qs) for p, qs in results.items()}

    print("=" * 78)
    print("DIVERGENCE (deterministic — no LLM judge)")
    print("=" * 78)
    print(f"{'pair':22} {'topic Jaccard':>14} {'lexical Jaccard':>16}")
    t_scores, l_scores = [], []
    for a, b in combinations(personas, 2):
        t = _jaccard(topic_sets[a], topic_sets[b])
        l = _jaccard(word_sets[a], word_sets[b])
        t_scores.append(t)
        l_scores.append(l)
        print(f"{a+' vs '+b:22} {t:14.2f} {l:16.2f}")

    t_mean = sum(t_scores) / len(t_scores)
    l_mean = sum(l_scores) / len(l_scores)
    print(f"{'MEAN':22} {t_mean:14.2f} {l_mean:16.2f}")
    print()
    for p in personas:
        print(f"  {p:10} topics: {sorted(x for x in topic_sets[p] if x)}")
    print()

    # --- compare against the NULL, not an arbitrary threshold --------------
    # Asking for N_QUESTIONS picks from a fixed topic vocabulary means even a
    # random tagger produces substantial Jaccard spread. The first version of
    # this gate used a flat "<= 0.70 means diverge" rule, which is BELOW the
    # random baseline — it would have called chance divergence, and did.
    # Divergence requires scoring BELOW what random tagging produces.
    null_mean, null_p05, null_p95 = _random_tagger_baseline(len(personas))
    print(f"\nRANDOM-TAGGER NULL (same {N_QUESTIONS}-of-{len(TOPIC_VOCAB)} choice):")
    print(f"  mean {null_mean:.3f}   90% range {null_p05:.3f}-{null_p95:.3f}")

    diverges = t_mean < null_p05
    if t_mean > null_p95:
        verdict = "CONVERGE (significantly more aligned than chance) -> stop; close Stage I at B-2"
    elif diverges:
        verdict = "DIVERGE (more different than chance) -> B-4 justified"
    else:
        verdict = "NO EVIDENCE (indistinguishable from random tagging) -> stop; close Stage I at B-2"
    print("=" * 78)
    print(f"GATE: {verdict}")
    print("      Divergence means scoring BELOW the null. Scoring above it is")
    print("      evidence of convergence, not of divergence.")
    print(f"COST: {tok_in} in / {tok_out} out tokens across {len(personas)} {MODEL} calls")
    print("=" * 78)

    out = Path(__file__).parent / f"b3_results_{council_mode}_{MODEL}.json"
    out.write_text(json.dumps({
        "model": MODEL, "council_mode": council_mode, "personas": personas,
        "results": results,
        "topic_jaccard_mean": t_mean, "lexical_jaccard_mean": l_mean,
        "null_mean": null_mean, "null_p05": null_p05, "null_p95": null_p95,
        "verdict": verdict,
        "diverges": diverges, "tokens_in": tok_in, "tokens_out": tok_out,
    }, indent=2), encoding="utf-8")
    print(f"saved -> {out}")


main()
