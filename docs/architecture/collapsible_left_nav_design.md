# Collapsible left navigation — one nav for the whole app

**Created:** 2026-08-22
**Status:** Design note. **Not built.** Smallest and most contained of the current UI threads.

---

## 1. Why this exists

Requested directly: "need a collapsable menu on the left."

Navigation today is fragmented per-page, with no shared mechanism:

- **`/dashboard`** — `AppHeader.tsx` (79 lines) has exactly two forward nav affordances: icon
  links to `/context` and `/settings` (`AppHeader.tsx:70-75`). No link to `/portfolio` anywhere.
  `AppHeader` is rendered in **one place only** (`DashboardView.tsx:103`) — it is not the app's
  header, it is the dashboard's header.
- **`/context`** — its own inline header with only a "Back" link to `/dashboard`
  (`ContextExplorer.tsx:271-277`).
- **`/portfolio`** — its own inline bar using `window.history.back()` (`Portfolio.tsx:476-482`),
  not a route link.
- **`/settings/*`** — its own dedicated sidebar (see §2), plus a "Back to Situation Console" link.

Net effect: **Portfolio and Context Explorer are dead ends with respect to each other.** Reaching
one from the other requires returning to the dashboard or typing a URL. There are no breadcrumbs and
no tabs anywhere.

Found live while testing this: navigating directly to `/portfolio` renders a raw developer error —
*"Failed to load portfolio — No principal ID provided. Add `?principal=cfo_001` to the URL."* It
leaks the internal ID format and instructs the user to hand-edit a URL. Bookmarks and refreshes die
there. (Filed as a bug in `DEVELOPMENT_PLAN.md` tech debt, not fixed by this design, but it is a
symptom of the same absent-navigation problem.)

---

## 2. Correcting a stale assumption

`DEVELOPMENT_PLAN.md:119` and `ui_refinement_plan.md` §4.4 both describe Settings as having "10
horizontal tabs" and call for a left-hand hierarchical nav refactor. **That refactor already
shipped.** `decision-studio-ui/src/components/SettingsLayout.tsx` (304 lines) renders a two-pane
layout with an `<aside className="w-56 ...">` sidebar, and no horizontal tab strip remains in
`RegistryExplorer.tsx`.

What is genuinely still open:

1. It is **not collapsible** — a static `w-56`, no toggle, no rail state.
2. It is **Settings-only** — every other section still has ad-hoc navigation.
3. Its group taxonomy does not match the plan doc. Shipped `MAINTENANCE_NAV`
   (`SettingsLayout.tsx:44-79`) uses **Registry / Intelligence / Ownership / Workspace**; the
   governance-mode nav uses **Strategic / Registry / Assessment**; `DEVELOPMENT_PLAN.md:119` still
   proposes **Workspace / Data / Decision Registry / People / Governance**. Three taxonomies, none
   authoritative.

---

## 3. Scope is small — 4 to 6 items, not 15

`App.tsx` declares 35 `<Route>` entries across 22 page components, but most are marketing, auth or
token-handler pages that do not belong in an authenticated nav (`/`, `/login`, `/landing`,
`/how-it-works`, `/insights/*`, `/data-onboarding`, `/action`, `/delegate`, plus `/admin/*`
redirects).

The real authenticated surface is four sections:

| Item | Route | Notes |
|---|---|---|
| Situations | `/dashboard` | The console; today's default landing |
| Portfolio | `/portfolio` | Approved solutions + VA tracking |
| Context | `/context` | Principals / processes / KPIs / data products |
| Settings | `/settings/*` | Fans out into ~15 sub-sections via `SettingsLayout` |

Deep views (`/debate/:id`, `/briefing/:id`, `/report/:id`) are situation-scoped destinations reached
from within a flow, not nav destinations — they should keep a contextual back affordance rather than
appearing in the nav.

If `decision_framer_and_decision_maker_personas_design.md` lands, a fifth item ("Awaiting my
decision") becomes the Decision Maker's default landing.

---

## 4. Design

**A persistent app-wide left nav**, replacing `AppHeader`'s two icon links and giving every page —
including `/context` and `/portfolio`, which have none — a consistent way to reach every other
section.

**Two states:** expanded (icon + label, ~`w-56` to match the shipped Settings sidebar) and collapsed
(icon rail, ~`w-14`) with labels as tooltips. Persist the state in `localStorage`; it is a per-viewer
convenience, not shared state.

**Settings nesting:** `SettingsLayout`'s existing sidebar becomes the second level, revealed when
Settings is the active section — rather than a second parallel sidebar sitting beside the first.
Two stacked `<aside>` elements would be worse than what exists today.

**Taxonomy:** pick one and correct the other two references (§2.3). Recommendation: keep the
**shipped** `Registry / Intelligence / Ownership / Workspace` grouping, because it is real, in use,
and matches what maintainers already navigate — and update `DEVELOPMENT_PLAN.md:119` to stop
proposing a taxonomy that was never built.

### A pattern that does not exist yet

`DESIGN_SYSTEM.md` documents one collapse pattern — the **accordion**
(`DESIGN_SYSTEM.md:222-223`, "state managed with `Set<string>` of open section IDs", used in
`DeepFocusView`). That is *content collapse* (hide a panel's contents in place). A nav rail is
*width collapse*, which has no precedent anywhere in the codebase. It needs specifying in
`DESIGN_SYSTEM.md` as a new documented pattern, not improvised per-component.

Related gap worth closing in the same pass: `DESIGN_SYSTEM.md` documents **no responsive or
breakpoint conventions at all** (grep for `breakpoint|sm:|md:|lg:` returns nothing). A nav that
must collapse is the natural place to establish them.

---

## 5. Open questions

1. **Does the nav replace `AppHeader` or sit alongside it?** The principal selector, "Scan Now"
   button and last-scanned timestamp are dashboard-specific state. Moving the principal selector to
   a global nav is arguably right (it is global context) but it is currently wired through
   `DashboardView`'s props only.
2. **Where does the client indicator go?** `ui_refinement_plan.md` §4.2 wants a client badge; Settings
   already shows `Client: lubricants` but the dashboard shows nothing. A global nav is the natural
   home — which would close that Tier 2 item as a side effect.
3. **Mobile/narrow behaviour** — off-canvas drawer, or always-rail? Needs the breakpoint conventions
   from §4 first.

---

## 6. Related documents

- `ui_refinement_plan.md` §4.2 (client indicator), §4.4 (the stale Settings item this corrects),
  §8 (the empirical nav findings)
- `DEVELOPMENT_PLAN.md:119` — the stale tech-debt line requiring correction
- `decision_framer_and_decision_maker_personas_design.md` — may add a fifth nav item
- `decision-studio-ui/DESIGN_SYSTEM.md` — needs the width-collapse pattern and breakpoint
  conventions added
