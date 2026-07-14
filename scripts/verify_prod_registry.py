#!/usr/bin/env python3
"""
Production registry verifier.

Queries production (or local) Supabase and checks that each client's registry data
matches what the seed file expects. Reports mismatches, missing records, and stale data.

Usage:
    python scripts/verify_prod_registry.py                          # all clients, production
    python scripts/verify_prod_registry.py --client apex_lubricants # single client
    python scripts/verify_prod_registry.py --env local              # check local Supabase
    python scripts/verify_prod_registry.py --client bicycle --client lubricants

Exit codes:
    0 — all checks passed
    1 — one or more mismatches found
"""

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

_CLIENTS_DIR = Path(__file__).resolve().parent / "clients"
_ALL_CLIENTS = [
    p.stem for p in _CLIENTS_DIR.glob("*.py")
    if p.stem not in ("__init__",)
]


# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------

def _load_env_file(path: str) -> None:
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
    }


def _fetch(client: httpx.Client, base_url: str, service_key: str, table: str, client_id: str) -> List[Dict]:
    """Fetch all rows for a client_id from a table."""
    url = f"{base_url.rstrip('/')}/rest/v1/{table}?client_id=eq.{client_id}&select=*"
    resp = client.get(url, headers=_headers(service_key))
    if resp.status_code != 200:
        print(f"  ERROR fetching {table}: {resp.status_code} {resp.text[:200]}")
        return []
    return resp.json()


def _fetch_business_context(client: httpx.Client, base_url: str, service_key: str, client_id: str) -> Optional[Dict]:
    """Fetch business context row (uses id not client_id)."""
    url = f"{base_url.rstrip('/')}/rest/v1/business_contexts?id=eq.{client_id}&select=*"
    resp = client.get(url, headers=_headers(service_key))
    if resp.status_code != 200:
        return None
    rows = resp.json()
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def _check_business_context(actual: Optional[Dict], expected_meta: Dict, client_id: str) -> List[str]:
    issues = []
    if actual is None:
        issues.append(f"business_contexts: no row found for id='{client_id}'")
        return issues
    for field in ("name", "industry"):
        exp = expected_meta.get(field, "")
        got = actual.get(field, "")
        if exp and got != exp:
            issues.append(f"business_contexts.{field}: expected '{exp}', got '{got}'")
    return issues


def _check_table(actual_rows: List[Dict], expected_rows: List[Dict], table: str, id_field: str = "id") -> List[str]:
    issues = []
    actual_ids = {r[id_field] for r in actual_rows}
    expected_ids = {r[id_field] for r in expected_rows}

    missing = expected_ids - actual_ids
    extra = actual_ids - expected_ids

    if missing:
        issues.append(f"{table}: {len(missing)} row(s) in seed but NOT in Supabase: {sorted(missing)[:5]}")
    if extra:
        issues.append(f"{table}: {len(extra)} row(s) in Supabase but NOT in seed (may be stale): {sorted(extra)[:5]}")

    # For rows that exist in both, check key fields
    actual_by_id = {r[id_field]: r for r in actual_rows}
    for exp in expected_rows:
        exp_id = exp[id_field]
        if exp_id not in actual_by_id:
            continue
        act = actual_by_id[exp_id]
        # Check a few important fields
        for field in _key_fields_for(table):
            exp_val = exp.get(field)
            act_val = act.get(field)
            if exp_val is not None and exp_val != act_val:
                issues.append(
                    f"{table}[{exp_id}].{field}: seed has {json.dumps(exp_val)[:80]}, "
                    f"Supabase has {json.dumps(act_val)[:80]}"
                )
    return issues


def _key_fields_for(table: str) -> List[str]:
    """Fields to compare for drift detection (beyond just ID presence)."""
    return {
        "kpis": ["sql_query", "source_system", "business_process_ids", "data_product_id"],
        "data_products": ["source_system", "domain", "owner"],
        "principal_profiles": ["role", "business_processes"],
        "business_processes": ["domain", "name"],
        "business_glossary_terms": ["definition"],
    }.get(table, [])


# ---------------------------------------------------------------------------
# RLS verification (Infra B3)
# ---------------------------------------------------------------------------

