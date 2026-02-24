#!/usr/bin/env python3
"""
Generate Lubricants Business Demo Data for BigQuery.

Creates a realistic lubricants-industry financial star schema with engineered
business scenarios that trigger Situation Awareness detection at multiple severity
levels (CRITICAL, HIGH, MEDIUM, INFORMATION).

Usage:
    python scripts/generate_lubricants_demo_data.py [--dry-run]

Environment:
    GOOGLE_APPLICATION_CREDENTIALS - Path to GCP service account JSON
"""

import argparse
import json
import os
import random
import sys
import uuid
from datetime import date, timedelta
from typing import Dict, List

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ID = "agent9-465818"
DATASET_ID = "LubricantsBusiness"
VIEW_NAME = "LubricantsStarSchemaView"

# Date range: 2024-01-01 through 2026-02-28
DATE_START = date(2024, 1, 1)
DATE_END = date(2026, 2, 28)

random.seed(42)  # Reproducible data

# ---------------------------------------------------------------------------
# Dimension Data
# ---------------------------------------------------------------------------

GL_ACCOUNTS = [
    # Revenue
    {"gl_account_id": "GL-R100", "account_name": "Net Revenue - Product Sales",    "account_type": "Revenue",  "account_category": "Product Sales",       "account_group": "Revenue"},
    {"gl_account_id": "GL-R200", "account_name": "Net Revenue - Service",          "account_type": "Revenue",  "account_category": "Service Revenue",     "account_group": "Revenue"},
    # COGS
    {"gl_account_id": "GL-C100", "account_name": "Base Oil & Additives",           "account_type": "COGS",     "account_category": "Raw Materials",       "account_group": "Cost of Goods Sold"},
    {"gl_account_id": "GL-C200", "account_name": "Blending & Manufacturing",       "account_type": "COGS",     "account_category": "Manufacturing",       "account_group": "Cost of Goods Sold"},
    {"gl_account_id": "GL-C300", "account_name": "Packaging",                      "account_type": "COGS",     "account_category": "Packaging",           "account_group": "Cost of Goods Sold"},
    {"gl_account_id": "GL-C400", "account_name": "Distribution & Freight",         "account_type": "COGS",     "account_category": "Distribution",        "account_group": "Cost of Goods Sold"},
    # SG&A
    {"gl_account_id": "GL-S100", "account_name": "Sales & Marketing",              "account_type": "SGA",      "account_category": "Sales & Marketing",   "account_group": "SG&A"},
    {"gl_account_id": "GL-S200", "account_name": "Brand & Advertising",            "account_type": "SGA",      "account_category": "Brand & Advertising", "account_group": "SG&A"},
    {"gl_account_id": "GL-S300", "account_name": "General & Administrative",       "account_type": "SGA",      "account_category": "G&A",                 "account_group": "SG&A"},
    # Other
    {"gl_account_id": "GL-O100", "account_name": "Depreciation & Amortization",    "account_type": "Other",    "account_category": "D&A",                 "account_group": "Other Operating"},
    {"gl_account_id": "GL-O200", "account_name": "Interest Expense",               "account_type": "Other",    "account_category": "Interest",            "account_group": "Non-Operating"},
    {"gl_account_id": "GL-O300", "account_name": "Income Tax Provision",           "account_type": "Other",    "account_category": "Tax",                 "account_group": "Non-Operating"},
]

