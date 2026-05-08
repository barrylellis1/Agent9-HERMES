#!/usr/bin/env python3
"""
Patch the dp_lubricants_snowflake data product in Supabase to include
snowflake_username in its metadata, bypassing the Railway SF_USERNAME env var.

Usage:
    python scripts/patch_snowflake_username.py [--dry-run]
"""

import argparse
import json
import os
import sys

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--username", default="BARRYLELLIS1",
                        help="Snowflake username to store in metadata")
    parser.add_argument("--data-product-id", default="dp_lubricants_snowflake",
                        help="Data product ID to patch")
    parser.add_argument("--supabase-url", default=None,
                        help="Override SUPABASE_URL (e.g. production URL)")
    parser.add_argument("--service-key", default=None,
                        help="Override SUPABASE_SERVICE_ROLE_KEY")
    parser.add_argument("--env-file", default=None,
                        help="Path to an env file to load (e.g. .env.production)")
    args = parser.parse_args()

    if args.env_file:
        from dotenv import dotenv_values
        env_overrides = dotenv_values(args.env_file)
        supabase_url = args.supabase_url or env_overrides.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
        service_key = args.service_key or env_overrides.get("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    else:
        supabase_url = args.supabase_url or os.getenv("SUPABASE_URL")
        service_key = args.service_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        sys.exit(1)

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    with httpx.Client(timeout=30.0) as client:
        # Fetch current record
        resp = client.get(
            f"{supabase_url.rstrip('/')}/rest/v1/data_products",
            headers=headers,
            params={"id": f"eq.{args.data_product_id}", "select": "id,metadata"},
        )
        resp.raise_for_status()
        rows = resp.json()

        if not rows:
            print(f"ERROR: No data product found with id={args.data_product_id}", file=sys.stderr)
            sys.exit(1)

        row = rows[0]
        current_metadata = row.get("metadata") or {}
        print(f"Current metadata for {args.data_product_id}:")
        print(json.dumps(current_metadata, indent=2))

        updated_metadata = {**current_metadata, "snowflake_username": args.username}
        print(f"\nPatched metadata (adding snowflake_username={args.username!r}):")
        print(json.dumps(updated_metadata, indent=2))

        if args.dry_run:
            print("\n[DRY RUN] No changes written.")
            return

        # PATCH the record
        patch_resp = client.patch(
            f"{supabase_url.rstrip('/')}/rest/v1/data_products",
            headers={**headers, "Prefer": "return=representation"},
            params={"id": f"eq.{args.data_product_id}"},
            json={"metadata": updated_metadata},
        )
        patch_resp.raise_for_status()
        result = patch_resp.json()
        print(f"\nUpdated {len(result)} row(s). Done.")
        print("The next Snowflake connection will use the username from metadata.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
