# A9_Solution_Finder_Agent Card

Status: MVP Active

## Overview
The `A9_Solution_Finder_Agent` systematically generates, evaluates, and recommends solutions for diagnosed problems (often from Deep Analysis). It produces a trade-off matrix and emits a single HITL approval event per cycle (per PRD). It leverages the LLM Service to run an expert persona debate and synthesize a consensus rationale, with business context injection for domain-specific recommendations.

## Protocol Entrypoints
- `recommend_actions(request: SolutionFinderRequest) -> SolutionFinderResponse`
- `evaluate_options(request: SolutionFinderRequest) -> SolutionFinderResponse`

Models defined in `src/agents/models/solution_finder_models.py`.

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_Solution_Finder_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    # Core behavior
    hitl_enabled: bool = True  # Single HITL event per cycle
    enable_llm_debate: bool = False  # Toggle persona debate and consensus
    expert_personas: List[str] = [
        "QA Lead", "Operations Manager", "Finance Controller"
    ]
    # Scoring weights
    weight_impact: float = 0.5
    weight_cost: float = 0.25
    weight_risk: float = 0.25
    
    # Hybrid Council settings
    enable_hybrid_council: bool = False
    consulting_personas: List[str] = []
    council_preset: Optional[str] = None

    # Orchestration & logging
    require_orchestrator: bool = True
    log_all_requests: bool = True