PRODUCTS = [
    {"product_id": "P-EO-FS", "product_name": "Full Synthetic Engine Oil",       "product_line": "Engine Oils",                "product_category": "Premium"},
    {"product_id": "P-EO-SB", "product_name": "Synthetic Blend Engine Oil",      "product_line": "Engine Oils",                "product_category": "Mid-Range"},
    {"product_id": "P-EO-CV", "product_name": "Conventional Engine Oil",         "product_line": "Engine Oils",                "product_category": "Value"},
    {"product_id": "P-EO-HM", "product_name": "High Mileage Engine Oil",        "product_line": "Engine Oils",                "product_category": "Specialty"},
    {"product_id": "P-TF-01", "product_name": "Automatic Transmission Fluid",   "product_line": "Transmission & Drivetrain",  "product_category": "Mid-Range"},
    {"product_id": "P-TF-02", "product_name": "Manual Gear Oil",                "product_line": "Transmission & Drivetrain",  "product_category": "Value"},
    {"product_id": "P-IL-HY", "product_name": "Hydraulic Oil",                  "product_line": "Industrial Lubricants",      "product_category": "Industrial"},
    {"product_id": "P-IL-CO", "product_name": "Compressor Oil",                 "product_line": "Industrial Lubricants",      "product_category": "Industrial"},
    {"product_id": "P-IL-TB", "product_name": "Turbine Oil",                    "product_line": "Industrial Lubricants",      "product_category": "Industrial"},
    {"product_id": "P-GR-01", "product_name": "Multi-Purpose Grease",           "product_line": "Greases & Specialty",        "product_category": "Specialty"},
    {"product_id": "P-GR-02", "product_name": "High-Temp Bearing Grease",       "product_line": "Greases & Specialty",        "product_category": "Premium"},
    {"product_id": "P-CL-01", "product_name": "Extended Life Coolant",          "product_line": "Coolants & Antifreeze",      "product_category": "Mid-Range"},
    {"product_id": "P-CL-02", "product_name": "Heavy-Duty Coolant",             "product_line": "Coolants & Antifreeze",      "product_category": "Industrial"},
    {"product_id": "P-CH-01", "product_name": "Fuel System Cleaner",            "product_line": "Chemicals & Additives",      "product_category": "Specialty"},
    {"product_id": "P-CH-02", "product_name": "Oil Treatment Additive",         "product_line": "Chemicals & Additives",      "product_category": "Specialty"},
]

CUSTOMERS = [
    # Retail Partners
    {"customer_id": "C-RP-01", "customer_name": "National Auto Parts Chain A",     "customer_segment": "Retail Partners",     "customer_region": "North America"},
    {"customer_id": "C-RP-02", "customer_name": "National Auto Parts Chain B",     "customer_segment": "Retail Partners",     "customer_region": "North America"},
    {"customer_id": "C-RP-03", "customer_name": "Mass Retailer Group",             "customer_segment": "Retail Partners",     "customer_region": "North America"},
    {"customer_id": "C-RP-04", "customer_name": "Hardware & Home Chain",           "customer_segment": "Retail Partners",     "customer_region": "North America"},
    {"customer_id": "C-RP-05", "customer_name": "Regional Auto Parts Distributor", "customer_segment": "Retail Partners",     "customer_region": "North America"},
    # Service Centers
    {"customer_id": "C-SC-01", "customer_name": "Quick Lube Franchise Network",    "customer_segment": "Service Centers",     "customer_region": "North America"},
    {"customer_id": "C-SC-02", "customer_name": "Dealer Service Network",          "customer_segment": "Service Centers",     "customer_region": "North America"},
    {"customer_id": "C-SC-03", "customer_name": "Independent Service Centers",     "customer_segment": "Service Centers",     "customer_region": "North America"},
    # Commercial Fleet
    {"customer_id": "C-FL-01", "customer_name": "Fleet Customer A",                "customer_segment": "Commercial Fleet",    "customer_region": "North America"},
    {"customer_id": "C-FL-02", "customer_name": "Fleet Customer B",                "customer_segment": "Commercial Fleet",    "customer_region": "North America"},
    {"customer_id": "C-FL-03", "customer_name": "Fleet Customer C",                "customer_segment": "Commercial Fleet",    "customer_region": "North America"},
    {"customer_id": "C-FL-04", "customer_name": "Mining & Construction Corp",      "customer_segment": "Commercial Fleet",    "customer_region": "North America"},
    {"customer_id": "C-FL-05", "customer_name": "Agriculture Coop",                "customer_segment": "Commercial Fleet",    "customer_region": "North America"},
    # Industrial
    {"customer_id": "C-IN-01", "customer_name": "Manufacturing Plant Group",       "customer_segment": "Industrial",          "customer_region": "North America"},
    {"customer_id": "C-IN-02", "customer_name": "Power Generation Utility",        "customer_segment": "Industrial",          "customer_region": "North America"},
    {"customer_id": "C-IN-03", "customer_name": "Marine Operations Co",            "customer_segment": "Industrial",          "customer_region": "International"},
    # International
    {"customer_id": "C-IT-01", "customer_name": "European Distributor",            "customer_segment": "International Distributors", "customer_region": "Europe"},
    {"customer_id": "C-IT-02", "customer_name": "Asia-Pacific Distributor",        "customer_segment": "International Distributors", "customer_region": "Asia-Pacific"},
    {"customer_id": "C-IT-03", "customer_name": "Latin America Distributor",       "customer_segment": "International Distributors", "customer_region": "Latin America"},
    {"customer_id": "C-IT-04", "customer_name": "Middle East Distributor",         "customer_segment": "International Distributors", "customer_region": "Middle East"},
]

