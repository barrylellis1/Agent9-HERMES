# Decision Studio — Design System

**Last updated:** 2026-05-23  
**See also:** [`docs/architecture/ui_brand_guidelines.md`](../docs/architecture/ui_brand_guidelines.md) — brand voice, Swiss Style aesthetic, adaptive contextualization

---

## 1. Severity Semantic Tokens

The single most important design-system rule. **Never hardcode color classes for semantic meaning.** Always use the `severity-*` token group.

### Tokens

| Token | Tailwind class | CSS variable | Value | Meaning |
|---|---|---|---|---|
| critical | `severity-critical` | `--color-severity-critical` | `248 113 113` (red-400 `#f87171`) | Threshold breach, FAILED, destructive |
| warning | `severity-warning` | `--color-severity-warning` | `251 191 36` (amber-400 `#fbbf24`) | Medium severity, caution |
| opportunity | `severity-opportunity` | `--color-severity-opportunity` | `52 211 153` (emerald-400 `#34d399`) | Upside, positive variance, VALIDATED |
| healthy | `severity-healthy` | `--color-severity-healthy` | `74 222 128` (green-400 `#4ade80`) | Within normal range, low severity |
| info | `severity-info` | `--color-severity-info` | `74 222 128` (green-400 `#4ade80`) | Informational (same value as healthy) |

### Usage

```tsx
// Border accent
<div className="border-l-[3px] border-l-severity-critical" />

// Text
<span className="text-severity-opportunity">+12.4%</span>

// Background with opacity modifier
<div className="bg-severity-critical/10 border border-severity-critical/20" />

// Dot indicator
<span className="w-1.5 h-1.5 rounded-full bg-severity-warning" />
```

### Implementation Note (Critical)

Two-part contract — **both** must be correct or border/ring utilities silently break:

**1. CSS variables** store raw RGB channel values (no `rgb()` wrapper):
```css
/* CORRECT — raw channels so Tailwind can compose rgb(var(...) / alpha) */
--color-severity-critical: 248 113 113;

/* WRONG */
--color-severity-critical: #f87171;
--color-severity-critical: rgb(248, 113, 113);
```

**2. tailwind.config.js** must use `rgb(var(...) / <alpha-value>)` format — NOT bare `var(...)`:
```js
/* CORRECT — enables text-, bg-, border-l-, ring- etc. with opacity modifiers */
severity: {
  critical: "rgb(var(--color-severity-critical) / <alpha-value>)",
}

/* WRONG — border-l-severity-critical resolves to `border-left-color: 248 113 113` (invalid CSS) */
severity: {
  critical: "var(--color-severity-critical)",
}
```

The `<alpha-value>` placeholder is replaced by Tailwind with the actual opacity value (e.g. `1` for solid, `0.1` for `/10` modifier).

**Tailwind JIT and new files:** When adding new components in new files, Tailwind JIT may not pick up `severity-*` classes immediately, even after restart. Use inline styles with hardcoded RGB as a fallback:

```tsx
// Safe fallback when JIT hasn't picked up the class
style={{ color: 'rgb(248 113 113)' }}   // critical
style={{ color: 'rgb(251 191 36)' }}    // warning
style={{ color: 'rgb(52 211 153)' }}    // opportunity
```

### Enforcement (2026-08-27)

`scripts/severity_token_lint.py`, wired into `.pre-commit-config.yaml`, fails any new hardcoded
`red/amber/emerald/green` on screen. 742 pre-existing sites were swept to tokens the same day (55 →
797 uses); full write-up, including two real bugs found by rendering rather than reading the diff, is
in `docs/architecture/ui_refinement_plan.md` under "Severity token sweep."

**A single token is one fixed shade — this has two consequences, both learned the hard way:**

1. **Never pair `bg-severity-X` and `text-severity-X` both solid (no alpha) on one element.** They
   render as the identical color — invisible text. This exact bug shipped mid-sweep on `Portfolio.tsx`'s
   verdict pills (blank pills where "Validated"/"Failed" should read) and was only caught by rendering
   the page, not by reading the diff. If text needs to sit on a same-hue background, tint the background
   (`bg-severity-X/20`), never both solid.
2. **A light badge (`bg-X-100 text-X-800`) cannot be token-swapped directly** — it relies on two
   *different* shades for contrast, and the token only has one. ~20 such call sites remain deliberately
   unconverted (tracked in `ui_refinement_plan.md`, not silently declared compliant); redesigning them to
   the dark-tinted idiom is a separate, larger change than a token rename.

