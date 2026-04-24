"""
Seed VA solutions with various lifecycle phases for demo/testing.
Run: .venv/Scripts/python scripts/seed_va_demo_data.py
"""
import httpx
import json
import sys

SUPA_URL = "http://127.0.0.1:54321/rest/v1/value_assurance_solutions"
SUPA_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"

HEADERS = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=minimal",
}

STRAT = {
    "captured_at": "2026-03-15T10:00:00Z",
    "principal_role": "CFO",
    "data_product_id": "lub_star_schema",
    "key_assumptions": [],
    "strategic_rationale": None,
    "principal_priorities": ["Gross Margin", "Revenue Growth"],
    "business_context_name": "lubricants",
    "business_process_domain": "finance",
    "kpi_threshold_at_approval": 0.0,
}

SOLUTIONS = [
    # 1. APPROVED — just approved, no work started
    {
        "id": "a0000001-0001-0001-0001-000000000001",
        "situation_id": "sit-gm-001",
        "kpi_id": "lub_gross_margin_pct",
        "principal_id": "cfo_001",
        "approved_at": "2026-04-10T14:00:00Z",
        "solution_description": "Renegotiate base oil supply contracts with top 3 vendors to lock in Q2 pricing before the seasonal spike. Consolidate orders across divisions for volume leverage.",
        "expected_impact_lower": 1.5,
        "expected_impact_upper": 3.2,
        "measurement_window_days": 90,
        "status": "MEASURING",
        "phase": "APPROVED",
        "inaction_trend": [45.2, 44.8, 44.3, 43.9, 43.4, 42.8, 42.3],
        "expected_trend": [45.2, 45.8, 46.5, 47.1, 47.8],
        "actual_trend": [],
        "actual_trend_dates": [],
        "baseline_kpi_value": 45.2,
        "pre_approval_slope": -0.42,
        "inaction_horizon_months": 6,
        "strategy_snapshot": STRAT,
    },
    # 2. IMPLEMENTING — approved a week ago, being deployed
    {
        "id": "a0000001-0001-0001-0001-000000000002",
        "situation_id": "sit-rev-001",
        "kpi_id": "lub_net_revenue",
        "principal_id": "cfo_001",
        "approved_at": "2026-04-03T09:30:00Z",
        "solution_description": "Launch premium synthetic product bundle for B2B direct accounts. Pilot with top 20 accounts offering 12-month contracts with volume-tiered pricing.",
        "expected_impact_lower": 850000,
        "expected_impact_upper": 2200000,
        "measurement_window_days": 120,
        "status": "MEASURING",
        "phase": "IMPLEMENTING",
        "inaction_trend": [12400000, 12250000, 12100000, 11950000, 11800000, 11650000, 11500000],
        "expected_trend": [12400000, 12700000, 13100000, 13500000, 13900000],
        "actual_trend": [],
        "actual_trend_dates": [],
        "baseline_kpi_value": 12400000,
        "pre_approval_slope": -150000,
        "inaction_horizon_months": 6,
        "strategy_snapshot": STRAT,
    },
    # 3. LIVE — deployed 2 weeks ago, 2 measurements in
    {
        "id": "a0000001-0001-0001-0001-000000000003",
        "situation_id": "sit-pmix-001",
        "kpi_id": "lub_premium_mix_pct",
        "principal_id": "cfo_001",
        "approved_at": "2026-03-15T11:00:00Z",
        "go_live_at": "2026-03-28T08:00:00Z",
        "solution_description": "Reposition shelf space allocation in retail division to prioritize synthetic and premium-blend SKUs. Redeploy co-op marketing budget from conventional to premium products.",
        "expected_impact_lower": 5.0,
        "expected_impact_upper": 12.0,
        "measurement_window_days": 90,
        "status": "MEASURING",
        "phase": "LIVE",
        "inaction_trend": [38.0, 37.2, 36.4, 35.6, 34.8, 34.0, 33.2],
        "expected_trend": [38.0, 41.0, 44.0, 47.0],
        "actual_trend": [38.0, 40.5],
        "actual_trend_dates": ["2026-03-28", "2026-04-07"],
        "baseline_kpi_value": 38.0,
        "pre_approval_slope": -0.8,
        "inaction_horizon_months": 6,
        "strategy_snapshot": STRAT,
    },
    # 4. MEASURING — full measurement window, 4 data points
    {
        "id": "a0000001-0001-0001-0001-000000000004",
        "situation_id": "sit-cogs-001",
        "kpi_id": "lub_cogs",
        "principal_id": "cfo_001",
        "approved_at": "2026-02-10T10:00:00Z",
        "go_live_at": "2026-02-20T08:00:00Z",
        "solution_description": "Consolidate distribution routes and renegotiate freight contracts. Implement just-in-time inventory for top 50 SKUs to reduce warehousing overhead.",
        "expected_impact_lower": -450000,
        "expected_impact_upper": -180000,
        "measurement_window_days": 60,
        "status": "MEASURING",
        "phase": "MEASURING",
        "inaction_trend": [8200000, 8350000, 8500000, 8650000, 8800000, 8950000],
        "expected_trend": [8200000, 8050000, 7900000],
        "actual_trend": [8200000, 8120000, 8010000, 7950000],
        "actual_trend_dates": ["2026-02-20", "2026-03-01", "2026-03-10", "2026-03-20"],
        "baseline_kpi_value": 8200000,
        "pre_approval_slope": 150000,
        "inaction_horizon_months": 5,
        "strategy_snapshot": STRAT,
    },
    # 5. COMPLETE — VALIDATED (success)
    {
        "id": "a0000001-0001-0001-0001-000000000005",
        "situation_id": "sit-ecom-001",
        "kpi_id": "lub_ecommerce_revenue",
        "principal_id": "cfo_001",
        "approved_at": "2026-01-15T09:00:00Z",
        "go_live_at": "2026-01-25T08:00:00Z",
        "completed_at": "2026-03-25T16:00:00Z",
        "solution_description": "Launch direct-to-consumer e-commerce channel with subscription model for recurring oil change customers. Bundle with loyalty program and free shipping over threshold.",
        "expected_impact_lower": 320000,
        "expected_impact_upper": 780000,
        "measurement_window_days": 60,
        "status": "VALIDATED",
        "phase": "COMPLETE",
        "inaction_trend": [1200000, 1150000, 1100000, 1050000, 1000000, 950000],
        "expected_trend": [1200000, 1400000, 1600000],
        "actual_trend": [1200000, 1450000, 1720000],
        "actual_trend_dates": ["2026-01-25", "2026-02-25", "2026-03-25"],
        "baseline_kpi_value": 1200000,
        "pre_approval_slope": -50000,
        "inaction_horizon_months": 5,
        "strategy_snapshot": STRAT,
    },
    # 6. COMPLETE — PARTIAL
    {
        "id": "a0000001-0001-0001-0001-000000000006",
        "situation_id": "sit-sga-001",
        "kpi_id": "lub_sga_expense",
        "principal_id": "cfo_001",
        "approved_at": "2026-01-20T10:00:00Z",
        "go_live_at": "2026-02-01T08:00:00Z",
        "completed_at": "2026-04-01T14:00:00Z",
        "solution_description": "Rationalize trade show spending and redirect 40% of print advertising budget to digital demand-gen channels with measurable ROI attribution.",
        "expected_impact_lower": -280000,
        "expected_impact_upper": -120000,
        "measurement_window_days": 60,
        "status": "PARTIAL",
        "phase": "COMPLETE",
        "inaction_trend": [3800000, 3850000, 3900000, 3950000, 4000000, 4050000],
        "expected_trend": [3800000, 3650000, 3520000],
        "actual_trend": [3800000, 3750000, 3710000],
        "actual_trend_dates": ["2026-02-01", "2026-03-01", "2026-04-01"],
        "baseline_kpi_value": 3800000,
        "pre_approval_slope": 50000,
        "inaction_horizon_months": 5,
        "strategy_snapshot": STRAT,
    },
    # 7. COMPLETE — FAILED
    {
        "id": "a0000001-0001-0001-0001-000000000007",
        "situation_id": "sit-b2b-001",
        "kpi_id": "lub_b2b_revenue",
        "principal_id": "cfo_001",
        "approved_at": "2026-01-10T08:00:00Z",
        "go_live_at": "2026-01-20T08:00:00Z",
        "completed_at": "2026-03-20T15:00:00Z",
        "solution_description": "Aggressive price matching program for B2B direct accounts to counter competitor undercutting. Offer retroactive rebates on Q1 volumes.",
        "expected_impact_lower": 400000,
        "expected_impact_upper": 950000,
        "measurement_window_days": 60,
        "status": "FAILED",
        "phase": "COMPLETE",
        "inaction_trend": [5600000, 5450000, 5300000, 5150000, 5000000, 4850000],
        "expected_trend": [5600000, 5900000, 6200000],
        "actual_trend": [5600000, 5480000, 5350000],
        "actual_trend_dates": ["2026-01-20", "2026-02-20", "2026-03-20"],
        "baseline_kpi_value": 5600000,
        "pre_approval_slope": -150000,
        "inaction_horizon_months": 5,
        "strategy_snapshot": STRAT,
    },
]


def main():
    print(f"Seeding {len(SOLUTIONS)} VA solutions...")
    with httpx.Client() as client:
        for sol in SOLUTIONS:
            resp = client.post(SUPA_URL, headers=HEADERS, json=sol)
            phase = sol["phase"]
            status = sol["status"]
            kpi = sol["kpi_id"]
            if resp.status_code in (200, 201, 204):
                print(f"  OK  {phase:15s} | {status:10s} | {kpi}")
            else:
                print(f"  ERR {phase:15s} | {status:10s} | {kpi} — {resp.status_code}: {resp.text[:120]}")
    print("Done.")


if __name__ == "__main__":
    main()
