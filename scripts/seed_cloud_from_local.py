#!/usr/bin/env python3
"""
Seed Supabase Cloud from local Supabase — live data transfer.

Reads all rows from each registry table in local Supabase (via .env)
and upserts them into cloud Supabase (via .env.production).

Usage:
    python scripts/seed_cloud_from_local.py [--dry-run]

Requirements:
    - Local Supabase running (.\supabase.exe start)
    - .env with local credentials
    - .env.production with cloud credentials
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# ---------------------------------------------------------------------------
# Tables to sync (order matters for foreign key dependencies)
# ---------------------------------------------------------------------------

TABLES = [
    "business_glossary_terms",
    "data_products",
    "business_processes",
    "kpis",
    "principal_profiles",
    "business_contexts",
]

# ---------------------------------------------------------------------------
# Env file loader
# ---------------------------------------------------------------------------

def load_env_file(filepath: str) -> Dict[str, str]:
    """Parse a .env file into a dict (simple key=value, ignores comments)."""
    env = {}
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: {filepath} not found", file=sys.stderr)
        sys.exit(1)
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

def _headers(service_key: str) -> Dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Profile": "public",
    }


def _headers_upsert(service_key: str) -> Dict[str, str]:
    h = _headers(service_key)
    h["Prefer"] = "resolution=merge-duplicates,return=representation"
    return h


def fetch_all(client: httpx.Client, url: str, key: str, table: str) -> List[Dict[str, Any]]:
    """Fetch all rows from a Supabase table via REST API with pagination."""
    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    all_rows = []
    offset = 0
    limit = 1000

    while True:
        params = {"select": "*", "offset": str(offset), "limit": str(limit)}
        resp = client.get(endpoint, headers=_headers(key), params=params)
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < limit:
            break
        offset += limit

    return all_rows


def upsert_batch(client: httpx.Client, url: str, key: str,
                 table: str, rows: List[Dict[str, Any]]) -> int:
    """Upsert rows into cloud Supabase in batches of 500."""
    if not rows:
        return 0

    endpoint = f"{url.rstrip('/')}/rest/v1/{table}"
    headers = _headers_upsert(key)
    total = 0
    batch_size = 500

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        resp = client.post(endpoint, headers=headers, json=batch)
        resp.raise_for_status()
        total += len(resp.json())

    return total


def clean_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove auto-generated timestamps that might conflict on upsert."""
    for row in rows:
        # Keep created_at/updated_at — Supabase will handle via ON CONFLICT
        pass
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seed cloud Supabase from local Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Show row counts without writing")
    parser.add_argument("--tables", nargs="*", help="Only sync specific tables (default: all)")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    # Load both env files
    local_env = load_env_file(str(project_root / ".env"))
    cloud_env = load_env_file(str(project_root / ".env.production"))

    local_url = local_env.get("SUPABASE_URL")
    local_key = local_env.get("SUPABASE_SERVICE_ROLE_KEY")
    cloud_url = cloud_env.get("SUPABASE_URL")
    cloud_key = cloud_env.get("SUPABASE_SERVICE_ROLE_KEY")

    if not all([local_url, local_key, cloud_url, cloud_key]):
        print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env or .env.production",
              file=sys.stderr)
        sys.exit(1)

    # Safety check — don't write to local
    if cloud_url == local_url:
        print("ERROR: Cloud and local URLs are the same — aborting to prevent overwrite",
              file=sys.stderr)
        sys.exit(1)

    tables = args.tables if args.tables else TABLES

    print(f"Source: {local_url}")
    print(f"Target: {cloud_url}")
    print(f"Tables: {', '.join(tables)}")
    print()

    with httpx.Client(timeout=60.0) as client:
        for table in tables:
            # Read from local
            print(f"[{table}] Reading from local...", end=" ", flush=True)
            try:
                rows = fetch_all(client, local_url, local_key, table)
            except httpx.HTTPStatusError as e:
                print(f"SKIP (table may not exist locally: {e.response.status_code})")
                continue

            print(f"{len(rows)} rows found.", end=" ", flush=True)

            if not rows:
                print("Nothing to sync.")
                continue

            if args.dry_run:
                print("(dry-run, not writing)")
                continue

            # Write to cloud
            rows = clean_rows(rows)
            print("Writing to cloud...", end=" ", flush=True)
            try:
                count = upsert_batch(client, cloud_url, cloud_key, table, rows)
                print(f"{count} rows upserted.")
            except httpx.HTTPStatusError as e:
                print(f"ERROR: {e.response.status_code}")
                print(f"  Response: {e.response.text[:500]}")
                continue

    print("\nDone!")


if __name__ == "__main__":
    main()
