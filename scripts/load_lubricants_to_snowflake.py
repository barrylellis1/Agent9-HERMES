#!/usr/bin/env python3
"""
Load Lubricants demo data into Snowflake.

Re-uses the same dimension data and transaction generator from
generate_lubricants_demo_data.py but targets Snowflake instead of BigQuery.

Uses externalbrowser auth — a browser tab will open for SSO login.

Usage:
    .venv/Scripts/python scripts/load_lubricants_to_snowflake.py [--dry-run]
"""

import argparse
import sys
import os

# Add project root to path so we can import the generator
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.generate_lubricants_demo_data import (
    GL_ACCOUNTS, PRODUCTS, CUSTOMERS, PROFIT_CENTERS, CHANNELS,
    generate_transactions,
)

# ---------------------------------------------------------------------------
# Snowflake connection config
# ---------------------------------------------------------------------------
SF_ACCOUNT = "VSGHWKW-SI38932"
SF_USER = "BARRYLELLIS1"
SF_DATABASE = "AGENT9_DEMO"
SF_SCHEMA = "LUBRICANTS"
SF_WAREHOUSE = "AGENT9_WH"
SF_ROLE = "ACCOUNTADMIN"


def load_to_snowflake(dry_run: bool = False):
    """Generate data and load into Snowflake."""
    import snowflake.connector

    # ── Generate transactions ──
    print("Generating transactions...")
    transactions = generate_transactions()
    print(f"  Generated {len(transactions)} transactions")

    if dry_run:
        print("\n[DRY RUN] Would load:")
        print(f"  GLAccounts:            {len(GL_ACCOUNTS)} rows")
        print(f"  Products:              {len(PRODUCTS)} rows")
        print(f"  Customers:             {len(CUSTOMERS)} rows")
        print(f"  ProfitCenters:         {len(PROFIT_CENTERS)} rows")
        print(f"  Channels:              {len(CHANNELS)} rows")
        print(f"  FinancialTransactions: {len(transactions)} rows")
        print("\nSample transaction:", transactions[0])
        return

    # ── Connect to Snowflake (password auth via env var) ──
    sf_password = os.environ.get("SF_PASSWORD") or os.environ.get("SNOWFLAKE_PASSWORD", "")
    if not sf_password:
        print("\nError: Set SF_PASSWORD (or SNOWFLAKE_PASSWORD) environment variable first.")
        print("  Windows: set SF_PASSWORD=your_password")
        print("  Bash:    export SF_PASSWORD=your_password")
        sys.exit(1)

    print(f"\nConnecting to Snowflake ({SF_ACCOUNT})...")
    conn = snowflake.connector.connect(
        account=SF_ACCOUNT,
        user=SF_USER,
        password=sf_password,
        database=SF_DATABASE,
        schema=SF_SCHEMA,
        warehouse=SF_WAREHOUSE,
        role=SF_ROLE,
    )
    cur = conn.cursor()
    print("  Connected!")

    try:
        # ── Truncate existing data (idempotent reload) ──
        print("\nClearing existing data...")
        # Order matters due to FK constraints
        cur.execute("TRUNCATE TABLE IF EXISTS FinancialTransactions")
        cur.execute("TRUNCATE TABLE IF EXISTS GLAccounts")
        cur.execute("TRUNCATE TABLE IF EXISTS Products")
        cur.execute("TRUNCATE TABLE IF EXISTS Customers")
        cur.execute("TRUNCATE TABLE IF EXISTS ProfitCenters")
        cur.execute("TRUNCATE TABLE IF EXISTS Channels")
        print("  Cleared.")

        # ── Load dimension tables ──
        print("\nLoading dimension tables...")

        # GLAccounts
        cur.executemany(
            "INSERT INTO GLAccounts (gl_account_id, account_name, account_type, account_category, account_group) "
            "VALUES (%s, %s, %s, %s, %s)",
            [(r["gl_account_id"], r["account_name"], r["account_type"],
              r["account_category"], r["account_group"]) for r in GL_ACCOUNTS]
        )
        print(f"  GLAccounts:    {len(GL_ACCOUNTS)} rows")

        # Products
        cur.executemany(
            "INSERT INTO Products (product_id, product_name, product_line, product_category) "
            "VALUES (%s, %s, %s, %s)",
            [(r["product_id"], r["product_name"], r["product_line"],
              r["product_category"]) for r in PRODUCTS]
        )
        print(f"  Products:      {len(PRODUCTS)} rows")

        # Customers
        cur.executemany(
            "INSERT INTO Customers (customer_id, customer_name, customer_segment, customer_region) "
            "VALUES (%s, %s, %s, %s)",
            [(r["customer_id"], r["customer_name"], r["customer_segment"],
              r["customer_region"]) for r in CUSTOMERS]
        )
        print(f"  Customers:     {len(CUSTOMERS)} rows")

        # ProfitCenters
        cur.executemany(
            "INSERT INTO ProfitCenters (profit_center_id, profit_center_name, business_unit) "
            "VALUES (%s, %s, %s)",
            [(r["profit_center_id"], r["profit_center_name"],
              r["business_unit"]) for r in PROFIT_CENTERS]
        )
        print(f"  ProfitCenters: {len(PROFIT_CENTERS)} rows")

        # Channels
        cur.executemany(
            "INSERT INTO Channels (channel_id, channel_name, channel_type) "
            "VALUES (%s, %s, %s)",
            [(r["channel_id"], r["channel_name"],
              r["channel_type"]) for r in CHANNELS]
        )
        print(f"  Channels:      {len(CHANNELS)} rows")

        # ── Load fact table in batches ──
        print(f"\nLoading FinancialTransactions ({len(transactions)} rows)...")
        BATCH_SIZE = 5000
        insert_sql = (
            "INSERT INTO FinancialTransactions "
            "(transaction_id, fiscal_year, fiscal_period, transaction_date, "
            "gl_account_id, product_id, customer_id, profit_center_id, channel_id, "
            "amount, version, currency) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        )

        for i in range(0, len(transactions), BATCH_SIZE):
            batch = transactions[i:i + BATCH_SIZE]
            rows = [
                (r["transaction_id"], r["fiscal_year"], r["fiscal_period"],
                 r["transaction_date"], r["gl_account_id"], r["product_id"],
                 r["customer_id"], r["profit_center_id"], r["channel_id"],
                 r["amount"], r["version"], r["currency"])
                for r in batch
            ]
            cur.executemany(insert_sql, rows)
            loaded = min(i + BATCH_SIZE, len(transactions))
            print(f"  {loaded}/{len(transactions)} rows loaded...")

        # ── Create/replace the star schema view ──
        print("\nCreating LubricantsStarSchemaView...")
        cur.execute("""
CREATE OR REPLACE VIEW LubricantsStarSchemaView AS
SELECT
    ft.transaction_id,
    ft.fiscal_year,
    ft.fiscal_period,
    ft.transaction_date,
    ft.amount,
    ft.version,
    ft.currency,
    gl.account_name,
    gl.account_type,
    gl.account_category,
    gl.account_group,
    p.product_name,
    p.product_line,
    p.product_category,
    c.customer_name,
    c.customer_segment,
    c.customer_region,
    pc.profit_center_name,
    pc.business_unit,
    ch.channel_name,
    ch.channel_type
FROM        FinancialTransactions    ft
LEFT JOIN   GLAccounts              gl  ON ft.gl_account_id    = gl.gl_account_id
LEFT JOIN   Products                p   ON ft.product_id       = p.product_id
LEFT JOIN   Customers               c   ON ft.customer_id      = c.customer_id
LEFT JOIN   ProfitCenters           pc  ON ft.profit_center_id = pc.profit_center_id
LEFT JOIN   Channels                ch  ON ft.channel_id       = ch.channel_id
        """)
        print("  LubricantsStarSchemaView created.")

        # ── Verify ──
        print("\nVerifying...")
        cur.execute("SELECT COUNT(*) FROM LubricantsStarSchemaView")
        count = cur.fetchone()[0]
        print(f"  LubricantsStarSchemaView: {count} rows")

        cur.execute("SELECT COUNT(DISTINCT fiscal_year) FROM FinancialTransactions")
        years = cur.fetchone()[0]
        print(f"  Fiscal years: {years}")

        cur.execute("SELECT fiscal_year, COUNT(*) FROM FinancialTransactions GROUP BY fiscal_year ORDER BY fiscal_year")
        for row in cur.fetchall():
            print(f"    {row[0]}: {row[1]} transactions")

        print("\nDone! Snowflake lubricants data loaded successfully.")

    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Load lubricants demo data to Snowflake")
    parser.add_argument("--dry-run", action="store_true", help="Generate data without uploading")
    args = parser.parse_args()
    load_to_snowflake(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
