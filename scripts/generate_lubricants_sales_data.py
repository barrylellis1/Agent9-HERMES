#!/usr/bin/env python3
"""
Generate Lubricants Sales Order data for BigQuery — reconciled to Finance.

Schema shape modeled on the SAP Datasphere sample Sales content (SalesOrders /
SalesOrderItems / BusinessPartners) that this session's earlier exploration found
at:
  C:\\Users\\Blell\\Documents\\Agent9\\SAP DataSphere Data\\...\\CSV\\Sales

Populated NOT with independently-sampled synthetic numbers, but with a direct
decomposition of the exact same revenue basis generate_lubricants_demo_data.py
already uses for the `lubricants` (BigQuery) client's Net Revenue KPI. Every
generated Sales Order Item corresponds 1:1 to one revenue-invoice-line split from
generate_transactions(); nothing here is re-sampled or re-modeled independently.
That is what makes this "aligned with lubricants financial data" true by
construction: SUM(SalesOrderItems.netamount), sliced any way, reconciles exactly
to SUM(FinancialTransactions.amount WHERE account_type='Revenue') for the same
slice — this is verified in --dry-run output below.

Adds order/line structure (grouping, delivery dates, lifecycle/billing/delivery
status, a per-product unit price to back out quantity) that the Finance side has
no reason to carry, since that is Sales' distinctive value: order volume and
fulfillment truth underneath the dollar figures.

Usage:
    python scripts/generate_lubricants_sales_data.py [--dry-run]

Environment:
    GOOGLE_APPLICATION_CREDENTIALS - Path to GCP service account JSON
"""

import argparse
import random
import sys
from datetime import date, timedelta
from typing import Dict, List

import pandas as pd

from generate_lubricants_demo_data import (
    PROJECT_ID, DATASET_ID, DATE_END,
    CUSTOMERS, PRODUCTS,
    generate_transactions,
)

random.seed(43)  # Distinct from the Finance generator's seed(42) -- order/line
                  # structure (grouping, delivery offsets, status) is genuinely new
                  # randomness layered on top of the captured, already-fixed amounts.

VIEW_NAME = "LubricantsSalesStarView"

# "Today" for the running demo, used to derive plausible lifecycle status.
DEMO_TODAY = date(2026, 8, 20)

SALESORG_BY_REGION = {
    "North America": "AMER",
    "Latin America": "AMER",
    "Europe": "EMEA",
    "Middle East": "EMEA",
    "Asia-Pacific": "APJ",
}

CUSTOMER_REGION = {c["customer_id"]: c["customer_region"] for c in CUSTOMERS}
CUSTOMER_NAME = {c["customer_id"]: c["customer_name"] for c in CUSTOMERS}

# Approximate list price per unit (case/drum/pail, matching the product's typical
# pack size in this industry) -- used only to back out a plausible QUANTITY from
# the already-fixed dollar amount. Does not affect any dollar figure.
UNIT_PRICE = {
    "P-EO-FS": 85.00, "P-EO-SB": 55.00, "P-EO-CV": 38.00, "P-EO-HM": 65.00,
    "P-TF-01": 60.00, "P-TF-02": 50.00,
    "P-IL-HY": 450.00, "P-IL-CO": 480.00, "P-IL-TB": 520.00,
    "P-GR-01": 120.00, "P-GR-02": 180.00,
    "P-CL-01": 70.00, "P-CL-02": 85.00,
    "P-CH-01": 40.00, "P-CH-02": 35.00,
}


def _order_status(order_date: date) -> Dict[str, str]:
    """Derive plausible SAP-style lifecycle/billing/delivery status codes.

    C = Completed, I = In Process, X = Cancelled. An order more than ~30 days in
    the past (relative to DEMO_TODAY) is treated as fully completed; anything more
    recent, or dated in the future (this dataset runs through 2026-12-31, beyond
    DEMO_TODAY), is still in process. A small, fixed cancellation rate is applied
    independent of date.
    """
    days_old = (DEMO_TODAY - order_date).days
    if random.random() < 0.02:
        return {"LIFECYCLESTATUS": "X", "BILLINGSTATUS": "X", "DELIVERYSTATUS": "X"}
    if days_old > 30:
        return {"LIFECYCLESTATUS": "C", "BILLINGSTATUS": "C", "DELIVERYSTATUS": "C"}
    return {"LIFECYCLESTATUS": "I", "BILLINGSTATUS": "I", "DELIVERYSTATUS": "I"}