Two exception classes are permanent, not technical debt: `print:` variants (paper needs different
literal shades than the single screen token provides) and the four Persuade-mode marketing pages
(`LandingPage.tsx`, `LandingPageAlternate.tsx`, `HowItWorks.tsx`, `InsightsBIModernization.tsx` — their
accent color is a brand choice, not a KPI-severity indicator, and coupling the two would make a rebrand
of either break the other).

---

## 2. Color Palette

Dark-first. Color is scarce — used only for semantic meaning.

### Base Surface Stack (slate)

| Usage | Tailwind | Hex approx |
|---|---|---|
| Page background | `bg-slate-950` | `#020617` |
| Card / panel | `bg-slate-900` | `#0f172a` |
| Card hover | `bg-slate-800/90` | `#1e293b` |
| Subtle fill | `bg-slate-900/50` | semi-transparent |
| Border | `border-slate-800` | `#1e293b` |
| Border subtle | `border-slate-700` | `#334155` |
| Divider | `divide-slate-800` | |

### Text Hierarchy

| Role | Tailwind | Usage |
|---|---|---|
| Primary | `text-white` | Headings, hero numbers, key values |
| Secondary | `text-slate-300` | Body copy, analysis text |
| Tertiary | `text-slate-400` | Labels, supporting context |
| Muted | `text-slate-500` | Metadata, timestamps |
| Disabled | `text-slate-600` | Inactive, decorative |

### Action / AI Colors

| Usage | Tailwind | Note |
|---|---|---|
| AI action / CTA | `indigo-400` / `indigo-600` | Refinement, Generate Solutions, Solution Active badge |
| AI recommendation | `purple-400` / `purple-600` | Council recommendations, AI-authored output |
| System processing | `blue-400` | Loader, analyzing states |
| Destructive | `severity-critical` | Delete, FAILED, errors |

---

## 3. Typography

**Font family:** Satoshi (loaded via CSS), fallback: `system-ui`, `-apple-system`, `sans-serif`

### Scale in Use

| Role | Classes | Usage |
|---|---|---|
| Page title | `text-2xl font-bold text-white` | Hero KPI name in HeroBriefing |
| Section heading | `text-lg font-semibold text-white` | Accordion headers, "Priority Briefings" |
| Card heading | `text-base font-semibold text-white` | KPI tile name |
| SCQA recommendation | `text-lg font-medium text-white leading-relaxed` | Answer-first BLUF |
| Hero deviation | `text-5xl font-mono font-bold tracking-tight` | HeroBriefing hero number |
| Tile deviation | `text-3xl font-mono font-bold tracking-tight` | KPITile hero number |
| Body | `text-sm text-slate-300 leading-relaxed` | Analysis text, descriptions |
| Label | `text-xs font-semibold uppercase tracking-wider text-slate-500` | Section labels, badges |
| Micro | `text-[11px]` / `text-[10px]` | Badges, chip labels, action hints |

**Mono font:** `font-mono` — used for all numeric values (deviations, KPIs, deltas)

---

## 4. Spacing Conventions

| Context | Pattern |
|---|---|
| Page padding | `p-8` (32px) |
| Card padding | `p-5` to `p-6` |
| Section gap | `space-y-8` between major sections |
| Card gap | `gap-4` (secondary grid) / `gap-6` (primary grid — deprecated in favour of 4) |
| Inline gap | `gap-2` to `gap-3` |
| Border radius | `rounded-xl` (cards), `rounded-lg` (inner panels), `rounded` (small) |
| Border accent | `border-l-[3px]` (left accent bar on tiles and hero) |

---

## 5. Component Library Index

### Shared (`src/components/shared/`)

| Component | File | Props | Usage |
|---|---|---|---|
| `AppShell` | `AppShell.tsx` | `children` | App-wide layout wrapper — `LeftNav` + content pane. Pages wrap themselves in it (no nested-route layout); see the component's own docstring for why |
| `LeftNav` | `LeftNav.tsx` | none (reads `localStorage`/`settingsMode` itself) | Primary nav rail — Situations / Portfolio / Context / Settings, width-collapse (see §7) |
| `AppHeader` | `AppHeader.tsx` | `selectedPrincipal, availablePrincipals, onSelectPrincipal, loading, onRefresh, statusMsg?` | Dashboard-local header — principal selector + scan control (global nav/branding live in `LeftNav` now) |
| `PrincipalSelector` | `PrincipalSelector.tsx` | `principals, selectedId, onSelect` | Principal dropdown with "Viewing as" context cue |
| `SummaryStrip` | `SummaryStrip.tsx` | `kpisScanned, breachCount, impactLevel, impactColor, situations` | Single-line scan results strip |
| `SolutionsProgressBar` | `SolutionsProgressBar.tsx` | `portfolio, selectedPrincipal` | VA solutions segmented bar + legend |

