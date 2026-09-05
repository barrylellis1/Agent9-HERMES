#!/usr/bin/env python
"""
Phase 22 Stage D — does lens-probing actually increase Stage 1 diversity?

Stages A-C built the mechanism (a real coverage gap, a real architectural
fix, a real UI). This is the step that turns "this should work" into "this
measurably worked" — everything upstream is a hypothesis about mechanism
until this confirms the number moved.

WHAT IS MEASURED, AND WHY IT ISN'T A REPLAY OF THE 2026-09-04 BAKE-OFF
-----------------------------------------------------------------------
That bake-off held Stage 1 FROZEN and compared SYNTHESIS models. This
measures the opposite half: does giving Stage 1 itself lens-differentiated
input change what it produces. Measured directly on Stage 1's own three
`proposed_option` titles via classify_lever — no synthesis call needed,
because classify_lever doesn't care where a title came from, and Stage 1's
own diversity is exactly the thing Stage B/C changed.

CORRECTION, FOUND DURING THIS SCRIPT'S OWN PILOT (2026-09-05): baseline was
originally run at N=1 on the theory that Stage 1's temperature=0.0
("ensures identical inputs always produce the same hypothesis" —
a9_solution_finder_agent.py's own comment) makes repeated baseline runs
redundant. Two independent baseline calls with byte-identical input
produced DIFFERENT titles and different distinct-family counts (2 vs 3).
temperature=0 does not guarantee bit-identical output in practice for most
hosted LLM APIs — batching and non-associative floating-point summation on
the serving side are well-documented causes, independent of anything in
this codebase. The comment's claim does not hold empirically; trust the
measurement, not the comment. Baseline now runs at the SAME N as the
with-lens arm so both sides get a real distribution, not a single
point compared against ten.

WHY THE "WITH LENS" ARM VARIES ACROSS N RUNS
----------------------------------------------
The lens-probe QUESTIONS are also deterministic (same temperature=0.0 path)
— they'd be identical every run too. What varies, and is the actual
independent variable here, is the ANSWER to each question. No live
executive exists to answer them in an automated harness, so a SEPARATE,
explicitly-labeled simulation model answers on their behalf (higher
temperature, so each run gets a genuinely different plausible answer set).

THIS IS A REAL, NAMED LIMITATION, NOT GLOSSED OVER: these are simulated
answers, not real executive input. This experiment can show whether
DIFFERENT plausible lens-shaped input causes Stage 1 to diversify — it
CANNOT show whether real executives would answer usefully, whether they'd
bother answering at all, or whether the questions themselves are ones a
real principal would find sensible. That is a live-usage question, not a
harness question, and no simulation substitutes for it.

CORRECTION #2 (2026-09-05, on direct instruction): the first run's
simulated-executive prompt used a 3-line recap (kt_is_is_not.what_is only),
missing 4 of the fixture's 5 segment-level change_points — exactly the
detail the lens-probe questions themselves ask about. A hedging answer from
a simulator that was never given the numbers to answer confidently is not
informative about lens-probing. Fixed once by matching a real persona's own
compact recap (a9_solution_finder_agent.py's dataset_recap_lines), then
fixed again, further: the simulator now receives the COMPLETE DA execution
output, not a recap of any size. A persona's own prompt stays compact for
token economy; nothing requires the SIMULATED EXECUTIVE to be similarly
constrained, and removing the information ceiling entirely is a cleaner
test than narrowing it. If diversity still doesn't improve when the
simulator has every fact DA produced, that is a materially stronger
negative result than "under-provisioned" could ever be.

USAGE
-----
    python scripts/run_lens_probe_validation.py \
        --fixture decision-studio-ui/scratchpad/dq_comparison/lens_run \
        --personas commercial,operational,structural \
        --n 10 --out scratchpad/lens_probe_validation
"""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logger = logging.getLogger("lens_probe_validation")

# $ per 1M (input, output). All calls here are cheap-tier (Haiku), so this
# run costs well under $1 even at N=10 -- no synthesis calls at all.
PRICE = {"claude-haiku-4-5-20251001": (1.0, 5.0), "claude-sonnet-5": (2.0, 10.0)}


async def _connect(agent: object, orchestrator) -> None:
    fn = getattr(agent, "connect", None)
    if not callable(fn):
        return
    try:
        res = fn(orchestrator)
    except TypeError:
        res = fn()
    if inspect.isawaitable(res):
        await res


