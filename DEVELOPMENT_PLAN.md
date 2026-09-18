# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Last updated:** 2026-09-17
**Status:** Active — restarting after a 12-day pause (last commit 2026-09-05)

> **How this document works.** This file is the **index**: verified status and what to do next.
> It is deliberately short enough to read in one sitting.
>
> - Design detail for open work → [`docs/DEVELOPMENT_BACKLOG.md`](docs/DEVELOPMENT_BACKLOG.md)
> - Shipped phases + post-mortems → [`docs/DEVELOPMENT_HISTORY.md`](docs/DEVELOPMENT_HISTORY.md)
> - Architecture of record → [`docs/architecture/`](docs/architecture/) (39 docs — **these win over any narrative here**)
>
> **Rule for keeping it manageable:** every phase heading carries a status word. If you can't
> state the status in one word, the phase is scoped wrong. Detail goes to the backlog, not here.

---

## Status legend

| Word | Means | How it was checked |
|---|---|---|
| **SHIPPED** | Artifact present in tree + commit exists | grep/ls + `git log` |
| **LIVE** | Present *and* reachable from a running path | traced to route/registration |
| **PARTIAL** | Some slices shipped, named remainder open | per-slice check |
| **OPEN** | Not built — verified absent | grep returned nothing |
| **GATED** | Built, but blocked on a condition not in your control | condition named below |
| **DECIDE** | Built, but the evidence says stop and choose | see note |

Statuses below were re-verified against the code on **2026-09-17**. Where a phase's own prose
inside the backlog disagrees, **this table wins** — the prose predates the sweep.

---

## Where you are — 2026-09-17

**Health:** `1688 passed, 3 skipped` (unit suite, 9.06s, exit 0). Tree is green.

**Last work:** Phase 22 Stage D, 2026-09-05. **The result was NEGATIVE** across three independent
measurements. The plan's own verdict: *"Phase 22 is not validated by this measurement, in either
direction."* You did not stop mid-build — you stopped at a genuine decision point, which is
probably why restarting felt unclear.

**Uncommitted:** Phase 24 (Adaptive Investigation) — a 227-line proposal added 2026-09-09, never
committed. Plus `.agents/`, `.codex/`, `.github/agents|hooks|skills/`, `.tmp_sweep/`.

**Pipeline, unchanged and operational:**

```
run_enterprise_assessment.py
  → SA (detect KPI breaches, client-scoped)
  → DA (Is/Is Not root cause, benchmark segments)
  → kpi_assessments + assessment_runs (Supabase)
  → A9_PIB_Agent (compose + email)
  → Decision Studio (Deep Analysis → Solution Finding → HITL → Value Assurance)
  → Portfolio (5-phase lifecycle → verdict → ROI)
```

---

## The three things to decide first

Pick these before writing code. Each is a fork, not a task.

### 1. Phase 22 — DECIDE

Stages A–C shipped (`CouncilDebatePage.tsx` carries the lens-probe screen). Stage D's validation
came back **negative**, and the phase's own text says the real test *"can only come from real
executives answering real questions through Stage C's shipped UI, not from a simulated
executive."* Stage C is shipped, so that test is now available to run.

**Options:** run the real-user test → redesign the measurement → or park the phase and
de-prioritise the lens thesis. Do not start Stage E-equivalent work until this is settled.

### 2. Phase 18 — OPEN, and it's a commercial exposure

**This is the finding I'd act on first.** The de-branding was never done. Live MBB firm names
across **14 files**, including user-facing surfaces:

| File | Hits |
|---|---|
| `decision-studio-ui/src/components/CouncilDebate.tsx` | 9 |
| `src/agents/new/a9_solution_finder_agent.py` | 6 |
| `src/agents/new/a9_deep_analysis_agent.py` | 5 |
| `decision-studio-ui/src/config/uiConstants.ts` | 5 |
| `src/registry/consulting_personas/consulting_persona_provider.py` | 4 |
| `LandingPage.tsx`, `HowItWorks.tsx`, `ExecutiveBriefing.tsx`, `CouncilDebatePage.tsx`, `ProblemRefinementChat.tsx`, `InsightsBIModernization.tsx`, `LandingPageAlternate.tsx`, `personaLabels.ts`, `decision_quality.py` | 1–3 each |

`a9_deep_analysis_agent.py:246-250` hardcodes `"McKinsey-style"` / `"BCG-style"` / `"Bain-style"`
into prompts; `a9_solution_finder_agent.py:1604` instructs the model to critique *"from each
consulting firm."* A landing page and an executive briefing template carry the names too.

These are third-party trademarks on a product you intend to sell. Mechanically it's a rename;
the reason it ranks first is exposure, not difficulty.

### 3. Phase 24 — commit or drop

227 lines of proposal sitting uncommitted for 8 days. Either commit it as a proposal (it's
explicitly marked *"Proposed, unscheduled"*, which is honest) or drop it. Leaving it dirty in the
tree is what makes `git status` unreadable on restart.

---

## Open phases — verified

### Ready to build (nothing blocking)

