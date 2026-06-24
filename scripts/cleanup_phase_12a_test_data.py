#!/usr/bin/env python3
"""
Cleanup Phase 12A template KPIs from Supabase.

Removes rows from the `kpis` table where `status='template'`, scoped to a
single client_id. Active KPIs are never touched — `status='active'` is the
hard guard.

Usage:
    # Show what would be deleted (no changes)
    python scripts/cleanup_phase_12a_test_data.py --dry-run

    # Delete all template KPIs for the default client (lubricants)
    python scripts/cleanup_phase_12a_test_data.py

    # Different client
    python scripts/cleanup_phase_12a_test_data.py --client bicycle

    # Target a specific created_by tag (e.g. e2e_runbook)
    python scripts/cleanup_phase_12a_test_data.py --created-by kpi_intelligence_ui

Environment:
    SUPABASE_URL               - Supabase project URL (e.g. http://127.0.0.1:54321)
    SUPABASE_SERVICE_ROLE_KEY  - Service role key (admin access)
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

import httpx


def _supabase_headers(service_key: str) -> Dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }


def list_template_kpis(
    base_url: str,
    headers: Dict[str, str],
    client_id: str,
    created_by: Optional[str],
) -> List[Dict[str, Any]]:
    """Return all template KPIs matching the filter."""
    params = {
        "select": "id,name,client_id,status,benchmark_source,metadata,created_at",
        "client_id": f"eq.{client_id}",
        "status": "eq.template",
    }
    resp = httpx.get(
        f"{base_url}/rest/v1/kpis",
        headers=headers,
        params=params,
        timeout=15.0,
    )
    resp.raise_for_status()
    rows = resp.json()
    if not created_by:
        return rows
    # Filter client-side on metadata.created_by since PostgREST JSONB path
    # filtering varies by deployment
    return [r for r in rows if (r.get("metadata") or {}).get("created_by") == created_by]


def delete_template_kpis(
    base_url: str,
    headers: Dict[str, str],
    client_id: str,
    kpi_ids: List[str],
) -> int:
    """Delete the listed template KPIs. Returns rows deleted."""
    if not kpi_ids:
        return 0
    # Use the `in` filter for batch delete: id=in.(a,b,c)
    quoted = ",".join(f'"{k}"' for k in kpi_ids)
    params = {
        "client_id": f"eq.{client_id}",
        "status": "eq.template",  # double safety — status MUST be template
        "id": f"in.({quoted})",
    }
    resp = httpx.delete(
        f"{base_url}/rest/v1/kpis",
        headers=headers,
        params=params,
        timeout=30.0,
    )
    resp.raise_for_status()
    deleted = resp.json()
    return len(deleted)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--client", default="lubricants", help="client_id to scope cleanup (default: lubricants)")
    parser.add_argument(
        "--created-by",
        default=None,
        help="Optional metadata.created_by filter (e.g. 'kpi_intelligence_ui')",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted, no changes")
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not service_key:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.", file=sys.stderr)
        return 1

    headers = _supabase_headers(service_key)

    try:
        templates = list_template_kpis(
            supabase_url, headers, args.client, args.created_by
        )
    except httpx.HTTPError as exc:
        print(f"ERROR: failed to list template KPIs: {exc}", file=sys.stderr)
        return 1

    if not templates:
        print(f"No template KPIs found for client='{args.client}'"
              + (f" with created_by='{args.created_by}'" if args.created_by else "")
              + ".")
        return 0

    print(f"Found {len(templates)} template KPI(s) for client='{args.client}':")
    for r in templates:
        src = r.get("benchmark_source") or "—"
        created_by = (r.get("metadata") or {}).get("created_by", "—")
        print(f"  - {r['id']:30s}  {r['name']:30s}  source={src:8s}  by={created_by}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would delete {len(templates)} row(s). Re-run without --dry-run to commit.")
        return 0

    try:
        deleted = delete_template_kpis(
            supabase_url, headers, args.client, [r["id"] for r in templates]
        )
    except httpx.HTTPError as exc:
        print(f"ERROR: delete failed: {exc}", file=sys.stderr)
        return 1

    print(f"\nDeleted {deleted} template KPI(s) for client='{args.client}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
