# UI Refinement Plan

**Created:** 2026-08-21
**Status:** Design note — audit complete, fixes not yet built (except where marked)
**Scope:** Compliance and cleanup against the design language that already exists, not a
redesign. See "What this plan is not" below.

---

## 1. Why this exists

`ui_brand_guidelines.md` and `decision-studio-ui/DESIGN_SYSTEM.md` already establish a real,
specific, opinionated design language — "Swiss Style" monochrome-plus-scarce-color, "The Quiet
Expert" voice, "The Chart is the Receipt" (Proof Not Playground — no drill-down buttons, no
filter dropdowns, ask the AI instead of clicking a control), progressive disclosure via
collapsible accordions. Both docs predate this note (Apr / May 2026) and are not being
revisited here.

What triggered this: three live UI bugs found this session while testing the causal-graph
framing gate (auto-launch not firing, a scroll-clip hiding the submit button, the greyed-out
submit button that followed from it — all three fixed same-session), plus a broader concern
raised directly: *does the UI reliably surface the right information at the right layer, and
is that governed by anything, or ad hoc per component?* This document is the audit that
concern deserved — checking actual code against the two documents' own stated rules, not
against taste. Findings below are evidence-based (file:line), not impressions.

---

## 2. Already fixed this session (logged for completeness, not open work)

| Finding | Fix | Files |
|---|---|---|
| `DeepFocusView` didn't auto-launch analysis on navigating to a situation | New `useEffect` keyed on `analysisResults?.kpi_name`/`analysis_mode`, guarded against re-firing | `DeepFocusView.tsx` |
| `ProblemRefinementChat`'s framing-gate footer clipped, hiding the submit button below the fold | Footer wrapper made `flex-1 min-h-0 flex flex-col overflow-hidden` when a framing prompt is active; `FramingGateCard` root gained matching `flex-1 min-h-0` | `ProblemRefinementChat.tsx`, `FramingGateCard.tsx` |
| Submit button appeared permanently greyed out | Direct consequence of the clip above — same fix | (same) |

---

## 3. Confirmed compliant — stated explicitly so these aren't "fixed" by mistake

Checked directly against the docs' own rules rather than assumed:

- **No drill-down buttons or filter dropdowns in any visualization.** Grepped
  `src/components/visualizations/` for interactive filter/drill affordances — every hit was an
  array `.filter()` call, not a UI control. `DivergingBarChart`, `CausalTrendChart`,
  `TrajectoryChart` are genuinely static-first, matching "Proof, Not Playground" as written,
  not as aspiration.
- **Answer-first SCQA is real and shipped.** `ScqaBlock` in `DeepFocusView.tsx` renders the
  Answer first and hides Situation/Complication/Question behind a "Show reasoning" toggle —
  progressive disclosure working exactly as `ui_brand_guidelines.md` §1 describes it.
- **The "+1 more causal measure evaluated, not shown" line is correct as built, not a gap.**
  Raised earlier this session as a candidate fix (turn it into an interactive "show more"
  affordance) — on rereading the brand doc, that would be the exact drill-down control §3
  rejects. The intended path is already the Refinement Chat conversation. No change
  recommended here; recorded so it isn't "fixed" into a violation later.
- **No `console.log` left in `DeepFocusView.tsx`** — checked directly, none found.

---

## 4. Open findings

### 4.1 Hardcoded severity colors — direct violation of DESIGN_SYSTEM.md §1

DESIGN_SYSTEM.md calls this "the single most important design-system rule": never hardcode
`red-400`/`amber-400`/`emerald-400`/`green-400` for semantic meaning, always use the
`severity-*` token group. Grepped the full component tree; the rule is violated in at least
15 files:

`AccountabilityInterviewPanel.tsx`, `animations/AgentAnimations.tsx`, `AttributionBreakdown.tsx`,
`briefing/AssumptionsPanel.tsx`, `briefing/DecisionAskBlock.tsx`,
`briefing/ImmediateActionsChecklist.tsx`, `CausalNeighbourhoodEvidence.tsx`,
`ConnectionHealthPanel.tsx`, `ConnectionProfileManager.tsx`, `CouncilDebate.tsx`,
`dashboard/HeroBriefing.tsx`, `dashboard/KPITile.tsx`, `DataProductSelector.tsx`,
`FramingGateCard.tsx` — this list is from one grep pass, not exhaustive.

