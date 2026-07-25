# RACI Accountability Model

## Overview

This document extends `kpi_accountability_model.md`'s dimensional accountability model from a
2-role, KPI-only design to a 4-role RACI (Responsible / Accountable / Consulted / Informed) model
applied at **both KPI and Business Process levels**, with Business-Process-level assignments
cascading down to KPIs by default.

The core change in stance: **ownership stops being a visibility gate and becomes a routing/escalation
axis only.** The original accountability model's stated goal — "the right principal gets the right
signal by construction" — is preserved, but "right signal" now means graduated visibility (R/A
surfaced actively, C included, I summarized in a digest) rather than binary include/exclude. This
redefines **Phase 12B: Org-First Accountability Onboarding** (`DEVELOPMENT_PLAN.md`), which is
currently an unbuilt stub scoped to the old 2-role model.

---

## The Problem

### It broke live, twice, in one afternoon

Onboarding `brookshire_brothers` and registering 5 new KPIs against a real Snowflake connection
(`dp1`), `detect_situations` returned **zero situations for every principal** despite all 5 KPIs
having real thresholds and correct SQL. Two independent gates in
`A9_Situation_Awareness_Agent._get_relevant_kpis` were both silently zeroing out real data:

1. **Business-process match**: all three principals (CEO/COO/CFO) had `business_processes: []` —
   never populated, because Day 2 of the onboarding wizard (Principal Profiles) runs *before* Day 3
   (which creates the client's actual Business Process registry rows). The KPIs *did* have real
   `business_process_ids`, so the "KPI has no BP" escape hatch didn't apply either — the match
   loop had nothing to iterate and excluded everything.
2. **Accountability filter**: the CFO principal already had 4 `kpi_accountability` rows against
   older KPIs (from the Day 3/4 KPI-Library + ownership-interview flow). Because those assignments
   existed, the filter activated — and since it only checked "is this KPI in *my* accountable set,"
   it hid the 5 brand-new, wholly-unassigned KPIs from *every* principal, not just CFO.

Both were patched same-day with a narrow "fail open on incomplete registry data" fix (empty
principal-side filter = no filter; a KPI unclaimed by anyone stays visible). That fix is correct and
stays — but it's a patch on a model whose fundamental shape has three deeper problems:

### 1. Fragility is structural, not incidental
Strict ownership-match visibility only works when the principal→business-process→KPI chain is
fully populated. For a freshly onboarded client that chain is *always* incomplete somewhere first —
this isn't an edge case to patch around, it's the common case the model has to work under.

### 2. It fights the theory layer's actual value proposition
The theory/causal layer's differentiator is surfacing cross-KPI, cross-domain correlation (e.g., "a
revenue miss correlates with a supplier's inventory turnover"). Ownership-gated visibility
structurally hides exactly the connective tissue that makes that valuable — a VP legitimately needs
to see a KPI they don't "own" because it's a candidate driver of one they do. Narrow filtering and a
causal-model layer pull in opposite directions.

### 3. It was designed for the wrong persona
The original model assumed a busy executive personally navigating SA→DA→SF and needing it
pre-filtered to survive their attention span. The more realistic ICP workflow: an FP&A analyst
stewards situations (validates data, shapes HITL problem statements), a VP tests solution
constraints, and the executive mostly consumes a distilled PIB briefing and gives final sign-off. An
analyst-steward needs *broader* cross-functional visibility than any single principal's ownership
scope to do their job — narrow filtering blocks the actual operator, not just the exec.

---

## Target Data Model

### Schema: generalize, don't duplicate

Today's `kpi_accountability` table (`src/registry/models/kpi_accountability.py`,
`supabase/migrations/20260518_kpi_accountability.sql`) is KPI-only:
`id, client_id, kpi_id, principal_id, scope_dimension, scope_value, role (accountable|responsible),
notes, created_by, created_at, updated_at`.

**Recommended**: generalize this table rather than adding a second, near-identical
`business_process_accountability` table. Add a `subject_type` discriminator and rename
`kpi_id` → `subject_id`:

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel

class RACIRole(str, Enum):
    RESPONSIBLE = "responsible"   # Does the work — validates data, shapes the problem statement
    ACCOUNTABLE = "accountable"   # Owns the decision — sets targets, signs off
    CONSULTED = "consulted"       # Two-way input sought — sees it because it's relevant, doesn't own it
    INFORMED = "informed"         # One-way notification — digest/briefing only

