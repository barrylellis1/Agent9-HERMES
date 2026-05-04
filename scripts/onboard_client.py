#!/usr/bin/env python3
"""
Generic client onboarding script — seeds all six registry tables for a given client.

Usage:
    python scripts/onboard_client.py --client bicycle [--dry-run]
    python scripts/onboard_client.py --client lubricants [--dry-run]
    python scripts/onboard_client.py --client bicycle --env production

Environment variables (loaded from .env or .env.production):
    SUPABASE_URL               - Supabase project URL
    SUPABASE_SERVICE_ROLE_KEY  - Service role key (admin access)

Client definitions live in scripts/clients/<client_id>.py and must export:
    CLIENT_ID              str
    CLIENT_META            Dict   - business context anchor row
    DATA_PRODUCT           Dict   - single data product definition
    KPIS                   List[Dict]
    PRINCIPALS             List[Dict]
    EXTRA_BUSINESS_PROCESSES List[Dict]  - client-specific BPs beyond canonical (may be [])
    EXTRA_GLOSSARY_TERMS   List[Dict]   - client-specific glossary terms (may be [])
    BUSINESS_PROCESS_IDS   List[str]    - which canonical BP IDs to seed for this client

Seeding order (all idempotent upserts):
    1. business_contexts      (client anchor)
    2. business_processes     (canonical filtered + client extras)
    3. business_glossary_terms (core terms + client extras)
    4. data_products
    5. kpis
    6. principal_profiles
"""

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Ensure project root is on sys.path so we can import src.*
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.registry.canonical.business_processes import ALL_BUSINESS_PROCESSES, BP_BY_ID
from src.registry.canonical.glossary import CORE_GLOSSARY_TERMS


# ---------------------------------------------------------------------------
# .env loader  (stdlib only — avoids python-dotenv dependency)
# ---------------------------------------------------------------------------

def _load_env_file(path: str) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ."""
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except FileNotFoundError:
        pass


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
        "Prefer": "resolution=merge-duplicates,return=representation",
    }


def _normalize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure all rows in a batch have the same key set (PostgREST requirement).

    Missing keys are filled with None so every dict is structurally identical.
    """
    if len(rows) <= 1:
        return rows
    all_keys = set().union(*(r.keys() for r in rows))
    return [{k: r.get(k) for k in sorted(all_keys)} for r in rows]


def _upsert(
    client: httpx.Client,
    base_url: str,
    service_key: str,
    table: str,
    rows: List[Dict[str, Any]],
    dry_run: bool = False,
) -> int:
    if not rows:
        return 0
    rows = _normalize_rows(rows)
    if dry_run:
        print(f"  [DRY-RUN] would upsert {len(rows)} row(s) into {table}")
        if len(rows) <= 3:
            for r in rows:
                print(f"    {json.dumps({k: v for k, v in r.items() if k not in ('sql_query', 'dimensions', 'metadata')})}")
        else:
            print(f"    first: {rows[0].get('id')} ... last: {rows[-1].get('id')}")
        return len(rows)

    url = f"{base_url.rstrip('/')}/rest/v1/{table}"
    resp = client.post(url, headers=_headers(service_key), json=rows)
    if resp.status_code not in (200, 201):
        print(f"  ERROR {resp.status_code} on {table}: {resp.text[:400]}")
        resp.raise_for_status()
    result = resp.json()
    count = len(result) if isinstance(result, list) else 1
    return count


def _delete_by_client(
    client: httpx.Client,
    base_url: str,
    service_key: str,
    table: str,
    client_id: str,
    dry_run: bool = False,
) -> None:
    """Delete all rows for a client_id from a table (used before re-keying)."""
    if dry_run:
        print(f"  [DRY-RUN] would DELETE FROM {table} WHERE client_id='{client_id}'")
        return
    url = f"{base_url.rstrip('/')}/rest/v1/{table}?client_id=eq.{client_id}"
    headers = {**_headers(service_key), "Prefer": "return=minimal"}
    resp = client.delete(url, headers=headers)
    if resp.status_code not in (200, 204):
        print(f"  WARNING: DELETE from {table} returned {resp.status_code}: {resp.text[:200]}")


# ---------------------------------------------------------------------------
# Business process + glossary stamp helpers
# ---------------------------------------------------------------------------

def _stamp_client_id(rows: List[Dict[str, Any]], client_id: str) -> List[Dict[str, Any]]:
    """Return copies of rows with client_id set."""
    return [{**r, "client_id": client_id} for r in rows]


def _select_canonical_bps(bp_ids: List[str], client_id: str) -> List[Dict[str, Any]]:
    """Return canonical BP rows for the given IDs, stamped with client_id."""
    rows = []
    missing = []
    for bp_id in bp_ids:
        bp = BP_BY_ID.get(bp_id)
        if bp:
            rows.append({**bp, "client_id": client_id})
        else:
            missing.append(bp_id)
    if missing:
        print(f"  WARNING: BP IDs not found in canonical taxonomy: {missing}")
    return rows


