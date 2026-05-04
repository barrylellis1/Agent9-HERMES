"""
Bicycle client (Global Bike Inc.) — DuckDB backend.
Client ID: bicycle
Data product: fi_star_schema (DuckDB / local CSV)

This is the canonical definition for the bicycle client. It is the single
source of truth used by scripts/onboard_client.py to seed (or re-seed
idempotently) all Supabase records for this client.
"""

from typing import Any, Dict, List
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.registry.canonical.business_processes import (
    ALL_BUSINESS_PROCESSES,
    FINANCE_BUSINESS_PROCESSES,
    STRATEGY_BUSINESS_PROCESSES,
)

# ---------------------------------------------------------------------------
# Client identity
# ---------------------------------------------------------------------------

CLIENT_ID = "bicycle"

CLIENT_META: Dict[str, Any] = {
    "id": CLIENT_ID,
    "name": "Global Bike Inc.",
    "industry": "Retail & Manufacturing",
    "data_product_ids": ["fi_star_schema"],
}

# ---------------------------------------------------------------------------
# Data Product
# ---------------------------------------------------------------------------

DATA_PRODUCT: Dict[str, Any] = {
    "id": "fi_star_schema",
    "client_id": CLIENT_ID,
    "name": "FI Star Schema",
    "domain": "Finance",
    "source_system": "duckdb",
    "description": (
        "SAP-style financial star schema for Global Bike Inc., loaded from CSV "
        "into DuckDB. Covers revenue, cost, profitability, expense, and cash flow "
        "KPIs across profit centres, customers, and products."
    ),
    "owner": "Finance",
    "owner_role": "CFO",
    "version": "1.0.0",
    "related_business_processes": [
        "finance_revenue_growth_analysis",
        "finance_profitability_analysis",
        "finance_expense_management",
        "finance_cash_flow_management",
        "finance_budget_vs_actuals",
        "strategy_ebitda_growth_tracking",
        "finance_investor_relations_reporting",
    ],
    "tags": ["finance", "bicycle", "duckdb", "sap", "fi-star-schema"],
    "metadata": {"source_system": "duckdb"},
    "tables": {},
    "views": {
        "fi_star_schema": {
            "columns": [
                "Account Hierarchy Desc",
                "Parent Account/Group Description",
                "Transaction Value Amount",
                "Version",
                "Fiscal Year",
                "Fiscal Quarter",
                "Fiscal Month",
                "Fiscal Year-Month",
                "Profit Center Name",
                "Profit Center Hierarchyid",
                "Customer Name",
                "Customer Hierarchyid",
                "Customer Type Name",
                "Product Name",
            ]
        }
    },
    "reviewed": True,
    "staging": False,
    "language": "EN",
}

# ---------------------------------------------------------------------------
# Standard FI dimensions (shared across all bicycle KPIs)
# ---------------------------------------------------------------------------

_DIMENSIONS: List[Dict[str, Any]] = [
    {"name": "Profit Center", "field": "profit_center"},
    {"name": "Customer Segment", "field": "customer_segment"},
]

# Convenience shorthand used in sql_query strings
_VIEW = "fi_star_schema"
_DP_ID = "fi_star_schema"

# ---------------------------------------------------------------------------
# KPI definitions
# ---------------------------------------------------------------------------
# SQL uses the DuckDB view pattern. The view is registered by
# A9_Data_Product_Agent at runtime and exposes FI Star Schema columns.
# "Account Hierarchy Desc" is the leaf-level account label.
# "Parent Account/Group Description" is the rollup group label.
# All queries filter version = 'Actual'.
# ---------------------------------------------------------------------------

