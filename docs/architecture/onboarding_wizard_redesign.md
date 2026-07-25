# Onboarding Flow Redesign — Implementation Spec

Handoff doc for Claude Code. Source of truth for visual/interaction design is the
prototype `Onboarding Wizard Prototype.dc.html` (static, no real API calls) — this
doc translates it into wiring instructions against the real
`decision-studio-ui` React app in `barrylellis1/Agent9-HERMES`.

**Status:** Approved for implementation (2026-07-14). Supersedes the "Guided onboarding
flow (4 steps)" deliverable described in `DEVELOPMENT_PLAN.md`'s Infra A2 section — that
deliverable is now realized as the 6-step wizard described below instead of a 4-step flow.
The concrete, codebase-verified implementation plan (route reshuffle, per-component embed
changes, backend aggregator endpoint, RLS/Infra B3 compliance notes) lives in the plan
history for this feature; this document retains the original product spec for reference.

## 1. What's changing and why

Today, admin onboarding (`OnboardingDayView.tsx` + `SettingsLayout.tsx`) is a
6-day sidebar with each day showing a summary card, a list of action `Link`s, and
static tips. Problems being fixed:

- No single obvious primary action — actions render as a plain list of links,
  easy to miss which one to click first.
- No resume affordance — returning to `/settings/onboarding/day-N` shows content
  based on the URL only; there's no "you were 9/14 through ownership, pick up
  here" moment. `isComplete` in the sidebar is inferred purely from current
  route position (`SettingsLayout.tsx`'s `OnboardingNav`), not real data.
- No dependency awareness — nothing tells the admin Day 5 (Connect Data) is
  gated on Day 4 (Assign Ownership) reaching 100% coverage.
- Day 5 today is a single link out to `/settings/onboarding` (a full 7-step
  wizard, `DataProductOnboardingNew.tsx`), so the outer 6-step frame and the
  inner 7-step frame have no visual relationship — user can lose track of
  which wizard they're in.

Target flow: a guided wizard shell (6 steps) that embeds the *real* screens for
each step (Company Profile, Principal registry, KPI Intelligence, Accountability
Interview, Data Product Onboarding, Connection Health), adds a resume entry
screen, and computes progress from actual registry state rather than route
history or clicks.

## 2. New/changed files

| File | Change |
|---|---|
| `src/pages/OnboardingDayView.tsx` | Rewrite as the wizard shell: progress bar, resumed-session chip, Back/Skip/Continue footer, embeds existing components per step instead of rendering static summary text. |
| `src/components/SettingsLayout.tsx` | `OnboardingNav` — replace click-history-based `isComplete` heuristic with real completeness (see §4) via a new hook. |
| `src/pages/OnboardingResume.tsx` (**new**) | The "Welcome back" screen. Route: `/settings/onboarding` (redirects to `/settings/onboarding/day-N` on Resume, or day-1 on Review all steps / first visit with zero progress). |
| `src/hooks/useOnboardingProgress.ts` (**new**) | Central hook: computes per-step completion + overall %, exposes `firstIncompleteStep`, `isStepUnlocked(n)`. Used by `OnboardingResume`, `OnboardingDayView`, and `SettingsLayout`. |
| `src/api/client.ts` | Add `getOnboardingProgress(clientId)` — see §5. |

## 3. Step → real component mapping

The wizard shell does **not** rebuild each step's UI — it wraps the existing
page/component in a consistent frame (progress bar + step header + Back/Skip/
Continue footer) and renders the real content in the body slot.

| Step | Title | Embeds | Notes |
|---|---|---|---|
| 1 | Workspace Setup | `CompanyProfile.tsx` form (client ID + profile fields) | Client ID field becomes read-only once step 1 is first completed (per existing "cannot be renamed" rule). |
| 2 | Principal Profiles | Principal list/editor from `RegistryExplorer.tsx` (principals section) or a trimmed version of `PrincipalManagement.tsx` | Show avatar/title/decision_style/business_processes/kpi-count per principal (matches prototype's richer card, not just name+email). |
| 3 | KPI Library | Two-panel sequence sharing this one route (`day3SubStep` local state, resets on day change): `BusinessProcessIntelligence.tsx` first (Phase 12F, July 2026 — selects from the 39-process canonical taxonomy + a few industry-specific extras), then `KPIIntelligence.tsx` (4-state flow: input → researching → review → committed) | Manual KPI editor link (`/settings?section=kpis`) stays available as a secondary action, not the primary CTA. Back from the KPI panel returns to the Business Processes panel, not out to Step 2. |
| 4 | Assign Ownership | `AccountabilityInterviewPanel.tsx` embedded as-is (chat + live assignments table, already two-panel) | This component already matches the prototype's design — no rebuild needed, just embed it here instead of only at `/settings?section=ownership-interview`. |
| 5 | Connect Data | `DataProductOnboardingNew.tsx`, entering directly at `workflowMode='new'` (skip its internal mode-picker screen since the outer wizard already establishes intent) | Its own 7-step sub-stepper renders inside the outer step-5 body. Outer "Continue" stays disabled until the sub-wizard reaches `review` step and registers successfully. |
| 6 | Validate & Launch | Connection health list (reuse logic from `/settings?section=connection-health`) + a "Run First Assessment" action that navigates to `/dashboard` and fires detection | Add an explicit final action: "Exit Admin Mode" (calls `exitAdminMode()` from `utils/adminMode.ts`, navigates to `/login`) rather than leaving hand-off implicit. |

## 4. Completeness rules (drives resume + progress bar + step locking)

Compute from real registry data, **not** click/route history. Suggested rule
per step (adjust field names to match actual registry provider responses):

```
step1_workspace_setup:  client record exists AND company_profile.industry is set
step2_principals:       principal_count >= 1 AND all principals have non-empty email
step3_kpi_library:      kpi_count >= 1 (template or active status)
step4_ownership:        (kpis_with_accountable_owner / total_kpis) === 1.0
step5_connect_data:     >= 1 data_product registered AND all its kpi sql_query validated
step6_validate_launch:  connection_health.all_ok === true AND >= 1 assessment_run exists
```

**Implementation note (2026-07-14):** step5 and step6 ship with scoped-down v1
rules — see the implementation plan's "Decisions requiring sign-off" section.
Step 5 originally shipped as `data_products_count >= 1` (no persisted KPI
sql_query validation flag exists yet). Step 6's assessment-run check is a
known limitation: in-memory run storage resets on every backend redeploy.

**Fix (2026-07-24):** the `data_products_count >= 1` rule for step 5 was
found live to be too coarse — `register_data_product` fires as early as the
Metadata Analysis step, long before KPI Definition / Query Validation /
Review & Register finish, so a data product with zero KPIs already read as
"step 5 complete." That made `OnboardingResume` jump an admin straight past
in-progress, unsaved KPI Definition work to Day 6 (reproduced against
brookshire_brothers: `BB_FI_01` existed with 0 KPIs, and 5 KPIs pending
"Accept All" were lost on resume). Step 5 now additionally requires
`kpis_connected >= 1` — at least one KPI in the registry whose
`data_product_id` matches one of the client's real data products, which only
becomes true once `finalize_kpis` (Review & Register) has actually persisted
something. sql_query validation itself is still not a persisted flag — this
tightening only closes the "zero KPIs at all" case.

**Implementation note (2026-07-22, Phase 12F):** step3's payload also
includes an informational `business_processes_count` field, deliberately
**not** folded into `complete` — a client that onboarded before the
Business Process Intelligence panel shipped has 0 business processes and
would be retroactively marked "incomplete" with no backfill path if this
were a hard gate. `step3_kpi_library`'s completeness rule is unchanged
(`kpi_count >= 1`).

`firstIncompleteStep` = first step (1–6) where the rule evaluates false. This
is what the Resume screen and the wizard's initial `step` state should use —
not a value read from `localStorage`.

Unlock rule for the sidebar / "Continue" button: step N+1 is only enabled once
step N's rule is true (matches the "blocked" banner pattern in the prototype's
1C/2A explorations). Exception: allow non-linear jump via `SettingsLayout`'s
existing sidebar even to "locked" steps — display a dismissible "this step
usually needs X first" note rather than hard-blocking, since admins do
sometimes need to jump ahead (e.g. re-checking KPI library after adjusting
ownership).

## 5. API surface

New lightweight endpoint (or client-side aggregation if you'd rather avoid a
new backend route — the six checks above only need data most existing
registry endpoints already return):

```
GET /api/v1/onboarding/progress?client_id={id}
→ {
    "client_id": "valvoline",
    "steps": {
      "workspace_setup":  { "complete": true },
      "principals":       { "complete": true, "count": 6, "with_email": 6 },
      "kpi_library":      { "complete": true, "count": 14 },
      "ownership":        { "complete": false, "assigned": 9, "total": 14 },
      "connect_data":     { "complete": false, "data_products": 0 },
      "validate_launch":  { "complete": false }
    },
    "first_incomplete_step": 4
  }
```

If a dedicated endpoint is more work than it's worth right now, `useOnboardingProgress`
can instead fan out to the existing registry endpoints (principals, KPIs,
accountability records, data products, connection health) and compute the same
shape client-side — functionally equivalent, just more round trips on load.

**Implementation note (2026-07-14):** a dedicated backend endpoint was chosen
over frontend fan-out — see the implementation plan for the concrete provider/
agent calls it reuses and the RLS/Infra B3 compliance rationale.

## 6. Resume screen behavior

Route: visiting `/settings/onboarding` directly (not a specific `day-N`).

- If `first_incomplete_step` is 1 and nothing else is complete → skip resume
  screen, go straight to Day 1 (first-ever visit, nothing to resume).
- Otherwise show the resume screen: last-worked-on step title, its specific
  in-progress metric (e.g. "9 / 14 KPIs assigned" — pull the relevant number
  out of the `steps` payload for whichever step is incomplete), a 6-segment
  progress strip, "Resume Step N →" (primary, navigates to
  `/settings/onboarding/day-N`) and "Review all steps" (secondary, navigates to
  day-1).
- On landing inside a step via Resume, show the "↻ Resumed from your last
  session" chip (prototype's Step 4 treatment) for that first render only —
  clear it on any Continue/Back click so it doesn't persist across the whole
  session.

## 7. Footer nav contract (every step)

- **Back**: always enabled except step 1; goes to step N-1 without re-validating.
- **Skip for now**: advances without requiring the step's completeness rule to
  be true. Keep this — several tips in the existing copy explicitly say fields
  "can be completed later."
- **Continue**: label becomes "Run First Assessment & Launch" only on step 6;
  disabled on step 5 until nested sub-wizard reports success (§3).

## 8. Out of scope / open questions for product

- Whether "Extend Existing Product" should also be reachable from the outer
  Step 5 (prototype intentionally skips straight to "New Data Product" per
  your last request) — flag if admins onboarding a second data product for the
  same client need that path from inside the wizard too.
  **Resolved (2026-07-14):** yes — `DataProductOnboardingNew.tsx` keeps a
  standalone route (`/settings/data-onboarding`) with its full mode-picker
  intact, separate from the wizard's Step 5 embed, so this path remains
  available.
- Whether step-locking (§4) should hard-block or just warn — recommend warn-only
  to start, tighten later if admins abuse the non-linear jump.
- Company Profile's industry-research side panel (auto-fetches on industry
  blur) is unchanged by this spec — still supplementary context, not autofill.
