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

## Infra A4-a: Per-Request Registry Refresh (May 2026)
- `get_principal_context_by_role` and `get_principal_context_by_id` now call `provider.load()` on every invocation (non-fatal fallback on error) then `_load_principal_profiles()` — replacing the lazy-load guard. New principals seeded post-startup are visible without a service restart.

## Phase 10B-DGA: Data Governance Wiring (Apr 2026)
- **client_id propagation**: All 5 PrincipalContext constructor call sites now explicitly carry `client_id` from source PrincipalProfile to returned context object
- **Cross-client data leak prevention**: client_id is the primary isolation boundary; all downstream agents (SA, DA, DPA, DG) validate this field before executing queries
- **Dual-lookup client scoping**: Both direct (principal_id) and role-based (client_id, role) lookups return contexts with matching client_id, ensuring no principal can access another client's data
- **Business process mapping**: Business process objects retrieved in context of principal's client_id, preventing process-based KPI access bypass

## Fix: uuid shadowing crash in error path (Jul 2026)
- `get_principal_context_by_id` had a local `import uuid` inside the default-profile success branch. Python treats any name imported/assigned anywhere in a function as local to that whole function, so this shadowed the module-level `import uuid` for the entire method — including the `except` handler's own `uuid.uuid4()` call. Any exception raised earlier in the try block (e.g. `_load_principal_profiles()` failing) crashed the fallback response itself with `cannot access local variable 'uuid'`, found live in production 2026-07-29. Fixed by removing the redundant local import; the module-level import (line 13) now resolves correctly everywhere in the function. Regression test: `tests/unit/test_principal_context_extraction.py::test_get_principal_context_by_id_error_path_does_not_crash_on_uuid`.

## Fix: identify_data_product_owner — undefined helpers + cross-tenant leak (Aug 2026)
Found running the real data-product-onboarding pipeline end to end for the first time (against a new `dp_lubricants_sales` data product).

- **Crash**: `_normalize_profile_data` and `_iter_principal_profiles` were called (in `identify_data_product_owner`, the ownership-resolution step) but never defined — `AttributeError` on every call. `_get_profile_case_insensitive` (defined) gated every branch on `hasattr(profile, 'get')`, always `False` against real `PrincipalProfile` Pydantic instances — `PrincipalProfileProvider.get()`/`.get_all()` return validated models, not dicts — so it silently returned `None` on every call instead of raising. The whole method was written against an assumed dict-shaped profile that predates the current Supabase-backed `PrincipalProfile` model. All three now implemented/fixed to work off real `PrincipalProfile` attributes (via `.model_dump()`), with `title` aliased to `role` for existing `.get("role")` call sites (not the same convention as the short role codes like `"CFO"` used elsewhere — known, documented mismatch, not resolved by this fix).
- **Cross-tenant leak** (found after fixing the crash): the workflow resolved a **Hess** principal as owner of a **Lubricants** data product. `PrincipalOwnershipRequest` had no `client_id` field; the orchestrator's `ownership_payload` never threaded `request.client_id` through; `PrincipalProfileProvider`'s internal `_profiles` dict is keyed on bare `id`, and principal IDs (e.g. `coo_001`, `cfo_001`) are reused across clients by design (Rule 8 — uniqueness is the composite `(client_id, id)` key), so a bare-ID lookup has no way to stay inside one tenant. Fixed: `client_id` added to `PrincipalOwnershipRequest`, threaded through the orchestrator, every branch of `identify_data_product_owner` now strict-matches `client_id`, and the method fails closed (returns `pending`, skips auto-matching) when `client_id` is absent rather than guessing across tenants. Verified live via `/workflows/data-product-onboarding/run`.
- **Known remaining gap, not fixed at first**: because `_profiles` is keyed on bare `id`, it can only cache one tenant's copy of a colliding ID at a time — whichever client loaded last wins the slot for the whole process. The per-result `client_id` check this fix adds means a collision can only cause an *under*-resolution (correctly falls through to last-resort/manual assignment), never a wrong-tenant assignment — but a direct-nominee match can still miss a real match that exists for the right tenant.

**Follow-up same day: the actual root cause was a startup race, not the provider class.** Tracing why `A9_Principal_Context_Agent` had the flat, bare-ID-keyed `PrincipalProfileProvider` at all — `registry.py`'s REST routes (e.g. `create_principal`) were correctly using `DatabaseRegistryProvider`, which already supports `get(id, client_id=...)` properly. `connect()`'s own fallback logic was the problem: `self.registry_factory.get_principal_profile_provider()` returns `None` if this agent connects *before* `RegistryBootstrap` (the real, comprehensive registry initializer, run once via `AgentRuntime` at app startup) has registered the DB-backed providers — a genuine race with no guaranteed order. When that happened, `connect()` manufactured its own `PrincipalProfileProvider()` and **registered it into the shared factory**, which can pre-empt `RegistryBootstrap`'s own `if existing is None` registration guard for the rest of the process — not just degrading this one agent, but potentially poisoning every other consumer of the `'principal_profile'` slot too.

Fixed: `connect()` now calls `await RegistryBootstrap.initialize()` first — idempotent and self-healing (it re-verifies `principal_profile`/`business_glossary`/`data_product`/`kpi` and only re-runs what's actually missing), so this is a no-op on the normal startup-ordered path and a correct on-demand bootstrap otherwise. The local-fallback `PrincipalProfileProvider()` is now used only if `RegistryBootstrap.initialize()` itself still leaves the provider missing (a real failure, e.g. DB unreachable) — and is deliberately **not** registered into the shared factory, so it can never be handed to another consumer as if it were the real one. `registry.py`'s `get_registry_factory()` dependency was fixed the same way (was calling `RegistryFactory().initialize()`, which only loads data for providers *already* registered and does nothing if none are — it was implicitly relying on `RegistryBootstrap` having already run, not ensuring it).

`identify_data_product_owner`'s branch 1 (direct nominee lookup) now also passes `client_id=` straight into `provider.get()` when the provider supports it (try/except `TypeError` falls back to the bare call for the degraded local fallback), rather than fetching ambiguously and rejecting after the fact — verified live: with only the strict-match rejection, a same-tenant candidate (`cfo_001`, which does belong to `lubricants`) still failed to match directly because the bare `get('cfo_001')` call returned a *different* tenant's copy; with the `client_id`-scoped lookup it now resolves precisely and deterministically to the requesting tenant's own principal.

A full fix for the underlying provider storage (`_profiles` keyed on the composite `(client_id, id)` instead of bare `id`) is still not done and still a materially larger change to a widely-shared registry provider class — deliberately deferred; the startup-race fix above removes the actual live exposure without needing it.