PROFIT_CENTERS = [
    {"profit_center_id": "PC-RP", "profit_center_name": "Retail Products Division",       "business_unit": "Retail Products"},
    {"profit_center_id": "PC-SC", "profit_center_name": "Service Centers Division",       "business_unit": "Service Centers"},
    {"profit_center_id": "PC-CI", "profit_center_name": "Commercial & Industrial Division","business_unit": "Commercial & Industrial"},
    {"profit_center_id": "PC-IN", "profit_center_name": "International Division",          "business_unit": "International"},
    {"profit_center_id": "PC-CO", "profit_center_name": "Corporate",                       "business_unit": "Corporate"},
]

CHANNELS = [
    {"channel_id": "CH-DIY",  "channel_name": "DIY Retail",              "channel_type": "Retail"},
    {"channel_id": "CH-DIFM", "channel_name": "DIFM Service Centers",    "channel_type": "Service"},
    {"channel_id": "CH-B2B",  "channel_name": "B2B Direct Sales",        "channel_type": "Direct"},
    {"channel_id": "CH-ECOM", "channel_name": "E-Commerce",              "channel_type": "Digital"},
    {"channel_id": "CH-INTL", "channel_name": "International Distribution","channel_type": "International"},
]

# ---------------------------------------------------------------------------
# Revenue & cost allocation weights (annual basis, in $M)
# These define the "normal" P&L shape before anomalies
# ---------------------------------------------------------------------------

# Channel revenue weights (% of total ~$1.4B product + service revenue)
CHANNEL_REVENUE_WEIGHTS = {
    "CH-DIY":  0.30,   # $420M - DIY retail
    "CH-DIFM": 0.13,   # $180M - Service centers
    "CH-B2B":  0.22,   # $310M - B2B direct (fleet + industrial)
    "CH-ECOM": 0.05,   # $74M  - E-Commerce (growing fast)
    "CH-INTL": 0.10,   # $140M - International
}
# Remaining ~20% is spread across smaller accounts/overhead

# Seasonal multipliers by month (1.0 = average, summer peak for retail/service)
SEASONAL = {
    1: 0.85, 2: 0.87, 3: 0.92, 4: 0.98, 5: 1.08,  6: 1.15,
    7: 1.18, 8: 1.12, 9: 1.02, 10: 0.95, 11: 0.90, 12: 0.88,
}

# Cost seasonality (flatter -- production schedules are smoothed vs retail demand)
COST_SEASONAL = {
    1: 0.96, 2: 0.96, 3: 0.98, 4: 0.99, 5: 1.02, 6: 1.03,
    7: 1.04, 8: 1.03, 9: 1.01, 10: 0.99, 11: 0.98, 12: 0.97,
}

