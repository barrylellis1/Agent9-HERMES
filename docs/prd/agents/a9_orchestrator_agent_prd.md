# Orchestrator Agent PRD — Updated Alignment

## Overview

**Agent Name:** A9_Orchestrator_Agent  
**Status:** [MVP] — 7 of 7 workflow methods implemented  
**Last PRD Sync:** 2026-05-02  
**Code Location:** `src/agents/new/a9_orchestrator_agent.py`  
**Singleton Registry:** `src/registry/agent_registry.py`  
**Alignment:** 90% → 100% (removed REST/gRPC variants, documented core routing)

---

## 1. Purpose & Role in Workflow

The Orchestrator Agent is the **central nervous system** of Agent9-HERMES:
- **Single Point of Coordination** — all agent-to-agent communication flows through orchestrator
- **Dependency Resolution** — ensures agents are instantiated and connected in correct order
- **Workflow Routing** — maps user requests to appropriate agent sequences
- **Error Propagation** — catches and logs failures, returns structured error responses
- **Agent Registry** — singleton holder of all agent instances (pool pattern)

Operates as a **Singleton** — one instance per Python process, created at application startup.

---

## 2. Design Philosophy

### 2.1 Agent-to-Agent (A2A) Protocol

All agent communication uses **A2A protocol**:

```python
# Agent calls another agent: ALWAYS routed through Orchestrator
orchestrator = AgentRegistry.get_agent("orchestrator")

response = await orchestrator.call_agent(
    target_agent_name="a9_situation_awareness_agent",
    method_name="detect_situations",
    input=SituationDetectionRequest(
        principal_id="cfo_001",
        date_range=DateRange(start=..., end=...),
    )
)

# Response is Pydantic model
assert isinstance(response, SituationDetectionResponse)
```

**Key rules:**
- NO direct agent instantiation (`AgentA(config)`)
- NO direct method calls (`agent_a.method()`)
- ALL calls: `orchestrator.call_agent(target, method, input) → response`
- Input/Output: Pydantic models only (no raw dicts)

### 2.2 Dependency Resolution

**Problem:** Agents have dependencies (SA depends on KPI provider, DGA depends on DP agent, etc.). Can't instantiate agents in arbitrary order.

**Solution:** Orchestrator builds **dependency DAG** and instantiates in topological order:

```
Dependency Graph:
  RegistryFactory (no deps)
    ↓
  LLM_Service_Agent, Data_Product_Agent, Principal_Context_Agent
    ↓
  Data_Governance_Agent (depends on Data_Product_Agent)
    ↓
  Situation_Awareness_Agent, Deep_Analysis_Agent (depend on DGA)
    ↓
  Solution_Finder_Agent (depends on DA + MA)
```

**Orchestrator algorithm:**
1. Identify agents needed for workflow
2. Resolve dependencies recursively
3. Instantiate in order (parents before children)
4. Inject parent agents into children via config
5. Verify all agents connected

If dependency missing → raise `DependencyResolutionError`, workflow fails.

### 2.3 Scope: Core Routing Only

**Implemented:**
- A2A protocol routing (call_agent, call_agents_parallel)
- Dependency resolution DAG
- Singleton registry (one orchestrator per process)
- 7 workflow methods (see Section 3)
- Error handling + structured responses

**Out of Scope (Not Implemented):**
- REST/gRPC hybrid protocols — was speculative in v1.0 PRD; not in DEVELOPMENT_PLAN
- Load balancing across multiple orchestrator instances — roadmap; not in plan
- Circuit breaker for cascading failures — roadmap; not in plan
- Message queue buffering — roadmap; not in plan

---

## 3. Entrypoints (7 Workflow Methods — All Implemented)

### 3.1 run_situation_awareness_workflow()

```
Input:
  principal_id: str
  date_range: Optional[DateRange] = None
  kpi_id: Optional[str] = None  # Single-KPI mode

Output:
  SituationAwarenessWorkflowResponse:
    - situations: List[SituationCard]
    - opportunities: List[OpportunityCard]
    - kpi_definitions: List[KPIDefinition]
    - assessment_timestamp: datetime
    - workflow_status: "success" | "partial_failure" | "failure"
```

**Orchestration (Lines 150–220):**
1. Call PCA: `get_principal_context_by_id(principal_id)` → immutable context
2. Call SA: `detect_situations(principal_id, date_range, kpi_id)` → situations + opportunities
3. If empty response: log warning, return empty situations
4. Return aggregated response

