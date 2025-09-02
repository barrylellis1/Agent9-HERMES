"""
Data Governance Models

This module defines Pydantic models for the Data Governance Agent protocol.
These models are used for business-to-technical term translation, data access validation,
data quality checks, data lineage tracking, and KPI to data product mapping.
"""

from typing import Dict, List, Optional, Any, Set, Union
from pydantic import BaseModel, Field


class BusinessTermTranslationRequest(BaseModel):
    """Request for translating business terms to technical attribute names."""
    business_terms: List[str] = Field(
        ..., description="List of business terms to translate"
    )
    system: Optional[str] = Field(
        "duckdb", description="System context for mapping (default: duckdb)"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for translation (e.g., principal context)"
    )


class BusinessTermTranslationResponse(BaseModel):
    """Response for business term translation."""
    resolved_terms: Dict[str, str] = Field(
        {}, description="Mapping of business terms to technical attribute names"
    )
    unmapped_terms: List[str] = Field(
        [], description="Business terms that could not be mapped"
    )
    human_action_required: bool = Field(
        False, description="Flag indicating if human action is required"
    )
    human_action_type: Optional[str] = Field(
        None, description="Type of human action required (e.g., clarification)"
    )
    human_action_context: Optional[Dict[str, Any]] = Field(
        None, description="Context for human action"
    )


class DataAccessValidationRequest(BaseModel):
    """Request for validating data access permissions."""
    principal_id: str = Field(..., description="ID of the principal requesting access")
    data_product_id: str = Field(..., description="ID of the data product to access")
    access_type: str = Field(
        "read", description="Type of access (read, write, execute)"
    )


class DataAccessValidationResponse(BaseModel):
    """Response for data access validation."""
    allowed: bool = Field(..., description="Flag indicating if access is allowed")
    reason: Optional[str] = Field(None, description="Reason for access decision")
    policy_id: Optional[str] = Field(None, description="ID of the applied policy")


class DataLineageRequest(BaseModel):
    """Request for retrieving data lineage."""
    data_product_id: str = Field(..., description="ID of the data product")
    max_depth: Optional[int] = Field(
        3, description="Maximum depth of lineage graph to return"
    )


class LineageNode(BaseModel):
    """Represents a node in the data lineage graph."""
    id: str = Field(..., description="ID of the node")
    name: str = Field(..., description="Name of the node")
    type: str = Field(..., description="Type of the node (table, view, file, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for the node"
    )


class LineageEdge(BaseModel):
    """Represents an edge in the data lineage graph."""
    source: str = Field(..., description="ID of the source node")
    target: str = Field(..., description="ID of the target node")
    relationship: str = Field(
        ..., description="Relationship type (e.g., 'derived_from')"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for the edge"
    )


class DataLineageResponse(BaseModel):
    """Response for data lineage retrieval."""
    data_product_id: str = Field(..., description="ID of the data product")
    lineage_nodes: List[LineageNode] = Field(
        [], description="Nodes in the lineage graph"
    )
    lineage_edges: List[LineageEdge] = Field(
        [], description="Edges in the lineage graph"
    )


class DataQualityIssue(BaseModel):
    """Represents a data quality issue."""
    severity: str = Field(..., description="Severity of the issue (high, medium, low)")
    dimension: str = Field(
        ..., description="Quality dimension (completeness, accuracy, etc.)"
    )
    description: str = Field(..., description="Description of the issue")
    affected_columns: Optional[List[str]] = Field(
        None, description="Columns affected by the issue"
    )


class DataQualityCheckRequest(BaseModel):
    """Request for checking data quality."""
    data_product_id: str = Field(..., description="ID of the data product")
    dimensions: Optional[List[str]] = Field(
        None, description="Quality dimensions to check"
    )


class DataQualityCheckResponse(BaseModel):
    """Response for data quality check."""
    data_product_id: str = Field(..., description="ID of the data product")
    quality_metrics: Dict[str, float] = Field(
        {}, description="Quality metrics by dimension"
    )
    issues: List[DataQualityIssue] = Field([], description="Data quality issues found")


class KPIDataProductMappingRequest(BaseModel):
    """Request for mapping KPIs to data products."""
    kpi_names: List[str] = Field(
        ..., description="List of KPI names to map to data products"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for mapping (e.g., principal context)"
    )


class KPIDataProductMapping(BaseModel):
    """Mapping of a KPI to a data product."""
    kpi_name: str = Field(..., description="Name of the KPI")
    data_product_id: str = Field(..., description="ID of the data product")
    technical_name: Optional[str] = Field(
        None, description="Technical name of the KPI in the data product"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for the mapping"
    )


class KPIDataProductMappingResponse(BaseModel):
    """Response for KPI to data product mapping."""
    mappings: List[KPIDataProductMapping] = Field(
        [], description="List of KPI to data product mappings"
    )
    unmapped_kpis: List[str] = Field(
        [], description="KPIs that could not be mapped to data products"
    )
    human_action_required: bool = Field(
        False, description="Flag indicating if human action is required"
    )
    human_action_context: Optional[Dict[str, Any]] = Field(
        None, description="Context for human action"
    )


class DataAssetPathRequest(BaseModel):
    """Request for resolving data asset paths."""
    asset_name: str = Field(..., description="Name of the data asset")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context for resolution"
    )


class DataAssetPathResponse(BaseModel):
    """Response for data asset path resolution."""
    asset_name: str = Field(..., description="Name of the data asset")
    data_product_id: str = Field(..., description="ID of the data product")
    asset_path: str = Field(..., description="Path to the data asset")
    access_type: str = Field("read", description="Type of access allowed")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata for the asset"
    )
