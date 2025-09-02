---
configuration:
  name: A9_Performance_Optimization_Agent
  version: '1.0'
  capabilities:
  - performance_monitoring
  - bottleneck_detection
  - optimization_recommendations
  - recommendation_generation
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Performance_Optimization_Agent
- **Team / Agent Context Tags:** performance_team, performance_optimization
- **Purpose:** Monitors system performance, detects bottlenecks, and recommends optimizations to maintain SLA/KPI targets.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9PerformanceOptimizationAgentConfig(BaseModel):
    monitor_interval_sec: int = 60
    alert_threshold_ms: int = 1000
    enable_llm_reco: bool = False
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `monitor_performance` | Monitor metrics and detect issues | `PerformanceMonitorRequest` | `PerformanceStatus` | emits alerts |
| `recommend_optimization` | Suggest optimizations | `OptimizationRequest` | `OptimizationRecommendation` | logs events |

Supported hand-off commands / state updates:
- `escalate_to_orchestrator` – escalate critical performance incident

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 90%
  - Integration workflow test present
- **Runtime KPIs & Monitoring Hooks**
  - Mean monitoring latency < 100 ms
  - Recommendation accuracy ≥ 95 %
  - Incident false-positive rate ≤ 2 %

---

# Error Handling
Standard error handling via AgentExecutionError and AgentInitializationError.

# Example Usage
```python
from src.agents.new.A9_Performance_Optimization_Agent import A9_Performance_Optimization_Agent
from src.agents.new.agent_config_models import A9PerformanceOptimizationAgentConfig
config = {
    "name": "A9_Performance_Optimization_Agent",
    "version": "1.0",
    "capabilities": [
        "performance_monitoring",
        "bottleneck_detection",
        "optimization_recommendations",
        "recommendation_generation"
    ],
    "config": {},
    "hitl_enabled": False
}
agent = A9_Performance_Optimization_Agent(config)
```

# LLM Settings
- preferred_model: gpt-4
- temperature: 0.2
- max_tokens: 2048

# Discoverability
- registry_compliant: true
- a2a_ready: true
- tags: [performance, optimization, a2a_protocol]
---
