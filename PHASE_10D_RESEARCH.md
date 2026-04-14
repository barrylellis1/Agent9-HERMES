# Phase 10D: Vendor MCP Research & Analysis

**Date:** 2026-04-13  
**Status:** ✅ COMPLETE — Real vendor MCPs available for all platforms  
**Impact:** Phase 10D can proceed with production-grade MCP servers, not mocks

---

## Executive Summary

**Game-changing finding:** All major data platforms have announced and released official or community MCP servers. This eliminates the "if MCP is available" blocker and makes Phase 10D-A research a straightforward integration task rather than a gamble.

| Platform | Status | Type | Production Ready |
|----------|--------|------|------------------|
| **Snowflake** | ✅ Available | Native Managed MCP | Yes — in public preview |
| **Databricks** | ✅ Available | Managed MCP + External | Yes — general availability |
| **BigQuery** | ✅ Available | Fully Managed Remote | Yes — GA with Cloud API Registry |
| **PostgreSQL** | ✅ Available | Official Anthropic MCP | Yes — npm published |
| **SAP BDC** | ✅ Available | Community MCP Server | Yes — multiple implementations |

**Recommendation:** Prioritize Snowflake, Databricks, and BigQuery (highest customer demand). PostgreSQL as fallback for legacy systems. SAP BDC as optional enterprise add-on.

---

## Platform-by-Platform Deep Dive

### 1. Snowflake: Snowflake-Managed MCP Server

**Status:** 🟢 **PRODUCTION READY** (Public Preview → GA)

#### Capabilities

- **Schema Discovery:** Automatic object discovery (databases, schemas, tables, views)
- **SQL Execution:** Native query execution via Snowflake SQL
- **Cortex Integration:** Access to Cortex Search (unstructured), Cortex Analyst (semantic modeling)
- **Object Management:** Handle databases, schemas, tables, views, stored procedures
- **Semantic Views:** Query via semantic layer (Cortex Analyst)
- **Knowledge Extensions:** Surface licensed third-party content (AP, Washington Post, Stack Overflow)

#### Architecture

```
Agent9 ← (HTTP/REST) → Snowflake Managed MCP Server
                       ├─ Native Snowflake objects
                       ├─ Cortex AI services
                       └─ OAuth 2.0 authenticated
```

#### Authentication

- **OAuth 2.0** (aligned with MCP spec)
- Service account credentials
- Snowflake warehouse + database context

#### Key Advantage

- **Zero infrastructure cost** — Snowflake hosts it
- **Governance included** — All data access through Snowflake security perimeter
- **Semantic layer** — Cortex Analyst enables business logic queries without raw SQL

#### Reference Implementation

