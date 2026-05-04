#!/usr/bin/env python3
"""
Fix bicycle client isolation in Supabase.

Migration 0007 stamped DEFAULT 'lubricants' on every pre-existing row, so all
bicycle KPIs, the bicycle data product, and the original generic principals have
client_id='lubricants'. This script corrects that.

What it does:
  1. Reports current state (always runs)
  2. Updates bicycle KPIs (data_product_id='fi_star_schema') → client_id='bicycle'
  3. Updates bicycle data product (id='fi_star_schema') → client_id='bicycle'
  4. Upserts two bicycle principals (bi_cfo_001, bi_finance_001)
     with business_process_ids aligned to the bicycle KPI BPs found in step 1

Usage:
    python scripts/fix_bicycle_client_isolation.py [--dry-run]

Environment:
    SUPABASE_URL               - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY  - Service role key (admin access)
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

import httpx


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

def _headers(service_key: str) -> Dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }


def _fetch(client: httpx.Client, url: str, headers: Dict[str, str],
           table: str, filters: Optional[str] = None) -> List[Dict[str, Any]]:
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    params = {}
    if filters:
        # filters is a raw query string, e.g. "data_product_id=eq.fi_star_schema"
        for part in filters.split("&"):
            k, v = part.split("=", 1)
            params[k] = v
    params["select"] = "*"
    resp = client.get(endpoint, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()


def _delete(client: httpx.Client, url: str, headers: Dict[str, str],
            table: str, filters: str) -> List[Dict[str, Any]]:
    """Delete rows matching filters. Returns deleted rows."""
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    params = {}
    for part in filters.split("&"):
        k, v = part.split("=", 1)
        params[k] = v
    del_headers = {**headers, "Prefer": "return=representation"}
    resp = client.delete(endpoint, headers=del_headers, params=params)
    resp.raise_for_status()
    return resp.json()


def _insert(client: httpx.Client, url: str, headers: Dict[str, str],
            table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Insert rows (no conflict resolution — rows must not already exist)."""
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    ins_headers = {**headers, "Prefer": "return=representation"}
    resp = client.post(endpoint, headers=ins_headers, json=rows)
    resp.raise_for_status()
    return resp.json()