# Must stay in sync with supabase/migrations/20260713_rls_client_isolation.sql
_RLS_TABLES = [
    "kpis",
    "principal_profiles",
    "data_products",
    "business_processes",
    "business_glossary_terms",
    "value_assurance_solutions",
    "kpi_accountability",
    "kpi_relationships",
    "connection_profiles",
    "briefing_runs",
    "assessment_runs",
    "business_contexts",
]


def verify_rls(dsn: str, probe_client_id: str) -> List[str]:
    """Verify database-level tenant isolation is live. Returns issue strings.

    Checks that the a9_tenant_scope role exists (without BYPASSRLS), that every
    tenant table has RLS enabled with the client_isolation policy, and runs a
    live probe: the tenant role with no app.client_id must see zero rows, and
    scoped to one client must see only that client.
    """
    import asyncio

    import asyncpg

    async def _run() -> List[str]:
        issues: List[str] = []
        # statement_cache_size=0: required through the Supabase pgbouncer pooler
        # Non-local Supabase hosts require SSL; the Supavisor pooler returns a
        # misleading "tenant/user not found" error rather than a clean SSL
        # failure when the handshake isn't encrypted (mirrors PostgresManager.connect).
        from urllib.parse import urlparse
        host = (urlparse(dsn).hostname or "").lower()
        ssl_setting = False if host in ("localhost", "127.0.0.1", "::1") else "require"
        conn = await asyncpg.connect(dsn, statement_cache_size=0, timeout=15, ssl=ssl_setting)
        try:
            role = await conn.fetchrow(
                "SELECT rolbypassrls FROM pg_roles WHERE rolname = 'a9_tenant_scope'"
            )
            if role is None:
                return [
                    "RLS: role 'a9_tenant_scope' does not exist — migration "
                    "20260713_rls_client_isolation.sql has not been applied "
                    "(run: supabase db push --linked)"
                ]
            if role["rolbypassrls"]:
                issues.append("RLS: a9_tenant_scope has BYPASSRLS — policies are inert")

            rows = await conn.fetch(
                """
                SELECT c.relname AS table_name,
                       c.relrowsecurity AS rls_enabled,
                       EXISTS (
                           SELECT 1 FROM pg_policies p
                           WHERE p.schemaname = 'public'
                             AND p.tablename = c.relname
                             AND p.policyname = 'client_isolation'
                       ) AS has_policy
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = ANY($1::text[])
                """,
                _RLS_TABLES,
            )
            found = {r["table_name"]: r for r in rows}
            for table in _RLS_TABLES:
                r = found.get(table)
                if r is None:
                    issues.append(f"RLS: table '{table}' not found in database")
                elif not r["rls_enabled"]:
                    issues.append(f"RLS: '{table}' does not have row security enabled")
                elif not r["has_policy"]:
                    issues.append(f"RLS: '{table}' is missing the client_isolation policy")

            # Live probe — fail-closed: tenant role without app.client_id sees nothing
            async with conn.transaction():
                await conn.execute("SET LOCAL ROLE a9_tenant_scope")
                n = await conn.fetchval("SELECT count(*) FROM kpis")
                if n != 0:
                    issues.append(
                        f"RLS: tenant role with NO client context sees {n} kpi rows (expected 0)"
                    )

            # Live probe — scoped: only the probe client's rows are visible
            async with conn.transaction():
                await conn.execute("SET LOCAL ROLE a9_tenant_scope")
                await conn.execute(
                    "SELECT set_config('app.client_id', $1, true)", probe_client_id
                )
                visible = [
                    r["client_id"]
                    for r in await conn.fetch("SELECT DISTINCT client_id FROM kpis")
                ]
                if visible and visible != [probe_client_id]:
                    issues.append(
                        f"RLS: scoped to '{probe_client_id}' but sees clients {visible}"
                    )
        finally:
            await conn.close()
        return issues

    try:
        return asyncio.run(_run())
    except Exception as e:
        return [f"RLS: verification failed to run: {e}"]


# ---------------------------------------------------------------------------
# Per-client verification
# ---------------------------------------------------------------------------

