# UI Refinement Plan

**Created:** 2026-08-21
**Updated:** 2026-08-22 — added §7 (external-input review) and §8 (live Playwright findings)
**Status:** Design note — audit complete, fixes not yet built (except where marked)
**Scope:** Originally compliance-and-cleanup against the design language that already exists
(§1–§6). §8 goes beyond that: it records defects found by driving the running app, several of
which are not compliance questions at all. The "not a redesign" boundary in §6 still holds for
this document — the redesign work it anticipated now exists as four separate design notes, listed
in §9.

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

### 4.4 Settings tab bar density — ~~already tracked~~ **STALE, corrected 2026-08-22**

This entry (and `DEVELOPMENT_PLAN.md:119`, which it cross-referenced) described Settings as having
10 horizontal tabs needing a left-hand hierarchical nav refactor. **That refactor already shipped.**
`decision-studio-ui/src/components/SettingsLayout.tsx` (304 lines) renders a two-pane layout with an
`<aside className="w-56 ...">` sidebar and grouped nav; no horizontal tab strip remains in
`RegistryExplorer.tsx`.

Genuinely still open, and now owned by `collapsible_left_nav_design.md`:
- the shipped sidebar is **not collapsible** (static `w-56`, no toggle)
- it is **Settings-only** — no other section has real navigation
- **three competing taxonomies** exist: shipped maintenance nav uses Registry / Intelligence /
  Ownership / Workspace (`SettingsLayout.tsx:44-79`), governance mode uses Strategic / Registry /
  Assessment, and `DEVELOPMENT_PLAN.md:119` still proposes Workspace / Data / Decision Registry /
  People / Governance — a taxonomy that was never built

---

## 5. Prioritized sequence

Reordered 2026-08-22. Demo-blocking defects from §8 take precedence over the original mechanical
compliance work — a raw developer error on a route and a test record on the login screen are worse
than an inconsistent token.

| Tier | Item | Why this order |
|---|---|---|
| **1** | Portfolio direct-nav error + `Test Probe` principal (§8.1) | Demo-blocking, both small, both visible within the first minute of any walkthrough |
| **2** | Severity-token color sweep (§4.1) | Mechanical, no logic/layout change, directly checkable against the doc's own token table, highest file count so highest latent-drift risk if left alone |
| **3** | Colour-encoding collision on KPI tiles (§8.2) | A card whose number is red and whose chart is green is self-contradictory; same design-system rule as Tier 2, but a real misread risk rather than latent drift |
| **4** | Client indicator badge (§4.2) | Small, contained, closes a known demo-confusion gap — may fall out of `collapsible_left_nav_design.md` for free |
| **5** | Persistent `ANALYZE` affordance + stray `0` fix (§8.3) | Two small, unambiguous fixes |
| **6** | Variance breakdown: rank by explanatory power, humanise column labels (§8.4) | Supersedes the §4.3 disclosure-depth question — the depth was never the real problem |
| **7** | Dashboard entry point into `ProblemRefinementChat` (§7.2) | Closes a discoverability gap without new NL infrastructure |
| **8** | Dark/light theme toggle — accessibility (§7.1) | Additive, opt-in, lowest priority |

~~Settings tab bar hierarchical nav~~ — shipped; remaining collapse/taxonomy work moved to
`collapsible_left_nav_design.md` (§4.4).

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

**Update 2026-08-22:** that larger piece of work now exists as four separate design notes — see §9.

---

## 7. External-input review (2026-08-22)

A general "best practice executive dashboard" recommendation was obtained from an external LLM and
reviewed against what this codebase actually decided. Recorded so the same generic advice isn't
re-adopted later without the reasoning that closed it.

### 7.1 Light canvas vs. dark-first Swiss style — **rejected, with one accepted carve-out**
`ui_brand_guidelines.md:16-18` treats deep slate/charcoal as brand identity, not an incidental
dark-mode default. Generic advice that doesn't know the brand isn't evidence of a problem.
**Accepted separately:** an opt-in dark/light toggle as an *accessibility* affordance for
visually-impaired users. This does not reopen the default. Tier 8.

