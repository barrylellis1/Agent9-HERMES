"""Evaluations are read back with the solutions they belong to.

Found live 2026-10-12: `upsert_evaluation` had always written evaluation rows,
but nothing read them. Every solution reloaded from Supabase carried a verdict
with no measurement behind it, so the Portfolio page could never show the
breakdown, and the trajectory chart said "first measurement period in progress"
beside a final verdict.
"""
from __future__ import annotations

import json
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.models.value_assurance_models import AcceptedSolution, SolutionVerdict
from src.agents.new.a9_value_assurance_agent import _attach_evaluation
from src.database.va_solutions_store import VASolutionsStore

_STRATEGY = {
    "original_priorities": ["margin"], "current_priorities": ["margin"],
    "priority_drift": False, "priority_overlap": 1.0, "kpi_still_monitored": True,
    "threshold_changed": False, "current_threshold": None, "business_process_active": True,
    "data_product_active": True, "principal_still_accountable": True,
    "current_principal_id": "cfo_001", "alignment_verdict": "ALIGNED",
    "drift_factors": [], "drift_summary": None,
}
_COMPOSITE = {
    "kpi_verdict": "VALIDATED", "strategy_verdict": "ALIGNED",
    "composite_label": "Full success", "include_in_roi_totals": True,
    "recommended_action": "Document outcome.", "executive_attention_required": False,
}


def _db_row(solution_id: str = "s1") -> dict:
    """An evaluation row as PostgREST returns it."""
    return {
        "id": "row-1", "created_at": "2026-10-05T00:00:00+00:00", "include_in_roi": True,
        "solution_id": solution_id,
        "baseline_kpi_value": 30.0, "current_kpi_value": 31.7, "total_kpi_change": 1.7,
        "control_group_change": 0.4, "market_driven_recovery": 0.0, "seasonal_component": 0.0,
        "attributable_impact": 1.3, "expected_impact_lower": 1.0, "expected_impact_upper": 2.2,
        "verdict": "VALIDATED", "confidence": "MODERATE",
        "confidence_rationale": "1/3 attribution inputs provided.",
        "attribution_method": "difference_in_differences",
        "control_group_description": "Independent Service Centers",
        "market_context_summary": None,
        "strategy_alignment": _STRATEGY, "composite_verdict": _COMPOSITE,
        "evaluated_at": "2026-10-05T00:00:00+00:00",
        "vs_plan_verdict": None, "vs_plan_pct": None,
    }


def _solution(**over) -> AcceptedSolution:
    base = dict(
        solution_id="s1", situation_id="sit1", kpi_id="premium_mix_pct", principal_id="cfo_001",
        client_id="lubricants", approved_at="2026-10-04T00:00:00+00:00",
        solution_description="Fleet account win-back", expected_impact_lower=1.0,
        expected_impact_upper=2.2, status=SolutionVerdict.VALIDATED,
        strategy_snapshot=dict(
            principal_priorities=["margin"], principal_role="CFO", business_process_domain="finance",
            data_product_id="dp", kpi_threshold_at_approval=30.0, key_assumptions=[],
            business_context_name="Summit", captured_at="2026-10-04T00:00:00+00:00",
        ),
    )
    base.update(over)
    return AcceptedSolution(**base)


async def _shaped(rows) -> dict:
    store = VASolutionsStore.__new__(VASolutionsStore)
    store.enabled = True
    store.headers = {}
    store.evaluations_endpoint = "http://local/evals"
    response = MagicMock()
    response.content = json.dumps(rows).encode()
    response.raise_for_status = MagicMock()
    client = MagicMock()
    client.get = AsyncMock(return_value=response)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    with patch("src.database.va_solutions_store.httpx.AsyncClient", return_value=ctx):
        return await store.get_evaluations_for_solutions(["s1"])


class TestStoreReadsEvaluationsBack:
    @pytest.mark.asyncio
    async def test_row_is_shaped_for_the_model(self):
        out = await _shaped([_db_row()])
        row = out["s1"]
        assert "strategy_alignment" not in row and row["strategy_check"] == _STRATEGY
        assert not {"id", "created_at", "include_in_roi"} & set(row)

    @pytest.mark.asyncio
    async def test_json_stored_as_text_is_decoded(self):
        raw = _db_row()
        raw["strategy_alignment"] = json.dumps(_STRATEGY)
        raw["composite_verdict"] = json.dumps(_COMPOSITE)
        out = await _shaped([raw])
        assert out["s1"]["strategy_check"]["alignment_verdict"] == "ALIGNED"

    @pytest.mark.asyncio
    async def test_no_ids_means_no_query(self):
        store = VASolutionsStore.__new__(VASolutionsStore)
        store.enabled = True
        assert await store.get_evaluations_for_solutions([]) == {}


class TestAttachEvaluation:
    @pytest.mark.asyncio
    async def test_a_stored_row_becomes_the_solutions_evaluation(self):
        row = (await _shaped([_db_row()]))["s1"]
        sol = _attach_evaluation(_solution(), row, None, logging.getLogger("t"))
        assert sol.impact_evaluation is not None
        assert sol.impact_evaluation.attributable_impact == 1.3
        assert sol.impact_evaluation.confidence.value == "MODERATE"
        assert sol.impact_evaluation.control_group_description == "Independent Service Centers"

    def test_nothing_stored_and_nothing_held_stays_empty(self):
        sol = _attach_evaluation(_solution(), None, None, logging.getLogger("t"))
        assert sol.impact_evaluation is None

    @pytest.mark.asyncio
    async def test_an_evaluation_already_held_survives_a_reload_with_no_row(self):
        """evaluate() stores the evaluation in memory. If its persist failed, the
        next portfolio reload must not wipe it."""
        row = (await _shaped([_db_row()]))["s1"]
        held = _attach_evaluation(_solution(), row, None, logging.getLogger("t"))
        reloaded = _attach_evaluation(_solution(), None, held, logging.getLogger("t"))
        assert reloaded.impact_evaluation is held.impact_evaluation

    def test_a_row_that_does_not_parse_is_absent_not_defaulted(self, caplog):
        with caplog.at_level(logging.WARNING):
            sol = _attach_evaluation(_solution(), {"solution_id": "s1", "verdict": "VALIDATED"}, None, logging.getLogger("t"))
        assert sol.impact_evaluation is None
        assert "did not parse" in caplog.text