**Error handling:**
- Principal not found → PrincipalNotFoundError (halt workflow)
- SA timeout/error → log, return partial response (workflow_status="partial_failure")

### 3.2 run_deep_analysis_workflow()

```
Input:
  situation_id: str  # From SA situation card
  principal_id: str

Output:
  DeepAnalysisWorkflowResponse:
    - situation_analysis: IsIsNotAnalysis
    - benchmark_segments: List[BenchmarkSegment]
    - root_causes: List[RootCauseHypothesis]
    - recommended_actions: List[ActionRecommendation]
    - workflow_status: "success" | "failure"
```

**Orchestration (Lines 230–320):**
1. Call SA: `get_situation_detail(situation_id)` → load situation card
2. Call PCA: `get_principal_context_by_id(principal_id)` → context
3. Call DGA: `validate_data_access(principal_id, kpi_id, data_product_id)` → guard access
4. Call DA: `analyze_situation(situation, principal_context)` → Is/Is Not analysis + root causes
5. Call MA: `analyze_market_opportunity(kpi_name, situation.title)` → market context
6. Synthesize: combine DA + MA into final response
7. Return response

**Error handling:**
- DGA denies access → DataAccessDeniedError (halt workflow)
- DA/MA timeout → skip that component, continue with partial analysis

### 3.3 run_solution_finding_workflow()

```
Input:
  situation_id: str
  deep_analysis_id: str
  principal_id: str

Output:
  SolutionFindingWorkflowResponse:
    - solution_recommendations: List[SolutionRecommendation]
    - trade_off_matrix: TradeOffMatrix
    - implementation_roadmap: List[ImplementationPhase]
    - roi_projections: List[ROIProjection]
    - hitl_approval_required: bool
    - workflow_status: "success" | "failure"
```

**Orchestration (Lines 330–450):**
1. Call DA: `get_analysis_detail(deep_analysis_id)` → retrieve prior analysis
2. Call SA: `get_situation_detail(situation_id)` → context
3. Call PCA: `get_principal_context_by_id(principal_id)` → principal context
4. Call SF: `generate_solutions(analysis, principal_context)` → 3 personas × Stage 1, synthesis
5. Call MA: `analyze_market_opportunity(kpi_name, recommendation.title)` → market signal for each recommendation
6. Call VA: `evaluate_solution_outcomes(recommendations, principal_context)` → DiD attribution + cost-of-inaction
7. Return recommendations + HITL approval requirement flag
8. If hitl_approval_required=true → workflow pauses, awaits human approval (see 3.4)

**Error handling:**
- SF fails → SolutionGenerationError (halt workflow)
- VA fails → return SF results only (recommendations without DiD attribution)

### 3.4 process_hitl_approval_decision()

```
Input:
  recommendation_id: str
  principal_id: str
  action: "approve" | "reject" | "request_modifications"
  notes: Optional[str]

Output:
  HitlApprovalResponse:
    - acknowledged: bool
    - next_step: str
    - briefing_generation_initiated: bool
```

**Orchestration (Lines 460–530):**
1. Validate recommendation belongs to principal (via DGA: validate_data_access)
2. Call SF: `process_hitl_feedback(recommendation_id, action, notes)` → record decision
3. If action="approve":
   - Call VA: `register_solution(recommendation_id, principal_id, expected_impact, cost_of_inaction)` → persist to Supabase
   - Call PIB: `generate_briefing(recommendation_id, principal_id)` → create email briefing
   - Return next_step="Briefing generated. Review and delegate via PIB panel."
4. If action="reject":
   - Call SF: `archive_recommendation(recommendation_id)` → mark as dismissed
   - Return next_step="Recommendation archived. Return to Deep Analysis to explore other root causes."
5. If action="request_modifications":
   - Call SF: `request_refinement(recommendation_id, notes)` → log feedback
   - Return next_step="Feedback recorded. Awaiting Solution Finder refinement."

### 3.5 run_kpi_assessment_workflow()

```
Input:
  principal_id: str
  kpi_id: str  # Single KPI, full assessment

Output:
  KPIAssessmentResponse:
    - kpi_definition: KPIDefinition
    - base_value: float
    - comparison_value: float
    - trend: "up" | "down" | "flat"
    - situations: List[SituationCard]
    - recommended_analysis: str
```

