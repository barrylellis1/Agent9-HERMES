"""
Agent configuration models for Agent9-HERMES.
All agent configuration models must be defined here for centralized validation.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, ConfigDict, Field
from src.llm_services.claude_service import ClaudeTaskType, get_claude_model_for_task
from src.agents.models.nlp_models import (
    NLPBusinessQueryInput,
    NLPBusinessQueryResult,
    EntityExtractionInput,
    EntityExtractionResult,
)


def _default_llm_provider() -> str:
    """Read LLM_PROVIDER env var; fall back to 'anthropic'."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    p = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    # Map legacy value "openai" to openai, everything else → anthropic
    return p if p in ("openai", "anthropic") else "anthropic"


def _default_api_key_env_var() -> str:
    """Return the env-var name for the API key matching the configured provider."""
    p = _default_llm_provider()
    return "ANTHROPIC_API_KEY" if p == "anthropic" else "OPENAI_API_KEY"


class A9_LLM_Service_Agent_Config(BaseModel):
    """
    Configuration for the A9_LLM_Service_Agent.
    Controls LLM provider settings, model selection, and guardrails.

    Provider selection: set LLM_PROVIDER env var to 'anthropic' (default) or 'openai'.

    Claude task types for automatic model selection:
    - sql_generation / nlp_parsing  → claude-haiku-4-5-20251001 (cheap, fast)
    - reasoning / solution_finding / briefing / synthesis → claude-sonnet-5 (11O-B)
    - stage1_persona → claude-haiku-4-5-20251001 (single-persona focused call)
    - general → claude-sonnet-5
    """
    model_config = ConfigDict(extra="allow")

    # Provider settings — default driven by LLM_PROVIDER env var
    provider: str = Field(
        default_factory=_default_llm_provider,
        description="LLM provider: 'anthropic' (default) or 'openai'. Set via LLM_PROVIDER env var."
    )
    model_name: Optional[str] = Field(
        None,
        description="Model to use. If None, auto-selected based on task_type."
    )
    task_type: str = Field("general", description="Task type for automatic model selection")
    api_key_env_var: str = Field(
        default_factory=_default_api_key_env_var,
        description="Environment variable containing the API key (auto-set from provider)"
    )
    
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
        "C:/Users/Blell/Documents/Agent9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI", 
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