# Channel -> applicable product pools (for realistic product mix)
CHANNEL_PRODUCTS = {
    "CH-DIY":  ["P-EO-FS", "P-EO-SB", "P-EO-CV", "P-EO-HM", "P-TF-01", "P-TF-02",
                "P-CL-01", "P-CH-01", "P-CH-02", "P-GR-01"],
    "CH-DIFM": ["P-EO-FS", "P-EO-SB", "P-EO-CV", "P-EO-HM", "P-TF-01", "P-CL-01",
                "P-CH-01", "P-GR-01"],
    "CH-B2B":  ["P-EO-FS", "P-EO-SB", "P-EO-CV", "P-IL-HY", "P-IL-CO", "P-IL-TB",
                "P-GR-01", "P-GR-02", "P-CL-02", "P-TF-01"],
    "CH-ECOM": ["P-EO-FS", "P-EO-FS", "P-EO-SB", "P-EO-HM", "P-CH-01", "P-CH-02",
                "P-CL-01", "P-TF-01"],  # Premium-skewed (FS appears 2x)
    "CH-INTL": ["P-EO-FS", "P-EO-SB", "P-EO-CV", "P-IL-HY", "P-IL-CO", "P-GR-01",
                "P-CL-02", "P-TF-01"],
}

# Channel -> customer pool
CHANNEL_CUSTOMERS = {
    "CH-DIY":  ["C-RP-01", "C-RP-02", "C-RP-03", "C-RP-04", "C-RP-05"],
    "CH-DIFM": ["C-SC-01", "C-SC-02", "C-SC-03"],
    "CH-B2B":  ["C-FL-01", "C-FL-02", "C-FL-03", "C-FL-04", "C-FL-05",
                "C-IN-01", "C-IN-02", "C-IN-03"],
    "CH-ECOM": ["C-RP-01", "C-RP-03"],
    "CH-INTL": ["C-IT-01", "C-IT-02", "C-IT-03", "C-IT-04"],
}


def _quarter(m: int) -> int:
    return (m - 1) // 3 + 1


def _fiscal_period(m: int) -> str:
    return f"{m:03d}"


# ---------------------------------------------------------------------------
# Transaction generator
# ---------------------------------------------------------------------------