def _upsert(client: httpx.Client, url: str, headers: Dict[str, str],
            table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Upsert rows using composite PK conflict resolution."""
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    upsert_headers = {
        **headers,
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    resp = client.post(endpoint, headers=upsert_headers, json=rows)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Bicycle principals
# ---------------------------------------------------------------------------

BICYCLE_PRINCIPALS = [
    {
        "id": "bi_cfo_001",
        "client_id": "bicycle",
        "name": "Alex Morgan",
        "first_name": "Alex",
        "last_name": "Morgan",
        "title": "Chief Financial Officer",
        "role": "CFO",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "CFO responsible for financial performance of Global Bike Inc. "
            "Key focus areas: revenue growth across product lines and channels, "
            "gross margin management, and operating expense discipline."
        ),
        "responsibilities": [
            "maximize operating profit",
            "manage revenue across product lines and channels",
            "control COGS and SG&A expenses",
            "oversee divisional P&L reporting",
        ],
        # Business process IDs — using standard IDs that match bicycle KPI BPs.
        # If bicycle KPIs use different IDs (detected in step 1), update this list
        # and re-run the script.
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth",
            "finance_expense_management",
            "finance_budget_vs_actuals",
        ],
        "default_filters": {
            "Fiscal Year": ["2024", "2025"],
        },
        "typical_timeframes": ["Monthly", "Quarterly"],
        "principal_groups": ["Executive Leadership", "Finance Committee"],
        "persona_profile": {
            "decision_style": "analytical",
            "risk_tolerance": "moderate",
            "communication_style": "concise",
            "values": ["accuracy", "growth", "efficiency"],
        },
        "preferences": {"channel": "email", "ui": "summary_dashboard"},
        "permissions": ["finance_read", "finance_write"],
        "metadata": {
            "kpi_line_preference": "bottom_line_first",
            "kpi_altitude_preference": "strategic_first",
        },
    },
    {
        "id": "bi_finance_001",
        "client_id": "bicycle",
        "name": "Jordan Lee",
        "first_name": "Jordan",
        "last_name": "Lee",
        "title": "Finance Manager",
        "role": "Finance Manager",
        "department": "Finance",
        "source": "HR Database",
        "description": (
            "Finance Manager supporting financial operations and reporting for Global Bike Inc."
        ),
        "responsibilities": [
            "financial reporting and variance analysis",
            "budget management",
            "cost control and SG&A tracking",
        ],
        "business_process_ids": [
            "finance_profitability_analysis",
            "finance_revenue_growth",
            "finance_expense_management",
            "finance_budget_vs_actuals",
            "finance_cash_flow_management",
        ],
        "default_filters": {
            "Fiscal Year": ["2024", "2025"],
        },
        "typical_timeframes": ["Monthly", "Quarterly"],
        "principal_groups": ["Finance Committee"],
        "persona_profile": {
            "decision_style": "analytical",
            "risk_tolerance": "low",
            "communication_style": "detailed",
            "values": ["accuracy", "compliance", "predictability"],
        },
        "preferences": {"channel": "email", "ui": "detail_view"},
        "permissions": ["finance_read"],
        "metadata": {
            "kpi_line_preference": "balanced",
            "kpi_altitude_preference": "operational_first",
        },
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Fix bicycle client isolation in Supabase")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change without writing to Supabase")
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        sys.exit(1)

    dry = args.dry_run
    headers = _headers(service_key)

    with httpx.Client(timeout=30.0) as http:

        # ------------------------------------------------------------------
        # Step 1: Report current state
        # ------------------------------------------------------------------
        print("=" * 60)
        print("STEP 1 — Current state")
        print("=" * 60)

        bicycle_kpis = _fetch(http, supabase_url, headers, "kpis",
                               "data_product_id=eq.fi_star_schema")
        print(f"\nBicycle KPIs (data_product_id='fi_star_schema'): {len(bicycle_kpis)}")
        client_ids_found = set(k.get("client_id") for k in bicycle_kpis)
        print(f"  client_id values in DB: {client_ids_found}")

        # Collect all BP IDs used by bicycle KPIs
        all_bp_ids: set = set()
        for kpi in bicycle_kpis:
            bp_ids = kpi.get("business_process_ids") or []
            all_bp_ids.update(bp_ids)
            needs_fix = kpi.get("client_id") != "bicycle"
            marker = "  [NEEDS FIX]" if needs_fix else ""
            print(f"  - {kpi['id']:30s}  client_id={kpi.get('client_id')!r:15s}  "
                  f"bps={kpi.get('business_process_ids')}{marker}")

        print(f"\n  Unique BP IDs across all bicycle KPIs: {sorted(all_bp_ids)}")

        bicycle_dps = _fetch(http, supabase_url, headers, "data_products",
                              "id=eq.fi_star_schema")
        print(f"\nBicycle data product (id='fi_star_schema'): {len(bicycle_dps)}")
        for dp in bicycle_dps:
            needs_fix = dp.get("client_id") != "bicycle"
            marker = "  [NEEDS FIX]" if needs_fix else ""
            print(f"  - {dp['id']}  client_id={dp.get('client_id')!r}{marker}")

        existing_bi_principals = _fetch(http, supabase_url, headers, "principal_profiles",
                                        "client_id=eq.bicycle")
        print(f"\nExisting bicycle principals (client_id='bicycle'): {len(existing_bi_principals)}")
        for p in existing_bi_principals:
            print(f"  - {p.get('id')}  name={p.get('name')}")

        if dry:
            print("\n[DRY RUN] No changes written.")
            print("\nWould update:")
            print(f"  - {len(bicycle_kpis)} KPIs → client_id='bicycle'")
            print(f"  - {len(bicycle_dps)} data product → client_id='bicycle'")
            print(f"  - Upsert {len(BICYCLE_PRINCIPALS)} bicycle principals")
            return

        # ------------------------------------------------------------------
        # Step 2: Re-key bicycle KPIs with client_id='bicycle'
        # (client_id is part of the composite PK — must delete + re-insert)
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("STEP 2 — Re-keying bicycle KPIs → client_id='bicycle'")
        print("=" * 60)

        if bicycle_kpis:
            # Delete existing rows (currently keyed under wrong client_id)
            deleted = _delete(http, supabase_url, headers, "kpis",
                              "data_product_id=eq.fi_star_schema")
            print(f"  Deleted {len(deleted)} KPI rows (old client_id keys)")

            # Re-insert with client_id='bicycle'
            new_kpis = [{**kpi, "client_id": "bicycle"} for kpi in bicycle_kpis]
            inserted = _insert(http, supabase_url, headers, "kpis", new_kpis)
            print(f"  Re-inserted {len(inserted)} KPIs with client_id='bicycle'")
        else:
            print("  No bicycle KPIs found (data_product_id='fi_star_schema') — nothing to update")

        # ------------------------------------------------------------------
        # Step 3: Re-key bicycle data product with client_id='bicycle'
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("STEP 3 — Re-keying bicycle data product → client_id='bicycle'")
        print("=" * 60)

        if bicycle_dps:
            deleted_dp = _delete(http, supabase_url, headers, "data_products",
                                 "id=eq.fi_star_schema")
            print(f"  Deleted {len(deleted_dp)} data product row(s)")

            new_dps = [{**dp, "client_id": "bicycle"} for dp in bicycle_dps]
            inserted_dp = _insert(http, supabase_url, headers, "data_products", new_dps)
            print(f"  Re-inserted {len(inserted_dp)} data product(s) with client_id='bicycle'")
        else:
            print("  Data product 'fi_star_schema' not found — may need to be seeded separately")

        # ------------------------------------------------------------------
        # Step 4: Upsert bicycle principals
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("STEP 4 — Upserting bicycle principals")
        print("=" * 60)

        result = _upsert(http, supabase_url, headers, "principal_profiles", BICYCLE_PRINCIPALS)
        print(f"  Upserted {len(result)} bicycle principals:")
        for p in result:
            print(f"    - {p.get('id')}  name={p.get('name')}  client_id={p.get('client_id')}")

        # ------------------------------------------------------------------
        # Step 5: Verify
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("STEP 5 — Verification")
        print("=" * 60)

        updated_kpis = _fetch(http, supabase_url, headers, "kpis",
                               "data_product_id=eq.fi_star_schema")
        correct = sum(1 for k in updated_kpis if k.get("client_id") == "bicycle")
        wrong = len(updated_kpis) - correct
        print(f"\nBicycle KPIs: {correct} correct (client_id='bicycle'), {wrong} still wrong")

        updated_principals = _fetch(http, supabase_url, headers, "principal_profiles",
                                    "client_id=eq.bicycle")
        print(f"Bicycle principals: {len(updated_principals)}")
        for p in updated_principals:
            print(f"  - {p.get('id')}  name={p.get('name')}")

        if wrong == 0:
            print("\n✓ Bicycle client isolation fixed successfully")
        else:
            print(f"\n⚠ {wrong} KPIs still have wrong client_id — check for composite PK issues")


if __name__ == "__main__":
    main()