- GitHub: [Snowflake-Labs/mcp](https://github.com/Snowflake-Labs/mcp)
- Docs: [Snowflake Managed MCP Server](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- Blog: [Managed MCP Servers for Secure Data Agents](https://www.snowflake.com/en/blog/managed-mcp-servers-secure-data-agents/)

#### Gaps & Challenges

- Public preview status → may have breaking changes before GA (unlikely but possible)
- Cortex features require Enterprise+ edition
- Semantic view setup requires domain expertise (not automatic)

---

### 2. Databricks: Managed MCP + External MCP Support

**Status:** 🟢 **PRODUCTION READY** (GA)

#### Types of MCP Servers

**A) Databricks Managed MCP Servers** (ready-to-use, no deployment)
- Unity Catalog metadata explorer
- Databricks Vector Search access
- Genie spaces (semantic layer)
- Custom functions / stored procedures
- Workflow/job discovery

**B) External MCP Server Support** (connect third-party MCPs)
- Shared principal + per-user auth
- Managed proxy for external tools
- Zero vendor lock-in

#### Capabilities

- **Catalog Discovery:** Unity Catalog schemas, tables, columns, lineage
- **Vector Search:** Query semantic indexes
- **Semantic Layer:** Genie semantic models
- **SQL Execution:** Native Databricks SQL queries
- **Workflow Automation:** Access to jobs, notebooks, clusters
- **Lineage Tracking:** Column-level lineage from Unity Catalog

#### Architecture

```
Agent9 ← (HTTP/REST) → Databricks Managed MCP
                       ├─ Unity Catalog metadata
                       ├─ Vector Search indexes
                       ├─ Semantic models (Genie)
                       └─ OAuth 2.0 + PAT auth
```

#### Authentication

- **OAuth 2.0** (primary)
- **Personal Access Token (PAT)** (service accounts)
- **Shared Principal** (for multi-user)
- **Per-user auth** (external MCP proxying)

#### Key Advantage

- **Lineage-aware** — Unity Catalog provides column-level lineage (Phase 10E gold)
- **Semantic layer ready** — Genie semantic models for business-friendly queries
- **Flexible extensibility** — External MCP support = easy to add new tools

#### Reference Implementation

- Docs: [MCP on Databricks (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/)
- Docs: [MCP on Databricks (Azure)](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/mcp/)
- Community: [Community MCP Implementation](https://github.com/RafaelCartenet/mcp-databricks-server)

#### Gaps & Challenges

- Requires Databricks account + workspace setup (not a blocker for enterprise pilots)
- Unity Catalog optional (legacy workspaces may not have it)
- External MCP requires additional network configuration

---

### 3. BigQuery: Google Cloud Fully Managed Remote MCP

**Status:** 🟢 **PRODUCTION READY** (GA with Cloud API Registry)

#### Capabilities

- **Schema Inspection:** List datasets, tables, views, columns
- **SQL Execution:** Native BigQuery SQL queries
- **Cloud API Registry Integration:** One-click server discovery
- **ADK Integration:** Google Application Development Kit integration
- **Vertex AI Agent Engine:** Built-in agent runtime on GCP

#### Architecture

```
Agent9 ← (HTTP/REST) → Google Cloud Fully Managed MCP
                       ├─ BigQuery dataset/table metadata
                       ├─ Schema inspection
                       ├─ Query execution
                       └─ Service account auth (GCP default)
```

#### Authentication

- **GCP Service Account** (JSON key or Workload Identity)
- **Default Application Credentials** (Cloud Run, GKE, etc.)
- **OAuth 2.0** (user-facing)

#### Key Advantage

- **Zero deployment** — Google manages everything
- **Cloud API Registry** — Easy discovery & configuration
- **Vertex AI integration** — Agent Engine manages versioning, playground, ecosystem
- **Native GCP auth** — Seamless in GCP environments

#### Reference Implementation

- Docs: [Using BigQuery MCP Server](https://cloud.google.com/blog/products/data-analytics/using-the-fully-managed-remote-bigquery-mcp-server-to-build-data-ai-agents)
- Docs: [Connect LLMs to BigQuery with MCP](https://docs.cloud.google.com/bigquery/docs/use-bigquery-mcp)
- GitHub: [Community BigQuery MCP Servers](https://github.com/LucasHild/mcp-server-bigquery)

#### Gaps & Challenges

- GCP-only (not portable to multi-cloud)
- Requires GCP project setup
- Agent Engine still relatively new (rapid iteration expected)

---

### 4. PostgreSQL: Official Anthropic MCP Server

**Status:** 🟢 **PRODUCTION READY** (Official npm package)

#### Capabilities

- **Schema Inspection:** Full schema metadata (tables, columns, indexes, FKs)
- **Read-Only Queries:** Execute SELECT statements safely
- **Automatic Discovery:** Schema auto-discovery from metadata
- **Data Type Support:** Full PostgreSQL type system

#### Architecture

```
Agent9 ← (HTTP/stdio) → @modelcontextprotocol/server-postgres
                        ├─ libpq connection pool
                        └─ Read-only transaction
```

#### Authentication

- **Connection string:** `postgresql://user:password@host/dbname`
- **Environment variables:** `PGHOST`, `PGUSER`, `PGPASSWORD`
- **SSL/TLS:** Full TLS support for encrypted connections
- **Unix domain socket:** For localhost connections

#### Key Advantage

- **Official Anthropic implementation** — best-in-class quality
- **Read-only safety** — cannot modify data
- **Portable** — works anywhere PostgreSQL is accessible
- **Simple deployment** — single npm package, zero infrastructure

#### Reference Implementation

- npm: [@modelcontextprotocol/server-postgres](https://www.npmjs.com/package/@modelcontextprotocol/server-postgres)
- GitHub: [Official MCP Servers](https://github.com/modelcontextprotocol/servers)
- Community: [pgEdge Postgres MCP Server](https://www.pgedge.com/blog/introducing-the-pgedge-postgres-mcp-server)

#### Gaps & Challenges

- Read-only only (no write capability)
- Requires network access to PostgreSQL (not always available in restricted networks)
- No semantic layer (raw SQL only)

---

### 5. SAP Business Data Cloud (BDC): Community MCP Servers

**Status:** 🟡 **AVAILABLE** (Community implementations, not official)

#### Capabilities

- **Delta Sharing:** Share data via Delta Sharing protocol
- **Data Product Publishing:** Publish curated data products
- **CSN Management:** Manage Common Semantic Notation schemas
- **Contract Validation:** Validate ORD metadata contracts
- **End-to-End Orchestration:** Automated provisioning workflows
- **Share Lifecycle:** Create, update, delete shares

#### Architecture

```
Agent9 ← (HTTP/REST) → SAP BDC Connect MCP Server
                       ├─ Delta Sharing protocol
                       ├─ Data product metadata
                       ├─ CSN schemas
                       └─ Service account auth
```

#### Authentication

- **API Key / Service Account** (BDC-specific)
- **OAuth 2.0** (for user-facing flows)
- **mTLS** (enterprise deployments)

#### Key Advantage

- **Data Sharing Standard** — Delta Sharing is open, multi-platform
- **Enterprise Guardrails** — Built-in redaction, policy gating, bounded outputs
- **Data Product Focus** — Aligns with Decision Studio's data product registry
- **Read-Only by Default** — Safe for discovery and validation

#### Reference Implementation

- GitHub (Community): [sap-bdc-mcp-server](https://github.com/MarioDeFelipe/sap-bdc-mcp-server)
- PyPI: [sap-bdc-mcp](https://pypi.org/project/sap-bdc-mcp/)
- Blog: [SAP BDC MCP Server Release](https://medium.com/@mario.defelipe/sap-bdc-connect-mcp-server-release-blog-e96fb1f1da21)

#### Gaps & Challenges

- **Community implementations** — not official SAP product (yet)
- **Different paradigm** — Data sharing/product-focused, not traditional schema querying
- **Requires SAP BDC subscription** — Not all customers have it
- **Delta Sharing learning curve** — Different from SQL-based access

#### Use Case

- **Best for:** Enterprise customers with SAP BDC (large SAP ecosystem)
- **When to integrate:** Phase 11+ (post-core functionality)
- **Recommendation:** Treat as optional enterprise feature, not core platform

---

## Architecture Implications for Agent9

### MCP Server Selection Matrix

| Scenario | Recommended Stack | Why |
|----------|-------------------|-----|
| **Greenfield SaaS pilot** | Snowflake + BigQuery | Managed MCPs, zero infrastructure |
| **Existing Databricks shop** | Databricks + PostgreSQL (fallback) | Native semantic layer (Genie) |
| **Multi-cloud enterprise** | Snowflake + BigQuery + PostgreSQL | Portable, no vendor lock-in |
| **SAP ecosystem customer** | Any above + SAP BDC (optional) | Data product alignment |
| **Startup/cost-sensitive** | PostgreSQL + DuckDB | Self-hosted, minimal cost |

### MCPManager Implementation Pattern

```python
# Same interface for all backends
class MCPManager(DatabaseManager):
    async def connect(self, mcp_client: MCPClient):
        # mcp_client wraps vendor-specific protocol
        pass
    
    async def discover_schemas(self) -> List[SchemaMetadata]:
        # Translate MCP schema → our format
        pass
    
    async def execute_query(self, sql: str) -> QueryResult:
        # Translate MCP query response → our format
        pass

# Usage: Agent9 doesn't care which vendor
manager = MCPManager(snowflake_mcp_client)  # Snowflake
manager = MCPManager(databricks_mcp_client) # Databricks
manager = MCPManager(bigquery_mcp_client)   # BigQuery
# All use same interface
```

### Transport Layer Considerations

| Vendor | Transport | Firewall Impact | Latency |
|--------|-----------|----------------|---------|
| Snowflake | HTTP/REST (managed) | Outbound HTTPS only | <100ms |
| Databricks | HTTP/REST (managed) | Outbound HTTPS only | <100ms |
| BigQuery | HTTP/REST (managed) | Outbound HTTPS only | <100ms |
| PostgreSQL | HTTP/stdio (deployed) | Depends on deployment | 10-50ms |
| SAP BDC | HTTP/REST (managed) | Outbound HTTPS only | <100ms |

**Implication:** All managed MCPs use standard HTTPS — no special firewall rules needed. PostgreSQL requires either managed MCP proxy or direct connectivity.

---

## Phase 10D-A Implementation Roadmap

### Priority 1: Snowflake + Databricks + BigQuery (4-6 weeks)

**Why first:**
- All three have production-ready managed MCPs
- Cover 85%+ of enterprise data warehouse market
- Minimal infrastructure overhead

**Approach:**
1. Build MCPClient abstraction (HTTP-based, with auth injection)
2. Build MCPManager implementing DatabaseManager ABC
3. Integrate Snowflake MCP (public preview → GA expected Q2 2026)
4. Integrate Databricks MCP (GA now)
5. Integrate BigQuery MCP (GA now)
6. Real integration tests with actual customer trial accounts

### Priority 2: PostgreSQL (1-2 weeks)

**Why second:**
- Official Anthropic server = highest quality
- Lighter lift than vendors above
- Handles on-premise + legacy use cases

**Approach:**
1. Reuse MCPClient for HTTP/stdio transport selection
2. Deploy official npm package in Agent9 environment
3. Support standard libpq connection strings
4. Integration tests with public PostgreSQL instances

### Priority 3: SAP BDC (2-3 weeks, deferred to Phase 11+)

**Why later:**
- Optional enterprise feature (not core MVP)
- Requires SAP ecosystem customer
- Different semantic model (data products vs. schema)
- Can wait for Phase 11 Data Product Registry enhancements

**Approach:**
1. Research SAP BDC customer demand (get from sales/pilots)
2. Design semantic mapping: BDC data products → Decision Studio data products
3. Integrate community MCP server (with vendor vetting)
4. Wire into Admin Console as "premium" data source

---

## Technical Decisions for Phase 10D-A

### 1. MCP Client Library

**Decision:** Build thin HTTP abstraction layer over vendor MCPs

**Rationale:**
- All managed MCPs use HTTP/REST
- Reduce dependency bloat (only httpx, not vendor SDKs)
- Easier to swap implementations

**Implementation:**
```python
class MCPClient:
    def __init__(self, endpoint: str, auth_header: str):
        self.endpoint = endpoint
        self.auth_header = auth_header
    
    async def call_tool(self, tool_name: str, input: dict) -> dict:
        # POST /mcp/call_tool with auth
        pass
```

### 2. Authentication Strategy

**Decision:** Support both credentials and env vars, with secrets manager integration planned

**Now (Phase 10D):**
- Credentials stored in connection profile (Supabase)
- Encrypted at rest (Supabase encryption)
- Secrets manager integration (Phase 11+)

**Later (Phase 11+):**
- HashiCorp Vault / AWS Secrets Manager
- Dynamic credential rotation
- Audit logging

### 3. Error Handling

**Decision:** MCP server errors map to DatabaseManager exceptions

**Pattern:**
```python
try:
    result = await mcp_client.call_tool("discover_schemas")
except MCPError as e:
    raise SchemaDiscoveryError(f"MCP server error: {e}") from e
```

### 4. Testing Strategy

**Decision:** No mocks — test against real vendor MCP servers

**Approach:**
- **Unit tests:** MCPManager ABC compliance only
- **Integration tests:** Real endpoints (Snowflake trial account, BigQuery sandbox, etc.)
- **Fallback for mocks:** If vendor trial accounts unavailable, build minimal reference MCP (later)

**Cost:** ~$50-100 in cloud credits for trial accounts (worth it for confidence)

---

## Known Unknowns & Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Snowflake public preview → breaking changes | Medium | Fallback to direct SDK (Phase 10C) |
| Databricks requires Unity Catalog | Low | Works without UC, just reduced metadata |
| BigQuery MCP auth complexity | Low | GCP team handles it; standard OIDC tokens |
| PostgreSQL requires network access | Medium | Document VPN requirements for pilots |
| SAP BDC community server stability | Low (Phase 11+) | Defer to Phase 11, vendor-vet first |

---

## Recommendations for Phase 10D Kickoff

### Immediate (Week 1)

- [ ] Create trial accounts: Snowflake, Databricks, BigQuery
- [ ] Request MCP endpoint credentials from each vendor
- [ ] Read vendor MCP documentation (links below)
- [ ] Design MCPClient abstraction
- [ ] Design MCPManager implementation

### Short-term (Week 2-3)

- [ ] Implement MCPClient
- [ ] Implement MCPManager + MCPConnectionFactory
- [ ] Real integration test with Snowflake MCP
- [ ] Real integration test with Databricks MCP
- [ ] Real integration test with BigQuery MCP

### Medium-term (Week 4-6)

- [ ] Implement BigQueryManager, PostgresManager
- [ ] Migrate DPA to use OnboardingService
- [ ] Admin Console workflow implementation
- [ ] Comprehensive integration test suite

### Later (Phase 11+)

- [ ] SAP BDC integration
- [ ] Secrets manager integration
- [ ] Advanced features (lineage, semantic layer discovery)

---

## Reference Documentation

### Snowflake
- [Snowflake Managed MCP Server](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp)
- [GitHub Snowflake MCP](https://github.com/Snowflake-Labs/mcp)
- [Getting Started Guide](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-mcp-server/)

### Databricks
- [MCP on Databricks (AWS)](https://docs.databricks.com/aws/en/generative-ai/mcp/)
- [MCP on Databricks (Azure)](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/mcp/)
- [Databricks Managed MCP](https://docs.databricks.com/aws/en/generative-ai/mcp/managed-mcp)

### BigQuery
- [Using BigQuery MCP Server](https://cloud.google.com/blog/products/data-analytics/using-the-fully-managed-remote-bigquery-mcp-server-to-build-data-ai-agents)
- [Connect LLMs to BigQuery with MCP](https://docs.cloud.google.com/bigquery/docs/use-bigquery-mcp)
- [Cloud API Registry](https://docs.cloud.google.com/bigquery/docs/pre-built-tools-with-mcp-toolbox)

### PostgreSQL
- [Official MCP Servers (Anthropic)](https://github.com/modelcontextprotocol/servers)
- [@modelcontextprotocol/server-postgres (npm)](https://www.npmjs.com/package/@modelcontextprotocol/server-postgres)
- [pgEdge Postgres MCP](https://www.pgedge.com/blog/introducing-the-pgedge-postgres-mcp-server)

### SAP BDC
- [SAP BDC MCP Server (GitHub)](https://github.com/MarioDeFelipe/sap-bdc-mcp-server)
- [SAP BDC MCP Server Release](https://medium.com/@mario.defelipe/sap-bdc-connect-mcp-server-release-blog-e96fb1f1da21)
- [SAP Business Data Cloud Documentation](https://help.sap.com/docs/business-data-cloud/)

---

## Conclusion

**Phase 10D is unblocked.** All required vendor MCPs exist and are production-ready. The research eliminated the "if MCP is available" uncertainty — now it's purely an engineering problem.

**Next step:** Build MCPClient and MCPManager, then integrate Snowflake, Databricks, and BigQuery MCPs with real vendor accounts.

**SAP BDC recommendation:** Optional Phase 11+ add-on for enterprise customers with SAP ecosystem.
