#!/usr/bin/env python3
"""
Create and seed the agent9_hess SQL Server database.

Creates:
  1. Database: agent9_hess
  2. Table:    dbo.hess_financials  (E&P star schema fact table)
  3. View:     dbo.HessStarSchemaView  (same column names as the data product contract)
  4. Demo data: 2 fiscal years (2024 = prior, 2025 = current) with realistic
     E&P financials — some KPIs deliberately declining YoY to generate situations.

Usage:
    python scripts/seed_sqlserver_hess.py [--host localhost] [--port 1433]
                                          [--username sa] [--password Agent9Test!2024]
                                          [--drop-if-exists]
"""

import argparse
import sys
from datetime import date, timedelta
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Demo data parameters  (all amounts in $M)
# ---------------------------------------------------------------------------

# Hess 2024 baseline — based on ~$12B annual revenue, scaled to $M
_MONTHS_2024 = [
    # (month, segment,    basin,           asset,             account_type, account_category, account_name,                 amount_M)
    # E&P Revenue — Guyana FPSO production
    (1,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            620.0),
    (2,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            615.0),
    (3,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            630.0),
    (4,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            605.0),
    (5,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            618.0),
    (6,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            625.0),
    (7,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            612.0),
    (8,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            608.0),
    (9,  "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            622.0),
    (10, "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            635.0),
    (11, "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            618.0),
    (12, "E&P",       "Guyana",        "Payara FPSO",     "Revenue",    "Production",     "Crude Oil Sales",            610.0),
    # E&P Revenue — Bakken
    (1,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            180.0),
    (2,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            182.0),
    (3,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            178.0),
    (4,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            175.0),
    (5,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            180.0),
    (6,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            185.0),
    (7,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            183.0),
    (8,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            179.0),
    (9,  "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            177.0),
    (10, "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            182.0),
    (11, "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            181.0),
    (12, "E&P",       "Bakken",        "Bakken Assets",   "Revenue",    "Production",     "Crude Oil Sales",            178.0),
    # Midstream Revenue
    (1,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      155.0),
    (2,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      153.0),
    (3,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      158.0),
    (4,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      150.0),
    (5,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      155.0),
    (6,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      160.0),
    (7,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      157.0),
    (8,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      154.0),
    (9,  "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      156.0),
    (10, "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      162.0),
    (11, "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      158.0),
    (12, "Midstream",  "Bakken",       "Midstream LP",    "Revenue",    "Midstream",      "Gathering & Processing",      155.0),
    # Lifting Costs (E&P COGS) — 2024 baseline
    (1,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  148.0),
    (2,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  145.0),
    (3,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  150.0),
    (4,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  147.0),
    (5,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  149.0),
    (6,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  151.0),
    (7,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  148.0),
    (8,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  146.0),
    (9,  "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  150.0),
    (10, "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  152.0),
    (11, "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  149.0),
    (12, "E&P",       "Guyana",        "Payara FPSO",     "COGS",       "Lifting Costs",  "Production Operating Costs",  148.0),
    (1,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   42.0),
    (2,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   43.0),
    (3,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   41.0),
    (4,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   43.0),
    (5,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   42.0),
    (6,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   44.0),
    (7,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   43.0),
    (8,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   42.0),
    (9,  "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   43.0),
    (10, "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   44.0),
    (11, "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   42.0),
    (12, "E&P",       "Bakken",        "Bakken Assets",   "COGS",       "Lifting Costs",  "Production Operating Costs",   43.0),
    # SG&A
    (1,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  55.0),
    (2,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  54.0),
    (3,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  56.0),
    (4,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  53.0),
    (5,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  55.0),
    (6,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  57.0),
    (7,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  56.0),
    (8,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  54.0),
    (9,  "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  55.0),
    (10, "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  58.0),
    (11, "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  55.0),
    (12, "E&P",       "Corporate",     "Corporate HQ",    "SGA",        "SGA",            "G&A Expense",                  56.0),
    # CapEx — 2024
    (1,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        275.0),
    (2,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        280.0),
    (3,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        270.0),
    (4,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        285.0),
    (5,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        275.0),
    (6,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        290.0),
    (7,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        280.0),
    (8,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        272.0),
    (9,  "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        278.0),
    (10, "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        285.0),
    (11, "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        275.0),
    (12, "E&P",       "Guyana",        "Payara FPSO",     "CapEx",      "Development",    "Development Drilling",        270.0),
    # Exploration — 2024
    (1,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        35.0),
    (2,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        32.0),
    (3,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        38.0),
    (4,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        33.0),
    (5,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        36.0),
    (6,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        34.0),
    (7,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        37.0),
    (8,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        35.0),
    (9,  "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        33.0),
    (10, "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        36.0),
    (11, "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        34.0),
    (12, "E&P",       "Guyana",        "Stabroek Block",  "COGS",       "Exploration",    "Seismic & Exploration",        35.0),
    # D&A (for EBITDA)
    (1,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  92.0),
    (2,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  92.0),
    (3,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  93.0),
    (4,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  91.0),
    (5,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  92.0),
    (6,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  93.0),
    (7,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  92.0),
    (8,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  91.0),
    (9,  "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  93.0),
    (10, "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  94.0),
    (11, "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  92.0),
    (12, "E&P",       "Guyana",        "Payara FPSO",     "DA",         "Depreciation",   "Depreciation & Amortization",  92.0),
    # Operating CF
    (1,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         420.0),
    (2,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         415.0),
    (3,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         425.0),
    (4,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         410.0),
    (5,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         418.0),
    (6,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         422.0),
    (7,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         416.0),
    (8,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         412.0),
    (9,  "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         420.0),
    (10, "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         428.0),
    (11, "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         418.0),
    (12, "E&P",       "Corporate",     "Corporate HQ",    "OperatingCF","Cash Flow",      "Operating Cash Flow",         415.0),
]

# 2025 data — oil price compression drives revenue down ~9% YoY (triggers red)
# Lifting costs up ~13% YoY (COGS inflation — also triggers red)
# CapEx up ~6% (yellow/red for cost KPIs)
_REVENUE_SCALE_2025 = 0.91   # -9% upstream revenue vs 2024
_MIDSTREAM_SCALE_2025 = 0.97  # midstream more stable, -3%
_LIFTING_SCALE_2025 = 1.13   # lifting cost +13% (red threshold is +10%)
_CAPEX_SCALE_2025 = 1.07     # capex +7%
_EXPLORATION_SCALE_2025 = 1.18  # exploration up 18% (new Guyana wells)
_SGA_SCALE_2025 = 1.04       # SGA +4% (slight increase)
_CF_SCALE_2025 = 0.88        # operating CF follows revenue down harder
_DA_SCALE_2025 = 1.02        # D&A barely changes


def _scale_2025(row):
    """Apply 2025 scaling factors based on account_type / account_category."""
    (month, segment, basin, asset, acc_type, acc_cat, acc_name, amount) = row
    if acc_type == "Revenue":
        scale = _MIDSTREAM_SCALE_2025 if segment == "Midstream" else _REVENUE_SCALE_2025
    elif acc_cat == "Lifting Costs":
        scale = _LIFTING_SCALE_2025
    elif acc_type == "CapEx":
        scale = _CAPEX_SCALE_2025
    elif acc_cat == "Exploration":
        scale = _EXPLORATION_SCALE_2025
    elif acc_type == "SGA":
        scale = _SGA_SCALE_2025
    elif acc_type == "OperatingCF":
        scale = _CF_SCALE_2025
    elif acc_type == "DA":
        scale = _DA_SCALE_2025
    else:
        scale = 1.0
    return (month, segment, basin, asset, acc_type, acc_cat, acc_name, round(amount * scale, 1))


_MONTHS_2025 = [_scale_2025(row) for row in _MONTHS_2024]


# ---------------------------------------------------------------------------
# SQL DDL
# ---------------------------------------------------------------------------

_CREATE_DB = "CREATE DATABASE [agent9_hess]"

_CREATE_TABLE = """
CREATE TABLE [dbo].[hess_financials] (
    transaction_id   NVARCHAR(50)    NOT NULL,
    fiscal_year      INT             NOT NULL,
    fiscal_period    NVARCHAR(10)    NOT NULL,
    transaction_date DATE            NOT NULL,
    amount           DECIMAL(18,2)   NOT NULL,
    version          NVARCHAR(20)    NOT NULL DEFAULT 'Actual',
    currency         NVARCHAR(10)    NOT NULL DEFAULT 'USD',
    account_name     NVARCHAR(200)   NOT NULL,
    account_type     NVARCHAR(50)    NOT NULL,
    account_category NVARCHAR(100)   NOT NULL,
    segment_name     NVARCHAR(100)   NOT NULL,
    basin_name       NVARCHAR(100)   NOT NULL,
    asset_name       NVARCHAR(200)   NOT NULL,
    country          NVARCHAR(100)   NOT NULL DEFAULT 'USA',
    region           NVARCHAR(100)   NOT NULL DEFAULT 'Americas',
    business_unit    NVARCHAR(100)   NOT NULL DEFAULT 'E&P',
    CONSTRAINT PK_hess_financials PRIMARY KEY (transaction_id)
)
"""

_CREATE_VIEW = """
CREATE VIEW [dbo].[HessStarSchemaView] AS
SELECT
    transaction_id,
    fiscal_year,
    fiscal_period,
    CONVERT(NVARCHAR(10), transaction_date, 120) AS transaction_date,
    amount,
    version,
    currency,
    account_name,
    account_type,
    account_category,
    segment_name,
    basin_name,
    asset_name,
    country,
    region,
    business_unit
FROM [dbo].[hess_financials]
"""

_CREATE_IDX = [
    "CREATE INDEX idx_hf_fiscal_year    ON [dbo].[hess_financials] (fiscal_year)",
    "CREATE INDEX idx_hf_account_type   ON [dbo].[hess_financials] (account_type)",
    "CREATE INDEX idx_hf_account_cat    ON [dbo].[hess_financials] (account_category)",
    "CREATE INDEX idx_hf_segment        ON [dbo].[hess_financials] (segment_name)",
    "CREATE INDEX idx_hf_version        ON [dbo].[hess_financials] (version)",
    "CREATE INDEX idx_hf_txn_date       ON [dbo].[hess_financials] (transaction_date)",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _month_to_period(month: int) -> str:
    return f"P{month:02d}"


def _month_first_day(year: int, month: int) -> date:
    return date(year, month, 1)


def _build_rows(year: int, month_rows) -> List[tuple]:
    rows = []
    for i, (month, segment, basin, asset, acc_type, acc_cat, acc_name, amount) in enumerate(month_rows):
        txn_id = f"HF-{year}-{month:02d}-{i+1:04d}"
        txn_date = _month_first_day(year, month)
        period = _month_to_period(month)
        country = "Guyana" if basin == "Guyana" else "USA"
        region = "South America" if basin == "Guyana" else "Americas"
        bu = segment
        rows.append((
            txn_id, year, period, txn_date,
            amount, "Actual", "USD",
            acc_name, acc_type, acc_cat,
            segment, basin, asset,
            country, region, bu,
        ))
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Create and seed agent9_hess SQL Server database")
    parser.add_argument("--host",     default="localhost")
    parser.add_argument("--port",     type=int, default=1433)
    parser.add_argument("--username", default="sa")
    parser.add_argument("--password", default="Agent9Test!2024")
    parser.add_argument("--drop-if-exists", action="store_true",
                        help="Drop and recreate the database if it already exists")
    args = parser.parse_args()

    import pyodbc

    master_conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={args.host},{args.port};"
        f"DATABASE=master;"
        f"UID={args.username};"
        f"PWD={args.password};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=no;"
    )

    # -----------------------------------------------------------------------
    # 1. Create database (connect to master first)
    # -----------------------------------------------------------------------
    print(f"Connecting to SQL Server at {args.host}:{args.port}...")
    master = pyodbc.connect(master_conn_str, autocommit=True)
    cur = master.cursor()

    existing = cur.execute(
        "SELECT name FROM sys.databases WHERE name = 'agent9_hess'"
    ).fetchone()

    if existing:
        if args.drop_if_exists:
            print("Dropping existing agent9_hess database...")
            cur.execute("ALTER DATABASE [agent9_hess] SET SINGLE_USER WITH ROLLBACK IMMEDIATE")
            cur.execute("DROP DATABASE [agent9_hess]")
            print("  Dropped.")
        else:
            print("Database agent9_hess already exists. Use --drop-if-exists to recreate.")
            print("Skipping DDL — seeding data into existing database.")
            master.close()
            _seed_data_only(args)
            return

    print("Creating database agent9_hess...")
    cur.execute(_CREATE_DB)
    master.close()
    print("  Done.")

    # -----------------------------------------------------------------------
    # 2. Create table + view in agent9_hess
    # -----------------------------------------------------------------------
    hess_conn_str = master_conn_str.replace("DATABASE=master;", "DATABASE=agent9_hess;")
    conn = pyodbc.connect(hess_conn_str, autocommit=True)
    cur = conn.cursor()

    print("Creating hess_financials table...")
    cur.execute(_CREATE_TABLE)
    print("  Done.")

    print("Creating indexes...")
    for sql in _CREATE_IDX:
        cur.execute(sql)
    print("  Done.")

    print("Creating HessStarSchemaView...")
    cur.execute(_CREATE_VIEW)
    print("  Done.")

    # -----------------------------------------------------------------------
    # 3. Insert demo data
    # -----------------------------------------------------------------------
    _insert_rows(cur, _build_rows(2024, _MONTHS_2024))
    _insert_rows(cur, _build_rows(2025, _MONTHS_2025))

    conn.close()

    # -----------------------------------------------------------------------
    # 4. Verify
    # -----------------------------------------------------------------------
    _verify(args)


def _seed_data_only(args):
    """Insert rows into an existing database (idempotent via MERGE)."""
    import pyodbc
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={args.host},{args.port};"
        f"DATABASE=agent9_hess;"
        f"UID={args.username};"
        f"PWD={args.password};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=no;"
    )
    conn = pyodbc.connect(conn_str, autocommit=True)
    cur = conn.cursor()
    _insert_rows(cur, _build_rows(2024, _MONTHS_2024))
    _insert_rows(cur, _build_rows(2025, _MONTHS_2025))
    conn.close()
    _verify(args)


def _insert_rows(cur, rows: List[tuple]):
    year = rows[0][1] if rows else "?"
    print(f"Inserting {len(rows)} rows for fiscal year {year}...")
    insert_sql = """
        IF NOT EXISTS (SELECT 1 FROM [dbo].[hess_financials] WHERE transaction_id = ?)
        INSERT INTO [dbo].[hess_financials]
            (transaction_id, fiscal_year, fiscal_period, transaction_date,
             amount, version, currency, account_name, account_type, account_category,
             segment_name, basin_name, asset_name, country, region, business_unit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for row in rows:
        cur.execute(insert_sql, row[0], *row)
    print(f"  {len(rows)} rows inserted.")


def _verify(args):
    import pyodbc
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={args.host},{args.port};"
        f"DATABASE=agent9_hess;"
        f"UID={args.username};"
        f"PWD={args.password};"
        f"TrustServerCertificate=yes;"
        f"Encrypt=no;"
    )
    conn = pyodbc.connect(conn_str, autocommit=False)
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM [dbo].[hess_financials]").fetchone()[0]
    by_year = cur.execute(
        "SELECT fiscal_year, COUNT(*) FROM [dbo].[hess_financials] GROUP BY fiscal_year ORDER BY fiscal_year"
    ).fetchall()
    revenue_2024 = cur.execute(
        "SELECT SUM(amount) FROM [dbo].[HessStarSchemaView] WHERE account_type='Revenue' AND fiscal_year=2024"
    ).fetchone()[0]
    revenue_2025 = cur.execute(
        "SELECT SUM(amount) FROM [dbo].[HessStarSchemaView] WHERE account_type='Revenue' AND fiscal_year=2025"
    ).fetchone()[0]

    conn.close()

    print("\n--- Verification ---")
    print(f"Total rows in hess_financials: {total}")
    for yr, cnt in by_year:
        print(f"  {yr}: {cnt} rows")
    pct_chg = (revenue_2025 - revenue_2024) / revenue_2024 * 100 if revenue_2024 else 0
    print(f"\nRevenue 2024: ${revenue_2024:,.1f}M  →  2025: ${revenue_2025:,.1f}M  ({pct_chg:+.1f}% YoY)")
    print("  Expected: ~-9% (should trigger RED threshold)\n")
    print("Done. HessStarSchemaView ready for SA agent queries.")


if __name__ == "__main__":
    main()