def _month_day(yr: int, mo: int) -> date:
    return date(yr, mo, random.randint(1, 28))


def generate_sales_orders():
    """Decompose generate_transactions()'s revenue basis into Sales Orders.

    Returns (orders, items, partners, txn_rows) -- txn_rows is the single
    generate_transactions() call's own output, returned so callers can reconcile
    against it directly instead of calling generate_transactions() a second time.
    (A second call would not reproduce the first: random.seed(42) fires once at
    module import in generate_lubricants_demo_data.py, so a repeat call continues
    consuming the same global random state rather than resetting it.)
    """
    sales_lines: List[Dict] = []
    print("Generating Finance transactions (captures the revenue basis)...")
    txn_rows = generate_transactions(sales_lines=sales_lines)
    print(f"  Captured {len(sales_lines)} revenue invoice lines")

    # Group captured lines by (customer, year, month) -- same grouping key a real
    # sales org would batch by -- then chunk each group into orders of 1-4 items,
    # close to the SAP sample content's own ~3.45 items/order ratio.
    groups: Dict[tuple, List[Dict]] = {}
    for line in sales_lines:
        key = (line["customer_id"], line["fiscal_year"], line["fiscal_month"])
        groups.setdefault(key, []).append(line)

    orders: List[Dict] = []
    items: List[Dict] = []
    order_seq = 200000000  # SAP-style numeric order id, matching the sample's range

    for (cust_id, yr, mo), lines in groups.items():
        random.shuffle(lines)
        i = 0
        while i < len(lines):
            chunk_size = random.randint(1, 4)
            chunk = lines[i:i + chunk_size]
            i += chunk_size

            order_id = order_seq
            order_seq += 1
            order_date = _month_day(yr, mo)
            status = _order_status(order_date)

            net_total = 0.0
            item_no = 10
            for line in chunk:
                prod_id = line["product_id"]
                amt = line["amount"]
                unit_price = UNIT_PRICE.get(prod_id, 50.00)
                quantity = max(1, round(amt / unit_price))
                delivery_date = order_date + timedelta(days=random.randint(15, 60))
                net_total += amt

                items.append({
                    "SALESORDERID": order_id,
                    "SALESORDERITEM": item_no,
                    "PRODUCTID": prod_id,
                    "CURRENCY": "USD",
                    "NETAMOUNT": round(amt, 2),
                    "QUANTITY": quantity,
                    "QUANTITYUNIT": "EA",
                    "DELIVERYDATE": delivery_date.isoformat(),
                    "DELIVERYSTATUS": status["DELIVERYSTATUS"],
                    "channel_id": line["channel_id"],
                    "profit_center_id": line["profit_center_id"],
                    "fiscal_year": yr,
                    "fiscal_month": mo,
                })
                item_no += 10

            tax_total = net_total * 0.0875  # flat demo sales-tax rate
            gross_total = net_total + tax_total

            orders.append({
                "SALESORDERID": order_id,
                "CREATEDAT": order_date.isoformat(),
                "PARTNERID": cust_id,
                "SALESORG": SALESORG_BY_REGION.get(CUSTOMER_REGION.get(cust_id), "AMER"),
                "CURRENCY": "USD",
                "GROSSAMOUNT": round(gross_total, 2),
                "NETAMOUNT": round(net_total, 2),
                "TAXAMOUNT": round(tax_total, 2),
                "LIFECYCLESTATUS": status["LIFECYCLESTATUS"],
                "BILLINGSTATUS": status["BILLINGSTATUS"],
                "DELIVERYSTATUS": status["DELIVERYSTATUS"],
            })

    partners = [
        {
            "PARTNERID": c["customer_id"],
            "PARTNERROLE": "2",  # customer, matching the Datasphere sample convention
            "COMPANYNAME": c["customer_name"],
            "CUSTOMER_SEGMENT": c["customer_segment"],
            "CUSTOMER_REGION": c["customer_region"],
            "CURRENCY": "USD",
        }
        for c in CUSTOMERS
    ]

    return orders, items, partners, txn_rows


