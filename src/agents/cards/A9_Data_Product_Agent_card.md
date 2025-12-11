---
configuration:
  name: A9_Data_Product_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Data_Product_Agent
- **Team / Agent Context Tags:** solution_architect, data_product
- **Purpose:** Catalogs data products, matches metadata, and resolves data asset paths via MCP backend.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
Key fields (see `src/agents/agent_config_models.py::A9_Data_Product_Agent_Config` for full schema):

- `data_directory: str` – Where DuckDB DB lives
- `database: { type, path }` – DB config (DuckDB in MVP)
- `allow_custom_sql: bool` – Allow custom SQL execution
- `validate_sql: bool` – Validate SQL statements
- `enable_llm_sql: bool` – Enable LLM-based SQL generation for NL queries
- `force_llm_sql: bool` – Force-enable LLM path; on failure returns deterministic error
- `fiscal_year_start_month: int` – Time dimension settings
- `llm_service_agent: A9_LLM_Service_Agent | Any` – Optional injected LLM agent instance for tests or advanced flows. If present, Data Product Agent will call it directly.

Notes:
- LLM path is attempted when `llm_service_agent` is present. Env flag `A9_ENABLE_LLM_SQL` is still read but not required for injected instances.
- Orchestrator creates/provides the LLM agent in production when `llm_service_agent` is not injected.
- Required secrets for LLMs are managed by the LLM Service Agent (`OPENAI_API_KEY`, etc.), not this agent.

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `get_data_asset_path` | Resolve path for a data asset | `DataAssetPathRequest` | `DataAssetPathResponse` | logs events |
| `search_data_products` | NLQ search across catalog | `DataProductNLQSearchInput` | `DataProductNLQSearchOutput` | logs query |

Supported hand-off commands / state updates:
- `refresh_catalog` – triggers MCP refresh

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

> **Flexible I/O Protocol:** Input and output models for this agent use Pydantic `extra = "allow"` where untyped or LLM-driven data is required. See Orchestration Refactor Plan for details.
description: |
  Manages and catalogs data products for analytics and reporting.
  
  **LLM Explainability (2025-06-24):**
  All summary and recommendation text fields are processed via the A9_LLM_Service_Agent for explainability and business-user-friendly output. LLM calls are protocol-compliant, orchestrator-driven, and fully async with structured event logging and error handling. See PRD for details.
  
  **YAML Contract Context:**
  This agent reads and responds to `yaml_contract_text` provided in the `context` kwarg for all protocol-compliant workflows. The YAML contract may define data product requirements, schema, or constraints, and is passed by the orchestrator.
  
  **Advanced Analytics Schema Support:**
  - Fully supports advanced analytics fields in YAML contracts as defined by the Agent9 DataProductModel and KPIModel (see `src/agents/new/yaml_data_product_loader.py`).
  - Handles derived KPIs, window functions, Top-N analytics, formulas, time bucketing, and custom filters as first-class schema features.
  - All protocol-compliant workflows and SQL generation leverage these schema extensions for analytics flexibility.
  
  **MCP-Only Compliance:**
  All data access, joining, filtering, and aggregation logic is performed exclusively by the MCP (DuckDB backend) service. This agent does not use direct pandas, file I/O, or agent-side data transformation in production. All data product onboarding, discovery, and access are handled via MCP endpoints.

team: solution_architect
agent_context: data_product
input_model: DataProductNLQSearchInput | DataAssetPathRequest
output_model: DataProductNLQSearchOutput | DataAssetPathResponse
configuration:
  - config: {}
      - data_product_cataloging
      - data_product_matching
      - metadata_management
    config: {}
    hitl_enabled: false  # For protocol compliance; see config model/PRD for rationale
error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.

compliance_notes: |
  - YAML contract propagation: This agent must read and use `yaml_contract_text` from the context kwarg if present, as passed by the orchestrator. All protocol-compliant workflows must support this context propagation.
  - Advanced analytics YAML schema: This agent and its SQL generator are protocol-compliant with the Agent9 advanced analytics schema (see DataProductModel/KPIModel), supporting derived KPIs, window functions, Top-N, custom formulas, time bucketing, and custom filters directly from YAML contracts.
  - MCP-only: All data access, joining, filtering, and aggregation logic is delegated to the MCP (DuckDB backend) service. No agent-side pandas/file I/O is permitted in production.

example_usage: |
  from src.agents.new.A9_Data_Product_Agent import A9_Data_Product_Agent
  from src.agents.new.data_governance_models import DataAssetPathRequest
  config = {
      "name": "A9_Data_Product_Agent",
      "version": "1.0",
      "capabilities": [
          "data_product_cataloging",
          "data_product_matching",
          "metadata_management",
          "data_asset_path_lookup"
      ],
      "config": {},
      "hitl_enabled": False
  }
  agent = A9_Data_Product_Agent(config)
  # Example: Dynamic asset path lookup
  request = DataAssetPathRequest(asset_name="example_asset")
  response = await agent.get_data_source_path(request)
  print(response)
  # Logging is structured and handled via A9_SharedLogger
  # Registration is orchestrator-controlled; do not instantiate directly except via orchestrator
  # To access the propagated YAML contract context in a protocol-compliant method:
  # def some_method(self, input_model: DataProductNLQSearchInput, context=None):
  #     yaml_contract = context.get('yaml_contract_text') if context else None
  # All protocol entrypoints must use only the input/output models defined above. Deprecated or legacy models are not supported.
  # Logging is always async and handled via A9_SharedLogger, and all event logging must be awaited.

llm_settings:
  preferred_model: gpt-4
  temperature: 0.2
  max_tokens: 2048
discoverability:
  registry_compliant: true
  a2a_ready: true
  tags:
    - data
    - product
    - a2a_protocol
    - mcp_only
    - duckdb_backend
  last_updated: "2024-12-10"

---
