"""
Validator script for testing registry integration with agent models.
This script does not run full agent tests but just validates the metadata alignment.
"""

import sys
import os
import logging
from typing import Dict, List, Any, Set
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def check_business_process_alignment() -> Dict[str, Any]:
    """Check business process alignment between models, registries, and data contract."""
    from src.agents.models.situation_awareness_models import BusinessProcess
    from src.registry.factory import RegistryFactory
    
    # Get business processes from the model
    model_bps = [bp.value for bp in BusinessProcess]
    logger.info(f"Found {len(model_bps)} business processes in the model: {model_bps}")
    
    # Initialize registry factory
    registry_factory = RegistryFactory()
    
    # Get principal profiles from registry
    principal_provider = registry_factory.get_principal_profile_provider()
    profiles = principal_provider.get_all_profiles() if principal_provider else {}
    
    # Get business processes from the principal profiles
    profile_bps: Set[str] = set()
    for profile in profiles.values():
        for bp in profile.business_processes:
            profile_bps.add(bp)
    
    logger.info(f"Found {len(profile_bps)} unique business processes in principal profiles")
    
    # Get business processes from the KPI registry
    kpi_provider = registry_factory.get_kpi_provider()
    kpis = kpi_provider.get_all_kpis() if kpi_provider else {}
    
    kpi_bps: Set[str] = set()
    for kpi in kpis.values():
        if kpi.business_processes:
            for bp in kpi.business_processes:
                kpi_bps.add(bp)
    
    logger.info(f"Found {len(kpi_bps)} unique business processes in KPI registry")
    
    # Check alignment
    model_set = set(model_bps)
    
    missing_in_model = profile_bps.union(kpi_bps) - model_set
    missing_in_profiles = model_set - profile_bps
    missing_in_kpis = model_set - kpi_bps
    
    logger.info(f"Business processes in profiles but not in model: {missing_in_model}")
    logger.info(f"Business processes in model but not used in profiles: {missing_in_profiles}")
    logger.info(f"Business processes in model but not used in KPIs: {missing_in_kpis}")
    
    return {
        "model_business_processes": list(model_bps),
        "profile_business_processes": list(profile_bps),
        "kpi_business_processes": list(kpi_bps),
        "missing_in_model": list(missing_in_model),
        "missing_in_profiles": list(missing_in_profiles),
        "missing_in_kpis": list(missing_in_kpis),
    }

async def check_principal_role_alignment() -> Dict[str, Any]:
    """Check principal role alignment between models, registries."""
    from src.agents.models.situation_awareness_models import PrincipalRole
    from src.registry_references.principal_registry.principal_roles import PrincipalRole as RegistryPrincipalRole
    from src.registry.factory import RegistryFactory
    
    # Get roles from the model
    model_roles = [role.value for role in PrincipalRole]
    logger.info(f"Found {len(model_roles)} principal roles in the model: {model_roles}")
    
    # Get roles from the registry
    registry_roles = [role.value for role in RegistryPrincipalRole]
    logger.info(f"Found {len(registry_roles)} principal roles in the registry: {registry_roles}")
    
    # Initialize registry factory
    registry_factory = RegistryFactory()
    
    # Get principal profiles from registry
    principal_provider = registry_factory.get_principal_profile_provider()
    profiles = principal_provider.get_all_profiles() if principal_provider else {}
    
    # Get roles from the profiles
    profile_roles = list(profiles.keys())
    profile_role_values = [str(role) for role in profile_roles]
    logger.info(f"Found {len(profile_roles)} principal profiles: {profile_role_values}")
    
    # Check alignment
    model_set = set(model_roles)
    registry_set = set(registry_roles)
    
    missing_in_model = registry_set - model_set
    missing_in_registry = model_set - registry_set
    
    logger.info(f"Principal roles in registry but not in model: {missing_in_model}")
    logger.info(f"Principal roles in model but not in registry: {missing_in_registry}")
    
    return {
        "model_roles": model_roles,
        "registry_roles": profile_role_values,
        "missing_in_model": list(missing_in_model),
        "missing_in_registry": list(missing_in_registry),
    }

