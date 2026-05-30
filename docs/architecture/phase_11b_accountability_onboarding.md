# Phase 11B: KPI Accountability Onboarding — LLM Interview

**Created:** 2026-05-25
**Status:** Spec — ready for implementation
**Builds on:** Phase 11A (kpi_accountability table, KPIAccountabilityProvider, SA routing, PIB filtering)

---

## Design Philosophy

**Assignments are always direct.** The `kpi_accountability` table (Phase 11A) is the single runtime source of truth. SA and PIB query it directly — no resolver, no inheritance chain, no process lookup at runtime.

**Process ownership is onboarding scaffolding.** During the interview, when an admin says "Sarah owns Revenue Management," the agent uses that to batch-suggest the KPIs in that process. The admin confirms, adjusts, or rejects each suggestion. Each confirmed item writes a direct row to `kpi_accountability`. The process knowledge is consumed during onboarding and does not persist as a runtime dependency.

This means:
- No new tables required — `kpi_accountability` from Phase 11A is unchanged
- No resolver logic — SA and PIB continue to query the table directly
- No override mechanism, no source field, no stale-row problem
- Process registry remains useful as a grouping and suggestion tool, never as a runtime authority

---

## What Phase 11A Left Open

Phase 11A built the table, the provider, and the routing. It left the onboarding question unanswered: how does a new client populate those rows without manually entering each KPI-to-principal pair?

Phase 11B answers that with a conversational LLM interview. The interview uses process knowledge as context to accelerate assignment — grouping KPIs by process, batch-proposing likely owners — but every assignment that results is a direct confirmed row.

---

## Interview Flow

The interview proceeds in three phases for each principal (or all principals in sequence):

### Phase 1 — Process-guided suggestion

```
Agent: "Sarah Chen is CFO. Which processes is she responsible for?"
Admin: "Revenue Management and Profitability Analysis"
Agent: "Those processes cover 8 KPIs. I'm proposing Sarah as accountable
        for all 8 enterprise-wide — confirm, adjust scope, or reject each:"

  ✓ Net Revenue          accountable   enterprise-wide
  ✓ Gross Revenue        accountable   enterprise-wide
  ✓ Gross Margin %       accountable   enterprise-wide
  ✓ EBITDA               accountable   enterprise-wide
  ✗ Operating Income     [admin rejects — assign to COO instead]
  ✓ Gross Profit         accountable   enterprise-wide
  ~ SG&A Expense         accountable   [admin changes scope to: region=North America]
  ✓ COGS                 accountable   enterprise-wide
```

Each tick writes one direct row to `kpi_accountability`. Rejected items move to the unassigned pool.

### Phase 2 — Gap resolution

After all principals have been interviewed, the agent computes coverage:

```
Agent: "All principals covered. 3 KPIs have no accountable owner yet:
        NPS Score, Carbon Intensity, Inventory Turnover.
        Who owns each one?"

Admin: "NPS Score → Rachel Kim. Carbon Intensity → Marcus Webb, EMEA only.
        Inventory Turnover → Rachel Kim."
```

Each answer writes a direct row.

### Phase 3 — Conflict and coverage review

```
Agent: "Coverage: 15/15 KPIs assigned. One note:
        Net Revenue has 3 accountable principals — is that intentional,
        or should we add dimensional scoping to distinguish their scope?"
```

Agent surfaces:
- KPIs with >1 accountable principal at the same scope (likely an error)
- Principals with no assignments (not yet interviewed or intentionally excluded)
- Any principal exceeding 8 KPI assignments (capacity warning)

Admin can adjust before final confirmation.

---

## Agent Design: `A9_Accountability_Interview_Agent`

### Single entrypoint

```python
async def interview(
    self,
    request: AccountabilityInterviewRequest,
) -> AccountabilityInterviewResponse:
    ...
```

### Models

