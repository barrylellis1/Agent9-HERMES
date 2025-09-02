# Agent9 Blueprint

_A high-level architecture & standards guide consolidating essential guidance for the Agent9 platform._  
**Audience:** architects, contributors, reviewers, Cascade.

---

## 1. Layered Reference Model
```
┌─────────────────────────┐
│     Interface Layer     │  (Decision Studio UI, HTTP/CLI APIs)
├─────────────────────────┤
│   Orchestration Layer   │  (A9_Orchestrator_Agent, LangGraph workflows)
├─────────────────────────┤
│    Capability Layer     │  (Situation, Analysis, Solution, etc.)
├─────────────────────────┤
│    Governance Layer     │  (Data Governance, KPI Registry, Compliance)
├─────────────────────────┤
│        Data Layer       │  (DuckDB test data, SAP Datasphere, contracts)
└─────────────────────────┘
```
Each agent & service maps to exactly **one primary layer**; cross-layer calls must traverse _downward_ only via the orchestrator.

## 2. Shared State Schema
All agents exchange a **typed Pydantic `Context`** object.
```python
from pydantic import BaseModel
class Context(BaseModel):
    principal_id: str
    workflow_id: str
    situation: SituationContext | None = None
    analysis: AnalysisContext | None = None
    solution: SolutionContext | None = None
    metadata: dict = {}
```
• `Context` is **append-only**; agents must not mutate previous sections.  
• Persist interim state via the **Agent Registry** at workflow transitions.

## 2.1 Registry Resources
Agent9 relies on a comprehensive registry system as the source of truth for configuration and metadata. See [Registry Resources](registry_resources.md) for detailed documentation of available registries:

- **Principal Registry**: Principal profiles and role definitions
- **Business Process Registry**: Business process definitions across domains
- **KPI Registry**: Key performance indicators and their definitions
- **Data Product Registry**: Data product definitions and metadata
- **Business Glossary**: Business terms and their technical mappings

## 3. Tracer-Bullet MVP Workflow
1. `A9_Situation_Awareness_Agent` populates `context.situation`.  
2. `A9_Deep_Analysis_Agent` consumes it, writes `context.analysis`.  
3. `A9_Solution_Finder_Agent` consumes analysis, writes `context.solution`.  
4. HITL checkpoints via email action links.  
All orchestrated by `A9_Orchestrator_Agent` using **async `create_from_registry`** calls.

## 3.1 Workflow Catalogue (YAML source-of-truth)
| Workflow | YAML Path | Typical Trigger | Key Agents |
|----------|-----------|-----------------|------------|
| Automated Situational Awareness | `workflow_definitions/automated_situational_awareness.yaml` | Scheduled daily run / KPI update event | Orchestrator → KPI/Data agents → Situation Awareness |
| Problem Deep Analysis | `workflow_definitions/problem_deep_analysis.yaml` | HITL request after situation flagged | Deep Analysis, Data Product, Orchestrator |
| Opportunity Deep Analysis | `workflow_definitions/opportunity_deep_analysis.yaml` | HITL request or Innovation workflow | Opportunity Analysis, Deep Analysis |
| Solution Finding | `workflow_definitions/solution_finding.yaml` | After analysis / innovation | Solution Finder, Implementation Planner |
| Solution Deployment | `workflow_definitions/solution_deployment.yaml` | Once solution approved | Deployment Service / Implementation Tracker |
| Business Optimization | `workflow_definitions/business_optimization.yaml` | Executive optimisation initiative | Business Optimization agent suite |
| Innovation Driver | `workflow_definitions/innovation_driver.yaml` | Innovation campaign kickoff | Innovation Driver, GenAI Expert |
| Value Assurance | `workflow_definitions/value_assurance.yaml` | Post-deployment monitoring | Situation Awareness, KPI Registry |
| Environment Administration | `workflow_definitions/agent9_environment_administration.yaml` | Scheduled maintenance | Environment Admin, Registry services |

Each YAML defines nodes, edges, validations and outputs; the orchestrator loads it at runtime to build a LangGraph DAG.

## 4. Design-Standards Checklist (CI-Enforced)
| Rule | Target | Notes |
|------|--------|-------|
| File length ≤ 300 lines | *.py | Skip generated code |
| `A9_` prefix & naming convention | agents/* | See memory rules |
| Strict A2A I/O (Pydantic) | entrypoints | No raw dicts |
| Async registry creation | create_from_registry | No direct instantiation |
| Structured logging | all modules | `logger = structlog.get_logger()` |
| Error classes | agents/errors.py | ConfigurationError, ProcessingError, ValidationError |

## 5. Runtime KPIs & SLAs
| KPI | Target |
|-----|--------|
| Design turnaround | ≤ 8 h |
| Post-implementation defect rate | ≤ 5 % |
| Situation Awareness latency | < 2 min per run |
| Daily KPI coverage | 20 KPIs |

## 6. Cost-Quality Monitoring
Monitor token spend & composite quality score per build; flag regressions if cost ↑10 % without quality gain.

## 7. Open Questions
1. Agent unavailability strategy.  
2. Auth mechanism for internal calls (JWT vs mTLS).  
3. Compliance audit logging detail.

---
*Version: 0.1  |  Generated 2025-08-30*