# ---------------------------------------------------------------------------
# Business context helper
# ---------------------------------------------------------------------------

def _business_context_row(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Build a business_contexts table row from CLIENT_META.

    Note: business_contexts uses 'id' as the sole PK — it IS the client anchor.
    There is no separate client_id column on this table.
    """
    return {
        "id": meta["id"],
        "name": meta["name"],
        "industry": meta.get("industry", ""),
        "data_product_ids": meta.get("data_product_ids", []),
    }


# ---------------------------------------------------------------------------
# Main onboarding logic
# ---------------------------------------------------------------------------

def onboard_client(
    client_id: str,
    base_url: str,
    service_key: str,
    dry_run: bool = False,
    force_rekeying: bool = False,
) -> None:
    """Seed all registry tables for one client. All operations are idempotent upserts."""

    # ------------------------------------------------------------------
    # Load client definition module
    # ------------------------------------------------------------------
    module_path = f"scripts.clients.{client_id}"
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError:
        print(f"ERROR: No client definition found at {module_path}")
        print(f"  Create scripts/clients/{client_id}.py with CLIENT_ID, CLIENT_META,")
        print(f"  DATA_PRODUCT, KPIS, PRINCIPALS, EXTRA_BUSINESS_PROCESSES, EXTRA_GLOSSARY_TERMS,")
        print(f"  and BUSINESS_PROCESS_IDS.")
        sys.exit(1)

    # Validate required exports
    required = ["CLIENT_ID", "CLIENT_META", "DATA_PRODUCT", "KPIS", "PRINCIPALS"]
    for attr in required:
        if not hasattr(mod, attr):
            print(f"ERROR: scripts/clients/{client_id}.py is missing required export: {attr}")
            sys.exit(1)

    assert mod.CLIENT_ID == client_id, (
        f"CLIENT_ID mismatch: file says '{mod.CLIENT_ID}', expected '{client_id}'"
    )

    bp_ids: List[str] = getattr(mod, "BUSINESS_PROCESS_IDS", [])
    extra_bps: List[Dict[str, Any]] = getattr(mod, "EXTRA_BUSINESS_PROCESSES", [])
    extra_glossary: List[Dict[str, Any]] = getattr(mod, "EXTRA_GLOSSARY_TERMS", [])

    print(f"\n{'='*60}")
    print(f"  Onboarding client: {client_id}")
    if dry_run:
        print(f"  Mode: DRY-RUN (no writes)")
    print(f"  Supabase: {base_url}")
    print(f"{'='*60}\n")

    with httpx.Client(timeout=30) as http:

        # ------------------------------------------------------------------
        # 1. business_contexts
        # ------------------------------------------------------------------
        print("[1/6] business_contexts")
        bc_row = _business_context_row(mod.CLIENT_META)
        n = _upsert(http, base_url, service_key, "business_contexts", [bc_row], dry_run)
        print(f"  OK  {n} row(s) upserted\n")

        # ------------------------------------------------------------------
        # 2. business_processes  (canonical BPs + client extras)
        # ------------------------------------------------------------------
        print("[2/6] business_processes")
        canonical_bps = _select_canonical_bps(bp_ids, client_id)
        extra_bps_stamped = _stamp_client_id(extra_bps, client_id)
        all_bps = canonical_bps + [
            ep for ep in extra_bps_stamped
            if ep["id"] not in {b["id"] for b in canonical_bps}
        ]
        print(f"  {len(canonical_bps)} canonical + {len(extra_bps_stamped)} extra = {len(all_bps)} total")
        n = _upsert(http, base_url, service_key, "business_processes", all_bps, dry_run)
        print(f"  OK  {n} row(s) upserted\n")

        # ------------------------------------------------------------------
        # 3. business_glossary_terms  (core + client extras)
        # ------------------------------------------------------------------
        print("[3/6] business_glossary_terms")
        # Table columns: id, name, term, definition, aliases, tags, metadata, client_id
        # 'name' is required (NOT NULL) — populate from 'term' if absent.
        # The canonical list includes a 'domain' field that doesn't exist in the table — strip it.
        _GLOSSARY_COLS = {"id", "name", "term", "definition", "aliases", "tags", "metadata", "client_id"}
        core_stamped = [
            {k: v for k, v in {**t, "name": t.get("name") or t.get("term", ""), "client_id": client_id}.items() if k in _GLOSSARY_COLS}
            for t in CORE_GLOSSARY_TERMS
        ]
        extra_glossary_stamped = [
            {k: v for k, v in {**t, "name": t.get("name") or t.get("term", ""), "client_id": client_id}.items() if k in _GLOSSARY_COLS}
            for t in extra_glossary
        ]
        all_glossary = core_stamped + [
            eg for eg in extra_glossary_stamped
            if eg["id"] not in {g["id"] for g in core_stamped}
        ]
        print(f"  {len(core_stamped)} core + {len(extra_glossary_stamped)} extra = {len(all_glossary)} total")
        n = _upsert(http, base_url, service_key, "business_glossary_terms", all_glossary, dry_run)
        print(f"  OK  {n} row(s) upserted\n")

        # ------------------------------------------------------------------
        # 4. data_products
        # ------------------------------------------------------------------
        print("[4/6] data_products")
        _DP_COLS = {
            "id", "name", "domain", "description", "owner", "version", "source_system",
            "related_business_processes", "tags", "metadata", "tables", "views",
            "yaml_contract_path", "output_path", "last_updated", "reviewed",
            "staging", "language", "documentation", "client_id",
        }
        raw_dp_rows = [mod.DATA_PRODUCT]
        if isinstance(getattr(mod, "DATA_PRODUCTS", None), list):
            raw_dp_rows = mod.DATA_PRODUCTS  # some clients may have multiple DPs
        dp_rows = [{k: v for k, v in row.items() if k in _DP_COLS} for row in raw_dp_rows]
        n = _upsert(http, base_url, service_key, "data_products", dp_rows, dry_run)
        print(f"  OK  {n} row(s) upserted\n")

        # ------------------------------------------------------------------
        # 5. kpis
        # ------------------------------------------------------------------
        print("[5/6] kpis")
        kpis: List[Dict[str, Any]] = mod.KPIS
        # Validate all KPIs have client_id set
        bad = [k["id"] for k in kpis if k.get("client_id") != client_id]
        if bad:
            print(f"  ERROR: {len(bad)} KPI(s) have wrong or missing client_id: {bad[:5]}")
            sys.exit(1)

        if force_rekeying:
            print(f"  --force-rekeying: deleting existing KPIs for '{client_id}' before re-insert")
            _delete_by_client(http, base_url, service_key, "kpis", client_id, dry_run)

        n = _upsert(http, base_url, service_key, "kpis", kpis, dry_run)
        print(f"  OK  {n} row(s) upserted\n")

        # ------------------------------------------------------------------
        # 6. principal_profiles
        # ------------------------------------------------------------------
        print("[6/6] principal_profiles")
        principals: List[Dict[str, Any]] = mod.PRINCIPALS
        bad_p = [p["id"] for p in principals if p.get("client_id") != client_id]
        if bad_p:
            print(f"  ERROR: {len(bad_p)} principal(s) have wrong or missing client_id: {bad_p}")
            sys.exit(1)

        if force_rekeying:
            print(f"  --force-rekeying: deleting existing principals for '{client_id}' before re-insert")
            _delete_by_client(http, base_url, service_key, "principal_profiles", client_id, dry_run)

        n = _upsert(http, base_url, service_key, "principal_profiles", principals, dry_run)
        print(f"  OK  {n} row(s) upserted\n")

    print(f"{'='*60}")
    if dry_run:
        print(f"  DRY-RUN complete — no data was written")
    else:
        print(f"  Onboarding complete for client: {client_id}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed all registry tables for a client from its definition file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/onboard_client.py --client bicycle --dry-run
  python scripts/onboard_client.py --client lubricants
  python scripts/onboard_client.py --client bicycle --env production
  python scripts/onboard_client.py --client lubricants --force-rekeying
        """,
    )
    parser.add_argument("--client", required=True, help="Client ID (e.g. bicycle, lubricants)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be seeded without writing")
    parser.add_argument(
        "--env",
        choices=["local", "production"],
        default="local",
        help="Load .env (local, default) or .env.production (production)",
    )
    parser.add_argument(
        "--force-rekeying",
        action="store_true",
        help="Delete existing KPIs and principals for this client before re-inserting (needed when re-keying composite PKs)",
    )
    args = parser.parse_args()

    # Load environment
    env_file = str(_PROJECT_ROOT / (".env.production" if args.env == "production" else ".env"))
    _load_env_file(env_file)

    base_url = os.environ.get("SUPABASE_URL", "").strip()
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not base_url:
        print(f"ERROR: SUPABASE_URL not set. Check {env_file}")
        sys.exit(1)
    if not service_key:
        print(f"ERROR: SUPABASE_SERVICE_ROLE_KEY not set. Check {env_file}")
        sys.exit(1)

    if args.env == "production" and not args.dry_run:
        print("WARNING: You are about to write to PRODUCTION Supabase.")
        print(f"  URL: {base_url}")
        confirm = input("  Type 'yes' to continue: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            sys.exit(0)

    onboard_client(
        client_id=args.client,
        base_url=base_url,
        service_key=service_key,
        dry_run=args.dry_run,
        force_rekeying=args.force_rekeying,
    )


if __name__ == "__main__":
    main()
