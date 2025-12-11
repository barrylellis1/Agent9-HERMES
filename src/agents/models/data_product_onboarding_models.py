"""Pydantic models for the Data Product Onboarding workflow.

These request/response models cover schema inspection, contract generation,
registry registration, governance mapping, principal ownership, and optional QA
validation. All models inherit from the Agent9 base request/response to ensure
protocol compliance and consistent serialization.
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel,
    A9AgentBaseRequest,
    A9AgentBaseResponse,
)


# ---------------------------------------------------------------------------
# Shared helper models used across onboarding steps
# ---------------------------------------------------------------------------


class TableColumnProfile(A9AgentBaseModel):
    """Column-level profiling details captured during schema inspection."""

    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Source system data type")
    is_nullable: bool = Field(True, description="Whether the column allows NULLs")
    sample_values: List[Any] = Field(
        default_factory=list,
        description="Representative values sampled from the column (if available)",
    )
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Numeric or categorical statistics (min, max, distinct_count, etc.)",
    )
    semantic_tags: List[str] = Field(
        default_factory=list,
        description="Semantic hints (e.g., measure, dimension:region, date)",
    )


class TableProfile(A9AgentBaseModel):
    """Table-level profiling summary returned by schema inspection."""

    name: str = Field(..., description="Fully-qualified table name within the source")
    row_count: Optional[int] = Field(
        None, description="Approximate row count reported by the source system"
    )
    primary_keys: List[str] = Field(
        default_factory=list, description="List of columns serving as primary/business keys"
    )
    timestamp_columns: List[str] = Field(
        default_factory=list, description="Columns providing timeframe context"
    )
    columns: List[TableColumnProfile] = Field(
        default_factory=list, description="Column profiles for the table"
    )
    notes: Optional[str] = Field(None, description="Additional metadata or caveats")


class KPIProposal(A9AgentBaseModel):
    """Candidate KPI derived during schema inspection."""

    name: str = Field(..., description="Suggested KPI name")
    expression: str = Field(..., description="SQL expression or formula for the KPI")
    grain: Optional[str] = Field(None, description="Business grain for the KPI (e.g., customer_day)")
    dimensions: List[str] = Field(
        default_factory=list,
        description="Recommended drill-dimension columns associated with the KPI",
    )
    description: Optional[str] = Field(None, description="Human-readable description of the KPI")
    confidence: float = Field(
        0.5, description="Confidence score (0-1) for the suggested KPI"
    )


class QAResult(A9AgentBaseModel):
    """Represents the outcome of an individual QA validation check."""

    check: str = Field(..., description="Name of the executed QA check")
    status: str = Field(..., description="Result status (pass, warn, fail)")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Structured details about the check outcome"
    )
    human_action_required: bool = Field(
        False, description="Whether human follow-up is required for this check"
    )


# ---------------------------------------------------------------------------
# Data Product Agent steps
# ---------------------------------------------------------------------------


class DataProductSchemaInspectionRequest(A9AgentBaseRequest):
    """Request model for inspecting a source schema."""

    source_system: str = Field(..., description="Identifier for the source system (duckdb, bigquery, etc.)")
    database: Optional[str] = Field(None, description="Database/catalog name if required by the source")
    schema: Optional[str] = Field(None, description="Schema/dataset name to inspect")
    tables: Optional[List[str]] = Field(
        None,
        description="Specific tables to profile; if omitted the agent will inspect all eligible tables",
    )
    inspection_depth: str = Field(
        "standard",
        description="Depth of profiling (basic, standard, extended) influencing stats computation",
    )
    include_samples: bool = Field(
        False, description="Whether to pull sample values for each column (may be slower)"
    )
    environment: str = Field(
        "dev", description="Execution environment (dev/test/prod) for connection routing"
    )
    connection_overrides: Optional[Dict[str, Any]] = Field(
        None,
        description="Override credentials/connection details to support per-environment onboarding",
    )


class DataProductSchemaInspectionResponse(A9AgentBaseResponse):
    """Response model containing schema profiling results."""

    environment: str = Field(..., description="Environment that was inspected")
    tables: List[TableProfile] = Field(
        default_factory=list, description="Profile summaries for inspected tables"
    )
    inferred_kpis: List[KPIProposal] = Field(
        default_factory=list, description="Automatically suggested KPIs based on the schema"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Non-blocking issues encountered during inspection"
    )
    blockers: List[str] = Field(
        default_factory=list, description="Blocking issues preventing contract generation"
    )
    inspection_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata such as profiling durations"
    )


class DataProductContractGenerationRequest(A9AgentBaseRequest):
    """Request model for generating a data product contract YAML."""

    data_product_id: str = Field(..., description="Identifier for the data product being generated")
    schema_summary: List[TableProfile] = Field(
        default_factory=list,
        description="Schema profiles produced by the inspection step",
    )
    kpi_proposals: List[KPIProposal] = Field(
        default_factory=list, description="Optional KPI proposals to embed in the contract"
    )
    target_contract_path: Optional[str] = Field(
        None,
        description="Desired filesystem path for the generated YAML contract (relative or absolute)",
    )
    contract_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Explicit overrides for contract sections (metadata, views, governance, etc.)",
    )


class DataProductContractGenerationResponse(A9AgentBaseResponse):
    """Response containing the generated contract details."""

    contract_yaml: str = Field(..., description="Generated YAML text for the data product contract")
    contract_path: Optional[str] = Field(
        None, description="Filesystem path where the contract YAML was written"
    )
    validation_messages: List[str] = Field(
        default_factory=list, description="Results from contract schema validation"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Non-blocking warnings surfaced during generation"
    )


class DataProductRegistrationRequest(A9AgentBaseRequest):
    """Request model for registering the data product in the registry."""

    data_product_id: str = Field(..., description="Unique identifier for the data product")
    contract_path: str = Field(..., description="Path to the persisted YAML contract")
    display_name: Optional[str] = Field(None, description="Human-friendly display name")
    domain: Optional[str] = Field(None, description="Business domain for the data product")
    description: Optional[str] = Field(None, description="Description of the data product")
    tags: List[str] = Field(default_factory=list, description="Tag metadata to store in the registry")
    owner_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Owner/principal hints to persist alongside the registry entry"
    )
    additional_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata blob forwarded to the registry provider"
    )


class DataProductRegistrationResponse(A9AgentBaseResponse):
    """Response model summarizing registry registration."""

    registry_entry: Dict[str, Any] = Field(
        default_factory=dict, description="The registry record created or updated for the data product"
    )
    was_created: bool = Field(
        False, description="True if this call created a new registry entry; False if it updated an existing one"
    )
    registry_path: Optional[str] = Field(
        None, description="Path to the registry file that was updated"
    )


# ---------------------------------------------------------------------------
# Data Governance Agent steps
# ---------------------------------------------------------------------------


class KPIThreshold(A9AgentBaseModel):
    """Represents KPI threshold configuration for governance updates."""

    type: str = Field(..., description="Threshold type (upper, lower, target, etc.)")
    value: float = Field(..., description="Threshold value")
    comparator: str = Field(
        "<=",
        description="Comparator used when evaluating the threshold (<=, >=, ==, etc.)",
    )
    unit: Optional[str] = Field(None, description="Optional unit for the threshold value")


class KPIRegistryEntry(A9AgentBaseModel):
    """Registry structure for a single KPI definition."""

    kpi_id: str = Field(..., description="Unique KPI identifier")
    name: str = Field(..., description="Human-readable KPI name")
    description: Optional[str] = Field(None, description="Description of the KPI")
    view_name: Optional[str] = Field(None, description="View or table backing the KPI")
    expression: Optional[str] = Field(None, description="SQL expression used to compute the KPI")
    dimensions: List[str] = Field(
        default_factory=list, description="Dimensions available for slicing the KPI"
    )
    business_process_ids: List[str] = Field(
        default_factory=list, description="Business process identifiers associated with the KPI"
    )
    thresholds: List[KPIThreshold] = Field(
        default_factory=list, description="Threshold definitions for governance alerts"
    )
    owner_roles: List[str] = Field(
        default_factory=list, description="Preferred owner roles for accountability"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional governance metadata"
    )


class KPIRegistryUpdateRequest(A9AgentBaseRequest):
    """Request to register or update KPI metadata."""

    data_product_id: str = Field(..., description="Data product associated with the KPIs")
    kpis: List[KPIRegistryEntry] = Field(
        default_factory=list,
        description="KPI entries to register or update in the governance registry",
    )
    overwrite_existing: bool = Field(
        False, description="Whether to overwrite existing registry entries with matching KPI IDs"
    )


class KPIRegistryUpdateResponse(A9AgentBaseResponse):
    """Response summarizing KPI registry updates."""

    updated_count: int = Field(
        0, description="Number of KPI entries created or updated in the registry"
    )
    duplicated_ids: List[str] = Field(
        default_factory=list, description="KPI IDs that already existed and were skipped"
    )
    registry_path: Optional[str] = Field(
        None, description="Path to the KPI registry file that was modified"
    )


class BusinessProcessMapping(A9AgentBaseModel):
    """Represents a mapping between a business process and one or more KPIs."""

    process_id: str = Field(..., description="Business process identifier")
    kpi_ids: List[str] = Field(
        default_factory=list, description="KPI IDs associated with this business process"
    )
    notes: Optional[str] = Field(None, description="Additional context for the mapping")
    compliance_policies: List[str] = Field(
        default_factory=list,
        description="Compliance policies or controls that apply to this mapping",
    )


class BusinessProcessMappingRequest(A9AgentBaseRequest):
    """Request to map KPIs/data products to governed business processes."""

    data_product_id: str = Field(..., description="Data product identifier")
    mappings: List[BusinessProcessMapping] = Field(
        default_factory=list, description="Mappings to apply"
    )
    overwrite_existing: bool = Field(
        False,
        description="If True, existing mappings for the supplied processes will be replaced",
    )


class BusinessProcessMappingResponse(A9AgentBaseResponse):
    """Response detailing applied business process mappings."""

    applied_mappings: List[BusinessProcessMapping] = Field(
        default_factory=list, description="Mappings that were successfully applied"
    )
    skipped_process_ids: List[str] = Field(
        default_factory=list, description="Process IDs skipped due to validation or conflicts"
    )
    registry_path: Optional[str] = Field(
        None, description="Path to the business process registry file that was updated"
    )


# ---------------------------------------------------------------------------
# Principal Context Agent steps
# ---------------------------------------------------------------------------


class PrincipalOwnershipRequest(A9AgentBaseRequest):
    """Request to identify accountable principal ownership for a data product."""

    data_product_id: str = Field(..., description="Identifier for the onboarded data product")
    candidate_owner_ids: List[str] = Field(
        default_factory=list,
        description="Preferred principal IDs to evaluate first (e.g., nominated owners)",
    )
    fallback_roles: List[str] = Field(
        default_factory=list, description="Roles to consult if direct principal matches fail"
    )
    business_process_context: List[str] = Field(
        default_factory=list,
        description="Business processes associated with the data product for ownership context",
    )
    environment: str = Field(
        "dev", description="Environment to consult for ownership metadata"
    )


class OwnershipChainEntry(A9AgentBaseModel):
    """Represents a single step in the ownership resolution chain."""

    principal_id: str = Field(..., description="Principal identifier")
    role: Optional[str] = Field(None, description="Principal role or title")
    reason: Optional[str] = Field(None, description="Explanation for the selection or escalation")


class PrincipalOwnershipResponse(A9AgentBaseResponse):
    """Response containing the resolved principal owner and chain."""

    owner_principal_id: Optional[str] = Field(
        None, description="Resolved principal responsible for the data product"
    )
    owner_profile: Dict[str, Any] = Field(
        default_factory=dict,
        description="Profile details for the resolved principal (if available)",
    )
    ownership_chain: List[OwnershipChainEntry] = Field(
        default_factory=list, description="Escalation chain evaluated during resolution"
    )
    notes: List[str] = Field(
        default_factory=list, description="Additional notes or recommendations from the agent"
    )


# ---------------------------------------------------------------------------
# Optional QA step (can be handled by QA or Data Product Agent helper)
# ---------------------------------------------------------------------------


class DataProductQARequest(A9AgentBaseRequest):
    """Request to validate the onboarding output before activation."""

    data_product_id: str = Field(..., description="Identifier for the data product under validation")
    contract_path: str = Field(..., description="Path to the generated YAML contract")
    environment: str = Field(
        "dev", description="Environment in which QA checks should run"
    )
    checks: List[str] = Field(
        default_factory=list,
        description="Specific QA checks to run (lint_contract, run_smoke_query, etc.)",
    )
    additional_context: Dict[str, Any] = Field(
        default_factory=dict, description="Extra metadata for QA execution"
    )


class DataProductQAResponse(A9AgentBaseResponse):
    """Response summarizing QA validation results."""

    results: List[QAResult] = Field(
        default_factory=list, description="Individual QA check outcomes"
    )
    blockers: List[str] = Field(
        default_factory=list, description="Blocking issues that must be resolved before activation"
    )
    overall_status: str = Field(
        "pending",
        description="Overall QA disposition (pass, warn, fail, pending)",
    )


# ---------------------------------------------------------------------------
# Orchestrated workflow request/response models
# ---------------------------------------------------------------------------


class WorkflowStepSummary(A9AgentBaseModel):
    """Summarizes the outcome of an onboarding workflow step."""

    name: str = Field(..., description="Identifier for the workflow step")
    status: str = Field(..., description="Resulting status for the step")
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Relevant payload captured from the step response",
    )


class DataProductOnboardingWorkflowRequest(A9AgentBaseRequest):
    """Top-level request driving the data product onboarding workflow."""

    data_product_id: str = Field(..., description="Identifier for the new data product")
    source_system: str = Field(..., description="Source system identifier (duckdb, bigquery, etc.)")
    database: Optional[str] = Field(
        None, description="Database or catalog housing the source tables"
    )
    schema: Optional[str] = Field(
        None, description="Schema or dataset name housing source tables"
    )
    tables: Optional[List[str]] = Field(
        None, description="Explicit tables to profile; if omitted all eligible tables will be inspected"
    )
    environment: str = Field(
        "dev", description="Environment route for all agent interactions (dev/test/prod)"
    )
    include_samples: bool = Field(
        False, description="Whether schema inspection should include sample values"
    )
    inspection_depth: str = Field(
        "standard", description="Schema inspection depth hint (basic, standard, extended)"
    )
    connection_overrides: Optional[Dict[str, Any]] = Field(
        None,
        description="Override connection parameters for inspection (per-environment credentials, etc.)",
    )
    contract_output_path: Optional[str] = Field(
        None, description="Desired filesystem path for the generated YAML contract"
    )
    data_product_name: Optional[str] = Field(
        None, description="Human-friendly name for the data product"
    )
    data_product_domain: Optional[str] = Field(
        None, description="Business domain for the data product"
    )
    data_product_description: Optional[str] = Field(
        None, description="Narrative description for registry registration"
    )
    data_product_tags: List[str] = Field(
        default_factory=list, description="Tag metadata for the registry entry"
    )
    contract_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Explicit contract overrides applied during YAML generation",
    )
    additional_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata forwarded to the registry entry",
    )
    owner_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Initial owner metadata captured alongside the registry entry",
    )
    kpi_entries: List[KPIRegistryEntry] = Field(
        default_factory=list,
        description="KPI definitions to register with Data Governance",
    )
    overwrite_existing_kpis: bool = Field(
        False, description="Allow overwriting existing KPI definitions"
    )
    business_process_mappings: List[BusinessProcessMapping] = Field(
        default_factory=list,
        description="Business process mappings to register for the onboarded data product",
    )
    overwrite_existing_mappings: bool = Field(
        False, description="Allow overwriting existing business process mappings"
    )
    candidate_owner_ids: List[str] = Field(
        default_factory=list,
        description="Nominated principal IDs evaluated first for ownership",
    )
    fallback_roles: List[str] = Field(
        default_factory=list,
        description="Role escalation chain when direct owner IDs are unavailable",
    )
    business_process_context: List[str] = Field(
        default_factory=list,
        description="Business processes used to infer ownership if nominees are absent",
    )
    qa_enabled: bool = Field(
        False, description="Whether the optional QA validation helper should run"
    )
    qa_checks: List[str] = Field(
        default_factory=list,
        description="Specific QA checks to execute when QA is enabled",
    )
    qa_additional_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context forwarded to the QA helper",
    )


class DataProductOnboardingWorkflowResponse(A9AgentBaseResponse):
    """Aggregated result returned by the data product onboarding workflow."""

    steps: List[WorkflowStepSummary] = Field(
        default_factory=list, description="Ordered execution summaries for workflow steps"
    )
    data_product_id: str = Field(
        ..., description="Identifier for the onboarded data product"
    )
    contract_paths: List[str] = Field(
        default_factory=list, description="Persisted contract paths generated during onboarding"
    )
    governance_status: str = Field(
        "pending", description="Aggregated status for governance-related steps"
    )
    principal_owner: Dict[str, Any] = Field(
        default_factory=dict,
        description="Resolved principal ownership payload",
    )
    qa_report: Dict[str, Any] = Field(
        default_factory=dict, description="Summary of QA validation results if executed"
    )
    activation_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Context payload for downstream activation workflows",
    )