| Phase | Status | Verified by |
|---|---|---|
| **25 step 1** — canonical `period_key` | **SHIPPED** (2026-09-18) | `TimeFilter.period_key_expr`/`period_key_grain`; DPA resolves via `_resolve_time_spec`; 4 new tests, 1692 passing. **Live-verified against BigQuery**: both products emit identical `YYYY-MM` keys; `sales_order_count` returns 9 trend rows where it returned none. SA's 3 hand-rolled copies deliberately untouched (live sparkline path) |
| **18** — Council de-branding + Lens Council UI | **OPEN** | MBB names present in 14 files |
| **11I-D** — PIB alert-type differentiation | **PARTIAL** | 11I-A/B/C shipped; D remaining |
| **11H** — DA seasonal decomposition | **PARTIAL** | effect size + outlier shipped; decomposition absent |
| **13** — Cat 4 role-adaptive collapse depth | **PARTIAL** | Cat 3 built 2026-08-16; one UI item left |
| **12B** — RACI accountability | **PARTIAL** | fields in `agent_config_models.py`, SA, `routes/registry.py`; **no migration** |
| **Infra C** — SOC 2 controls | **PARTIAL** | `audit_event` in SF agent + `src/analysis/*`; no migration, no sign-in audit |

### Blocked on a prerequisite

| Phase | Status | Blocker |
|---|---|---|
| **Pre-11K** — Meridian synthetic dataset | **OPEN** | `scripts/clients/meridian.py` absent — **this gates 11K–11N** |
| **11K** — Data product observability | **OPEN** | `pipeline_status` absent; needs Meridian |
| **11L** — EDA dimensional profiling | **OPEN** | `dimension_importance_profile` absent; needs Meridian |
| **11M** — Change detection + background DA | **OPEN** | no agent, no `da_background_runs`; needs 11L |
| **11N** — Event-driven PIB + DA state | **OPEN** | `da_state` absent; needs 11M |
| **11J** — Solution validity monitoring | **OPEN** | no health scoring in VA agent |
| **12C** — Business objectives registry | **OPEN** | `business_objectives` absent |
| **12D** — Objective health score | **OPEN** | needs 12C |
| **12E** — Principal templates | **OPEN** | *(earlier "present" reading was wrong — those `status='template'` hits are **KPI** templates from 12A)* |
| **25 step 2** — declared `comparison_basis` | **SHIPPED** (2026-09-18) | `comparison_basis` on `TimeDimensionSpec` + per-KPI `metadata['time_dimension']` override; `resolve_comparison_basis()` is step 3's read side. No migration (JSONB + `Dict[str,str]`). 10 new tests, 1702 passing. **Seed changed → needs `onboard_client.py --client lubricants --env production`** |
| **25 step 3** — guard causal affirmation | **DECIDE** | step 2 done; blocked only on **an open product question**: does a basis mismatch block affirmation outright or downgrade to a flagged edge? Changes what the theory layer may count |

**11K–11N is a four-phase chain behind one absent seed file.** That's the single highest-leverage
unblock in the backlog: build Meridian and four phases become available.

### Built but gated

| Phase | Status | Gate |
|---|---|---|
| **17** — Theory Layer | **GATED** | All of T1–T4 verified present: migrations `20260830160000/170000/180000/190000`, `src/analysis/decomposition.py`, `src/registry/validators/additivity_validator.py`, `_grade_assumptions_from_verdict` in the VA agent. Exhibit is `/dev/theory-layer`, **deliberately unlinked from nav**. Causal-edge density gate sits at 0 tested edges and **clears only through accumulated VA verdicts over real use — never by seeding.** Registry data not yet synced to production. |
| **20** — Causal-neighbourhood evidence | **PARTIAL** | Backend + `CausalTrendChart.tsx` present (`components/visualizations/`). BigQuery-only this pass. |

### Parallel tracks (no phase number)

| Track | Status | Where |
|---|---|---|
| UI Refinement | **OPEN** | backlog + `docs/architecture/ui_refinement_plan.md` |
| Data Onboarding Refinement | **OPEN** | backlog, 11 workstreams |
| Infra A2 / A3 / A5 / B2 | **OPEN** | backlog |
| MCP Abstraction (10D) / Native AI (10E) | **OPEN** | "MCP-ready, not proven" — not wired to the live path |

---

## Live defects (observed, not yet fixed)

These came from driving the app, not from tests — the suite is green and these are all still real.