async def bootstrap():
    """Same minimal agent set as run_dq_bakeoff.py's bootstrap() -- no DA, no
    DPA, no data access; the DA payload is frozen and nothing here queries a
    warehouse."""
    from src.registry.bootstrap import RegistryBootstrap
    from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, initialize_agent_registry

    await RegistryBootstrap.initialize()
    factory = RegistryBootstrap._factory
    orchestrator = await A9_Orchestrator_Agent.create({})
    await orchestrator.connect()
    await initialize_agent_registry()

    base = {"orchestrator": orchestrator, "registry_factory": factory}
    for name in ("A9_Data_Governance_Agent", "A9_Principal_Context_Agent"):
        agent = await orchestrator.create_agent_with_dependencies(name, dict(base))
        await _connect(agent, orchestrator)

    sf = await orchestrator.create_agent_with_dependencies(
        "A9_Solution_Finder_Agent",
        {"orchestrator": orchestrator, "registry_factory": factory,
         "enable_llm_debate": True, "enable_hybrid_council": True},
    )
    if getattr(sf, "orchestrator", None) is None:
        await sf.connect(orchestrator)

    return orchestrator, factory, sf


async def make_llm_agent(provider: str = "anthropic"):
    from src.agents.agent_config_models import A9_LLM_Service_Agent_Config
    from src.agents.new.a9_llm_service_agent import A9_LLM_Service_Agent

    cfg = A9_LLM_Service_Agent_Config(provider=provider, task_type="nlp_parsing")
    return await A9_LLM_Service_Agent.create(cfg.model_dump())


def load_fixture(path: Path) -> Dict[str, Any]:
    da_file = path / "da-payload.json"
    raw = json.loads(da_file.read_text(encoding="utf-8"))
    da = raw.get("execution")
    if not isinstance(da, dict):
        raise SystemExit(f"{da_file} has no 'execution' block")
    return da


async def run_sf(sf, da: Dict[str, Any], stage: str, personas: List[str],
                 lens_refinement: Optional[Dict[str, str]], client_id: str, principal_id: str):
    from src.agents.models.solution_finder_models import SolutionFinderRequest

    prefs: Dict[str, Any] = {"debate_stage": stage, "consulting_personas": personas}
    if lens_refinement:
        prefs["lens_refinement"] = lens_refinement

    req = SolutionFinderRequest(
        request_id=f"lpv-{stage}-{int(time.time()*1000)}", principal_id=principal_id,
        deep_analysis_output=da, client_id=client_id, preferences=prefs,
    )
    return await sf.recommend_actions(req)


def extract_proposed_options(resp) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
    """{persona_id: (title, description)} from a stage1_only response.

    Confirmed live (2026-09-05) that stage1_only's own early-return path
    keeps proposed_option intact on stage_1_hypotheses -- the later
    unconditional stripping block (which removes it for the synthesis
    response shape) does not run on this path. Read directly rather than
    positionally from options_ranked, since this is keyed by persona id
    explicitly.
    """
    out: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
    for pid, hyp in (resp.stage_1_hypotheses or {}).items():
        po = (hyp or {}).get("proposed_option") or {}
        out[pid] = (po.get("title"), po.get("description"))
    return out


def classify_all(options: Dict[str, Tuple[Optional[str], Optional[str]]]) -> Dict[str, Any]:
    from src.analysis.mechanism import classify_lever, UNCLASSIFIED

    families: Dict[str, str] = {}
    for pid, (title, desc) in options.items():
        fam, _ = classify_lever(title, desc)
        families[pid] = fam
    distinct = len({f for f in families.values() if f != UNCLASSIFIED})
    return {"families": families, "distinct": distinct,
            "titles": {pid: t for pid, (t, _) in options.items()}}


