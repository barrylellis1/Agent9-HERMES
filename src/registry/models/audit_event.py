"""Shared audit_events record (design note:
docs/architecture/audit_event_system_design.md).

One table, three event families, distinguished by `event_type` prefix and by
which caller writes them -- never by a schema difference:

  - SF narrative/debug events (pilot scope) -- `outcome=None`, they are not
    checks and have no verdict.
  - Infra C's SOC 2 access/action trail -- `outcome` 'pass'/'fail' maps 1:1
    from that draft's 'success'/'failure' vocabulary (reconciled onto this
    one per the design note's schema note).
  - The stage-wise reliability panel (2026-10-02 scope extension) -- SA
    detection confidence, DA's [ROLLUP-CHECK], `check_tree_reconciles`,
    `check_slice_validity`, KPI coverage. Each of these IS a check with a
    real verdict.

`severity` and `outcome` are independent axes -- do not infer one from the
other. A `fail` can be `warning` severity (non-fatal by design); an `abstain`
can be `info` severity (routine, e.g. nothing to check yet).
"""
from __future__ import annotations

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    id: Optional[str] = Field(None, description="UUID, server-generated on insert")
    client_id: str = Field(..., description="Client/tenant this event belongs to")
    event_type: str = Field(
        ..., description="Namespaced event name, e.g. 'reliability.rollup_check', 'auth.login', 'llm_debate_completed'"
    )
    severity: Literal["info", "warning", "error"] = Field(
        ..., description="How urgent this is to a human reader -- independent of outcome"
    )
    outcome: Optional[Literal["pass", "fail", "abstain"]] = Field(
        None,
        description=(
            "What a check concluded. None means this event_type is not a check -- no verdict to "
            "render (e.g. SF's narrative events). Mirrors src/analysis's True/False/None convention: "
            "abstain/None is excluded from both numerator and denominator wherever this is aggregated, "
            "never treated as pass."
        ),
    )
    source_agent: str = Field(..., description="e.g. 'A9_Deep_Analysis_Agent'")
    request_id: Optional[str] = Field(None, description="Correlates to the workflow run that produced this event")
    resource_type: Optional[str] = Field(None, description="What the event is about, e.g. 'kpi', 'dimension'")
    resource_id: Optional[str] = Field(None, description="The specific resource, e.g. a kpi_id or dimension label")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific detail")
    created_at: Optional[str] = Field(None, description="ISO timestamp, server-assigned on insert")
