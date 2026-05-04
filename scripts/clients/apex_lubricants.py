"""
Apex Lubricants client — Snowflake backend.
Client ID: apex_lubricants
Data product: dp_lubricants_snowflake (Snowflake AGENT9_DEMO.LUBRICANTS.LubricantsStarSchemaView)

BP ID fix applied here:
  KPIs previously seeded with business_process_ids=['finance_revenue_growth']
  corrected to ['finance_revenue_growth_analysis'] to match the canonical taxonomy.
"""

import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.registry.canonical.business_processes import (
    FINANCE_BUSINESS_PROCESSES,
    STRATEGY_BUSINESS_PROCESSES,
    PRICING_BUSINESS_PROCESSES,
)

CLIENT_ID = "apex_lubricants"

CLIENT_META = {
    "id": CLIENT_ID,
    "name": "Apex Lubricants",
    "industry": "Specialty Chemicals & Automotive Aftermarket",
    "data_product_ids": ["dp_lubricants_snowflake"],
}

_DP_ID = "dp_lubricants_snowflake"
_VIEW = "LubricantsStarSchemaView"

DATA_PRODUCT = {
    "id": _DP_ID,
    "client_id": CLIENT_ID,
    "name": "Lubricants Business Financial Analytics (Snowflake)",
    "domain": "Finance",
    "description": (
        "Lubricants industry financial star schema on Snowflake. "
        "Source: Snowflake AGENT9_DEMO.LUBRICANTS.LubricantsStarSchemaView"
    ),
    "owner": "Finance Analytics Team",
    "version": "1.0.0",
    "source_system": "snowflake",
    "related_business_processes": [
        "finance_profitability_analysis",
        "finance_revenue_growth_analysis",
        "finance_expense_management",
    ],
    "tags": ["finance", "lubricants", "snowflake", "demo", "oil-and-gas"],
    "metadata": {
        "snowflake_account": "VSGHWKW-SI38932",
        "snowflake_database": "AGENT9_DEMO",
        "snowflake_schema": "LUBRICANTS",
        "snowflake_warehouse": "AGENT9_WH",
        "snowflake_view": "LubricantsStarSchemaView",
    },
    "tables": {},
    "views": {
        _VIEW: {
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

_DIMS = [
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

KPIS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Revenue KPIs — business_process_ids corrected to finance_revenue_growth_analysis
    # -----------------------------------------------------------------------
    {
        "id": "net_revenue",
        "client_id": CLIENT_ID,
        "name": "Net Revenue",
        "domain": "Finance",
        "description": "Total net revenue across all channels and product lines",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_VIEW} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 3.0, "yellow_threshold": -2.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "top-line", "lubricants", "snowflake"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "product_sales_revenue",
        "client_id": CLIENT_ID,
        "name": "Product Sales Revenue",
        "domain": "Finance",
        "description": "Revenue from product sales (excludes service revenue)",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_VIEW} WHERE account_category = 'Product Sales' AND version = 'Actual'",
        "filters": {"account_category": "Product Sales", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "product-sales", "lubricants", "snowflake"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "service_revenue",
        "client_id": CLIENT_ID,
        "name": "Service Revenue",
        "domain": "Finance",
        "description": "Revenue from service centers (quick lube, dealer service)",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_VIEW} WHERE account_category = 'Service Revenue' AND version = 'Actual'",
        "filters": {"account_category": "Service Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -8.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 2.0, "yellow_threshold": -3.0, "red_threshold": -10.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "service", "lubricants", "snowflake"],
        "owner_role": "COO",
        "stakeholder_roles": ["CEO", "CFO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    # -----------------------------------------------------------------------
    # Profitability / Margin KPIs
    # -----------------------------------------------------------------------
    {
        "id": "gross_profit",
        "client_id": CLIENT_ID,
        "name": "Gross Profit",
        "domain": "Finance",
        "description": "Revenue minus Cost of Goods Sold",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type = 'Revenue' THEN amount WHEN account_type = 'COGS' THEN amount ELSE 0 END) AS value FROM {_VIEW} WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 2.0, "yellow_threshold": -3.0, "red_threshold": -10.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "gross-profit", "lubricants", "snowflake"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "middle", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "gross_margin_pct",
        "client_id": CLIENT_ID,
        "name": "Gross Margin %",
        "domain": "Finance",
        "description": "Gross Profit as percentage of Revenue (target: 33-37%)",
        "unit": "%",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT (SUM(CASE WHEN account_type IN ('Revenue','COGS') THEN amount ELSE 0 END) / NULLIF(SUM(CASE WHEN account_type = 'Revenue' THEN amount ELSE 0 END), 0)) * 100 AS value FROM {_VIEW} WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.05, "yellow_threshold": -0.02, "red_threshold": -0.07, "inverse_logic": False},
            {"comparison_type": "yoy", "green_threshold": 0.05, "yellow_threshold": -0.02, "red_threshold": -0.07, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "margin", "lubricants", "snowflake"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {
            "line": "middle", "altitude": "strategic", "positive_trend_is_good": "true",
            "kpi_type": "ratio",
            "bridge_numerator_sql": f"SELECT SUM(CASE WHEN account_type IN ('Revenue','COGS') THEN amount ELSE 0 END) AS value FROM {_VIEW} WHERE version = 'Actual'",
            "bridge_denominator_sql": f"SELECT SUM(CASE WHEN account_type = 'Revenue' THEN amount ELSE 0 END) AS value FROM {_VIEW} WHERE version = 'Actual'",
        },
    },
    {
        "id": "operating_income",
        "client_id": CLIENT_ID,
        "name": "Operating Income",
        "domain": "Finance",
        "description": "Revenue minus COGS minus SG&A",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type IN ('Revenue','COGS','SGA') THEN amount ELSE 0 END) AS value FROM {_VIEW} WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "operating-income", "lubricants", "snowflake"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "middle", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "ebitda",
        "client_id": CLIENT_ID,
        "name": "EBITDA",
        "domain": "Finance",
        "description": "Operating Income plus Depreciation & Amortization",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type IN ('Revenue','COGS','SGA') THEN amount WHEN account_category = 'D&A' THEN -amount ELSE 0 END) AS value FROM {_VIEW} WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 3.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "ebitda", "lubricants", "snowflake"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO"],
        "metadata": {"line": "middle", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    # -----------------------------------------------------------------------
    # Cost / Expense KPIs
    # -----------------------------------------------------------------------
    {
        "id": "cogs",
        "client_id": CLIENT_ID,
        "name": "Cost of Goods Sold",
        "domain": "Finance",
        "description": "Total COGS including base oil, blending, packaging, and distribution",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(-amount) AS value FROM {_VIEW} WHERE account_type = 'COGS' AND version = 'Actual'",
        "filters": {"account_type": "COGS", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": -2.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "cogs", "lubricants", "snowflake"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "Finance Manager"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "base_oil_cost",
        "client_id": CLIENT_ID,
        "name": "Base Oil & Additives Cost",
        "domain": "Finance",
        "description": "Raw material costs for base oil and additives",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(-amount) AS value FROM {_VIEW} WHERE account_category = 'Raw Materials' AND version = 'Actual'",
        "filters": {"account_category": "Raw Materials", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 15.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 2.0, "yellow_threshold": 8.0, "red_threshold": 15.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "raw-materials", "base-oil", "lubricants", "snowflake"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "sga_expense",
        "client_id": CLIENT_ID,
        "name": "SG&A Expense",
        "domain": "Finance",
        "description": "Selling, General & Administrative expenses",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(-amount) AS value FROM {_VIEW} WHERE account_type = 'SGA' AND version = 'Actual'",
        "filters": {"account_type": "SGA", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "budget", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
            {"comparison_type": "yoy", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "sga", "lubricants", "snowflake"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "CEO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "distribution_cost",
        "client_id": CLIENT_ID,
        "name": "Distribution & Freight Cost",
        "domain": "Finance",
        "description": "Logistics and distribution costs",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(-amount) AS value FROM {_VIEW} WHERE account_category = 'Distribution' AND version = 'Actual'",
        "filters": {"account_category": "Distribution", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "distribution", "logistics", "lubricants", "snowflake"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "middle", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    # -----------------------------------------------------------------------
    # Operational KPIs
    # -----------------------------------------------------------------------
    {
        "id": "avg_transaction_value",
        "client_id": CLIENT_ID,
        "name": "Average Transaction Value",
        "domain": "Finance",
        "description": "Average revenue per transaction",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT AVG(amount) AS value FROM {_VIEW} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 0.0, "yellow_threshold": -3.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "operational", "transaction-value", "lubricants", "snowflake"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "premium_mix_pct",
        "client_id": CLIENT_ID,
        "name": "Premium Product Mix %",
        "domain": "Finance",
        "description": "Percentage of revenue from Premium/Full Synthetic products",
        "unit": "%",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis", "finance_profitability_analysis"],
        "sql_query": f"SELECT (SUM(CASE WHEN product_category = 'Premium' THEN amount ELSE 0 END) / NULLIF(SUM(amount), 0)) * 100 AS value FROM {_VIEW} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "qoq", "green_threshold": 40.0, "yellow_threshold": 35.0, "red_threshold": 30.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "product-mix", "premium", "lubricants", "snowflake"],
        "owner_role": "CEO",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "ecommerce_revenue",
        "client_id": CLIENT_ID,
        "name": "E-Commerce Revenue",
        "domain": "Finance",
        "description": "Revenue from e-commerce / digital channel",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_VIEW} WHERE channel_name = 'E-Commerce' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel_name": "E-Commerce", "account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 15.0, "yellow_threshold": 5.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "ecommerce", "digital", "lubricants", "snowflake"],
        "owner_role": "CEO",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "b2b_revenue",
        "client_id": CLIENT_ID,
        "name": "B2B Direct Revenue",
        "domain": "Finance",
        "description": "Revenue from B2B direct sales channel (fleet + industrial customers)",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_VIEW} WHERE channel_name = 'B2B Direct Sales' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel_name": "B2B Direct Sales", "account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 3.0, "yellow_threshold": -2.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "b2b", "fleet", "industrial", "lubricants", "snowflake"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "CEO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
]

PRINCIPALS: List[Dict[str, Any]] = [
    {
        "id": "cfo_001",
        "client_id": CLIENT_ID,
        "name": "James Whitfield",
        "first_name": "James",
        "last_name": "Whitfield",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "CFO overseeing Apex Lubricants financial performance. "
            "Focus areas: revenue growth across channels, gross margin "
            "protection against base oil volatility, SG&A discipline, "
            "and divisional P&L accountability."
        ),
        "responsibilities": [
            "maximize EBIT across all divisions",
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
        "preferences": {"channel": "Email", "ui": "summary_dashboard"},
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
        "name": "Patricia Navarro",
        "first_name": "Patricia",
        "last_name": "Navarro",
        "title": "Chief Executive Officer",
        "role": "CEO",
        "department": "Executive",
        "source": "HR Database",
        "description": (
            "CEO driving Apex Lubricants strategy and market growth. "
            "Focus areas: market share expansion, premium product mix shift, "
            "e-commerce channel buildout, and operational efficiency."
        ),
        "responsibilities": [
            "set strategic direction for lubricants portfolio",
            "oversee company performance across all divisions",
            "lead executive team",
            "drive market share growth",
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
        "client_id": CLIENT_ID,
        "name": "Michael Okafor",
        "first_name": "Michael",
        "last_name": "Okafor",
        "title": "Chief Operating Officer",
        "role": "COO",
        "department": "Operations",
        "source": "HR Database",
        "description": (
            "COO focused on Apex Lubricants operational excellence. "
            "Focus areas: supply chain optimization, base oil procurement, "
            "distribution network efficiency, service center operations, "
            "and fleet customer retention."
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
        "client_id": CLIENT_ID,
        "name": "Linda Cheng",
        "first_name": "Linda",
        "last_name": "Cheng",
        "title": "Finance Manager",
        "role": "Finance Manager",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "Finance Manager responsible for divisional financial analysis "
            "and reporting at Apex Lubricants. Focus areas: budget tracking, "
            "variance analysis across profit centers, COGS component monitoring, "
            "and SG&A expense governance."
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

# Business processes: Finance + Strategy + Pricing (the core domains for apex_lubricants principals)
BUSINESS_PROCESS_IDS = [
    bp["id"] for bp in FINANCE_BUSINESS_PROCESSES + STRATEGY_BUSINESS_PROCESSES + PRICING_BUSINESS_PROCESSES
]

# Extra BPs referenced by the COO principal that are not in FINANCE/STRATEGY/PRICING canonical lists:
#   - operations_order_to_cash_cycle_optimization  (in OPERATIONS_BUSINESS_PROCESSES, not imported above)
#   - operations_production_cost_management         (not in any canonical list)
#   - sales_operations                              (in SALES_BUSINESS_PROCESSES, not imported above)
# Note: product_management is already in PRICING_BUSINESS_PROCESSES so it is covered above.
EXTRA_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "operations_order_to_cash_cycle_optimization",
        "name": "Order-to-Cash Cycle Optimization",
        "domain": "Operations",
        "display_name": "Operations: Order-to-Cash Cycle Optimization",
        "description": "Optimisation of the end-to-end order fulfilment and payment collection process",
        "owner_role": "COO",
        "stakeholder_roles": ["Sales Manager", "Finance Manager"],
        "tags": ["operations", "order-to-cash", "cycle-time"],
        "metadata": {},
    },
    {
        "id": "operations_production_cost_management",
        "name": "Production Cost Management",
        "domain": "Operations",
        "display_name": "Operations: Production Cost Management",
        "description": "Monitoring and control of manufacturing and blending production costs",
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "Finance Manager"],
        "tags": ["operations", "production", "cost", "manufacturing"],
        "metadata": {},
    },
    {
        "id": "sales_operations",
        "name": "Sales Operations",
        "domain": "Sales",
        "display_name": "Sales: Sales Operations",
        "description": "Sales process efficiency, tooling, and operational support",
        "owner_role": "Sales Manager",
        "stakeholder_roles": ["CFO"],
        "tags": ["sales", "operations", "enablement"],
        "metadata": {},
    },
]

EXTRA_GLOSSARY_TERMS: List[Dict[str, Any]] = []