KPIS: List[Dict[str, Any]] = [
    # ------------------------------------------------------------------
    # Revenue KPIs
    # ------------------------------------------------------------------
    {
        "id": "gross_revenue",
        "client_id": CLIENT_ID,
        "name": "Gross Revenue",
        "domain": "Finance",
        "description": "Total gross revenue recognized in the period before deductions.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_revenue_growth_analysis",
            "finance_profitability_analysis",
        ],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Gross Revenue\' AND "Version" = \'Actual\''
        ),
        "filters": {"Account Hierarchy Desc": "Gross Revenue", "Version": "Actual"},
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": False,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "revenue", "top-line", "bicycle"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager", "COO"],
        "metadata": {
            "altitude": "strategic",
            "line": "top",
            "positive_trend_is_good": "true",
        },
    },
    {
        "id": "net_revenue",
        "client_id": CLIENT_ID,
        "name": "Net Revenue",
        "domain": "Finance",
        "description": "Net revenue after deducting sales deductions from gross revenue.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_revenue_growth_analysis",
            "finance_profitability_analysis",
        ],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Parent Account/Group Description" = \'Net Revenue\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Parent Account/Group Description": "Net Revenue",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": False,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "revenue", "net-revenue", "bicycle"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {
            "altitude": "strategic",
            "line": "top",
            "positive_trend_is_good": "true",
        },
    },
    {
        "id": "sales_deductions",
        "client_id": CLIENT_ID,
        "name": "Sales Deductions",
        "domain": "Finance",
        "description": "Total sales deductions (discounts, rebates, returns) reducing gross to net revenue.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
        ],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Sales Deductions\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Sales Deductions",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "revenue", "deductions", "bicycle"],
        "owner_role": "CFO",
        "stakeholder_roles": ["Finance Manager", "COO"],
        "metadata": {
            "altitude": "operational",
            "line": "top",
            "positive_trend_is_good": "false",
        },
    },
    # ------------------------------------------------------------------
    # Profitability KPIs
    # ------------------------------------------------------------------
    {
        "id": "gross_margin",
        "client_id": CLIENT_ID,
        "name": "Gross Margin",
        "domain": "Finance",
        "description": "Gross Revenue minus Cost of Goods Sold.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
        ],
        "sql_query": (
            f'SELECT SUM(CASE WHEN "Account Hierarchy Desc" = \'Cost of Goods Sold\' '
            f'THEN -1 * "Transaction Value Amount" ELSE "Transaction Value Amount" END) AS value '
            f'FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" IN (\'Gross Revenue\', \'Cost of Goods Sold\') '
            f'AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": ["Gross Revenue", "Cost of Goods Sold"],
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": False,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "profitability", "gross-margin", "bicycle"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {
            "altitude": "strategic",
            "line": "middle",
            "positive_trend_is_good": "true",
        },
    },
    {
        "id": "cost_of_goods_sold",
        "client_id": CLIENT_ID,
        "name": "Cost of Goods Sold",
        "domain": "Finance",
        "description": "Total direct cost of goods sold in the period.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_expense_management",
        ],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Cost of Goods Sold\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Cost of Goods Sold",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "cost", "cogs", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "operating_income",
        "client_id": CLIENT_ID,
        "name": "Operating Income",
        "domain": "Finance",
        "description": "Net Revenue minus all operating costs (COGS + Operating Expense).",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_profitability_analysis"],
        "sql_query": (
            f'SELECT SUM(CASE WHEN "Parent Account/Group Description" IN '
            f'(\'Gross Margin\', \'Building Expense\', \'Employee Expense\', \'Operating Expense\') '
            f'THEN -1 * "Transaction Value Amount" ELSE "Transaction Value Amount" END) AS value '
            f'FROM {_VIEW} '
            f'WHERE "Parent Account/Group Description" IN '
            f'(\'Net Revenue\', \'Gross Margin\', \'Building Expense\', \'Employee Expense\', \'Operating Expense\') '
            f'AND "Version" = \'Actual\''
        ),
        "filters": {
            "Parent Account/Group Description": [
                "Net Revenue",
                "Gross Margin",
                "Building Expense",
                "Employee Expense",
                "Operating Expense",
            ],
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": False,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "profitability", "operating-income", "bicycle"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {
            "altitude": "strategic",
            "line": "middle",
            "positive_trend_is_good": "true",
        },
    },
    {
        "id": "earnings_before_interest_and_taxes",
        "client_id": CLIENT_ID,
        "name": "Earnings Before Interest and Taxes",
        "domain": "Finance",
        "description": "EBIT — Operating Income excluding interest and tax line items.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_profitability_analysis",
            "strategy_ebitda_growth_tracking",
        ],
        "sql_query": (
            f'SELECT SUM(CASE WHEN "Parent Account/Group Description" IN '
            f'(\'Gross Margin\', \'Building Expense\', \'Employee Expense\', \'Operating Expense\') '
            f'THEN -1 * "Transaction Value Amount" ELSE "Transaction Value Amount" END) AS value '
            f'FROM {_VIEW} '
            f'WHERE "Parent Account/Group Description" IN '
            f'(\'Net Revenue\', \'Gross Margin\', \'Building Expense\', \'Employee Expense\', \'Operating Expense\') '
            f'AND "Version" = \'Actual\''
        ),
        "filters": {
            "Parent Account/Group Description": [
                "Net Revenue",
                "Gross Margin",
                "Building Expense",
                "Employee Expense",
                "Operating Expense",
            ],
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": False,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "profitability", "ebit", "ebitda", "bicycle"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {
            "altitude": "strategic",
            "line": "middle",
            "positive_trend_is_good": "true",
        },
    },
    {
        "id": "net_income",
        "client_id": CLIENT_ID,
        "name": "Net Income",
        "domain": "Finance",
        "description": "Bottom-line profit after all expenses and deductions.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_investor_relations_reporting",
        ],
        "sql_query": (
            f'SELECT SUM(CASE WHEN "Parent Account/Group Description" IN '
            f'(\'Gross Margin\', \'Building Expense\', \'Employee Expense\', \'Operating Expense\') '
            f'THEN -1 * "Transaction Value Amount" ELSE "Transaction Value Amount" END) AS value '
            f'FROM {_VIEW} '
            f'WHERE "Parent Account/Group Description" IN '
            f'(\'Net Revenue\', \'Gross Margin\', \'Building Expense\', \'Employee Expense\', \'Operating Expense\') '
            f'AND "Version" = \'Actual\''
        ),
        "filters": {
            "Parent Account/Group Description": [
                "Net Revenue",
                "Gross Margin",
                "Building Expense",
                "Employee Expense",
                "Operating Expense",
            ],
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": False,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "profitability", "net-income", "bottom-line", "bicycle"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {
            "altitude": "strategic",
            "line": "bottom",
            "positive_trend_is_good": "true",
        },
    },
    # ------------------------------------------------------------------
    # Expense KPIs
    # ------------------------------------------------------------------
    {
        "id": "operating_expense",
        "client_id": CLIENT_ID,
        "name": "Operating Expense",
        "domain": "Finance",
        "description": "Total operating expenses (Building + Employee + Other Operating).",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Parent Account/Group Description" IN '
            f'(\'Building Expense\', \'Employee Expense\', \'Operating Expense\') '
            f'AND "Version" = \'Actual\''
        ),
        "filters": {
            "Parent Account/Group Description": [
                "Building Expense",
                "Employee Expense",
                "Operating Expense",
            ],
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "opex", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "building_expense",
        "client_id": CLIENT_ID,
        "name": "Building Expense",
        "domain": "Finance",
        "description": "Total building-related expenses including periodic building costs and utilities.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Parent Account/Group Description" = \'Building Expense\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Parent Account/Group Description": "Building Expense",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "building", "facilities", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "periodic_building_expense",
        "client_id": CLIENT_ID,
        "name": "Periodic Building Expense",
        "domain": "Finance",
        "description": "Recurring periodic building expense (maintenance, lease, insurance).",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Periodic Building Expense\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Periodic Building Expense",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "building", "periodic", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "utilities_expense",
        "client_id": CLIENT_ID,
        "name": "Utilities Expense",
        "domain": "Finance",
        "description": "Total utilities expense (electricity, gas, water).",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_expense_management",
            "finance_budget_vs_actuals",
        ],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Utilities Expense\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Utilities Expense",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "utilities", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "employee_expense",
        "client_id": CLIENT_ID,
        "name": "Employee Expense",
        "domain": "Finance",
        "description": "Total employee expenses (payroll, travel, office, and other employee costs).",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Parent Account/Group Description" = \'Employee Expense\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Parent Account/Group Description": "Employee Expense",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "employee", "headcount", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO", "COO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "payroll",
        "client_id": CLIENT_ID,
        "name": "Payroll",
        "domain": "Finance",
        "description": "Total payroll expense including salaries, wages, and employer contributions.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_expense_management",
            "finance_budget_vs_actuals",
        ],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Payroll\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Payroll",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "payroll", "hr", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "travel",
        "client_id": CLIENT_ID,
        "name": "Travel",
        "domain": "Finance",
        "description": "Total travel and entertainment expense.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Travel\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Travel",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "travel", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "office_expense",
        "client_id": CLIENT_ID,
        "name": "Office Expense",
        "domain": "Finance",
        "description": "Total office and administrative supply expenses.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_expense_management",
            "finance_budget_vs_actuals",
        ],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Office Expense\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Office Expense",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "office", "admin", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "employee_expense_other",
        "client_id": CLIENT_ID,
        "name": "Employee Expense Other",
        "domain": "Finance",
        "description": "Miscellaneous employee expenses not captured in payroll, travel, or office lines.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Employee Expense Other\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Employee Expense Other",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "employee", "other", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "other_operating_expense",
        "client_id": CLIENT_ID,
        "name": "Other Operating Expense",
        "domain": "Finance",
        "description": "Miscellaneous operating expenses not captured in building or employee expense lines.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_expense_management"],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Other Operating Expense\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Other Operating Expense",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "other-opex", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    # ------------------------------------------------------------------
    # Cash Flow KPIs
    # ------------------------------------------------------------------
    {
        "id": "depreciation",
        "client_id": CLIENT_ID,
        "name": "Depreciation",
        "domain": "Finance",
        "description": "Total depreciation and amortisation charged in the period.",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": [
            "finance_expense_management",
            "finance_cash_flow_management",
        ],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Account Hierarchy Desc" = \'Depreciation\' AND "Version" = \'Actual\''
        ),
        "filters": {
            "Account Hierarchy Desc": "Depreciation",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": True,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "expense", "depreciation", "amortisation", "bicycle"],
        "owner_role": "Finance Manager",
        "stakeholder_roles": ["CFO"],
        "metadata": {
            "altitude": "operational",
            "line": "middle",
            "positive_trend_is_good": "false",
        },
    },
    {
        "id": "cash_flow_from_operating_activities",
        "client_id": CLIENT_ID,
        "name": "Cash Flow from Operating Activities",
        "domain": "Finance",
        "description": "Net cash generated from core operating activities (CFO).",
        "unit": "$",
        "data_product_id": _DP_ID,
        "view_name": _VIEW,
        "business_process_ids": ["finance_cash_flow_management"],
        "sql_query": (
            f'SELECT SUM("Transaction Value Amount") AS value FROM {_VIEW} '
            f'WHERE "Parent Account/Group Description" = \'Cash Flow from Operating Activities (CFO)\' '
            f'AND "Version" = \'Actual\''
        ),
        "filters": {
            "Parent Account/Group Description": "Cash Flow from Operating Activities (CFO)",
            "Version": "Actual",
        },
        "thresholds": [
            {
                "comparison_type": "yoy",
                "green_threshold": 5.0,
                "yellow_threshold": 0.0,
                "red_threshold": -5.0,
                "inverse_logic": False,
            }
        ],
        "dimensions": _DIMENSIONS,
        "tags": ["finance", "cash-flow", "operating-cash-flow", "liquidity", "bicycle"],
        "owner_role": "CFO",
        "stakeholder_roles": ["CEO", "Finance Manager"],
        "metadata": {
            "altitude": "strategic",
            "line": "bottom",
            "positive_trend_is_good": "true",
        },
    },
]

