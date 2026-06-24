"""
Pydantic models for the Phase 12A Company Intelligence-Driven KPI Template Generator.

Defines the contract for:
  - Researching a company's public footprint via the Market Analysis Agent
  - Producing a CompanyKPIProfile with benchmark-anchored template KPIs
  - Committing accepted templates to the KPI registry with status='template'

Pre-mortem alignment:
  - M1 (benchmark trust): every TemplateKPI carries benchmark_source + confidence
  - M2 (dead KPI registry): committed rows always start with status='template'
  - M6 (legal/citation risk): research_sources lists source TYPES, not specific names
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

BenchmarkSource = Literal["filing", "peer", "inferred"]
"""
Provenance tier for a benchmark range:
  - filing  — company-reported (10-K, annual report, investor day)
  - peer    — industry analyst report or peer-disclosed comparable
  - inferred — LLM-derived from training knowledge; lowest trust
"""


class TemplateKPI(BaseModel):
    """
    A single research-generated KPI awaiting admin acceptance and data connection.

    Lives in the registry with status='template' until the admin maps it to a
    data product and promotes it to status='active'.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Display name, e.g. 'Gross Margin'")
    definition: str = Field(..., description="One-sentence business definition")
    unit: str = Field(..., description="Unit of measure, e.g. '%', '$M', 'days'")
    benchmark_low: Optional[float] = Field(
        None, description="Lower bound of industry benchmark range (numeric)"
    )
    benchmark_high: Optional[float] = Field(
        None, description="Upper bound of industry benchmark range (numeric)"
    )
    benchmark_range: Optional[str] = Field(
        None,
        description="Display-friendly range, e.g. '12-18%' or '5-7 days'. Derived from low/high.",
    )
    benchmark_source: Optional[BenchmarkSource] = Field(
        None, description="Provenance of the benchmark — filing | peer | inferred"
    )
    confidence: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Agent confidence in this KPI's relevance to the company (0-1)",
    )
    domain: str = Field(
        ..., description="Functional domain: 'Finance' | 'Operations' | 'Sales' | etc."
    )
    business_process_id: Optional[str] = Field(
        None,
        description="Business process slug the KPI maps to, when one is identified",
    )


class CompanyKPIProfile(BaseModel):
    """
    Complete research output for a company — industry context + grouped templates.

    Returned by A9_Market_Analysis_Agent.research_company_kpi_profile().
    """

    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(..., description="Echoed company name as researched")
    industry_inferred: Optional[str] = Field(
        None,
        description=(
            "Industry the agent inferred from research (may differ from any "
            "industry_hint supplied by the caller)"
        ),
    )
    is_public: bool = Field(
        False,
        description="Whether the agent could locate public filings — drives M1 trust badging",
    )
    domains: List[str] = Field(
        default_factory=list,
        description="Distinct functional domains represented in template_kpis",
    )
    template_kpis: List[TemplateKPI] = Field(
        default_factory=list, description="Generated KPI templates grouped by domain"
    )
    research_sources: List[str] = Field(
        default_factory=list,
        description=(
            "Source TYPES consulted, M6-compliant — e.g. "
            "['Company annual reports 2024', 'Specialty chemicals analyst reports']. "
            "Never lists specific competitor names or figures as fact."
        ),
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp the profile was produced",
    )
    degraded: bool = Field(
        False,
        description=(
            "True when MA agent ran in LLM-only fallback mode (Perplexity unavailable). "
            "All benchmark_source values will be 'inferred'."
        ),
    )


# ---------------------------------------------------------------------------
# API I/O wrappers — POST /api/v1/templates/research-company
# ---------------------------------------------------------------------------

class CompanyResearchRequest(BaseModel):
    """Request body for POST /api/v1/templates/research-company."""

    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(..., min_length=1, description="Legal or trading name to research")
    client_id: str = Field(
        ..., min_length=1, description="Tenant scope — strict isolation downstream"
    )
    industry_hint: Optional[str] = Field(
        None, description="Optional sector hint, e.g. 'Specialty Chemicals'"
    )
    sub_sector: Optional[str] = Field(
        None, description="Optional sub-sector, e.g. 'Industrial Lubricants' (M5 mitigation)"
    )
    business_description: Optional[str] = Field(
        None,
        max_length=400,
        description="One-line plain English business description (M5 mitigation)",
    )
    max_kpis: int = Field(
        15,
        ge=5,
        le=30,
        description="Soft cap on number of TemplateKPIs to generate",
    )


class CompanyResearchResponse(BaseModel):
    """Response body for POST /api/v1/templates/research-company."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "degraded", "error"] = Field(
        ..., description="success | degraded (LLM-only fallback) | error"
    )
    profile: Optional[CompanyKPIProfile] = Field(
        None, description="Populated on success or degraded; None on error"
    )
    error: Optional[str] = Field(None, description="Error message when status='error'")


# ---------------------------------------------------------------------------
# API I/O wrappers — POST /api/v1/templates/commit
# ---------------------------------------------------------------------------

class AcceptedTemplateKPI(BaseModel):
    """
    A TemplateKPI plus any admin overrides applied during review.

    The admin may edit name, definition, benchmark range, domain, and process
    mapping before commit. The original confidence + benchmark_source are
    preserved for audit.
    """

    model_config = ConfigDict(extra="forbid")

    # Original fields (may be overridden by admin)
    name: str
    definition: str
    unit: str
    domain: str
    business_process_id: Optional[str] = None
    benchmark_low: Optional[float] = None
    benchmark_high: Optional[float] = None
    benchmark_range: Optional[str] = None
    benchmark_source: Optional[BenchmarkSource] = None
    confidence: float = Field(0.5, ge=0.0, le=1.0)

    # Optional natural-semantic ID; backend generates one when omitted
    kpi_id: Optional[str] = Field(
        None,
        description="Override KPI ID (snake_case). Auto-generated from name when omitted.",
    )


class CommitTemplatesRequest(BaseModel):
    """Request body for POST /api/v1/templates/commit."""

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., min_length=1)
    accepted_kpis: List[AcceptedTemplateKPI] = Field(
        ..., min_length=1, description="At least one KPI must be accepted"
    )
    created_by: str = Field(
        "template_generator",
        description="Audit attribution; usually 'template_generator' or admin user id",
    )


class CommittedKPISummary(BaseModel):
    """Per-KPI commit outcome surfaced back to the UI."""

    model_config = ConfigDict(extra="forbid")

    kpi_id: str
    name: str
    status: Literal["written", "skipped_duplicate", "error"]
    error: Optional[str] = None


class CommitTemplatesResponse(BaseModel):
    """Response body for POST /api/v1/templates/commit."""

    model_config = ConfigDict(extra="forbid")

    rows_written: int = Field(..., ge=0)
    rows_skipped: int = Field(..., ge=0)
    rows_failed: int = Field(..., ge=0)
    results: List[CommittedKPISummary] = Field(
        default_factory=list, description="Per-KPI outcome — caller renders status badges"
    )
