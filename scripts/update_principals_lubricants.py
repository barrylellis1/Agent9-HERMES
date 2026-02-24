#!/usr/bin/env python3
"""
Update principal profiles to Lubricants Business industry personas.

Patches the 4 existing principals in Supabase with generic lubricants-industry
executive names, descriptions, responsibilities, and default filters so they
align with the LubricantsBusiness demo dataset.

Usage:
    python scripts/update_principals_lubricants.py
    python scripts/update_principals_lubricants.py --dry-run

Environment:
    SUPABASE_URL               - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY  - Service role key (admin access)
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

import httpx

# ---------------------------------------------------------------------------
# Principal profile patches
# ---------------------------------------------------------------------------

CLIENT_ID = "lubricants"

PROFILES: List[Dict[str, Any]] = [
    {
        "id": "cfo_001",
        "client_id": CLIENT_ID,
        "name": "Sarah Chen",
        "first_name": "Sarah",
        "last_name": "Chen",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "CFO responsible for financial performance of the Lubricants Business. "
            "Key focus areas: revenue growth across product lines and channels, "
            "gross margin protection against base oil price volatility, "
            "and SG&A cost discipline."
        ),
        "responsibilities": [
            "maximize EBIT",
            "manage revenue across product lines and channels",
            "control COGS and SG&A expenses",
            "protect gross margin against base oil volatility",
            "oversee divisional P&L reporting",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_cash_flow_management",
            "finance_budget_vs_actuals",
            "financial_reporting",
            "pricing_strategy",
        ],
        "default_filters": {
            "Profit Center Name": ["Total"],
            "Customer Segment": ["Total"],
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
        "name": "David Torres",
        "first_name": "David",
        "last_name": "Torres",
        "title": "Chief Executive Officer",
        "role": "CEO",
        "department": "Executive",
        "source": "HR Database",
        "description": (
            "CEO driving Lubricants Business strategy and market growth. "
            "Key focus areas: market share expansion, product innovation "
            "(synthetic and eco-friendly product lines), service center "
            "network growth, and digital channel transformation."
        ),
        "responsibilities": [
            "set strategic direction for lubricants portfolio",
            "oversee company performance across all divisions",
            "lead executive team",
            "drive market share growth in competitive landscape",
            "champion product innovation and sustainability",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "strategy_market_share_analysis",
            "strategy_ebitda_growth_tracking",
        ],
        "default_filters": {
            "Profit Center Name": ["Total"],
            "Customer Segment": ["Total"],
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
        "name": "Rachel Kim",
        "first_name": "Rachel",
        "last_name": "Kim",
        "title": "Chief Operating Officer",
        "role": "COO",
        "department": "Operations",
        "source": "HR Database",
        "description": (
            "COO focused on Lubricants Business operational excellence. "
            "Key focus areas: supply chain optimization (base oil procurement, "
            "blending plant efficiency), distribution network, service center "
            "operations, and fleet customer retention."
        ),
        "responsibilities": [
            "optimize supply chain and blending operations",
            "manage base oil procurement and vendor relationships",
            "improve distribution and freight efficiency",
            "oversee service center network operations",
            "retain and grow commercial fleet accounts",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "operations_order_to_cash_cycle_optimization",
            "operations_production_cost_management",
            "sales_operations",
            "product_management",
        ],
        "default_filters": {
            "Profit Center Name": [
                "Service Centers Division",
                "Commercial & Industrial Division",
            ],
            "Customer Segment": ["Total"],
            "Fiscal Year": ["2024", "2025", "2026"],
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
        "name": "Marcus Webb",
        "first_name": "Marcus",
        "last_name": "Webb",
        "title": "Finance Manager",
        "role": "Finance Manager",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "Finance Manager responsible for Lubricants Business divisional "
            "financial analysis and reporting. Key focus areas: budget tracking "
            "and variance analysis across profit centers, COGS component "
            "monitoring, and SG&A expense governance."
        ),
        "responsibilities": [
            "manage divisional budgets across profit centers",
            "analyze COGS components (base oil, blending, packaging, distribution)",
            "prepare monthly financial reports and variance commentary",
            "track SG&A spending against approved budgets",
            "support CFO with ad-hoc financial analysis",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_cash_flow_management",
            "finance_budget_vs_actuals",
        ],
        "default_filters": {
            "Profit Center Name": [
                "Retail Products Division",
                "Corporate",
            ],
            "Customer Segment": ["Total"],
            "Fiscal Year": ["2024", "2025", "2026"],
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

# Stamp client_id on every profile that doesn't already have one
for _p in PROFILES:
    _p.setdefault("client_id", CLIENT_ID)


def _supabase_headers(service_key: str) -> Dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation,resolution=merge-duplicates",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Update principals for Lubricants demo")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without writing")
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        sys.exit(1)

    base = supabase_url.rstrip("/")
    headers = _supabase_headers(service_key)

    if args.dry_run:
        print("=== DRY RUN — no Supabase writes ===\n")
        for p in PROFILES:
            print(f"  {p['id']:25s}  {p['name']:20s}  {p['role']}")
            print(f"    description: {p['description'][:80]}...")
            print(f"    responsibilities: {p['responsibilities'][:3]}...")
            print(f"    business_process_ids: {p['business_process_ids'][:3]}...")
            print()
        print(f"Total: {len(PROFILES)} profiles to upsert")
        return

    with httpx.Client(timeout=60.0) as client:
        for p in PROFILES:
            pid = p["id"]
            print(f"Upserting principal {pid} ({p['name']})...")

            # Upsert via PostgREST — POST with on-conflict resolution
            resp = client.post(
                f"{base}/rest/v1/principal_profiles",
                headers=headers,
                json=p,
            )
            if resp.status_code in (200, 201):
                print(f"  -> OK (HTTP {resp.status_code})")
            else:
                print(f"  -> FAILED (HTTP {resp.status_code}): {resp.text}", file=sys.stderr)
                sys.exit(1)

    print(f"\nDone! {len(PROFILES)} principal profiles updated for Lubricants demo.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
