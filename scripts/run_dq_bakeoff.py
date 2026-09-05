#!/usr/bin/env python
"""
Decision Quality model bake-off runner.

Replays a frozen Deep Analysis payload through Solution Finder N times per model
arm and writes each result in the layout `scripts/score_dq_run.py` already reads,
so scoring needs no new code.

WHAT IS HELD CONSTANT, AND WHY IT MATTERS
-----------------------------------------
The DA payload is frozen (one capture, replayed byte-identical) and Stage 1 runs
ONCE on Anthropic; its hypotheses are then replayed into every run of every arm
via `preferences.prior_stage1_hypotheses`, which SF honours by skipping the three
persona calls entirely (a9_solution_finder_agent.py, `_skip_stage1`). So the
synthesis-stage input is identical across arms and the model is the only variable.

What an "arm" honestly covers: the critic pass runs during the synthesis stage and
resolves through the same LLM service agent, so it moves with the arm's PROVIDER.
An arm is therefore "frozen Stage 1, then critic + synthesis on this provider",
not "synthesis only". The manifest records the served model for every call so this
is visible in the data rather than assumed.

WHY N MATTERS
-------------
These models reject `temperature=0` — output is stochastic and cannot be pinned.
Compare distributions, never single runs. N>=10 per arm is the floor.

COST
----
A real synthesis call is ~20K in / ~23K out, an order of magnitude past a toy
prompt. At astra/Fable rates ($10/$50 per 1M) that is ~$1.40+ per run, so a
10-run arm is ~$15. `--max-spend` aborts mid-sweep rather than discovering this
from a bill; `--dry-run` stops after the Stage 1 freeze and prints the estimate.

USAGE
-----
    python scripts/run_dq_bakeoff.py \
        --fixture decision-studio-ui/scratchpad/dq_comparison/lens_run \
        --arm fable:anthropic:claude-fable-5 \
        --arm astra:openai:gpt-6-astra \
        --n 10 --effort medium --max-spend 20 \
        --out scratchpad/bakeoff

Then score:
    python scripts/score_dq_run.py scratchpad/bakeoff/fable/run_01 ...
"""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

logger = logging.getLogger("bakeoff")

