"""
Agent configuration models for Agent9-HERMES.
All agent configuration models must be defined here for centralized validation.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ConfigDict, Field
from src.agents.models.nlp_models import (
    NLPBusinessQueryInput,
    NLPBusinessQueryResult,
    EntityExtractionInput,
    EntityExtractionResult,
)


class A9_LLM_Service_Agent_Config(BaseModel):
    """
    Configuration for the A9_LLM_Service_Agent.
    Controls LLM provider settings, model selection, and guardrails.
    
    Task types for automatic model selection:
    - sql_generation: Optimized for SQL output (gpt-4o-mini)
    - nlp_parsing: Optimized for extraction (gpt-4o-mini)
    - reasoning: Complex analysis (o1-mini)
    - solution_finding: Solution debate (o1-mini)
    - briefing: Executive briefing (gpt-4o)
    - general: Balanced (gpt-4o)
    """
    model_config = ConfigDict(extra="allow")
    
    # Provider settings
    provider: str = Field("openai", description="LLM provider to use (anthropic, openai)")
    model_name: Optional[str] = Field(None, 
                           description="Model to use. If None, auto-selected based on task_type")
    task_type: str = Field("general", 
                          description="Task type for automatic model selection")
    api_key_env_var: str = Field("OPENAI_API_KEY", 
                               description="Environment variable containing API key")
    
    # Generation settings
    max_tokens: int = Field(4096, description="Default maximum tokens for completion")
    temperature: float = Field(0.7, description="Default temperature for generation")
    
    # Guardrails settings
    guardrails_path: str = Field("docs/cascade_guardrails.yaml", 
                                description="Path to guardrails configuration file")
    prompt_templates_path: str = Field("docs/cascade_prompt_templates.md", 
                                     description="Path to prompt templates file")
    system_prompt_override: Optional[str] = Field(None, 
                                                description="Override for system prompt")
    
    # Routing and orchestration
    require_orchestrator: bool = Field(True, 
                                     description="Whether calls must be routed through orchestrator")
    log_all_requests: bool = Field(True, 
                                 description="Whether to log all LLM requests and responses")
    
    # Environment settings
    use_mocks_in_test: bool = Field(True, 
                                   description="Whether to use mock responses in test environment")


class A9_Data_Product_MCP_Service_Config(BaseModel):
    """
    Configuration for the A9_Data_Product_MCP_Service_Agent.
    Controls data sources, product registry, and query execution settings.
    """
    model_config = ConfigDict(extra="allow")
    
    # Data source settings
    sap_data_path: str = Field(..., description="Path to SAP data files")
    
    # Registry settings
    registry_path: str = Field("src/registry_references", 
                              description="Path to registry references")
    data_product_registry: str = Field("data_product_registry/data_product_registry.csv",
                                      description="Path to data product registry file")
    contracts_path: str = Field("src/registry_references/data_product_registry/data_products",
                              description="Path to data product contract YAML files")
    
    # Query execution settings
    allow_custom_sql: bool = Field(True, 
                                description="Whether to allow custom SQL execution")
    validate_sql: bool = Field(True, 
                            description="Whether to validate SQL for security")


class A9_Orchestrator_Agent_Config(BaseModel):
    """
    Configuration for the A9_Orchestrator_Agent.
    Controls workflow execution, agent discovery, and registry management.
    """
    model_config = ConfigDict(extra="allow")
    
    # Registry settings
    agent_discovery_paths: List[str] = Field(["src/agents"], 
                                          description="Paths to scan for agent modules")
    card_discovery_paths: List[str] = Field(["src/agents/cards"], 
                                         description="Paths to scan for agent cards")
    
    # Workflow settings
    workflow_definition_path: str = Field("src/workflows", 
                                        description="Path to workflow definitions")
    default_workflow: str = Field("situation_awareness", 
                                description="Default workflow to execute if not specified")
    
    # Logging settings
    log_level: str = Field("INFO", description="Default log level")
    log_to_file: bool = Field(True, description="Whether to log to file")
    log_file_path: str = Field("logs/orchestrator.log", description="Path to log file")
    
    # Performance settings
    max_concurrent_workflows: int = Field(10, 
                                       description="Maximum concurrent workflows")
    agent_timeout_seconds: int = Field(30, 
                                    description="Timeout for agent operations in seconds")


class A9_Principal_Context_Agent_Config(BaseModel):
    """
    Configuration for the A9_Principal_Context_Agent.
    Controls principal profile management and context handling.
    """
    model_config = ConfigDict(extra="allow")
    
    # Data sources
    registry_path: str = Field("src/registry_references/principal_registry", 
                             description="Path to principal registry data")
    cache_profiles: bool = Field(True, 
                               description="Whether to cache principal profiles in memory")
    
    # Context settings
    context_ttl_seconds: int = Field(300, 
                                   description="Time-to-live for cached context in seconds")
    refresh_on_access: bool = Field(True, 
                                  description="Whether to refresh context on access")
    
    # Privacy settings
    pii_fields: List[str] = Field(["email", "phone", "address"], 
                                description="Fields containing PII to be handled securely")


class A9_Data_Product_MCP_Service_Config(BaseModel):
    """
    Configuration for the A9_Data_Product_MCP_Service_Agent.
    Controls data access, SQL execution, and registry integration.
    """
    model_config = ConfigDict(extra="allow")
    
    # Data source settings
    sap_data_path: str = Field(
        "C:/Users/barry/Documents/Agent 9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI", 
        description="Path to SAP DataSphere CSV data files"
    )
    
    # Registry settings
    registry_path: str = Field(
        "src/registry_references", 
        description="Path to registry data files"
    )
    data_product_registry: str = Field(
        "data_product_registry/data_product_registry.csv", 
        description="Path to data product registry file relative to registry_path"
    )
    contracts_path: str = Field(
        "src/registry_references/data_product_registry/data_products",
        description="Path to data product contract YAML files"
    )
    
    # Security settings
    allow_custom_sql: bool = Field(
        True, 
        description="Whether to allow custom SQL execution (vs. only registry-defined queries)"
    )
    validate_sql: bool = Field(
        True, 
        description="Whether to validate SQL statements for security (only SELECT allowed)"
    )
    
    # Performance settings
    cache_tables: bool = Field(
        True, 
        description="Whether to cache loaded tables in memory"
    )
    max_result_rows: int = Field(
        10000, 
        description="Maximum number of rows to return in a result"
    )
    
    # Logging settings
    log_queries: bool = Field(
        True, 
        description="Whether to log all executed SQL queries"
    )
    include_query_results_in_logs: bool = Field(
        False, 
        description="Whether to include query results in logs (could expose sensitive data)"
    )


class A9_Data_Product_Agent_Config(BaseModel):
    """
    Configuration for the A9_Data_Product_Agent.
    Controls data product access, SQL generation and execution, and view creation.
    """
    model_config = ConfigDict(extra="allow")
    
    # Data source settings
    data_directory: str = Field(
        "data", 
        description="Directory containing database files"
    )
    
    # Database settings
    database: Dict[str, Any] = Field(
        {"type": "duckdb", "path": "data/agent9-hermes.duckdb"},
        description="Database configuration"
    )
    
    # Registry settings
    registry_path: Optional[str] = Field(
        None, 
        description="Path to registry data files"
    )
    data_product_registry: Optional[str] = Field(
        None, 
        description="Path to data product registry file relative to registry_path"
    )
    
    # Security settings
    allow_custom_sql: bool = Field(
        True, 
        description="Whether to allow custom SQL execution"
    )
    validate_sql: bool = Field(
        True, 
        description="Whether to validate SQL statements for security (only SELECT allowed)"
    )
    # LLM SQL generation settings
    enable_llm_sql: bool = Field(
        False,
        description="Enable LLM-based SQL generation for natural language queries"
    )
    force_llm_sql: bool = Field(
        False,
        description="Force-enable LLM-based SQL generation (overrides environment toggles)"
    )
    
    # Logging settings
    log_level: str = Field(
        "INFO",
        description="Log level for the agent"
    )
    log_queries: bool = Field(
        True, 
        description="Whether to log all executed SQL queries"
    )

    # Fiscal/time settings
    fiscal_year_start_month: int = Field(
        1,
        description="Fiscal year start month (1-12). Default is 1 (January)."
    )
    timezone: str = Field(
        "UTC",
        description="Timezone identifier for date computations (informational for DuckDB in MVP)."
    )

    # MCP client settings (embedded by default for unit tests)
    mcp_mode: str = Field(
        "embedded",
        description="MCP client mode: 'embedded' for in-process, 'remote' for HTTP calls"
    )
    mcp_base_url: Optional[str] = Field(
        None,
        description="Base URL of MCP service when mcp_mode='remote' (e.g., http://localhost:8000)"
    )
    mcp_timeout_ms: int = Field(
        10000,
        description="Timeout budget in milliseconds for remote MCP calls"
    )


class A9_NLP_Interface_Agent_Config(BaseModel):
    """
    Configuration for the A9_NLP_Interface_Agent.
    Controls parsing behavior, HITL, and orchestrator-driven integration.
    """
    model_config = ConfigDict(extra="allow")

    # Core behavior
    hitl_enabled: bool = Field(
        False, description="Enable HITL escalation for ambiguous/unmapped terms"
    )
    llm_parsing_enabled: bool = Field(
        False, description="Enable LLM-assisted parsing; deterministic fallback otherwise"
    )

    # Orchestration & logging
    require_orchestrator: bool = Field(
        True, description="All calls must be orchestrator-driven"
    )
    log_all_requests: bool = Field(
        True, description="Log structured inputs/outputs for audit"
    )

    # Parsing defaults
    default_topn_n: int = Field(
        10, description="Default N when user asks for 'top'/'bottom' without a number"
    )


class A9_Deep_Analysis_Agent_Config(BaseModel):
    """
    Configuration for the A9_Deep_Analysis_Agent.
    Controls planning limits, percent growth computation, and orchestration/logging flags.
    """
    model_config = ConfigDict(extra="allow")

    # Core behavior
    hitl_enabled: bool = Field(
        False, description="HITL disabled for Deep Analysis (per PRD; narrative only via LLM)."
    )
    max_dimensions: int = Field(
        5, description="Maximum number of dimensions to enumerate in analysis planning"
    )
    max_groups_per_dim: int = Field(
        10, description="Maximum groups per dimension to materialize for summaries"
    )
    enable_percent_growth: bool = Field(
        False, description="Include percent growth alongside delta comparisons when true"
    )

    # Orchestration & logging
    require_orchestrator: bool = Field(
        True, description="All calls must be orchestrator-driven"
    )
    log_all_requests: bool = Field(
        True, description="Log structured inputs/outputs for audit"
    )


class A9_Solution_Finder_Agent_Config(BaseModel):
    """
    Configuration for the A9_Solution_Finder_Agent.
    Controls scoring weights, HITL, and orchestration/logging flags.
    """
    model_config = ConfigDict(extra="allow")

    # Core behavior
    hitl_enabled: bool = Field(
        True, description="HITL is required for recommendation approval (single HITL event per cycle)"
    )
    enable_llm_debate: bool = Field(
        False, description="Enable LLM-driven expert persona debate and consensus synthesis"
    )
    expert_personas: List[str] = Field(
        [
            "QA Lead",
            "Operations Manager",
            "Finance Controller",
            "Management/Strategy Consultant",
            "Big 4 Consultant",
        ],
        description="Default expert personas to include in debate prompts when enabled"
    )
    
    # Hybrid Council settings
    enable_hybrid_council: bool = Field(
        False, description="Enable Hybrid Council mode using external consulting personas"
    )
    consulting_personas: List[str] = Field(
        [], description="List of consulting persona IDs to use in Hybrid Council mode"
    )
    council_preset: Optional[str] = Field(
        None, description="Council preset ID to use if consulting_personas is empty"
    )

    weight_impact: float = Field(
        0.5, description="Weight for expected business impact in option scoring"
    )
    weight_cost: float = Field(
        0.25, description="Weight for cost in option scoring (lower cost preferred)"
    )
    weight_risk: float = Field(
        0.25, description="Weight for risk in option scoring (lower risk preferred)"
    )

    # Orchestration & logging
    require_orchestrator: bool = Field(
        True, description="All calls must be orchestrator-driven"
    )
    log_all_requests: bool = Field(
        True, description="Log structured inputs/outputs for audit"
    )


class A9_KPI_Assistant_Agent_Config(BaseModel):
    """
    Configuration for the A9_KPI_Assistant_Agent.
    Controls KPI suggestion, validation, and LLM integration settings.
    """
    model_config = ConfigDict(extra="allow")
    
    # LLM settings
    llm_provider: str = Field("openai", description="LLM provider for KPI suggestions")
    llm_model: str = Field("gpt-4-turbo", description="Model for KPI generation and chat")
    temperature: float = Field(0.7, description="Temperature for LLM generation")
    max_tokens: int = Field(4096, description="Maximum tokens for LLM responses")
    
    # Suggestion settings
    default_num_suggestions: int = Field(5, description="Default number of KPI suggestions")
    include_rationale: bool = Field(True, description="Include rationale for suggestions")
    validate_sql: bool = Field(True, description="Validate SQL queries against schema")
    
    # Metadata validation
    enforce_strategic_metadata: bool = Field(
        True, description="Enforce all strategic metadata tags (line, altitude, profit_driver_type, lens_affinity)"
    )
    warn_on_inconsistencies: bool = Field(
        True, description="Warn on logical inconsistencies in metadata tags"
    )
    
    # Conversation settings
    max_conversation_history: int = Field(20, description="Maximum messages to keep in conversation history")
    conversation_timeout_minutes: int = Field(60, description="Conversation timeout in minutes")
    
    # Integration settings
    data_governance_agent_id: Optional[str] = Field(
        None, description="ID of Data Governance Agent for validation"
    )
    data_product_agent_id: Optional[str] = Field(
        None, description="ID of Data Product Agent for contract updates"
    )
    
    # Orchestration & logging
    require_orchestrator: bool = Field(
        True, description="All calls must be orchestrator-driven"
    )
    log_all_requests: bool = Field(
        True, description="Log structured inputs/outputs for audit"
    )


class A9RiskAnalysisAgentConfig(BaseModel):
    """Configuration for the A9_Risk_Analysis_Agent."""

    model_config = ConfigDict(extra="allow")

    hitl_enabled: bool = Field(False, description="HITL is not required for Risk Analysis (see PRD). Present for protocol consistency only.")
    weight_market: Optional[float] = Field(0.35, ge=0.0, le=1.0, description="Default weight for market risk in composite score calculation")
    weight_operational: Optional[float] = Field(0.35, ge=0.0, le=1.0, description="Default weight for operational risk in composite score calculation")
    weight_financial: Optional[float] = Field(0.30, ge=0.0, le=1.0, description="Default weight for financial risk in composite score calculation")
    require_orchestrator: bool = Field(True, description="All calls must be orchestrator-driven")
    log_all_requests: bool = Field(True, description="Log structured inputs/outputs for audit")


# Protocol model references for compliance checks and documentation
NLP_PROTOCOL_MODELS: Dict[str, Dict[str, Any]] = {
    "parse_business_query": {
        "input": NLPBusinessQueryInput,
        "output": NLPBusinessQueryResult,
    },
    "entity_extraction": {
        "input": EntityExtractionInput,
        "output": EntityExtractionResult,
    },
}
