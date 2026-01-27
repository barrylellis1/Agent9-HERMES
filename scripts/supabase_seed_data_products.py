#!/usr/bin/env python3
"""
Supabase Data Product Seeder

Reads data products from YAML and seeds them into Supabase.
Handles normalization and transformation for Supabase schema.

Usage:
    python scripts/supabase_seed_data_products.py [--dry-run] [--truncate-first]

Environment Variables:
    SUPABASE_URL - Supabase project URL (default: http://localhost:54321)
    SUPABASE_SERVICE_ROLE_KEY - Service role key for authentication
    SUPABASE_DATA_PRODUCT_TABLE - Table name (default: data_products)
"""

import os
import sys
import yaml
import json
import argparse
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_data_products(yaml_path: str) -> List[Dict[str, Any]]:
    """Load data products from YAML file."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # YAML file has a 'data_products' key
    if isinstance(data, dict) and 'data_products' in data:
        return data['data_products']
    else:
        raise ValueError(f"Expected dict with 'data_products' key, got {type(data)}")


def transform_data_product(dp: Dict[str, Any]) -> Dict[str, Any]:
    """Transform data product to Supabase-compatible format."""
    # Convert product_id to id for consistency
    dp_id = dp.get('product_id') or dp.get('id')
    
    # Parse last_updated to date if it's a string
    last_updated = dp.get('last_updated')
    if isinstance(last_updated, str):
        try:
            last_updated = datetime.strptime(last_updated, '%Y-%m-%d').date().isoformat()
        except:
            last_updated = None
            
    # Extract source_system from root or metadata
    source_system = dp.get('source_system')
    if not source_system and 'metadata' in dp:
        source_system = dp['metadata'].get('source_system')
    
    return {
        'id': dp_id,
        'name': dp.get('name'),
        'domain': dp.get('domain'),
        'description': dp.get('description'),
        'owner': dp.get('owner', f"{dp.get('domain')} Team"),
        'version': dp.get('version', '1.0.0'),
        'source_system': source_system or 'duckdb',
        'related_business_processes': dp.get('related_business_processes', []),
        'tags': dp.get('tags', []),
        'metadata': dp.get('metadata', {}),
        'tables': dp.get('tables', {}),
        'views': dp.get('views', {}),
        'yaml_contract_path': dp.get('yaml_contract_path'),
        'output_path': dp.get('output_path'),
        'last_updated': last_updated,
        'reviewed': dp.get('reviewed', False),
        'language': dp.get('language', 'EN'),
        'documentation': dp.get('documentation'),
        'staging': dp.get('staging', False),
    }


def load_staging_products() -> List[Dict[str, Any]]:
    """Load data products from staging directory."""
    staging_dir = project_root / 'src' / 'registry_references' / 'data_product_registry' / 'staging'
    products = []
    
    if not staging_dir.exists():
        return products
        
    for yaml_file in staging_dir.glob('*.yaml'):
        if yaml_file.name == 'README.md':
            continue
            
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if data:
                # Add staging flag and ensure ID matches filename if not present
                data['staging'] = True
                if 'id' not in data:
                    data['id'] = yaml_file.stem
                if 'product_id' not in data:
                    data['product_id'] = data['id']
                    
                products.append(data)
        except Exception as e:
            print(f"Warning: Failed to load staging file {yaml_file}: {e}")
            
    return products


def seed_to_supabase(
    rows: List[Dict[str, Any]],
    supabase_url: str,
    service_key: str,
    table: str = 'data_products',
    truncate_first: bool = False,
) -> None:
    """Seed data products to Supabase via REST API."""
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
        raise Exception(f"Failed to seed data products: {resp.status_code} {resp.text}")
    
    print(f"✅ Seeded {len(rows)} rows into {table}")


def main():
    parser = argparse.ArgumentParser(description='Seed data products to Supabase')
    parser.add_argument('--dry-run', action='store_true', help='Print rows without seeding')
    parser.add_argument('--truncate-first', action='store_true', help='Truncate table before seeding')
    args = parser.parse_args()
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL', 'http://localhost:54321')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    table = os.getenv('SUPABASE_DATA_PRODUCT_TABLE', 'data_products')
    
    if not service_key:
        print("Error: SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    
    # Load data products from YAML
    yaml_path = project_root / 'src' / 'registry' / 'data_product' / 'data_product_registry.yaml'
    print(f"Loading {yaml_path}...")
    
    data_products = load_data_products(str(yaml_path))
    print(f"Loaded {len(data_products)} registry data products")
    
    # Load staging products
    staging_products = load_staging_products()
    print(f"Loaded {len(staging_products)} staging data products")
    
    # Merge products (staging overrides registry if IDs conflict)
    products_map = {dp.get('product_id') or dp.get('id'): dp for dp in data_products}
    
    for sp in staging_products:
        sp_id = sp.get('product_id') or sp.get('id')
        if sp_id:
            if sp_id in products_map:
                print(f"Overriding registry product {sp_id} with staging version")
            products_map[sp_id] = sp
            
    all_products = list(products_map.values())
    
    # Transform to Supabase format
    rows = [transform_data_product(dp) for dp in all_products]
    print(f"Transformed {len(rows)} total data products")
    
    if args.dry_run:
        print("\n=== DRY RUN: Would seed the following rows ===")
        print(json.dumps(rows, indent=2))
        return
    
    # Seed to Supabase
    print(f"Upserting {len(rows)} rows to {table}...")
    seed_to_supabase(rows, supabase_url, service_key, table, args.truncate_first)


if __name__ == '__main__':
    main()