def generate_transactions() -> List[Dict]:
    """Generate ~50-60K financial transactions with engineered scenarios.

    Revenue transactions are generated per channel x customer x product to create
    the granularity that Deep Analysis needs for dimensional drill-down (IS/IS-NOT).

    COGS uses a flatter seasonal curve (production-schedule-based) so that the
    engineered Q4 2025 base-oil spike is clearly visible vs Q3.
    """
    rows: List[Dict] = []
    txn_counter = 0

    # Base monthly revenue before seasonality.
    # Channel weights sum to 0.80 -> effective revenue = 146M * 0.80 = ~$117M/month = ~$1.4B/year
    base_monthly_revenue = 146_000_000

    # Profit-center mapping by channel
    CHANNEL_PC = {
        "CH-DIY": "PC-RP", "CH-ECOM": "PC-RP",
        "CH-DIFM": "PC-SC", "CH-B2B": "PC-CI", "CH-INTL": "PC-IN",
    }

    def _make_txn(*, gl_id, prod_id, cust_id, pc_id, ch_id,
                  yr, mo, amt, version="Actual"):
        nonlocal txn_counter
        txn_counter += 1
        day = min(28, random.randint(1, 28))
        return {
            "transaction_id": f"TXN-{txn_counter:06d}",
            "fiscal_year": yr,
            "fiscal_period": _fiscal_period(mo),
            "transaction_date": date(yr, mo, day).isoformat(),
            "gl_account_id": gl_id,
            "product_id": prod_id,
            "customer_id": cust_id,
            "profit_center_id": pc_id,
            "channel_id": ch_id,
            "amount": round(amt, 2),
            "version": version,
            "currency": "USD",
        }

    # Iterate month by month
    current = DATE_START
    while current <= DATE_END:
        yr = current.year
        mo = current.month
        qtr = _quarter(mo)
        season = SEASONAL[mo]
        cost_season = COST_SEASONAL[mo]

        # ── Year-over-year growth factor ──
        if yr == 2024:
            yoy_growth = 1.0
        elif yr == 2025:
            yoy_growth = 1.04   # +4% YoY
        else:
            yoy_growth = 1.04 * 1.03  # +3% on top of 2025

        monthly_revenue_base = base_monthly_revenue * yoy_growth * season

        # ────────────────────────────────────────────────────────
        # REVENUE  (per channel -> customer -> product -> 1-3 txns)
        # ────────────────────────────────────────────────────────
        for channel_id, ch_weight in CHANNEL_REVENUE_WEIGHTS.items():
            channel_revenue = monthly_revenue_base * ch_weight

            # ── SCENARIO 2: Service Center decline in 2025+ ──
            if channel_id == "CH-DIFM" and yr >= 2025:
                channel_revenue *= 0.88

            # ── SCENARIO 5: E-Commerce surge in 2025+ ──
            if channel_id == "CH-ECOM" and yr >= 2025:
                channel_revenue *= 1.55

            # ── SCENARIO 2: Compensating DIY growth ──
            if channel_id == "CH-DIY" and yr >= 2025:
                channel_revenue *= 1.06

            gl_id = "GL-R200" if channel_id == "CH-DIFM" else "GL-R100"
            pc_id = CHANNEL_PC[channel_id]
            cust_pool = CHANNEL_CUSTOMERS[channel_id]
            prod_pool = CHANNEL_PRODUCTS[channel_id]

            # Distribute across customer x product with jitter
            n_custs = len(cust_pool)
            n_prods = len(prod_pool)
            total_combos = n_custs * n_prods

            # Random weights for each combo
            combo_weights = [random.uniform(0.5, 1.5) for _ in range(total_combos)]
            combo_total_w = sum(combo_weights)

            idx = 0
            for cust_id in cust_pool:
                for prod_id in prod_pool:
                    combo_share = channel_revenue * combo_weights[idx] / combo_total_w
                    idx += 1

                    # ── SCENARIO 4: Fleet Customer A decline in 2025+ ──
                    if cust_id == "C-FL-01" and yr >= 2025:
                        combo_share *= 0.69  # -31%

                    # Split into 5-12 invoice lines per combo (individual shipments/invoices)
                    n_lines = random.randint(5, 12)
                    splits = _random_splits(n_lines, combo_share)
                    for amt in splits:
                        rows.append(_make_txn(
                            gl_id=gl_id, prod_id=prod_id, cust_id=cust_id,
                            pc_id=pc_id, ch_id=channel_id,
                            yr=yr, mo=mo, amt=amt,
                        ))

        # ────────────────────────────────────────────────────────
        # COGS  (decoupled from revenue seasonality)
        # Uses COST_SEASONAL for production-schedule smoothing
        # ────────────────────────────────────────────────────────
        cogs_accounts = [
            ("GL-C100", 0.40),  # Base Oil & Additives
            ("GL-C200", 0.30),  # Blending & Manufacturing
            ("GL-C300", 0.12),  # Packaging
            ("GL-C400", 0.18),  # Distribution
        ]
        # Base COGS = annual revenue * 0.65 / 12, with mild cost seasonality
        annual_revenue = base_monthly_revenue * yoy_growth * sum(CHANNEL_REVENUE_WEIGHTS.values()) * 12
        monthly_cogs_base = (annual_revenue * 0.65 / 12) * cost_season

        cost_pcs = ["PC-RP", "PC-SC", "PC-CI"]
        cost_prods = [p["product_id"] for p in PRODUCTS[:6]]  # Engine oils + transmission

        for gl_id, cogs_pct in cogs_accounts:
            cogs_amount = monthly_cogs_base * cogs_pct

            # ── SCENARIO 1: Base Oil cost spike Q4 2025 + Q1 2026 ──
            if gl_id == "GL-C100":
                if yr == 2025 and qtr == 4:
                    cogs_amount *= 1.22  # +22% spike
                elif yr == 2026:
                    cogs_amount *= 1.18  # Elevated but easing

            # Normal +2% inflation on other COGS in 2025+
            if gl_id != "GL-C100" and yr >= 2025:
                cogs_amount *= 1.02

            # Distribute across profit centers and products
            n_splits = len(cost_pcs) * 3  # ~9 txns per COGS account
            splits = _random_splits(n_splits, cogs_amount)
            for i, amt in enumerate(splits):
                rows.append(_make_txn(
                    gl_id=gl_id,
                    prod_id=cost_prods[i % len(cost_prods)],
                    cust_id="C-RP-01",
                    pc_id=cost_pcs[i % len(cost_pcs)],
                    ch_id="CH-DIY",
                    yr=yr, mo=mo, amt=-amt,
                ))

        # ────────────────────────────────────────────────────────
        # SG&A
        # ────────────────────────────────────────────────────────
        actual_monthly_revenue = monthly_revenue_base * sum(CHANNEL_REVENUE_WEIGHTS.values())
        sga_base = actual_monthly_revenue * 0.15  # SG&A ~15% of revenue

        sga_accounts = [
            ("GL-S100", 0.45),  # Sales & Marketing
            ("GL-S200", 0.27),  # Brand & Advertising
            ("GL-S300", 0.28),  # G&A
        ]
        sga_pcs = ["PC-CO", "PC-RP", "PC-SC"]

        for gl_id, sga_pct in sga_accounts:
            sga_amount = sga_base * sga_pct

            # ── SCENARIO 3: Marketing overspend in 2025 ──
            if gl_id == "GL-S100" and yr == 2025:
                sga_amount *= 1.16  # +16% over budget

            # Distribute across profit centers (3 txns per account)
            splits = _random_splits(3, sga_amount)
            for i, amt in enumerate(splits):
                rows.append(_make_txn(
                    gl_id=gl_id,
                    prod_id="P-CH-01",
                    cust_id="C-RP-01",
                    pc_id=sga_pcs[i % len(sga_pcs)],
                    ch_id="CH-DIY",
                    yr=yr, mo=mo, amt=-amt,
                ))

        # ────────────────────────────────────────────────────────
        # Other (D&A, Interest, Tax)
        # ────────────────────────────────────────────────────────
        other_accounts = [
            ("GL-O100", actual_monthly_revenue * 0.03),
            ("GL-O200", actual_monthly_revenue * 0.01),
            ("GL-O300", actual_monthly_revenue * 0.04),
        ]
        for gl_id, amount in other_accounts:
            rows.append(_make_txn(
                gl_id=gl_id, prod_id="P-EO-FS", cust_id="C-RP-01",
                pc_id="PC-CO", ch_id="CH-DIY",
                yr=yr, mo=mo, amt=-amount,
            ))

        # ────────────────────────────────────────────────────────
        # BUDGET  (version=Budget, no anomalies)
        # ────────────────────────────────────────────────────────
        budget_monthly = base_monthly_revenue * (1.05 if yr >= 2025 else 1.0) * season

        # Budget revenue lines
        for gl_id, pct in [("GL-R100", 0.87), ("GL-R200", 0.13)]:
            rows.append(_make_txn(
                gl_id=gl_id, prod_id="P-EO-FS", cust_id="C-RP-01",
                pc_id="PC-RP" if gl_id == "GL-R100" else "PC-SC",
                ch_id="CH-DIY", yr=yr, mo=mo,
                amt=budget_monthly * pct, version="Budget",
            ))
        # Budget COGS (stable base oil assumed)
        rows.append(_make_txn(
            gl_id="GL-C100", prod_id="P-EO-FS", cust_id="C-RP-01",
            pc_id="PC-RP", ch_id="CH-DIY", yr=yr, mo=mo,
            amt=-(budget_monthly * 0.65 * 0.40), version="Budget",
        ))
        # Budget SG&A
        rows.append(_make_txn(
            gl_id="GL-S100", prod_id="P-EO-FS", cust_id="C-RP-01",
            pc_id="PC-CO", ch_id="CH-DIY", yr=yr, mo=mo,
            amt=-(budget_monthly * 0.15 * 0.45), version="Budget",
        ))

        # Move to next month
        if mo == 12:
            current = date(yr + 1, 1, 1)
        else:
            current = date(yr, mo + 1, 1)

    print(f"Generated {len(rows)} transactions ({txn_counter} IDs)")
    return rows