# $ per 1M (input, output). Reasoning/thinking tokens bill as output on both sides.
PRICING: Dict[str, Tuple[float, float]] = {
    "claude-fable-5": (10.0, 50.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "gpt-6-astra": (10.0, 50.0),
    "gpt-5.6-sol": (5.0, 30.0),
    "gpt-5.6-terra": (2.5, 15.0),
    "gpt-5.6-luna": (1.0, 6.0),
    "gpt-4-turbo": (10.0, 30.0),
}

# Per-task env override consulted by each provider's routing table.
SYNTHESIS_ENV = {"anthropic": "CLAUDE_MODEL_SYNTHESIS", "openai": "OPENAI_MODEL_SYNTHESIS"}


class Arm:
    """name:provider:model — e.g. `fable:anthropic:claude-fable-5`."""

    def __init__(self, spec: str):
        parts = spec.split(":")
        if len(parts) != 3:
            raise ValueError(f"--arm must be name:provider:model, got {spec!r}")
        self.name, self.provider, self.model = parts
        if self.provider not in SYNTHESIS_ENV:
            raise ValueError(f"provider must be anthropic|openai, got {self.provider!r}")

    def __repr__(self) -> str:
        return f"{self.name} ({self.provider}/{self.model})"


def cost_of(rows: List[Dict[str, Any]]) -> float:
    """Cost from the SF token ledger, priced per row by the model that served it."""
    total = 0.0
    for r in rows:
        pi, po = PRICING.get(str(r.get("model")), (0.0, 0.0))
        total += ((r.get("input_tokens") or 0) * pi + (r.get("output_tokens") or 0) * po) / 1e6
    return total


def ledger_of(solutions: Dict[str, Any]) -> List[Dict[str, Any]]:
    for e in solutions.get("audit_log") or []:
        if isinstance(e, dict) and e.get("event") == "token_usage":
            return e.get("by_call") or []
    return []


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

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
    """Minimal agent set for a replayed synthesis: no DA, no DPA, no data access.

    Deliberately omits the Data Product Agent — the DA payload is frozen, so
    nothing here queries a warehouse, and configuring a DuckDB client in a script
    is a known trap.
    """
    from src.registry.bootstrap import RegistryBootstrap
    from src.agents.new.a9_orchestrator_agent import (
        A9_Orchestrator_Agent,
        initialize_agent_registry,
    )

    await RegistryBootstrap.initialize()
    factory = RegistryBootstrap._factory

    orchestrator = await A9_Orchestrator_Agent.create({})
    await orchestrator.connect()
    await initialize_agent_registry()

    base = {"orchestrator": orchestrator, "registry_factory": factory}
    agents: Dict[str, Any] = {}
    for name in ("A9_Data_Governance_Agent", "A9_Principal_Context_Agent"):
        agent = await orchestrator.create_agent_with_dependencies(name, dict(base))
        await _connect(agent, orchestrator)
        agents[name] = agent

    return orchestrator, factory


async def make_llm_agent(provider: str):
    """A provider-pinned LLM service agent. Provider is fixed at construction, so
    switching arms means swapping the instance, not mutating config."""
    from src.agents.agent_config_models import A9_LLM_Service_Agent_Config
    from src.agents.new.a9_llm_service_agent import A9_LLM_Service_Agent

    cfg = A9_LLM_Service_Agent_Config(provider=provider, task_type="synthesis")
    return await A9_LLM_Service_Agent.create(cfg.model_dump())


def _env_flag(name: str) -> bool:
    return os.getenv(name, "false").lower() == "true"


async def make_sf(orchestrator, factory):
    """Build SF with the SAME env-driven config the production path uses.

    A9_Solution_Finder_Agent_Config defaults every Phase 15/17 flag to False, and
    the live server sets them from SF_ENABLE_* env vars in
    a9_orchestrator_agent.py. A bare config therefore produces a materially
    DIFFERENT pipeline: no causal grounding, so no critic pass and no theory
    moderator (both gated on it), and an empty constraint set. The first pilot
    scored exactly that way — `causal_context`, `critic_pass_findings` and
    `moderator_grades` all absent, and L3 reading "all options saw all 0 active
    constraints" against the production capture's 1. Benchmarking that would have
    measured a degraded pipeline and called it a model difference.
    """
    sf = await orchestrator.create_agent_with_dependencies(
        "A9_Solution_Finder_Agent",
        {
            "orchestrator": orchestrator,
            "registry_factory": factory,
            "enable_llm_debate": True,
            "enable_hybrid_council": True,
            # Mirrors a9_orchestrator_agent.py's solution-finding config exactly.
            "enable_causal_grounding": _env_flag("SF_ENABLE_CAUSAL_GROUNDING"),
            "causal_max_hops": int(os.getenv("SF_CAUSAL_MAX_HOPS", "2") or 2),
            "enable_critic_pass": _env_flag("SF_ENABLE_CRITIC_PASS"),
            "enable_theory_moderator": _env_flag("SF_ENABLE_THEORY_MODERATOR"),
            "use_structured_output": _env_flag("SF_USE_STRUCTURED_OUTPUT"),
            "stage1_allow_frame_challenge": _env_flag("SF_STAGE1_ALLOW_FRAME_CHALLENGE"),
            "enable_computed_impact": _env_flag("SF_ENABLE_COMPUTED_IMPACT"),
        },
    )
    if getattr(sf, "orchestrator", None) is None:
        await sf.connect(orchestrator)
    else:
        await _connect(sf, orchestrator)
    return sf


# ---------------------------------------------------------------------------
# Fixture + SF invocation
# ---------------------------------------------------------------------------

def fixture_personas(path: Path) -> Optional[List[str]]:
    """The council the fixture's own capture ran, read from its Stage 1 keys.

    SF chooses personas from `preferences.consulting_personas`; with none set it
    falls back to the MBB council. The first pilot silently ran mckinsey/bcg/bain
    against the `lens_run` fixture, whose capture used the commercial/operational/
    structural LENS council — so the replay was not reproducing the run it claimed
    to replay. Defaulting to what the capture recorded makes that impossible.
    """
    sf_file = path / "sf-synthesis-payload.json"
    if not sf_file.exists():
        return None
    raw = json.loads(sf_file.read_text(encoding="utf-8"))
    sol = raw.get("solutions", raw) if isinstance(raw, dict) else {}
    hyps = sol.get("stage_1_hypotheses") or {}
    return sorted(hyps) or None


def load_fixture(path: Path) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    da_file = path / "da-payload.json"
    if not da_file.exists():
        raise SystemExit(
            f"{da_file} not found. Only fixtures WITH a DA payload are usable — "
            f"link 5 (sound reasoning) scores not-checked without one."
        )
    raw = json.loads(da_file.read_text(encoding="utf-8"))
    da = raw.get("execution")
    if not isinstance(da, dict):
        raise SystemExit(f"{da_file} has no 'execution' block (the SF input)")
    market = None
    if raw.get("market_signals") or raw.get("market_synthesis"):
        market = {
            "market_signals": raw.get("market_signals"),
            "market_synthesis": raw.get("market_synthesis"),
            "market_conflict": raw.get("market_conflict"),
        }
    return da, market


async def run_sf(sf, da: Dict[str, Any], market, stage: str,
                 prior: Optional[Dict[str, Any]], client_id: str,
                 principal_id: str, personas: Optional[List[str]] = None) -> Any:
    from src.agents.models.solution_finder_models import SolutionFinderRequest

    prefs: Dict[str, Any] = {"debate_stage": stage}
    if personas:
        prefs["consulting_personas"] = list(personas)
    if prior is not None:
        prefs["prior_stage1_hypotheses"] = prior

    req = SolutionFinderRequest(
        request_id=f"bakeoff-{stage}-{int(time.time()*1000)}",
        principal_id=principal_id,
        deep_analysis_output=da,
        market_analysis_input=market,
        preferences=prefs,
    )
    return await sf.recommend_actions(req)


def to_payload(resp: Any) -> Dict[str, Any]:
    """SF response -> the {"solutions": {...}} shape score_dq_run.py expects."""
    if hasattr(resp, "model_dump"):
        return {"solutions": resp.model_dump(mode="json")}
    return {"solutions": dict(resp)}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def use_arm_llm(orchestrator, sf, agent) -> None:
    """Point BOTH resolution paths at this arm's LLM agent.

    SF prefers the orchestrator's registered agent over its own attribute
    whenever an orchestrator is present (a9_solution_finder_agent.py: the
    synthesis call is `orchestrator.execute_agent_method("A9_LLM_Service_Agent",
    ...)`, with `self.llm_service_agent` only as the no-orchestrator fallback).
    Setting the attribute alone silently leaves every call on the registered
    agent — the pilot caught exactly that, with an "astra" arm served by
    claude-sonnet-5.
    """
    await orchestrator.register_agent("A9_LLM_Service_Agent", agent)
    sf.llm_service_agent = agent


async def main_async(args) -> int:
    fixture = Path(args.fixture)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    da, market = load_fixture(fixture)
    print(f"fixture     : {fixture}  (KPI={da.get('plan', {}).get('kpi_name')!r}, "
          f"client={da.get('plan', {}).get('client_id')!r})")

    personas = ([x.strip() for x in args.personas.split(",") if x.strip()]
                if args.personas else fixture_personas(fixture))
    if not personas:
        print("  WARNING: no council resolved from the fixture and --personas not given; "
              "SF will fall back to its default (MBB) council.", file=sys.stderr)
    print(f"council     : {', '.join(personas) if personas else '(SF default)'}")

    arms = [Arm(a) for a in args.arm]
    print(f"arms        : {', '.join(map(repr, arms))}")
    print(f"n per arm   : {args.n}    effort: {args.effort or '(unset)'}")

    # Effort is a GLOBAL env knob on the Anthropic side — record it, do not
    # assume it only touched the arm's model.
    if args.effort:
        os.environ["A9_LLM_EFFORT"] = args.effort

    orchestrator, factory = await bootstrap()
    sf = await make_sf(orchestrator, factory)

    llm_agents = {p: await make_llm_agent(p) for p in {a.provider for a in arms}}
    llm_agents.setdefault("anthropic", await make_llm_agent("anthropic"))

    # ---- Stage 1 pool: PAIRED sampling ----
    # One frozen capture would hold Stage 1 identical across every run, which
    # sounds like the tightest possible control but pins L2 (distinct lever
    # families) to whatever that single capture happened to yield — the first
    # pilot scored 1 family on every run of both arms because the frozen
    # hypotheses were homogeneous. A POOL restores L2's variance across runs
    # while still giving run i of every arm byte-identical input: a matched-pairs
    # design, which is both fairer and statistically stronger than either extreme.
    pool_size = args.stage1_pool if args.stage1_pool else args.n
    pool_file = out / "stage1-pool.json"
    pool: List[Dict[str, Any]] = []
    s1_cost = 0.0
    if pool_file.exists() and not args.refreeze:
        pool = json.loads(pool_file.read_text(encoding="utf-8"))
        print(f"stage 1     : reusing pool of {len(pool)} captures")
    else:
        print(f"stage 1     : capturing pool of {pool_size} (anthropic, council={personas}) ...")
        await use_arm_llm(orchestrator, sf, llm_agents["anthropic"])
        for k in range(pool_size):
            s1 = await run_sf(sf, da, market, "stage1_only", None, args.client_id,
                              args.principal_id, personas)
            hyps = getattr(s1, "stage_1_hypotheses", None)
            if not hyps:
                print(f"  capture {k+1}: FAILED (no stage_1_hypotheses) — "
                      f"status={getattr(s1, 'status', '?')}", file=sys.stderr)
                continue
            s1_cost += cost_of(ledger_of(to_payload(s1)["solutions"]))
            pool.append(hyps)
            print(f"  capture {k+1}/{pool_size}: {', '.join(sorted(hyps))}")
        if not pool:
            print("  FAILED: no Stage 1 captures succeeded.", file=sys.stderr)
            return 1
        pool_file.write_text(json.dumps(pool, indent=1), encoding="utf-8")
        print(f"  pool of {len(pool)} captured  (${s1_cost:.4f})")

    if args.dry_run:
        est = args.n * len(arms) * 1.05
        print(f"\n--dry-run: stopping after the freeze. "
              f"Estimated sweep cost ~${est:.2f} "
              f"({args.n} x {len(arms)} arms x ~$1.40/run). Re-run without --dry-run.")
        return 0

    # ---- Sweep ----
    manifest: Dict[str, Any] = {
        "fixture": str(fixture),
        "n": args.n,
        "effort": args.effort,
        "flags": {k: os.environ.get(k) for k in (
            "SF_ENABLE_CAUSAL_GROUNDING", "SF_ENABLE_CRITIC_PASS",
            "SF_ENABLE_THEORY_MODERATOR", "DA_ENABLE_FRAMING_GATE",
            "SF_STAGE1_ALLOW_FRAME_CHALLENGE", "SF_CAUSAL_MAX_HOPS")},
        "sf_config": {k: getattr(sf.config, k, None) for k in (
            "enable_causal_grounding", "causal_max_hops", "enable_critic_pass",
            "enable_theory_moderator", "use_structured_output",
            "stage1_allow_frame_challenge", "enable_computed_impact")},
        "consulting_personas": personas,
        "stage1_pool_size": len(pool),
        "stage1_paired": True,
        "stage1_cost_usd": round(s1_cost, 4),
        "arms": {},
    }
    spent = s1_cost

    for arm in arms:
        arm_dir = out / arm.name
        arm_dir.mkdir(parents=True, exist_ok=True)
        os.environ["LLM_PROVIDER"] = arm.provider
        os.environ[SYNTHESIS_ENV[arm.provider]] = arm.model
        await use_arm_llm(orchestrator, sf, llm_agents[arm.provider])
        rows: List[Dict[str, Any]] = []
        print(f"\n=== arm {arm.name}: {arm.provider}/{arm.model} ===")

        for i in range(1, args.n + 1):
            if args.max_spend and spent >= args.max_spend:
                print(f"  ABORT: spend ${spent:.2f} reached --max-spend ${args.max_spend}", file=sys.stderr)
                manifest["aborted_at"] = f"{arm.name}/run_{i:02d}"
                break
            # Run i of EVERY arm gets pool[i-1] — the pairing.
            frozen = pool[(i - 1) % len(pool)]
            t0 = time.perf_counter()
            try:
                resp = await run_sf(sf, da, market, "synthesis", frozen,
                                    args.client_id, args.principal_id, personas)
            except Exception as e:
                print(f"  run {i:02d}: EXCEPTION {type(e).__name__}: {e}")
                rows.append({"run": i, "error": f"{type(e).__name__}: {e}"})
                continue
            el = time.perf_counter() - t0

            payload = to_payload(resp)
            sol = payload["solutions"]
            ledger = ledger_of(sol)
            c = cost_of(ledger)
            spent += c

            run_dir = arm_dir / f"run_{i:02d}"
            run_dir.mkdir(exist_ok=True)
            (run_dir / "sf-synthesis-payload.json").write_text(
                json.dumps(payload, indent=1), encoding="utf-8")
            # score_dq_run.py looks for the DA payload beside the SF payload.
            shutil.copyfile(fixture / "da-payload.json", run_dir / "da-payload.json")

            # Per-run diagnostics that decide whether a link is comparable across
            # arms. The critic pass runs on the arm's provider, and SF only emits
            # `critic_pass_findings` when the list is non-empty — so zero findings
            # is indistinguishable from a parse failure or a swallowed exception.
            # L3 reads critic text, so an arm that systematically yields no findings
            # is not comparable on that link. Counting it per run turns an anecdote
            # into a rate.
            events = [e for e in (sol.get("audit_log") or []) if isinstance(e, dict)]
            crit = next((e for e in events if e.get("event") == "critic_pass_findings"), None)
            critic_n = int(crit.get("count") or 0) if crit else 0
            event_names = sorted({str(e.get("event")) for e in events})
            served = sorted({str(r.get("model")) for r in ledger if r.get("model")})
            drift = [m for m in served if m != arm.model and m in PRICING
                     and m not in (None,)] if served else []
            n_opts = len(sol.get("options_ranked") or [])
            degraded = bool(sol.get("analysis_degraded"))
            rows.append({
                "run": i, "stage1_index": (i - 1) % len(pool),
                "seconds": round(el, 1), "cost_usd": round(c, 4),
                "options": n_opts, "degraded": degraded,
                "degraded_reason": sol.get("degraded_reason"),
                "served_models": served, "ledger": ledger,
                "critic_findings": critic_n,
                "narrative_claim_mismatch": "narrative_claim_mismatch" in event_names,
                "audit_events": event_names,
            })
            flag = ""
            if degraded:
                flag = "  <-- DEGRADED (stub/truncation), exclude"
            elif arm.model not in served:
                # Fable's automatic refusal fallback lands here: HTTP 200, but a
                # different model authored the synthesis.
                flag = f"  <-- ARM MODEL ABSENT from ledger, exclude"
            print(f"  run {i:02d}: {el:6.1f}s  ${c:6.4f}  options={n_opts}  "
                  f"critic={critic_n}  served={','.join(served) or '?'}{flag}")

        manifest["arms"][arm.name] = {
            "provider": arm.provider, "model": arm.model, "runs": rows,
            "cost_usd": round(sum(r.get("cost_usd", 0) for r in rows), 4),
        }
        os.environ.pop(SYNTHESIS_ENV[arm.provider], None)

    manifest["total_cost_usd"] = round(spent, 4)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    print(f"\n{'='*70}\ntotal spend: ${spent:.4f}")
    for name, a in manifest["arms"].items():
        ok = [r for r in a["runs"] if not r.get("error") and not r.get("degraded")
              and a["model"] in (r.get("served_models") or [])]
        print(f"  {name:10} {len(ok)}/{len(a['runs'])} usable runs   ${a['cost_usd']:.4f}")
    print(f"manifest: {out / 'manifest.json'}")
    print(f"\nScore with:\n  python scripts/score_dq_run.py {out}/*/run_*")
    return 0


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fixture", required=True, help="run dir holding da-payload.json")
    p.add_argument("--arm", action="append", required=True,
                   help="name:provider:model (repeatable)")
    p.add_argument("--n", type=int, default=10, help="runs per arm (>=10 recommended)")
    p.add_argument("--effort", default=None,
                   help="low|medium|high|xhigh — both providers support this range")
    p.add_argument("--out", required=True)
    p.add_argument("--personas", default=None,
                   help="comma-separated council (e.g. commercial,operational,structural). "
                        "Default: whatever the fixture's own capture ran.")
    p.add_argument("--client-id", default="lubricants")
    p.add_argument("--principal-id", default="cfo_001")
    p.add_argument("--max-spend", type=float, default=None,
                   help="abort the sweep once cumulative cost reaches this ($)")
    p.add_argument("--stage1-pool", type=int, default=None,
                   help="number of Stage 1 captures to pool (default: --n, i.e. one "
                        "per run index, paired across arms). 1 = single frozen capture.")
    p.add_argument("--refreeze", action="store_true",
                   help="recapture the Stage 1 pool even if one exists")
    p.add_argument("--dry-run", action="store_true",
                   help="bootstrap + Stage 1 freeze only, then report the estimate")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv[1:])

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    if args.n < 10 and not args.dry_run:
        print(f"WARNING: n={args.n}. These models reject temperature=0; output is "
              f"stochastic. n>=10 per arm is the floor for comparing distributions.\n",
              file=sys.stderr)
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