# ---------------------------------------------------------------------------
# Principals
# ---------------------------------------------------------------------------

PRINCIPALS: List[Dict[str, Any]] = [
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
            "maximise EBIT",
            "manage revenue performance",
            "control operating expenses",
            "ensure cash flow adequacy",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth_analysis",
            "finance_expense_management",
            "finance_cash_flow_management",
            "finance_budget_vs_actuals",
            "finance_investor_relations_reporting",
            "strategy_ebitda_growth_tracking",
            "financial_reporting",
            "tax_management",
            "pricing_strategy",
        ],
        "default_filters": {
            "Profit Center Hierarchyid": ["Total"],
            "Customer Hierarchyid": ["Total"],
            "Fiscal Year": ["2024", "2025"],
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
            "strategy_ebitda_growth_tracking",
            "strategy_market_share_analysis",
            "strategy_capital_allocation_efficiency",
        ],
        "default_filters": {
            "Profit Center Hierarchyid": ["Total"],
            "Customer Hierarchyid": ["Total"],
            "Fiscal Year": ["2024", "2025"],
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
        "description": "COO focused on operational excellence and cost efficiency in bicycle manufacturing and distribution.",
        "responsibilities": [
            "optimise operations",
            "reduce operational costs",
            "improve process efficiency",
        ],
        "business_process_ids": [
            "finance_expense_management",
            "finance_profitability_analysis",
            "operations_order_to_cash_cycle_optimization",
            "operations_inventory_turnover_analysis",
            "order_processing",
            "sales_operations",
        ],
        "default_filters": {
            "Profit Center Hierarchyid": ["Total"],
            "Customer Hierarchyid": ["Total"],
            "Fiscal Year": ["2024", "2025"],
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
            "analyse financial data",
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
            "Profit Center Hierarchyid": ["Total"],
            "Customer Hierarchyid": ["Total"],
            "Fiscal Year": ["2024", "2025"],
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

# ---------------------------------------------------------------------------
# Business processes
# ---------------------------------------------------------------------------
# The onboard script stamps client_id on these before inserting.
# Bicycle uses Finance + Strategy domains from the canonical taxonomy.

BUSINESS_PROCESS_IDS: List[str] = [
    bp["id"] for bp in FINANCE_BUSINESS_PROCESSES + STRATEGY_BUSINESS_PROCESSES
]

# No bicycle-specific BPs beyond the canonical taxonomy.
EXTRA_BUSINESS_PROCESSES: List[Dict[str, Any]] = []

# No bicycle-specific glossary terms.
EXTRA_GLOSSARY_TERMS: List[Dict[str, Any]] = []
