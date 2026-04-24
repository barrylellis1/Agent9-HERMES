#!/usr/bin/env python3
"""
Seed SQL Server Lubricants data product and KPIs into Supabase.

Registers dp_lubricants_sqlserver (local Docker SQL Server 2022, agent9_lubricants DB)
with 8 finance KPIs using T-SQL queries against LubricantsStarSchemaView.

Usage:
    python scripts/seed_sqlserver_lubricants.py [--dry-run]

Environment:
    SUPABASE_URL               - Supabase project URL (default: http://localhost:54321)
    SUPABASE_SERVICE_ROLE_KEY  - Service role key (admin access)
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List

import httpx

# ---------------------------------------------------------------------------
# Supabase helpers (same pattern as demo_seed_lubricants.py)
# ---------------------------------------------------------------------------

def _supabase_headers(service_key: str) -> Dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Profile": "public",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }


def _upsert(client: httpx.Client, url: str, headers: Dict[str, str],
            table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    resp = client.post(endpoint, headers=headers, json=rows)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Data Product definition
# ---------------------------------------------------------------------------

DATA_PRODUCT = {
    "id": "dp_lubricants_sqlserver",
    "client_id": "lubricants",
    "name": "Lubricants Business Financial Analytics (SQL Server)",
    "domain": "Finance",
    "description": (
        "Lubricants industry financial star schema in SQL Server. All 6 dimension "
        "and fact tables loaded from BigQuery LubricantsBusiness dataset. Star schema "
        "view LubricantsStarSchemaView built with T-SQL joins — identical 21-column "
        "schema to the BigQuery source view. Used for SQL Server connectivity testing "
        "and to validate the SA\u2192VA pipeline against a SQL Server backend. "
        "Source: agent9_lubricants.dbo (localhost:1433, Docker SQL Server 2022)"
    ),
    "owner": "Finance Analytics Team",
    "version": "1.0.0",
    "source_system": "sqlserver",
    "related_business_processes": [
        "finance_profitability_analysis",
        "finance_revenue_growth",
        "finance_expense_management",
    ],
    "tags": ["finance", "lubricants", "sqlserver", "demo", "oil-and-gas"],
    "metadata": {
        "sqlserver_host": "localhost",
        "sqlserver_port": "1433",
        "sqlserver_database": "agent9_lubricants",
        "sqlserver_schema": "dbo",
        "sqlserver_view": "LubricantsStarSchemaView",
        "connection_note": "Docker SQL Server 2022 container agent9_sqlserver; SA=Agent9Test!2024",
    },
    "tables": {},
    "views": {
        "LubricantsStarSchemaView": {
            "columns": [
                "transaction_id", "fiscal_year", "fiscal_period", "transaction_date",
                "amount", "version", "currency",
                "account_name", "account_type", "account_category", "account_group",
                "product_name", "product_line", "product_category",
                "customer_name", "customer_segment", "customer_region",
                "profit_center_name", "business_unit",
                "channel_name", "channel_type",
            ]
        }
    },
    "reviewed": True,
    "staging": False,
    "language": "EN",
}

# ---------------------------------------------------------------------------
# Common dimension definitions (same across all KPIs)
# ---------------------------------------------------------------------------

DIMENSIONS = [
    {
        "name": "Product Line",
        "field": "product_line",
        "values": [
            "Engine Oils", "Transmission & Drivetrain", "Industrial Lubricants",
            "Greases & Specialty", "Coolants & Antifreeze", "Chemicals & Additives",
        ],
    },
    {
        "name": "Customer Segment",
        "field": "customer_segment",
        "values": [
            "Retail Partners", "Service Centers", "Commercial Fleet",
            "Industrial", "International Distributors",
        ],
    },
    {
        "name": "Channel",
        "field": "channel_name",
        "values": [
            "DIY Retail", "DIFM Service Centers", "B2B Direct Sales",
            "E-Commerce", "International Distribution",
        ],
    },
    {
        "name": "Profit Center",
        "field": "profit_center_name",
        "values": [
            "Retail Products Division", "Service Centers Division",
            "Commercial & Industrial Division", "International Division", "Corporate",
        ],
    },
]

# ---------------------------------------------------------------------------
# KPI definitions — T-SQL queries against LubricantsStarSchemaView
# Note: SQL Server uses CAST(amount AS FLOAT), bracket identifiers [view],
#       and does NOT support BigQuery backtick syntax.
# ---------------------------------------------------------------------------

VIEW = "LubricantsStarSchemaView"
DP_ID = "dp_lubricants_sqlserver"
CLIENT_ID = "lubricants"

KPIS: List[Dict[str, Any]] = [
    # -- Revenue KPIs --
    {
        "id": "ss_lub_net_revenue",
        "name": "Net Revenue",
        "domain": "Finance",
        "description": "Total net revenue across all channels and product lines",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CAST(amount AS FLOAT)) AS value FROM [{VIEW}] WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 3.0, "yellow_threshold": -2.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "top-line", "lubricants", "sqlserver"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "ss_lub_service_revenue",
        "name": "Service Revenue",
        "domain": "Finance",
        "description": "Revenue from service centers (quick lube, dealer service)",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth"],
        "sql_query": f"SELECT SUM(CAST(amount AS FLOAT)) AS value FROM [{VIEW}] WHERE account_category = 'Service Revenue' AND version = 'Actual'",
        "filters": {"account_category": "Service Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -8.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 2.0, "yellow_threshold": -3.0, "red_threshold": -10.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "service", "lubricants", "sqlserver"],
        "owner_role": "COO",
        "stakeholder_roles": ["CEO", "CFO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    # -- Profitability KPIs --
    {
        "id": "ss_lub_gross_margin_pct",
        "name": "Gross Margin %",
        "domain": "Finance",
        "description": "Gross Profit as percentage of Revenue (target: 33-37%)",
        "unit": "%",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": (
            f"SELECT (SUM(CASE WHEN account_type IN ('Revenue','COGS') THEN CAST(amount AS FLOAT) ELSE 0 END) "
            f"/ NULLIF(SUM(CASE WHEN account_type = 'Revenue' THEN CAST(amount AS FLOAT) ELSE 0 END), 0)) * 100 AS value "
            f"FROM [{VIEW}] WHERE version = 'Actual'"
        ),
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.05, "yellow_threshold": -0.02, "red_threshold": -0.07, "inverse_logic": False},
            {"comparison_type": "yoy", "green_threshold": 0.05, "yellow_threshold": -0.02, "red_threshold": -0.07, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "profitability", "margin", "lubricants", "sqlserver"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {
            "line": "middle",
            "altitude": "strategic",
            "positive_trend_is_good": "true",
            "kpi_type": "ratio",
        },
    },
    # -- Cost KPIs --
    {
        "id": "ss_lub_cogs",
        "name": "Cost of Goods Sold",
        "domain": "Finance",
        "description": "Total COGS including base oil, blending, packaging, and distribution",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_expense_management", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(-CAST(amount AS FLOAT)) AS value FROM [{VIEW}] WHERE account_type = 'COGS' AND version = 'Actual'",
        "filters": {"account_type": "COGS", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": -2.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "cost", "cogs", "lubricants", "sqlserver"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "Finance Manager"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "ss_lub_base_oil_cost",
        "name": "Base Oil & Additives Cost",
        "domain": "Finance",
        "description": "Raw material costs for base oil and additives (volatile, key risk factor)",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(-CAST(amount AS FLOAT)) AS value FROM [{VIEW}] WHERE account_category = 'Raw Materials' AND version = 'Actual'",
        "filters": {"account_category": "Raw Materials", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 15.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 2.0, "yellow_threshold": 8.0, "red_threshold": 15.0, "inverse_logic": True},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "cost", "raw-materials", "base-oil", "lubricants", "sqlserver"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "ss_lub_sga_expense",
        "name": "SG&A Expense",
        "domain": "Finance",
        "description": "Selling, General & Administrative expenses",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(-CAST(amount AS FLOAT)) AS value FROM [{VIEW}] WHERE account_type = 'SGA' AND version = 'Actual'",
        "filters": {"account_type": "SGA", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "budget", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "cost", "sga", "lubricants", "sqlserver"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "CEO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    # -- Channel KPIs --
    {
        "id": "ss_lub_ecommerce_revenue",
        "name": "E-Commerce Revenue",
        "domain": "Finance",
        "description": "Revenue from e-commerce / digital channel",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth"],
        "sql_query": f"SELECT SUM(CAST(amount AS FLOAT)) AS value FROM [{VIEW}] WHERE channel_name = 'E-Commerce' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel_name": "E-Commerce", "account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 15.0, "yellow_threshold": 5.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "ecommerce", "digital", "lubricants", "sqlserver"],
        "owner_role": "CEO",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "ss_lub_b2b_revenue",
        "name": "B2B Direct Revenue",
        "domain": "Finance",
        "description": "Revenue from B2B direct sales channel (fleet + industrial customers)",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth"],
        "sql_query": f"SELECT SUM(CAST(amount AS FLOAT)) AS value FROM [{VIEW}] WHERE channel_name = 'B2B Direct Sales' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel_name": "B2B Direct Sales", "account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 3.0, "yellow_threshold": -2.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "b2b", "fleet", "industrial", "lubricants", "sqlserver"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "CEO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
]

# Stamp client_id on every KPI
for _kpi in KPIS:
    _kpi.setdefault("client_id", CLIENT_ID)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Seed SQL Server Lubricants data product and KPIs into Supabase"
    )
    parser.add_argument("--dry-run", action="store_true", help="Print data without upserting")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN ===")
        print(f"\nData Product: {DATA_PRODUCT['id']} — {DATA_PRODUCT['name']}")
        print(f"  source_system={DATA_PRODUCT['source_system']}, domain={DATA_PRODUCT['domain']}")
        print(f"\nKPIs ({len(KPIS)}):")
        for kpi in KPIS:
            print(f"  {kpi['id']}: {kpi['name']} ({kpi['unit']}) — {len(kpi['thresholds'])} thresholds")
            print(f"    SQL: {kpi['sql_query'][:90]}...")
        return

    supabase_url = os.getenv("SUPABASE_URL", "http://localhost:54321")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not service_key:
        print("ERROR: SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        sys.exit(1)

    headers = _supabase_headers(service_key)

    with httpx.Client(timeout=30.0) as client:
        # 1. Upsert data product
        print(f"Upserting data product: {DATA_PRODUCT['id']}...")
        result = _upsert(client, supabase_url, headers, "data_products", [DATA_PRODUCT])
        print(f"  -> Data product upserted ({len(result)} row)")

        # 2. Upsert KPIs
        print(f"Upserting {len(KPIS)} KPIs...")
        result = _upsert(client, supabase_url, headers, "kpis", KPIS)
        print(f"  -> {len(result)} KPIs upserted")

    print(f"\nDone! '{DATA_PRODUCT['id']}' registered with {len(KPIS)} KPIs.")
    print("\nNext: run SA assessment against this data product:")
    print("  .venv/Scripts/python run_enterprise_assessment.py --principal cfo_001 --data-product dp_lubricants_sqlserver")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
