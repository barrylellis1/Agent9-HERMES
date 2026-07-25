"""
Pydantic models for the Phase 12F Business Process Template Generator.

Defines the contract for:
  - Selecting relevant processes from the canonical taxonomy
    (src/registry/canonical/business_processes.py) for a client, plus
    proposing a small number of client-specific extras
  - Committing accepted processes to the business_processes registry

Unlike the KPI template generator, no external research is needed — this is
a selection/curation task over an already-known taxonomy, not benchmark
research. Canonical selections are always hydrated server-side from
BP_BY_ID, never trusted verbatim from the LLM response, so the canonical
taxonomy stays the single source of truth for their content.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

class TemplateBusinessProcess(BaseModel):
    """
    A single candidate business process awaiting admin acceptance.

    `source='canonical'` rows are hydrated verbatim from BP_BY_ID; the LLM
    only chose to include them. `source='extra'` rows are LLM-proposed and
    not in the canonical taxonomy.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(
        None, description="Canonical id when source='canonical'; None for extras until slugified"
    )
    name: str = Field(..., description="Display name, e.g. 'Expense Management'")
    domain: str = Field(..., description="Functional domain: 'Finance' | 'Operations' | etc.")
    description: Optional[str] = Field(None, description="One-sentence description")
    owner_role: Optional[str] = Field(None, description="Primary role responsible, e.g. 'CFO'")
    stakeholder_roles: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source: Literal["canonical", "extra"] = Field(
        ..., description="canonical = verbatim from the taxonomy; extra = LLM-proposed gap"
    )
    confidence: float = Field(
        0.5, ge=0.0, le=1.0, description="Agent confidence this process applies to the client"
    )
    rationale: Optional[str] = Field(
        None, description="Short reason this process fits the client — not asserted as external fact"
    )


class CompanyBusinessProcessProfile(BaseModel):
    """
    Complete selection output for a client — selected canonical + extra processes.

    Returned by A9_Market_Analysis_Agent.research_company_business_processes().
    """

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., description="Tenant this profile was generated for")
    industry_used: Optional[str] = Field(
        None, description="Industry the selection was grounded in — stored profile or override"
    )
    domains: List[str] = Field(
        default_factory=list, description="Distinct functional domains represented in `selected`"
    )
    selected: List[TemplateBusinessProcess] = Field(
        default_factory=list, description="Candidate processes — canonical + extra, grouped by domain"
    )
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    degraded: bool = Field(
        False,
        description=(
            "True when no stored company profile and no industry_override were available — "
            "selection falls back to a generic cross-industry subset of the canonical taxonomy."
        ),
    )


# ---------------------------------------------------------------------------
# API I/O wrappers — POST /api/v1/templates/research-business-processes
# ---------------------------------------------------------------------------

class BusinessProcessResearchRequest(BaseModel):
    """Request body for POST /api/v1/templates/research-business-processes."""

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., min_length=1, description="Tenant scope — strict isolation downstream")
    industry_override: Optional[str] = Field(
        None,
        description="Manual industry fallback — only needed when no stored company profile exists",
    )
    max_extra_processes: int = Field(
        5, ge=0, le=15, description="Soft cap on LLM-proposed processes not in the canonical taxonomy"
    )


class BusinessProcessResearchResponse(BaseModel):
    """Response body for POST /api/v1/templates/research-business-processes."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "degraded", "error"] = Field(
        ..., description="success | degraded (no industry context) | error"
    )
    profile: Optional[CompanyBusinessProcessProfile] = Field(
        None, description="Populated on success or degraded; None on error"
    )
    error: Optional[str] = Field(None, description="Error message when status='error'")


# ---------------------------------------------------------------------------
# API I/O wrappers — POST /api/v1/templates/commit-business-processes
# ---------------------------------------------------------------------------

class AcceptedTemplateBusinessProcess(BaseModel):
    """
    A TemplateBusinessProcess plus any admin overrides applied during review.
    """

    model_config = ConfigDict(extra="forbid")

    id: Optional[str] = Field(
        None, description="Override id (snake_case). Auto-generated from domain+name when omitted."
    )
    name: str
    domain: str
    description: Optional[str] = None
    owner_role: Optional[str] = None
    stakeholder_roles: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    source: Literal["canonical", "extra"] = "extra"
    confidence: float = Field(0.5, ge=0.0, le=1.0)


class CommitBusinessProcessTemplatesRequest(BaseModel):
    """Request body for POST /api/v1/templates/commit-business-processes."""

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., min_length=1)
    accepted_processes: List[AcceptedTemplateBusinessProcess] = Field(
        ..., min_length=1, description="At least one process must be accepted"
    )
    created_by: str = Field(
        "bp_template_generator",
        description="Audit attribution; usually 'bp_template_generator' or admin user id",
    )


class CommittedBusinessProcessSummary(BaseModel):
    """Per-process commit outcome surfaced back to the UI."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    status: Literal["written", "skipped_duplicate", "error"]
    error: Optional[str] = None


class CommitBusinessProcessTemplatesResponse(BaseModel):
    """Response body for POST /api/v1/templates/commit-business-processes."""

    model_config = ConfigDict(extra="forbid")

    rows_written: int = Field(..., ge=0)
    rows_skipped: int = Field(..., ge=0)
    rows_failed: int = Field(..., ge=0)
    results: List[CommittedBusinessProcessSummary] = Field(default_factory=list)
