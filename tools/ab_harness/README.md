# A/B Harness — Phase 15 experiment instrument

Drives the **live** API to compare Solution Finder arms under a fixed input. Every Phase 15
adoption decision (Stage H moderator, Stage A `use_structured_output`) rests on numbers this
produced, and an experimental result whose harness is unversioned is not reproducible — which is why
it lives here rather than in a scratchpad.

Promoted from a session scratchpad 2026-08-12. `DEVELOPMENT_PLAN.md` Phase 15 references it as
`ab_debate.py`.

## Why `tools/` and not `tests/`

It drives a live server and **spends money**. `pytest.ini` sets `testpaths = tests`, so nothing here
is ever collected by a test run — but the separation is intentional, not incidental.

## Usage

```bash
python tools/ab_harness/ab_debate.py capture          # DA + stage1_only -> ab_input.json
python tools/ab_harness/ab_debate.py run <arm> <n>    # n synthesis runs; arm = moderator | baseline
python tools/ab_harness/ab_debate.py report           # comparison table from ab_results.jsonl
python tools/ab_harness/ab_debate.py capture_diverse  # drive Problem Refinement to completion
python tools/ab_harness/ab_debate.py run_diverse <n>
```

Requires the stack running (`.\restart_decision_studio_ui.ps1`). Fixed constants:
`PRINCIPAL=cfo_001`, `CLIENT=lubricants`, `KPI=Gross Margin %`.

## Protocol — read before running

1. **Check API credit first.** A zero-credit account renders as `state: completed` with generic
   stub options — indistinguishable from a real recommendation. See `DEVELOPMENT_PLAN.md`
   ("A total LLM outage renders as a successful briefing"). The harness detects
   `heuristic_stub_fallback` and excludes those runs, but only after you have paid for them.
2. **The arm is a server-side env flag read at agent creation.** Batch per arm and **restart the
   backend between batches**. The harness confirms each run's arm from the response payload
   (`moderator_grades` vs `cross_review`) rather than trusting the env — do not weaken that.
3. **One variable per batch** (PM-4). Anything else moving invalidates the comparison.
4. Runs are numbered non-destructively and stamped with `git rev-parse --short HEAD`, so every row
   is attributable to the build that produced it. An earlier batch silently overwrote
   `ab_raw/moderator_1..2.json`; metrics survived in the JSONL, raw payloads did not.

## What is committed, and what is not

| Path | Committed | Why |
|---|---|---|
| `ab_debate.py` | yes | the instrument |
| `ab_input.json` | yes | **the situation under test** — results are meaningless without it |
| `ab_results.jsonl` | no | output; readouts belong in `DEVELOPMENT_PLAN.md` |
| `ab_raw/` | no | output |

## Stage I B-3 scripts

| Script | What it does |
|---|---|
| `b3_question_divergence.py <da.json> [mbb\|diverse\|famous] [model]` | 3–4 personas propose 6 refinement questions each; topic + lexical Jaccard against a simulated null |
| `b3_discovery_round.py <da.json> [model] [bare]` | 20 methods, one question + one follow-up each; saturation curve, unique contribution, Jaccard. `bare` strips the authored profiles and prompts with the name only — the circularity control |

Both hold `effort` at `medium` so model is the only variable. Record and findings:
`docs/architecture/persona_council_experiments.md`.

**Always compare against the null, never a hand-picked threshold.** Choosing k topics from a fixed
vocabulary produces overlap by arithmetic alone — 6-of-9 nulls at ~0.51, 2-of-9 at ~0.16. The first
version of the gate used a flat `<= 0.70 ⇒ diverge` rule that sat *below* the null and reported
divergence for chance, twice. Both scripts now simulate the null with a fixed seed.

## Measurement note

Read outputs against `src/analysis/` (`mechanism.py`, `groundedness.py`, `problem_profile.py`) —
deterministic instruments, compared **within** `problem_profile.cell_key()`. No LLM judge: a
stochastic ruler cannot measure a stochastic process.