```

## Dependencies
- `A9_Deep_Analysis_Agent` (consumes its output for context)
- `A9_LLM_Service_Agent` (persona debate and narrative synthesis; fallback acquisition from AgentRegistry if not injected)

## LLM Configuration
| Task Type | Optimal Model | Rationale |
|-----------|---------------|-----------|
| `solution_finding` | `o1-mini` | Complex multi-perspective reasoning for solution generation and trade-off analysis |

Environment variable override: `OPENAI_MODEL_SOLUTION`

## Key Features (Dec 2024)
- **Business Context Injection**: Loads domain-specific context from `src/registry_references/business_context/*.yaml` to inform LLM recommendations
- **Enhanced Problem Statement**: Dynamically constructs quantitative problem statements from Deep Analysis change points (KPI, delta, dimension, attribute)
- **Principal Input Support**: Accepts user-defined priorities and constraints via `PrincipalInputPreferences` to guide solution generation
- **Fallback LLM Acquisition**: If LLM service not injected by orchestrator, acquires directly from `AgentRegistry`
- **Prompt Constraints**: Forbids "more analysis" solutions; requires actionable, implementable recommendations

## Principal-Driven Approach (Dec 2024)
- **Decision Style to Persona Mapping**: Uses principal's `decision_style` from their profile to select appropriate consulting personas:
  - `analytical` → McKinsey-style (root cause, MECE, hypothesis-driven)
  - `visionary` → BCG-style (portfolio view, growth-share, value creation)
  - `pragmatic` → Bain-style (operational excellence, quick wins, results-first)
  - `decisive` → McKinsey-style (structured decision-making, clear trade-offs)
- **Persona Selection Priority**: Request override → decision_style → role affinity → MBB default
- **Framing Context**: All responses include `framing_context` with transparency about personas used and presentation style
- **Guardrails**: Agent adapts presentation FOR the principal, does NOT speak FOR the principal or impersonate colleagues

## Dynamic Diverse Council (Dec 2025)
- **Recommended Council Integration**: Accepts `recommended_council_members` from Deep Analysis Problem Refinement
- **Dynamic Cross-Review**: Cross-review section uses actual persona IDs from the diverse council (not hardcoded MBB)
- **Persona Resolution**: Uses `get_consulting_persona()` to resolve persona IDs from the consulting personas registry
- **LLM Instruction**: Explicit instruction to LLM to use the exact persona IDs provided in the cross-review JSON template
- **Persona Safety**: Initializes `persona_ids` before prompt construction to guarantee identifiers are always defined, even when debate presets are overridden.

## Multi-Call Architecture + Quality Fixes (Mar 2026 — Phase 11)
- **Multi-call debate stages**: `stage1_only` → `hypothesis` → `cross_review` → `synthesis`; Stage 1 runs 3 parallel Haiku calls (McKinsey/BCG/Bain); synthesis uses Sonnet
- **`impact_estimate` field**: Added to `SolutionOption` Pydantic model; LLM-generated recovery range extracted from synthesis output (e.g. "2.1–3.4pp Gross Margin recovery")
- **Recommendation rationale**: Fixed extraction — now reads `parsed.get("recommendation_rationale")` instead of hardcoded boilerplate text
- **Stage 1 hypothesis restoration**: `stage_1_hypotheses` re-attached to cross_review/synthesis responses for progressive reveal in Council In Session UI
- **`max_tokens`**: Raised to 16384 to prevent synthesis truncation on complex briefings

## Synthesis Prompt Quality Improvements (Mar 2026 — Phase 12)
- **next_steps**: Requires minimum 4 items with action verb + named role + specific deliverable + deadline; rejects generic boilerplate
- **recovery_range**: RECOVERY RANGE ANCHORS include failure-mode fallback (30–60% of observed variance) to prevent LLM outputting 0.0
- **CONSISTENCY CHECK**: Validates that mix-shift recommendations target segments with better margins than the problem segment; forces explicit paradox resolution if not
- **unresolved_tensions.requires**: Format instruction with concrete example replaces enum placeholder ("human judgment / more data / stakeholder input")
- **recommendation_rationale**: Explicitly requires entity-specific rationale citing named data points; forbids generic boilerplate
- **UnresolvedTension model**: `requires` field docstring corrected to describe expected format, preventing LLM from echoing meta-labels verbatim

## Dual-Framing Pipeline — Benchmark Replication (Mar 2026)
- **`_extract_deep_analysis_summary()`**: Extracts top-3 `internal_benchmark` segments from DA output into `summary["benchmark_segments"]`
- **`_trim_deep_analysis_context()`**: Passes benchmark segments through in the trimmed DA context dict
- **Stage 1 prompts**: When `internal_benchmarks` present, task item 5 instructs each persona to consider replication strategies
- **Synthesis prompt**: `INTERNAL BENCHMARK FEASIBILITY` section added — at least one option MUST address replication when benchmark_segments are present

## Market Analysis Integration (Mar 2026)
- **Deep Analysis Workflow**: Market Analysis Agent now runs at the END of Deep Analysis workflow. Market signals are attached to DA output as `market_signals` field and passed downstream.
- **Problem Refinement Pipeline**: Problem Refinement Chat receives signals from DA output via `external_context`, enabling targeted questions anchored in market facts.
- **Solution Finding**: Market signals arrive via DA output → SF preferences as external_context. No separate MA call in SF. Post-synthesis enrichment has been removed.
- **`pending_market_signals` field**: Reserved on `SolutionFinderResponse` for future HITL signal confirmation workflow (not yet actively populated).
- **Backward Compatibility**: `market_intelligence` field is now always None (deprecated).

## Compliance
- A2A Pydantic IO for requests/responses
- Orchestrator-driven lifecycle; single HITL event per cycle
- Full audit logging of options, scoring, recommendation, and human approvals

## Deliverables (MVP)
- Ranked options with perspectives from expert personas
- Trade-off matrix (impact/cost/risk)
- Problem reframe (Situation/Complication/Question)
- Recommendation + rationale
- HITL approval context and audit trail

## Fast Debate Mode — Phase 10D (Apr 2026)

**Dev/prod performance split** controlled by `VITE_DEBATE_MODE` env var:

| Mode | Stages | API Calls | Latency | Use Case |
|------|--------|-----------|---------|----------|
| `fast` | stage1_only → synthesis | 2 | ~3 min | Development testing |
| `full` | stage1_only → hypothesis → cross_review → synthesis | 4 | ~9 min | Production |

- `.env.development`: `VITE_DEBATE_MODE=fast` — skips hypothesis + cross_review stages
- `.env.production`: `VITE_DEBATE_MODE=full` — all 4 stages for maximum depth
- Frontend conditional in `useDecisionStudio.ts` and `CouncilDebatePage.tsx`
- Backend stages 2-4 hit identical Sonnet endpoint — skipping 2-3 saves ~6 min with equivalent output quality

**DA context trimming** (token optimization):
- When Stage 1 hypotheses are present, `deep_analysis_context` (~8-12K tokens) is excluded from synthesis payload
- `da_summary` carries all key signals — full DA context is redundant when hypotheses already incorporate it
- Conditional: `_include_full_da = not stage_1_hyps_dict`

## Recent Updates (Apr 2026)
- Removed debug print statements from exception handling (cleanup)
- Error logging via logger.info() for LLM debate failures (fallback to heuristic)
- Phase 10D fast debate mode and DA context trimming shipped

- May 2026: Bug fixes — NaN normalization, multi-tenant kpi_registry collision fix, comparison value extraction
