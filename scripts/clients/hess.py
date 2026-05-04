"""
Hess Corporation client — SQL Server backend.
Client ID: hess
Data product: dp_hess_financials (SQL Server agent9_hess database)

Hess Corporation is a major independent E&P oil and gas company. KPIs cover
upstream revenue, production costs, capital expenditure, and operating metrics
sourced from the HessStarSchemaView in the agent9_hess SQL Server database.
"""

import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.registry.canonical.business_processes import (
    FINANCE_BUSINESS_PROCESSES,
    STRATEGY_BUSINESS_PROCESSES,
)

CLIENT_ID = "hess"

CLIENT_META = {
    "id": CLIENT_ID,
    "name": "Hess Corporation",
    "industry": "Oil & Gas — Exploration & Production",
    "data_product_ids": ["dp_hess_financials"],
}

DATA_PRODUCT = {
    "id": "dp_hess_financials",
    "client_id": CLIENT_ID,
    "name": "Hess Corporation Financial Analytics",
    "domain": "Finance",
    "source_system": "sqlserver",
    "description": (
        "Financial star schema for Hess Corporation E&P operations. "
        "Covers upstream revenue, production costs, capital expenditure, and operating metrics. "
        "Source: SQL Server agent9_hess database."
    ),
    "owner": "Finance",
    "owner_role": "CFO",
    "version": "1.0.0",
    "related_business_processes": [
        "finance_revenue_growth_analysis",
        "finance_profitability_analysis",
        "finance_expense_management",
        "finance_cash_flow_management",
    ],
    "tags": ["finance", "hess", "sqlserver", "oil-gas", "ep"],
    "metadata": {
        "source_system": "sqlserver",
        "sqlserver_host": "localhost",
        "sqlserver_port": "1433",
        "sqlserver_database": "agent9_hess",
        "sqlserver_schema": "dbo",
        "sqlserver_view": "HessStarSchemaView",
    },
    "tables": {},
    "views": {
        "HessStarSchemaView": {
            "columns": [
                "transaction_id", "fiscal_year", "fiscal_period", "transaction_date",
                "amount", "version", "currency",
                "account_name", "account_type", "account_category",
                "segment_name", "basin_name", "asset_name",
                "country", "region", "business_unit",
            ]
        }
    },
    "reviewed": True,
    "staging": False,
    "language": "EN",
}

_VIEW = "HessStarSchemaView"
_SS_PREFIX = "[dbo].[HessStarSchemaView]"

_DIMS = [
    {"name": "Segment", "field": "segment_name"},
    {"name": "Basin", "field": "basin_name"},
    {"name": "Country", "field": "country"},
    {"name": "Asset", "field": "asset_name"},
    {"name": "Business Unit", "field": "business_unit"},
]