class A9_Situation_Awareness_Agent_Config(BaseModel):
    """
    Configuration for the A9_Situation_Awareness_Agent.
    Controls KPI monitoring, threshold evaluation, and opportunity detection settings.
    """
    model_config = ConfigDict(extra="allow")

    # Contract / registry settings
    contract_path: Optional[str] = Field(
        None,
        description="Path to the data contract YAML file. Defaults to fi_star_schema.yaml when None."
    )
    target_domains: List[str] = Field(
        default_factory=lambda: ["Finance"],
        description="Domain prefixes used to filter KPIs from the registry."
    )

    # Opportunity detection settings (Phase 11C: results now appear in situations[], not opportunities[])
    opportunity_threshold_multiplier: float = Field(
        1.5,
        ge=1.0,
        description=(
            "How much better than the threshold a KPI must be to qualify as an outperformance "
            "opportunity. E.g. 1.5 means the current value must exceed threshold * 1.5."
        )
    )
    opportunity_recovery_min_delta_pct: float = Field(
        5.0,
        ge=0.0,
        description=(
            "Minimum positive percent change required to flag a 'recovery' opportunity "
            "when a KPI crosses back above its warning threshold."
        )
    )

    # Orchestration & logging
    require_orchestrator: bool = Field(
        True, description="All calls must be orchestrator-driven"
    )
    log_all_requests: bool = Field(
        True, description="Log structured inputs/outputs for audit"
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
        10,
        description=(
            "How many dimensions to QUERY — search width, not report width. Raised 5->10 "
            "(Stage I Part A). The funnel downstream is bounded separately: change_points "
            "is globally sorted by |delta| and cut to the top 5, and where_is[:5] feeds "
            "SCQA, so a wider search yields a better-selected top 5 rather than more of "
            "them. Solution Finder's evidence base is unchanged. Cost is ~1 extra query "
            "per added dimension, run sequentially."
        ),
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
    causal_max_hops: int = Field(
        2,
        description=(
            "How far to walk the causal graph from the analysed KPI when assembling "
            "causal context. 1 = only edges touching this KPI (the pre-Aug-2026 "
            "behaviour, which hid base_oil_cost -> cogs -> gross_margin_pct — the "
            "upstream cause of the margin problem being analysed). 2 reaches the "
            "upstream cause without pulling in the whole client graph. Each extra hop "
            "widens the prompt and lengthens the inferential chain, so the average "
            "edge is weaker evidence."
        ),
    )
    stage1_allow_frame_challenge: bool = Field(
        False,
        description=(
            "EXPERIMENTAL (2026-08-14 evidence-scope test, step 1). The Stage 1 task "
            "statement hardcodes 'primary driver of THIS KPI situation' and requires "
            "recovery_range to be non-zero and 'proportional to the observed variance' "
            "— which structurally forbids any option that doesn't recover the analysed "
            "KPI, e.g. a portfolio/exit move. Baseline: 21 real-run options across 7 "
            "arms, 0 challenged the frame, 61% concentrated in indexation + "
            "pricing_corridor. Default False = unchanged production behaviour. When "
            "True, permits (does not require) an option to name a frame assumption "
            "instead of a KPI recovery. One-variable A/B; do not flip without recording "
            "the comparison in docs/architecture/persona_council_experiments.md."
        ),
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

    # Phase 15 Stage A/B: forced tool-use structured output for the synthesis call.
    # Default False — the API-level schema guarantee is a reliability improvement,
    # but semantic output quality vs the current hand-tuned prompt is unvalidated
    # until the live A/B compliance run (Phase 15 M2/M5) passes. Flip only after
    # that run confirms quality parity or better.
    use_structured_output: bool = Field(
        False, description="Route the synthesis call through forced tool-use structured output (Phase 15 Stage A)"
    )

    # Phase 15 Stage D: grounding + constraint input contract. Default False —
    # the READ path is safe (non-fatal, degrades to no context if the schema
    # isn't migrated or tables are empty), but consuming this content in real
    # recommendations is still gated on tenant-isolation tests + a pilot with
    # real SF usage (theory_layer_design.md §5.2/§10 P2). Flip only after that
    # gate passes.
    enable_causal_grounding: bool = Field(
        False, description="Inject kpi_relationships causal chain + active constraints into the synthesis prompt (Phase 15 Stage D)"
    )

    # Phase 15 Stage E: critic pass (generate -> critique-against-theory -> synthesize).
    # Default False, same gating discipline as the other Phase 15 stages. Also
    # requires enable_causal_grounding — a critic with no causal graph to check
    # proposals against has nothing to critique, so it's a no-op either way, but
    # the flag stays explicit rather than implicitly inferred from another flag.
    enable_critic_pass: bool = Field(
        False, description="Run a critic LLM pass tracing each Stage 1 proposal through the causal graph before synthesis (Phase 15 Stage E)"
    )

    # Phase 15 Stage H: theory-guided moderator. Default False — this is the NEW
    # arm of the PM-2 A/B (old simulated cross-review vs moderator grading), so
    # both prompt variants must coexist until the A/B readout kills one. When
    # True, the synthesis prompt replaces the single-author simulated firm-vs-firm
    # cross-review with a moderator duty: grade each option against the assumption
    # register (constraint survival), the causal graph (edge grounding), the data
    # (impact arithmetic), and the critic findings (answered vs standing) — and
    # state the denominator it graded against (PM-1: thin register must yield
    # "insufficient theory data", never confident grades over nothing). Requires
    # enable_causal_grounding for the same reason the critic does: a moderator
    # with no register has nothing to grade against.
    enable_theory_moderator: bool = Field(
        False, description="Replace simulated cross-review with theory-guided moderator grading in the synthesis prompt (Phase 15 Stage H)"
    )
    # PM-9 seam, deliberately just a string: "judge" (grade independent options,
    # pick a winner) is the only implemented protocol. "integrator" (compose
    # complementary contributions, check interfaces) is designed but gated on the
    # first cross-discipline pilot problem — unknown values fall back to judge
    # with a log line, so a typo can't silently change behavior.
    moderator_protocol: str = Field(
        "judge", description="Moderator rubric: 'judge' (implemented) or 'integrator' (designed, gated — falls back to judge)"
    )


class A9_KPI_Assistant_Agent_Config(BaseModel):
    """
    Configuration for the A9_KPI_Assistant_Agent.
    Controls KPI suggestion, validation, and LLM integration settings.
    """
    model_config = ConfigDict(extra="allow")
    
    # LLM settings — honour LLM_PROVIDER env var (same as all other agents)
    llm_provider: str = Field(default_factory=_default_llm_provider, description="LLM provider for KPI suggestions")
    llm_model: str = Field(default_factory=lambda: "claude-sonnet-5" if _default_llm_provider() == "anthropic" else "gpt-4-turbo", description="Model for KPI generation and chat")
    temperature: float = Field(0.7, description="Temperature for LLM generation")
    max_tokens: int = Field(8192, description="Maximum tokens for LLM responses")
    
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


class A9_Market_Analysis_Agent_Config(BaseModel):
    """
    Configuration for the A9_Market_Analysis_Agent.
    Controls Perplexity integration, signal limits, synthesis model, and logging.
    """

    model_config = ConfigDict(extra="allow")

    enable_perplexity: bool = Field(
        True,
        description="Enable Perplexity web search for market signals. Set False for LLM-only mode.",
    )
    max_signals: int = Field(
        5, description="Default maximum number of market signals to retrieve per request"
    )
    synthesis_model: str = Field(
        default_factory=lambda: get_claude_model_for_task(ClaudeTaskType.SYNTHESIS),
        description="Claude model for market signal synthesis — follows the SYNTHESIS routing table entry (honours CLAUDE_MODEL_SYNTHESIS)",
    )
    require_orchestrator: bool = Field(
        False,
        description="When False the agent can acquire A9_LLM_Service_Agent directly from AgentRegistry",
    )
    log_all_requests: bool = Field(
        True, description="Log all incoming requests and outgoing responses for audit"
    )


class A9ValueAssuranceAgentConfig(BaseModel):
    """
    Configuration for the A9_Value_Assurance_Agent.
    Controls measurement windows, confidence thresholds, and persistence settings.
    """
    model_config = ConfigDict(extra="allow")

    agent_name: str = Field("A9_Value_Assurance_Agent", description="Agent identifier")
    measurement_window_days: int = Field(
        30, description="Default measurement window in days"
    )
    min_confidence_for_roi: str = Field(
        "MODERATE",
        description="Minimum ConfidenceLevel to include attribution in ROI totals"
    )
    inaction_cost_revenue_multiplier: float = Field(
        0.005,
        description="Heuristic: 0.5% revenue impact per 1% KPI change (flagged LOW confidence)"
    )
    supabase_enabled: bool = Field(
        False,
        description="Phase 7A: in-memory store; Phase 7B: Supabase persistence"
    )
    require_orchestrator: bool = Field(
        True, description="All calls should be orchestrator-driven"
    )
    log_all_requests: bool = Field(
        True, description="Log structured inputs/outputs for audit"
    )


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
