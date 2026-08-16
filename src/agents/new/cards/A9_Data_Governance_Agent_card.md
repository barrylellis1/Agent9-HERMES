# A9_Data_Governance_Agent Card

**Last Updated:** 2026-07-13  
**Status:** MVP

## Overview
The `A9_Data_Governance_Agent` handles business term resolution, KPI-to-data-product mapping, and data access validation.

## Protocol Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `map_kpis_to_data_products` | `async def map_kpis_to_data_products(request: KPIDataProductMappingRequest) -> KPIDataProductMappingResponse` | mappings[] + unmapped_kpis[] (client-scoped) |
| `translate_business_terms` | `async def translate_business_terms(request: BusinessTermTranslationRequest) -> BusinessTermTranslationResponse` | resolved_terms dict + unmapped_terms[] |
| `validate_data_access` | `async def validate_data_access(request: DataAccessValidationRequest) -> DataAccessValidationResponse` | allowed: bool + reason + policy_id |
| `get_view_name_for_kpi` | `async def get_view_name_for_kpi(request: KPIViewNameRequest) -> KPIViewNameResponse` | view_name (or "unknown" if not found) |
| `map_business_process` | `async def map_business_process(request: BusinessProcessMappingRequest) -> BusinessProcessMappingResponse` | mapped process + ownership + KPIs |
| `check_slice_validity` | `async def check_slice_validity(request: SliceValidityCheckRequest) -> SliceValidityCheckResponse` | per-dimension completeness + cross-component verdicts + not_sliceable_by (persisted to the KPI record) |

**All methods are async. All returns use Pydantic models.**