KPIS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------------
    # Revenue KPIs
    # -----------------------------------------------------------------------
    {
        "id": "upstream_revenue",
        "client_id": CLIENT_ID,
        "name": "Upstream Revenue",
        "domain": "Finance",
        "description": "Total upstream revenue from E&P operations across all basins and assets",
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
        ),
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "upstream", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "production_revenue",
        "client_id": CLIENT_ID,
        "name": "Production Revenue",
        "domain": "Finance",
        "description": "Revenue from E&P segment production activities (oil, gas, and NGL sales)",
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [segment_name] = 'E&P' AND [account_type] = 'Revenue' AND [version] = 'Actual'"
        ),
        "filters": {"segment_name": "E&P", "account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "production", "ep", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "midstream_revenue",
        "client_id": CLIENT_ID,
        "name": "Midstream Revenue",
        "domain": "Finance",
        "description": "Revenue from Midstream segment operations (gathering, processing, transportation)",
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [segment_name] = 'Midstream' AND [account_type] = 'Revenue' AND [version] = 'Actual'"
        ),
        "filters": {"segment_name": "Midstream", "account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "midstream", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO"],
        "metadata": {"line": "top", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "total_revenue",
        "client_id": CLIENT_ID,
        "name": "Total Revenue",
        "domain": "Finance",
        "description": "Total consolidated revenue across all segments and business units",
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_revenue_growth_analysis", "finance_profitability_analysis"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
        ),
        "filters": {"account_type": "Revenue", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "revenue", "total", "consolidated", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
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
        "description": (
            "Total revenue minus cost of goods sold. "
            "Cost amounts are stored as positive values and subtracted to derive gross profit."
        ),
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": (
            f"SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] "
            f"WHEN [account_type] = 'COGS' THEN -[amount] ELSE 0 END) AS value "
            f"FROM {_SS_PREFIX} WHERE [version] = 'Actual'"
        ),
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "gross-profit", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "gross_margin_pct",
        "client_id": CLIENT_ID,
        "name": "Gross Margin %",
        "domain": "Finance",
        "description": "Gross profit as a percentage of total revenue",
        "unit": "%",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": (
            f"SELECT ROUND(100.0 * "
            f"SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] WHEN [account_type] = 'COGS' THEN -[amount] ELSE 0 END) "
            f"/ NULLIF(SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE 0 END), 0), 2) AS value "
            f"FROM {_SS_PREFIX} WHERE [version] = 'Actual'"
        ),
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 1.0, "yellow_threshold": 0.0, "red_threshold": -1.5, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "margin", "gross-margin", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "operating_income",
        "client_id": CLIENT_ID,
        "name": "Operating Income",
        "domain": "Finance",
        "description": "Revenue minus COGS and SG&A expenses (EBIT proxy for E&P operations)",
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": (
            f"SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE -[amount] END) AS value "
            f"FROM {_SS_PREFIX} "
            f"WHERE [account_type] IN ('Revenue', 'COGS', 'SGA') AND [version] = 'Actual'"
        ),
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "operating-income", "ebit", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "ebitda",
        "client_id": CLIENT_ID,
        "name": "EBITDA",
        "domain": "Finance",
        "description": (
            "Earnings before interest, taxes, depreciation, and amortisation. "
            "Operating income plus depreciation and amortisation charges."
        ),
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis", "strategy_ebitda_growth_tracking"],
        "sql_query": (
            f"SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE -[amount] END) AS value "
            f"FROM {_SS_PREFIX} "
            f"WHERE [account_type] IN ('Revenue', 'COGS', 'SGA', 'DA') AND [version] = 'Actual'"
        ),
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "profitability", "ebitda", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Board"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    # -----------------------------------------------------------------------
    # Cost / Expense KPIs
    # -----------------------------------------------------------------------
    {
        "id": "lifting_cost",
        "client_id": CLIENT_ID,
        "name": "Lifting Cost",
        "domain": "Finance",
        "description": (
            "Production operating expenses (lifting costs) — the per-barrel cost to extract "
            "and process oil and gas from Hess-operated assets. Lower is better."
        ),
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management", "operations_production_cost_management"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [account_category] = 'Lifting Costs' AND [version] = 'Actual'"
        ),
        "filters": {"account_category": "Lifting Costs", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -3.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "lifting-cost", "production-opex", "hess"],
        "owner_role": "COO",
        "stakeholder_roles": ["CFO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "exploration_expense",
        "client_id": CLIENT_ID,
        "name": "Exploration Expense",
        "domain": "Finance",
        "description": (
            "Costs associated with exploration activities including seismic surveys, "
            "exploratory well drilling, and dry hole write-offs. Lower is better."
        ),
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [account_category] = 'Exploration' AND [version] = 'Actual'"
        ),
        "filters": {"account_category": "Exploration", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -3.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cost", "exploration", "ep", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    {
        "id": "capital_expenditure",
        "client_id": CLIENT_ID,
        "name": "Capital Expenditure",
        "domain": "Finance",
        "description": (
            "Total CapEx invested in development drilling, facilities, and asset acquisitions. "
            "Tracked against approved capital budgets. Lower vs. budget is better."
        ),
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management", "finance_cash_flow_management"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [account_type] = 'CapEx' AND [version] = 'Actual'"
        ),
        "filters": {"account_type": "CapEx", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -3.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "capex", "investment", "development", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "COO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "false"},
    },
    {
        "id": "sga_expense",
        "client_id": CLIENT_ID,
        "name": "SG&A Expense",
        "domain": "Finance",
        "description": "Selling, general and administrative expenses. Lower is better.",
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [account_type] = 'SGA' AND [version] = 'Actual'"
        ),
        "filters": {"account_type": "SGA", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": -3.0, "yellow_threshold": 5.0, "red_threshold": 10.0, "inverse_logic": True},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "expense", "sga", "opex", "hess"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {"line": "bottom", "altitude": "operational", "positive_trend_is_good": "false"},
    },
    # -----------------------------------------------------------------------
    # Cash Flow KPIs
    # -----------------------------------------------------------------------
    {
        "id": "operating_cash_flow",
        "client_id": CLIENT_ID,
        "name": "Operating Cash Flow",
        "domain": "Finance",
        "description": "Net cash generated from core E&P operating activities",
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_cash_flow_management"],
        "sql_query": (
            f"SELECT SUM([amount]) AS value FROM {_SS_PREFIX} "
            f"WHERE [account_type] = 'OperatingCF' AND [version] = 'Actual'"
        ),
        "filters": {"account_type": "OperatingCF", "version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cash-flow", "operating", "liquidity", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "free_cash_flow",
        "client_id": CLIENT_ID,
        "name": "Free Cash Flow",
        "domain": "Finance",
        "description": (
            "Operating cash flow minus capital expenditure. "
            "Key metric for Hess's ability to fund dividends, debt repayment, and returns to shareholders."
        ),
        "unit": "$",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_cash_flow_management", "strategy_ebitda_growth_tracking"],
        "sql_query": (
            f"SELECT SUM(CASE WHEN [account_type] = 'OperatingCF' THEN [amount] "
            f"WHEN [account_type] = 'CapEx' THEN -[amount] ELSE 0 END) AS value "
            f"FROM {_SS_PREFIX} WHERE [account_type] IN ('OperatingCF', 'CapEx') AND [version] = 'Actual'"
        ),
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "cash-flow", "free-cash-flow", "fcf", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Board", "Finance Manager"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
    {
        "id": "return_on_capital",
        "client_id": CLIENT_ID,
        "name": "Return on Capital Employed",
        "domain": "Finance",
        "description": (
            "ROCE proxy: Operating Income as a percentage of capital employed "
            "(approximated as Revenue × 0.6 as a proxy for the asset base). "
            "Measures how efficiently Hess generates profit from deployed capital."
        ),
        "unit": "%",
        "data_product_id": "dp_hess_financials",
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis", "strategy_capital_allocation_efficiency"],
        "sql_query": (
            f"SELECT ROUND(100.0 * "
            f"SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE -[amount] END) "
            f"/ NULLIF(SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE 0 END) * 0.6, 0), 2) AS value "
            f"FROM {_SS_PREFIX} "
            f"WHERE [account_type] IN ('Revenue', 'COGS', 'SGA') AND [version] = 'Actual'"
        ),
        "filters": {"version": "Actual"},
        "thresholds": [
            {"comparison_type": "yoy", "green_threshold": 5.0, "yellow_threshold": 0.0, "red_threshold": -5.0, "inverse_logic": False},
        ],
        "dimensions": _DIMS,
        "tags": ["finance", "roce", "return-on-capital", "efficiency", "hess"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Board"],
        "metadata": {"line": "bottom", "altitude": "strategic", "positive_trend_is_good": "true"},
    },
]


PRINCIPALS: List[Dict[str, Any]] = [
    {
        "id": "cfo_001",
        "client_id": CLIENT_ID,
        "name": "John Rielly",
        "first_name": "John",
        "last_name": "Rielly",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "CFO responsible for the financial performance of Hess Corporation. "
            "Key focus areas: E&P revenue growth, gross margin protection against commodity price cycles, "
            "capital discipline, and cash flow generation to support shareholder returns."
        ),
        "responsibilities": [
            "oversee consolidated P&L and balance sheet",
            "manage investor relations and earnings guidance",
            "drive capital allocation discipline across E&P portfolio",
            "protect operating margins against oil price volatility",
            "ensure free cash flow generation targets are met",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_cash_flow_management",
            "finance_budget_vs_actuals",
            "financial_reporting",
        ],
        "default_filters": {
            "Segment": ["Total"],
            "Fiscal Year": ["2024", "2025", "2026"],
        },
        "typical_timeframes": ["Monthly", "Quarterly"],
        "principal_groups": ["Executive Leadership", "Finance Committee"],
        "persona_profile": {
            "decision_style": "analytical",
            "risk_tolerance": "low",
            "communication_style": "concise",
            "values": ["accuracy", "compliance", "capital-discipline"],
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
        "name": "John Hess",
        "first_name": "John",
        "last_name": "Hess",
        "title": "Chief Executive Officer",
        "role": "CEO",
        "department": "Executive",
        "source": "HR Database",
        "description": (
            "CEO of Hess Corporation, responsible for strategic direction and enterprise performance. "
            "Focused on growing the Guyana and Bakken asset base, EBITDA expansion, and long-term "
            "shareholder value creation."
        ),
        "responsibilities": [
            "set strategic direction for E&P portfolio",
            "oversee enterprise-wide financial performance",
            "lead Guyana and Bakken growth strategy",
            "drive EBITDA growth and capital returns",
            "represent Hess to investors and board",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "strategy_ebitda_growth_tracking",
            "strategy_market_share_analysis",
            "strategy_capital_allocation_efficiency",
        ],
        "default_filters": {
            "Fiscal Year": ["2024", "2025", "2026"],
        },
        "typical_timeframes": ["Quarterly", "Annually"],
        "principal_groups": ["Executive Leadership", "Board"],
        "persona_profile": {
            "decision_style": "strategic",
            "risk_tolerance": "moderate",
            "communication_style": "executive",
            "values": ["growth", "returns", "sustainability"],
        },
        "preferences": {"channel": "Email", "ui": "summary_dashboard"},
        "permissions": ["finance_read"],
        "metadata": {
            "kpi_line_preference": "top_line_first",
            "kpi_altitude_preference": "strategic_first",
        },
    },
    {
        "id": "coo_001",
        "client_id": CLIENT_ID,
        "name": "Greg Hill",
        "first_name": "Greg",
        "last_name": "Hill",
        "title": "President & Chief Operating Officer, E&P",
        "role": "COO",
        "department": "Operations",
        "source": "HR Database",
        "description": (
            "President and COO responsible for all E&P operations globally. "
            "Oversees upstream production performance, lifting cost reduction, "
            "and capital project execution across Guyana, Bakken, Gulf of Mexico, and international assets."
        ),
        "responsibilities": [
            "manage all upstream E&P operations",
            "drive lifting cost reduction and production efficiency",
            "oversee capital project execution and delivery",
            "optimise portfolio allocation across basins",
            "ensure safe and reliable operations",
        ],
        "business_process_ids": [
            "finance_expense_management",
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "operations_production_cost_management",
        ],
        "default_filters": {
            "Segment": ["E&P"],
            "Fiscal Year": ["2024", "2025", "2026"],
        },
        "typical_timeframes": ["Monthly", "Quarterly"],
        "principal_groups": ["Executive Leadership"],
        "persona_profile": {
            "decision_style": "operational",
            "risk_tolerance": "low",
            "communication_style": "detailed",
            "values": ["efficiency", "safety", "execution"],
        },
        "preferences": {"channel": "Slack", "ui": "detail_view"},
        "permissions": ["finance_read"],
        "metadata": {
            "kpi_line_preference": "bottom_line_first",
            "kpi_altitude_preference": "operational_first",
        },
    },
    {
        "id": "finance_manager_001",
        "client_id": CLIENT_ID,
        "name": "Timothy Goodell",
        "first_name": "Timothy",
        "last_name": "Goodell",
        "title": "Finance Manager / Controller",
        "role": "Finance Manager",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "Finance Manager and Controller supporting the CFO with P&L variance analysis, "
            "budget management, cost control reporting, and financial close processes."
        ),
        "responsibilities": [
            "financial close and reporting",
            "budget vs. actuals variance analysis",
            "cost centre management and expense tracking",
            "support investor relations reporting",
            "KPI integrity and data quality",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_budget_vs_actuals",
            "finance_cash_flow_management",
        ],
        "default_filters": {
            "Fiscal Year": ["2024", "2025", "2026"],
        },
        "typical_timeframes": ["Monthly"],
        "principal_groups": ["Finance Committee"],
        "persona_profile": {
            "decision_style": "analytical",
            "risk_tolerance": "low",
            "communication_style": "detailed",
            "values": ["accuracy", "compliance", "cost-control"],
        },
        "preferences": {"channel": "Email", "ui": "detail_view"},
        "permissions": ["finance_read", "finance_write"],
        "metadata": {
            "kpi_line_preference": "balanced",
            "kpi_altitude_preference": "operational_first",
        },
    },
]

# Business processes: Finance + Strategy (the domains Hess principals reference)
BUSINESS_PROCESS_IDS = [
    bp["id"] for bp in FINANCE_BUSINESS_PROCESSES + STRATEGY_BUSINESS_PROCESSES
]

EXTRA_BUSINESS_PROCESSES: List[Dict[str, Any]] = [
    {
        "id": "operations_production_cost_management",
        "name": "Production Cost Management",
        "domain": "Operations",
        "display_name": "Operations: Production Cost Management",
        "description": (
            "Managing and optimising per-barrel production costs across upstream assets. "
            "Covers lifting costs, well workover expenses, and field-level opex efficiency."
        ),
        "owner_role": "COO",
        "stakeholder_roles": ["CFO"],
        "tags": ["operations", "production", "cost", "lifting", "ep"],
        "metadata": {},
    },
]

EXTRA_GLOSSARY_TERMS: List[Dict[str, Any]] = []
