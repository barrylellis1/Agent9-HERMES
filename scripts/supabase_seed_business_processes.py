#!/usr/bin/env python3
"""
DEPRECATED: Supabase Business Process Seeder

As of 2026-02-19, business processes are managed directly in Supabase.
Pass --force to run this script for disaster recovery only.

Original description:
Reads business processes from YAML and seeds them into Supabase.
Handles normalization and transformation for Supabase schema.

Usage:
    python scripts/supabase_seed_business_processes.py [--dry-run] [--truncate-first]

Environment Variables:
    SUPABASE_URL - Supabase project URL (default: http://localhost:54321)
    SUPABASE_SERVICE_ROLE_KEY - Service role key for authentication
    SUPABASE_BUSINESS_PROCESS_TABLE - Table name (default: business_processes)
"""

import os
import sys
import yaml
import json
import argparse
from typing import List, Dict, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_business_processes(yaml_path: str) -> List[Dict[str, Any]]:
    """Load business processes from YAML file."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # YAML file is a list of business processes
    if isinstance(data, list):
        return data
    else:
        raise ValueError(f"Expected list of business processes, got {type(data)}")


def transform_business_process(bp: Dict[str, Any]) -> Dict[str, Any]:
    """Transform business process to Supabase-compatible format."""
    return {
        'id': bp.get('id'),
        'name': bp.get('name'),
        'domain': bp.get('domain'),
        'description': bp.get('description'),
        'owner_role': bp.get('owner_role'),
        'stakeholder_roles': bp.get('stakeholder_roles', []),
        'display_name': bp.get('display_name'),
        'tags': bp.get('tags', []),
        'metadata': bp.get('metadata', {}),
    }


def seed_to_supabase(
    rows: List[Dict[str, Any]],
    supabase_url: str,
    service_key: str,
    table: str = 'business_processes',
    truncate_first: bool = False,
) -> None:
    """Seed business processes to Supabase via REST API."""
    import requests
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
    }
    
    # Truncate table if requested
    if truncate_first:
        delete_url = f'{supabase_url}/rest/v1/{table}'
        delete_headers = {**headers}
        delete_headers['Prefer'] = 'return=minimal'
        resp = requests.delete(delete_url, headers=delete_headers, params={'id': 'neq.___NONE___'})
        if resp.status_code not in (200, 204):
            print(f"Warning: Failed to truncate table: {resp.status_code} {resp.text}")
        else:
            print(f"Truncated {table} table")
    
    # Upsert rows
    url = f'{supabase_url}/rest/v1/{table}'
    resp = requests.post(url, headers=headers, json=rows)
    
    if resp.status_code not in (200, 201):
        raise Exception(f"Failed to seed business processes: {resp.status_code} {resp.text}")
    
    print(f"[SUCCESS] Seeded {len(rows)} rows into {table}")


def main():
    # DEPRECATED — Supabase is now the sole registry backend
    if "--force" not in sys.argv:
        print("⚠️  DEPRECATED: supabase_seed_business_processes.py — registries now live in Supabase. Pass --force to run.")
        return

    parser = argparse.ArgumentParser(description='Seed business processes to Supabase')
    parser.add_argument('--dry-run', action='store_true', help='Print rows without seeding')
    parser.add_argument('--truncate-first', action='store_true', help='Truncate table before seeding')
    parser.add_argument('--force', action='store_true', help='Force run deprecated script')
    args = parser.parse_args()
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL', 'http://localhost:54321')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    table = os.getenv('SUPABASE_BUSINESS_PROCESS_TABLE', 'business_processes')
    
    if not service_key:
        print("Error: SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    
    # Load business processes from YAML
    yaml_path = project_root / 'src' / 'registry' / 'business_process' / 'business_process_registry.yaml'
    print(f"Loading {yaml_path}...")
    
    business_processes = load_business_processes(str(yaml_path))
    print(f"Loaded {len(business_processes)} business processes")
    
    # Transform to Supabase format
    rows = [transform_business_process(bp) for bp in business_processes]
    print(f"Transformed {len(rows)} business processes")
    
    if args.dry_run:
        print("\n=== DRY RUN: Would seed the following rows ===")
        print(json.dumps(rows, indent=2))
        return
    
    # Seed to Supabase
    print(f"Upserting {len(rows)} rows to {table}...")
    seed_to_supabase(rows, supabase_url, service_key, table, args.truncate_first)


if __name__ == '__main__':
    main()
