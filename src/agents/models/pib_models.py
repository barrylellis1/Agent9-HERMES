"""
Pydantic models for the Principal Intelligence Briefing (PIB).

These models represent the data contracts for briefing composition,
token management, and email delivery.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BriefingFormat(str, Enum):
    DETAILED = "detailed"
    DIGEST = "digest"


class BriefingRunStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class TokenType(str, Enum):
    DEEP_LINK = "deep_link"
    SNOOZE = "snooze"
    DELEGATE = "delegate"
    REQUEST_INFO = "request_info"
    APPROVE = "approve"


# ---------------------------------------------------------------------------
# Content models — assembled by the composition engine
# ---------------------------------------------------------------------------

class SituationBriefingItem(BaseModel):
    """A single detected situation formatted for the PIB email."""

    situation_id: str
    kpi_assessment_id: str
    kpi_name: str
    severity: str                    # "critical" | "high" | "medium" | "low"
    severity_score: float
    description: str
    deviation_summary: str           # e.g. "decreased 32.9% vs baseline (threshold=red)"
    current_value: Optional[float] = None
    is_new: bool = True              # True if not present in previous run
    weeks_open: int = 0              # 0 for new situations
    deep_link_token: Optional[str] = None   # UUID token for Launch DA link
    snooze_token: Optional[str] = None
    delegate_token: Optional[str] = None
    request_info_token: Optional[str] = None


class SolutionProgressItem(BaseModel):
    """A solution currently being tracked by Value Assurance."""

    solution_id: str
    solution_title: str
    kpi_name: str
    status: str                      # e.g. "measuring", "validated", "partial"
    expected_impact_lower: Optional[float] = None
    expected_impact_upper: Optional[float] = None
    accepted_at: Optional[datetime] = None
    approve_token: Optional[str] = None   # token for approve-from-email (if pending HITL)


class ManagedSituationItem(BaseModel):
    """A situation that has been snoozed or delegated."""

    situation_id: str
    kpi_name: str
    action_type: str                 # "snooze" | "delegate"
    action_taken_at: datetime
    snooze_expires_at: Optional[datetime] = None
    delegated_to: Optional[str] = None    # principal name


class UrgencyItem(BaseModel):
    """A situation that has been open for too long without action."""

    situation_id: str
    kpi_name: str
    severity: str
    weeks_open: int
    deep_link_token: Optional[str] = None


class BriefingContent(BaseModel):
    """
    Fully assembled PIB content ready for template rendering.

    Produced by the PIB composition engine; consumed by the email template.
    """

    principal_id: str
    principal_name: str
    principal_role: str
    client_id: str
    client_name: str
    assessment_run_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    briefing_format: BriefingFormat = BriefingFormat.DETAILED

    # Email sections
    new_situations: List[SituationBriefingItem] = Field(default_factory=list)
    urgency_flags: List[UrgencyItem] = Field(default_factory=list)
    solutions_in_progress: List[SolutionProgressItem] = Field(default_factory=list)
    managed_situations: List[ManagedSituationItem] = Field(default_factory=list)

    # Decision Studio base URL for deep links
    decision_studio_url: str = "http://localhost:5173"

    @property
    def has_content(self) -> bool:
        return bool(
            self.new_situations
            or self.urgency_flags
            or self.solutions_in_progress
            or self.managed_situations
        )


# ---------------------------------------------------------------------------
# Persistence models (map to Supabase tables)
# ---------------------------------------------------------------------------

class BriefingToken(BaseModel):
    """Maps to the briefing_tokens table."""

    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    token: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    token_type: TokenType
    principal_id: str
    situation_id: str
    kpi_assessment_id: Optional[str] = None
    briefing_run_id: Optional[str] = None
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BriefingRun(BaseModel):
    """Maps to the briefing_runs table."""

    id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    principal_id: str
    client_id: str
    assessment_run_id: Optional[str] = None
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    new_situation_count: int = 0
    format: BriefingFormat = BriefingFormat.DETAILED
    email_to: str
    status: BriefingRunStatus = BriefingRunStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BriefingConfig(BaseModel):
    """Run-level configuration for a PIB generation."""

    principal_id: str
    client_id: str
    email_to: Optional[str] = None        # overrides principal profile email
    format: BriefingFormat = BriefingFormat.DETAILED
    urgency_threshold_weeks: int = 2      # flag situations open longer than this
    dry_run: bool = False                 # compose but do not send
    decision_studio_url: str = "http://localhost:5173"
