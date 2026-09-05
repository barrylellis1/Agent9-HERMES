# DQ comparison corpus

Captured Solution Finder runs, scoreable via `scripts/score_dq_run.py <run-dir>`.
Referenced as the held-out validation corpus in
`docs/architecture/dq_l1_framing_signal_design.md`.

| Run | Date | KPI / client | Framing outcome | DA payload? | DQ result |
|---|---|---|---|---|---|
| `lens_run` | 2026-08-19 | (pre-Phase-19, no framing gate) | n/a | yes | see `cat3-summary.json` |
| `mbb_run` | 2026-08-19 | (pre-Phase-19, no framing gate) | n/a | yes | see `cat3-summary.json` |
| `gross_margin_reframe_run` | 2026-08-22 | Gross Margin % / lubricants (CFO, owner) | **reframed** → COGS (1 hop, accounting identity) | **no** | 5/5 (L5 not-checked) |
| `ecommerce_confirm_run` | 2026-08-22 | E-Commerce Revenue / bicycle (CEO, non-owner, mixed-mode) | **confirmed** (0 alternatives offered) | **no** | 4/5, capped by L1 |
| `frontier_bakeoff_2026-09-04/` | 2026-09-04 | Gross Margin % / lubricants (lens council) | n/a (replay of `lens_run`'s DA payload) | **yes** (per run) | 10 matched pairs per arm — see its own README |
| `lens_probe_validation_2026-09-05/` | 2026-09-05 | Gross Margin % / lubricants (lens council) | n/a | n/a (Stage 1 diversity test, not a full SF run) | NEGATIVE (3 independent measurement attempts) -- see its own README |

## What `lens_probe_validation_2026-09-05` adds

Phase 22 Stage D: does persona-keyed refinement (Stages A-C) actually increase
Stage 1 hypothesis diversity? Measured directly via classify_lever on Stage 1's
own proposed_option titles -- no synthesis call needed. THREE completed runs,
kept all three: **v1** gave the simulated executive only a 3-line recap,
missing 4 of 5 segment-level change_points the questions themselves asked
about -- every answer hedged, mean dropped to 2.60 vs baseline's 3.00, later
found to be a harness confound (under-provisioned information), not evidence
about lens-probing. **v2**, corrected to give the simulator the COMPLETE DA
output, came back near-neutral: mean 2.90 vs baseline's 3.00 (9/10 tied, 1/10
below, 0/10 above) -- attributed to baseline already sitting at the diversity
ceiling (3/3) on this fixture. **v3**, on direct instruction, prescribed
three simulated-executive postures (conservative/assertive/middle) with
non-hedging enforced by regex check (not just requested) rather than left to
chance -- all three postures came back at or slightly below a *fresh* baseline
draw (2.50, 2.50, 2.40 vs baseline's 2.60), and that fresh baseline draw was
NOT at ceiling, contradicting v2's ceiling explanation. The real finding from
v3: baseline's own run-to-run swing (3.00 in v2 vs 2.60 in v3, same fixture,
same code) is as large as any posture-vs-baseline gap observed -- this
measurement's noise floor rivals the effect size it's trying to detect.
None of the three runs indict the Stage A-C plumbing (independently
unit-tested and confirmed working); all three share the same irreducible
limitation -- no live executive answered these questions, and no simulation
can substitute for that. See its own README for the full three-run writeup.

## What `frontier_bakeoff_2026-09-04` adds

The first **paired model comparison** in this corpus, and the first entry produced by
`scripts/run_dq_bakeoff.py` rather than a Playwright capture off a live UI session.
20 runs (10 per arm) replaying `lens_run`'s DA payload through today's SF with the
lens council, comparing `claude-fable-5` against `gpt-6-astra` on the synthesis call.

Headline: astra 94.7% vs fable 86.7% DQ, but **sign test p=0.375 — not significant**,
with 5 of 10 pairs tied. Both models pass 96.7%/98.9% of option-level groundedness
checks, so the scorer is near saturation on frontier models and finer endpoints tie
*more*, not less. The durable finding is cost: astra 37% cheaper on identical list
pricing, consistent across all 10 pairs.

That directory's README also lists five traps that each produced runs looking
completely normal — read it before running another bake-off.

## What the two 2026-08-22 runs add

Captured live against `live-framing-gate.spec.ts` / `live-framing-gate-ecommerce.spec.ts` —
first real runs to exercise the `causal_direction` path-validity filter and the
`accounting_identity`/`causal_estimate` reclassification
(`docs/architecture/kpi_relationship_basis_design.md`) end to end, and the first pair
with genuinely different framing outcomes (reframe vs. confirm) captured back to back.
The L1 split — reframe passes, confirm-with-zero-alternatives fails — matches the design
note's own prediction, on two independent KPIs from two different clients.

**Neither carries a `da-payload.json`** — the framing-gate specs don't intercept the DA
response, only `/workflows/deep-analysis/refine` and `/workflows/solutions/run`. Link 5
(reasoning) scores `not-checked` for both, same as it would for any run missing that file.
Adding DA-payload capture to those specs would close this gap; not done here since it
wasn't asked for and would mean another live run.

**`gross_margin_reframe_run` is missing its screenshots and turn-by-turn JSON** — lost, not
withheld: `npx playwright test` clears the whole `playwright-results-live` output directory
on each invocation, and three subsequent runs (fixing an unrelated auto-launch race in the
e-commerce spec) wiped this run's artifacts before they were archived here.
`sf-synthesis-payload.json` survived because it was extracted to scratch immediately after
the run finished. `framing-gate-summary.json` in that folder is reconstructed from the live
console log and this conversation's own transcript — its own `_provenance_note` field says
so explicitly, and every value in it is a fact read out of one of those two sources, not
invented. `ecommerce_confirm_run` still has its full bundle (7 screenshots,
`refinement-turns.json`, `sf-request-and-response.json`) since it was the last run before
this cleanup, not overwritten by anything after it.
