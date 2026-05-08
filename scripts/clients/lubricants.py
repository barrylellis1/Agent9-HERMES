"""
Lubricants Business client — BigQuery backend.
Client ID: lubricants
Data product: dp_lubricants_financials (BigQuery LubricantsBusiness dataset)

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

CLIENT_ID = "lubricants"

CLIENT_META = {
    "id": CLIENT_ID,
    "name": "Lubricants Business",
    "industry": "Oil & Gas / Specialty Chemicals",
    "data_product_ids": ["dp_lubricants_financials"],
}

DATA_PRODUCT = {
    "id": "dp_lubricants_financials",
    "client_id": CLIENT_ID,
    "name": "Lubricants Business Financial Analytics",
    "domain": "Finance",
    "source_system": "bigquery",
    "description": (
        "BigQuery dataset covering the full P&L for the Lubricants Business division. "
        "Includes revenue by channel and product line, COGS by component, and SG&A."
    ),
    "owner": "Finance",
    "owner_role": "CFO",
    "metadata": {
        "source_system": "bigquery",
        "bigquery_project": "agent9-465818",
        "bigquery_dataset": "LubricantsBusiness",
    },
}

_VIEW = "LubricantsStarSchemaView"
_BQ_PREFIX = f"`agent9-465818.LubricantsBusiness.{_VIEW}`"

_DIMS = [
    {"name": "Profit Center", "field": "profit_center_name"},
    {"name": "Customer Segment", "field": "customer_segment"},
    {"name": "Product Line", "field": "product_line"},
    {"name": "Channel", "field": "channel"},
    {"name": "Region", "field": "region"},
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
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
            {"comparison_type": "qoq", "green_threshold": 3.0, "yellow_threshold": -2.0, "red_threshold": -8.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "top-line", "lubricants"],
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
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_category = 'Product Sales' AND version = 'Actual'",
        "filters": {"account_category": "Product Sales", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "product-sales", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "service_revenue",
        "client_id": CLIENT_ID,
        "name": "Service Revenue",
        "domain": "Finance",
        "description": "Revenue from service contracts and technical services",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_category = 'Service Revenue' AND version = 'Actual'",
        "filters": {"account_category": "Service Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 8.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "services", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["COO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "b2b_revenue",
        "client_id": CLIENT_ID,
        "name": "B2B Revenue",
        "domain": "Finance",
        "description": "Revenue from B2B channel customers",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE channel_name = 'B2B' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel": "B2B", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "b2b", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "ecommerce_revenue",
        "client_id": CLIENT_ID,
        "name": "E-Commerce Revenue",
        "domain": "Finance",
        "description": "Revenue from digital / e-commerce channel",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE channel_name = 'E-Commerce' AND account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"channel": "E-Commerce", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 15.0, "yellow_threshold": 5.0, "red_threshold": 0.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "ecommerce", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["COO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "avg_transaction_value",
        "client_id": CLIENT_ID,
        "name": "Average Transaction Value",
        "domain": "Finance",
        "description": "Average revenue per transaction across all channels",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": f"SELECT AVG(amount) AS value FROM {_BQ_PREFIX} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 3.0, "yellow_threshold": 0.0, "red_threshold": -3.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "transaction-value", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "top", "altitude": "operational", "positive_trend_is_good": "true"},
    },
    {
        "id": "premium_mix_pct",
        "client_id": CLIENT_ID,
        "name": "Premium Product Mix %",
        "domain": "Finance",
        "description": "Percentage of revenue from premium product lines",
        "unit": "%",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis", "finance_profitability_analysis"],
        "sql_query": f"SELECT ROUND(100.0 * SUM(CASE WHEN product_category = 'Premium' THEN amount ELSE 0 END) / NULLIF(SUM(amount), 0), 2) AS value FROM {_BQ_PREFIX} WHERE account_type = 'Revenue' AND version = 'Actual'",
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 2.0, "yellow_threshold": 0.0, "red_threshold": -2.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "premium-mix", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    # -----------------------------------------------------------------------
    # Profitability / Margin KPIs
    # -----------------------------------------------------------------------
    {
        "id": "gross_profit",
        "client_id": CLIENT_ID,
        "name": "Gross Profit",
        "domain": "Finance",
        "description": "Net revenue minus cost of goods sold",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type = 'Revenue' THEN amount WHEN account_type = 'COGS' THEN -amount ELSE 0 END) AS value FROM {_BQ_PREFIX} WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "gross-profit", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "gross_margin_pct",
        "client_id": CLIENT_ID,
        "name": "Gross Margin %",
        "domain": "Finance",
        "description": "Gross profit as a percentage of net revenue",
        "unit": "%",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT ROUND(100.0 * SUM(CASE WHEN account_type = 'Revenue' THEN amount WHEN account_type = 'COGS' THEN -amount ELSE 0 END) / NULLIF(SUM(CASE WHEN account_type = 'Revenue' THEN amount ELSE 0 END), 0), 2) AS value FROM {_BQ_PREFIX} WHERE version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 1.0, "yellow_threshold": 0.0, "red_threshold": -1.5, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "margin", "gross-margin", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "operating_income",
        "client_id": CLIENT_ID,
        "name": "Operating Income",
        "domain": "Finance",
        "description": "Gross profit minus SG&A and other operating expenses (EBIT)",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type IN ('Revenue') THEN amount ELSE -amount END) AS value FROM {_BQ_PREFIX} WHERE account_type IN ('Revenue', 'COGS', 'SGA') AND version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "operating-income", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "ebitda",
        "client_id": CLIENT_ID,
        "name": "EBITDA",
        "domain": "Finance",
        "description": "Earnings before interest, taxes, depreciation, and amortisation",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(CASE WHEN account_type IN ('Revenue') THEN amount ELSE -amount END) AS value FROM {_BQ_PREFIX} WHERE account_type IN ('Revenue', 'COGS', 'SGA', 'DA') AND version = 'Actual'",
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "ebitda", "lubricants"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Board"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    # -----------------------------------------------------------------------
    # Cost / Expense KPIs
    # -----------------------------------------------------------------------
    {
        "id": "cogs",
        "client_id": CLIENT_ID,
        "name": "Cost of Goods Sold",
        "domain": "Finance",
        "description": "Total direct cost of producing and delivering products",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management", "finance_profitability_analysis"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_type = 'COGS' AND version = 'Actual'",
        "filters": {"account_type": "COGS", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -3.0, "yellow_threshold": 3.0, "red_threshold": 8.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "cogs", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "base_oil_cost",
        "client_id": CLIENT_ID,
        "name": "Base Oil Cost",
        "domain": "Finance",
        "description": "Cost of base oil — primary raw material input for lubricants",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_category = 'Base Oil' AND version = 'Actual'",
        "filters": {"account_category": "Base Oil", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -5.0, "yellow_threshold": 5.0, "red_threshold": 15.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "raw-materials", "base-oil", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "distribution_cost",
        "client_id": CLIENT_ID,
        "name": "Distribution Cost",
        "domain": "Finance",
        "description": "Total logistics and distribution costs for product delivery",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_category = 'Distribution' AND version = 'Actual'",
        "filters": {"account_category": "Distribution", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -3.0, "yellow_threshold": 3.0, "red_threshold": 8.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "distribution", "logistics", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "sga_expense",
        "client_id": CLIENT_ID,
        "name": "SG&A Expense",
        "domain": "Finance",
        "description": "Selling, general and administrative expenses",
        "unit": "$",
        "data_product_id": "dp_lubricants_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": f"SELECT SUM(amount) AS value FROM {_BQ_PREFIX} WHERE account_type = 'SGA' AND version = 'Actual'",
        "filters": {"account_type": "SGA", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -2.0, "yellow_threshold": 3.0, "red_threshold": 8.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "expense", "sga", "opex", "lubricants"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
]


PRINCIPALS: List[Dict[str, Any]] = [
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
        # Corrected: use finance_revenue_growth_analysis (matches canonical BP + KPI BP IDs)
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
        "metadata": {
            "kpi_line_preference": "bottom_line_first",
            "kpi_altitude_preference": "strategic_first",
        },
    },
    {
        "id": "ceo_001",
        "client_id": CLIENT_ID,
        "name": "David Torres",
        "first_name": "David",
        "last_name": "Torres",
        "title": "Chief Executive Officer",
        "role": "CEO",
        "department": "Executive",
        "source": "HR Database",
        "description": "CEO driving Lubricants Business strategy and market growth.",
        "responsibilities": [
            "set strategic direction for lubricants portfolio",
            "oversee company performance across all divisions",
            "drive market share growth",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "strategy_market_share_analysis",
            "strategy_ebitda_growth_tracking",
        ],
        "default_filters": {"Fiscal Year": ["2024", "2025", "2026"]},
        "typical_timeframes": ["Quarterly", "Annually"],
        "persona_profile": {"decision_style": "strategic", "risk_tolerance": "moderate", "communication_style": "executive"},
        "metadata": {"kpi_line_preference": "top_line_first", "kpi_altitude_preference": "strategic_first"},
    },
    {
        "id": "coo_001",
        "client_id": CLIENT_ID,
        "name": "Rachel Kim",
        "first_name": "Rachel",
        "last_name": "Kim",
        "title": "Chief Operating Officer",
        "role": "COO",
        "department": "Operations",
        "source": "HR Database",
        "description": "COO overseeing production, supply chain, and operational efficiency.",
        "responsibilities": [
            "manage manufacturing and supply chain operations",
            "drive COGS reduction",
            "oversee distribution network",
        ],
        "business_process_ids": [
            "finance_expense_management",
            "finance_profitability_analysis",
            "operations_inventory_turnover_analysis",
            "supply_chain_logistics_efficiency",
        ],
        "default_filters": {"Fiscal Year": ["2024", "2025", "2026"]},
        "typical_timeframes": ["Monthly", "Quarterly"],
        "persona_profile": {"decision_style": "operational", "risk_tolerance": "low", "communication_style": "detailed"},
        "metadata": {"kpi_line_preference": "bottom_line_first", "kpi_altitude_preference": "operational_first"},
    },
    {
        "id": "finance_001",
        "client_id": CLIENT_ID,
        "name": "Marcus Webb",
        "first_name": "Marcus",
        "last_name": "Webb",
        "title": "Finance Manager",
        "role": "Finance Manager",
        "department": "Finance",
        "source": "HR Database",
        "description": "Finance Manager supporting P&L analysis and budget management.",
        "responsibilities": [
            "financial reporting and variance analysis",
            "budget management",
            "cost control",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_budget_vs_actuals",
            "finance_cash_flow_management",
            "financial_reporting",
        ],
        "default_filters": {"Fiscal Year": ["2024", "2025", "2026"]},
        "typical_timeframes": ["Monthly"],
        "persona_profile": {"decision_style": "analytical", "risk_tolerance": "low", "communication_style": "detailed"},
        "metadata": {"kpi_line_preference": "balanced", "kpi_altitude_preference": "operational_first"},
    },
]

# Business processes: Finance + Strategy + Pricing (the domains lubricants principals reference)
BUSINESS_PROCESS_IDS = [
    bp["id"] for bp in FINANCE_BUSINESS_PROCESSES + STRATEGY_BUSINESS_PROCESSES + PRICING_BUSINESS_PROCESSES
]

EXTRA_BUSINESS_PROCESSES: List[Dict[str, Any]] = []
EXTRA_GLOSSARY_TERMS: List[Dict[str, Any]] = []
