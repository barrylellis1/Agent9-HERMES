#!/usr/bin/env python3
"""
Seed Bicycle Business principal profiles into Supabase.

The original YAML principals (Lars, Alex, Priya, Emily) are the Bicycle Business
executives. Composite PK (client_id, id) allows the same role IDs across clients.

Usage:
    python scripts/seed_bicycle_principals.py [--dry-run]

Environment:
    SUPABASE_URL               - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY  - Service role key
"""

import argparse
import os
import sys
from typing import Any, Dict, List

import httpx

CLIENT_ID = "bicycle"

PROFILES: List[Dict[str, Any]] = [
    {
        "id": "cfo_001",
        "client_id": CLIENT_ID,
        "name": "Lars Mikkelsen",
        "first_name": "Lars",
        "last_name": "Mikkelsen",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "department": "Finance",
        "source": "HR Database",
        "description": "CFO responsible for financial performance in EMEA bicycle operations.",
        "responsibilities": [
            "maximize EBIT",
            "manage revenue",
            "control expenses",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_cash_flow_management",
            "finance_budget_vs_actuals",
            "sales_management",
            "financial_reporting",
            "tax_management",
            "pricing_strategy",
        ],
        "default_filters": {
            "Profit Center Hierarchyid": ["Total"],
            "Customer Hierarchyid": ["Total"],
            "Fiscal Year": ["2024", "2025", "2026"],
        },
        "typical_timeframes": ["Monthly", "Quarterly"],
        "principal_groups": ["Executive Leadership", "Finance Committee"],
        "persona_profile": {
            "decision_style": "analytical",
            "risk_tolerance": "low",
            "communication_style": "concise",
            "values": ["accuracy", "compliance", "predictability"],
        },
        "preferences": {"channel": "Slack", "ui": "summary_dashboard"},
        "permissions": ["finance_read", "finance_write"],
        "time_frame": {
            "default_period": "QTD",
            "historical_periods": 4,
            "forward_looking_periods": 2,
        },
        "communication": {
            "detail_level": "high",
            "format_preference": ["visual", "text", "table"],
            "emphasis": ["trends", "anomalies", "forecasts"],
        },
        "metadata": {
            "kpi_line_preference": "bottom_line_first",
            "kpi_altitude_preference": "strategic_first",
        },
    },
    {
        "id": "ceo_001",
        "client_id": CLIENT_ID,
        "name": "Alex Morgan",
        "first_name": "Alex",
        "last_name": "Morgan",
        "title": "Chief Executive Officer",
        "role": "CEO",
        "department": "Executive",
        "source": "HR Database",
        "description": "CEO driving company strategy and performance for the bicycle business.",
        "responsibilities": [
            "set strategic direction",
            "oversee company performance",
            "lead executive team",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "strategy_market_share_analysis",
            "strategy_ebitda_growth_tracking",
        ],
        "default_filters": {
            "Profit Center Hierarchyid": ["Total"],
            "Customer Hierarchyid": ["Total"],
            "Fiscal Year": ["2024", "2025", "2026"],
        },
        "typical_timeframes": ["Quarterly", "Annually"],
        "principal_groups": ["Executive Leadership", "Board of Directors"],
        "persona_profile": {
            "decision_style": "visionary",
            "risk_tolerance": "medium",
            "communication_style": "inspirational",
            "values": ["growth", "innovation", "leadership"],
        },
        "preferences": {"channel": "Email", "ui": "executive_dashboard"},
        "permissions": ["executive_read", "executive_write"],
        "time_frame": {
            "default_period": "YTD",
            "historical_periods": 3,
            "forward_looking_periods": 4,
        },
        "communication": {
            "detail_level": "medium",
            "format_preference": ["visual", "summary"],
            "emphasis": ["trends", "strategic_impact"],
        },
        "metadata": {
            "kpi_line_preference": "top_line_first",
            "kpi_altitude_preference": "strategic_first",
        },
    },
    {
        "id": "coo_001",
        "client_id": CLIENT_ID,
        "name": "Priya Desai",
        "first_name": "Priya",
        "last_name": "Desai",
        "title": "Chief Operating Officer",
        "role": "COO",
        "department": "Operations",
        "source": "HR Database",
        "description": "COO focused on operational excellence and efficiency in bicycle manufacturing and distribution.",
        "responsibilities": [
            "optimize operations",
            "reduce operational costs",
            "improve process efficiency",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "operations_order_to_cash_cycle_optimization",
            "operations_production_cost_management",
            "order_processing",
            "sales_operations",
            "product_management",
        ],
        "default_filters": {
            "Profit Center Name": ["Production", "Mountain Cycles - Production", "Racing Cycles - Production"],
            "Customer Hierarchyid": ["Total"],
        },
        "typical_timeframes": ["Monthly", "Quarterly"],
        "principal_groups": ["Executive Leadership", "Operations Committee"],
        "persona_profile": {
            "decision_style": "pragmatic",
            "risk_tolerance": "medium",
            "communication_style": "direct",
            "values": ["efficiency", "execution", "quality"],
        },
        "preferences": {"channel": "Email", "ui": "operations_dashboard"},
        "permissions": ["operations_read", "operations_write"],
        "time_frame": {
            "default_period": "MTD",
            "historical_periods": 6,
            "forward_looking_periods": 2,
        },
        "communication": {
            "detail_level": "high",
            "format_preference": ["table", "visual"],
            "emphasis": ["variances", "operational_metrics"],
        },
        "metadata": {
            "kpi_line_preference": "bottom_line_first",
            "kpi_altitude_preference": "operational_first",
        },
    },
    {
        "id": "finance_manager_001",
        "client_id": CLIENT_ID,
        "name": "Emily Chen",
        "first_name": "Emily",
        "last_name": "Chen",
        "title": "Finance Manager",
        "role": "Finance Manager",
        "department": "Finance",
        "source": "HR Database",
        "description": "Finance Manager responsible for departmental financial analysis and reporting for the bicycle business.",
        "responsibilities": [
            "manage departmental budget",
            "analyze financial data",
            "prepare financial reports",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_cash_flow_management",
            "finance_budget_vs_actuals",
        ],
        "default_filters": {
            "Profit Center Name": ["Corporate", "Cruise Cycles - Large", "Cruise Cycles - Speciality"],
            "Customer Hierarchyid": ["Total"],
        },
        "typical_timeframes": ["Monthly", "Quarterly"],
        "principal_groups": ["Finance Team", "Budget Committee"],
        "persona_profile": {
            "decision_style": "analytical",
            "risk_tolerance": "low",
            "communication_style": "concise",
            "values": ["accuracy", "timeliness", "efficiency"],
        },
        "preferences": {"channel": "Email", "ui": "finance_dashboard"},
        "permissions": ["finance_read", "finance_write"],
        "time_frame": {
            "default_period": "MTD",
            "historical_periods": 6,
            "forward_looking_periods": 3,
        },
        "communication": {
            "detail_level": "high",
            "format_preference": ["table", "visual", "text"],
            "emphasis": ["variances", "trends", "forecasts"],
        },
        "metadata": {
            "kpi_line_preference": "bottom_line_first",
            "kpi_altitude_preference": "operational_first",
        },
    },
]


def _supabase_headers(service_key: str) -> Dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation,resolution=merge-duplicates",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Bicycle Business principals")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if args.dry_run:
        print("=== DRY RUN ===\n")
        for p in PROFILES:
            print(f"  {p['id']:35s}  {p['name']:20s}  {p['role']}")
        print(f"\nTotal: {len(PROFILES)} bicycle principals")
        return

    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        sys.exit(1)

    headers = _supabase_headers(service_key)
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/principal_profiles"

    with httpx.Client(timeout=30.0) as client:
        print(f"Upserting {len(PROFILES)} bicycle principals...")
        resp = client.post(endpoint, headers=headers, json=PROFILES)
        resp.raise_for_status()
        result = resp.json()
        print(f"  -> {len(result)} principals upserted")

    print("\nDone! Bicycle Business principals seeded.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
