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
| `AppHeader` | `AppHeader.tsx` | `selectedPrincipal, availablePrincipals, onSelectPrincipal, loading, onRefresh, statusMsg?` | Top nav bar — every view |
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
Used on KPITile and HeroBriefing — `group` on parent, `group-hover:opacity-100 opacity-0` on overlay:
```tsx
<div className="group relative ...">
  {/* content */}
  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none ...">
    Analyze →
  </div>
</div>
```

### Accordion section
Used in DeepFocusView for collapsible analysis sections. State managed with `Set<string>` of open section IDs.

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