| Defect | Note |
|---|---|
| **Causal Neighbourhood chart plots only the primary KPI** (2026-09-17) | ✅ **Fixed 2026-09-18 via Phase 25 step 1.** `generate_monthly_series_sql` guessed `transaction_date`, which the sales view doesn't have; Net Revenue rendered **by accident**. Now resolves the data product's declared `TimeDimensionSpec` and emits a canonical `YYYY-MM` key. A dropped series now says so in the UI instead of vanishing. **Live-verified 2026-09-18**: `sales_order_count` returns 9 trend rows; the old `display_expr` was observed emitting `"2026-012"` against the date path's `"2026-05"`. |
| **Per-lens arguments dropped from the briefing** (2026-09-17) | ✅ **Fixed 2026-09-17.** `briefingUtils.ts` read `views[0]` only, so 1 of 3 lenses' `arguments_for`/`arguments_against` reached the page under a heading that reads as the council's consensus — verified against a captured payload: 3 of 3 lenses now, was 1 of 3. `decision_quality.py` reads the raw payload and was never affected, which is why it survived: the scorer saw what the reader could not. |
| **SA severity calibration** — 14 of 15 KPIs flagged CRITICAL | Red carries no information. The "N KPIs within normal range" collapse never engages. Related: **the number shown on the tile is not the number that triggered the alert.** Threshold calibration + a tile data contract, not a UI fix. |
| **DA prose is polarity-unaware** | Rendered "Raw Materials Cost is **over-performing**" for a cost *up* 22.3%, flagged CRITICAL. Narrative contradicts the badge on the same screen. |
| **SF convergence / dominated options / ID leakage** | Three personas produced near-verbatim restatements, all "High conviction", rendered as three independent columns implying corroboration. `opt_1`/`opt_2` modelled at identical `$3.8M–$5.2M` with opt_2 strictly dominated. Internal IDs leak into executive prose ("…under opt_1"). |
| **Workflow re-run guards** | `CouncilDebatePage.runDebate()` unconditionally deletes every `solutions_*`/`briefing_*` localStorage key and re-runs ~5.5 min of real LLM spend, no confirmation, no partial retry. `handleDeepAnalysis` has no cache check. **At minimum, stop deleting what cannot be restored.** |
| **No client indicator in `AppHeader`** | Testers can't tell bicycle from lubricants and assume DA is broken. |
| `situations` table partially redundant with `kpi_assessments` | Deprecation deferred — VA pipeline uses it. |
| `run_enterprise_assessment.py` has no scheduler | CLI only; event-driven design lives in 11K–11N. |
| `_workflow_store` is in-memory only | A Railway restart between DA run and HITL approval yields a VA record with `control_group_segments=None`. Permanent fix belongs to Infra A5. |

---

## Architecture decisions (non-negotiable)

- **SA = sensor** — detects KPI movements, no problem/opportunity labeling
- **DA = analyst + framer** — determines `analysis_mode` from segment variance structure, not SA. Mixed mode is the normal enterprise state; pure problem / pure opportunity are edge cases.
- **Unit of decision is the segment, not the KPI headline** — DA's IS/IS NOT produces dimensional coordinates; SF targets those coordinates; VA validates recovery at segment level before aggregating
- **Assessment runs are client-scoped** — one enterprise scan per client, all principals read from it
- **KPI accountability is dimensional** — same KPI can belong to multiple principals at different scopes
- **Accountability is a routing/escalation axis, not a visibility gate** — RACI role determines *how* a KPI surfaces, never whether it's hidden; unassigned is visible to everyone (fail-open)
- **No snooze/hide preference layer** — correct signal routing eliminates noise at source
- **LLM-assisted accountability import** — HCM documents are source of truth; LLM extracts, human confirms
- **Brand: "Decision Studio"** — Swiss Style, monochrome dominance, semantic color only, "Quiet Expert" voice
- **Domains:** decision-studios.com (brand) + trydecisionstudio.com (demo/trial)

Full model: `docs/architecture/kpi_accountability_model.md` (original 2-role) and
`docs/architecture/raci_accountability_model.md` (4-role RACI — redefines Phase 12B).

---

## Suggested restart sequence

Ordered by leverage, not by phase number.

1. **Clear the tree** — commit or drop Phase 24; deal with the untracked dirs. Ten minutes, and `git status` becomes readable again.
2. **Phase 25 step 1 — canonical `period_key`.** ~1 day, pure consolidation of logic already hand-rolled in three places. Restores the causal trend lines as a side effect and unblocks steps 2–3. Do this before any further causal-graph work: every edge affirmed on the current basis is affirmed on an unverified time alignment.
3. **Phase 18 de-branding** — mechanical, bounded to 14 files, removes trademark exposure. Good re-entry work: it re-familiarises you with SF, DA, and the UI council surfaces without requiring a design decision.
4. **Decide Phase 22** — Stage C is shipped, so the real-executive test is available. Settle it before building further on the lens thesis.
5. **Pick one live defect** — SA severity calibration is the highest-value one; "14 of 15 CRITICAL" undermines the core demo more than any missing phase does.
6. **Then, if you want new capability:** build Meridian (Pre-11K) and unblock the 11K→11N chain in one move.

---

## Phase numbering — known irregularities

Left as-is deliberately; renumbering would break every cross-reference in `docs/architecture/`.

- **21 and 23 do not exist.** 21 was written and deleted (a design doc's stale self-description was trusted over the agent cards and code). **25 was chosen for the temporal-alignment phase rather than reusing either** — a deleted number carries history that would confuse cross-references.
- **12A–12F are not in alphabetical order** — they were invented as needed: 12A, 12F, 12E, 12B, 12C, 12D.
- **"Phase 10D" names two different things** — Solution Finder Performance Tuning (shipped) *and* the MCP Abstraction Layer (open).
- **11A–11I live inside "Phase 11: Platform Correctness"** in the history file rather than as top-level phases.
