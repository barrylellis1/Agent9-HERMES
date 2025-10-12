"""
Protocol definition for the Solution Finder Agent.
Defines the interface for problem intake, option generation/evaluation,
trade-off analysis, recommendation, and HITL support.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.agents.models.solution_finder_models import (
    SolutionFinderRequest,
    SolutionFinderResponse,
)


@runtime_checkable
class SolutionFinderProtocol(Protocol):
    """Protocol for Solution Finder Agent (A2A-compliant)."""

    async def recommend_actions(self, request: SolutionFinderRequest) -> SolutionFinderResponse:
        """
        Generate, evaluate, and recommend solutions for a problem/diagnosis, possibly
        using Deep Analysis output and optional Market Analysis input.
        """
        ...

    async def evaluate_options(self, request: SolutionFinderRequest) -> SolutionFinderResponse:
        """
        Evaluate solution options (impact/cost/risk) and return a ranked list with a trade-off matrix.
        """
        ...