### Dashboard (`src/components/dashboard/`)

| Component | File | Props | Usage |
|---|---|---|---|
| `HeroBriefing` | `HeroBriefing.tsx` | `situation, onClick, isDelegated?, hasActiveSolution?` | Full-width lead finding tile |
| `KPITile` | `KPITile.tsx` | `situation, onClick, isDelegated?, hasActiveSolution?` | Secondary grid tiles; hover reveals "Analyze →" |

### Views (`src/components/views/`)

| Component | File | Description |
|---|---|---|
| `DashboardView` | `DashboardView.tsx` | SA Console — hero + secondary grid + summary strip |
| `DeepFocusView` | `DeepFocusView.tsx` | DA view — accordion sections + collapsible Action Center |

### Visualizations (`src/components/visualizations/`)

| Component | File | Usage |
|---|---|---|
| `IsIsNotExhibit` | `DivergingBarChart.tsx` | IS / IS NOT diverging bar chart |
| `TrajectoryChart` | `TrajectoryChart.tsx` | VA solution trajectory (expected vs actual vs inaction) |
| `TradeOffAnalysis` | `TradeOffAnalysis.tsx` | Solution option trade-off matrix |
| `VarianceCharts` | `VarianceCharts.tsx` | Variance breakdown charts |

### Other Components

| Component | File | Usage |
|---|---|---|
| `CostOfInactionBanner` | `CostOfInactionBanner.tsx` | CoI projection (Executive Briefing; pending F7 for DeepFocusView) |
| `ValueAssurancePanel` | `ValueAssurancePanel.tsx` | VA tracking panel |
| `PortfolioDashboard` | `PortfolioDashboard.tsx` | VA portfolio table |
| `AttributionBreakdown` | `AttributionBreakdown.tsx` | DiD attribution breakdown |
| `CouncilDebate` | `CouncilDebate.tsx` | Stage 1/2/3 debate view |
| `ProblemRefinementChat` | `ProblemRefinementChat.tsx` | Refinement conversation UI |
| `BrandLogo` | `BrandLogo.tsx` | Aperture mark + Decision Studio wordmark |
| `OpportunityCard` | `OpportunityCard.tsx` | Opportunity signal card (uses `severity-opportunity`) |

---

## 6. Utility Functions

| Utility | File | Usage |
|---|---|---|
| `formatExecutive(value, currency?, forceSign?)` | `src/utils/formatExecutive.ts` | `-189051582 → -$189.1M` — all financial display |
| `formatCompact(value)` | `src/utils/formatExecutive.ts` | Absolute display without sign: `189.1M` |

---

## 7. Common Patterns

### Hover-reveal action overlay
Used on KPITile and HeroBriefing — `group` on parent, `group-hover:opacity-100 opacity-0` on the
**decorative gradient scrim only**. The action label itself must render unconditionally: hover-gating
the label (not just the scrim) meant the tile's primary action was invisible across a full grid and
unreachable on touch — found live, Aug 2026. Decoration is hover-only; the affordance is not:
```tsx
<div className="group relative ...">
  {/* content */}
  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none ...">
    {/* gradient scrim only — decoration */}
  </div>
  <span className="absolute inset-x-0 bottom-0 ...">
    Analyze → {/* always visible — the affordance */}
  </span>
</div>
```

### Accordion section
Used in DeepFocusView for collapsible analysis sections. State managed with `Set<string>` of open section IDs.
This is **content collapse** — a panel's contents hide in place, the panel itself doesn't change size.
See "Width-collapse nav" and "Group-collapse nav" below for the other two collapse families.

### Width-collapse nav (`LeftNav`)
The app-wide nav rail (`src/components/shared/LeftNav.tsx`, wrapped via `AppShell.tsx`) collapses by
shrinking its own width, not by hiding content in place — a different pattern from the accordion
above, introduced 2026-08-25 (first precedent in the codebase). Two states, both fixed widths so the
transition is a clean `transition-[width]`, not a reflow:

