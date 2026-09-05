# Frontier model bake-off — Claude Fable 5 vs GPT-6 Astra

**Captured 2026-09-04.** First paired model comparison in this corpus, and the
first entry produced by `scripts/run_dq_bakeoff.py` rather than by a Playwright
capture off a live UI session.

## The question

Which model should serve the Solution Finder **synthesis** call. Fable 5 and
GPT-6 Astra are the tier-matched pairing: identical list pricing ($10/$50 per
1M), both 128K max output, both reject `temperature`. sonnet-5 vs astra would
have been a tier mismatch.

## Configuration

| | |
|---|---|
| Fixture | `../lens_run/da-payload.json` (`execution` block), replayed byte-identical |
| KPI / client | Gross Margin % / lubricants |
| Council | **lens** — `commercial, operational, structural` |
| Effort | `medium` on both arms (`A9_LLM_EFFORT` / `reasoning_effort`) |
| SF flags | causal_grounding=True, critic_pass=True, theory_moderator=True, causal_max_hops=2 |
| `SF_USE_STRUCTURED_OUTPUT` | **off** — matches production `.env`, so both arms ran the prompt-based JSON path |
| N | 10 matched pairs per arm |

Per-call routing, recorded in `manifest.json`:

```
fable   critic_pass -> claude-sonnet-5    moderator -> claude-fable-5
astra   critic_pass -> gpt-5.6-terra      moderator -> gpt-6-astra
```

**An arm is "frozen Stage 1, then critic + synthesis on this provider"** — not
"synthesis only". The critic resolves through the same LLM service agent, so it
moves with the arm's provider. That asymmetry is inherent to how SF resolves
providers and is recorded per run rather than assumed away.

## Design: paired Stage 1

Stage 1 ran **once per pair index** on Anthropic (Haiku) and the resulting
hypotheses were replayed into run *i* of **both** arms via
`preferences.prior_stage1_hypotheses`, which makes SF skip the three persona
calls entirely. `stage1-pool.json` holds all 10 captures.

A single frozen capture shared by every run was tried first and rejected: it
pins L2 (distinct lever families) to whatever that one capture yielded — an
early pilot scored 1 family on every run of both arms because the frozen
hypotheses were homogeneous. Pooling restores L2's variance across runs while
each pair still sees byte-identical input.

## Results

| pair | Stage 1 capture | fable DQ | astra DQ | lever families F/A | critic findings F/A | $ F/A |
|---|---|---|---|---|---|---|
| 1 | 0 | 6/6 (100%) | 4/5 (80%) | 3/1 | 4/2 | 0.75/0.48 |
| 2 | 1 | 5/6 (83%) | 6/6 (100%) | 3/3 | 2/1 | 0.68/0.48 |
| 3 | 2 | 5/6 (83%) | 5/6 (83%) | 2/3 | 2/1 | 0.75/0.46 |
| 4 | 3 | 5/6 (83%) | 6/6 (100%) | 3/2 | 3/0 | 0.76/0.40 |
| 5 | 4 | 4/6 (67%) | 6/6 (100%) | 2/3 | 2/1 | 0.66/0.44 |
| 6 | 5 | 5/6 (83%) | 5/6 (83%) | 2/3 | 3/2 | 0.69/0.51 |
| 7 | 6 | 6/6 (100%) | 6/6 (100%) | 3/3 | 2/1 | 0.80/0.47 |
| 8 | 7 | 4/6 (67%) | 5/5 (100%) | 2/1 | 3/2 | 0.68/0.46 |
| 9 | 8 | 6/6 (100%) | 6/6 (100%) | 2/2 | 4/1 | 0.76/0.48 |
| 10 | 9 | 6/6 (100%) | 6/6 (100%) | 2/3 | 2/0 | 0.69/0.42 |

| | Fable 5 | GPT-6 Astra |
|---|---|---|
| usable runs | 10/10 | 10/10 |
| DQ score | 86.7% (sd 13.1) | **94.7%** (sd 8.6) |
| range | 67–100% | 80–100% |
| chain verdict holds | 4/10 | **7/10** |
| lever families | 2.40 | 2.40 |
| L2 alternatives | 10/10 | 8/8 |
| L3 information | 10/10 | 10/10 |
| **L5 reasoning** | **7/10** | **9/10** |
| L6 commitment | 10/10 | 10/10 |
| cost/run | $0.722 | **$0.458** |
| latency | 134s | 128s |