def verify_client(
    http: httpx.Client,
    base_url: str,
    service_key: str,
    client_id: str,
) -> List[str]:
    """Return a list of issue strings for one client. Empty = clean."""

    # Load seed module
    try:
        mod = importlib.import_module(f"scripts.clients.{client_id}")
    except ModuleNotFoundError:
        return [f"No seed file found at scripts/clients/{client_id}.py"]

    issues = []

    # 1. business_contexts
    bc = _fetch_business_context(http, base_url, service_key, client_id)
    issues += _check_business_context(bc, mod.CLIENT_META, client_id)

    # 2. data_products
    raw_dp = getattr(mod, "DATA_PRODUCTS", [mod.DATA_PRODUCT] if hasattr(mod, "DATA_PRODUCT") else [])
    actual_dps = _fetch(http, base_url, service_key, "data_products", client_id)
    issues += _check_table(actual_dps, raw_dp, "data_products")

    # 3. kpis
    actual_kpis = _fetch(http, base_url, service_key, "kpis", client_id)
    issues += _check_table(actual_kpis, mod.KPIS, "kpis")

    # 4. principal_profiles
    actual_principals = _fetch(http, base_url, service_key, "principal_profiles", client_id)
    issues += _check_table(actual_principals, mod.PRINCIPALS, "principal_profiles")

    # 5. Count check for business_processes (canonical + extras)
    bp_ids = getattr(mod, "BUSINESS_PROCESS_IDS", [])
    extra_bps = getattr(mod, "EXTRA_BUSINESS_PROCESSES", [])
    expected_bp_count = len(bp_ids) + len(extra_bps)
    actual_bps = _fetch(http, base_url, service_key, "business_processes", client_id)
    if expected_bp_count > 0 and len(actual_bps) != expected_bp_count:
        issues.append(
            f"business_processes: seed expects {expected_bp_count} rows, "
            f"Supabase has {len(actual_bps)}"
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify production Supabase registry matches seed files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/verify_prod_registry.py
  python scripts/verify_prod_registry.py --client apex_lubricants
  python scripts/verify_prod_registry.py --env local
        """,
    )
    parser.add_argument(
        "--client", action="append", dest="clients",
        help="Client ID(s) to check (default: all)",
    )
    parser.add_argument(
        "--env", choices=["local", "production"], default="production",
        help="Which Supabase to check (default: production)",
    )
    args = parser.parse_args()

    env_file = str(_PROJECT_ROOT / (".env.production" if args.env == "production" else ".env"))
    _load_env_file(env_file)

    base_url = os.environ.get("SUPABASE_URL", "").strip()
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not base_url or not service_key:
        print(f"ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in {env_file}")
        return 1

    clients_to_check = args.clients or _ALL_CLIENTS

    print(f"\n{'='*65}")
    print(f"  Registry Verification — {args.env.upper()} Supabase")
    print(f"  Clients: {', '.join(clients_to_check)}")
    print(f"{'='*65}\n")

    all_clean = True

    # Database-level isolation check (Infra B3) — needs a direct Postgres DSN,
    # which PostgREST cannot provide.
    dsn = (os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL") or "").strip()
    print("Checking: RLS tenant isolation")
    if dsn:
        rls_issues = verify_rls(dsn, clients_to_check[0])
        if rls_issues:
            all_clean = False
            for issue in rls_issues:
                print(f"  MISMATCH  {issue}")
        else:
            print("  OK  — a9_tenant_scope role, policies, and fail-closed probes verified")
    else:
        print(f"  SKIPPED — set SUPABASE_DB_URL in {env_file} to verify RLS")
    print()

    with httpx.Client(timeout=30) as http:
        for client_id in clients_to_check:
            print(f"Checking: {client_id}")
            issues = verify_client(http, base_url, service_key, client_id)
            if issues:
                all_clean = False
                for issue in issues:
                    print(f"  MISMATCH  {issue}")
            else:
                print(f"  OK  — all registry tables match seed file")
            print()

    print("=" * 65)
    if all_clean:
        print("  All clients clean — production registry matches seed files.")
        print("=" * 65 + "\n")
        return 0
    else:
        print("  Mismatches found. Run onboard_client.py to resync:")
        for client_id in clients_to_check:
            print(f"    python scripts/onboard_client.py --client {client_id} --env production")
        print("=" * 65 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
