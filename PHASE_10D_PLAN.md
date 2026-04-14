# Phase 10D: MCP Abstraction Layer & Platform Migration

**Status:** Planning (Ready for implementation in next session)  
**Scope:** Option C — Comprehensive (MCP abstraction + platform migration + Admin Console integration)  
**Test Strategy:** Real MCP servers where available (no mocks)  
**Complexity:** High — Requires vendor MCP research, abstraction design, UI integration

---

## Vision

Agent9 currently connects to data platforms via direct SDK connections (SnowflakeManager, DatabricksManager in Phase 10C). Phase 10D introduces **MCP (Model Context Protocol) abstraction**, enabling:

1. **Vendor-Managed Servers** — Data platforms provide MCP servers that expose schema discovery, metadata extraction, and query execution
2. **Flexible Connectivity** — OnboardingService works transparently via SDK or MCP
3. **Platform Parity** — Uniform interface for Snowflake, Databricks, BigQuery, PostgreSQL
4. **UI Integration** — Admin Console guides users through MCP server selection/configuration

### Why MCP?

- **Reduces credential burden** — Agent9 doesn't hold database passwords; MCP server acts as proxy
- **Standardizes vendor APIs** — One protocol for all platforms
- **Future-proofs onboarding** — New platforms add MCP server → Agent9 auto-supports them
- **Separates concerns** — OnboardingService (what) from connectivity (how)

---

## Architecture

### Current State (Phase 10C)

```
OnboardingService
├─ DatabaseManagerFactory
│  ├─ SnowflakeManager (direct SDK)
│  ├─ DatabricksManager (direct SDK)
│  └─ (BigQuery, PostgreSQL: legacy DPA inspect_schema)
```

### Target State (Phase 10D)

```
OnboardingService
├─ DatabaseManagerFactory
│  ├─ DatabaseManager (SDK-based)
│  │  ├─ SnowflakeManager
│  │  ├─ DatabricksManager
│  │  └─ BigQueryManager (new)
│  │
│  └─ MCPConnectionFactory (NEW)
│     ├─ MCPManager (decorator pattern)
│     └─ Vendor MCP Servers
│        ├─ Snowflake Native App MCP
│        ├─ Databricks LLM-Evaluators MCP
│        └─ BigQuery Cortex MCP (if available)
```

### Key Design Pattern: Decorator

```python
# Both implement DatabaseManager ABC
manager1 = SnowflakeManager(config)  # Direct SDK
manager2 = MCPManager(mcp_client)    # Via MCP
manager3 = MCPManager(mcp_client)    # Different vendor MCP

# OnboardingService doesn't care which
await onboarding.connect(manager1 or manager2)
```

---

## Implementation Phases

### Phase 10D-A: MCP Foundation

**Goal:** Build MCP abstraction layer + test with real vendor servers

1. **Research Vendor MCP Availability**
   - Snowflake: Check for published MCP (unlikely; Cortex is LLM, not schema tools)
   - Databricks: Check for LLM/evaluation MCPs (may exist)
   - BigQuery: Check for Vertex AI MCP
   - Create matrix of what's available

2. **Design MCPManager Class**
   - Implement DatabaseManager ABC
   - Connect via MCP protocol (stdio, HTTP, etc.)
   - Translate MCP capabilities → DatabaseManager methods
   - Handle MCP errors → DatabaseManager exceptions

3. **Implement MCPConnectionFactory**
   - User provides MCP server endpoint/config
   - Factory creates appropriate MCPManager
   - Same interface as DatabaseManagerFactory

4. **Write Integration Tests**
   - Test with **real MCP servers** (not mocks)
   - If no public MCP available, build reference implementation
   - Fallback: Mock tests + integration tests with real servers when available

### Phase 10D-B: Platform Migration

**Goal:** Migrate BigQuery and PostgreSQL from legacy DPA to OnboardingService

1. **BigQueryManager**
   - Queries `INFORMATION_SCHEMA.*` for metadata
   - Similar to SnowflakeManager/DatabricksManager
   - Integrate into DatabaseManagerFactory

2. **PostgresManager**
   - Queries `information_schema.*` for metadata
   - Handle schema + table enumeration
   - Integrate into DatabaseManagerFactory

3. **Migrate DPA inspect_schema()**
   - Remove platform-specific logic from DPA
   - Replace with calls to OnboardingService
   - DPA becomes thin wrapper around OnboardingService

4. **Backward Compatibility**
   - Existing BigQuery/DuckDB workflows continue
   - Graceful fallback if OnboardingService unavailable
   - Test that no existing workflows break

### Phase 10D-C: Admin Console Integration

**Goal:** Wire OnboardingService into Admin Console UI

1. **Data Product Onboarding Workflow**
   - **Step 1:** Connection Method (SDK or MCP)
   - **Step 2:** Select Source Platform (Snowflake, Databricks, BigQuery, PostgreSQL)
   - **Step 3:** Provide Connection Details
     - If SDK: credentials, warehouse/catalog, schema
     - If MCP: MCP server endpoint, auth token
   - **Step 4:** Discovery (OnboardingService discovers tables/views)
   - **Step 5:** Selection (user chooses which views to onboard)
   - **Step 6:** Analysis (OnboardingService extracts schema, FKs, semantic tags)
   - **Step 7:** Review (user confirms metadata)
   - **Step 8:** Registration (contract saved to registry)