## What this establishes — and what it does not

**Not significant.** Paired: astra higher in 4, Fable in 1, **5 ties**. A sign
test on the 5 non-tied pairs gives **p = 0.375**. The direction favours astra;
the evidence does not support a quality claim.

**The instrument is near saturation.** Finer endpoints tie *more*, not less:

| endpoint | fable | astra | ties | p |
|---|---|---|---|---|
| DQ score | 0.867 | 0.947 | 5/10 | 0.375 |
| failed links (lower better) | 0.80 | 0.30 | 5/10 | 0.375 |
| option groundedness (mean frac) | 0.967 | 0.989 | 8/10 | 0.500 |
| lever families | 2.40 | 2.40 | 3/10 | 1.000 |

At option level (30 observations per arm) both models pass 96.7% / 98.9% of
groundedness checks. The scorer was built to catch gross failures — stubs,
unsupported arithmetic, single-lever option sets — and two frontier models
mostly do not make those on this problem. **More runs on this fixture would
certify a ~2-point difference; they would not make it meaningful.**

**The durable finding is cost.** Astra ran **37% cheaper** on identical list
pricing, consistent across all 10 pairs — Fable's always-on thinking bills as
output. That gap is far more stable than the quality difference.

**Scope.** One fixture, one KPI, one client, one council, one effort level.
L1 and L4 are advisory screens, not verdicts. Nothing here speaks to whether an
executive would *trust* either set of recommendations — DQ is itself a proxy for
that, and the link between them is unvalidated. The real outcome signal is the
HITL action plus the later VA verdict, and the HITL `comment` is currently not
persisted by `PendingDecisionsStore.resolve()`.

## Reproducing / re-scoring

```bash
# score any run, or all of them
python scripts/score_dq_run.py decision-studio-ui/scratchpad/dq_comparison/frontier_bakeoff_2026-09-04/*/run_*

# re-run an arm (reuses stage1-pool.json, so pairing survives)
python scripts/run_dq_bakeoff.py \
  --fixture decision-studio-ui/scratchpad/dq_comparison/lens_run \
  --arm astra:openai:gpt-6-astra \
  --n 10 --effort medium --max-spend 12 \
  --out <this directory>
```

Every run directory carries its own `da-payload.json` (identical across all 20 —
git stores one blob) because `score_dq_run.py` expects it beside the SF payload.

## Traps this bake-off hit — read before running another

Each of these produced runs that looked **completely fine**: 3 options, plausible
titles, no error raised. They were caught only by per-run checks on the served
model and the degradation flag.

1. **Swapping `sf.llm_service_agent` does nothing.** SF resolves the synthesis
   call via `orchestrator.execute_agent_method("A9_LLM_Service_Agent", ...)` and
   only falls back to the attribute when there is no orchestrator. An "astra"
   arm ran entirely on claude-sonnet-5. Register the agent with the orchestrator.
2. **SF feature flags default False.** The live server sets them from `SF_ENABLE_*`
   env vars in `a9_orchestrator_agent.py`. A bare config gives no causal
   grounding — hence no critic pass and no theory moderator, both gated on it —
   and 0 active constraints where production had 1.
3. **SF falls back to the MBB council** when `preferences.consulting_personas` is
   unset. The first pilots ran mckinsey/bcg/bain against the *lens* fixture.
4. **`Config(provider="openai")` used to send the Anthropic key** (fixed in
   `8c1f29a`) — `api_key_env_var` defaulted off the `LLM_PROVIDER` env var.
5. **Anthropic credit exhaustion mid-sweep** returned the heuristic stub with 2
   plausible options and no error. Nine runs would have entered the data as
   Fable results. `analysis_degraded` is the only thing that caught it.

## Provenance

Fable arm re-run after the initial sweep hit credit exhaustion; astra arm is from
the original sweep, merged from `manifest.astra.json`. Pairing is preserved
because run *i* always draws `stage1-pool.json[i-1]` regardless of when it ran.
Total API spend for the captured runs: $11.80 ($4.58 OpenAI, $7.22 Anthropic).