This isn't cosmetic. It's exactly the failure mode the design system's own "Implementation
Note (Critical)" section warns about: raw Tailwind color utilities can't be swapped by a
future palette/theme change the way `severity-critical`/`severity-warning`/
`severity-opportunity` can, and it means two different components can disagree about which
shade of red means "critical" if either drifts.

**Recommendation:** a mechanical sweep, one file at a time — swap `text-red-400` →
`text-severity-critical`, `text-amber-400` → `text-severity-warning`,
`text-emerald-400`/`text-green-400` → `text-severity-opportunity`/`text-severity-healthy`
(check which semantic meaning each site actually intends — opportunity vs. healthy differ in
meaning even though DESIGN_SYSTEM.md currently gives `healthy`/`info` the same underlying
value). Low risk, no layout change, directly checkable against the doc's own token table.
Tier 1 below.

### 4.2 No visible client indicator

Already named in project memory before this audit, still true: nothing in `AppHeader.tsx`
shows which client dataset is active (lubricants vs. bicycle vs. hess vs. apex). Checked
directly — no `client_id` reference anywhere in that component. A tester moving between demo
clients has no way to tell which one they're looking at without checking the principal
dropdown's contents. Small, contained fix; Tier 2 below.

### 4.3 Variance breakdown disclosure depth — an open design question, not a bug

`DeepFocusView`'s Variance Breakdown accordion reveals up to 59 segments flat on one click.
This is a correct application of "collapsible accordions ensures the screen is never
overwhelming" as far as it goes — but the brand doc specifies *that* disclosure should be
progressive, not *how many levels* it should have. One level (collapsed → all 59 flat) and two
levels (collapsed → top-N → "see all") are both consistent readings of the same sentence.
Nothing in either governing doc settles which is right for a screen at this specific density.
**Recommendation:** flag as a real open call, not something this audit should resolve
unilaterally — matches the "needs real design judgment, not a mechanical fix" category named
in conversation. Tier 3 below.

### 4.4 Settings tab bar density — already tracked, cross-referenced not duplicated

`DEVELOPMENT_PLAN.md`'s "Known tech debt" table already carries this: 10 horizontal tabs in
Settings, trigger for a left-hand hierarchical nav refactor already crossed (>7 sections), a
suggested 5-group taxonomy already sketched (Workspace / Data / Decision Registry / People /
Governance). Not re-scoped here — listed as Tier 4 for sequencing only.

---

## 5. Prioritized sequence

| Tier | Item | Why this order |
|---|---|---|
| **1** | Severity-token color sweep (§4.1) | Mechanical, no logic/layout change, directly checkable against the doc's own token table, highest file count so highest latent-drift risk if left alone |
| **2** | Client indicator badge in `AppHeader` (§4.2) | Small, contained, closes a known demo-confusion gap |
| **3** | Variance breakdown disclosure depth decision (§4.3) | Needs a call, not just code — resolve the question before building either answer |
| **4** | Settings tab bar hierarchical nav (§4.4) | Already scoped in `DEVELOPMENT_PLAN.md`; larger, cross-cutting, sequenced last on purpose |

---

## 6. What this plan is not

Not a redesign, and not a substitute for the real UI/UX expertise named directly in
conversation this session ("the UI needs a real expert UI designer to think through what
information to present..."). Everything in §4.1–4.2 is mechanical compliance work checkable
against documents that already exist. §4.3 is explicitly flagged as needing judgment this
audit doesn't presume to supply on its own. §4.4 is pre-existing scoped work, not new. If the
gap named earlier in conversation is about *information architecture and layout taste*
generally — what's on-screen by default vs. behind a click, across the whole app, not just the
specific screens audited here — that remains open and is a different, larger piece of work
than this document covers.
