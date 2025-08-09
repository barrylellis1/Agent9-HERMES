"""
Simple test script to verify registry loading and adapter modules.
"""

import sys
import os
import logging

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def main():
    """Test loading of registries and check adapter modules using Registry Factory."""
    try:
        # Import and initialize Registry Factory
        from src.registry.factory import RegistryFactory
        from src.registry.providers.registry_provider import (
            PrincipalProfileProvider,
            KPIProvider,
            BusinessProcessProvider,
            DataProductProvider
        )
        
        # Initialize the registry factory
        registry_factory = RegistryFactory()
        await registry_factory.initialize()
        
        # Get principal profiles from registry factory
        principal_provider = registry_factory.get_principal_profile_provider()
        profiles = principal_provider.get_all_profiles() if principal_provider else {}
        
        # Print info about loaded registries
        print(f"\n=== Testing Principal Profiles Registry (via Registry Factory) ===")
        print(f"Loaded {len(profiles)} principal profiles")
        for role, profile in profiles.items():
            print(f"  - {role}: {profile.first_name} {profile.last_name}, {profile.role}")
            print(f"    Business processes: {len(profile.business_processes)}")
        
        # Get KPIs from registry factory
        kpi_provider = registry_factory.get_kpi_provider()
        kpis = kpi_provider.get_all_kpis() if kpi_provider else {}
        
        print(f"\n=== Testing KPI Registry (via Registry Factory) ===")
        print(f"Loaded {len(kpis)} KPIs")
        for i, (kpi_id, kpi) in enumerate(list(kpis.items())[:3]):  # Show first 3 for brevity
            print(f"  - KPI {i+1}: {kpi.name}")
            print(f"    Description: {kpi.description}")
            print(f"    Business processes: {kpi.business_processes}")
        
        # Check if any KPIs have business processes matching the ones in principal profiles
        kpi_bps = set()
        for kpi in kpis.values():
            for bp in kpi.business_processes:
                kpi_bps.add(bp)
        
        principal_bps = set()
        for role, profile in profiles.items():
            for bp in profile.business_processes:
                principal_bps.add(bp)
        
        common_bps = kpi_bps.intersection(principal_bps)
        print(f"\n=== Checking Business Process Alignment ===")
        print(f"KPI business processes: {len(kpi_bps)}")
        print(f"Principal business processes: {len(principal_bps)}")
        print(f"Common business processes: {len(common_bps)}")
        
        if common_bps:
            print("Sample common business processes:")
            for bp in list(common_bps)[:3]:  # Show first 3 for brevity
                print(f"  - {bp}")
        else:
            print("WARNING: No common business processes between KPIs and principal profiles!")
        
        print("\nRegistry test completed successfully")
        
    except Exception as e:
        logger.error(f"Error loading registries: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
