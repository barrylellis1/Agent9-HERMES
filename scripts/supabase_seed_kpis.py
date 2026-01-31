#!/usr/bin/env python3
"""
Supabase KPI Seeder

Reads kpi_registry.yaml and business_process_registry.yaml, transforms KPIs
into Supabase-compatible rows with normalized business_process_ids, and upserts via REST API.

Usage:
    python scripts/supabase_seed_kpis.py [--dry-run] [--truncate-first]

Environment variables:
    SUPABASE_URL                    - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY       - Service role key (admin access)
    SUPABASE_SCHEMA                 - Schema name (default: public)
    SUPABASE_KPI_TABLE              - Table name (default: kpis)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx
import yaml


# Paths to registry files
KPI_REGISTRY_PATH = Path("src/registry/kpi/kpi_registry.yaml")
BUSINESS_PROCESS_REGISTRY_PATH = Path("src/registry/business_process/business_process_registry.yaml")
STAGING_DIR = Path("src/registry_references/data_product_registry/staging")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Seed Supabase kpis table from YAML")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print transformed rows without upserting to Supabase",
    )
    parser.add_argument(
        "--truncate-first",
        action="store_true",
        help="Delete all existing rows before upserting (destructive)",
    )
    return parser.parse_args()


def load_yaml_file(path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    if not data:
        print(f"Error: Empty or invalid YAML: {path}", file=sys.stderr)
        sys.exit(1)
    
    return data


def build_business_process_map(bp_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Build a mapping from business process display_name to id.
    
    Args:
        bp_data: Parsed business_process_registry.yaml
    
    Returns:
        Dict mapping display_name -> id
    """
    bp_map = {}
    
    # business_process_registry.yaml is a list at the root
    if isinstance(bp_data, list):
        for bp in bp_data:
            if isinstance(bp, dict) and "id" in bp and "display_name" in bp:
                bp_map[bp["display_name"]] = bp["id"]
    
    return bp_map


def transform_kpi(kpi: Dict[str, Any], bp_map: Dict[str, str]) -> Dict[str, Any]:
    """
    Transform a KPI from YAML format to Supabase row format.
    
    Args:
        kpi: KPI dict from YAML
        bp_map: Business process display_name -> id mapping
    
    Returns:
        Dict ready for Supabase upsert
    """
    # Map business_process_ids (could be display names or IDs) to normalized IDs
    business_process_ids = []
    for bp_ref in kpi.get("business_process_ids", []):
        # Try as ID first, then as display name
        if bp_ref in [bp_id for bp_id in bp_map.values()]:
            business_process_ids.append(bp_ref)
        elif bp_ref in bp_map:
            business_process_ids.append(bp_map[bp_ref])
        else:
            print(f"Warning: Unknown business process '{bp_ref}' for KPI {kpi.get('id')}", file=sys.stderr)
    
    # Build Supabase row (matching migration schema)
    row = {
        "id": kpi.get("id"),
        "name": kpi.get("name"),
        "domain": kpi.get("domain"),
        "description": kpi.get("description"),
        "unit": kpi.get("unit"),
        "data_product_id": kpi.get("data_product_id"),
        "view_name": kpi.get("view_name"),
        "business_process_ids": business_process_ids,  # Normalized IDs
        "sql_query": kpi.get("sql_query"),
        "filters": kpi.get("filters", {}),
        "thresholds": kpi.get("thresholds", []),
        "dimensions": kpi.get("dimensions", []),
        "tags": kpi.get("tags", []),
        "synonyms": kpi.get("synonyms", []),
        "owner_role": kpi.get("owner_role"),
        "stakeholder_roles": kpi.get("stakeholder_roles", []),
        "metadata": kpi.get("metadata", {}),
    }
    
    return row