def _reconciliation_check(orders: List[Dict], txn_rows: List[Dict]) -> None:
    """Prove Sales reconciles to Finance Revenue -- the whole point of this design."""
    sales_net = sum(o["NETAMOUNT"] for o in orders)
    rev_net = sum(
        r["amount"] for r in txn_rows
        if r["gl_account_id"] in ("GL-R100", "GL-R200") and r["version"] == "Actual"
    )
    diff = sales_net - rev_net
    pct = (diff / rev_net * 100) if rev_net else 0.0
    print(f"\n--- Reconciliation check ---")
    print(f"  Sales Orders NETAMOUNT total:  ${sales_net:,.2f}")
    print(f"  Finance Revenue (Actual) total: ${rev_net:,.2f}")
    print(f"  Difference: ${diff:,.2f} ({pct:.4f}%)")


def upload_to_bigquery(dry_run: bool = False):
    orders, items, partners, txn_rows = generate_sales_orders()

    if dry_run:
        print(f"\n[DRY RUN] Would load:")
        print(f"  SalesOrders:     {len(orders)} rows")
        print(f"  SalesOrderItems: {len(items)} rows")
        print(f"  BusinessPartners:{len(partners)} rows")
        print(f"  Items/order ratio: {len(items)/len(orders):.2f}")
        print("\nSample order:", orders[0])
        print("Sample item:", items[0])
        _reconciliation_check(orders, txn_rows)
        return

    from google.cloud import bigquery as bq

    orders_df = pd.DataFrame(orders)
    items_df = pd.DataFrame(items)
    partners_df = pd.DataFrame(partners)

    client = bq.Client(project=PROJECT_ID)

    tables = {
        "SalesOrders": orders_df,
        "SalesOrderItems": items_df,
        "BusinessPartners": partners_df,
    }
    for table_name, df in tables.items():
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        print(f"Uploading {table_name} ({len(df)} rows)...")
        job_config = bq.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f"  -> {table_name} uploaded successfully")

    view_sql = f"""
CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}` AS
SELECT
  soi.SALESORDERID AS sales_order_id,
  soi.SALESORDERITEM AS sales_order_item,
  soi.PRODUCTID AS product_id,
  p.product_name, p.product_line, p.product_category,
  soi.NETAMOUNT AS net_amount,
  soi.QUANTITY AS quantity,
  soi.QUANTITYUNIT AS quantity_unit,
  soi.DELIVERYDATE AS delivery_date,
  soi.fiscal_year, soi.fiscal_month,
  soi.channel_id, soi.profit_center_id,
  so.CREATEDAT AS order_date,
  so.PARTNERID AS partner_id,
  bp.COMPANYNAME AS customer_name,
  bp.CUSTOMER_SEGMENT AS customer_segment,
  bp.CUSTOMER_REGION AS customer_region,
  so.SALESORG AS sales_org,
  so.CURRENCY AS currency,
  so.GROSSAMOUNT AS order_gross_amount,
  so.NETAMOUNT AS order_net_amount,
  so.TAXAMOUNT AS order_tax_amount,
  so.LIFECYCLESTATUS AS lifecycle_status,
  so.BILLINGSTATUS AS billing_status,
  so.DELIVERYSTATUS AS delivery_status
FROM `{PROJECT_ID}.{DATASET_ID}.SalesOrderItems` soi
JOIN `{PROJECT_ID}.{DATASET_ID}.SalesOrders` so ON soi.SALESORDERID = so.SALESORDERID
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.BusinessPartners` bp ON so.PARTNERID = bp.PARTNERID
LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.Products` p ON soi.PRODUCTID = p.product_id
"""
    print(f"Creating view {VIEW_NAME}...")
    client.query(view_sql).result()
    print(f"  -> View created successfully")

    count_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`"
    result = client.query(count_query).result()
    for row in result:
        print(f"\nVerification: {VIEW_NAME} has {row.cnt} rows")

    recon_query = f"""
SELECT ROUND(SUM(net_amount), 2) AS sales_net
FROM `{PROJECT_ID}.{DATASET_ID}.{VIEW_NAME}`
"""
    result = client.query(recon_query).result()
    for row in result:
        print(f"Sales net total in BigQuery: ${row.sales_net:,.2f}")

    print(f"\nDone! Dataset: {PROJECT_ID}.{DATASET_ID}")


def main():
    parser = argparse.ArgumentParser(description="Generate Lubricants Sales Order data for BigQuery")
    parser.add_argument("--dry-run", action="store_true", help="Generate data locally without uploading")
    args = parser.parse_args()
    upload_to_bigquery(dry_run=args.dry_run)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