def _random_splits(n: int, total: float) -> List[float]:
    """Split total into n random-ish amounts summing to total."""
    weights = [random.uniform(0.5, 1.5) for _ in range(n)]
    total_w = sum(weights)
    return [total * w / total_w for w in weights]


# ---------------------------------------------------------------------------
# BigQuery upload
# ---------------------------------------------------------------------------

def upload_to_bigquery(dry_run: bool = False):
    """Generate all data and upload to BigQuery."""
    from google.cloud import bigquery as bq

    # Build DataFrames
    gl_df = pd.DataFrame(GL_ACCOUNTS)
    products_df = pd.DataFrame(PRODUCTS)
    customers_df = pd.DataFrame(CUSTOMERS)
    profit_centers_df = pd.DataFrame(PROFIT_CENTERS)
    channels_df = pd.DataFrame(CHANNELS)

    print("Generating transactions...")
    txn_rows = generate_transactions()
    txn_df = pd.DataFrame(txn_rows)

    if dry_run:
        actual = txn_df[txn_df["version"] == "Actual"]
        print(f"\n{'='*60}")
        print(f"DRY RUN SUMMARY")
        print(f"{'='*60}")
        print(f"Tables: GLAccounts={len(gl_df)}, Products={len(products_df)}, "
              f"Customers={len(customers_df)}, ProfitCenters={len(profit_centers_df)}, "
              f"Channels={len(channels_df)}")
        print(f"FinancialTransactions: {len(txn_df)} total ({len(actual)} actual + "
              f"{len(txn_df)-len(actual)} budget)")

        # Revenue & Gross Margin by year
        print(f"\n--- Annual P&L (Actual) ---")
        for yr in sorted(actual["fiscal_year"].unique()):
            yr_data = actual[actual["fiscal_year"] == yr]
            rev = yr_data[yr_data["amount"] > 0]["amount"].sum()
            cogs = yr_data[yr_data["gl_account_id"].str.startswith("GL-C")]["amount"].sum()
            gp = rev + cogs  # cogs is negative
            gm = gp / rev * 100 if rev else 0
            sga = yr_data[yr_data["gl_account_id"].str.startswith("GL-S")]["amount"].sum()
            print(f"  {yr}: Rev=${rev/1e6:,.0f}M, COGS=${-cogs/1e6:,.0f}M, "
                  f"GP=${gp/1e6:,.0f}M ({gm:.1f}%), SGA=${-sga/1e6:,.0f}M")

        # Scenario 1: COGS by quarter (Q3 vs Q4 2025)
        print(f"\n--- Scenario 1: COGS by Quarter (Base Oil Spike) ---")
        for yr in [2024, 2025, 2026]:
            yr_cogs = actual[(actual["fiscal_year"] == yr) & actual["gl_account_id"].str.startswith("GL-C")]
            for q in range(1, 5):
                q_months = [str(m).zfill(3) for m in range((q-1)*3+1, q*3+1)]
                q_data = yr_cogs[yr_cogs["fiscal_period"].isin(q_months)]
                if len(q_data) > 0:
                    total = -q_data["amount"].sum()
                    base_oil = -q_data[q_data["gl_account_id"] == "GL-C100"]["amount"].sum()
                    print(f"  {yr} Q{q}: Total COGS=${total/1e6:,.0f}M, "
                          f"Base Oil=${base_oil/1e6:,.0f}M")

        # Scenario 2: Service Center revenue YoY
        print(f"\n--- Scenario 2: Service Center Revenue ---")
        for yr in sorted(actual["fiscal_year"].unique()):
            sc_rev = actual[(actual["fiscal_year"] == yr) & (actual["channel_id"] == "CH-DIFM") & (actual["amount"] > 0)]["amount"].sum()
            print(f"  {yr}: DIFM Revenue=${sc_rev/1e6:,.0f}M")

        # Scenario 4: Fleet Customer A
        print(f"\n--- Scenario 4: Fleet Customer A Revenue ---")
        for yr in sorted(actual["fiscal_year"].unique()):
            fa_rev = actual[(actual["fiscal_year"] == yr) & (actual["customer_id"] == "C-FL-01") & (actual["amount"] > 0)]["amount"].sum()
            print(f"  {yr}: Fleet A=${fa_rev/1e6:,.0f}M")

        # Scenario 5: E-Commerce
        print(f"\n--- Scenario 5: E-Commerce Revenue ---")
        for yr in sorted(actual["fiscal_year"].unique()):
            ec_rev = actual[(actual["fiscal_year"] == yr) & (actual["channel_id"] == "CH-ECOM") & (actual["amount"] > 0)]["amount"].sum()
            print(f"  {yr}: E-Commerce=${ec_rev/1e6:,.0f}M")

        # Channel breakdown for latest full year
        print(f"\n--- 2025 Revenue by Channel ---")
        yr_data = actual[(actual["fiscal_year"] == 2025) & (actual["amount"] > 0)]
        for ch in sorted(yr_data["channel_id"].unique()):
            ch_rev = yr_data[yr_data["channel_id"] == ch]["amount"].sum()
            print(f"  {ch}: ${ch_rev/1e6:,.0f}M")

        return

    # Connect to BigQuery
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS not set", file=sys.stderr)
        sys.exit(1)

    client = bq.Client(project=PROJECT_ID)

    # Create dataset if needed
    dataset_ref = bq.DatasetReference(PROJECT_ID, DATASET_ID)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {DATASET_ID} already exists")
    except Exception:
        dataset = bq.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Created dataset {DATASET_ID}")

    # Upload tables
    tables = {
        "GLAccounts": gl_df,
        "Products": products_df,
        "Customers": customers_df,
        "ProfitCenters": profit_centers_df,
        "Channels": channels_df,
        "FinancialTransactions": txn_df,
    }

    for table_name, df in tables.items():
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        print(f"Uploading {table_name} ({len(df)} rows)...")

        job_config = bq.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait
        print(f"  -> {table_name} uploaded successfully")

    # Create star schema view
    view_sql = f"""
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}` AS
SELECT
  ft.transaction_id,
  ft.fiscal_year, ft.fiscal_period, ft.transaction_date,
  ft.amount, ft.version, ft.currency,
  gl.account_name, gl.account_type, gl.account_category, gl.account_group,
  p.product_name, p.product_line, p.product_category,
  c.customer_name, c.customer_segment, c.customer_region,
  pc.profit_center_name, pc.business_unit,
  ch.channel_name, ch.channel_type
FROM `{PROJECT_ID}.{DATASET_ID}.FinancialTransactions` ft
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.GLAccounts` gl ON ft.gl_account_id = gl.gl_account_id
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.Products` p ON ft.product_id = p.product_id
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.Customers` c ON ft.customer_id = c.customer_id
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.ProfitCenters` pc ON ft.profit_center_id = pc.profit_center_id
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.Channels` ch ON ft.channel_id = ch.channel_id
"""
    print(f"Creating view {VIEW_NAME}...")
    client.query(view_sql).result()
    print(f"  -> View created successfully")

    # Verify
    count_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`"
    result = client.query(count_query).result()
    for row in result:
        print(f"\nVerification: {VIEW_NAME} has {row.cnt} rows")

    print(f"\nDone! Dataset: {PROJECT_ID}.{DATASET_ID}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate Lubricants Business demo data for BigQuery")
    parser.add_argument("--dry-run", action="store_true", help="Generate data locally without uploading")
    args = parser.parse_args()

    upload_to_bigquery(dry_run=args.dry_run)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