Not yet added to this table despite being real, callable methods (pre-existing staleness, not introduced by this update — flagged so the next edit doesn't silently perpetuate it): `check_data_quality` (hardcoded stub — always returns `completeness: 0.98` regardless of input, does not implement its own contract), `validate_registry_integrity` (returns a plain `Dict[str, Any]`, not a Pydantic model — violates the "all returns use Pydantic models" rule above), `compute_and_persist_top_dimensions`.

## Dependencies
- RegistryFactory + providers: KPI, Business Glossary, Data Product, Business Process
- `data_product_agent` — `A9_Data_Product_Agent` reference, wired post-bootstrap by `runtime._wire_governance_dependencies()` (reverse direction from the DGA-into-DPA/DA/SA wiring below). Required only by `check_slice_validity`, for multi-backend SQL execution via `execute_sql()`.

## Contract Path Resolution
Uses `_contract_path()` method to resolve contract files:
- Canonical location: `src/registry_references/data_product_registry/data_products/fi_star_schema.yaml`

## KPI Lookup & View Resolution
- Normalizes KPI identifiers (e.g., `Gross Revenue` → `gross_revenue`) and exhaustively scans registry entries to tolerate naming drift before failing.
- Defers view-name decisions to upstream registry data; if a view cannot be found, returns `"unknown"` rather than synthesizing a `view_*` alias.

## Recent Updates (Dec 2025)
- Contract path consolidated to single source of truth in `registry_references`

## Request/Response Models

### KPIDataProductMappingRequest
```python
kpi_names: List[str]                # KPI identifiers to map
client_id: Optional[str]            # Tenant filter (when provided, results scoped to this client)
context: Optional[Dict]             # Additional context (principal context, etc.)
```

### KPIDataProductMappingResponse
```python
mappings: List[KPIDataProductMapping]  # Mapped KPI → data_product_id entries
unmapped_kpis: List[str]            # KPI names not found in registry
```

### BusinessTermTranslationRequest
```python
business_terms: List[str]           # Terms to translate (e.g., ["Gross Margin", "Profit Center"])
system: Optional[str] = "duckdb"    # Backend context for mapping
context: Optional[Dict]             # Principal context, etc.
```

### BusinessTermTranslationResponse
```python
resolved_terms: Dict[str, str]      # {business_term: technical_column_name}
unmapped_terms: List[str]           # Terms not found in glossary
human_action_required: bool         # Escalation flag for ambiguous terms
human_action_type: Optional[str]    # "clarification" or "ambiguity"
human_action_context: Optional[Dict] # Disambiguation choices
```

### DataAccessValidationRequest
```python
principal_id: str                   # Principal requesting access
data_product_id: str                # Data product to access
access_type: str = "read"           # "read" | "write" | "execute"
client_id: Optional[str]            # Tenant filter (principal's client_id)
```

### DataAccessValidationResponse
```python
allowed: bool                       # Access granted/denied
reason: Optional[str]               # Reason for decision
policy_id: Optional[str]            # Governance policy applied
```

### KPIViewNameRequest
```python
kpi_id: str                         # KPI identifier
client_id: Optional[str]            # Tenant context
```

### KPIViewNameResponse
```python
view_name: str                      # Resolved view name or "unknown"
kpi_id: str
data_product_id: Optional[str]      # Source data product
```

### SliceValidityCheckRequest
```python
kpi_id: str                         # KPI to check (client-scoped lookup)
client_id: str                      # Tenant — strict scope, mandatory
dimensions: Optional[List[str]]     # Defaults to the KPI's own declared dimensions
measure_column: str = "account_type"
components: Optional[List[str]]     # Defaults to extract_components(kpi.sql_query) — may resolve to ONE value
value_column: str = "amount"        # used by the completeness check
version_filter: Optional[str] = "Actual"
```

### SliceValidityCheckResponse
```python
kpi_id: str
client_id: str
status: str                         # "success" | "error" | "skipped"
error_message: Optional[str]
cross_component_results: List[SliceValidityDimensionResult]   # [] when < 2 components — nothing to compare
completeness_results: List[SliceValidityDimensionResult]      # runs for EVERY KPI, 1 component or many
components_used: List[str]          # explicit or auto-derived
not_sliceable_by: List[NotSliceableByEntry]  # UNION of dims where EITHER check landed "INVALID" — see below (Aug 2026)
checked_at: Optional[datetime]      # None unless the write-back actually persisted
```

**Two independent checks per dimension**, not one — `src/analysis/slice_validity.py`'s module docstring has the full reasoning:
- **Cross-component** (`profile()`): do 2+ components (e.g. Revenue vs COGS) reach the same dimension values? Only runs when the KPI has 2+ components — nothing to compare for a plain sum.
- **Completeness** (`check_completeness()`, added 2026-08-16): of THIS KPI's own rows, what fraction have a non-NULL value for this dimension? Runs for every KPI regardless of component count — the check that closes the gap where 26 of 42 KPIs across the seeded clients (every plain single-component sum) were previously unchecked entirely, because cross-component coverage structurally cannot apply to them.

`components` auto-derives from the KPI's own `sql_query` via `extract_components()` (regex over `account_type = 'X'` / `account_type IN (...)`, including multiple matches inside a `CASE WHEN` expression) — required to run this against every KPI without a caller having to know and specify each one's components by hand.

## Error Behaviour

| Scenario | Returns | Notes |
|----------|---------|-------|
| KPI not found | mappings=[], unmapped_kpis=[kpi_name] | Non-fatal; caller handles empty mappings |
| Registry unavailable | Empty mappings/resolved_terms, all input terms → unmapped | Graceful fallback; no exception raised |
| client_id mismatch | Filters out non-matching KPIs; unmapped_kpis increases | Strict isolation: never leaks cross-client KPIs |
| Business term ambiguous | human_action_required=True + human_action_context with choices | NLP agent must escalate to HITL for clarification |
| check_slice_validity: DPA not wired / KPI not found or cross-tenant / no dimensions / view unresolvable | status="error" + error_message | Non-fatal by design — a diagnostic result to display, not a workflow step anything depends on |
| check_slice_validity: profiling succeeded but the write-back to the KPI record failed | status="error", checked_at=None, but results/not_sliceable_by still populated | Deliberately NOT status="success" — a fresh timestamp on an unpersisted result reverts to stale on the next read, the exact false-confidence failure this feature exists to prevent |
| Data access denied | allowed=False + reason (e.g., "Principal not authorized for this product") | No exception; caller sees denied status |
| View not found for KPI | view_name="unknown" | No exception; indicates incomplete registry mapping |
| Invalid business_terms input | unmapped_terms=[all terms], resolved_terms={} | Tolerates empty input gracefully |

## Caching & Glossary Structure

**No caching:** All lookups are live against RegistryFactory providers (Supabase). No in-memory glossary cache.

**Glossary structure** (BusinessGlossaryProvider):
```
Glossary entries map business terms to technical columns:
  Business Term: "Gross Margin"
  Technical Name: "gross_margin_pct"
  Description: "Gross profit divided by revenue"
  Source System: "FI_Star_View"
```

On ambiguity (e.g., "Margin" could be gross_margin or net_margin), `human_action_required=True` and `human_action_context` lists candidates.

## Phase 10B-DGA: Data Governance Wiring (Apr 2026)
- `validate_data_access()` enforces real client_id filtering — no longer returns allow-all
- `map_kpis_to_data_products()` filters mapped results by client_id, preventing cross-client KPI visibility
- Post-bootstrap DGA wiring: A9_Orchestrator calls `runtime._wire_governance_dependencies()` after all agents connect, injecting DGA into Data Product and Deep Analysis agents
- Client isolation hardened: all governance queries scoped to PrincipalContext.client_id
- DGA is a required dependency of Data Product Agent — wiring enforced at bootstrap (raises RuntimeError if DGA unavailable)

## Infra B3: Runtime Enforcement (Jul 2026)
- `validate_data_access()` is now CALLED at runtime: DPA `execute_sql` invokes it before routing any SQL when the caller supplies a tenant-scoped principal_context (client_id set) plus data_product_id. Previously the method existed but had no runtime callers.
- Deny semantics (fail-closed): cross-client mismatch → deny; data product missing client_id while principal is scoped → deny; unscoped principal (system/admin) → allow.
- Regression coverage: `tests/unit/test_client_isolation.py` (DGA deny/allow + DPA gate tests).

## Infra A2: Registry write persistence fix (Jul 2026)
- `register_kpi_metadata()` and `map_business_process()` now `await` `kpi_provider.upsert()` / `bp_provider.upsert()` — these are genuinely async now (see `DatabaseRegistryProvider` fix in the Data Product Agent card). Previously the coroutine was created and discarded unawaited, so KPI/business-process registration through DGA silently never persisted to Supabase.

## Slice validity (Aug 2026)
- New `check_slice_validity()` — docs/architecture/kpi_semantic_contract.md §4. Wires the previously hand-run `scripts/check_slice_validity.py` into the onboarding Day 6 panel and Settings → Maintenance, writing `not_sliceable_by` / `slice_validity_details` / `slice_validity_checked_at` onto the KPI record (`src/registry/models/kpi.py`). **No longer advisory-only as of the §4.5 enforcement entry below — `A9_Deep_Analysis_Agent` now reads `not_sliceable_by` and excludes those dimensions from analysis.** What this method itself does — profile, classify, persist — has not changed; only what a downstream consumer now does with the result has.
- Pure profiling logic lives in `src/analysis/slice_validity.py` (moved from the script, which now re-exports it) — backend-aware, not BigQuery-only: identifier quoting is chosen per `source_system` (BigQuery backtick-wraps the whole fully-qualified name; SQL Server brackets each dot-separated segment; Snowflake and DuckDB are unquoted), matching conventions already live elsewhere in this codebase, not invented here.
- New reverse dependency: `data_product_agent`, wired post-bootstrap alongside the existing DGA-into-DPA/DA/SA wiring in `runtime._wire_governance_dependencies()`. `execute_sql()` is always called with `data_product_id` set explicitly, engaging Tier-1 registry-based backend routing — Snowflake/DuckDB queries are unquoted by this check's own convention, so `execute_sql`'s Tier-2 regex fallback (backtick → BigQuery, bracket → SQL Server) would not recognise them and would misroute silently.
- Non-fatal throughout, matching this agent's established convention (`get_view_name_for_kpi` returns `"unknown"` rather than raising): DPA not wired, KPI not found or cross-tenant, no dimensions, unresolvable view, and write-back failure all return `status="error"` with a message, never an exception.
- Tenant-safe by construction, not by assumption: passes `client_id` to `provider.get()` (falling back to a bare call only on `TypeError`, for the plain in-memory `KPIProvider`, which doesn't accept the kwarg) and enforces `client_id` STRICT MATCH itself regardless, so the check is safe whichever concrete provider class is live. **Not a theoretical concern** — found live 2026-08-15: two real clients (`lubricants`, `brookshire_brothers`) share the KPI id `gross_margin_pct`, and the original bare-lookup version returned the wrong tenant's record.
- Regression coverage: `tests/unit/test_dga_slice_validity.py` (wiring, tenant isolation, persistence, the Tier-1-routing regression), `tests/unit/test_slice_validity_dialects.py` (one assertion per `source_system`), `tests/unit/test_slice_validity.py` (unchanged — `assess()`'s own logic, now imported from `src/analysis/slice_validity.py`).

## Slice validity — completeness check + auto-derived components (Aug 2026)
- **The gap:** the original `check_slice_validity()` ran exactly one check — cross-component coverage — which structurally cannot apply to a single-component KPI (a plain `SUM(amount)` like `net_revenue`, 26 of 42 KPIs across the three seeded clients). A user pushed back on this directly: a single-component KPI can still be wrong when sliced — some rows might have no value for the dimension at all, silently dropping out of "revenue by customer" rather than corrupting one customer's number, and nothing checked for that at all.
- New `check_completeness()` in `src/analysis/slice_validity.py`: for every dimension, what fraction of this KPI's own rows have a non-NULL value for it (`COUNT(dim)` vs `COUNT(*)`, filtered to the KPI's own components/version). Applies to every KPI, 1 component or many — shares `assess()`/`DimensionVerdict`/`_quote_view()` with the pre-existing cross-component check, differing only in what `counts` means (`{"total_rows","complete_rows"}` vs component-name → value-count).
- `check_slice_validity()` now runs BOTH per dimension: completeness always; cross-component only when there are 2+ components. `not_sliceable_by` is the UNION of dimensions where EITHER check landed on `INVALID` — persisted per-dimension detail keeps both sub-verdicts distinguishable (`slice_validity_details[dim] = {"completeness": {...}, "cross_component": {...} | absent}`).
- New `extract_components()` (regex over `account_type = 'X'` / `IN (...)`, including multiple matches inside a `CASE WHEN` expression) auto-derives a KPI's components from its own `sql_query` — required to run this against every KPI without a caller specifying components by hand for each one; `SliceValidityCheckRequest.components` is now `Optional`, explicit values still override.
- Regression coverage: `tests/unit/test_slice_validity_completeness.py`, `tests/unit/test_slice_validity_extract_components.py` (against real `sql_query` strings read live off KPI records across all three backends, not synthesized), `tests/unit/test_dga_slice_validity.py` (the two-check merge, auto-derivation, the union `not_sliceable_by`).

## Slice validity — `reason_class` classification + `not_sliceable_by` enforced by DA (Aug 2026, §4.5)

- **`not_sliceable_by` is now a list of `NotSliceableByEntry` (`{dimension, reason_class, note, source}`), not bare dimension names.** Reopened deliberately: the user pointed out advisory-only display defeats the field's own stated purpose ("the reason we added the not sliceable by is to protect the DA from mis-calculating KPIs"), matching `kpi_semantic_contract.md` §4.5 verbatim. Before enforcing, added what §4.6 says a deny list needs first or it becomes "a place to hide bugs": `reason_class` distinguishes `structural` (a permanent fact about the client's own business data) from `pipeline_gap` (a completeness gap in the client's own source data/ETL — **not an Agent9 code defect**, corrected mid-session after conflating the two — Agent9 doesn't own the client's warehouse pipeline). `check_slice_validity()` defaults every derived entry to `pipeline_gap` with a human-readable `note` quoting the actual coverage numbers; `source` defaults to `derived`. A human can override via `source="declared"` (not yet exposed in any UI — the model supports it, nothing writes it today).
- **Backward-compat `field_validator` on `KPI.not_sliceable_by`** (`src/registry/models/kpi.py`) normalizes legacy bare-string entries — real data persisted by this session's earlier batch run, before this shape existed — into structured entries on load (`reason_class="pipeline_gap"`, `source="derived"`, `note=None`). No migration/backfill needed; verified live against `apex_lubricants`' real persisted deny list.
- **`A9_Deep_Analysis_Agent.execute_deep_analysis()` now consumes this** — excludes every `not_sliceable_by` dimension from `dims` before the `max_dimensions` cut, records each exclusion on `DeepAnalysisResponse.dimensions_excluded`. See `A9_Deep_Analysis_Agent_card.md`'s "§4.5 Enforcement" entry for the DA-side detail and live verification.
- **`validate_registry_integrity` does NOT yet surface `pipeline_gap` entries as a data-quality finding** — §4.6's other half (the deny list should double as a running inventory of the client's own data-completeness gaps, worth flagging to whoever owns that client's pipeline). The data already exists (every derived entry defaults to `pipeline_gap`); nothing reads it yet. Recorded as a fast-follow in `DEVELOPMENT_PLAN.md`, not required for DA's own correctness.
- New migration `20260816_kpi_not_sliceable_by_enforcement.sql` — comment-only, corrects the prior migration's now-false "advisory only, nothing reads these to gate Deep Analysis's dimension selection" column comment. No functional schema change (`not_sliceable_by` is `JSONB`, already accepted arbitrary shapes).
- Regression coverage: `tests/unit/test_kpi_not_sliceable_by_model.py` (the structured shape, the backward-compat normalizer, `model_copy(update=...)` preserving readability).