| State | Width | Shows |
|---|---|---|
| Expanded | `w-56` | icon + label (+ the Settings sub-tree, see below, if active) |
| Collapsed | `w-14` | icon rail only, `title` attribute for a native tooltip, sub-tree hidden |

State persists per-viewer in `localStorage` (`a9_nav_collapsed`), read once at mount inside a
`try/catch` (private browsing / blocked storage falls back to expanded, never throws). Apply this
pattern — not a new accordion — to any future component that needs to reclaim horizontal space
without losing its content entirely (e.g. a collapsible detail rail).

`LeftNav` briefly had a same-day sibling: `SettingsLayout` rendered its own second full-height
sidebar immediately to the right of this one, each anchoring its own brand mark — live-caught by a
user screenshot within hours of shipping. That sidebar's entire nav tree (types, `MAINTENANCE_NAV`/
`GOVERNANCE_NAV`, the onboarding step list) moved into `LeftNav.tsx` the same day and renders indented
directly beneath the "Settings" destination whenever a `/settings/*` route is active — one panel, not
two. `SettingsLayout` is now a one-line pass-through of `AppShell`. **There is exactly one `<aside>`
in this app now; if a future change reintroduces a second one, that's the same defect recurring.**

### Group-collapse nav (`LeftNav`'s `SettingsGroupNav`)
A third collapse family, distinct from both above — a *list of groups* collapses independently, not
the whole panel's width and not one panel's contents as a unit. Introduced 2026-08-25 when
Maintenance mode's Registry/Intelligence/Ownership/Workspace (14 leaf items across 4 groups) forced
an internal scrollbar rendered flat — found live, testing as a Maintenance-mode principal for the
first time this session.

- The group containing the **current page always renders open**, regardless of stored state — this
  nav must never hide the page you're already on.
- Manually-opened groups persist across navigation in `localStorage`
  (`a9_settings_nav_open_groups`, a JSON array of group names) — necessary here, unlike a plain
  accordion, because each Settings page wraps itself in a fresh `<SettingsLayout>` (same
  self-wrapping pattern as `AppShell`), so `LeftNav` remounts on every route change within Settings.
  Component-local state alone would silently re-collapse a group the moment you clicked one of its
  own links.
- Reach for this pattern (not the accordion, not width-collapse) whenever a **flat list of items is
  itself long enough to need grouping** — the accordion pattern above collapses one section's
  content in place; this collapses *which of several sibling groups* are expanded at once.

### Responsive / breakpoint conventions

**The convention, established on the Executive Briefing 2026-08-27. Follow it; don't improvise
per-component.**

| Pattern | Breakpoint | Rule |
|---|---|---|
| **Two-pane split** (content + fixed-width side rail) | `lg` (1024px) | Stack below it. A 320px rail needs ~1024px before *both* panes have room — at `md` (768px) it leaves the content 448px, narrower than a comparison table's own minimum. |
| **Grid column count** | `sm` / `md` | `grid-cols-2 md:grid-cols-4`, `grid-cols-1 sm:grid-cols-3`. A 4-up metric row is unreadable below `sm`. |
| **Wide tables** | `lg` | Hide below `lg` **only when an equivalent stacked representation already exists** (e.g. per-option cards). If a column has no equivalent — a baseline/status-quo column — render a compact card for it rather than dropping it silently. |
| **Nav bars** | `sm` | `flex-wrap` plus `hidden sm:inline` on button labels, keeping the icon. |

Why `lg` and not the `md` this section previously recommended: `md` is right for *column counts*,
which is what the dashboard grids use it for. It is wrong for a **two-pane split against a fixed
rail**, because the rail's width is absolute while the breakpoint is not.

**What "no responsive layout" actually looked like**, measured before the fix: the Executive
Briefing's rail was `w-80 flex-shrink-0` with no breakpoint at any width. At a 390px viewport that
left the briefing column **70px wide**, rendering the document as a vertical column of one- and
two-character fragments. Nothing in the type system or the tests could see this; it took a render.

**When a fixed-height inner scroll pane becomes a document scroll below a breakpoint, re-check every
`scrollIntoView` on the page.** A chat auto-scroll that was a harmless no-op inside a 320px rail
dragged the whole mobile document to y=8504 of 9786 — the page opened on its own footer. Guard such
effects on *content* (`if (messages.length === 0) return`), never on a `didMount` ref: StrictMode
runs effects twice against the same refs in dev, so a mount flag is already spent by the second
pass. Prefer `block: 'nearest'`, which does nothing when the anchor is already visible.

