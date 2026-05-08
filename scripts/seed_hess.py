#!/usr/bin/env python3
"""
Seed "Hess Corporation" client into Supabase.

Creates:
  1. Business context  (business_contexts)
  2. Business processes: canonical Finance + Strategy + 1 extra Operations (business_processes)
  3. 4 principal profiles (principal_profiles)
  4. SQL Server data product (data_products)
  5. 14 KPIs pointing to the SQL Server data product (kpis)

Usage:
    python scripts/seed_hess.py [--dry-run]

Environment:
    SUPABASE_URL               - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY  - Service role key (admin access)
"""

import argparse
import os
import sys

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.clients.hess import (
    CLIENT_ID,
    CLIENT_META,
    DATA_PRODUCT,
    KPIS,
    PRINCIPALS,
    EXTRA_BUSINESS_PROCESSES,
)
from src.registry.canonical.business_processes import (
    FINANCE_BUSINESS_PROCESSES,
    STRATEGY_BUSINESS_PROCESSES,
)

# Canonical business processes scoped to the hess client_id
_CANONICAL_BPS = [
    {**bp, "client_id": CLIENT_ID}
    for bp in FINANCE_BUSINESS_PROCESSES + STRATEGY_BUSINESS_PROCESSES
]
ALL_BUSINESS_PROCESSES = _CANONICAL_BPS + EXTRA_BUSINESS_PROCESSES

# ---------------------------------------------------------------------------
# Business context (derived from CLIENT_META)
# ---------------------------------------------------------------------------

BUSINESS_CONTEXT = {
    "id": CLIENT_ID,
    "name": CLIENT_META["name"],
    "industry": CLIENT_META["industry"],
    "sub_sector": "Exploration & Production",
    "revenue": "$12.6B",
    "employees": "1,650",
    "ownership": "Public (NYSE: HES)",
    "description": (
        "Hess Corporation is a leading independent global E&P company with assets "
        "in the Bakken, Gulf of Mexico, Guyana, and Southeast Asia. "
        "Operations span upstream oil and gas production with a growing Midstream segment."
    ),
    "business_model": {
        "revenue_streams": [
            "E&P Upstream (88%): Oil, NGL, and gas sales from production assets",
            "Midstream (12%): Gathering, processing, and transportation via Hess Midstream Partners",
        ],
        "key_markets": [
            "Guyana (Stabroek Block — largest growth asset)",
            "Bakken (North Dakota)",
            "Gulf of Mexico",
            "Southeast Asia",
        ],
    },
    "strategic_priorities": [
        "Accelerate Guyana production ramp from Stabroek Block FPSOs",
        "Sustain Bakken cash flow at $40–50/bbl breakeven",
        "Maintain capital discipline and grow free cash flow per share",
        "Protect balance sheet — investment-grade credit rating",
    ],
    "competitors": [
        "Pioneer Natural Resources",
        "Devon Energy",
        "ConocoPhillips",
        "Marathon Oil",
    ],
    "operational_context": {
        "commodity_exposure": "~70% oil, ~30% gas/NGL by revenue — highly sensitive to Brent price",
        "growth_driver": "Guyana represents >50% of 5-year production growth",
        "capex_discipline": "Annual CapEx guidance: $3.7–3.9B; free cash flow breakeven ~$50 Brent",
    },
    "is_demo": True,
}

# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

def _headers(service_key: str):
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }


def _upsert(client: httpx.Client, url: str, headers, table: str, rows: list) -> list:
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    resp = client.post(endpoint, headers=headers, json=rows)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seed Hess Corporation client into Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Print data without upserting")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN ===\n")
        print(f"Business Context: {BUSINESS_CONTEXT['id']} - {BUSINESS_CONTEXT['name']}")
        print(f"\nPrincipals ({len(PRINCIPALS)}):")
        for p in PRINCIPALS:
            print(f"  {p['id']:25s}  {p['name']:20s}  {p['role']}")
        print(f"\nData Product: {DATA_PRODUCT['id']} - {DATA_PRODUCT['name']}")
        print(f"  source_system={DATA_PRODUCT['source_system']}")
        print(f"\nKPIs ({len(KPIS)}):")
        for kpi in KPIS:
            print(f"  {kpi['id']:30s}  {kpi['name']} ({kpi['unit']})")
        print(f"\nBusiness Processes ({len(ALL_BUSINESS_PROCESSES)} total = {len(_CANONICAL_BPS)} canonical + {len(EXTRA_BUSINESS_PROCESSES)} extra):")
        for bp in ALL_BUSINESS_PROCESSES:
            print(f"  {bp['id']:45s}  {bp['name']}")
        return

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        sys.exit(1)

    headers = _headers(service_key)

    with httpx.Client(timeout=30.0) as client:
        # 1. Business context
        print(f"Upserting business context: {BUSINESS_CONTEXT['id']}...")
        result = _upsert(client, supabase_url, headers, "business_contexts", [BUSINESS_CONTEXT])
        print(f"  -> {len(result)} row(s)")

        # 2. Business processes (canonical Finance + Strategy + Hess-specific Operations)
        print(f"\nUpserting {len(ALL_BUSINESS_PROCESSES)} business processes ({len(_CANONICAL_BPS)} canonical + {len(EXTRA_BUSINESS_PROCESSES)} extra)...")
        result = _upsert(client, supabase_url, headers, "business_processes", ALL_BUSINESS_PROCESSES)
        print(f"  -> {len(result)} row(s)")

        # 3. Principal profiles
        print(f"\nUpserting {len(PRINCIPALS)} principal profiles...")
        result = _upsert(client, supabase_url, headers, "principal_profiles", PRINCIPALS)
        print(f"  -> {len(result)} row(s)")
        for p in result:
            print(f"     {p.get('id', '?'):25s}  {p.get('name', '?')}")

        # 4. Data product
        print(f"\nUpserting data product: {DATA_PRODUCT['id']}...")
        result = _upsert(client, supabase_url, headers, "data_products", [DATA_PRODUCT])
        print(f"  -> {len(result)} row(s)")

        # 5. KPIs
        print(f"\nUpserting {len(KPIS)} KPIs...")
        result = _upsert(client, supabase_url, headers, "kpis", KPIS)
        print(f"  -> {len(result)} row(s)")
        for k in result:
            print(f"     {k.get('id', '?'):30s}  {k.get('name', '?')}")

    print(f"\nDone! Hess Corporation client seeded.")
    print(f"  Client ID:    {CLIENT_ID}")
    print(f"  Principals:   {len(PRINCIPALS)}")
    print(f"  Data Product: {DATA_PRODUCT['id']}")
    print(f"  KPIs:         {len(KPIS)}")
    print(f"\nSelect 'Hess Corporation' on the login page to start testing.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