class RACISubjectType(str, Enum):
    KPI = "kpi"
    BUSINESS_PROCESS = "business_process"

class RACIAssignment(BaseModel):
    id: str
    client_id: str
    subject_type: RACISubjectType
    subject_id: str                        # kpi_id or business_process_id
    principal_id: str
    scope_dimension: Optional[str] = None  # unchanged from today — e.g. "geography"
    scope_value: Optional[str] = None      # unchanged from today — e.g. "EMEA"
    role: RACIRole
    notes: Optional[str] = None
    created_by: str = "system"
    created_at: str
    updated_at: str
```

This is one mechanism reused for both subject types — the same principle already applied this
session to `_sample_distinct_values` (one shared sampler instead of four duplicated per-backend
profiling methods) and the tenant-scoped `.get()` fix (one corrected method instead of patching
each call site). The tradeoff: every current call site that names `kpi_id` as a column/param —
the interview agent, SA's `_get_relevant_kpis`, PIB's `/delegates`, the `/coverage/{client_id}`
endpoint — needs updating to filter on `subject_type="kpi"` plus `subject_id`. That's mechanical,
not risky, and is listed as an open question below in case the migration cost changes the call.

**Constraint fix required**: today's unique constraint is
`(client_id, kpi_id, scope_dimension, scope_value)` with no `role` or `principal_id` in it — as
written it would block a second RACI row (say, a Consulted assignment) at a scope that already has
an Accountable row. The real invariant to preserve is narrower than "one row per scope": **only one
`accountable` row per `(client_id, subject_type, subject_id, scope_dimension, scope_value)`** — any
number of `responsible`/`consulted`/`informed` rows can coexist at the same scope. The new unique
constraint should be `(client_id, subject_type, subject_id, scope_dimension, scope_value, role,
principal_id)` with an additional partial/application-level check restricting `role='accountable'`
to at most one row per scope.

### BP → KPI cascading

A KPI's *effective* RACI set is: its own KPI-level rows, **plus** every RACI row on any Business
Process in the KPI's `business_process_ids` list, unless a KPI-level row for that same principal
exists (KPI-level overrides BP-level for that principal only — it doesn't remove other principals'
BP-level assignments).

This isn't a new idea — it formalizes what `A9_Accountability_Interview_Agent` already does as an
LLM heuristic today (its system prompt builds a business-process→domain map and infers KPI
ownership from it, per `_load_registry_context`). Making it an explicit, deterministic two-level
model means the inference doesn't have to be re-derived by an LLM call every time; a BP-level
assignment (e.g., "VP Operations is Accountable for Cost Management") is set once and every KPI
tagged `cost_management` picks it up automatically.

---

## Visibility Semantics

Ownership answers **"who's accountable for escalation and routing,"** not **"who's allowed to see
this."** Concretely, for a given principal and KPI/situation:

| Role | SA working view (dashboard, live situations) | PIB briefing |
|---|---|---|
| Responsible / Accountable | Actively surfaced, full priority | Full section |
| Consulted | Included, lower priority/sort order | Included |
| Informed | Not shown in the working view | Digest-only entry |
| No RACI assignment exists at all | **Visible** (fail-open default) | Visible |

The last row preserves today's shipped fix exactly — an unassigned KPI/BP stays visible to
everyone, it isn't a new lenient carve-out. What changes is that an *assigned-but-not-owned* KPI
(Consulted) no longer needs to be hidden to make ownership meaningful — Consulted is precisely the
mechanism that resolves the theory-layer tension: a VP sees a correlated KPI legitimately, without
"owning" it and without the system needing to fall back to all-or-nothing visibility.

---

## Governance Rules (extends `kpi_accountability_model.md`'s rules)

1. **Singleton Accountable per scope** — unchanged, now stated precisely: at most one
   `role=accountable` row per `(subject_type, subject_id, scope_dimension, scope_value)`.
   `responsible`/`consulted`/`informed` are unbounded at the same scope.
2. **BP-level Accountable is not required to cascade an Accountable KPI role** — a KPI can inherit
   `consulted` from its BP while having its own dedicated `accountable` principal; cascading applies
   role-by-role, not as a single inherited bundle.
3. **Capacity limit** (unchanged from the existing model, extended to RACI): flag when a principal
   holds `accountable`/`responsible` roles (not `consulted`/`informed`, which are expected to be
   broader) on more than ~8 subjects.
4. **KPI-level override is principal-scoped, not row-scoped** — overriding a cascaded BP assignment
   for one principal must not silently drop other principals' BP-level assignments to that KPI.

---

## Legacy Signal Reconciliation

Two free-text fields already carry proto-ownership signal and predate this model:
`KPI.owner_role`/`stakeholder_roles` (`src/registry/models/kpi.py`) and
`BusinessProcess.owner_role`/`stakeholder_roles` (`src/registry/models/business_process.py`). Both
are role-name strings (e.g. `"CFO"`), not principal IDs, set at KPI/BP-definition time (KPI
Assistant, Business Process Template Generator) and never reconciled against `kpi_accountability`
rows today — a real redundancy, not a second source of truth to preserve.

This document does not recommend deleting them outright (that's an implementation decision, not a
design claim) — instead, treat them as **bootstrap/seed input** to the interview agent's suggestion
pass: when proposing a RACI assignment for a KPI/BP with no existing rows, the interview agent
should resolve `owner_role`/`stakeholder_roles` (a role name) against actual principals with that
`title`, and pre-populate a suggested Accountable/Consulted row from it, exactly the way it already
resolves business-process ownership today.

---

## Onboarding Wizard Implications

Two concrete gaps caused the live incident and should be closed as part of this redefinition:

1. **Day 2 (Principal Profiles) runs before Day 3 (Business Processes exist)** — `PrincipalEditor.tsx`'s
   `business_processes` field is a free-text CSV input with zero validation against the real BP
   registry, and nothing routes an admin back to Day 2 after Day 3 creates real rows. Fix: either
   move BP/RACI assignment to a step after Day 3 (Day 4's interview is the natural place — it
   already runs after KPI Library), or validate `PrincipalEditor.tsx` entries against
   `factory.get_business_process_provider()` once BPs exist.
2. **Day 4's interview (`A9_Accountability_Interview_Agent`) only proposes 2 roles at the KPI level**
   — extend its `ProposedAssignment` output to the 4-role set and to Business-Process-level
   assignment directly (not just inferred-down-to-KPI), so the "templates show which principal is
   typically accountable for each process" behavior already planned for Phase 12B becomes a first-class
   BP-level RACI row, not a side effect of KPI-level inference.

---

## Integration with Existing Agents

### `A9_Situation_Awareness_Agent`
`_get_relevant_kpis`/`detect_situations`'s current fail-open fix (KPI-id-level, accountable-only)
becomes the R/A/unassigned rows of the table above. Add: Consulted-role KPIs included at lower
sort priority; Informed-role KPIs excluded from the working view (they surface via PIB instead).
No change to the dimensional `scope_dimension`/`scope_value` fields, which the current filter loads
but doesn't yet consult — this document doesn't require fixing that gap, just noting it stays
consistent with the RACI role axis being orthogonal to scope.

### `A9_Accountability_Interview_Agent`
Extend `ProposedAssignment` to the 4-role enum and to `subject_type`/`subject_id` instead of
`kpi_id`-only. The existing 3-phase flow (`process_suggestion → gap_resolution → review`) and
business-process-ownership inference logic carry over unchanged — only the output shape and subject
scope grow.

### `A9_PIB_Agent`
Informed-role assignments become the natural source for a "digest" briefing section. The existing
`/delegates` endpoint (`src/api/routes/pib.py`) currently ranks suggestions by raw business-process
*name* overlap between a KPI and each principal's `business_processes` list — once RACI rows exist,
this should rank by actual RACI role (a Responsible/Consulted principal is a better delegate
suggestion than a name-overlap heuristic), though this isn't required for the model itself to ship.

### `A9_Principal_Context_Agent`
When resolving a principal's KPI set, resolve BP-level cascaded RACI in addition to direct KPI-level
rows — this is where the BP→KPI cascading logic in "Target Data Model" above actually executes.

---

## Out of Scope / Forward References (not designed here)

- **Situation-level RACI**: `SituationCard` already declares `assignee_id`,
  `assignment_candidates: List[AssignmentCandidate]`, and `assignment_decision: AssignmentDecision`
  (`src/agents/models/situation_awareness_models.py`) — fields that exist in the schema but are
  **never populated anywhere in the code today**. The natural next extension is populating
  `assignee_id` from a KPI's Responsible principal at detection time. Flagged here so it isn't
  rediscovered from scratch; not designed in this document.
- **Solution-level RACI**: Value Assurance's `register_solution` sets a single `principal_id` (the
  approver) and already tracks accountability drift via `principal_still_accountable`
  (`a9_value_assurance_agent.py`) — a useful precedent for how an Accountable-role drift check could
  generalize, but Solution Finder itself has no ownership field at all today. Out of scope here.
- **Teams-as-principals**: explicitly parked. A team principal would need roster/aggregation
  semantics (PIB delivery to a distribution list vs. one inbox; decision-style/communication
  preferences don't cleanly generalize to a group) that are a separate design question.
- **PIB's ad-hoc delegation** (`situation_actions` table: snooze/delegate/request_info/acknowledge)
  stays a separate, ephemeral, per-situation execution-layer mechanism — it is not folded into RACI's
  persistent ownership rows by this document.

---

## Phase Plan — redefines Phase 12B

Supersedes the current `DEVELOPMENT_PLAN.md` Phase 12B stub ("templates show which principal is
typically accountable for each process → admin confirms → rows written to `kpi_accountability`
directly" — 2-role, KPI-only).

| Deliverable | Description |
|---|---|
| Schema migration | Generalize `kpi_accountability` → `subject_type`/`subject_id`, add `consulted`/`informed` to the role enum, fix the unique constraint per "Target Data Model" above |
| Interview agent extension | `A9_Accountability_Interview_Agent` proposes 4 roles at both KPI and BP level; resolves `owner_role`/`stakeholder_roles` as bootstrap suggestions |
| SA visibility integration | `_get_relevant_kpis` applies the graduated R/A/C/I visibility table; Consulted sorted lower, Informed excluded from working view |
| PIB digest section | Informed-role assignments populate a new briefing section |
| Onboarding wizard fix | Day 2 BP field validated or resequenced after Day 3; Day 4 interview covers BP-level + 4 roles |
| Unit tests | Schema migration round-trip; BP→KPI cascade resolution (override, no-override cases); singleton-accountable-per-scope still enforced; SA visibility table (R/A/C/I × situation surfacing) |

**Prerequisite** (unchanged from the current stub): Phase 12A (template KPIs in registry) + Phase
11A (`kpi_accountability` table) + Phase 12F (business process templates — real `business_processes`
rows must exist before BP-level RACI has anything to assign against).

---

## Open Questions Requiring Sign-off

1. **Schema generalization vs. two tables** — recommended: generalize in place (see "Target Data
   Model"). Alternative: leave `kpi_accountability` untouched and add a parallel
   `business_process_accountability` table, at the cost of duplicating the query/filter logic in SA,
   the interview agent, and PIB across two tables instead of one.
2. **Unique constraint redesign** — confirm the narrower "one `accountable` row per scope, unbounded
   others" invariant is correct before writing the migration (today's constraint doesn't encode this
   distinction at all).
3. **Should PIB's `/delegates` suggestion ranking read RACI roles instead of raw business-process
   name overlap?** Improves suggestion quality but isn't required for RACI to ship.
4. **Do `KPI.owner_role`/`stakeholder_roles` and `BusinessProcess.owner_role`/`stakeholder_roles` get
   deprecated once RACI rows exist, or remain indefinitely as the bootstrap/seed layer?**

---

## Related Documents

- `docs/architecture/kpi_accountability_model.md` — the 2-role, KPI-only model this document extends
- `docs/architecture/business_process_hierarchy_blueprint.md` — proposed `parent_id`/inheritance
  hierarchy for Business Processes (not implemented); RACI cascading here is independent of that
  hierarchy landing, but would compose naturally with it (a RACI row on a parent Domain cascading to
  child Processes the same way it cascades to KPIs)
- `docs/architecture/theory_layer_design.md` — the causal/correlation model whose value proposition
  motivated moving ownership from a visibility gate to a routing axis
- `DEVELOPMENT_PLAN.md` — Phase 12B (redefined by this document), Phase 11A/11B/12A/12F (prerequisites)
