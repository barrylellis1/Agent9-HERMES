import asyncio
import os
import sys
import logging
from typing import Dict, Any, List, Set, TypeVar
from pydantic import BaseModel

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from src.registry.providers.data_product_provider import DataProductProvider, SupabaseDataProductProvider
from src.registry.providers.kpi_provider import KPIProvider, SupabaseKPIProvider
from src.registry.providers.business_process_provider import BusinessProcessProvider, SupabaseBusinessProcessProvider
from src.registry.providers.principal_provider import PrincipalProfileProvider, SupabasePrincipalProfileProvider
from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider, SupabaseBusinessGlossaryProvider
from src.registry.models.data_product import DataProduct
from src.registry.models.kpi import KPI
from src.registry.models.business_process import BusinessProcess
from src.registry.models.principal import PrincipalProfile
from src.registry.providers.business_glossary_provider import BusinessTerm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

def compare_sets(yaml_items: List[T], supabase_items: List[T], item_type: str, id_attr: str = "id"):
    """Compare two lists of items and print differences."""
    yaml_map = {getattr(i, id_attr): i for i in yaml_items}
    supabase_map = {getattr(i, id_attr): i for i in supabase_items}
    
    yaml_ids = set(yaml_map.keys())
    supabase_ids = set(supabase_map.keys())
    
    common = yaml_ids.intersection(supabase_ids)
    only_yaml = yaml_ids - supabase_ids
    only_supabase = supabase_ids - yaml_ids
    
    print(f"\n--- {item_type} Comparison ---")
    print(f"Total YAML: {len(yaml_items)}")
    print(f"Total Supabase: {len(supabase_items)}")
    print(f"Common: {len(common)}")
    
    if only_yaml:
        print(f"\n[!] Only in YAML ({len(only_yaml)}):")
        for i in sorted(only_yaml):
            print(f"  - {i}")
            
    if only_supabase:
        print(f"\n[!] Only in Supabase ({len(only_supabase)}):")
        for i in sorted(only_supabase):
            print(f"  - {i}")
            
    # Detailed comparison for common items could go here
    # For now, just checking existence
    print("-" * 30)

async def main():
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    registry_path = os.path.join(base_path, "src", "registry")
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not service_key:
        logger.error("Supabase credentials not found in environment variables.")
        return

    print("=== Comparing YAML Registry vs Supabase ===")
    
    # 1. Data Products
    print("\nLoading Data Products...")
    # YAML
    # Logic from bootstrap to find paths
    dp_registry_path = os.path.join(registry_path, "data_product", "data_product_registry.yaml")
    # Check for references if not found or empty (simplified logic from bootstrap)
    registry_references_path = os.path.join(base_path, "src", "registry_references")
    dp_ref_dir = os.path.join(registry_references_path, "data_product_registry", "data_products")
    
    yaml_source = dp_ref_dir if os.path.isdir(dp_ref_dir) else dp_registry_path
    
    dp_yaml = DataProductProvider(source_path=yaml_source, storage_format="yaml")
    await dp_yaml.load()
    
    # Supabase
    dp_supa = SupabaseDataProductProvider(
        supabase_url=supabase_url,
        service_key=service_key,
        source_path=None # No fallback for comparison
    )
    try:
        await dp_supa.load()
        compare_sets(dp_yaml.get_all(), dp_supa.get_all(), "Data Products")
    except Exception as e:
        logger.error(f"Failed to load Data Products from Supabase: {e}")

    # 2. KPIs
    print("\nLoading KPIs...")
    kpi_path = os.path.join(registry_path, "kpi", "kpi_registry.yaml")
    kpi_yaml = KPIProvider(source_path=kpi_path, storage_format="yaml")
    await kpi_yaml.load()
    
    kpi_supa = SupabaseKPIProvider(
        supabase_url=supabase_url,
        service_key=service_key,
        source_path=None
    )
    try:
        await kpi_supa.load()
        compare_sets(kpi_yaml.get_all(), kpi_supa.get_all(), "KPIs")
    except Exception as e:
        logger.error(f"Failed to load KPIs from Supabase: {e}")

    # 3. Business Processes
    print("\nLoading Business Processes...")
    bp_path = os.path.join(registry_path, "business_process", "business_process_registry.yaml")
    bp_yaml = BusinessProcessProvider(source_path=bp_path, storage_format="yaml")
    await bp_yaml.load()
    
    bp_supa = SupabaseBusinessProcessProvider(
        supabase_url=supabase_url,
        service_key=service_key,
        source_path=None
    )
    try:
        await bp_supa.load()
        compare_sets(bp_yaml.get_all(), bp_supa.get_all(), "Business Processes")
    except Exception as e:
        logger.error(f"Failed to load Business Processes from Supabase: {e}")

    # 4. Principals
    print("\nLoading Principals...")
    principal_path = os.path.join(registry_path, "principal", "principal_registry.yaml")
    p_yaml = PrincipalProfileProvider(source_path=principal_path, storage_format="yaml")
    await p_yaml.load()
    
    p_supa = SupabasePrincipalProfileProvider(
        supabase_url=supabase_url,
        service_key=service_key,
        source_path=None
    )
    try:
        await p_supa.load()
        compare_sets(p_yaml.get_all(), p_supa.get_all(), "Principals")
    except Exception as e:
        logger.error(f"Failed to load Principals from Supabase: {e}")

    # 5. Glossary
    print("\nLoading Business Glossary...")
    bg_path = os.path.join(registry_path, "data", "business_glossary.yaml")
    bg_yaml = BusinessGlossaryProvider(glossary_path=bg_path)
    # Glossary provider loads in init, but let's check
    
    bg_supa = SupabaseBusinessGlossaryProvider(
        supabase_url=supabase_url,
        service_key=service_key,
        glossary_path=None
    )
    try:
        await bg_supa.load()
        compare_sets(bg_yaml.get_all(), bg_supa.get_all(), "Business Terms", id_attr="name")
    except Exception as e:
        logger.error(f"Failed to load Glossary from Supabase: {e}")

if __name__ == "__main__":
    asyncio.run(main())