**Orchestration (Lines 540–600):**
1. Call PCA: `validate_principal_access(principal_id, kpi_id)` → confirm principal can assess KPI
2. Call SA: `detect_situations(principal_id, kpi_id=kpi_id)` → evaluate single KPI
3. Call DA: (optional) if situation detected, auto-run shallow Is/Is Not analysis
4. Return KPI assessment card

**Use case:** Principal clicks on a KPI tile in Registry Explorer, wants "Tell me about this KPI" → single-KPI assessment.

### 3.6 run_data_product_onboarding_workflow()

```
Input:
  data_product_name: str
  connection_profile_id: str
  client_id: str

Output:
  DataProductOnboardingResponse:
    - data_product_id: str
    - schema_inspection: SchemaInspection
    - contract_yaml: str (optional)
    - kpi_suggestions: List[KPISuggestion]
    - registered_kpis: List[str]
    - business_process_assignments: Dict[str, List[str]]  # BP → KPI mapping
    - workflow_status: "success" | "partial_failure"
```

**Orchestration (Lines 610–750):**
1. Call DPA: `inspect_schema(connection_profile_id)` → fetch columns, data types
2. Call KPI_Assistant: `suggest_kpis(data_product_id, domain)` → LLM suggestions
3. (User loop: refine KPIs via KPI_Assistant.refine_kpi() + validate_kpi())
4. Call KPI_Assistant: `finalize_kpi(kpi_definition, client_id)` → register to Supabase
5. Call DGA: `map_kpis_to_business_processes(kpi_ids, business_processes)` → assign to BPs
6. Call PCA: `update_principal_profiles(business_process_assignments)` → assign BPs to principals
7. Return onboarding summary

**Note:** This is an **interactive workflow** — user inputs decisions between orchestrator calls (not a single synchronous call). Steps 3–4 loop until user is satisfied.

### 3.7 run_enterprise_assessment_workflow()

```
Input:
  client_id: str
  principal_ids: Optional[List[str]] = None  # If None, assess all
  kpi_ids: Optional[List[str]] = None
  date_range: DateRange

Output:
  EnterpriseAssessmentResponse:
    - assessments_by_principal: Dict[str, SituationAwarenessWorkflowResponse]
    - aggregate_situations: List[SituationCard]  # Merged across principals
    - cross_principal_opportunities: List[OpportunityCard]
    - execution_summary: dict  # {kpi_count, principal_count, errors, timeouts}
```

**Orchestration (Lines 760–900):**
1. If principal_ids not provided: call PCA `list_principal_profiles(client_id)` → all principals for client
2. For each principal in parallel (up to 10 concurrent):
   - Call SA: `detect_situations(principal_id, kpi_ids, date_range)` → assess
   - Collect situations + opportunities
3. Merge results: aggregate situations by KPI, deduplicate opportunities
4. Return enterprise-level assessment

**Use case:** Run nightly enterprise assessment: "For all lubricants principals, what are the top 50 situations requiring attention?"

**Async pattern:** Orchestrator uses `asyncio.gather()` for parallel assessment. See `run_enterprise_assessment.py` for implementation.

---

## 4. Agent Registry (Singleton Pattern)

**File:** `src/registry/agent_registry.py`

**Singleton access:**
```python
# Anywhere in codebase
from src.registry.agent_registry import AgentRegistry

orchestrator = AgentRegistry.get_agent("orchestrator")  # Always returns same instance
sa_agent = AgentRegistry.get_agent("a9_situation_awareness_agent")

# Or via class methods
orch = AgentRegistry.get_orchestrator()  # Same as get_agent("orchestrator")
```

**Lifecycle:**
```
Application startup:
  1. FastAPI app initialization
  2. Call: await AgentRegistry.initialize()  # Dependency resolution, agent instantiation
  3. All agents now available via get_agent()

Application shutdown:
  1. Call: await AgentRegistry.disconnect_all()  # Cleanup connections
  2. Agents removed from registry
```

**Registry structure:**
```python
class AgentRegistry:
    _agents: Dict[str, BaseAgent] = {}  # {agent_name: agent_instance}
    _lock: asyncio.Lock  # Thread-safe access
    
    @classmethod
    async def get_agent(cls, name: str) -> BaseAgent:
        """Return agent instance or raise AgentNotFoundError"""
    
    @classmethod
    async def initialize(cls):
        """Build dependency DAG, instantiate all agents"""
    
    @classmethod
    async def disconnect_all(cls):
        """Cleanup all agent connections"""
```

