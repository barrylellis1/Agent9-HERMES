#!/usr/bin/env python3
"""
DEPRECATED: Seed business contexts into Supabase.

As of 2026-02-19, business contexts are managed directly in Supabase.
Pass --force to run this script for disaster recovery only.

Original description:
This script reads business context data and inserts it into the business_contexts table.
Supports both demo contexts and real customer contexts.

Usage:
    python scripts/supabase_seed_business_contexts.py [--dry-run] [--truncate-first]

Environment Variables:
    SUPABASE_URL: Supabase project URL (required)
    SUPABASE_SERVICE_ROLE_KEY: Service role key (required)
    SUPABASE_SCHEMA: Database schema (default: public)
    SUPABASE_BUSINESS_CONTEXTS_TABLE: Table name (default: business_contexts)
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("Error: pyyaml is required. Install with: pip install pyyaml")
    sys.exit(1)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_bicycle_context() -> dict:
    """Load bicycle retail context from YAML."""
    yaml_path = project_root / "src/registry_references/business_context/bicycle_retail_context.yaml"
    
    if yaml_path.exists():
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return {
                "id": "demo_bicycle",
                "name": data.get("name", "Global Bike Inc."),
                "industry": data.get("industry", "Retail & Manufacturing"),
                "sub_sector": data.get("sub_sector"),
                "description": data.get("description"),
                "business_model": data.get("business_model", {}),
                "strategic_priorities": data.get("strategic_priorities", []),
                "competitors": data.get("competitors", []),
                "operational_context": data.get("operational_context", {}),
                "is_demo": True,
            }
    
    # Fallback if YAML doesn't exist
    logger.warning(f"Bicycle context YAML not found at {yaml_path}, using hardcoded data")
    return {
        "id": "demo_bicycle",
        "name": "Global Bike Inc.",
        "industry": "Retail & Manufacturing",
        "sub_sector": "Bicycles & Accessories",
        "description": "A leading global bicycle manufacturer and retailer operating across North America, Europe, and APAC.",
        "business_model": {
            "type": "Hybrid (Manufacturing + Retail)",
            "revenue_streams": ["Wholesale Sales (B2B)", "Internet Sales (B2C)"],
            "key_markets": ["US West", "US East", "Germany", "Australia"]
        },
        "strategic_priorities": [
            "Expand market share in the growing E-Bike segment",
            "Optimize global supply chain to reduce inventory holding costs",
            "Maintain premium brand positioning against competitors"
        ],
        "competitors": ["Trek Bicycle Corporation", "Specialized Bicycle Components", "Giant Manufacturing", "Canyon Bicycles"],
        "operational_context": {
            "inventory_challenges": "High seasonality in sales; long lead times from Asian component suppliers",
            "margin_pressures": "Rising logistics costs and competitive pricing in the mid-range segment"
        },
        "is_demo": True,
    }


def create_lubricants_context() -> dict:
    """Create lubricants & specialty products context."""
    return {
        "id": "demo_lubricants",
        "name": "Summit Lubricants & Specialty Products",
        "industry": "Specialty Chemicals & Automotive Aftermarket",
        "sub_sector": "Automotive & Industrial Lubricants",
        "revenue": "$3.2B",
        "employees": "4,800",
        "ownership": "Public (NYSE: SLSP)",
        "description": (
            "Leading manufacturer and distributor of automotive and industrial lubricants. "
            "Product portfolio includes synthetic motor oils, conventional lubricants, "
            "transmission fluids, and specialty chemicals. Channels include retail (AutoZone, "
            "O'Reilly), quick-lube franchises, and industrial B2B."
        ),
        "business_model": {
            "revenue_streams": [
                "Retail (40%): Branded products through auto parts stores",
                "Quick-Lube (35%): Valvoline Instant Oil Change franchises",
                "Industrial B2B (25%): Fleet and manufacturing customers"
            ],
            "key_markets": [
                "North America (75%)",
                "Europe (15%)",
                "Asia-Pacific (10%)"
            ]
        },
        "strategic_priorities": [
            "Improve gross margin from 38% to 42% (raw material cost pressure)",
            "Optimize product mix (shift to high-margin synthetic products)",
            "Expand direct-to-consumer channel (quick-lube franchises)",
            "Reduce manufacturing costs (12 plants, optimize footprint)"
        ],
        "competitors": [
            "Shell Lubricants",
            "Castrol (BP)",
            "Mobil 1 (ExxonMobil)",
            "Pennzoil (Shell)"
        ],
        "operational_context": {
            "margin_pressures": "Base oil prices volatile ($2.50-$4.00/gal), impacting 60% of COGS",
            "channel_complexity": "Different margin profiles by channel (Retail 45%, Quick-Lube 40%, Industrial 30%)",
            "product_mix_challenge": "Synthetic products 50% margin vs conventional 35% margin"
        },
        "consulting_spend": "$3.5M annually",
        "consulting_firms_used": {
            "Bain": {"focus": "pricing strategy", "spend": "$1.2M"},
            "AlixPartners": {"focus": "cost reduction", "spend": "$1.5M"},
            "Regional firms": {"focus": "ad-hoc projects", "spend": "$800K"}
        },
        "pain_points": [
            "Margin analysis by product/channel takes 2-3 weeks (need real-time visibility)",
            "Pricing decisions delayed by slow analytics (miss market windows)",
            "Plant network optimization requires 6-month $500K consulting project",
            "Multiple consulting firms = fragmented recommendations, no audit trail"
        ],
        "is_demo": True,
    }


def get_all_contexts() -> list[dict]:
    """Get all business contexts to seed."""
    return [
        load_bicycle_context(),
        create_lubricants_context(),
    ]


def delete_existing_rows(endpoint: str, headers: dict):
    """Delete all existing rows from the table."""
    logger.info("Truncating business_contexts table...")
    try:
        response = httpx.delete(
            endpoint,
            headers=headers,
            params={"id": "neq."}  # Delete all rows
        )
        response.raise_for_status()
        logger.info("✅ Table truncated")
    except Exception as e:
        logger.error(f"Failed to truncate table: {e}")
        raise


def upsert_rows(endpoint: str, headers: dict, rows: list[dict]):
    """Upsert rows into Supabase."""
    logger.info(f"Upserting {len(rows)} business contexts...")
    
    # Add Prefer header for upsert
    upsert_headers = {
        **headers,
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    
    try:
        response = httpx.post(
            endpoint,
            headers=upsert_headers,
            json=rows
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"✅ Seeded {len(result)} rows into business_contexts")
        return result
    except Exception as e:
        logger.error(f"Failed to upsert rows: {e}")
        if hasattr(e, 'response'):
            logger.error(f"Response: {e.response.text}")
        raise


def main():
    # DEPRECATED — Supabase is now the sole registry backend
    if "--force" not in sys.argv:
        print("⚠️  DEPRECATED: supabase_seed_business_contexts.py — registries now live in Supabase. Pass --force to run.")
        return

    parser = argparse.ArgumentParser(description="Seed business contexts into Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Print data without inserting")
    parser.add_argument("--truncate-first", action="store_true", help="Delete existing rows before inserting")
    parser.add_argument("--force", action="store_true", help="Force run deprecated script")
    args = parser.parse_args()
    
    # Get configuration from environment
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    schema = os.getenv("SUPABASE_SCHEMA", "public")
    table_name = os.getenv("SUPABASE_BUSINESS_CONTEXTS_TABLE", "business_contexts")
    
    if not supabase_url or not service_key:
        logger.error("Missing required environment variables: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
    
    endpoint = f"{supabase_url}/rest/v1/{table_name}"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Profile": schema,
    }
    
    # Get all contexts
    contexts = get_all_contexts()
    
    if args.dry_run:
        logger.info("DRY RUN - would insert the following data:")
        print(json.dumps(contexts, indent=2))
        return
    
    # Truncate if requested
    if args.truncate_first:
        delete_existing_rows(endpoint, headers)
    
    # Upsert rows
    upsert_rows(endpoint, headers, contexts)
    
    logger.info("✅ Business contexts seeding complete")
    logger.info(f"   - Bicycle demo: demo_bicycle")
    logger.info(f"   - Lubricants demo: demo_lubricants")


if __name__ == "__main__":
    main()
