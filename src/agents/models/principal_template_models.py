"""
Pydantic models for the Phase 12E Company Intelligence-Driven Principal Template Generator.

Defines the contract for:
  - Researching a company's leadership team via the Market Analysis Agent
  - Producing a CompanyPrincipalProfile with verified-source-attributed
    template principals (NO decision_style or communication_style inference)
  - Committing accepted templates to the principal_profiles registry with
    status='template' and email optional
  - Promoting templates to status='active' after admin enters email

Pre-mortem alignment (DEVELOPMENT_PLAN.md Phase 12E):
  - P1 (misidentification): every TemplatePrincipal carries confidence + source_urls
  - P2 (stale data): generated_at + per-source as_of_date stamps
  - P4 (legal/consent): only public information; one-click delete path
  - P6 (email guessing): email field is NEVER inferred; admin-entered only
  - P7 (org chart): reports_to populated only when explicitly stated in a source

Scope decision (2026-06-04):
  - Decision 1: NO decision_style or communication_style inference. These fields
    are absent from TemplatePrincipal. Admin sets them manually post-promote
    after seeing Solution Finder output in different styles.
  - Decision 2: email may be NULL at commit; required at promote.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

RoleCategory = Literal[
    "CEO", "CFO", "COO", "CTO", "CIO", "CHRO", "CMO", "CRO", "CDO", "CISO",
    "General Counsel", "Board Chair", "Board Member", "Other Executive",
]
"""High-level role taxonomy. Used for UI grouping and role-based access defaults."""


class TemplatePrincipal(BaseModel):
    """
    A research-generated principal awaiting admin acceptance and email entry.

    Lives in the registry with status='template' until the admin enters an
    email address and explicitly promotes it to status='active'.
    """

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., description="Verified or best-known full name")
    role: str = Field(..., description="Display title, e.g. 'Chief Financial Officer'")
    role_category: RoleCategory = Field(
        ..., description="Normalized role taxonomy for UI grouping"
    )
    tenure_years: Optional[float] = Field(
        None,
        description="Approximate years in current role; null when not disclosed",
    )
    appointed_date: Optional[str] = Field(
        None, description="Date appointed if disclosed (ISO format)"
    )
    source_urls: List[str] = Field(
        default_factory=list,
        description="Direct source URLs (10-K, proxy, IR page) — used for per-row attribution badge",
    )
    as_of_date: Optional[str] = Field(
        None,
        description="Publication date of the most recent source — drives 'as of' stamp in UI (P2)",
    )
    confidence: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description=(
            "Agent confidence in this identification. P1 mitigation: UI may "
            "default-accept only when confidence ≥ 0.8 (stricter than 0.6 for KPIs)."
        ),
    )
    reports_to: Optional[str] = Field(
        None,
        description="Name of person they report to — populated ONLY when explicitly stated in a source (P7)",
    )
    bio_snippet: Optional[str] = Field(
        None,
        max_length=500,
        description="One-paragraph public bio drawn from research; for admin context only",
    )


class CompanyPrincipalProfile(BaseModel):
    """
    Complete research output for a company — leadership team grouped by role.

    Returned by A9_Market_Analysis_Agent.research_company_principals().
    """

    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(..., description="Echoed company name as researched")
    template_principals: List[TemplatePrincipal] = Field(
        default_factory=list,
        description="Generated principal templates ordered by role_category priority",
    )
    research_sources: List[str] = Field(
        default_factory=list,
        description=(
            "Source TYPES consulted, e.g. '10-K and proxy 2024', "
            "'Company investor relations site'. M6-compliant."
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
            "Source URLs may be absent; confidence values reduced."
        ),
    )


# ---------------------------------------------------------------------------
# API I/O wrappers — POST /api/v1/templates/research-principals
# ---------------------------------------------------------------------------

class CompanyPrincipalsResearchRequest(BaseModel):
    """Request body for POST /api/v1/templates/research-principals."""

    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(..., min_length=1, description="Legal or trading name to research")
    client_id: str = Field(
        ..., min_length=1, description="Tenant scope — strict isolation downstream"
    )
    roles_filter: Optional[List[RoleCategory]] = Field(
        default=None,
        description=(
            "Optional role filter. When None, defaults to the C-suite + executive set: "
            "CEO, CFO, COO, CTO, CIO, CHRO, CMO, CRO. Pass a custom list to target "
            "specific roles (e.g. only ['CEO', 'CFO'])."
        ),
    )
    max_principals: int = Field(
        10,
        ge=3,
        le=20,
        description="Soft cap on number of TemplatePrincipals to return",
    )


class CompanyPrincipalsResearchResponse(BaseModel):
    """Response body for POST /api/v1/templates/research-principals."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "degraded", "error"] = Field(
        ..., description="success | degraded (LLM-only fallback) | error"
    )
    profile: Optional[CompanyPrincipalProfile] = Field(
        None, description="Populated on success or degraded; None on error"
    )
    error: Optional[str] = Field(None, description="Error message when status='error'")


