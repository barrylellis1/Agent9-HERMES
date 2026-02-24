#!/usr/bin/env python3
"""
Reset Lubricants Business demo data from Supabase.

Removes the Lubricants data product and its KPIs so the live onboarding demo
can walk through the full registration wizard from scratch.

Usage:
    python scripts/demo_reset_lubricants.py

Environment:
    SUPABASE_URL               - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY  - Service role key (admin access)
"""

import os
import sys
from typing import Dict

import httpx


DP_ID = "dp_lubricants_financials"


def _supabase_headers(service_key: str, schema: str = "public") -> Dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Profile": schema,
        "Prefer": "return=minimal",
    }


def main():
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        sys.exit(1)

    headers = _supabase_headers(service_key)
    base = supabase_url.rstrip("/")

    with httpx.Client(timeout=30.0) as client:
        # 1. Delete KPIs for this data product
        print(f"Deleting KPIs for data_product_id={DP_ID}...")
        resp = client.delete(
            f"{base}/rest/v1/kpis",
            headers=headers,
            params={"data_product_id": f"eq.{DP_ID}"},
        )
        resp.raise_for_status()
        print(f"  -> KPIs deleted (HTTP {resp.status_code})")

        # 2. Delete the data product
        print(f"Deleting data product {DP_ID}...")
        resp = client.delete(
            f"{base}/rest/v1/data_products",
            headers=headers,
            params={"id": f"eq.{DP_ID}"},
        )
        resp.raise_for_status()
        print(f"  -> Data product deleted (HTTP {resp.status_code})")

    print(f"\nDone! Lubricants demo data cleared. Ready for live onboarding demo.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