### 7.2 Persistent global "ask the data" bar — **rejected; narrower fix accepted**
Conflicts with `hitl_decision_philosophy.md:170-171` ("Not a chatbot... not a general-purpose
conversational interface"), and there is no general NL→SQL layer to back it — DPA/NLP are thin
adapters by deliberate product direction. An always-on box that can't answer most of what it invites
is worse than none. **Accepted:** the real complaint is discoverability — `ProblemRefinementChat` is
only reachable after drilling into a situation. A dashboard-level entry point routing into the
*existing scoped* chat closes it without new infrastructure. Tier 7.

### 7.3 Role-differentiated views — **already satisfied, plus a genuinely deferred piece**
KPI-ownership filtering is already live (`_get_relevant_kpis` filters on `kpi_accountability`).
Regional/dimensional scoping ("EMEA VP sees EMEA") is the genuinely deferred part —
`scope_dimension`/`scope_value` columns exist but the filter doesn't consult them
(`raci_accountability_model.md:219-221`). **Out of scope for this document** — it is registry/backend
design owned by `raci_accountability_model.md` and Phase 12B. Not a UI gap.

### 7.4 Scope correction — see §4.4.

### 7.5 Scenario / forecast selector — **rejected as product scope**
SA already runs multiple always-on comparison lenses per KPI (11I-A: `threshold_breach`,
`plan_variance`, `projected_breach` — a real forward extrapolation — and `acceleration`), and SF's
3-option trade-off matrix already delivers "multiple quantified paths with different ROI and risk."
What neither does is user-directed Base/Upside/Downside hypotheticals over *external conditions*.
**Decision: no forecasting or scenario-planning functionality in Agent9 for now** — a deliberate
product-scope boundary, not a scheduling deferral.

---

## 8. Live findings — Playwright pass, 2026-08-22

Driven against the running stack with real lubricants data. Artifacts:
`decision-studio-ui/scratchpad/ui_review/` and `scratchpad/sf_run2/`. **Zero console errors across
the whole session** — every item below is a design or data defect, not a JS failure.

### 8.1 Demo-blocking
- **`/portfolio` renders a raw developer error on direct navigation:** *"Failed to load portfolio —
  No principal ID provided. Add `?principal=cfo_001` to the URL."* Leaks the internal ID format,
  instructs the user to hand-edit a URL, breaks bookmarks and refresh.
- **`Test Probe / Test Title` is a selectable identity on the login screen** and appears again in
  Context Explorer. Registry hygiene, visible in the first five seconds of a demo.

### 8.2 Colour encodings collide on KPI tiles
The large percentage renders red for nearly every tile (tracking *severity*) while the sparkline
renders green (tracking *direction*) — so `+3.3%` appears in red directly above a rising green area
chart. One colour channel doing two contradictory jobs, against DESIGN_SYSTEM's own "colour is
scarce, strictly semantic" rule.

### 8.3 Two small, unambiguous defects
- **`ANALYZE →` is hover-gated** (`opacity-0` until `group-hover`). On a page of 15 cards the primary
  action is invisible until hovered, and unreachable on touch. Confirmed by Playwright being unable
  to click it without hovering first.
- **A stray `0` renders in the Action Center.** `ProblemRefinementChat.tsx:451-452` —
  `{(a?.length || b?.length || c?.length || d?.length) && (...)}` evaluates to `0` when all four are
  empty, and React renders it as a text node. Fix: `Number(...) > 0 &&` or a `!!` wrap.

### 8.4 Variance Breakdown says nothing
Every dimension row (`CUSTOMER_REGI…`, `PRODUCT_LINE`, `PRODUCT_NAME`, `CUSTOMER_NAME`,
`CHANNEL_NAME`, `CHANNEL_TYPE`, `PRODUCT_CATEG…`) displays the **same** `+$5.5M`. Arithmetically
fine — it's one total decomposed seven ways — and analytically useless: it doesn't say which
dimension *explains* the variance. Rows should rank by explanatory power. Separately, those are raw
database column names in UPPER_SNAKE_CASE, truncated mid-word.

**This supersedes §4.3.** The open question there was disclosure *depth* (one level vs. two). Depth
was never the problem; the rows carry no discriminating information at any depth.

### 8.5 Latent, not currently firing
`KPITile.tsx:118-131` fabricates a 9-point quadratic curve from a single `percent_change` when
`monthly_values` is absent, rendered identically to real data — including a dashed "mean baseline"
computed from invented numbers. **Probed all 15 live tiles: 0 of 15 synthetic**, so it isn't biting
on lubricants today. But it is undetectable if it ever does, and it contradicts "The Chart is the
Receipt" directly.

### 8.6 Not UI problems — filed to their real owners
Found in the same pass; recorded here only so they aren't rediscovered as UI issues. Owned in
`DEVELOPMENT_PLAN.md` against the agents that produce them.

| Finding | Owner |
|---|---|
| 14 of 15 KPIs flagged CRITICAL — severity doesn't discriminate | SA threshold calibration |
| Net Revenue `+3.3%` = CRITICAL while Product Sales `+3.3%` = HIGH; the displayed number isn't the alert driver | SA / KPI tile data contract |
| "Raw Materials Cost is **over-performing**" for a cost up 22.3% and flagged critical | DA prose, polarity-unaware |
| Council converges (three near-verbatim hypotheses, all "High conviction") but renders as three independent opinions | SF / persona design |
| Two options modelled at an identical recovery range | SF synthesis quality |
| `opt_1`/`opt_2`/`opt_3` leaking into executive-facing prose | SF output hygiene |
| `MCKINSEY`/`BCG`/`BAIN` still rendered on the Council Debate page | Phase 18 Category C |

---

## 9. The redesign work this document anticipated

§6 said the wider information-architecture question was "a different, larger piece of work." It now
has four design notes:

- `decision_framer_and_decision_maker_personas_design.md` — two principal workflow roles
- `executive_briefing_redesign.md` — one briefing, two default disclosure states
- `collapsible_left_nav_design.md` — one nav for the whole app (owns the §4.4 remainder)
- `refinement_iteration_and_session_persistence_design.md` — refinement rounds and resume
- `audit_event_system_design.md` — persisted diagnostics (not UI-scoped, but requested in the same
  pass)
