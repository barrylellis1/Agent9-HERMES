# A9_Accountability_Interview_Agent PRD

<!--
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-05-30
-->

## 1. Overview

**Purpose:** The `A9_Accountability_Interview_Agent` delivers a guided, LLM-driven conversational interview that helps administrators assign KPI accountability across their leadership team. By walking admins through business process domains and surfacing coverage gaps, it converts an otherwise tedious manual process into a structured 3-phase dialogue that terminates with confirmed rows in the `kpi_accountability` registry table.

**Agent Type:** Admin Onboarding / Registry Population Agent
**Version:** 1.0 (Phase 11B)
**Status:** Active

> **COMPLIANCE NOTE:**
> - Instantiated via `A9_Accountability_Interview_Agent.create()` — a lightweight async factory that bypasses AgentRegistry (this agent is not part of the SA→DA→SF pipeline).
> - Do NOT instantiate directly with `A9_Accountability_Interview_Agent()` — always use `await A9_Accountability_Interview_Agent.create()` so `connect()` is called.
> - **Usage Example:**
> ```python
> agent = await A9_Accountability_Interview_Agent.create()
> response = await agent.interview(request)
> ```

---

## 2. Strategic Context

### Why This Agent Exists

KPI accountability is a prerequisite for the dimensional accountability model introduced in Phase 11. Without knowing which principal is accountable for which KPI (and at what scope dimension), the system cannot:

- Route situation cards to the right principal
- Scope assessments to a principal's domain without over-including others' KPIs
- Generate meaningful accountability reports for governance/SOC 2 evidence

Manually assigning accountability for 15–100+ KPIs across a leadership team is tedious and error-prone. The interview agent eliminates this friction by:
1. Pre-proposing assignments derived from process ownership (most KPIs can be auto-assigned this way)
2. Using dialogue to resolve the ambiguous remainder
3. Surfacing and resolving conflicts (two principals claiming the same KPI at the same scope)

### Business Outcome

After a completed interview, every KPI in the client registry has at least one `accountable` principal assignment. SA agent can then filter KPI assessments by `client_id` AND use the accountability table to determine which situation cards reach which principal.

---

## 3. Position in the System

This agent is a **standalone admin utility**, not part of the SA→DA→SF→VA pipeline. It is invoked from the Decision Studio admin console (Registry Explorer → Accountability tab).

```
Admin Console (RegistryExplorer.tsx)
  → AccountabilityInterviewPanel.tsx (2-column: chat left, assignments table right)
    → POST /accountability/interview/start    ← new session
    → POST /accountability/interview/chat     ← repeated per turn
    → POST /accountability/interview/confirm  ← write confirmed rows to Supabase
      → kpi_accountability table
```

---

## 4. Functional Requirements

### 4.1 Three-Phase Interview Structure

| Phase | Entry Condition | Behaviour | Exit Condition |
|-------|----------------|-----------|----------------|
| `process_suggestion` | Session start | Two-step per principal: domain selection → KPI confirmation | All principals have at least one proposed assignment |
| `gap_resolution` | All principals covered but unassigned KPIs remain | For each gap KPI, ask admin to assign one directly | No unassigned KPIs |
| `review` | All KPIs assigned | Sonnet summarises coverage + flags conflicts | Admin satisfied; agent says "Interview complete" |

If no gaps exist after process_suggestion, the agent skips directly to review.

### 4.2 Session State

Session state is in-memory; not persisted across server restarts. Each session is identified by a UUID `session_id` generated at start.

Session holds:
- `proposed_assignments: List[ProposedAssignment]` — accumulated across all turns
- `conversation_history: List[dict]` — last 6 messages injected into LLM context
- `all_kpis / all_processes / all_principals` — loaded from RegistryFactory at session start
- `phase`, `turn_count`, `interview_complete`

### 4.3 Assignment States

Each `ProposedAssignment` has a `status` field:

| Status | Meaning |
|--------|---------|
| `proposed` | Agent has suggested this; admin has not yet acted |
| `confirmed` | Admin explicitly confirmed |
| `modified` | Admin accepted with scope change |
| `rejected` | Admin declined; KPI goes to unassigned pool |

Only `proposed`, `confirmed`, and `modified` count toward coverage percentage. `rejected` assignments re-enter the unassigned pool.

### 4.4 Conflict Detection

A conflict exists when >1 principal has `role=accountable` for the same `(kpi_id, scope_dimension, scope_value)` triple with status in `{proposed, confirmed, modified}`. Conflicts are surfaced in Phase 3 (review) in the `conflict_warnings` list.

### 4.5 Coverage Calculation

```
coverage_pct = (total_kpis - len(unassigned_kpis)) / total_kpis
```

`unassigned_kpis` = KPIs with no assignment in `{proposed, confirmed, modified}` status.

### 4.6 LLM Output Protocol

Every LLM turn must include structured JSON blocks within the response:

- ` ```assignments ` block — emitted when proposing new assignments
- ` ```status_updates ` block — emitted when the admin confirms/rejects/modifies
- ` ```suggested_responses ` block — always emitted (3–4 quick-reply options for admin)

The agent strips these blocks before returning `agent_message` to the UI. The UI renders `suggested_responses` as clickable chips.

### 4.7 Confirm Endpoint Behaviour

`POST /accountability/interview/confirm` receives a list of `ProposedAssignment` objects with `status=confirmed` or `status=modified`. The route handler writes each to the `kpi_accountability` Supabase table. `status=rejected` entries are silently skipped.

The agent itself NEVER writes to the database.

---

## 5. Non-Functional Requirements

| Requirement | Spec |
|-------------|------|
| Latency per chat turn | < 3s for Haiku model turns; < 6s for Sonnet (Phase 3 entry) |
| Session isolation | Separate `session_id` per admin; no cross-session state leakage |
| Multi-tenant isolation | All registry loads filter strictly by `client_id`; the agent never loads data for a different client |
| LLM fallback | If LLM call fails, return `AccountabilityInterviewResponse` with error message in `agent_message` |

---

## 6. Models

All models are defined inline in `src/agents/new/a9_accountability_interview_agent.py`.

### AccountabilityInterviewRequest

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `Optional[str]` | None to start a new session |
| `client_id` | `str` | Tenant identifier — required |
| `principal_id` | `Optional[str]` | Scope interview to one principal; None = all |
| `user_message` | `Optional[str]` | Admin's chat message; None on first turn |
| `conversation_history` | `List[dict]` | Full history for client-side state management |
| `turn_count` | `int` | Running turn count |

### AccountabilityInterviewResponse

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | UUID identifying this session |
| `agent_message` | `str` | Plain-text message to display (JSON blocks stripped) |
| `suggested_responses` | `List[str]` | Quick-reply chips for the admin |
| `proposed_assignments` | `List[ProposedAssignment]` | Full accumulated assignment list |
| `unassigned_kpis` | `List[dict]` | `[{id, name}]` for KPIs with no active assignment |
| `coverage_pct` | `float` | 0.0–1.0 |
| `conflict_warnings` | `List[str]` | Human-readable conflict descriptions (Phase 3 only) |
| `phase` | `str` | Current phase |
| `interview_complete` | `bool` | True when agent says "Interview complete" |
| `conversation_history` | `List[dict]` | Updated history for next request |
| `turn_count` | `int` | Incremented each turn |

---

## 7. Agent Configuration

No `AgentConfig` model. The agent initialises `A9_LLM_Service_Agent` directly in `connect()` with `task_type="general"`. Model selection is hardcoded:

```python
MODEL_CHAT     = "claude-haiku-4-5-20251001"   # all chat turns
MODEL_ANALYSIS = "claude-sonnet-4-6"            # Phase 3 coverage/conflict analysis
```

---

## 8. LLM Routing

All LLM calls go through `A9_LLM_Service_Agent.generate(A9_LLM_Request(...))`. No direct `anthropic` or `openai` imports. The `operation` field is set to `"accountability_interview"` for audit trail purposes.

---

## 9. Dependencies

| Component | What This Agent Needs |
|-----------|-----------------------|
| `A9_LLM_Service_Agent` | Chat turns (Haiku) + Phase 3 analysis (Sonnet) |
| `RegistryFactory` → KPI provider | Client-scoped KPI list (id, name, domain, business_process_ids) |
| `RegistryFactory` → principal_profile provider | Client-scoped principal list (id, name, title) |
| `RegistryFactory` → business_process provider | Process → KPI membership (for domain grouping) |
| `KPIAccountabilityProvider` | `get_coverage()` reads confirmed rows from `kpi_accountability` |

---

## 10. API Routes

All routes in `src/api/routes/kpi_accountability.py`:

| Method | Path | Handler |
|--------|------|---------|
| `POST` | `/accountability/interview/start` | Calls `interview()` with `session_id=None` |
| `POST` | `/accountability/interview/chat` | Calls `interview()` with existing `session_id` |
| `POST` | `/accountability/interview/confirm` | Writes confirmed `ProposedAssignment` rows to Supabase |
| `GET` | `/accountability/coverage/{client_id}` | Calls `get_coverage(client_id)` |

---

## 11. UI Integration

Component: `decision-studio-ui/src/components/AccountabilityInterviewPanel.tsx`

Layout: two-column
- Left: chat window with agent messages, admin input, suggested-response chips
- Right: live `ProposedAssignment` table with per-row confirm / modify / reject buttons and coverage progress bar

Wired into: `decision-studio-ui/src/pages/RegistryExplorer.tsx` → Accountability tab → "Start Interview" button.

---

## 12. Constraints and Invariants

- The agent MUST NOT write to any database table directly
- The agent MUST filter all registry reads by `client_id` — no cross-tenant data
- `ProposedAssignment` objects with `status=rejected` MUST NOT be written to `kpi_accountability`
- Phase transitions are deterministic: `process_suggestion → gap_resolution → review` (gap_resolution skipped if coverage is full after process_suggestion)
- Backward phase transitions are not supported

---

## 13. Future Considerations

- Persist sessions to Supabase so interviews can resume after server restart
- Import accountability assignments from HCM systems (LLM-assisted mapping)
- Automatic conflict resolution suggestions (not just warnings)
- Scheduled re-interview triggers when principal roster changes significantly
