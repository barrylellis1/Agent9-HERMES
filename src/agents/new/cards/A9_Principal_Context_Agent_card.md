# A9_Principal_Context_Agent Card

Status: Operational (multi-tenant client isolation, Phase 10B-DGA)

## Overview
The `A9_Principal_Context_Agent` is the security and context gateway for all principal-scoped operations. It retrieves principal profiles from the registry, constructs `PrincipalContext` objects enriched with client_id and business process mappings, and enables role-based access control and client isolation across all workflows.

## Protocol Entrypoints
- `get_principal_context(principal_id: str) -> PrincipalContext`
- `resolve_principal_by_role(client_id: str, role: str) -> PrincipalContext`
- `get_principal_profiles(client_id: str) -> List[PrincipalProfile]`

Models defined in `src/agents/models/principal_context_models.py`.

## Key Data Structures

### PrincipalProfile
Registry entry with:
- `principal_id` — unique identifier
- `full_name`, `email`, `role` (CEO, CFO, COO, etc.)
- `client_id` — owning customer tenant
- `metadata.decision_style`, `metadata.communication_style` — persona preferences
- `metadata.kpi_line_preference`, `metadata.kpi_altitude_preference` — KPI ordering
- `business_processes: List[str]` — assigned process domains

### PrincipalContext
Runtime object derived from profile:
- `principal_id`, `client_id`, `role` — inherited from profile
- `decision_style`, `communication_style` — persona traits
- `business_processes: List[BusinessProcess]` — expanded to full objects
- `default_filters: Dict` — default query filters scoped to client_id

## Dependencies
- Registry providers: `principal_profile`, `business_process`
- No LLM calls; purely data retrieval and enrichment

## Client Isolation (Critical for Multi-Tenant)
**Every PrincipalContext carries client_id.** Workflows MUST propagate client_id through all downstream calls:
- SA Agent: filters KPIs by `principal_context.client_id`
- DA Agent: KPI resolution respects `principal_context.client_id`
- DPA Agent: SQL execution scoped to client data products
- DGA Agent: `validate_data_access()` checks client_id matching

## Dual Lookup Pattern
The agent supports two lookup modes for flexibility:

| Mode | Input | Purpose | Returns |
|---|---|---|---|
| **Direct** | `principal_id` | Known principal, quick retrieval | Single PrincipalContext |
| **Role-Based** | `client_id` + `role` | Workflow assignment, discovery | Principal matching role in client |

Both paths propagate client_id into the returned context.

## Dependencies
- A9_Principal_Context_Agent (self, for lookup)
- Registry: principal_profile and business_process providers

## Recent Updates (Feb 2026)
- Multi-tenant client_id support: all PrincipalProfile entries carry client_id
- Role-based lookup added: `resolve_principal_by_role(client_id, role)` for workflow routing

## Phase 10B-DGA: Data Governance Wiring (Apr 2026)
- **client_id propagation**: All 5 PrincipalContext constructor call sites now explicitly carry `client_id` from source PrincipalProfile to returned context object
- **Cross-client data leak prevention**: client_id is the primary isolation boundary; all downstream agents (SA, DA, DPA, DG) validate this field before executing queries
- **Dual-lookup client scoping**: Both direct (principal_id) and role-based (client_id, role) lookups return contexts with matching client_id, ensuring no principal can access another client's data
- **Business process mapping**: Business process objects retrieved in context of principal's client_id, preventing process-based KPI access bypass
