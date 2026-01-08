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
