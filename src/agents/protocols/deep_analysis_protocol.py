"""
Protocol definition for the Deep Analysis Agent.
Defines the interface that must be implemented by any agent providing
structured, auditable deep analysis capabilities.
"""
from __future__ import annotations

from typing import Protocol, Optional, runtime_checkable

from src.agents.models.deep_analysis_models import (
    DeepAnalysisRequest,
    DeepAnalysisPlan,
    DeepAnalysisResponse,
)


@runtime_checkable
class DeepAnalysisProtocol(Protocol):
    """Protocol for Deep Analysis Agent (A2A-compliant)."""

    async def enumerate_dimensions(self, request: DeepAnalysisRequest) -> DeepAnalysisResponse:
        """
        Enumerate candidate analysis dimensions (MECE-guided) for a KPI/timeframe.
        Returns a response with proposed dimensions in the plan and an audit trail.
        """
        ...

    async def plan_deep_analysis(self, request: DeepAnalysisRequest) -> DeepAnalysisResponse:
        """
        Build an analysis plan using KT as the core backbone and SCQA/MECE framing.
        The plan describes grouped/timeframe comparisons to be executed by the DPA.
        """
        ...

    async def execute_deep_analysis(self, plan: DeepAnalysisPlan) -> DeepAnalysisResponse:
        """
        Execute a previously built plan via the Data Product Agent and produce
        a KT "Is/Is Not" table, change-points, and a concise SCQA summary.
        Narrative hypotheses are generated via A9_LLM_Service (optional).
        """
        ...