async def generate_simulated_answers(llm_agent, questions: Dict[str, str],
                                     da_full: Dict[str, Any], temperature: float) -> Dict[str, str]:
    """ONE combined call, all personas at once -- cheaper than N separate
    calls, and the simulation model sees all three questions together so it
    doesn't need to be told the questions are related.

    Explicitly and unavoidably a SIMULATION: temperature > 0 so each
    invocation produces a different plausible answer set, which is the
    actual independent variable this experiment varies. Never presented
    anywhere in this script's output as a real executive's input.

    CORRECTION (2026-09-05, second pass): the first correction reused
    a9_solution_finder_agent.py's own dataset_recap_lines-equivalent (top-3
    change points), matching what a real Stage 1 persona sees. Changed again
    on direct instruction: pass the COMPLETE DA execution output, not a
    recap of any size -- removing the information-deficit question entirely
    rather than narrowing it. A persona's own prompt is deliberately compact
    for token economy; a SIMULATED EXECUTIVE has no such constraint, and if
    it still hedges or Stage 1 still fails to diversify with every fact DA
    produced in hand, that is a materially stronger negative signal than
    "hedged because under-provisioned" could ever be -- and if diversity
    DOES improve given full information, that marks the recap's compactness,
    not the lens-probing mechanism itself, as the actual constraint.

    Uses .analyze() + A9_LLM_AnalysisRequest, not the plain .generate() path
    -- the same JSON-out pattern _run_stage1 and _generate_lens_probe both
    use server-side, rather than a raw-text call this script would have to
    parse itself (tried first; a raw .generate() call returned free text
    that failed json.loads outright).
    """
    from src.agents.new.a9_llm_service_agent import A9_LLM_AnalysisRequest

    q_block = "\n".join(f'- ({pid}) {q}' for pid, q in questions.items())
    prompt = (
        "You are simulating a well-informed CFO answering quick clarifying "
        "questions from three advisors. Below is the COMPLETE Deep Analysis "
        "output your team produced -- use any relevant fact in it, at any "
        "level of detail. Keep each answer to one or two sentences, grounded "
        "in the data -- do not invent numbers not present in it.\n\n"
        f"## COMPLETE DEEP ANALYSIS OUTPUT\n{json.dumps(da_full, indent=2, default=str)}\n\n"
        f"## QUESTIONS\n{q_block}\n\n"
        '## OUTPUT (JSON only): {"<persona_id>": "<one-to-two-sentence answer>", ...}'
    )
    # Retried, not raised on the first failure: a 10-run sweep makes ~20 LLM
    # calls, and this project's own multi-run scripts (run_dq_bakeoff.py) all
    # treat one transient call failure as a per-run event to log and continue
    # past, never a reason to abort the whole sweep. Found the hard way: an
    # unretried first version of this function crashed an N=10 run at run 7
    # on a single transient "[SF] LLM call failed: unknown error" -- the
    # exact class of intermittent failure this codebase's other harnesses
    # already treat as routine, not exceptional.
    last_err: Optional[Exception] = None
    for attempt in range(3):
        req = A9_LLM_AnalysisRequest(
            request_id=f"lpv-simanswer-{int(time.time()*1000)}-{attempt}", principal_id="cfo_001",
            content=prompt, analysis_type="custom", context="", temperature=temperature,
        )
        resp = await llm_agent.analyze(req)
        if resp.status == "success" and isinstance(resp.analysis, dict):
            return {pid: str(a) for pid, a in resp.analysis.items() if pid in questions}
        last_err = RuntimeError(f"status={resp.status} analysis_type={type(resp.analysis).__name__}")
        if attempt < 2:
            await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"simulated-answer generation failed after 3 attempts: {last_err}")


