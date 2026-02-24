"""DEPRECATED: Seed the Supabase business_glossary_terms table from the YAML registry.

As of 2026-02-19, the business glossary is managed directly in Supabase.
Pass --force to run this script for disaster recovery only.

Original description:
This script is intended for local/dev usage while piloting the Supabase-backed
registry. It reads `src/registry/data/business_glossary.yaml`, transforms each
term into a Supabase row, and performs an upsert into the target table.

Usage (example):
    SUPABASE_URL=http://localhost:54321 \
    SUPABASE_SERVICE_ROLE_KEY=... \
    python scripts/supabase_seed_business_glossary.py --dry-run

Flags:
    --dry-run          Print the payload without performing any writes.
    --truncate-first   Delete existing rows before upserting new ones.

Environment variables:
    SUPABASE_URL (required)
    SUPABASE_SERVICE_ROLE_KEY (required)
    SUPABASE_SCHEMA (default: public)
    SUPABASE_BUSINESS_GLOSSARY_TABLE (default: business_glossary_terms)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_PATH = PROJECT_ROOT / "src" / "registry" / "data" / "business_glossary.yaml"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "term"


def load_glossary(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Glossary file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    terms = data.get("terms", [])
    if not isinstance(terms, list):
        raise ValueError("Glossary YAML must contain a list under the 'terms' key")
    return terms


def transform_terms(raw_terms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for entry in raw_terms:
        name = (entry.get("name") or "").strip()
        if not name:
            continue

        term_id = entry.get("id") or slugify(name)
        synonyms = entry.get("synonyms") or []
        if isinstance(synonyms, str):
            synonyms = [synonyms]

        technical_mappings = entry.get("technical_mappings") or {}
        if not isinstance(technical_mappings, dict):
            technical_mappings = {}

        rows.append(
            {
                "id": term_id,
                "term": name,
                "definition": entry.get("description"),
                "aliases": [syn for syn in synonyms if syn],
                "tags": list({*technical_mappings.keys()}),
                "metadata": technical_mappings,
            }
        )
    return rows


def delete_existing_rows(client: httpx.Client, endpoint: str, headers: Dict[str, str]) -> None:
    # "id=not.is.null" is the supported pattern for deleting all rows in table
    response = client.delete(endpoint, headers=headers, params={"id": "not.is.null"})
    response.raise_for_status()


def upsert_rows(
    client: httpx.Client,
    endpoint: str,
    headers: Dict[str, str],
    rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    response = client.post(
        endpoint,
        headers={**headers, "Content-Type": "application/json"},
        params={"on_conflict": "id"},
        content=json.dumps(rows),
    )
    response.raise_for_status()
    try:
        return response.json()
    except json.JSONDecodeError:
        return []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed Supabase business glossary table")
    parser.add_argument("--dry-run", action="store_true", help="Print payload without writing")
    parser.add_argument("--truncate-first", action="store_true", help="Delete existing rows before upsert")
    parser.add_argument("--force", action="store_true", help="Force run deprecated script")
    return parser.parse_args()


def main() -> int:
    # DEPRECATED — Supabase is now the sole registry backend
    if "--force" not in sys.argv:
        print("⚠️  DEPRECATED: supabase_seed_business_glossary.py — registries now live in Supabase. Pass --force to run.")
        return 0

    args = parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_role = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_service_role:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set", file=sys.stderr)
        return 1

    table = os.getenv("SUPABASE_BUSINESS_GLOSSARY_TABLE", "business_glossary_terms")
    schema = os.getenv("SUPABASE_SCHEMA", "public")
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/{table}"

    raw_terms = load_glossary(GLOSSARY_PATH)
    rows = transform_terms(raw_terms)

    if args.dry_run:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        print(f"Prepared {len(rows)} rows. Dry run mode - no changes applied.")
        return 0

    headers = {
        "apikey": supabase_service_role,
        "Authorization": f"Bearer {supabase_service_role}",
        "Prefer": "resolution=merge-duplicates,return=representation",
        "Accept": "application/json",
        "Accept-Profile": schema,
    }

    with httpx.Client(timeout=30.0) as client:
        if args.truncate_first:
            delete_existing_rows(client, endpoint, headers)
            print("Existing rows deleted.")

        inserted = upsert_rows(client, endpoint, headers, rows)

    print(f"Seeded {len(inserted) if inserted else len(rows)} rows into {table}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
