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
| `hitl_decision_philosophy.md` | HITL gate design, Solution Q&A, cognitive dissonance principle, context stack, approval flow |
| `llm_prompt_redesign_da_sf.md` | DA+SF prompt redesign proposal: structured outputs, principal/business context contract, prompt slimming (Phase 13 Cat 2/4 = Phase 15 Stages A–C) |
| `theory_layer_design.md` | Theory layer: per-client causal model + assumption register, HITL-accreted + template-seeded, provenance ladder; SF/LLM trust pillars = DEVELOPMENT_PLAN Phase 15 Stages D–F |
| `persona_council_experiments.md` | **Experimental record + method, no build authorised.** Seven arms testing whether consulting personas ask different questions (Stage I B-3). Findings: topic selection converges under every configuration; content differentiates with roster differentiation; a better model converges weak personas and diverges genuine ones; the differentiation survives stripping the authored profiles. Contains the transferable methodology lessons (compute the null, one variable per run, predict before running, beware stacked tests) and a phased screening design. §7b adds the **evidence-scope experiment** (6 real SF runs): causal traversal depth showed no measurable effect because the *direct* edge's mechanism prose already narrates what the 2-hop node contributes — graph depth and mechanism text are substitutes — while market-signal routing produced a checkable correction (indexing a base-oil surcharge to Group I/II spot rather than to WTI crude). **Next spend is an outcome measure, not another arm** |
| `problem_framing_design.md` | **Design settled, build in progress — Phase 19.** DQ link 1 (appropriate frame) failed both the 13-run corpus adjudication and a second, structurally different problem shape (§10–11) — the only systematic cap left on the chain, empirically confirmed rather than merely argued. Mechanism: `problem_framing` becomes the **mandatory first topic** of the existing refinement interview (not an unbundled pre-DA step — that was superseded), gating "Generate Solutions" until answered; SCQA generation defers until the frame is chosen, then generates against it. Alternatives shown at 1–2 hops via the causal graph, unfiltered by direction, plus (Decision #12) a labeled market-conflict alternative sourced from Market Analysis, now wired as an input to DA's own framing/SCQA construction rather than a sidecar between DA and SF. Build sequencing: `C:\Users\Blell\.claude\plans\with-this-now-in-goofy-meteor.md`; status: `DEVELOPMENT_PLAN.md` Phase 19 |
| `decision_quality_rubric.md` | **Design note, not built.** The outcome measure Stage H/I has been missing — Stanford SDG **Decision Quality** (six links, weakest-link scoring) adopted as the referent that `persona_council_experiments.md` §5 says must precede further optimisation. Maps each DQ link to fields already present in the SF payload and to existing `src/analysis` instruments; records a **falsifiable prediction before scoring** (links 1 *frame* and 2 *alternatives* fail; 3/5/6 pass; the moderator grades only the links already passing). Corpus is the 33 options in `tools/ab_harness/scope_arm_*.json` — no new API spend — stratified pre/post the `_build_kt_summary` fix. Chosen over MAP / Vroom-Yetton / KT-DA / AHP for stated reasons: DQ is a *standard*, not a *procedure*, so it grades the artefact without asking a customer to change how they meet |
| `kpi_semantic_contract.md` | **Design note, not built.** DGA-governed semantics per KPI — additivity, unit class, sign convention, scope eligibility (§3), plus **sliceability** (§4): which dimensions a KPI must *not* be cut by, as a KPI × dimension deny list derived from `check_slice_validity.py` rather than authored. Turns `groundedness`'s cross-segment-summation *heuristic* into a declared *fact*, and gives the −457% margin-by-customer failure its first check anywhere. No longer parked (Stage H A/B closed); pairs with token substitution |

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
