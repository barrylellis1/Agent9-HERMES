#!/usr/bin/env python3
"""
Seed Lubricants Business demo data into Supabase.

Registers the Lubricants data product and ~15 KPIs so the Situation Awareness
workflow can run against the BigQuery LubricantsBusiness dataset.

Usage:
    python scripts/demo_seed_lubricants.py [--dry-run]

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
# Supabase helpers
# ---------------------------------------------------------------------------

def _supabase_headers(service_key: str, schema: str = "public") -> Dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Profile": schema,
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
    "id": "dp_lubricants_financials",
    "client_id": "lubricants",
    "name": "Lubricants Business Financial Analytics",
    "domain": "Finance",
    "description": (
        "Lubricants industry financial star schema with revenue, profitability, "
        "and operational KPIs across product lines, customer segments, channels, "
        "and business divisions. Source: BigQuery agent9-465818.LubricantsBusiness"
    ),
    "owner": "Finance Analytics Team",
    "version": "1.0.0",
    "source_system": "bigquery",
    "related_business_processes": [
        "finance_profitability_analysis",
        "finance_revenue_growth",
        "finance_expense_management",
    ],
    "tags": ["finance", "lubricants", "bigquery", "demo", "oil-and-gas"],
    "metadata": {
        "bigquery_project": "agent9-465818",
        "bigquery_dataset": "LubricantsBusiness",
        "bigquery_view": "LubricantsStarSchemaView",
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
# Common dimension definitions for KPIs
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
# KPI definitions
# ---------------------------------------------------------------------------

VIEW = "LubricantsStarSchemaView"
DP_ID = "dp_lubricants_financials"
CLIENT_ID = "lubricants"

KPIS: List[Dict[str, Any]] = [
    # -- Revenue KPIs --
    {
        "id": "lub_net_revenue",
        "name": "Net Revenue",
        "domain": "Finance",
        "description": "Total net revenue across all channels and product lines",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 3.0, "yellow_threshold": -2.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "top-line", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "lub_product_sales_revenue",
        "name": "Product Sales Revenue",
        "domain": "Finance",
        "description": "Revenue from product sales (excludes service revenue)",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth"],
        "sql_query": f"SELECT SUM(amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_category = 'Product Sales' AND version = 'Actual'",
        "filters": {"account_category": "Product Sales", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "product-sales", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "lub_service_revenue",
        "name": "Service Revenue",
        "domain": "Finance",
        "description": "Revenue from service centers (quick lube, dealer service)",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth"],
        "sql_query": f"SELECT SUM(amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_category = 'Service Revenue' AND version = 'Actual'",
        "filters": {"account_category": "Service Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -8.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 2.0, "yellow_threshold": -3.0, "red_threshold": -10.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "service", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CEO", "CFO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    # -- Profitability KPIs --
    {
        "id": "lub_gross_profit",
        "name": "Gross Profit",
        "domain": "Finance",
        "description": "Revenue minus Cost of Goods Sold",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type = 'Revenue' THEN amount WHEN account_type = 'COGS' THEN amount ELSE 0 END) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 2.0, "yellow_threshold": -3.0, "red_threshold": -10.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "profitability", "gross-profit", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "middle", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "lub_gross_margin_pct",
        "name": "Gross Margin %",
        "domain": "Finance",
        "description": "Gross Profit as percentage of Revenue (target: 33-37%)",
        "unit": "%",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT (SUM(CASE WHEN account_type IN ('Revenue','COGS') THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN account_type = 'Revenue' THEN amount ELSE 0 END), 0)) * 100 AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 34.0, "yellow_threshold": 30.0, "red_threshold": 28.0, "inverse_logic": False},
            {"comparison_type": "yoy", "green_threshold": 34.0, "yellow_threshold": 30.0, "red_threshold": 28.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "profitability", "margin", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {"line": "middle", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "lub_operating_income",
        "name": "Operating Income",
        "domain": "Finance",
        "description": "Revenue minus COGS minus SG&A",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type IN ('Revenue','COGS','SGA') THEN amount ELSE 0 END) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "profitability", "operating-income", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "middle", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "lub_ebitda",
        "name": "EBITDA",
        "domain": "Finance",
        "description": "Operating Income plus Depreciation & Amortization",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type IN ('Revenue','COGS','SGA') THEN amount WHEN account_category = 'D&A' THEN -amount ELSE 0 END) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 3.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "profitability", "ebitda", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO"],
        "metadata": {"line": "middle", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    # -- Cost KPIs --
    {
        "id": "lub_cogs",
        "name": "Cost of Goods Sold",
        "domain": "Finance",
        "description": "Total COGS including base oil, blending, packaging, and distribution",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_expense_management", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(-amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_type = 'COGS' AND version = 'Actual'",
        "filters": {"account_type": "COGS", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": -2.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "cost", "cogs", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "Finance Manager"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "lub_base_oil_cost",
        "name": "Base Oil & Additives Cost",
        "domain": "Finance",
        "description": "Raw material costs for base oil and additives (volatile, key risk factor)",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(-amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_category = 'Raw Materials' AND version = 'Actual'",
        "filters": {"account_category": "Raw Materials", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 15.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 2.0, "yellow_threshold": 8.0, "red_threshold": 15.0, "inverse_logic": True},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "cost", "raw-materials", "base-oil", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "lub_sga_expense",
        "name": "SG&A Expense",
        "domain": "Finance",
        "description": "Selling, General & Administrative expenses",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(-amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_type = 'SGA' AND version = 'Actual'",
        "filters": {"account_type": "SGA", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "budget", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "cost", "sga", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "CEO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "lub_distribution_cost",
        "name": "Distribution & Freight Cost",
        "domain": "Finance",
        "description": "Logistics and distribution costs",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(-amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_category = 'Distribution' AND version = 'Actual'",
        "filters": {"account_category": "Distribution", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "cost", "distribution", "logistics", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    # -- Operational KPIs --
    {
        "id": "lub_avg_transaction_value",
        "name": "Average Transaction Value",
        "domain": "Finance",
        "description": "Average revenue per transaction",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth"],
        "sql_query": f"SELECT AVG(amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.0, "yellow_threshold": -3.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "operational", "transaction-value", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "lub_premium_mix_pct",
        "name": "Premium Product Mix %",
        "domain": "Finance",
        "description": "Percentage of revenue from Premium/Full Synthetic products",
        "unit": "%",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth", "finance_profitability_analysis"],
        "sql_query": f"SELECT (SUM(CASE WHEN product_category = 'Premium' THEN amount ELSE 0 END) / NULLIF(SUM(amount), 0)) * 100 AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 40.0, "yellow_threshold": 35.0, "red_threshold": 30.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "product-mix", "premium", "lubricants"],
        "owner_role": "CEO",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "lub_ecommerce_revenue",
        "name": "E-Commerce Revenue",
        "domain": "Finance",
        "description": "Revenue from e-commerce / digital channel",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth"],
        "sql_query": f"SELECT SUM(amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE channel_name = 'E-Commerce' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel_name": "E-Commerce", "account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 15.0, "yellow_threshold": 5.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "ecommerce", "digital", "lubricants"],
        "owner_role": "CEO",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "lub_b2b_revenue",
        "name": "B2B Direct Revenue",
        "domain": "Finance",
        "description": "Revenue from B2B direct sales channel (fleet + industrial customers)",
        "unit": "$",
        "data_product_id": DP_ID,
        "view_name": VIEW,
        "business_process_ids": ["finance_revenue_growth"],
        "sql_query": f"SELECT SUM(amount) AS value FROM `agent9-465818.LubricantsBusiness.{VIEW}` WHERE channel_name = 'B2B Direct Sales' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel_name": "B2B Direct Sales", "account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 3.0, "yellow_threshold": -2.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": DIMENSIONS,
        "tags": ["finance", "revenue", "b2b", "fleet", "industrial", "lubricants"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "CEO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
]

# Stamp client_id on every KPI (avoids repeating in each dict above)
for _kpi in KPIS:
    _kpi.setdefault("client_id", CLIENT_ID)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seed Lubricants demo data into Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Print data without upserting")
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if args.dry_run:
        print("=== DRY RUN ===")
        print(f"\nData Product: {DATA_PRODUCT['id']} - {DATA_PRODUCT['name']}")
        print(f"  domain={DATA_PRODUCT['domain']}, source={DATA_PRODUCT['source_system']}")
        print(f"\nKPIs ({len(KPIS)}):")
        for kpi in KPIS:
            print(f"  {kpi['id']}: {kpi['name']} ({kpi['unit']}) - {len(kpi['thresholds'])} thresholds")
        return

    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
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

    print(f"\nDone! Data product '{DATA_PRODUCT['id']}' with {len(KPIS)} KPIs seeded.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