def transform_kpis(kpi_data: Dict[str, Any], bp_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Transform all KPIs from YAML to Supabase format.
    
    Args:
        kpi_data: Parsed kpi_registry.yaml
        bp_map: Business process display_name -> id mapping
    
    Returns:
        List of Supabase-ready rows
    """
    rows = []
    
    # kpi_registry.yaml has a "kpis" key with a list
    kpis = kpi_data.get("kpis", [])
    
    for kpi in kpis:
        if not isinstance(kpi, dict):
            continue
        
        row = transform_kpi(kpi, bp_map)
        rows.append(row)
    
    return rows


def delete_existing_rows(client: httpx.Client, endpoint: str, headers: Dict[str, str]) -> None:
    """Delete all existing rows from the table (truncate)."""
    try:
        response = client.delete(
            endpoint,
            headers={**headers, "Prefer": "return=minimal"},
            params={"id": "neq.___IMPOSSIBLE___"},  # Match all rows
        )
        response.raise_for_status()
        print(f"Deleted existing rows from {endpoint}")
    except httpx.HTTPStatusError as e:
        print(f"Error deleting rows: {e.response.status_code} {e.response.text}", file=sys.stderr)
        raise


def upsert_rows(client: httpx.Client, endpoint: str, headers: Dict[str, str], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Upsert rows to Supabase via REST API.
    
    Args:
        client: httpx.Client
        endpoint: Supabase REST endpoint
        headers: Request headers
        rows: List of rows to upsert
    
    Returns:
        List of inserted/updated rows from Supabase
    """
    try:
        response = client.post(
            endpoint,
            headers=headers,
            json=rows,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Error upserting rows: {e.response.status_code} {e.response.text}", file=sys.stderr)
        raise


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Load environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_role:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        return 1
    
    table = os.getenv("SUPABASE_KPI_TABLE", "kpis")
    schema = os.getenv("SUPABASE_SCHEMA", "public")
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/{table}"
    
    # Load registry files
    print(f"Loading {KPI_REGISTRY_PATH}...")
    kpi_data = load_yaml_file(KPI_REGISTRY_PATH)
    
    print(f"Loading {BUSINESS_PROCESS_REGISTRY_PATH}...")
    bp_data = load_yaml_file(BUSINESS_PROCESS_REGISTRY_PATH)
    
    # Build business process mapping
    bp_map = build_business_process_map(bp_data)
    print(f"Mapped {len(bp_map)} business processes")
    
    # Transform KPIs from central registry
    rows = transform_kpis(kpi_data, bp_map)
    print(f"Transformed {len(rows)} KPIs from central registry")

    # Load and transform KPIs from staging data products
    if STAGING_DIR.exists():
        print(f"Loading KPIs from staging: {STAGING_DIR}...")
        staging_kpis_count = 0
        for yaml_file in STAGING_DIR.glob("*.yaml"):
            try:
                dp_data = load_yaml_file(yaml_file)
                if "kpis" in dp_data and isinstance(dp_data["kpis"], list):
                    # Load KPIs directly without prefixing - enforcing global uniqueness
                    dp_rows = transform_kpis(dp_data, bp_map)
                    rows.extend(dp_rows)
                    staging_kpis_count += len(dp_rows)
            except Exception as e:
                print(f"Warning: Failed to load KPIs from {yaml_file}: {e}", file=sys.stderr)
        
        print(f"Transformed {staging_kpis_count} KPIs from staging data products")
    else:
        print(f"Warning: Staging directory not found: {STAGING_DIR}", file=sys.stderr)
    
    # Deduplicate rows by ID
    unique_rows = {}
    for row in rows:
        kpi_id = row.get("id")
        if kpi_id:
            if kpi_id in unique_rows:
                print(f"Warning: Duplicate KPI ID '{kpi_id}' found. Overwriting with latest definition.", file=sys.stderr)
            unique_rows[kpi_id] = row
        else:
            print("Warning: KPI missing ID, skipping.", file=sys.stderr)
            
    rows = list(unique_rows.values())
    print(f"Total Unique KPIs to seed: {len(rows)}")
    
    # Dry run: print and exit
    if args.dry_run:
        print("\n=== DRY RUN: Transformed rows ===")
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        print(f"\nPrepared {len(rows)} rows. Dry run mode - no changes applied.")
        return 0
    
    # Prepare headers
    headers = {
        "apikey": supabase_service_role,
        "Authorization": f"Bearer {supabase_service_role}",
        "Prefer": "resolution=merge-duplicates,return=representation",
        "Accept": "application/json",
        "Accept-Profile": schema,
        "Content-Type": "application/json",
    }
    
    # Execute upsert
    with httpx.Client(timeout=30.0) as client:
        if args.truncate_first:
            print("Truncating existing rows...")
            delete_existing_rows(client, endpoint, headers)
        
        print(f"Upserting {len(rows)} rows to {table}...")
        inserted = upsert_rows(client, endpoint, headers, rows)
    
    print(f"[SUCCESS] Seeded {len(inserted) if inserted else len(rows)} rows into {table}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
