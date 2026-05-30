# A9_Accountability_Interview_Agent Card

**Last Updated:** 2026-05-30
**Status:** Active — Phase 11B

## Overview

The `A9_Accountability_Interview_Agent` runs a conversational LLM-driven interview that helps administrators assign KPI ownership across their leadership team. It proposes accountability assignments derived from business process ownership and gap analysis, then returns `ProposedAssignment` objects for admin confirmation. **It does NOT write to the registry** — the confirm endpoint in `src/api/routes/kpi_accountability.py` writes approved rows to `kpi_accountability`.

Session state is in-memory; sessions are not persisted across restarts.

## Protocol Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `interview` | `async def interview(request: AccountabilityInterviewRequest) -> AccountabilityInterviewResponse` | Agent message + proposed assignments + coverage stats |
| `get_coverage` | `async def get_coverage(client_id: str) -> dict` | Live coverage stats from `kpi_accountability` table |

Both methods are async. `interview()` is the single entrypoint for all chat turns (start and continue).

## Models

Defined inline in `src/agents/new/a9_accountability_interview_agent.py`:

```python
class AccountabilityInterviewRequest(BaseModel):
    session_id: Optional[str]        # None = start new session
    client_id: str
    principal_id: Optional[str]      # None = interview all principals
    user_message: Optional[str]      # None on first turn
    conversation_history: List[dict]
    turn_count: int

class ProposedAssignment(BaseModel):
    kpi_id: str; kpi_name: str
    principal_id: str; principal_name: str
    scope_dimension: Optional[str]; scope_value: Optional[str]
    role: str                        # "accountable" | "responsible"
    suggestion_source: str           # "process:<id>" | "direct" | "gap"
    status: str                      # "proposed" | "confirmed" | "modified" | "rejected"

class AccountabilityInterviewResponse(BaseModel):
    session_id: str
    agent_message: str
    suggested_responses: List[str]
    proposed_assignments: List[ProposedAssignment]
    unassigned_kpis: List[dict]      # [{id, name}]
    coverage_pct: float
    conflict_warnings: List[str]
    phase: str                       # "process_suggestion" | "gap_resolution" | "review"
    interview_complete: bool
    conversation_history: List[dict]
    turn_count: int
```

## Interview Phases

| Phase | Behaviour |
|-------|-----------|
| `process_suggestion` | Two-step per principal: domain-level prompt → KPI confirmation. Emits `assignments` JSON block when admin selects domains. |
| `gap_resolution` | For each KPI with no accountable owner, asks admin to assign one directly. Emits `assignments` blocks. |
| `review` | Sonnet summarises coverage + conflicts. Session ends when agent says "Interview complete." |

## LLM Configuration

| Task | Model | Reason |
|------|-------|--------|
| All chat turns | `claude-haiku-4-5-20251001` | Low latency for conversational turns |
| Phase 3 coverage analysis | `claude-sonnet-4-6` | Conflict detection requires deeper reasoning |

LLM calls are made directly via `A9_LLM_Service_Agent` instantiated in `connect()`. This agent does NOT go through the Orchestrator (it is a standalone admin tool, not part of the SA→DA→SF pipeline).

## Dependencies

| Component | Role |
|-----------|------|
| `A9_LLM_Service_Agent` | All LLM calls for chat turns and analysis |
| `RegistryFactory` → KPI provider | Loads client-scoped KPI list for session context |
| `RegistryFactory` → principal_profile provider | Loads client-scoped principal list |
| `RegistryFactory` → business_process provider | Loads process→KPI membership |
| `KPIAccountabilityProvider` | `get_coverage()` reads confirmed assignments from Supabase |

## API Routes

Defined in `src/api/routes/kpi_accountability.py`:

| Endpoint | What it does |
|----------|--------------|
| `POST /accountability/interview/start` | Initialises a new session; returns opening message |
| `POST /accountability/interview/chat` | Continues an existing session |
| `POST /accountability/interview/confirm` | Writes confirmed `ProposedAssignment` rows to `kpi_accountability` |
| `GET /accountability/coverage/{client_id}` | Returns live coverage stats via `get_coverage()` |

## What This Agent Must NOT Do

- Write directly to the `kpi_accountability` table — confirm endpoint does that
- Call `yaml.safe_load()` for registry data — use RegistryFactory providers only
- Import `anthropic` or `openai` directly — all LLM calls go through `A9_LLM_Service_Agent`
- Cross client boundaries — all registry loads filter strictly by `client_id`

## Compliance

- A2A Pydantic I/O for all public methods
- Lifecycle: `create()` → `connect()` → `interview()` calls → `disconnect()`
- No direct LLM provider imports
- Multi-tenant: all registry loads are `client_id`-filtered

## Pipeline Position

This agent is a standalone admin utility, not part of the SA→DA→SF→VA pipeline. It is triggered from the **Registry Explorer → Accountability tab** in the admin console.

```
Admin Console (RegistryExplorer.tsx)
  → AccountabilityInterviewPanel.tsx
    → POST /accountability/interview/start
    → POST /accountability/interview/chat   (repeated)
    → POST /accountability/interview/confirm
      → writes to kpi_accountability (Supabase)
```
