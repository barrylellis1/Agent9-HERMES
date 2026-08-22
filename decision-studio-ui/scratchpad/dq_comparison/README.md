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
