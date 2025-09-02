---
configuration:
  name: A9_Market_Analysis_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Market_Analysis_Agent
- **Team / Agent Context Tags:** market_research, market_analysis
- **Purpose:** Analyzes market trends, competitor activity, and external factors to produce actionable insights and forecasts.
- **Owner:** <owner_or_squad>
- **Version:** 1.0.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9MarketAnalysisAgentConfig(BaseModel):
    provider: str | None = None  # Optional LLM provider for enhanced analysis
    use_llm_by_default: bool = False
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `analyze_market` | Perform market analysis | `A9_Market_Analysis_Input` | `A9_Market_Analysis_Output` | logs events |
| `generate_forecast` | Produce market forecast | `ForecastRequest` | `ForecastResponse` | logs + stores forecast |

Supported hand-off commands / state updates:
- `escalate_market_risk` – notify Risk Analysis Agent of significant threats

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
  - Avg latency target < 1 s
  - Success-rate target ≥ 99 %
  - Cost per call tracked via `A9_CostTracker`

---
# Market Analysis Agent

## Overview
The Market Analysis Agent analyzes market trends, competitor moves, and external factors to inform strategy and opportunity identification. Provides actionable insights for market positioning and forecasting.

## Version
1.0.0

## Team
- **Team**: Market Research
- **Agent Context**: Market Analysis

## Capabilities
- Market trend analysis
- Competitor analysis
- External factor monitoring
- Opportunity identification

## Protocol Compliance
This agent is fully compliant with the A2A protocol and implements the following standards:
- Uses Pydantic models for all inputs/outputs
- Implements ConfigDict for configuration
- Follows standard error handling patterns
- Supports orchestrator-controlled registration

## Configuration
```yaml
name: A9_Market_Analysis_Agent
version: "1.0.0"
capabilities:
  - market_trend_analysis
  - competitor_analysis
  - external_factor_monitoring
  - opportunity_identification
config: {}
hitl_enabled: false  # HITL not required for this agent
```

### Configuration Options
- `name` (str): Agent name, must be "A9_Market_Analysis_Agent"
- `version` (str): Agent version
- `capabilities` (List[str]): List of agent capabilities
- `config` (Dict): Additional configuration options
- `hitl_enabled` (bool): Whether Human-in-the-Loop is enabled (for protocol compliance only)

## Input/Output Models

### Input Model: `A9_Market_Analysis_Input`
```python
class A9_Market_Analysis_Input(BaseModel):
    signals: List[MarketSignal]
    context: Optional[Dict[str, str]] = Field(default_factory=dict)
    situation_context: Optional[A9_Situation_Context] = Field(default=None, description="Unified context model for recognized situation (problem or opportunity), handed off from upstream agents. Optional for principal-driven ad hoc requests.")
```

---

### Situation Context Handoff
- **Field:** `situation_context: Optional[A9_Situation_Context]`
- **Purpose:** Enables seamless, protocol-compliant handoff of structured problem/opportunity context from upstream agents or orchestrator.
- **Optionality:** This field is optional. It is included when the analysis is triggered as part of a larger workflow or by another agent, but may be omitted for principal-driven, ad hoc market analysis requests.
- **Protocol Compliance:** Fully aligns with Agent9 Agent Design Standards for context continuity and multi-agent workflows.

### Output Model: `A9_Market_Analysis_Output`
```python
class A9_Market_Analysis_Output(BaseModel):
    report: MarketReport
    status: str
    message: Optional[str] = None
```

## Entrypoints

### `analyze_market`
Main entrypoint for market analysis.

**Parameters:**
- `input_data` (A9_Market_Analysis_Input): Input data containing market signals
- `use_llm` (bool, optional): Whether to use LLM for enhanced analysis. Defaults to False.
- `llm_prompt` (str, optional): Custom prompt for LLM analysis. Defaults to None.

**Returns:**
- `A9_Market_Analysis_Output`: Analysis results

**Example:**
```python
from src.agents.new.A9_Market_Analysis_Agent import A9_Market_Analysis_Agent
from src.agents.new.market_analysis_models import MarketSignal, A9_Market_Analysis_Input

# Initialize through orchestrator (preferred)
agent = await registry.get_agent("A9_Market_Analysis_Agent")

# Create input
signals = [
    MarketSignal(
        type="price",
        source="market_data",
        value=1.2,
        unit="USD",
        timestamp="2023-01-01T00:00:00Z"
    )
]
input_data = A9_Market_Analysis_Input(signals=signals)

# Analyze
result = await agent.analyze_market(input_data, use_llm=True)
```

## Error Handling
- `AgentInitializationError`: Raised during agent initialization if configuration is invalid
- `AgentExecutionError`: Raised during execution if analysis fails

## LLM Integration
When `use_llm=True`, the agent can enhance analysis using GPT-4 with the following settings:
- Model: gpt-4
- Temperature: 0.2
- Max Tokens: 2048

## Testing
Unit and integration tests are available in `tests/agents/new/test_a9_market_analysis_agent.py`.

To run tests:
```bash
pytest tests/agents/new/test_a9_market_analysis_agent.py -v
```

## Discoverability
- **Registry Compliant**: Yes
- **A2A Ready**: Yes
- **Tags**: market, analysis, a2a_protocol

## Dependencies
- Python 3.8+
- Pydantic >=2.0.0
- Agent9 Core Libraries

## Maintenance
- **Owner**: Market Research Team
- **Last Updated**: 2025-06-05

---
