---
configuration:
  name: A9_Data_Governance_Agent
  version: '1.0'
  capabilities:
    - term_translation
    - kpi_mapping
    - registry_validation
    - data_quality_stub
    - data_lineage_stub
    - top_dimension_enrichment
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Data_Governance_Agent
- **Team / Agent Context Tags:** solution_architect, data_governance
- **Purpose:** Enforces data governance rules, validates KPIs and data sources, and resolves data asset paths.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9DataGovernanceAgentConfig(BaseModel):
    """Configuration parameters for A9_Data_Governance_Agent."""
    # validation_mode: str = "strict"  # strict or lenient mode
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `translate_business_terms` | Translate business terms to technical attributes | `BusinessTermTranslationRequest` | `BusinessTermTranslationResponse` | audit log |
| `get_view_name_for_kpi` | Resolve the view name for a KPI | `KPIViewNameRequest` | `KPIViewNameResponse` | none |
| `map_kpis_to_data_products` | Map KPIs to data products | `KPIDataProductMappingRequest` | `KPIDataProductMappingResponse` | audit log |
| `validate_registry_integrity` | Cross-registry drift check (dev/test) | n/a | dict report `{success, issues, summary}` | none |
| `validate_data_access` | Validate principal access (MVP) | `DataAccessValidationRequest` | `DataAccessValidationResponse` | audit log |
| `get_data_lineage` | Return lineage (MVP stub) | `DataLineageRequest` | `DataLineageResponse` | none |
| `check_data_quality` | Return quality metrics (MVP stub) | `DataQualityCheckRequest` | `DataQualityCheckResponse` | none |
| `compute_and_persist_top_dimensions` | Analyze and persist top dimensions per KPI to kpi_enrichment.yaml | orchestrated call (uses Data Product Agent) | `{success, written, path, kpis_analyzed, failures}` | writes `src/registry/kpi/kpi_enrichment.yaml` |

Supported hand-off commands / state updates:
- `refresh_governance_cache` – triggers background cache update

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

# Error Handling
Standard error handling via AgentExecutionError and AgentInitializationError.

# Example Usage (dev/test)
```python
from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent

agent = await A9_Data_Governance_Agent.create({})
# Run cross-registry validation against FI_Star_View
report = await agent.validate_registry_integrity(view_name="FI_Star_View")
print(report)
```

# LLM Settings
- preferred_model: gpt-4
- temperature: 0.2
- max_tokens: 2048

# Discoverability
- registry_compliant: true
- a2a_ready: true
- tags: [data, governance, a2a_protocol]
---