```python
class AccountabilityInterviewRequest(BaseModel):
    session_id: Optional[str] = None      # None = start new session
    client_id: str
    principal_id: Optional[str] = None    # None = interview all principals
    user_message: Optional[str] = None    # None on first turn
    conversation_history: List[dict] = []
    turn_count: int = 0


class ProposedAssignment(BaseModel):
    kpi_id: str
    kpi_name: str
    principal_id: str
    principal_name: str
    scope_dimension: Optional[str] = None
    scope_value: Optional[str] = None
    role: str = "accountable"             # accountable | responsible
    suggestion_source: str                # "process:<process_id>" | "direct" | "gap"
    # suggestion_source is for interview UX only — not written to kpi_accountability


class AccountabilityInterviewResponse(BaseModel):
    session_id: str
    agent_message: str
    suggested_responses: List[str]
    proposed_assignments: List[ProposedAssignment]  # full list, updated each turn
    unassigned_kpis: List[dict]           # [{id, name}] not yet covered
    coverage_pct: float                   # % of client KPIs with an accountable principal
    conflict_warnings: List[str]          # surfaced in Phase 3
    phase: str                            # "process_suggestion" | "gap_resolution" | "review"
    interview_complete: bool
    conversation_history: List[dict]
    turn_count: int
```

### Context injected per LLM turn

```
- Client name
- Full KPI list: id, name, domain, business_process_ids
- Full process list: id, name, domain, KPI members (derived from kpi.business_process_ids)
- Full principal list: id, name, title
- Proposed assignments confirmed so far
- Remaining unassigned KPIs
- Current phase
```

### Model routing

- Chat turns (all three phases): `claude-haiku-4-5-20251001` — fast, low cost
- Coverage computation and conflict detection: `claude-sonnet-4-6` — called once at Phase 3 entry

### What the agent does NOT do

- Does not write to the registry — it only returns `ProposedAssignment` objects
- Does not query `kpi_accountability` at runtime — it uses the KPI and process registries only
- Does not create new processes or KPIs — it works with what is registered

---

## API Endpoints

```
POST /api/v1/accountability/interview/start
  body: { client_id, principal_id? }
  response: AccountabilityInterviewResponse (session_id, opening message)

POST /api/v1/accountability/interview/chat
  body: { session_id, client_id, message }
  response: AccountabilityInterviewResponse (next message, updated proposals)

POST /api/v1/accountability/interview/confirm
  body: {
    client_id,
    approved: ProposedAssignment[]   # subset admin confirmed
  }
  response: { rows_written: int }
  action: writes each approved item as a direct KPIAccountability row

GET /api/v1/accountability/coverage/{client_id}
  response: {
    covered_kpis: int,
    total_kpis: int,
    coverage_pct: float,
    unassigned_kpis: [{ id, name }],
    principals_without_assignments: [{ id, name }],
    conflicts: [{ kpi_id, kpi_name, principal_count: int }]
  }
```

---

## Admin UI: "Assign KPI Ownership" Panel

New tab in Admin Console alongside the existing read-only Accountability tab.

### Layout

```
┌──────────────────────────────┬────────────────────────────────────────────┐
│  Interview                   │  Proposed Assignments                      │
│  ────────────────            │  ──────────────────────────────────────    │
│                              │  Coverage: 12 / 15 KPIs  (80%)            │
│  Agent: "Sarah owns Revenue  │  3 KPIs unassigned                        │
│  Management — confirming     │                                            │
│  6 KPIs..."                  │  Principal   KPI             Scope   Role  │
│                              │  ─────────── ──────────────  ──────  ────  │
│                              │  S. Chen   ✓ Net Revenue     Global  Acct  │
│                              │  S. Chen   ✓ Gross Revenue   Global  Acct  │
│                              │  S. Chen   ~ SG&A Expense    N.Am    Acct  │
│                              │  S. Chen   ✗ Op. Income      —       —     │
│  [suggested responses]       │  R. Kim    ✓ NPS Score       Global  Acct  │
│                              │  ...                                       │
│  [input]         [Send]      │                                            │
│                              │  ⚠  Net Revenue: 2 accountable principals  │
│                              │                                            │
│                              │  [Approve All Confirmed]                   │
└──────────────────────────────┴────────────────────────────────────────────┘
```