---

## 5. Implementation Status

| Entrypoint | Status | Lines | Notes |
|---|---|---|---|
| `run_situation_awareness_workflow()` | ✅ Production | 150–220 | Called by /assessments/run API |
| `run_deep_analysis_workflow()` | ✅ Production | 230–320 | Chained after SA; calls DA + MA |
| `run_solution_finding_workflow()` | ✅ Production | 330–450 | Chained after DA; HITL approval gate |
| `process_hitl_approval_decision()` | ✅ Production | 460–530 | Processes human decisions from HITL panel |
| `run_kpi_assessment_workflow()` | ✅ Production | 540–600 | Single-KPI assessment (Registry Explorer) |
| `run_data_product_onboarding_workflow()` | ✅ Production | 610–750 | 8-step orchestrated onboarding |
| `run_enterprise_assessment_workflow()` | ✅ Production | 760–900 | Parallel multi-principal assessment |
| Agent Registry (Singleton) | ✅ Production | all | Dependency resolution + pool management |
| A2A Protocol enforcement | ✅ Production | all | All agent calls via call_agent() |

---

## 6. Known Limitations

1. **No request queuing** — synchronous only; high load will block

2. **No cascading failure isolation** — if one agent crashes, entire workflow fails (no circuit breaker)

3. **No distributed tracing** — workflow execution not logged to external tracing system

4. **Single-threaded dependency resolution** — DAG built on every app startup; no caching

5. **No dynamic agent registration** — agents must be listed in dependency DAG at compile time; can't add new agents at runtime

6. **DGA post-bootstrap wiring dependency (Critical)** — Data Governance Agent is wired after all agents instantiate via `runtime._wire_governance_dependencies()` (src/runtime.py). If DGA wiring fails, all subsequent `run_deep_analysis_workflow()` and `run_solution_finding_workflow()` calls raise `RuntimeError` with no fallback. This is a mandatory hard dependency — workflows cannot proceed without DGA. Mitigation: DGA wiring must be idempotent and should fail loudly during app startup rather than silently during a user workflow.

7. **Timeout cascades with no graceful degradation** — Multi-agent workflow chains (SA → DA → SF) are sequential. If DA times out (30s+), SF never executes and user receives partial response. Optional agents (MA for market signals) can timeout/fail, but this still blocks the entire workflow response. No circuit breaker for optional enrichment. Mitigation: Phase 10+ can parallelize independent agents (MA can run async while DA executes) and skip optional context gracefully.

---

## 7. Dependencies

- **AgentRegistry** — singleton holder of all agent instances
- **All 13 production agents** — direct dependencies (SA, DA, SF, DPA, DGA, PCA, MA, etc.)
- **RegistryFactory** — resolution of providers for dependent agents
- **A2A Protocol** — Pydantic models for agent I/O

---

## 8. Testing

**Unit tests:** `tests/unit/test_a9_orchestrator_agent.py`
- ✅ Workflow routing (situation_awareness → deep_analysis → solution_finding)
- ✅ Dependency resolution (agents instantiated in correct order)
- ✅ Error propagation (DGA denial → workflow halt)
- ✅ HITL feedback processing (approve → briefing generation)
- ✅ A2A protocol enforcement (no direct agent calls)

**Integration tests:** Run against live agents + Supabase
- Situation awareness workflow → returns situations
- Deep analysis workflow → returns root causes
- Solution finding workflow → returns recommendations + HITL flag
- Enterprise assessment → parallel multi-principal assessment

---

## 9. Changelog

**v1.0 (2025-10-15)** — Initial MVP with 7 workflow methods

**v2.0 (2026-02-28)** — Dependency resolution + A2A protocol enforcement

**v3.0 (2026-05-02)** — Aligned with actual implementation:
- Documented all 7 workflow methods with exact line numbers
- Removed REST/gRPC hybrid protocols (not planned in DEVELOPMENT_PLAN)
- Removed load balancing + circuit breaker (not in plan)
- Removed message queue buffering (not in plan)
- Clarified A2A protocol is the only call mechanism
- Documented Agent Registry singleton pattern
- Updated dependency resolution algorithm
- Clarified scope: core routing only, not multi-service architecture
- Updated error handling + partial failure modes
- Added DGA post-bootstrap wiring dependency (critical) and timeout cascade limitations

---