2. **UI Components**
   - `ConnectionMethodSelector` — SDK vs MCP
   - `SourcePlatformSelector` — Snowflake, Databricks, BigQuery, PostgreSQL
   - `CredentialsForm` — Dynamic based on platform + method
   - `TableDiscoveryBrowser` — Lists available tables/views
   - `SchemaViewer` — Displays extracted columns, FKs, types
   - `SemanticTagEditor` — Override inferred tags
   - `ContractPreview` — YAML preview before registration

3. **Workflow State Machine**
   - Track progress through steps
   - Allow back/forward navigation
   - Save partial progress (session storage)
   - Validate at each step

---

## Vendor MCP Research

### Snowflake

**Status:** ❓ Unknown
- Cortex AI is LLM-based, not schema/query tool
- Check: Snowflake documentation for schema discovery APIs via Cortex
- If available: Use for metadata extraction
- If not: Fall back to direct SDK (Phase 10C)

**Action:** Research Snowflake Native App MCP or similar

### Databricks

**Status:** ❓ Unknown
- LLM-Evaluators might expose schema APIs
- Check: Databricks documentation for MCP servers
- If available: Integrate
- If not: Direct SDK (Phase 10C) is primary

**Action:** Research Databricks MCP or API gateway

### BigQuery

**Status:** ❓ Unknown
- Vertex AI might have MCP
- Check: Google Cloud documentation
- If available: Use for schema discovery
- If not: Direct SDK approach

**Action:** Research Vertex AI MCP

### PostgreSQL

**Status:** ❓ Unknown
- pg_iam or similar for remote access
- Check: PostgreSQL extension ecosystem
- If available: Integrate
- If not: psycopg2 direct connection (Phase 10C approach)

**Action:** Research PostgreSQL MCP options

---

## Test Strategy

### Unit Tests
- MCPManager class (mocked MCP client)
- MCPConnectionFactory (mocked vendor servers)
- DatabaseManager ABC compliance

### Integration Tests
- **Real MCP servers** (when available)
- OnboardingService + MCPManager end-to-end
- Schema discovery via MCP
- FK extraction via MCP
- Contract generation from MCP data

### Admin Console Tests
- Workflow state transitions
- Form validation (credentials, selections)
- Discovery callback handling
- Error recovery

---

## File Changes Summary

| Component | File | Action |
|-----------|------|--------|
| MCP Abstraction | `src/database/mcp_connection_factory.py` | NEW |
| MCP Manager | `src/database/mcp_manager.py` | NEW |
| BigQuery Manager | `src/database/backends/bigquery_manager.py` | NEW (migrate from legacy) |
| PostgreSQL Manager | `src/database/backends/postgres_manager.py` | NEW (migrate from legacy) |
| DPA | `src/agents/new/a9_data_product_agent.py` | REFACTOR (use OnboardingService) |
| Admin Console | `decision-studio-ui/src/pages/AdminConsole.tsx` | ENHANCE (add workflow) |
| Tests | `tests/unit/test_mcp_*.py` | NEW (10+ test files) |
| Docs | `docs/design/mcp_architecture.md` | NEW |

---

## Success Criteria

- ✅ MCPManager implements DatabaseManager ABC
- ✅ OnboardingService works transparently with SDK and MCP
- ✅ BigQuery and PostgreSQL migrated to OnboardingService
- ✅ Admin Console data product onboarding workflow complete
- ✅ Real vendor MCP servers tested (if available)
- ✅ All existing tests pass (no regressions)
- ✅ 10+ new integration tests for MCP flows
- ✅ UI supports both SDK and MCP connection methods

---

## Timeline Estimate

- **Research & Design:** 4-6 hours (vendor MCP investigation)
- **MCP Foundation:** 8-10 hours (MCPManager, factories, tests)
- **Platform Migration:** 6-8 hours (BigQuery/PostgreSQL managers)
- **Admin Console:** 12-16 hours (UI components, workflow, integration)
- **Testing & Polish:** 4-6 hours

**Total:** ~40-50 hours (5-6 days of development)

---

## Open Questions

1. **Are real vendor MCPs available?** Research needed in next session
2. **Reference MCP Implementation:** If no vendor MCPs, should we build a reference MCP for testing?
3. **BigQuery Credentials:** How should BQ service account keys be handled? Secure storage?
4. **PostgreSQL Security:** Should we support password, SSH key, or environment variables?
5. **MCP Protocol:** Which transport (stdio, HTTP, SSE)? Determined by vendor.
6. **Fallback Strategy:** If MCP unavailable, always fall back to SDK?

---

## Deferred to Phase 10E+

- Lineage tracking (view SQL parsing → column lineage)
- Data quality checks (row counts, null analysis)
- Semantic query validation (LLM-assisted synonym harvesting)
- Native AI capabilities (Snowflake Cortex, Databricks Mosaic integration)
- Registry maintenance UI (KPI/data product CRUD via UI)
- Scheduled/offline assessment runs (already in Phase 9C, may enhance)

---

## Related Documentation

- Phase 10C Plan: `PHASE_10C_PLAN.md` (completed)
- Onboarding Architecture: `docs/design/data_product_onboarding_architecture.md`
- OnboardingService: `src/services/data_product_onboarding_service.py`
- Bootstrap Utilities: `scripts/BOOTSTRAP_README.md`

---

## Next Session Checklist

- [ ] Research vendor MCP availability (Snowflake, Databricks, BigQuery, PostgreSQL)
- [ ] Create MCP architecture decision document
- [ ] Define MCPManager ABC implementation
- [ ] Identify real MCP servers to test against
- [ ] Create test plan with real servers
- [ ] Begin Phase 10D-A implementation

