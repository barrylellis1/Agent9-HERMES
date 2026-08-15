"""Stage I B-3 extension — how many perspectives does a council actually need?

THE QUESTION
------------
The B-3 gate found consulting personas converge (topic Jaccard 0.60-0.67 against
a 0.51 random null) while four sharply-opposed operators reached the null and
asked visibly different things. Topic-tag Jaccard could not see that difference:
four people asking about blending tanks, volume retention, target mechanisms and
approval authority all tag `hypothesis_validation`.

So this asks a better question with a better instrument: assemble 20 minds whose
METHODS genuinely differ, let each ask one opening question plus one follow-up,
and measure how quickly the council stops learning anything new.

DESIGN NOTE — why blind, not a shared queue
-------------------------------------------
Each persona is asked independently and cannot see the others. A shared queue
("here is what has been asked; add what is missing") is the B-4 mechanic, but as
a measurement it is stacked: a persona told not to repeat will produce something
new regardless of who it is. That measures instruction-following, not
perspective. Blind is the only version where the persona is doing the work.

INSTRUMENT
----------
1. Saturation curve — over many random orderings, how much NEW content does the
   k-th persona add? Deterministic, no LLM judge, order-independent by averaging.
   This is the headline: it sizes the council.
2. Unique contribution — content words a persona is alone in raising. Identifies
   who brings something nobody else does.
3. Topic Jaccard vs the random-tagger null — carried over for continuity with the
   earlier arms, and reported knowing it is the least sensitive of the three.

Usage:
    python tools/ab_harness/b3_discovery_round.py <path-to-da-payload.json>
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

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO / ".env")

import anthropic  # noqa: E402

MODEL = "claude-sonnet-5"  # overridable per run; see __main__ — ONE variable at a time
EFFORT = "medium"          # held constant across models: changing both confounds them

# BARE mode strips the authored method description and prompts with the NAME ONLY.
# This is the circularity control: the profiles below were written by the same
# person analysing the results, so differentiation found WITH them is partly
# authored rather than discovered. If divergence survives on name alone, it lives
# in the model's knowledge of these people rather than in the prompt.
BARE = False

TOPIC_VOCAB = [
    "hypothesis_validation", "scope_boundaries", "external_context",
    "constraints", "success_criteria", "replication_potential",
    "tradeoff_tolerance", "segment_specific_causation", "comparison_baseline",
]

# 20 methods, chosen for spread of DIAGNOSTIC STANCE rather than fame — and
# weighted toward stances that could plausibly bite on a margin problem.
# Each carries a known bias: a persona without one is a hagiography, and
# hagiographies all sound the same.
MINDS = {
    "buffett": "Warren Buffett — pricing power is the whole test; a business that cannot raise price has no moat. Owner earnings, return on incremental capital. Bias: reaches for price before cost; may write off a fixable operation as a poor business.",
    "munger": "Charlie Munger — invert, always invert: ask what would guarantee this margin never recovers, then check whether we are doing it. Checklists, multiple mental models, incentive analysis. Bias: sceptical to the point of inaction; assumes stupidity or bad incentives before bad luck.",
    "bezos": "Jeff Bezos — margin is an output metric nobody can act on; find the controllable inputs that produce it. Working backwards from the customer, one-way vs two-way doors. Bias: tolerant of thin margin if it buys share; treats margin defence as short-term thinking.",
    "musk": "Elon Musk — reduce the product to its raw-material cost floor; the ratio of actual to floor is the only number. Question every requirement and who set it. Bias: treats contracts and org constraints as requirements to challenge rather than facts.",
    "ohno": "Taiichi Ohno — a number in a report is not a cause; go and see the operation. Five whys to root cause. Cost falls by removing waste, never by raising price. Bias: distrusts any diagnosis made away from the workplace; patient where speed may be needed.",
    "deming": "W. Edwards Deming — distinguish common-cause variation from special cause; reacting to noise as if it were signal makes things worse. 94% of problems are the system, not the people. Bias: demands statistical control before any action; hostile to targets set without method.",
    "porter": "Michael Porter — is this a firm problem or an industry problem? Five forces, supplier and buyer power, rivalry. A margin decline across a whole industry is structure, not execution. Bias: sees structure everywhere; slow to credit operational fixes.",
    "christensen": "Clayton Christensen — is a low-end entrant taking the segment we are least willing to defend, exactly as theory predicts? Jobs to be done, disruption, resource-allocation drift. Bias: reads every share loss as disruption; can over-fit the pattern.",
    "drucker": "Peter Drucker — what is this business, who is the customer, and what does the customer actually value? The most dangerous answer is one to the wrong question. Bias: reframes rather than solves; may reopen settled scope.",
    "grove": "Andy Grove — is this a 10X change, a strategic inflection point, or ordinary noise? Only the paranoid survive; middle managers see inflections first. Bias: escalates blips into inflections; bias toward drastic response.",
    "rockefeller": "John D. Rockefeller — know the unit cost of every step to the fraction of a cent, and control the inputs you depend on. Refining margin is won on cost accounting and integration. Bias: reflexively vertically integrates; ruthless on competitors.",
    "carnegie": "Andrew Carnegie — watch the costs and the profits take care of themselves; cost accounting per unit per process, always. Bias: cost-obsessed to the exclusion of demand and brand.",
    "walton": "Sam Walton — everyday low cost precedes everyday low price; buying power and shrink are where margin actually lives. Bias: assumes scale solves it; underweights premium and mix.",
    "kamprad": "Ingvar Kamprad — design the cost out at the drawing board; the price tag comes first and the product is designed to meet it. Bias: solves through redesign, which is slow; indifferent to short-term reporting pressure.",
    "arnault": "Bernard Arnault — never discount; desirability is the asset and a price cut spends it permanently. Scarcity and brand over volume. Bias: assumes premium positioning is available; dismissive of value segments.",
    "dell": "Michael Dell — margin is a working-capital and inventory question; build to order, negative cash conversion cycle, obsolete stock is a margin leak. Bias: sees supply chain in everything; underweights pricing and brand.",
    "kelleher": "Herb Kelleher — cost structure IS the strategy, not a consequence of it; a low-cost position is defended by simplicity and culture. Bias: resists complexity even where it earns; culture as universal answer.",
    "dalio": "Ray Dalio — diagnose to root cause before designing anything, and write the diagnosis down as a principle so the same failure is caught next time. Pain plus reflection equals progress. Bias: systematises prematurely; process-heavy for urgent problems.",
    "levitt": "Theodore Levitt — marketing myopia: firms define their business by the product rather than the need, then miss the substitution that eats them. Bias: reframes to category level; can miss a mundane operational cause.",
    "sloan": "Alfred Sloan — a product for every purse and purpose; margin lives in the ladder and in not letting the rungs cannibalise each other. Bias: solves through segmentation and structure; slow-moving, committee-driven.",
}

_STOP = set("""
a an the and or but if is are was were be been being of to in on at for with by from as that this these those it its
we you they i do does did what which who whom how why when where should would could can may might will shall about
into over under than then there their our your his her not no any all some each per vs versus given have has had
been more most less least much many other another same such only own than too very s t don now d ll m o re ve y
margin margins gross product products line lines decline declined declining point points percentage percent
question questions ask asking answer business company
""".split())


def _content_words(texts) -> set:
    out = set()
    for t in texts:
        for w in re.findall(r"[a-z]+", str(t).lower()):
            if w not in _STOP and len(w) > 3:
                out.add(w)
    return out


def _jaccard(a: set, b: set) -> float:
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def _kt_summary(da_payload: dict) -> str:
    from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
    return A9_Deep_Analysis_Agent({})._build_kt_summary(da_payload)


def _ask(client, pid: str, profile: str, kt: str):
    if BARE:
        # Name only. No method, no frameworks, no stated bias — nothing authored.
        name = profile.split(" — ")[0]
        method_block = f"## THE THINKER\n{name}\n"
        preamble = (
            f"Reason in the documented style of the business thinker named below, applying "
            f"the method and priorities they are known for. Do not roleplay or write in "
            f"first person as them — produce the enquiry their method implies.\n\n"
        )
    else:
        method_block = f"## THE METHOD YOU ARE APPLYING\n{profile}\n"
        preamble = (
            f"Reason in the documented style of this business thinker, applying the method and "
            f"priorities below. Do not roleplay or write in first person as them — produce the "
            f"enquiry their method implies.\n\n"
        )
    system = (
        preamble
        + method_block + "\n"
        "## THE ANALYSIS (already complete — do not ask for more of this data)\n"
        f"{kt}\n\n"
        "## YOUR TASK\n"
        "You get ONE opening question to the CFO, and ONE follow-up or comment after it. "
        "That is your entire turn in a discovery round, so spend it on what only this method "
        "would think to ask. Ask what only the executive can answer — the data above is known.\n\n"
        "Tag each with the single best-fitting topic from:\n" + ", ".join(TOPIC_VOCAB) + "\n\n"
        '## OUTPUT (JSON only)\n'
        '{"opening": {"question": "<one question>", "topic": "<topic>"}, '
        '"followup": {"question": "<follow-up or comment>", "topic": "<topic>"}}'
    )
    kwargs = dict(
        model=MODEL, max_tokens=700,
        output_config={"effort": EFFORT},
        system=system,
        messages=[{"role": "user", "content": "Return ONLY the JSON object."}],
    )
    if MODEL.startswith("claude-fable"):
        # Fable's classifiers can decline a request; server-side fallbacks re-run
        # it on the recommended model rather than handing back a refusal.
        r = client.beta.messages.create(
            betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs
        )
    else:
        r = client.messages.create(**kwargs)

    # A refusal is HTTP 200 with empty/partial content — check before reading.
    if r.stop_reason == "refusal":
        cat = getattr(getattr(r, "stop_details", None), "category", None)
        raise SystemExit(f"{pid}: refused (category={cat!r}) — discard this arm")

    # Never index content[0] blindly: thinking is on by default on both models
    # with display="omitted", so the first block is often an empty ThinkingBlock.
    text = next((b.text for b in r.content if getattr(b, "type", None) == "text"), "")
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise SystemExit(f"{pid}: no JSON in response:\n{text[:300]}")
    d = json.loads(m.group())
    return d, r.usage.input_tokens, r.usage.output_tokens


def _saturation(word_sets: dict, trials: int = 2000):
    """Novel content contributed by the k-th persona, averaged over orderings."""
    ids = list(word_sets)
    rng = random.Random(11)
    by_pos = [[] for _ in ids]
    for _ in range(trials):
        rng.shuffle(ids)
        seen: set = set()
        for k, pid in enumerate(ids):
            new = word_sets[pid] - seen
            by_pos[k].append(len(new))
            seen |= word_sets[pid]
    return [statistics.mean(x) for x in by_pos]


def main():
    global MODEL, BARE
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if len(sys.argv) > 2:
        MODEL = sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3] == "bare":
        BARE = True
    mode = "NAME ONLY (circularity control)" if BARE else "authored method profiles"
    print(f"MODEL={MODEL}  EFFORT={EFFORT}  PROMPT={mode}\n")
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    da = raw.get("result", raw)
    kt = _kt_summary(da)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    results, tok_in, tok_out = {}, 0, 0
    for pid, profile in MINDS.items():
        d, ti, to = _ask(client, pid, profile, kt)
        results[pid] = d
        tok_in += ti
        tok_out += to
        print(f"[{pid}]")
        print(f"   Q  ({d['opening'].get('topic','?')}): {d['opening'].get('question','')}")
        print(f"   ++ ({d['followup'].get('topic','?')}): {d['followup'].get('question','')}")

    word_sets = {
        pid: _content_words([d["opening"].get("question", ""), d["followup"].get("question", "")])
        for pid, d in results.items()
    }
    topic_sets = {
        pid: {d["opening"].get("topic"), d["followup"].get("topic")}
        for pid, d in results.items()
    }

    # --- saturation ------------------------------------------------------
    curve = _saturation(word_sets)
    total = len(set().union(*word_sets.values()))
    print("\n" + "=" * 78)
    print("SATURATION — novel content contributed by the k-th persona")
    print("(averaged over 2000 random orderings; order-independent)")
    print("=" * 78)
    cum = 0.0
    for k, v in enumerate(curve, 1):
        cum += v
        bar = "#" * int(v)
        print(f"  persona {k:2}: +{v:5.1f} new terms   ({cum/total:5.1%} of total coverage)  {bar}")

    # --- unique contribution --------------------------------------------
    print("\n" + "=" * 78)
    print("UNIQUE CONTRIBUTION — terms this mind alone raised")
    print("=" * 78)
    uniq = {}
    for pid, ws in word_sets.items():
        others = set().union(*(w for p, w in word_sets.items() if p != pid))
        uniq[pid] = sorted(ws - others)
    for pid, u in sorted(uniq.items(), key=lambda kv: -len(kv[1])):
        print(f"  {pid:12} {len(u):3}  {', '.join(u[:10])}")

    # --- topic Jaccard vs null (continuity with earlier arms) ------------
    pair_t = [_jaccard(topic_sets[a], topic_sets[b]) for a, b in combinations(topic_sets, 2)]
    pair_l = [_jaccard(word_sets[a], word_sets[b]) for a, b in combinations(word_sets, 2)]
    print("\n" + "=" * 78)
    print(f"topic Jaccard mean   : {statistics.mean(pair_t):.3f}  (2 tags from {len(TOPIC_VOCAB)})")
    print(f"lexical Jaccard mean : {statistics.mean(pair_l):.3f}")
    print(f"total distinct terms : {total}")
    print(f"COST: {tok_in} in / {tok_out} out across {len(MINDS)} {MODEL} calls")
    print("=" * 78)

    out = Path(__file__).parent / f"b3_discovery_round_{MODEL}{'_bare' if BARE else ''}.json"
    out.write_text(json.dumps({
        "model": MODEL, "effort": EFFORT, "bare": BARE, "results": results,
        "saturation_curve": curve, "total_terms": total,
        "unique_contribution": {k: v for k, v in uniq.items()},
        "topic_jaccard_mean": statistics.mean(pair_t),
        "lexical_jaccard_mean": statistics.mean(pair_l),
        "tokens_in": tok_in, "tokens_out": tok_out,
    }, indent=2), encoding="utf-8")
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