`LeftNav` remains **rail-only at every width** — it does not yet collapse to an off-canvas drawer;
that is an explicit open item in `collapsible_left_nav_design.md` §5, not an oversight.

### Accessibility baseline (established 2026-08-27)

Before this date `ExecutiveBriefing.tsx` had **0 `aria-*` and 0 `role=`** across 2,000+ lines, and
`prefers-reduced-motion` appeared **0 times in the entire `src` tree**. What the foundation got
right, and what to keep: there were **zero `<div onClick>`** — every control was a real `<button>`,
`<Link>`, or `<input type="radio">` in a `<label>`, so all of them were already keyboard-reachable.
The semantic layer was simply never added on top.

Required on any new page or panel:

- **Disclosure/accordion** — a heading whose only child is the toggle: `<h2><button aria-expanded
  aria-controls>`, with the panel carrying `id`, `role="region"`, `aria-labelledby`. See
  `AccordionSection` in `ExecutiveBriefing.tsx`; ten sections inherit it from one component.
- **Modal / drawer** — `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing at a real
  heading id, `tabIndex={-1}` on the panel, focus moved in on open, Tab trapped, focus restored to
  the trigger on close, `document.body.style.overflow` locked and restored, overlay
  `aria-hidden="true"`. Escape alone is **not** a dialog: it only helps a sighted keyboard user who
  already knows the drawer opened. `OptionDetailDrawer` is the reference implementation.
- **Async state** — `aria-live="polite"` on the region that receives new content, and `role="status"`
  plus an `sr-only` label on every spinner. An icon that spins announces nothing.
- **Icon-only controls** — `aria-label` on the control, `aria-hidden="true"` on the icon.
- **Motion** — `useReducedMotion()` from framer-motion; swap transform-based entrances for a fade.
- **Focus** — `focus-visible:ring-2` on interactive surfaces; the UA default outline disappears
  against `bg-slate-800`.

**Verify behaviourally, not by grep.** Attribute presence proves nothing about focus order. Drive it
in a browser: does focus actually land inside the dialog, does Tab escape it, does Escape restore
focus to the trigger, does the body still scroll behind the overlay.

### Page headline / `<h1>`
Every full-page route owes the document exactly one `<h1>`. The Executive Briefing had **zero** until
2026-08-27 — it named itself only in `text-sm` truncated nav chrome. Where a page leads with a
finding rather than a label, the finding *is* the `<h1>` (`ContradictionBanner`'s `headline`
variant). Do not stack a `text-[10px] uppercase` kicker above it: an eyebrow over a heading is
decoration the heading already earns, and it was how this page previously avoided having a real
title at all.

### Dark-first is not optional per-state
A component with per-state styling must be dark in **every** state. `CostOfInactionBanner` had a
dark `stable` state and light `bg-amber-50` / `bg-emerald-50` states, so it became the brightest
object on a slate-950 page whenever the KPI happened to be moving. Centralize per-state colour in a
single config object rather than repeating ternaries through the render — five scattered ternaries
is how those three states drifted apart. Add `print:` variants there: on paper the light treatment
is correct.

### Answer-first SCQA
`parseScqa(raw: string)` in `DeepFocusView.tsx` extracts S/C/Q/A from the flat backend string. `ScqaBlock` component renders Answer first, hides S/C/Q behind "Show reasoning" toggle.

### Severity border accent
All situation cards (KPITile, HeroBriefing) use `border-l-[3px] border-l-severity-{level}` as the primary severity indicator. Avoid doubling with both border color AND text color in the same badge — border accent is sufficient.

### Market signal source attribution
`formatSignalSource(source, url?)` in `DeepFocusView.tsx` maps `llm_knowledge` → `Analyst synthesis (Claude Sonnet 4.6) · No live citation`. Real sources with URLs get a linked external icon.

---

## 8. What NOT to Do

- Don't use `red-400`, `amber-400`, `green-400`, `emerald-400` for severity — use `severity-*` tokens
- Don't write `rgb()` or hex into CSS variables for severity tokens — use raw channel values
- Don't use `print()` / `console.log` for debugging — remove before committing
- Don't add Tailwind classes to inline-only files without verifying JIT picks them up
- Don't import `openai` or `anthropic` in UI files
- Don't hardcode `http://localhost:8000` in components — use `api/client.ts`
