# Agent9 MVP Implementation Plan (November 2025 Refresh)

## 1. Current State Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Agent infrastructure (registry, protocols, shared models) | **Complete** | Orchestrator + AgentRegistry live in `src/agents/new/`, agents implement protocol interfaces and share registry providers.@src/agents/new/a9_orchestrator_agent.py#1-208 |
| Core workflow agents | **Implemented** | Principal Context, Data Governance, Data Product, Situation Awareness, Deep Analysis, and Solution Finder agents exist in `src/agents/new/` and follow PRD responsibilities.@src/agents/new/a9_principal_context_agent.py#1-200@src/agents/new/a9_data_governance_agent.py#1-200@src/agents/new/a9_data_product_agent.py#1-200@src/agents/new/a9_situation_awareness_agent.py#1-200@src/agents/new/a9_deep_analysis_agent.py#1-200@src/agents/new/a9_solution_finder_agent.py#1-107 |
| Decision Studio UI | **MVP debug UI** | Streamlit-based debugging experience; consumer-grade UI pending (see Phase 4).
| Data sources | **FI schema available; Sales schema onboarding** | DuckDB demo data in place; BigQuery Sales schema work underway to enable cross-source stories.
| Testing | **Partial** | Unit coverage improved, but cross-agent integration, Decision Studio UI, and multi-source regression tests still required.

## 2. Updated Phased Plan

### Phase 1 – Foundation Validation (Status: Complete)
- Confirm orchestrator-driven lifecycle, protocol compliance, and logging standards across existing agents.
- Catalog remaining gaps in config models, cards, and tests; track tech debt for future sprints.

### Phase 2 – Data Foundations & Cross-Source Enablement (Status: In Progress)
- Onboard Sales schema in Google BigQuery; document ingestion and environment configuration.
- Extend Data Product & Data Governance agents for dual-source KPI metadata, including config/card/test updates.
- Update registry providers so KPIs resolve across FI and Sales, and ensure Principal Context covers new personas/scopes.

### Phase 3 – Workflow Completion & Agent Coverage (Status: In Progress)
- Finish end-to-end workflows: Situation Awareness → Deep Analysis → Solution Finder with DG/DP/NLP/LLM orchestration.
- Validate SQL generation stays within Data Product Agent while DG manages KPI thresholds/mappings.
- Add integration tests for SA→DP→DG→PC interactions and BigQuery-backed flows; ensure orchestrator-driven execution in Decision Studio.

### Phase 4 – Decision Studio Upgrade (Status: Planned)
- Replace the Streamlit debug UI with a consumer-grade Decision Studio aligned to the product vision doc.
- Implement hierarchical situation inbox, inline HITL actions, KPI evaluation summaries, and assignment workflows.
- Script investor demo narrative showcasing FI + Sales KPI alignment and DG mediation; rehearse end-to-end experience.

### Phase 5 – Compliance & Launch Prep (Status: Planned)
- Achieve comprehensive unit, integration, and UI test coverage, including multi-source scenarios.
- Complete agent card/config synchronization, documentation updates, and Situation model finalization.
- Run performance, reliability, and environment-promotion checks; finalize demo environment start/stop procedures.

### Phase 6 & Registry Externalization (Status: Implemented)
- **Architecture**: Implemented "Hybrid Schema" pattern with `DatabaseManager` abstraction supporting DuckDB, Postgres, and BigQuery.
- **Components**: Created `DatabaseRegistryProvider`, `PostgresManager`, and updated `RegistryBootstrap` to support `DATABASE_URL`.
- **Status**: The registry is now database-agnostic and supports BYODB (Bring Your Own Database). Legacy Supabase-specific providers have been deprecated in favor of the generic provider.
- **Next Steps**: Validate multi-tenant isolation and perform final migration of production data if applicable.

## 3. Testing & Compliance Backlog
- **Completed**: 
  - Core agents implement required protocols.
  - Orchestrator-driven lifecycle enforced.
  - Baseline unit tests in place.
  - **Registry Database Provider tests passed.**
- **Outstanding**:
  - Multi-source integration tests covering DG-mediated KPI resolution.
  - Decision Studio UI regression and investor-demo smoke tests.
  - Automated checks for agent card/config parity and architectural guardrails.
  - Performance monitoring for BigQuery-backed workflows.

## 4. Immediate Action Items (Q4 2025)
1. Finalize Sales schema onboarding and update registry/config artifacts.
2. Close workflow integration gaps and add tests for DG/DP/SA/PC orchestration.
3. Launch Decision Studio upgrade sprint after Sales schema is live, targeting investor demo readiness.
4. Establish CI gates for protocol compliance, agent card sync, and decision-studio UI checks.