### Behaviour

- `suggestion_source` shown as a subtle tag: "via Revenue Management" or "direct"
- ✓ = admin confirmed, ~ = admin modified scope/role, ✗ = admin rejected
- Rejected items move to unassigned list visible to agent on next turn
- Coverage percentage updates after each turn
- Conflicts shown as warnings — do not block approval but require acknowledgement
- "Approve All Confirmed" writes only ✓ and ~ rows to `kpi_accountability`; ✗ rows are discarded

---

## Confirm Step: Writing to Registry

On confirm, the API writes each approved `ProposedAssignment` to `kpi_accountability`:

```python
for assignment in approved:
    row = KPIAccountability(
        id=str(uuid.uuid4()),
        client_id=client_id,
        kpi_id=assignment.kpi_id,
        principal_id=assignment.principal_id,
        scope_dimension=assignment.scope_dimension,
        scope_value=assignment.scope_value,
        role=AccountabilityRole(assignment.role),
        notes=f"Set via accountability interview — {assignment.suggestion_source}",
        created_by="interview",
    )
    await provider.upsert(row)
```

`suggestion_source` is recorded in `notes` for audit purposes but is not a schema field — it is interview scaffolding only.

---

## Implementation Sequence

| Step | Deliverable | Notes |
|---|---|---|
| 1 | `A9_Accountability_Interview_Agent` — backend | Core agent, 3-phase flow, Haiku/Sonnet routing |
| 2 | API endpoints: `start`, `chat`, `confirm`, `coverage` | 4 endpoints under `/api/v1/accountability/interview/` |
| 3 | Admin UI panel — chat + proposed assignments table | New tab in Admin Console |
| 4 | Seed lubricants via interview | End-to-end validation |
| 5 | Unit tests | See below |

No schema migrations required — `kpi_accountability` from Phase 11A is unchanged.

---

## Test Requirements

### `tests/unit/test_accountability_interview.py`

| Test | Scenario |
|---|---|
| `test_process_suggestion_phase` | Admin assigns a process → agent proposes all KPIs in that process |
| `test_gap_detection` | After process phase, agent correctly identifies unassigned KPIs |
| `test_scope_adjustment` | Admin narrows scope on a proposed assignment → modified row in proposals |
| `test_rejection_moves_to_unassigned` | Admin rejects a proposal → KPI appears in gap phase |
| `test_conflict_warning` | Two principals proposed as accountable for same KPI + scope → warning generated |
| `test_coverage_calculation` | 15 KPIs, 12 assigned → coverage_pct = 0.80 |
| `test_confirm_writes_direct_rows` | Approved proposals write correct `KPIAccountability` rows |
| `test_confirm_skips_rejected` | Rejected proposals not written to registry |

### `tests/unit/test_accountability_coverage.py`

| Test | Scenario |
|---|---|
| `test_coverage_endpoint_empty` | New client, no assignments → 0% coverage, all KPIs unassigned |
| `test_coverage_endpoint_partial` | 10 of 15 KPIs assigned → correct counts and unassigned list |
| `test_conflict_detection` | Two accountable rows for same (kpi_id, scope) → surfaces in conflicts |

---

## Answered Design Questions

| Question | Decision |
|---|---|
| Scope inheritance | Scope flows from process suggestion to proposed KPI rows by default — interview confirms per assignment |
| Multi-process KPIs | Same principal inheriting via two processes → one proposed row (deduplicated by interview agent before presenting) |
| Role precedence | Not needed — assignments are direct; no inherited vs direct conflict |
| Principal without assignments | Zero KPIs (not fall-back-to-all) — admin is shown gap via coverage endpoint |
| Principal represents a team | Yes — `principal_type: "individual" \| "team" \| "committee"` added to Principal model; interview can reference team principals |
| Assignment cardinality | One accountable principal per KPI per scope; multiple responsible principals allowed |
| Process knowledge at runtime | Not used — interview scaffolding only; `suggestion_source` recorded in `notes` for audit |