async def check_kpi_metadata_completeness() -> Dict[str, Any]:
    """Check KPI metadata completeness."""
    from src.registry.factory import RegistryFactory
    
    # Initialize registry factory
    registry_factory = RegistryFactory()
    
    # Get KPIs from registry
    kpi_provider = registry_factory.get_kpi_provider()
    kpis = kpi_provider.get_all_kpis() if kpi_provider else {}
    
    total_kpis = len(kpis)
    kpis_with_thresholds = 0
    kpis_with_business_processes = 0
    kpis_with_data_product_id = 0
    kpis_with_comparison_methods = 0
    kpis_with_dimensions = 0
    
    for kpi in kpis.values():
        if kpi.thresholds:
            kpis_with_thresholds += 1
        if kpi.business_processes:
            kpis_with_business_processes += 1
        if kpi.data_product_id:
            kpis_with_data_product_id += 1
        if kpi.comparison_methods:
            kpis_with_comparison_methods += 1
        if kpi.dimensions:
            kpis_with_dimensions += 1
    
    logger.info(f"KPIs with thresholds: {kpis_with_thresholds}/{total_kpis}")
    logger.info(f"KPIs with business processes: {kpis_with_business_processes}/{total_kpis}")
    logger.info(f"KPIs with data_product_id: {kpis_with_data_product_id}/{total_kpis}")
    logger.info(f"KPIs with comparison_methods: {kpis_with_comparison_methods}/{total_kpis}")
    logger.info(f"KPIs with dimensions: {kpis_with_dimensions}/{total_kpis}")
    
    return {
        "total_kpis": total_kpis,
        "kpis_with_thresholds": kpis_with_thresholds,
        "kpis_with_business_processes": kpis_with_business_processes,
        "kpis_with_data_product_id": kpis_with_data_product_id,
        "kpis_with_comparison_methods": kpis_with_comparison_methods,
        "kpis_with_dimensions": kpis_with_dimensions,
    }

async def main():
    """Main validation function."""
    try:
        print("\n" + "="*60)
        print("REGISTRY INTEGRATION VALIDATION")
        print("="*60)
        
        # Initialize the registry factory once
        from src.registry.factory import RegistryFactory
        registry_factory = RegistryFactory()
        await registry_factory.initialize()
        
        # Test 1: Business Process Alignment
        print("\n1. CHECKING BUSINESS PROCESS ALIGNMENT")
        print("-"*40)
        bp_results = await check_business_process_alignment()
        
        # Test 2: Principal Role Alignment
        print("\n2. CHECKING PRINCIPAL ROLE ALIGNMENT")
        print("-"*40)
        role_results = await check_principal_role_alignment()
        
        # Test 3: KPI Metadata Completeness
        print("\n3. CHECKING KPI METADATA COMPLETENESS")
        print("-"*40)
        kpi_results = await check_kpi_metadata_completeness()
        
        # Output summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        # Combine all results
        all_results = {
            "business_process_alignment": bp_results,
            "principal_role_alignment": role_results,
            "kpi_metadata_completeness": kpi_results,
        }
        
        # Check for any issues
        has_issues = (
            len(bp_results["missing_in_model"]) > 0 or
            len(bp_results["missing_in_kpis"]) > 0 or
            len(role_results["missing_in_model"]) > 0 or
            len(role_results["missing_in_registry"]) > 0 or
            kpi_results["kpis_with_thresholds"] < kpi_results["total_kpis"] or
            kpi_results["kpis_with_business_processes"] < kpi_results["total_kpis"] or
            kpi_results["kpis_with_data_product_id"] < kpi_results["total_kpis"]
        )
        
        if has_issues:
            print("\nValidation found issues that need to be addressed:")
            
            if len(bp_results["missing_in_model"]) > 0:
                print(f"- {len(bp_results['missing_in_model'])} business processes used in registries but not defined in the model")
            
            if len(bp_results["missing_in_kpis"]) > 0:
                print(f"- {len(bp_results['missing_in_kpis'])} business processes defined but not used in any KPI")
            
            if kpi_results["kpis_with_thresholds"] < kpi_results["total_kpis"]:
                print(f"- {kpi_results['total_kpis'] - kpi_results['kpis_with_thresholds']} KPIs missing thresholds")
            
            if kpi_results["kpis_with_business_processes"] < kpi_results["total_kpis"]:
                print(f"- {kpi_results['total_kpis'] - kpi_results['kpis_with_business_processes']} KPIs missing business processes")
            
            if kpi_results["kpis_with_data_product_id"] < kpi_results["total_kpis"]:
                print(f"- {kpi_results['total_kpis'] - kpi_results['kpis_with_data_product_id']} KPIs missing data_product_id")
        else:
            print("\nValidation completed successfully! No issues found.")
            
        # Save detailed results to file
        with open("validation_results.json", "w") as f:
            json.dump(all_results, f, indent=2)
            print(f"\nDetailed results saved to validation_results.json")
        
    except Exception as e:
        logger.error(f"Error in validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
