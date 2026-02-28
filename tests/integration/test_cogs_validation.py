"""
Integration test to validate Cost of Goods Sold (COGS) amounts used by Situation Awareness
match direct SQL computed from the FI_Star_View for Last Quarter vs Year-over-Year.

This test prepares the FI Star environment (tables + view) via the Orchestrator and
then compares the SA agent's detected COGS value/baseline with a direct SQL computation.

Assumptions:
- Local CSVs referenced by the contract are available (as in the Decision Studio flow).
- DuckDB database is at data/agent9-hermes.duckdb (default in agents).
"""
import os
import sys
import math
import pytest

# Add project root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import duckdb

from src.agents.models.situation_awareness_models import (
    SituationDetectionRequest,
    TimeFrame,
    ComparisonType,
)

@pytest.mark.asyncio
async def test_cogs_amounts_match_sql(orchestrator):
    # Ensure FI Star tables and view are prepared, same as Decision Studio
    contract_path = os.path.join(ROOT, "src", "registry_references", "data_product_registry", "data_products", "fi_star_schema.yaml")
    prep = await orchestrator.prepare_environment(contract_path, view_name="FI_Star_View")
    assert prep.get("status") in {"success", "error"}, "Prep call should return a status key"

    # Build a detection request for Last Quarter, Year-over-Year
    req = SituationDetectionRequest(
        request_id="test-cogs-validation",
        principal_context={
            "role": "CFO",
            "principal_id": "cfo_001",
            "business_processes": ["Finance"],
            "default_filters": {},
            "decision_style": "Analytical",
            "communication_style": "Concise",
            "preferred_timeframes": [TimeFrame.LAST_QUARTER]
        },
        business_processes=["Finance: Profitability Analysis"],
        timeframe=TimeFrame.LAST_QUARTER,
        comparison_type=ComparisonType.YEAR_OVER_YEAR,
        filters={}
    )

    resp = await orchestrator.execute_agent_method(
        "A9_Situation_Awareness_Agent", "detect_situations", {"request": req.model_dump()}
    )
    # Normalize to dict (avoid Pydantic v1 dict())
    if hasattr(resp, 'model_dump'):
        resp = resp.model_dump()
    else:
        try:
            resp = {
                "status": getattr(resp, 'status', None),
                "situations": getattr(resp, 'situations', []),
                "message": getattr(resp, 'message', ''),
            }
        except Exception:
            resp = {"status": None, "situations": [], "message": ""}

    assert isinstance(resp, dict), "Response should be a dict after normalization"
    assert resp.get("status") == "success", f"SA detect_situations failed: {resp}"

    # Find the COGS situation
    situations = resp.get("situations", [])
    cogs = None
    for s in situations:
        name = s.get("kpi_name") if isinstance(s, dict) else getattr(s, "kpi_name", "")
        if str(name).lower() in {"cost of goods sold", "cogs", "cost of sales"}:
            cogs = s
            break

    pytest.skip("COGS situation not returned; skipping amount validation") if cogs is None else None

    kv = cogs.get("kpi_value") if isinstance(cogs, dict) else getattr(cogs, "kpi_value", {})
    current = kv.get("value") if isinstance(kv, dict) else getattr(kv, "value", None)
    baseline = kv.get("comparison_value") if isinstance(kv, dict) else getattr(kv, "comparison_value", None)

    # Compute the same via direct SQL on DuckDB
    db_path = os.path.join(ROOT, "data", "agent9-hermes-api.duckdb")
    if not os.path.exists(db_path):
        pytest.skip("DuckDB path not found; skipping COGS SQL validation")

    con = duckdb.connect(db_path)
    sql = r'''
    WITH q AS (
      SELECT date_trunc('quarter', current_date) AS this_q_start
    ), bounds AS (
      SELECT 
        -- Last quarter start: take one day before current quarter start, then truncate to quarter
        date_trunc('quarter', this_q_start - INTERVAL 1 day) AS lq_start,
        this_q_start AS lq_end,
        -- Prior-year same quarter bounds
        date_trunc('quarter', (this_q_start - INTERVAL 1 day) - INTERVAL 1 year) AS py_lq_start,
        this_q_start - INTERVAL 1 year AS py_lq_end
      FROM q
    ), curr AS (
      SELECT SUM("Transaction Value Amount") AS cogs
      FROM FI_Star_View, bounds
      WHERE "Account Hierarchy Desc" = 'Cost of Goods Sold'
        AND "Version" = 'Actual'
        AND "Transaction Date" >= lq_start
        AND "Transaction Date" <  lq_end
    ), prev AS (
      SELECT SUM("Transaction Value Amount") AS cogs
      FROM FI_Star_View, bounds
      WHERE "Account Hierarchy Desc" = 'Cost of Goods Sold'
        AND "Version" = 'Actual'
        AND "Transaction Date" >= py_lq_start
        AND "Transaction Date" <  py_lq_end
    )
    SELECT curr.cogs AS current_value, prev.cogs AS baseline_value
    FROM curr, prev;
    '''
    df = con.execute(sql).fetchdf()
    con.close()

    if df.empty:
        pytest.skip("No rows returned for COGS validation; skipping")

    curr_sql = float(df.loc[0, "current_value"]) if df.loc[0, "current_value"] is not None else None
    base_sql = float(df.loc[0, "baseline_value"]) if df.loc[0, "baseline_value"] is not None else None

    assert current is not None and baseline is not None, "SA did not return current/baseline for COGS"
    assert curr_sql is not None and base_sql is not None, "SQL returned NULL current/baseline"

    # Compare within a tolerance (few cents after casting)
    assert math.isclose(float(current), curr_sql, rel_tol=0, abs_tol=0.5), (
        f"Current mismatch: SA={current} SQL={curr_sql}"
    )
    assert math.isclose(float(baseline), base_sql, rel_tol=0, abs_tol=0.5), (
        f"Baseline mismatch: SA={baseline} SQL={base_sql}"
    )