# ---------------------------------------------------------------------------
# API I/O wrappers — POST /api/v1/templates/commit-principals
# ---------------------------------------------------------------------------

class AcceptedTemplatePrincipal(BaseModel):
    """
    A TemplatePrincipal plus any admin overrides applied during review.

    Decision 2: email is optional at commit. Admin may enter it here OR
    leave NULL and enter later via the promote endpoint.
    """

    model_config = ConfigDict(extra="forbid")

    # Original fields (may be overridden by admin)
    full_name: str
    role: str
    role_category: RoleCategory
    tenure_years: Optional[float] = None
    appointed_date: Optional[str] = None
    source_urls: List[str] = Field(default_factory=list)
    as_of_date: Optional[str] = None
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    reports_to: Optional[str] = None
    bio_snippet: Optional[str] = None

    # Admin-entered field (NEVER inferred — Decision 2 + P6)
    # Format validation lives in the route handler; using plain str here keeps
    # the email-validator dependency optional.
    email: Optional[str] = Field(
        None,
        description="Contact email. Optional at commit; required to promote to active.",
    )

    # Optional natural-semantic ID; backend generates from name + role when omitted
    principal_id: Optional[str] = Field(
        None,
        description="Override principal ID (snake_case). Auto-generated from name + role when omitted.",
    )


class CommitPrincipalsRequest(BaseModel):
    """Request body for POST /api/v1/templates/commit-principals."""

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., min_length=1)
    accepted_principals: List[AcceptedTemplatePrincipal] = Field(
        ..., min_length=1, description="At least one principal must be accepted"
    )
    created_by: str = Field(
        "principal_intelligence_ui",
        description="Audit attribution; usually 'principal_intelligence_ui' or admin user id",
    )


class CommittedPrincipalSummary(BaseModel):
    """Per-principal commit outcome surfaced back to the UI."""

    model_config = ConfigDict(extra="forbid")

    principal_id: str
    full_name: str
    status: Literal["written", "skipped_duplicate", "error"]
    has_email: bool = Field(
        ..., description="True when email was entered at commit; drives 'ready to promote' UI"
    )
    error: Optional[str] = None


class CommitPrincipalsResponse(BaseModel):
    """Response body for POST /api/v1/templates/commit-principals."""

    model_config = ConfigDict(extra="forbid")

    rows_written: int = Field(..., ge=0)
    rows_skipped: int = Field(..., ge=0)
    rows_failed: int = Field(..., ge=0)
    results: List[CommittedPrincipalSummary] = Field(
        default_factory=list,
        description="Per-principal outcome — caller renders status badges + email entry CTAs",
    )


# ---------------------------------------------------------------------------
# API I/O wrappers — PATCH /api/v1/registry/principals/{id}/promote
# ---------------------------------------------------------------------------

class PromotePrincipalRequest(BaseModel):
    """Request body for PATCH /api/v1/registry/principals/{id}/promote.

    The promote operation transitions a template principal to active state.
    Hard requirement: email MUST be present on the row (set either at commit
    via AcceptedTemplatePrincipal.email, or via this request body which patches
    email atomically before promotion).
    """

    model_config = ConfigDict(extra="forbid")

    client_id: str = Field(..., min_length=1)
    email: Optional[str] = Field(
        None,
        description=(
            "If the template was committed without email, supply it here. "
            "The endpoint patches email AND status='active' atomically. "
            "If email is None AND the row has no email, the endpoint returns 400. "
            "Format validation happens in the route handler."
        ),
    )


class PromotePrincipalResponse(BaseModel):
    """Response body for PATCH /api/v1/registry/principals/{id}/promote."""

    model_config = ConfigDict(extra="forbid")

    principal_id: str
    status: Literal["active"] = Field(
        "active", description="Always 'active' on successful promote"
    )
    message: str
