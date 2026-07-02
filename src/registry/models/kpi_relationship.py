"""KPI relationship model for compound alert detection (Phase 11I-B)."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class KPIRelationship(BaseModel):
    """Declared relationship between two KPIs for compound alert detection."""
    kpi_id: str = Field(..., description="Primary KPI identifier")
    related_kpi_id: str = Field(..., description="Related KPI identifier")
    client_id: str = Field(..., description="Client/tenant this relationship belongs to")
    relationship_type: Literal["volume_margin", "receivables_revenue", "cost_revenue", "custom"] = Field(
        ..., description="Class of relationship"
    )
    conflict_direction: Literal["diverging", "converging"] = Field(
        ...,
        description=(
            "'diverging' = opposite movements signal a problem (revenue UP / margin DOWN); "
            "'converging' = same-direction movements signal a problem (receivables UP / revenue UP)"
        )
    )
    description: Optional[str] = Field(None, description="Human-readable description of the relationship")