async def main_async(args) -> int:
    fixture = Path(args.fixture)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    personas = [p.strip() for p in args.personas.split(",") if p.strip()]

    da = load_fixture(fixture)
    print(f"fixture  : {fixture}  (KPI={da.get('plan', {}).get('kpi_name')!r})")
    print(f"personas : {personas}")
    print(f"n        : {args.n} runs per arm (baseline included -- see this script's "
          f"module docstring: temperature=0.0 was found NOT to be reproducible in "
          f"practice, so both arms need a real distribution, not one point vs ten)")

    orchestrator, factory, sf = await bootstrap()
    llm_agent = await make_llm_agent("anthropic")

    # ---- Baseline: today's behavior, no lens_refinement, run N times ----
    # (originally N=1 on a determinism assumption this script's own pilot
    # disproved -- see module docstring)
    print(f"\n=== baseline (no lens_refinement, {args.n} runs) ===")
    baseline_runs: List[Dict[str, Any]] = []
    for i in range(1, args.n + 1):
        resp = await run_sf(sf, da, "stage1_only", personas, None,
                            args.client_id, args.principal_id)
        options = extract_proposed_options(resp)
        scored = classify_all(options)
        baseline_runs.append({"run": i, **scored})
        print(f"  run {i:02d}: distinct={scored['distinct']}  "
              f"families={list(scored['families'].values())}")
    baseline_distinct_counts = [r["distinct"] for r in baseline_runs]

    # ---- Lens probe: generate the real questions once (also deterministic) ----
    print("\n=== lens_probe questions (generated once, deterministic) ===")
    probe_resp = await run_sf(sf, da, "lens_probe", personas, None,
                              args.client_id, args.principal_id)
    questions = probe_resp.lens_probe_questions or {}
    if not questions:
        print("  FAILED: no lens_probe_questions returned.", file=sys.stderr)
        return 1
    for pid, q in questions.items():
        print(f"  {pid:<12} {q}")

    # The simulated executive sees the COMPLETE DA execution output, not a
    # recap -- see generate_simulated_answers()'s own docstring for the two
    # corrections that led here (first: a 3-line recap missing 4 of 5
    # segment-level change_points; second, on direct instruction: pass
    # everything DA produced, removing the information-deficit question
    # entirely rather than narrowing it). Both prior results are retained in
    # lens_probe_validation_2026-09-05/ for the record.

    manifest: Dict[str, Any] = {
        "fixture": str(fixture), "personas": personas, "n": args.n,
        "baseline_runs": baseline_runs,
        "lens_probe_questions": questions,
        "with_lens_runs": [],
        "caveat": (
            "with_lens answers are SIMULATED (a separate LLM, not a real "
            "executive) -- this measures whether varying plausible lens-shaped "
            "input changes Stage 1 output, not whether real executives would "
            "answer usefully or at all. Baseline runs N times, not once -- "
            "temperature=0.0 was found not to be reproducible in practice. "
            "See this script's own module docstring for both caveats."
        ),
    }

    # ---- With-lens: N runs, each with a fresh simulated answer set ----
    print(f"\n=== with lens_refinement ({args.n} runs, simulated answers) ===")
    distinct_counts: List[int] = []
    for i in range(1, args.n + 1):
        answers = await generate_simulated_answers(llm_agent, questions, da, temperature=0.8)
        resp = await run_sf(sf, da, "stage1_only", personas, answers,
                            args.client_id, args.principal_id)
        options = extract_proposed_options(resp)
        scored = classify_all(options)
        distinct_counts.append(scored["distinct"])
        manifest["with_lens_runs"].append({
            "run": i, "answers": answers,
            "families": scored["families"], "distinct": scored["distinct"],
            "titles": scored["titles"],
        })
        print(f"  run {i:02d}: distinct={scored['distinct']}  "
              f"families={list(scored['families'].values())}")

    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    import statistics as st

    print(f"\n{'='*70}")
    print(f"baseline  distinct families : mean={st.mean(baseline_distinct_counts):.2f}  "
          f"min={min(baseline_distinct_counts)}  max={max(baseline_distinct_counts)}  (N={args.n})")
    print(f"with-lens distinct families : mean={st.mean(distinct_counts):.2f}  "
          f"min={min(distinct_counts)}  max={max(distinct_counts)}  (N={args.n})")

    # Unpaired comparison (the two arms are independent draws, not matched
    # pairs -- with-lens varies the simulated answer, baseline varies only
    # whatever makes temperature=0 non-reproducible in practice, an
    # unrelated and uncontrolled source of variance). Sign-test-style count
    # against the pooled baseline mean is a coarse but honest summary; this
    # is NOT the matched-pairs design the 2026-09-04 bake-off used, and
    # shouldn't be read with the same statistical weight.
    baseline_mean = st.mean(baseline_distinct_counts)
    higher = sum(1 for c in distinct_counts if c > baseline_mean)
    lower = sum(1 for c in distinct_counts if c < baseline_mean)
    print(f"with-lens runs above the baseline mean : {higher}/{args.n}")
    print(f"with-lens runs below the baseline mean : {lower}/{args.n}")
    print(f"manifest: {out / 'manifest.json'}")
    print(f"\nCAVEAT: with-lens answers are simulated, not real executive input. "
          f"See the module docstring before treating this as a live-usage result.")
    return 0


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fixture", required=True)
    p.add_argument("--personas", default="commercial,operational,structural")
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--out", required=True)
    p.add_argument("--client-id", default="lubricants")
    p.add_argument("--principal-id", default="cfo_001")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv[1:])
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
