# UI Refinement Plan

**Created:** 2026-08-21
**Updated:** 2026-08-22 — added §7 (external-input review) and §8 (live Playwright findings)
**Status:** Tiers 1-6 built. Tiers 7-8 open. See §5 for per-tier state (verified 2026-08-27).
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

State verified against source 2026-08-27, not against this table's own prior claims.

| Tier | Item | State |
|---|---|---|
| **1** | Portfolio direct-nav error + `Test Probe` principal (§8.1) | **Done** — neither string exists in the tree |
| **2** | Severity-token color sweep (§4.1) | **Done, 2026-08-27.** 742 sites converted across 52 files (55 → 797 `severity-*` uses). Four Persuade-mode marketing pages and two documented pattern classes were deliberately left as literal Tailwind colors — see the write-up below, not a gap. A permanent lint (`scripts/severity_token_lint.py`, wired into `.pre-commit-config.yaml`) now fails any new hardcoded occurrence, so this does not need re-auditing. |
| **3** | Colour-encoding collision on KPI tiles (§8.2) | **Done** — `chartTrendIsGood` drives the sparkline stroke |
| **4** | Client indicator badge (§4.2) | **Done** — fell out of the nav work as predicted (`LeftNav.tsx`) |
| **5** | Persistent `ANALYZE` affordance + stray `0` fix (§8.3) | **Done** — label unconditional; guard coerced with `Boolean()` |
| **6** | Variance breakdown ranking + humanised labels (§8.4) | **Done** |
| **7** | Dashboard entry point into `ProblemRefinementChat` (§7.2) | **Open** — still one call site, in `DeepFocusView` |
| **8** | Dark/light theme toggle — accessibility (§7.1) | **Open** — no theme machinery in the tree |

### §8.5 was never given a tier — **fixed 2026-08-27**

The fabricated sparkline. `KPITile.tsx` synthesised a 9-point quadratic curve from a single
`percent_change` when `monthly_values` was absent, rendered it identically to real data, and drew a
mean baseline computed from the invented numbers — undetectable by looking. Dormant on lubricants
(0 of 15 live tiles), and a direct contradiction of "The Chart is the Receipt" on a surface whose
entire claim is that the chart is proof.

The fallback is deleted. Fewer than two measured points now renders no chart at all. A blank space
costs less than an unfalsifiable one.

### Severity token sweep — what was converted, what wasn't, and why (2026-08-27)

**Converted: 742 sites, 52 files, mechanically.** Every `{prefix}-{red|amber|emerald|green}-{shade}` on
screen (not `print:`) mapped 1:1 by hue — red→critical, amber→warning, emerald→opportunity,
green→healthy — preserving any alpha modifier. This is the exact transform `DESIGN_SYSTEM.md` §1
already prescribes: since each token is a single fixed shade, `bg-red-700/40` → `bg-severity-critical/40`
is not a shade-number swap, it's the alpha-modifier idiom the doc's own usage examples show.

**Two real bugs found and fixed mid-sweep, both by rendering, not by reading the diff:**
- A first version of the script substituted per *line* rather than per *match*, converting print-scoped
  colors that shared a line with a screen color (e.g. `bg-amber-950/20 ... print:bg-amber-50` both became
  `severity-warning`). Caught before commit; the whole sweep was reverted and rerun with match-level
  print detection.
- A second version dropped the line-level gating that kept "light badge" patterns
  (`bg-green-100 text-green-800`) out of scope, converting some of them anyway. Since severity tokens are
  a single shade, `bg-severity-healthy text-severity-healthy` collapses background and text to the
  identical color — **invisible text**. Caught live on `Portfolio.tsx`'s VALIDATED/FAILED verdict pills
  (blank colored bars where "Validated"/"Failed" should read). Isolated to 9 true collisions
  (`bg-severity-X` + `text-severity-X`, both solid, no alpha) across 3 files and fixed by adding a `/20`
  tint to the background only — the documented idiom, not a new pattern.

**Deliberately excluded, not silently declared compliant:**
- **Four Persuade-mode marketing pages** (`LandingPage.tsx`, `LandingPageAlternate.tsx`,
  `HowItWorks.tsx`, `InsightsBIModernization.tsx`, 64 occurrences) — `ui_brand_guidelines.md` §5 requires
  these to share the app's *style*, not its severity CSS variables; coupling a landing page's accent
  color to "what counts as a critical KPI" would make a rebrand of either one break the other.
  `AgentAnimations.tsx` is the one exception inside that boundary: it renders a live mock-up of the real
  app's severity UI for the "how it works" explainer, so it was converted to stay visually identical to
  what it's demonstrating.
- **104 `print:` occurrences** — a severity token is one fixed shade; print needs a different, lighter
  or darker shade for contrast on white paper. Forcing the single screen value onto paper would either
  wash out or over-darken text depending on direction. Left as literal colors; not covered by the lint.
- **67 "light badge" occurrences** (`bg-X-100 text-X-800`, screen only) — same single-shade problem as
  above, this time on a light chip on a dark page. This is arguably its own defect (a light island on a
  dark-first surface, the same class of issue fixed in `CostOfInactionBanner`), not merely an unconverted
  token. Flagged as a follow-up, not fixed here — redesigning ~20 badge call sites to the dark-tinted
  idiom is a larger, more visible change than a token rename and deserves its own review.
- **Two hand-reviewed categorical exceptions**: `Login.tsx`'s decision-style archetype badges
  (analytical/visionary/pragmatic/decisive → blue/purple/emerald/amber) are an identity palette, not a
  severity indicator — same shape as the persona-lens palette removed from `ExecutiveBriefing.tsx`
  earlier in this sweep. Marked with `// severity-lint-allow:` rather than silently skipped.

**New, unrelated finding surfaced by a pixel probe, not the sweep itself:** `PortfolioDashboard.tsx`'s
`PARTIAL` verdict uses `text-yellow-400` — Tailwind's `yellow`, not `amber` — which is neither a
severity token nor covered by this lint's four governed hues at all. Not fixed here; flagged for a
follow-up decision on whether "yellow" should exist in this palette.

### Executive Briefing composition pass (2026-08-27)

Not from this document's backlog. A `/impeccable critique` of the Executive Briefing scored it
**19/40 — Poor** (7 of 8 cognitive-load checks failing) after nine consecutive feature-layering
commits with no design review between any of them. Fixes are recorded in
`executive_briefing_redesign.md` under "Build state". Measured before/after, real data, six
viewports:

| Metric | Before | After |
|---|---|---|
| Briefing pane width @ 390px | **70px** | 390px |
| Workspace rail width @ 390px | 320px (fixed at every width) | full-width, stacked |
| Blocks above the fold | 7 | 3 |
| Contradiction visible in first viewport | no | yes |
| `<h1>` count | 0 | 1 |
| Scroll height (Decision Maker, collapsed) | 6,635px | 5,632px |
| Worst measured text contrast | 1.95:1 | 3.07:1 |
| Console errors | 0 | 0 |

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
