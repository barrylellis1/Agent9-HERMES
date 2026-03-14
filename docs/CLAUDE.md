# Documentation — docs/

## Architecture Docs: docs/architecture/

Read before designing changes to agents, registries, or workflows:

| File | Contents |
|---|---|
| `Agent9_Architecture_Overview.md` | Full system architecture, principles, components |
| `orchestration_architecture.md` | Orchestrator-driven design principles |
| `orchestrator_implementation.md` | Dependency resolution implementation detail |
| `core_workflow_diagram.md` | Visual workflow diagrams, agent interaction sequences |
| `analytical_methodology_positioning.md` | KT + MBB architecture rationale, IS NOT as control group, competitive positioning |

Technical debt and known issue plans:

| File | Issue |
|---|---|
| `business_process_provider_initialization.md` | Provider init warnings and patterns |
| `data_governance_agent_connection.md` | Missing DG → DP connection pattern |
| `principal_id_based_lookup_plan.md` | Migration from role-based to ID-based lookup |
| `business_process_hierarchy_blueprint.md` | Future hierarchical BP design |
| `registry_display_ui_updates.md` | Decision Studio UI updates for business processes |

## Agent PRDs: docs/prd/agents/

One PRD per implemented agent. **Read the PRD before adding new capabilities to an agent.**

- `a9_orchestrator_agent_prd.md`
- `a9_principal_context_agent_prd.md`
- `a9_data_governance_agent_prd.md`
- `a9_data_product_agent_prd.md`
- `a9_situation_awareness_agent_prd.md`
- `a9_deep_analysis_agent_prd.md`
- `a9_solution_finder_agent_prd.md`
- `a9_llm_service_prd.md`
- `a9_nlp_interface_agent_prd.md`
- `a9_kpi_assistant_agent_prd.md`
- `a9_value_assurance_agent_prd.md`

## Update Rule

When adding new agent capabilities:
1. Update the relevant PRD in `docs/prd/agents/`
2. Update the agent's row in the **Current Capabilities** table in root `CLAUDE.md`

## Other Reference Docs (project root)

- `AGENT_SPECIFICATIONS.md` — extracted PRD requirements and protocol violations checklist
- `TECHNICAL_DEBT.md` — full technical debt inventory
- `DEVELOPMENT_PLAN.md` — **Active development plan** (Phase 7+: VA, Opportunity DA, Business Optimization)
- `IMPLEMENTATION_PLAN.md` / `HERMES_IMPLEMENTATION_PLAN.md` — **DEPRECATED** historical plans (Phases 1-6, completed)
