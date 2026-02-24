#!/usr/bin/env python3
"""
DEPRECATED: Supabase Principal Profiles Seeder

As of 2026-02-19, principal profiles are managed directly in Supabase.
Pass --force to run this script for disaster recovery only.

Original description:
Reads principal_registry.yaml and business_process_registry.yaml, transforms principals
into Supabase-compatible rows with normalized business_process_ids, and upserts via REST API.

Usage:
    python scripts/supabase_seed_principal_profiles.py [--dry-run] [--truncate-first]

Environment variables:
    SUPABASE_URL                    - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY       - Service role key (admin access)
    SUPABASE_SCHEMA                 - Schema name (default: public)
    SUPABASE_PRINCIPAL_TABLE        - Table name (default: principal_profiles)
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
PRINCIPAL_REGISTRY_PATH = Path("src/registry/principal/principal_registry.yaml")
BUSINESS_PROCESS_REGISTRY_PATH = Path("src/registry/business_process/business_process_registry.yaml")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Seed Supabase principal_profiles table from YAML")
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
    parser.add_argument("--force", action="store_true", help="Force run deprecated script")
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
        Dict mapping display_name -> id (e.g., "Finance: Profitability Analysis" -> "finance_profitability_analysis")
    """
    bp_map = {}
    
    # business_process_registry.yaml is a list at the root
    if isinstance(bp_data, list):
        for bp in bp_data:
            if isinstance(bp, dict) and "id" in bp and "display_name" in bp:
                bp_map[bp["display_name"]] = bp["id"]
    
    return bp_map


def transform_principal(principal: Dict[str, Any], bp_map: Dict[str, str]) -> Dict[str, Any]:
    """
    Transform a principal from YAML format to Supabase row format.
    
    Args:
        principal: Principal dict from YAML
        bp_map: Business process display_name -> id mapping
    
    Returns:
        Dict ready for Supabase upsert
    """
    # Map business_processes (display names) to business_process_ids (IDs)
    business_process_ids = []
    for bp_display in principal.get("business_processes", []):
        bp_id = bp_map.get(bp_display)
        if bp_id:
            business_process_ids.append(bp_id)
        else:
            print(f"Warning: Unknown business process '{bp_display}' for principal {principal.get('id')}", file=sys.stderr)
    
    # Build Supabase row (matching migration schema)
    row = {
        "id": principal.get("id"),
        "name": principal.get("name"),
        "title": principal.get("title"),
        "first_name": principal.get("first_name"),
        "last_name": principal.get("last_name"),
        "role": principal.get("role"),
        "department": principal.get("department"),
        "source": principal.get("source"),
        "description": principal.get("description"),
        "responsibilities": principal.get("responsibilities", []),
        "business_process_ids": business_process_ids,  # Normalized IDs
        "default_filters": principal.get("default_filters", {}),
        "typical_timeframes": principal.get("typical_timeframes", []),
        "principal_groups": principal.get("principal_groups", []),
        "persona_profile": principal.get("persona_profile", {}),
        "preferences": principal.get("preferences", {}),
        "permissions": principal.get("permissions", []),
        "time_frame": principal.get("time_frame", {}),
        "communication": principal.get("communication", {}),
        "metadata": principal.get("metadata", {}),
    }
    
    return row


def transform_principals(principal_data: Dict[str, Any], bp_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Transform all principals from YAML to Supabase format.
    
    Args:
        principal_data: Parsed principal_registry.yaml
        bp_map: Business process display_name -> id mapping
    
    Returns:
        List of Supabase-ready rows
    """
    rows = []
    
    # principal_registry.yaml has a "principals" key with a list
    principals = principal_data.get("principals", [])
    
    for principal in principals:
        if not isinstance(principal, dict):
            continue
        
        row = transform_principal(principal, bp_map)
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
    # DEPRECATED — Supabase is now the sole registry backend
    if "--force" not in sys.argv:
        print("⚠️  DEPRECATED: supabase_seed_principal_profiles.py — registries now live in Supabase. Pass --force to run.")
        return 0

    args = parse_args()

    # Load environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_role:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        return 1
    
    table = os.getenv("SUPABASE_PRINCIPAL_TABLE", "principal_profiles")
    schema = os.getenv("SUPABASE_SCHEMA", "public")
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/{table}"
    
    # Load registry files
    print(f"Loading {PRINCIPAL_REGISTRY_PATH}...")
    principal_data = load_yaml_file(PRINCIPAL_REGISTRY_PATH)
    
    print(f"Loading {BUSINESS_PROCESS_REGISTRY_PATH}...")
    bp_data = load_yaml_file(BUSINESS_PROCESS_REGISTRY_PATH)
    
    # Build business process mapping
    bp_map = build_business_process_map(bp_data)
    print(f"Mapped {len(bp_map)} business processes")
    
    # Transform principals
    rows = transform_principals(principal_data, bp_map)
    print(f"Transformed {len(rows)} principal profiles")
    
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
